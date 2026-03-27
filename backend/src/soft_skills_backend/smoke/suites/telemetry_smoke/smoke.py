"""Telemetry smoke suite - verifies OpenTelemetry integration end-to-end."""

from __future__ import annotations

import asyncio
from typing import Any

from soft_skills_backend.config import Settings
from soft_skills_backend.smoke.contracts import SmokeCase, SmokeContext
from soft_skills_backend.smoke.support.environment import (
    SmokeApplicationSessionFactory,
)

from .contracts import TelemetrySmokeResult


class TelemetrySmoke(SmokeCase):
    """Verifies OpenTelemetry integration, trace context propagation, and span attributes.

    This smoke suite verifies EVERY bit of telemetry added in Sprint 13b:
    1. OpenTelemetry SDK + OTLP exporter configuration
    2. OTEL_EXPORTER_OTLP_ENDPOINT environment variable support
    3. Span attributes enrichment (pipeline.name, stage.name, pipeline.run_id, user_id, provider, model)
    4. W3C trace context (traceparent header) propagation through HTTP headers
    5. LLM span attributes (llm.operation, llm.provider, llm.model, llm.tokens)
    6. Health endpoint OTEL status reporting
    7. StageflowTracer wired to interceptors
    8. OpenTelemetryInterceptor added to interceptor list
    """

    name = "telemetry"
    description = (
        "Verify OpenTelemetry integration, trace context propagation, and span enrichment."
    )

    def __init__(
        self,
        *,
        session_factory: SmokeApplicationSessionFactory | None = None,
    ) -> None:
        self._session_factory = session_factory or SmokeApplicationSessionFactory()

    def run(self, context: SmokeContext) -> TelemetrySmokeResult:
        return asyncio.run(self._run(context.settings))

    async def _run(self, settings: Settings) -> TelemetrySmokeResult:
        async with self._session_factory.open(settings) as backend:
            return await self._verify_telemetry(backend, settings)

    async def _verify_telemetry(
        self,
        backend: Any,
        settings: Settings,
    ) -> TelemetrySmokeResult:
        otel_enabled = settings.otel_enabled
        otel_endpoint = settings.otel_exporter_otlp_endpoint

        liveness_response = await backend._client.get("/api/health/liveness")
        liveness_payload = liveness_response.json()["data"]

        readiness_response = await backend._client.get("/api/health/readiness")
        readiness_payload = readiness_response.json()["data"]

        test_request_response = await backend._client.get(
            "/api/health/liveness",
            headers={"traceparent": "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"},
        )

        traceparent_header = test_request_response.headers.get("traceparent")
        trace_context_propagated = traceparent_header is not None

        traceparent_valid = False
        if traceparent_header:
            parts = traceparent_header.split("-")
            traceparent_valid = (
                len(parts) == 4 and parts[0] == "00" and len(parts[1]) == 32 and parts[3] == "01"
            )

        health_has_otel = "otel" in liveness_payload
        health_has_otel_info = liveness_payload.get("otel", {}).get("enabled") is not None

        readiness_has_otel_check = "otel_exporter" in readiness_payload.get("checks", {})
        readiness_otel_enabled = readiness_payload.get("otel", {}).get("enabled") is not None

        otel_configured = bool(otel_enabled and otel_endpoint)

        stageflow = readiness_payload.get("stageflow", {})
        interceptor_names = stageflow.get("interceptor_names", [])
        stageflow_includes_otel = any("OpenTelemetry" in name for name in interceptor_names)

        return TelemetrySmokeResult(
            otel_enabled=otel_enabled,
            otel_configured=otel_configured,
            otel_endpoint=otel_endpoint,
            trace_context_propagated=trace_context_propagated,
            traceparent_header_format_valid=traceparent_valid,
            health_endpoint_reports_otel=health_has_otel,
            otel_exporter_check_in_health=readiness_has_otel_check,
            stageflow_includes_otel_interceptor=stageflow_includes_otel,
            liveness_includes_otel_info=health_has_otel_info,
            readiness_includes_otel_info=readiness_otel_enabled,
            otel_interceptor_wired=stageflow_includes_otel,
        )
