from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, Iterable, Optional

from .api_models import CodexActionContext, CodexChatStreamRequest

try:
    from openai import AsyncOpenAI
except ImportError:  # pragma: no cover - package is optional in local fallback mode
    AsyncOpenAI = None  # type: ignore[assignment]


DEFAULT_MODEL = "gpt-4.1-mini"
DEFAULT_ACTIONS = [
    "explain_mapping",
    "compare_alternatives",
    "draft_reviewer_note",
    "approve_mapping",
    "reject_mapping",
    "rerun_reasoning",
    "prepare_package",
]


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sse(event_type: str, data: Dict[str, Any]) -> str:
    return "event: {event}\ndata: {data}\n\n".format(
        event=event_type,
        data=json.dumps(data),
    )


def _event_type(event: Any) -> str:
    if hasattr(event, "type"):
        return str(getattr(event, "type"))
    if isinstance(event, dict):
        return str(event.get("type", ""))
    return ""


def _event_value(event: Any, key: str, default: Any = None) -> Any:
    if hasattr(event, key):
        return getattr(event, key)
    if isinstance(event, dict):
        return event.get(key, default)
    return default


def _chunk_text(text: str, chunk_size: int = 72) -> Iterable[str]:
    for idx in range(0, len(text), chunk_size):
        yield text[idx : idx + chunk_size]


def _effective_actions(action_context: Optional[CodexActionContext]) -> list[str]:
    if action_context is None:
        return list(DEFAULT_ACTIONS)
    actions = [action for action in action_context.available_actions if action in DEFAULT_ACTIONS]
    return actions or list(DEFAULT_ACTIONS)


def _simulate_demo_action(action_context: Optional[CodexActionContext]) -> Optional[Dict[str, Any]]:
    if action_context is None or action_context.requested_action is None:
        return None

    action = action_context.requested_action
    selected_mapping_id = action_context.selected_mapping_id or "map_demo_001"
    payload: Dict[str, Any] = {
        "action": action,
        "run_id": action_context.run_id,
        "project_id": action_context.project_id,
        "case_id": action_context.case_id,
        "selected_mapping_id": selected_mapping_id,
        "executed_at": _utcnow(),
        "mode": "demo_simulated",
    }

    if action == "explain_mapping":
        payload["result"] = {
            "explanation": (
                "Source and target fields share customer identity semantics with compatible constraints; "
                "this mapping is likely valid pending human review."
            )
        }
    elif action == "compare_alternatives":
        payload["result"] = {
            "comparison": (
                "customer_status better preserves downstream reporting and package validation, while "
                "account_state is closer to the finance source semantics."
            )
        }
    elif action == "draft_reviewer_note":
        payload["result"] = {
            "note": (
                "Draft: Mapping appears semantically aligned based on naming, value distribution, and graph context. "
                "Recommend approve unless downstream constraints conflict."
            )
        }
    elif action == "approve_mapping":
        payload["result"] = {"decision": "approved", "new_status": "mapping_approved_demo"}
    elif action == "reject_mapping":
        payload["result"] = {"decision": "rejected", "new_status": "mapping_rejected_demo"}
    elif action == "rerun_reasoning":
        payload["result"] = {"job_status": "queued", "job_id": f"rerun_{selected_mapping_id}"}
    elif action == "prepare_package":
        payload["result"] = {"package_status": "prepared", "package_id": f"pkg_{selected_mapping_id}"}
    else:
        payload["result"] = {"message": "Action not recognized in demo mode."}

    return payload


def _build_system_prompt(actions: list[str], action_result: Optional[Dict[str, Any]]) -> str:
    lines = [
        "You are Codex assisting a migration review workspace demo.",
        "Use concise, direct responses and reference available UI actions when useful.",
        "Available demo actions: {actions}.".format(actions=", ".join(actions)),
        "If an action has already been executed server-side, incorporate its result into your response.",
    ]
    if action_result:
        lines.append("Executed action payload: {payload}".format(payload=json.dumps(action_result)))
    return "\n".join(lines)


def _build_model_input(
    request: CodexChatStreamRequest,
    action_result: Optional[Dict[str, Any]],
) -> list[Dict[str, str]]:
    actions = _effective_actions(request.action_context)
    messages: list[Dict[str, str]] = [{"role": "system", "content": _build_system_prompt(actions, action_result)}]

    for message in request.messages:
        messages.append({"role": message.role, "content": message.content})

    return messages


def _extract_output_text(response_payload: Any) -> str:
    if response_payload is None:
        return ""

    if isinstance(response_payload, dict):
        output_text = response_payload.get("output_text")
        if isinstance(output_text, str):
            return output_text
        return ""

    output_text = getattr(response_payload, "output_text", "")
    if isinstance(output_text, str):
        return output_text
    return ""


async def _stream_fallback(
    request: CodexChatStreamRequest,
    *,
    reason: str,
    action_result: Optional[Dict[str, Any]],
    model: str,
) -> AsyncIterator[str]:
    last_user_message = next((msg.content for msg in reversed(request.messages) if msg.role == "user"), "")
    fallback_text = (
        "Demo mode active. {reason} "
        "I can still guide the review flow and simulate actions while the UI/backend integration is tested."
    ).format(reason=reason)
    if last_user_message:
        fallback_text += " You asked: {message}".format(message=last_user_message)
    if action_result:
        fallback_text += " Executed action: {action}.".format(action=action_result.get("action", "unknown"))

    yield _sse(
        "meta",
        {
            "status": "fallback",
            "reason": reason,
            "model": model,
        },
    )
    if action_result:
        yield _sse("tool_action", action_result)

    for chunk in _chunk_text(fallback_text):
        yield _sse("assistant_delta", {"delta": chunk})
        await asyncio.sleep(0.03)

    yield _sse("done", {"status": "completed", "mode": "fallback"})


async def stream_codex_chat(
    request: CodexChatStreamRequest,
    *,
    api_key: Optional[str],
    model: Optional[str] = None,
) -> AsyncIterator[str]:
    chosen_model = model or request.model or DEFAULT_MODEL
    action_result = _simulate_demo_action(request.action_context)

    if not api_key:
        async for chunk in _stream_fallback(
            request,
            reason="OPENAI_API_KEY is not configured on the server.",
            action_result=action_result,
            model=chosen_model,
        ):
            yield chunk
        return

    if AsyncOpenAI is None:
        async for chunk in _stream_fallback(
            request,
            reason="The openai package is not installed in this API environment.",
            action_result=action_result,
            model=chosen_model,
        ):
            yield chunk
        return

    client = AsyncOpenAI(api_key=api_key)
    model_input = _build_model_input(request, action_result)
    yielded_text = False

    try:
        yield _sse("meta", {"status": "connected", "model": chosen_model})
        if action_result:
            yield _sse("tool_action", action_result)

        stream = await client.responses.create(
            model=chosen_model,
            input=model_input,
            stream=True,
        )
        async for event in stream:
            event_type = _event_type(event)
            if event_type == "response.output_text.delta":
                delta = _event_value(event, "delta", "")
                if isinstance(delta, str) and delta:
                    yielded_text = True
                    yield _sse("assistant_delta", {"delta": delta})
            elif event_type == "response.error":
                error_payload = _event_value(event, "error", {})
                yield _sse("error", {"message": str(error_payload)})
            elif event_type == "response.completed":
                response_payload = _event_value(event, "response")
                if not yielded_text:
                    final_text = _extract_output_text(response_payload)
                    for chunk in _chunk_text(final_text):
                        yield _sse("assistant_delta", {"delta": chunk})
                yield _sse("done", {"status": "completed", "mode": "openai"})
                return

        yield _sse("done", {"status": "completed", "mode": "openai"})
    except Exception as exc:  # pragma: no cover - exercised in live integration
        async for chunk in _stream_fallback(
            request,
            reason="OpenAI request failed: {error}".format(error=str(exc)),
            action_result=action_result,
            model=chosen_model,
        ):
            yield chunk
