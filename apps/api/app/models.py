from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_CRAWL_REVIEW = "awaiting_crawl_review"
    AWAITING_REASONING_REVIEW = "awaiting_reasoning_review"
    AWAITING_MAPPING_REVIEW = "awaiting_mapping_review"
    MIGRATION_READY = "migration_ready"
    MIGRATING = "migrating"
    MIGRATION_COMPLETED = "migration_completed"
    COMPLETED = "completed"
    FAILED = "failed"


class EventType(str, Enum):
    RUN_CREATED = "run_created"
    FILE_ATTACHED = "file_attached"
    CODEX_STARTED = "codex_started"
    REASONING_SUMMARY = "reasoning_summary"
    NODE_CREATED = "node_created"
    EDGE_CREATED = "edge_created"
    QUESTION_RAISED = "question_raised"
    CONFIDENCE_CHANGED = "confidence_changed"
    SOURCE_CRAWL_STARTED = "source_crawl_started"
    SOURCE_CRAWL_COMPLETED = "source_crawl_completed"
    TARGET_CRAWL_STARTED = "target_crawl_started"
    TARGET_CRAWL_COMPLETED = "target_crawl_completed"
    CONTEXT_GRAPH_BUILT = "context_graph_built"
    CRAWL_REVIEW_REQUIRED = "crawl_review_required"
    SEMANTIC_REASONING_STARTED = "semantic_reasoning_started"
    SEMANTIC_REASONING_COMPLETED = "semantic_reasoning_completed"
    REASONING_REVIEW_REQUIRED = "reasoning_review_required"
    MAPPINGS_PROPOSED = "mappings_proposed"
    MAPPING_REVIEW_REQUIRED = "mapping_review_required"
    REVIEW_SUBMITTED = "review_submitted"
    MIGRATION_READY = "migration_ready"
    MIGRATION_TRIGGERED = "migration_triggered"
    MIGRATION_COMPLETED = "migration_completed"
    RUN_COMPLETED = "run_completed"
    RUN_FAILED = "run_failed"


class ConnectionRole(str, Enum):
    SOURCE = "source"
    TARGET = "target"


class ConnectionKind(str, Enum):
    ORACLE = "oracle"
    SUPABASE = "supabase"
    POSTGRES = "postgres"


class ReviewType(str, Enum):
    CRAWL = "crawl"
    REASONING = "reasoning"
    MAPPINGS = "mappings"


class ReviewDecision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    DEFER = "defer"
    REQUEST_CHANGES = "request_changes"


class Project(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class FileRecord(BaseModel):
    id: str
    project_id: str
    name: str
    filename: str
    size_bytes: int
    checksum: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


class DatabaseConnection(BaseModel):
    id: str
    project_id: str
    name: str
    role: ConnectionRole
    kind: ConnectionKind
    config: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Run(BaseModel):
    id: str
    project_id: str
    mode: str
    instructions: str
    status: RunStatus = RunStatus.PENDING
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class RunEvent(BaseModel):
    id: str
    run_id: str
    project_id: str
    type: EventType
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class GraphNode(BaseModel):
    id: str
    run_id: str
    label: str
    type: str
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class GraphEdge(BaseModel):
    id: str
    run_id: str
    source: str
    target: str
    relation: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class GraphSnapshot(BaseModel):
    run_id: str
    version: int = 1
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Entity(BaseModel):
    name: str
    description: Optional[str] = None
    confidence: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FieldDescriptor(BaseModel):
    name: str
    entity: Optional[str] = None
    semantic_type: Optional[str] = None
    description: Optional[str] = None
    confidence: Optional[float] = None


class InferredMeaning(BaseModel):
    subject: str
    meaning: str
    confidence: Optional[float] = None


class Question(BaseModel):
    prompt: str
    context: Optional[str] = None
    severity: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ConfidenceSummary(BaseModel):
    overall: float = 0.0
    by_entity: Dict[str, float] = Field(default_factory=dict)


class UnderstandResult(BaseModel):
    run_id: str
    summary: str = ""
    entities: List[Entity] = Field(default_factory=list)
    fields: List[FieldDescriptor] = Field(default_factory=list)
    inferred_meanings: List[InferredMeaning] = Field(default_factory=list)
    questions: List[Question] = Field(default_factory=list)
    confidence: ConfidenceSummary = Field(default_factory=ConfidenceSummary)
    graph_snapshot: Optional[GraphSnapshot] = None
    produced_at: datetime = Field(default_factory=datetime.utcnow)
