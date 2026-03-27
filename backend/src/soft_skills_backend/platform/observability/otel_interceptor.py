"""OpenTelemetry interceptor for Stageflow pipeline and stage execution."""

from __future__ import annotations

from typing import Any

from stageflow.api import PipelineContext
from stageflow.pipeline.interceptors import BaseInterceptor, ErrorAction

from soft_skills_backend.platform.observability.telemetry import StageflowTracer


class OpenTelemetryInterceptor(BaseInterceptor):
    """Emit OpenTelemetry spans for Stageflow stage execution.

    This interceptor wraps stage execution and emits spans with:
    - pipeline.name, pipeline.run_id, stage.name, stage.kind
    - user.id, provider.name, model.slug when available
    - llm.* attributes for provider-backed stages
    """

    def __init__(self, tracer: StageflowTracer) -> None:
        self._tracer = tracer

    async def before(self, stage_name: str, ctx: PipelineContext) -> None:
        span_data = ctx.data.get("_otel_span")
        if span_data is None:
            return

        span = span_data.get("stage_span")
        if span is not None:
            span.set_attribute("stage.status", "started")

    async def after(self, stage_name: str, result: Any, ctx: PipelineContext) -> None:
        span_data = ctx.data.get("_otel_span")
        if span_data is None:
            return

        span = span_data.get("stage_span")
        if span is not None:
            duration_ms = span_data.get("duration_ms", 0)
            self._tracer.end_stage_span(span, status="completed", duration_ms=duration_ms)

    async def on_error(
        self, stage_name: str, error: Exception, ctx: PipelineContext
    ) -> ErrorAction:
        span_data = ctx.data.get("_otel_span")
        if span_data is None:
            return ErrorAction.FAIL

        span = span_data.get("stage_span")
        if span is not None:
            duration_ms = span_data.get("duration_ms", 0)
            self._tracer.end_stage_span(
                span, status="failed", error=str(error), duration_ms=duration_ms
            )
        return ErrorAction.FAIL


class OpenTelemetryPipelineSpanInterceptor:
    """Emit OpenTelemetry spans for pipeline-level lifecycle events."""

    def __init__(self, tracer: StageflowTracer) -> None:
        self._tracer = tracer

    def wrap_pipeline_run(self, ctx: PipelineContext, pipeline_name: str) -> dict[str, Any]:
        """Create a pipeline span and attach it to the context."""
        pipeline_run_id = str(ctx.pipeline_run_id) if ctx.pipeline_run_id else "unknown"
        trace_id = ctx.metadata.get("trace_id") if ctx.metadata else None
        user_id = str(ctx.user_id) if ctx.user_id else None

        span_data = self._tracer.start_pipeline_span(
            pipeline_name=pipeline_name,
            pipeline_run_id=pipeline_run_id,
            trace_id=trace_id,
            user_id=user_id,
        )
        return span_data


def create_otel_interceptor(tracer: StageflowTracer) -> OpenTelemetryInterceptor:
    """Factory to create an OpenTelemetry interceptor."""
    return OpenTelemetryInterceptor(tracer=tracer)


def create_pipeline_span_interceptor(
    tracer: StageflowTracer,
) -> OpenTelemetryPipelineSpanInterceptor:
    """Factory to create a pipeline span interceptor."""
    return OpenTelemetryPipelineSpanInterceptor(tracer=tracer)
