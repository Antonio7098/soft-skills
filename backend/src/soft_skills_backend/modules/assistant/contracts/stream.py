"""Assistant websocket event contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AssistantStreamEvent(BaseModel):
    event_id: str
    session_id: str
    type: str
    turn_id: str
    trace_id: str | None = None
    workflow_id: str | None = None
    sequence_number: int
    emitted_at: datetime
    payload: dict[str, Any] = Field(default_factory=dict)


class AssistantStreamControlMessage(BaseModel):
    type: str
    reason: str | None = None
