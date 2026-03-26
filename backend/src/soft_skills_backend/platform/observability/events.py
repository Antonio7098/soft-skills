"""Structured observability payloads."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class WorkflowEvent(BaseModel):
    """Machine-readable event payload."""

    event_id: str = Field(default_factory=lambda: uuid4().hex)
    event_type: str
    request_id: str | None = None
    trace_id: str | None = None
    workflow_id: str | None = None
    error_code: str | None = None
    organisation_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PipelineRunLog(BaseModel):
    """Pipeline run persistence payload."""

    pipeline_run_id: str
    pipeline_name: str
    topology: str | None = None
    execution_mode: str | None = None
    status: str
    request_id: str | None = None
    trace_id: str | None = None
    user_id: str | None = None
    error: str | None = None
    failed_stage: str | None = None
    stage_results: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None


class ProviderCallLog(BaseModel):
    """Provider call persistence payload."""

    call_id: str
    operation: str
    provider: str
    model_id: str | None = None
    success: bool
    latency_ms: int | None = None
    error: str | None = None
    pipeline_run_id: str | None = None
    request_id: str | None = None
    trace_id: str | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
