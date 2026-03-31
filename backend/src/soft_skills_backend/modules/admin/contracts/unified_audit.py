"""Unified audit log contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field


class UnifiedAuditEntryView(BaseModel):
    """One row in the unified audit log."""

    id: str
    source: str  # "workflow_event", "pipeline_run", "provider_call"
    event_type: str
    user_id: str | None = None
    trace_id: str | None = None
    workflow_id: str | None = None
    request_id: str | None = None
    error_code: str | None = None
    occurred_at: str
    payload: dict[str, object] = Field(default_factory=dict)


class PaginatedUnifiedAuditView(BaseModel):
    """Paginated unified audit log response."""

    items: list[UnifiedAuditEntryView]
    total: int
    offset: int
    limit: int
