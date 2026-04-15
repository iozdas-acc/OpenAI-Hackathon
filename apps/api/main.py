from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator, Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from app.api_models import (  # noqa: E402
    CodexChatStreamRequest,
    CreateConnectionRequest,
    CreateProjectRequest,
    CreateRunRequest,
    SubmitReviewRequest,
    TriggerMigrationRequest,
)
from app.codex_chat import stream_codex_chat  # noqa: E402
from app.runtime import EventHub  # noqa: E402

try:  # noqa: E402
    from app.models import (
        EventType,
        GraphSnapshot,
        ReviewDecision,
        ReviewType,
        RunStatus,
        UnderstandResult,
    )
    from app.store import FileBackedStore
except ImportError:  # pragma: no cover - worker-owned files land later in the turn
    FileBackedStore = None  # type: ignore[assignment]
    EventType = None  # type: ignore[assignment]
    GraphSnapshot = None  # type: ignore[assignment]
    ReviewDecision = None  # type: ignore[assignment]
    ReviewType = None  # type: ignore[assignment]
    RunStatus = None  # type: ignore[assignment]
    UnderstandResult = None  # type: ignore[assignment]

try:  # noqa: E402
    from services.orchestrator.workflow import run_understand_workflow
except ImportError:  # pragma: no cover - worker-owned files land later in the turn
    run_understand_workflow = None  # type: ignore[assignment]

try:  # noqa: E402
    from services.context_graph_builder import build_context_graph, propose_mapping_candidates
    from services.crawlers import crawl_oracle_source, crawl_supabase_target
except ImportError:  # pragma: no cover - worker-owned files land later in the turn
    build_context_graph = None  # type: ignore[assignment]
    propose_mapping_candidates = None  # type: ignore[assignment]
    crawl_oracle_source = None  # type: ignore[assignment]
    crawl_supabase_target = None  # type: ignore[assignment]

try:  # noqa: E402
    from services.migration.supabase import execute_supabase_migration
except ImportError:  # pragma: no cover - worker-owned files land later in the turn
    execute_supabase_migration = None  # type: ignore[assignment]


def _default_data_dir() -> Path:
    env_value = os.getenv("SEMANTIC_API_DATA_DIR") or os.getenv("CODEX_STORE_DIR")
    if env_value:
        return Path(env_value)
    return Path(__file__).resolve().parent / ".data"


app = FastAPI(title="Semantic Translation API")
app.state.event_hub = EventHub()
app.state.store = None

REVIEW_STATUS_BY_TYPE = {
    "crawl": "awaiting_crawl_review",
    "reasoning": "awaiting_reasoning_review",
    "mappings": "awaiting_mapping_review",
}

REVIEW_METADATA_KEYS = {
    "crawl": "crawl_review",
    "reasoning": "reasoning_review",
    "mappings": "mapping_review",
}


@app.on_event("startup")
def startup() -> None:
    if FileBackedStore is None:
        raise RuntimeError("FileBackedStore is unavailable; app.store failed to import.")

    app.state.store = FileBackedStore(_default_data_dir())


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/codex/chat/stream")
async def codex_chat_stream(payload: CodexChatStreamRequest) -> StreamingResponse:
    async def stream() -> AsyncIterator[str]:
        async for chunk in stream_codex_chat(
            payload,
            api_key=os.getenv("OPENAI_API_KEY"),
            model=payload.model or os.getenv("OPENAI_CODEX_MODEL"),
        ):
            yield chunk

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/projects")
def create_project(payload: CreateProjectRequest) -> Any:
    project = app.state.store.create_project(
        name=payload.name,
        description=payload.description,
    )
    return project


@app.get("/projects/{project_id}/connections")
def list_project_connections(project_id: str) -> Any:
    store = app.state.store
    project = store.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return store.list_connections(project_id)


@app.post("/projects/{project_id}/connections")
def create_project_connection(project_id: str, payload: CreateConnectionRequest) -> Any:
    store = app.state.store
    project = store.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    connection = store.create_connection(
        project_id=project_id,
        name=payload.name,
        role=payload.role,
        kind=payload.kind,
        config=payload.config,
        metadata=payload.metadata,
    )
    return connection


@app.post("/projects/{project_id}/files")
async def upload_project_file(project_id: str, request: Request) -> Any:
    store = app.state.store
    project = store.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    filename = request.headers.get("x-filename")
    if not filename:
        raise HTTPException(status_code=400, detail="Missing x-filename header.")

    content = await request.body()
    if not content:
        raise HTTPException(status_code=400, detail="Request body is empty.")

    file_record = store.attach_file(
        project_id=project_id,
        filename=filename,
        content_type=request.headers.get("content-type", "application/octet-stream"),
        content=content,
    )
    return file_record


@app.get("/projects/{project_id}/runs")
def list_project_runs(project_id: str) -> Any:
    store = app.state.store
    project = store.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return store.list_runs(project_id)


@app.post("/projects/{project_id}/runs")
async def create_run(project_id: str, payload: CreateRunRequest) -> Any:
    if payload.mode != "understand":
        raise HTTPException(status_code=400, detail="Only 'understand' mode is supported.")

    store = app.state.store
    project = store.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    run_metadata: Dict[str, Any] = {}
    if payload.source_connection_id:
        source_connection = store.get_connection(payload.source_connection_id)
        if source_connection is None or source_connection.project_id != project_id:
            raise HTTPException(status_code=404, detail="Source connection not found.")
        run_metadata["source_connection_id"] = payload.source_connection_id

    if payload.target_connection_id:
        target_connection = store.get_connection(payload.target_connection_id)
        if target_connection is None or target_connection.project_id != project_id:
            raise HTTPException(status_code=404, detail="Target connection not found.")
        run_metadata["target_connection_id"] = payload.target_connection_id

    run = store.create_run(
        project_id=project_id,
        mode=payload.mode,
        instructions=payload.instructions,
        user_notes=payload.user_notes,
        metadata=run_metadata,
    )

    created_event = store.append_event(
        run_id=run.id,
        project_id=project_id,
        event_type="run_created",
        payload={
            "mode": payload.mode,
            "source_connection_id": payload.source_connection_id,
            "target_connection_id": payload.target_connection_id,
        },
    )
    await _publish_event(created_event)

    asyncio.create_task(
        _execute_understand_run(
            project_id=project_id,
            run_id=run.id,
            instructions=payload.instructions,
            user_notes=payload.user_notes,
        )
    )

    return run


@app.post("/runs/{run_id}/reviews/{review_type}")
async def submit_review(run_id: str, review_type: ReviewType, payload: SubmitReviewRequest) -> Any:
    store = app.state.store
    run = store.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found.")

    expected_status = REVIEW_STATUS_BY_TYPE[review_type.value]
    if run.status.value != expected_status:
        raise HTTPException(
            status_code=409,
            detail="Run is not awaiting this review checkpoint.",
        )

    metadata_key = REVIEW_METADATA_KEYS[review_type.value]
    review_payload = {
        "decision": payload.decision.value,
        "notes": payload.notes,
        "submitted_at": _utcnow(),
    }
    reviews = dict(run.metadata.get("reviews", {}))
    reviews[metadata_key] = review_payload
    updated_run = store.merge_run_metadata(run_id, {"reviews": reviews})
    if updated_run is None:
        raise HTTPException(status_code=404, detail="Run not found.")

    submitted_event = store.append_event(
        run_id=run_id,
        project_id=run.project_id,
        event_type="review_submitted",
        payload={"review_type": review_type.value, **review_payload},
    )
    await _publish_event(submitted_event)

    if payload.decision == ReviewDecision.APPROVE:
        if review_type == ReviewType.CRAWL:
            store.update_run_status(run_id, status=RunStatus.RUNNING.value)
            asyncio.create_task(_continue_after_crawl_review(run_id))
        elif review_type == ReviewType.REASONING:
            store.update_run_status(run_id, status=RunStatus.RUNNING.value)
            asyncio.create_task(_continue_after_reasoning_review(run_id))
        else:
            store.update_run_status(run_id, status=RunStatus.MIGRATION_READY.value)
            migration_ready_event = store.append_event(
                run_id=run_id,
                project_id=run.project_id,
                event_type="migration_ready",
                payload={"approved_review": review_type.value},
            )
            await _publish_event(migration_ready_event)

    return store.get_run(run_id)


@app.post("/runs/{run_id}/migrate")
async def trigger_migration(run_id: str, payload: TriggerMigrationRequest) -> Any:
    store = app.state.store
    run = store.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found.")

    if run.status != RunStatus.MIGRATION_READY:
        raise HTTPException(status_code=409, detail="Run is not ready for migration.")

    reviews = run.metadata.get("reviews", {})
    required_reviews = [
        "crawl_review",
        "reasoning_review",
        "mapping_review",
    ]
    missing = [
        key for key in required_reviews if reviews.get(key, {}).get("decision") != ReviewDecision.APPROVE.value
    ]
    if missing:
        raise HTTPException(
            status_code=409,
            detail="All review checkpoints must be approved before migration.",
        )

    snapshot = store.get_latest_graph_snapshot(run_id)
    if snapshot is None:
        raise HTTPException(status_code=409, detail="No graph snapshot is available for migration.")

    store.update_run_status(run_id, status=RunStatus.MIGRATING.value)
    if execute_supabase_migration is None:
        raise HTTPException(status_code=500, detail="Migration executor import failed.")

    store.merge_run_metadata(
        run_id,
        {
            "migration_request": {
                "notes": payload.notes,
                "requested_at": _utcnow(),
            }
        },
    )
    await _publish_named_event(
        run_id,
        run.project_id,
        "migration_triggered",
        {"notes": payload.notes},
    )

    migration_result = await asyncio.to_thread(execute_supabase_migration, run, snapshot)
    store.update_run_status(run_id, status=RunStatus.MIGRATION_COMPLETED.value)
    await _publish_named_event(
        run_id,
        run.project_id,
        "migration_completed",
        migration_result,
    )

    return {
        "run_id": run_id,
        "status": RunStatus.MIGRATION_COMPLETED,
        "detail": "Migration completed in mock mode.",
        "result": migration_result,
    }


@app.get("/runs/{run_id}")
def get_run(run_id: str) -> Any:
    store = app.state.store
    run = store.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found.")

    result = store.get_result(run_id)
    graph = store.get_latest_graph_snapshot(run_id)
    events = store.list_events(run_id)

    return {
        "run": run,
        "result": result,
        "graph": graph,
        "events": events,
    }


@app.get("/runs/{run_id}/events")
async def stream_run_events(run_id: str) -> StreamingResponse:
    store = app.state.store
    run = store.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found.")

    async def event_stream() -> AsyncIterator[str]:
        historical_events = store.list_events(run_id)
        for event in historical_events:
            yield _format_sse_event(event)

        async with app.state.event_hub.subscribe(run_id) as queue:
            while True:
                message = await queue.get()
                yield message

    return StreamingResponse(event_stream(), media_type="text/event-stream")


async def _execute_understand_run(
    project_id: str,
    run_id: str,
    instructions: str,
    user_notes: Optional[str],
) -> None:
    store = app.state.store

    store.update_run_status(run_id, status="running")
    project = store.get_project(project_id)
    files = store.list_files(project_id)
    for file_record in files:
        file_event = store.append_event(
            run_id=run_id,
            project_id=project_id,
            event_type="file_attached",
            payload={
                "file_id": file_record.id,
                "filename": file_record.filename,
                "size_bytes": file_record.size_bytes,
            },
        )
        await _publish_event(file_event)

    try:
        source_connection, target_connection = _resolve_run_connections(project_id=project_id, run_id=run_id)
        if source_connection is None or target_connection is None:
            raise RuntimeError("Runs require both source and target connections.")
        if getattr(target_connection, "kind", None) is None or target_connection.kind.value not in ("supabase", "postgres"):
            raise RuntimeError("Target connection must be Supabase or Postgres.")
        if crawl_oracle_source is None or crawl_supabase_target is None or build_context_graph is None:
            raise RuntimeError("crawler or context graph imports failed")

        await _publish_named_event(run_id, project_id, "source_crawl_started", {"connection_id": source_connection.id})
        source_profile = await asyncio.to_thread(crawl_oracle_source, source_connection, files)
        await _publish_named_event(
            run_id,
            project_id,
            "source_crawl_completed",
            {"table_count": len(source_profile.get("tables", []))},
        )

        await _publish_named_event(run_id, project_id, "target_crawl_started", {"connection_id": target_connection.id})
        try:
            target_profile = await asyncio.to_thread(crawl_supabase_target, target_connection)
        except Exception as exc:
            await _publish_named_event(
                run_id,
                project_id,
                "run_failed",
                {"stage": "target_crawl", "error": str(exc)},
            )
            raise
        await _publish_named_event(
            run_id,
            project_id,
            "target_crawl_completed",
            {
                "table_count": len(target_profile.get("tables", [])),
                "warning_count": len(target_profile.get("warnings", [])),
            },
        )

        crawl_graph = await asyncio.to_thread(
            build_context_graph,
            run_id,
            source_profile,
            target_profile,
        )
        store.save_graph_snapshot(_build_graph_snapshot(run_id, crawl_graph))
        await _record_graph_activity(run_id, project_id, crawl_graph)
        await _publish_named_event(
            run_id,
            project_id,
            "context_graph_built",
            {
                "node_count": len(crawl_graph.get("nodes", [])),
                "edge_count": len(crawl_graph.get("edges", [])),
            },
        )

        store.merge_run_metadata(
            run_id,
            {
                "crawl_artifacts": {
                    "source_profile": source_profile,
                    "target_profile": target_profile,
                }
            },
        )
        store.update_run_status(run_id, status=RunStatus.AWAITING_CRAWL_REVIEW.value)
        await _publish_named_event(run_id, project_id, "crawl_review_required", {"status": "awaiting_crawl_review"})
    except Exception as exc:  # pragma: no cover - exercised in live integration
        store.update_run_status(run_id, status="failed", error_message=str(exc))
        failed_event = store.append_event(
            run_id=run_id,
            project_id=project_id,
            event_type="run_failed",
            payload={"error": str(exc)},
        )
        await _publish_event(failed_event)


async def _publish_event(event: Any) -> None:
    run_id = getattr(event, "run_id", None)
    if not run_id:
        return
    await app.state.event_hub.publish(run_id, _format_sse_event(event))


async def _publish_named_event(run_id: str, project_id: str, event_type: str, payload: Dict[str, Any]) -> None:
    event = app.state.store.append_event(
        run_id=run_id,
        project_id=project_id,
        event_type=event_type,
        payload=payload,
    )
    await _publish_event(event)


async def _continue_after_crawl_review(run_id: str) -> None:
    store = app.state.store
    run = store.get_run(run_id)
    if run is None:
        return

    project = store.get_project(run.project_id)
    files = store.list_files(run.project_id)
    snapshot = store.get_latest_graph_snapshot(run_id)
    if project is None or snapshot is None:
        store.update_run_status(run_id, status=RunStatus.FAILED.value, error_message="Missing crawl artifacts.")
        return

    try:
        if run_understand_workflow is None:
            raise RuntimeError("orchestrator workflow import failed")

        await _publish_named_event(
            run_id,
            run.project_id,
            "semantic_reasoning_started",
            {"model": os.getenv("OPENAI_CODEX_MODEL", "gpt-5-codex")},
        )
        workflow_output = await asyncio.to_thread(
            run_understand_workflow,
            project=project,
            files=files,
            instructions=run.instructions,
            user_notes=run.metadata.get("user_notes"),
            run_id=run_id,
            graph_context={"nodes": [node.dict() for node in snapshot.nodes], "edges": [edge.dict() for edge in snapshot.edges]},
        )

        result = _coerce_result_payload(workflow_output)
        reasoning_graph = result.get("graph", {})
        merged_graph = _merge_graph_payloads(
            {"nodes": [node.dict() for node in snapshot.nodes], "edges": [edge.dict() for edge in snapshot.edges]},
            reasoning_graph,
        )
        result["graph"] = merged_graph

        store.save_result(_build_understand_result(run_id, result))
        store.save_graph_snapshot(_build_graph_snapshot(run_id, merged_graph))

        await _record_reasoning_outputs(run_id, run.project_id, result, reasoning_graph)
        await _publish_named_event(run_id, run.project_id, "semantic_reasoning_completed", {"status": "ok"})
        store.update_run_status(run_id, status=RunStatus.AWAITING_REASONING_REVIEW.value)
        await _publish_named_event(
            run_id,
            run.project_id,
            "reasoning_review_required",
            {"status": "awaiting_reasoning_review"},
        )
    except Exception as exc:  # pragma: no cover - exercised in live integration
        store.update_run_status(run_id, status=RunStatus.FAILED.value, error_message=str(exc))
        await _publish_named_event(run_id, run.project_id, "run_failed", {"error": str(exc)})


async def _continue_after_reasoning_review(run_id: str) -> None:
    store = app.state.store
    run = store.get_run(run_id)
    snapshot = store.get_latest_graph_snapshot(run_id)
    if run is None or snapshot is None:
        return

    try:
        if propose_mapping_candidates is None:
            raise RuntimeError("mapping candidate builder import failed")

        mapping_graph = await asyncio.to_thread(
            propose_mapping_candidates,
            run_id,
            {"nodes": [node.dict() for node in snapshot.nodes], "edges": [edge.dict() for edge in snapshot.edges]},
        )
        merged_graph = _merge_graph_payloads(
            {"nodes": [node.dict() for node in snapshot.nodes], "edges": [edge.dict() for edge in snapshot.edges]},
            mapping_graph,
        )
        store.save_graph_snapshot(_build_graph_snapshot(run_id, merged_graph))
        await _record_graph_activity(run_id, run.project_id, mapping_graph)
        await _publish_named_event(
            run_id,
            run.project_id,
            "mappings_proposed",
            {"candidate_count": len(mapping_graph.get("nodes", []))},
        )
        store.update_run_status(run_id, status=RunStatus.AWAITING_MAPPING_REVIEW.value)
        await _publish_named_event(
            run_id,
            run.project_id,
            "mapping_review_required",
            {"status": "awaiting_mapping_review"},
        )
    except Exception as exc:  # pragma: no cover - exercised in live integration
        store.update_run_status(run_id, status=RunStatus.FAILED.value, error_message=str(exc))
        await _publish_named_event(run_id, run.project_id, "run_failed", {"error": str(exc)})


def _utcnow() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _resolve_run_connections(project_id: str, run_id: str) -> tuple[Any, Any]:
    store = app.state.store
    run = store.get_run(run_id)
    if run is None:
        return None, None

    source_id = run.metadata.get("source_connection_id")
    target_id = run.metadata.get("target_connection_id")
    source_connection = store.get_connection(source_id) if source_id else None
    target_connection = store.get_connection(target_id) if target_id else None
    if source_connection is not None and source_connection.project_id != project_id:
        source_connection = None
    if target_connection is not None and target_connection.project_id != project_id:
        target_connection = None
    return source_connection, target_connection


async def _record_graph_activity(run_id: str, project_id: str, graph: Dict[str, Any]) -> None:
    for node in graph.get("nodes", []):
        await _publish_named_event(run_id, project_id, "node_created", node)
    for edge in graph.get("edges", []):
        await _publish_named_event(run_id, project_id, "edge_created", edge)


async def _record_reasoning_outputs(
    run_id: str,
    project_id: str,
    result: Dict[str, Any],
    reasoning_graph: Dict[str, Any],
) -> None:
    summary = result.get("summary", "")
    if summary:
        await _publish_named_event(run_id, project_id, "reasoning_summary", {"summary": summary})

    await _record_graph_activity(run_id, project_id, reasoning_graph)

    for question in result.get("questions", []):
        await _publish_named_event(run_id, project_id, "question_raised", question)

    confidence = result.get("confidence", {})
    if confidence:
        await _publish_named_event(run_id, project_id, "confidence_changed", confidence)


def _merge_graph_payloads(base_graph: Dict[str, Any], overlay_graph: Dict[str, Any]) -> Dict[str, Any]:
    nodes: Dict[str, Dict[str, Any]] = {}
    edges: Dict[str, Dict[str, Any]] = {}

    for node in base_graph.get("nodes", []) + overlay_graph.get("nodes", []):
        node_id = node.get("id") or node.get("label")
        if not node_id:
            continue
        nodes[node_id] = node

    for edge in base_graph.get("edges", []) + overlay_graph.get("edges", []):
        key = "{source}:{target}:{relation}".format(
            source=edge.get("source", ""),
            target=edge.get("target", ""),
            relation=edge.get("relation", ""),
        )
        edges[key] = edge

    return {"nodes": list(nodes.values()), "edges": list(edges.values())}


def _format_sse_event(event: Any) -> str:
    if hasattr(event, "json"):
        payload = json.loads(event.json())
    elif hasattr(event, "model_dump_json"):
        payload = json.loads(event.model_dump_json())
    elif hasattr(event, "model_dump"):
        payload = event.model_dump(mode="json")
    elif hasattr(event, "dict"):
        payload = event.dict()
    else:
        payload = dict(event)

    event_type = payload.get("type", "message")
    return "event: {event}\ndata: {data}\n\n".format(
        event=str(event_type),
        data=json.dumps(payload),
    )


def _coerce_result_payload(workflow_output: Any) -> Dict[str, Any]:
    if hasattr(workflow_output, "model_dump"):
        payload = workflow_output.model_dump()
    elif hasattr(workflow_output, "dict"):
        payload = workflow_output.dict()
    elif isinstance(workflow_output, dict):
        payload = workflow_output
    else:
        raise RuntimeError("Unexpected workflow output shape.")

    required_keys = [
        "entities",
        "fields",
        "inferred_meanings",
        "questions",
        "graph",
        "confidence",
        "summary",
    ]
    for key in required_keys:
        if key == "graph":
            payload.setdefault(key, {"nodes": [], "edges": []})
        elif key == "confidence":
            payload.setdefault(key, {"overall": 0, "by_entity": {}})
        elif key == "summary":
            payload.setdefault(key, "")
        else:
            payload.setdefault(key, [])

    if not isinstance(payload.get("graph"), dict):
        payload["graph"] = {"nodes": [], "edges": []}
    payload["graph"].setdefault("nodes", [])
    payload["graph"].setdefault("edges", [])

    if not isinstance(payload.get("confidence"), dict):
        payload["confidence"] = {"overall": 0, "by_entity": {}}
    payload["confidence"].setdefault("overall", 0)
    payload["confidence"].setdefault("by_entity", {})

    if not isinstance(payload.get("summary"), str):
        payload["summary"] = str(payload["summary"])

    return payload


def _build_graph_snapshot(run_id: str, graph: Dict[str, Any]) -> Any:
    if GraphSnapshot is None:
        raise RuntimeError("GraphSnapshot is unavailable.")

    return GraphSnapshot(
        run_id=run_id,
        nodes=graph.get("nodes", []),
        edges=graph.get("edges", []),
    )


def _build_understand_result(run_id: str, payload: Dict[str, Any]) -> Any:
    if UnderstandResult is None:
        raise RuntimeError("UnderstandResult is unavailable.")

    result_payload = dict(payload)
    graph_snapshot = _build_graph_snapshot(run_id, result_payload.pop("graph", {}))
    result_payload["run_id"] = run_id
    result_payload["graph_snapshot"] = graph_snapshot
    return UnderstandResult(**result_payload)
