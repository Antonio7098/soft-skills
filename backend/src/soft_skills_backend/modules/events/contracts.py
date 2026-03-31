"""Events domain contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field


class WorkflowEventView(BaseModel):
    event_id: str
    event_type: str
    request_id: str | None = None
    trace_id: str | None = None
    workflow_id: str | None = None
    error_code: str | None = None
    user_id: str | None = None
    payload: dict[str, object] = Field(default_factory=dict)
    occurred_at: str


class WorkflowEventListView(BaseModel):
    event_id: str
    event_type: str
    request_id: str | None = None
    trace_id: str | None = None
    workflow_id: str | None = None
    error_code: str | None = None
    user_id: str | None = None
    occurred_at: str


class UpdateWorkflowEventCommand(BaseModel):
    error_code: str | None = None
    payload: dict[str, object] | None = None


class PaginatedWorkflowEventsView(BaseModel):
    items: list[WorkflowEventListView]
    total: int
    offset: int
    limit: int
