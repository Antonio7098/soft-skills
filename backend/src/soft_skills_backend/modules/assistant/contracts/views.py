"""Assistant API view contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from soft_skills_backend.modules.assistant.domain.models import (
    AssistantMessageRole,
    AssistantSessionStatus,
    AssistantToolCallStatus,
    AssistantTurnStatus,
)


class AssistantMessageView(BaseModel):
    id: str
    turn_id: str
    role: AssistantMessageRole
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class AssistantToolCallView(BaseModel):
    id: str
    turn_id: str
    tool_name: str
    status: AssistantToolCallStatus
    args: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] | None = None
    error_code: str | None = None
    error_message: str | None = None
    child_run_id: str | None = None
    started_at: datetime
    completed_at: datetime | None = None


class AssistantTurnView(BaseModel):
    id: str
    session_id: str
    workflow_id: str
    request_id: str | None = None
    trace_id: str | None = None
    pipeline_run_id: str | None = None
    status: AssistantTurnStatus
    stream_token: str
    last_error_code: str | None = None
    cancel_reason: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
    user_message_id: str | None = None
    assistant_message_id: str | None = None
    messages: list[AssistantMessageView] = Field(default_factory=list)
    tool_calls: list[AssistantToolCallView] = Field(default_factory=list)


class AssistantSessionView(BaseModel):
    id: str
    user_id: str
    title: str | None = None
    status: AssistantSessionStatus
    created_at: datetime
    updated_at: datetime
    turns: list[AssistantTurnView] = Field(default_factory=list)
    messages: list[AssistantMessageView] = Field(default_factory=list)
