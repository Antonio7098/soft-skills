"""Admin-agent response contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class QueryAdminDataResultView(BaseModel):
    tool_name: str = "query_admin_data"
    approval_state: str = "auto_allowed"
    sql: str
    params: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
    source_views: list[str] = Field(default_factory=list)
    row_count: int
    row_cap_applied: bool
    duration_ms: int
    rows: list[dict[str, Any]] = Field(default_factory=list)


class AdminAgentResponseMetadataView(BaseModel):
    conversation_id: str
    request_id: str
    trace_id: str
    workflow_id: str
    provider: str
    model_slug: str
    prompt_version: str
    config_version: str
    generated_at: datetime


class AdminAgentChatView(BaseModel):
    message: str
    conversation_id: str
    tool_results: list[QueryAdminDataResultView] = Field(default_factory=list)
    metadata: AdminAgentResponseMetadataView
