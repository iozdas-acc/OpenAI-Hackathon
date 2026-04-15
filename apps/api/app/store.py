from __future__ import annotations

import json
import os
import uuid
from hashlib import sha256
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Iterable, List, Optional

from pydantic import BaseModel

from .models import (
    ConnectionKind,
    ConnectionRole,
    DatabaseConnection,
    EventType,
    FileRecord,
    GraphEdge,
    GraphNode,
    GraphSnapshot,
    Project,
    Run,
    RunEvent,
    RunStatus,
    UnderstandResult,
)


def _model_dict(model: BaseModel) -> Dict[str, Any]:
    return json.loads(model.json())


def _new_id() -> str:
    return uuid.uuid4().hex


class LocalStore:
    STORE_ENV = "CODEX_STORE_DIR"  # configurable root path for persistence

    def __init__(self, data_dir: Optional[Path] = None) -> None:
        raw_dir = data_dir or os.getenv(self.STORE_ENV) or Path("data") / "codex-backend"
        self.base_dir = Path(raw_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._dict_paths: Dict[str, Path] = {
            "connections": self.base_dir / "connections.json",
            "projects": self.base_dir / "projects.json",
            "files": self.base_dir / "files.json",
            "runs": self.base_dir / "runs.json",
            "results": self.base_dir / "results.json",
        }
        self._list_paths: Dict[str, Path] = {
            "events": self.base_dir / "events.json",
            "graph_nodes": self.base_dir / "graph_nodes.json",
            "graph_edges": self.base_dir / "graph_edges.json",
        }
        self.snapshots_dir = self.base_dir / "snapshots"
        self.snapshots_dir.mkdir(exist_ok=True)
        self.uploads_dir = self.base_dir / "uploads"
        self.uploads_dir.mkdir(exist_ok=True)
        self._lock = Lock()

    def _read_dict(self, key: str) -> Dict[str, Any]:
        path = self._dict_paths[key]
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write_dict(self, key: str, payload: Dict[str, Any]) -> None:
        path = self._dict_paths[key]
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

    def _read_list(self, key: str) -> List[Dict[str, Any]]:
        path = self._list_paths[key]
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write_list(self, key: str, payload: Iterable[Dict[str, Any]]) -> None:
        path = self._list_paths[key]
        with path.open("w", encoding="utf-8") as handle:
            json.dump(list(payload), handle, indent=2)

    def create_project(
        self,
        name: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Project:
        project = Project(
            id=_new_id(),
            name=name,
            description=description,
            metadata=metadata or {},
        )
        with self._lock:
            data = self._read_dict("projects")
            data[project.id] = _model_dict(project)
            self._write_dict("projects", data)
        return project

    def create_connection(
        self,
        project_id: str,
        name: str,
        role: ConnectionRole,
        kind: ConnectionKind,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DatabaseConnection:
        connection = DatabaseConnection(
            id=_new_id(),
            project_id=project_id,
            name=name,
            role=role,
            kind=kind,
            config=config or {},
            metadata=metadata or {},
        )
        with self._lock:
            data = self._read_dict("connections")
            data[connection.id] = _model_dict(connection)
            self._write_dict("connections", data)
        return connection

    def get_connection(self, connection_id: str) -> Optional[DatabaseConnection]:
        with self._lock:
            data = self._read_dict("connections")
            raw = data.get(connection_id)
        return DatabaseConnection(**raw) if raw else None

    def list_connections(self, project_id: Optional[str] = None) -> List[DatabaseConnection]:
        with self._lock:
            records = list(self._read_dict("connections").values())
        connections = [DatabaseConnection(**raw) for raw in records]
        if project_id:
            connections = [entry for entry in connections if entry.project_id == project_id]
        return connections

    def get_project(self, project_id: str) -> Optional[Project]:
        with self._lock:
            data = self._read_dict("projects")
            raw = data.get(project_id)
        return Project(**raw) if raw else None

    def list_projects(self) -> List[Project]:
        with self._lock:
            records = list(self._read_dict("projects").values())
        return [Project(**raw) for raw in records]

    def update_project(
        self,
        project_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Project]:
        with self._lock:
            data = self._read_dict("projects")
            raw = data.get(project_id)
            if not raw:
                return None
            project = Project(**raw)
            updates: Dict[str, Any] = {}
            if name is not None:
                updates["name"] = name
            if description is not None:
                updates["description"] = description
            if metadata is not None:
                updates["metadata"] = metadata
            updates["updated_at"] = datetime.utcnow()
            project = project.copy(update=updates)
            data[project_id] = _model_dict(project)
            self._write_dict("projects", data)
        return project

    def delete_project(self, project_id: str) -> bool:
        with self._lock:
            data = self._read_dict("projects")
            if project_id not in data:
                return False
            data.pop(project_id)
            self._write_dict("projects", data)
        return True

    def create_file(
        self,
        project_id: str,
        name: str,
        filename: str,
        size_bytes: int,
        checksum: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FileRecord:
        record = FileRecord(
            id=_new_id(),
            project_id=project_id,
            name=name,
            filename=filename,
            size_bytes=size_bytes,
            checksum=checksum,
            metadata=metadata or {},
        )
        with self._lock:
            data = self._read_dict("files")
            data[record.id] = _model_dict(record)
            self._write_dict("files", data)
        return record

    def attach_file(
        self,
        project_id: str,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> FileRecord:
        project_dir = self.uploads_dir / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        file_id = _new_id()
        stored_name = "{file_id}_{filename}".format(file_id=file_id, filename=filename)
        file_path = project_dir / stored_name
        file_path.write_bytes(content)

        checksum = sha256(content).hexdigest()
        return self.create_file(
            project_id=project_id,
            name=filename,
            filename=filename,
            size_bytes=len(content),
            checksum=checksum,
            metadata={
                "content_type": content_type,
                "path": str(file_path),
            },
        )

    def get_file(self, file_id: str) -> Optional[FileRecord]:
        with self._lock:
            data = self._read_dict("files")
            raw = data.get(file_id)
        return FileRecord(**raw) if raw else None

    def list_files(self, project_id: Optional[str] = None) -> List[FileRecord]:
        with self._lock:
            records = list(self._read_dict("files").values())
        files = [FileRecord(**raw) for raw in records]
        if project_id:
            files = [record for record in files if record.project_id == project_id]
        return files

    def delete_file(self, file_id: str) -> bool:
        with self._lock:
            data = self._read_dict("files")
            if file_id not in data:
                return False
            data.pop(file_id)
            self._write_dict("files", data)
        return True

    def create_run(
        self,
        project_id: str,
        mode: str,
        instructions: str,
        user_notes: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Run:
        combined_metadata = metadata or {}
        if user_notes:
            combined_metadata = dict(combined_metadata)
            combined_metadata["user_notes"] = user_notes
        run = Run(
            id=_new_id(),
            project_id=project_id,
            mode=mode,
            instructions=instructions,
            metadata=combined_metadata,
        )
        with self._lock:
            data = self._read_dict("runs")
            data[run.id] = _model_dict(run)
            self._write_dict("runs", data)
        return run

    def get_run(self, run_id: str) -> Optional[Run]:
        with self._lock:
            data = self._read_dict("runs")
            raw = data.get(run_id)
        return Run(**raw) if raw else None

    def list_runs(self, project_id: Optional[str] = None) -> List[Run]:
        with self._lock:
            records = self._read_dict("runs").values()
        runs = [Run(**cast) for cast in records]
        if project_id:
            runs = [run for run in runs if run.project_id == project_id]
        return runs

    def update_run(
        self,
        run_id: str,
        status: Optional[RunStatus] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Run]:
        with self._lock:
            data = self._read_dict("runs")
            raw = data.get(run_id)
            if not raw:
                return None
            run = Run(**raw)
            updates: Dict[str, Any] = {}
            if status is not None:
                updates["status"] = status
            if started_at is not None:
                updates["started_at"] = started_at
            if completed_at is not None:
                updates["completed_at"] = completed_at
            if metadata is not None:
                updates["metadata"] = metadata
            elif error_message is not None:
                next_metadata = dict(run.metadata)
                next_metadata["error_message"] = error_message
                updates["metadata"] = next_metadata
            updates["updated_at"] = datetime.utcnow()
            run = run.copy(update=updates)
            data[run_id] = _model_dict(run)
            self._write_dict("runs", data)
        return run

    def update_run_status(
        self,
        run_id: str,
        status: str,
        error_message: Optional[str] = None,
    ) -> Optional[Run]:
        started_at = datetime.utcnow() if status == RunStatus.RUNNING.value else None
        completed_at = datetime.utcnow() if status in (RunStatus.COMPLETED.value, RunStatus.FAILED.value) else None
        return self.update_run(
            run_id=run_id,
            status=RunStatus(status),
            started_at=started_at,
            completed_at=completed_at,
            error_message=error_message,
        )

    def merge_run_metadata(self, run_id: str, patch: Dict[str, Any]) -> Optional[Run]:
        run = self.get_run(run_id)
        if run is None:
            return None

        merged = dict(run.metadata)
        merged.update(patch)
        return self.update_run(run_id=run_id, metadata=merged)

    def append_event(
        self,
        run_id: str,
        project_id: str,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> RunEvent:
        event = RunEvent(
            id=_new_id(),
            run_id=run_id,
            project_id=project_id,
            type=EventType(event_type),
            payload=payload or {},
        )
        with self._lock:
            events = self._read_list("events")
            events.append(_model_dict(event))
            self._write_list("events", events)
        return event

    def list_events(self, run_id: Optional[str] = None, event_type: Optional[EventType] = None) -> List[RunEvent]:
        with self._lock:
            events = self._read_list("events")
        parsed = [RunEvent(**event) for event in events]
        if run_id:
            parsed = [entry for entry in parsed if entry.run_id == run_id]
        if event_type:
            parsed = [entry for entry in parsed if entry.type == event_type]
        return parsed

    def add_graph_node(
        self,
        run_id: str,
        label: str,
        type: str,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> GraphNode:
        node = GraphNode(
            id=_new_id(),
            run_id=run_id,
            label=label,
            type=type,
            data=data or {},
            metadata=metadata or {},
        )
        with self._lock:
            nodes = self._read_list("graph_nodes")
            nodes.append(_model_dict(node))
            self._write_list("graph_nodes", nodes)
        return node

    def add_graph_edge(
        self,
        run_id: str,
        source: str,
        target: str,
        relation: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> GraphEdge:
        edge = GraphEdge(
            id=_new_id(),
            run_id=run_id,
            source=source,
            target=target,
            relation=relation,
            metadata=metadata or {},
        )
        with self._lock:
            edges = self._read_list("graph_edges")
            edges.append(_model_dict(edge))
            self._write_list("graph_edges", edges)
        return edge

    def list_graph_nodes(self, run_id: Optional[str] = None) -> List[GraphNode]:
        with self._lock:
            nodes = self._read_list("graph_nodes")
        parsed = [GraphNode(**entry) for entry in nodes]
        if run_id:
            parsed = [node for node in parsed if node.run_id == run_id]
        return parsed

    def list_graph_edges(self, run_id: Optional[str] = None) -> List[GraphEdge]:
        with self._lock:
            edges = self._read_list("graph_edges")
        parsed = [GraphEdge(**entry) for entry in edges]
        if run_id:
            parsed = [edge for edge in parsed if edge.run_id == run_id]
        return parsed

    def save_result(self, result: UnderstandResult) -> UnderstandResult:
        with self._lock:
            data = self._read_dict("results")
            data[result.run_id] = _model_dict(result)
            self._write_dict("results", data)
        return result

    def get_result(self, run_id: str) -> Optional[UnderstandResult]:
        with self._lock:
            data = self._read_dict("results")
            raw = data.get(run_id)
        return UnderstandResult(**raw) if raw else None

    def _next_snapshot_version(self, run_id: str) -> int:
        pattern = f"{run_id}__*.json"
        files = list(self.snapshots_dir.glob(pattern))
        versions: List[int] = []
        for path in files:
            parts = path.stem.split("__")
            if len(parts) != 2:
                continue
            suffix = parts[1]
            if suffix.isdigit():
                versions.append(int(suffix))
        return max(versions, default=0) + 1

    def save_graph_snapshot(self, snapshot: GraphSnapshot) -> GraphSnapshot:
        with self._lock:
            version = self._next_snapshot_version(snapshot.run_id)
            snapshot = snapshot.copy(update={"version": version, "created_at": datetime.utcnow()})
            target = self.snapshots_dir / f"{snapshot.run_id}__{snapshot.version}.json"
            target.write_text(snapshot.json(), encoding="utf-8")
        return snapshot

    def list_graph_snapshots(self, run_id: str) -> List[GraphSnapshot]:
        with self._lock:
            files = sorted(self.snapshots_dir.glob(f"{run_id}__*.json"))
        snapshots: List[GraphSnapshot] = []
        for path in files:
            snapshots.append(GraphSnapshot.parse_file(path))
        return snapshots

    def get_latest_graph_snapshot(self, run_id: str) -> Optional[GraphSnapshot]:
        snapshots = self.list_graph_snapshots(run_id)
        if not snapshots:
            return None
        return snapshots[-1]


FileBackedStore = LocalStore
