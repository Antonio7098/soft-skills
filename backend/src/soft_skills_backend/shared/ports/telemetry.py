"""Shared telemetry context for application adapters."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProviderCallContext:
    """Correlation metadata for an outbound provider call."""

    operation: str
    request_id: str | None = None
    trace_id: str | None = None
    pipeline_run_id: str | None = None
    workflow_id: str | None = None
    user_id: str | None = None
