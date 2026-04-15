from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from urllib import error, request


SYSTEM_PROMPT = """
You are Codex operating in Understand Mode for enterprise ontology migration after an acquisition.
Analyze uploaded schema and sample data context to infer business meaning, identify entities and
fields, draft a provisional semantic context graph, and generate clarification questions for
employees who understand the source systems. Return only structured JSON that matches the provided
schema.
""".strip()


UNDERSTAND_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "entities": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": ["string", "null"]},
                    "confidence": {"type": ["number", "null"]},
                    "metadata": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {},
                    },
                },
                "required": ["name", "description", "confidence", "metadata"],
            },
        },
        "fields": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "name": {"type": "string"},
                    "entity": {"type": ["string", "null"]},
                    "semantic_type": {"type": ["string", "null"]},
                    "description": {"type": ["string", "null"]},
                    "confidence": {"type": ["number", "null"]},
                },
                "required": ["name", "entity", "semantic_type", "description", "confidence"],
            },
        },
        "inferred_meanings": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "subject": {"type": "string"},
                    "meaning": {"type": "string"},
                    "confidence": {"type": ["number", "null"]},
                },
                "required": ["subject", "meaning", "confidence"],
            },
        },
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "prompt": {"type": "string"},
                    "context": {"type": ["string", "null"]},
                    "severity": {"type": ["string", "null"]},
                },
                "required": ["prompt", "context", "severity"],
            },
        },
        "graph": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "nodes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "label": {"type": "string"},
                            "type": {"type": "string"},
                            "data": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {},
                            },
                            "metadata": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {},
                            },
                        },
                        "required": ["label", "type", "data", "metadata"],
                    },
                },
                "edges": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "source": {"type": "string"},
                            "target": {"type": "string"},
                            "relation": {"type": "string"},
                            "metadata": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {},
                            },
                        },
                        "required": ["source", "target", "relation", "metadata"],
                    },
                },
            },
            "required": ["nodes", "edges"],
        },
        "confidence": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "overall": {"type": "number"},
                "by_entity": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "entity": {"type": "string"},
                            "confidence": {"type": "number"},
                        },
                        "required": ["entity", "confidence"],
                    },
                },
            },
            "required": ["overall", "by_entity"],
        },
        "summary": {"type": "string"},
    },
    "required": [
        "entities",
        "fields",
        "inferred_meanings",
        "questions",
        "graph",
        "confidence",
        "summary",
    ],
}


def run_understand_workflow(
    project: Any,
    files: Iterable[Any],
    instructions: str,
    user_notes: Optional[str] = None,
    run_id: Optional[str] = None,
    graph_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")

    payload = {
        "model": os.getenv("OPENAI_CODEX_MODEL", "gpt-5-codex"),
        "instructions": SYSTEM_PROMPT,
        "input": _build_input_text(
            project=project,
            files=files,
            instructions=instructions,
            user_notes=user_notes,
            graph_context=graph_context,
        ),
        "text": {
            "format": {
                "type": "json_schema",
                "name": "understand_mode_result",
                "schema": UNDERSTAND_SCHEMA,
                "strict": True,
            }
        },
    }

    raw_response = _create_response(payload, api_key=api_key)
    parsed = _extract_json_payload(raw_response)
    return _normalize_result(parsed, run_id=run_id)


def _build_input_text(
    project: Any,
    files: Iterable[Any],
    instructions: str,
    user_notes: Optional[str],
    graph_context: Optional[Dict[str, Any]],
) -> str:
    sections: List[str] = []
    if project is not None:
        sections.append(
            "Project\nName: {name}\nDescription: {description}".format(
                name=getattr(project, "name", "Untitled project"),
                description=getattr(project, "description", "") or "",
            )
        )

    sections.append("Operator Instructions\n{instructions}".format(instructions=instructions.strip()))
    if user_notes:
        sections.append("User Notes\n{notes}".format(notes=user_notes.strip()))

    file_sections: List[str] = []
    for file_record in files:
        file_sections.append(_summarize_file(file_record))

    if file_sections:
        sections.append("Attached Files\n{files}".format(files="\n\n".join(file_sections)))

    if graph_context:
        sections.append(
            "Context Graph Evidence\n{graph}".format(
                graph=json.dumps(graph_context, indent=2, sort_keys=True)[:12000]
            )
        )

    sections.append(
        "Task\nInfer business entities, field meanings, a provisional semantic graph, employee"
        " clarification questions, and a concise reasoning summary."
    )
    return "\n\n".join(sections)


def _summarize_file(file_record: Any) -> str:
    metadata = getattr(file_record, "metadata", {}) or {}
    file_path = metadata.get("path")
    snippet = ""

    if file_path:
        path = Path(file_path)
        if path.exists():
            try:
                raw = path.read_text(encoding="utf-8")
                snippet = raw[:8000]
            except UnicodeDecodeError:
                snippet = path.read_bytes()[:2048].decode("utf-8", errors="replace")

    if not snippet:
        snippet = "No readable file contents were available."

    return (
        "File: {name}\nFilename: {filename}\nSize: {size}\nContent Preview:\n{snippet}".format(
            name=getattr(file_record, "name", ""),
            filename=getattr(file_record, "filename", ""),
            size=getattr(file_record, "size_bytes", 0),
            snippet=snippet,
        )
    )


def _create_response(payload: Dict[str, Any], api_key: str) -> Dict[str, Any]:
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    url = "{base}/responses".format(base=base_url.rstrip("/"))
    req = request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": "Bearer {token}".format(token=api_key),
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=120) as response:
            body = response.read().decode("utf-8")
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError("OpenAI Responses API error: {status} {body}".format(status=exc.code, body=body))
    except error.URLError as exc:
        raise RuntimeError("OpenAI Responses API request failed: {reason}".format(reason=exc.reason))

    return json.loads(body)


def _extract_json_payload(response_json: Dict[str, Any]) -> Dict[str, Any]:
    output_text = response_json.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return _loads_json(output_text)

    for output_item in response_json.get("output", []):
        for content_item in output_item.get("content", []):
            if isinstance(content_item.get("text"), str):
                return _loads_json(content_item["text"])
            if isinstance(content_item.get("json"), dict):
                return content_item["json"]

    raise RuntimeError("Could not find structured JSON in the OpenAI response.")


def _loads_json(value: str) -> Dict[str, Any]:
    candidate = value.strip()
    if candidate.startswith("```"):
        candidate = candidate.strip("`")
        if candidate.startswith("json"):
            candidate = candidate[4:].strip()
    parsed = json.loads(candidate)
    if not isinstance(parsed, dict):
        raise RuntimeError("Structured output was not a JSON object.")
    return parsed


def _normalize_result(payload: Dict[str, Any], run_id: Optional[str]) -> Dict[str, Any]:
    normalized = dict(payload)
    normalized.setdefault("entities", [])
    normalized.setdefault("fields", [])
    normalized.setdefault("inferred_meanings", [])
    normalized.setdefault("questions", [])
    normalized.setdefault("summary", "")

    graph = normalized.setdefault("graph", {})
    graph.setdefault("nodes", [])
    graph.setdefault("edges", [])

    confidence = normalized.setdefault("confidence", {})
    confidence.setdefault("overall", 0)
    confidence.setdefault("by_entity", {})
    if isinstance(confidence.get("by_entity"), list):
        confidence["by_entity"] = {
            item.get("entity", ""): item.get("confidence", 0)
            for item in confidence["by_entity"]
            if item.get("entity")
        }

    node_map: Dict[str, str] = {}
    for node in graph["nodes"]:
        label = node.get("label", "").strip()
        node_id = _slug(label) or uuid.uuid4().hex
        node["id"] = node_id
        if run_id:
            node["run_id"] = run_id
        node.setdefault("data", {})
        node.setdefault("metadata", {})
        node_map[label] = node_id

    for edge in graph["edges"]:
        source_label = edge.get("source", "").strip()
        target_label = edge.get("target", "").strip()
        edge["source"] = node_map.get(source_label, source_label)
        edge["target"] = node_map.get(target_label, target_label)
        edge["id"] = uuid.uuid4().hex
        if run_id:
            edge["run_id"] = run_id
        edge.setdefault("metadata", {})

    return normalized


def _slug(value: str) -> str:
    sanitized = "".join(char.lower() if char.isalnum() else "-" for char in value)
    parts = [part for part in sanitized.split("-") if part]
    return "-".join(parts)
