"""Telemetry smoke suite contracts."""

from __future__ import annotations

from pydantic import BaseModel


class TelemetrySmokeResult(BaseModel):
    """Result of the telemetry smoke suite."""

    otel_enabled: bool
    otel_configured: bool
    otel_endpoint: str | None
    trace_context_propagated: bool
    traceparent_header_format_valid: bool
    health_endpoint_reports_otel: bool
    otel_exporter_check_in_health: bool
    stageflow_includes_otel_interceptor: bool
    liveness_includes_otel_info: bool
    readiness_includes_otel_info: bool
    otel_interceptor_wired: bool
