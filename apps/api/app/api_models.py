from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from .models import ConnectionKind, ConnectionRole, ReviewDecision


class CreateProjectRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=4000)


class CreateRunRequest(BaseModel):
    mode: str = Field(default="understand")
    instructions: str = Field(min_length=1, max_length=12000)
    user_notes: Optional[str] = Field(default=None, max_length=12000)
    source_connection_id: Optional[str] = Field(default=None, min_length=1, max_length=200)
    target_connection_id: Optional[str] = Field(default=None, min_length=1, max_length=200)


class CreateConnectionRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    role: ConnectionRole
    kind: ConnectionKind
    config: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SubmitReviewRequest(BaseModel):
    decision: ReviewDecision
    notes: Optional[str] = Field(default=None, max_length=4000)


class TriggerMigrationRequest(BaseModel):
    notes: Optional[str] = Field(default=None, max_length=4000)


class ErrorResponse(BaseModel):
    detail: str


CodexActionName = Literal[
    "explain_mapping",
    "compare_alternatives",
    "draft_reviewer_note",
    "approve_mapping",
    "reject_mapping",
    "rerun_reasoning",
    "prepare_package",
]


class CodexChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"] = Field(default="user")
    content: str = Field(min_length=1, max_length=24000)


class CodexActionContext(BaseModel):
    run_id: Optional[str] = Field(default=None, max_length=200)
    project_id: Optional[str] = Field(default=None, max_length=200)
    case_id: Optional[str] = Field(default=None, max_length=200)
    selected_mapping_id: Optional[str] = Field(default=None, max_length=200)
    requested_action: Optional[CodexActionName] = Field(default=None)
    available_actions: List[CodexActionName] = Field(default_factory=list)
    ui_state: Dict[str, Any] = Field(default_factory=dict)


class CodexChatStreamRequest(BaseModel):
    messages: List[CodexChatMessage] = Field(min_length=1, max_length=100)
    action_context: Optional[CodexActionContext] = Field(default=None)
    session_id: Optional[str] = Field(default=None, max_length=200)
    model: Optional[str] = Field(default=None, max_length=200)


class CodexChatStreamEvent(BaseModel):
    type: str
    data: Dict[str, Any] = Field(default_factory=dict)
