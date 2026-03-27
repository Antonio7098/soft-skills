"""OpenTelemetry setup with OTLP exporter for unified traces and metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.trace import Tracer


OTEL_TRACE_CONTEXT_HEADER = "traceparent"
W3C_TRACE_VERSION = "00"


@dataclass
class TelemetryConfig:
    """Resolved OpenTelemetry configuration."""

    enabled: bool
    service_name: str
    otlp_endpoint: str | None
    export_timeout_ms: int


def build_telemetry_config(
    enabled: bool,
    service_name: str,
    otlp_endpoint: str | None,
    export_timeout_ms: int = 30_000,
) -> TelemetryConfig:
    """Build telemetry configuration."""
    return TelemetryConfig(
        enabled=enabled,
        service_name=service_name,
        otlp_endpoint=otlp_endpoint,
        export_timeout_ms=export_timeout_ms,
    )


def setup_telemetry(config: TelemetryConfig) -> Tracer | None:
    """Initialize OpenTelemetry SDK and OTLP exporter.

    Returns a tracer if telemetry is enabled, None otherwise.
    """
    if not config.enabled or not config.otlp_endpoint:
        return None

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        return None

    try:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    except ImportError:
        return None

    resource = Resource.create({"service.name": config.service_name})
    provider: TracerProvider = TracerProvider(resource=resource)

    span_exporter = OTLPSpanExporter(
        endpoint=config.otlp_endpoint,
        insecure=True,
    )
    provider.add_span_processor(BatchSpanProcessor(span_exporter))
    trace.set_tracer_provider(provider)

    return trace.get_tracer(config.service_name)


class StageflowTracer:
    """Bridge between Stageflow interceptors and OpenTelemetry spans.

    Intercepts Stageflow pipeline/stage lifecycle events and emits them
    as OpenTelemetry spans with proper context propagation.
    """

    def __init__(self, tracer: Tracer | None) -> None:
        self._tracer = tracer

    def start_pipeline_span(
        self,
        pipeline_name: str,
        pipeline_run_id: str,
        trace_id: str | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """Start a pipeline-level span."""
        if self._tracer is None:
            return {}

        from opentelemetry import trace

        span = self._tracer.start_span(f"pipeline.{pipeline_name}")
        span.set_attribute("pipeline.name", pipeline_name)
        span.set_attribute("pipeline.run_id", pipeline_run_id)
        if trace_id:
            span.set_attribute("trace.id", trace_id)
        if user_id:
            span.set_attribute("user.id", user_id)
        span.set_attribute("pipeline.status", "started")

        return {"span": span, "ctx": trace.set_span_in_context(span)}

    def start_stage_span(
        self,
        stage_name: str,
        stage_kind: str,
        pipeline_name: str,
        pipeline_run_id: str,
        parent_ctx: Any = None,
        user_id: str | None = None,
        provider: str | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        """Start a stage-level span."""
        if self._tracer is None:
            return {}

        from opentelemetry import trace

        span_name = f"stage.{stage_name}"
        span = self._tracer.start_span(span_name)
        span.set_attribute("stage.name", stage_name)
        span.set_attribute("stage.kind", stage_kind)
        span.set_attribute("pipeline.name", pipeline_name)
        span.set_attribute("pipeline.run_id", pipeline_run_id)
        if user_id:
            span.set_attribute("user.id", user_id)
        if provider:
            span.set_attribute("provider.name", provider)
        if model:
            span.set_attribute("model.slug", model)

        return {"span": span, "ctx": trace.set_span_in_context(span)}

    def add_llm_attributes(
        self,
        span: Any,
        operation: str,
        provider: str,
        model: str | None = None,
        tokens: dict[str, int] | None = None,
    ) -> None:
        """Add LLM-specific span attributes."""
        if span is None:
            return

        span.set_attribute("llm.operation", operation)
        span.set_attribute("llm.provider", provider)
        if model:
            span.set_attribute("llm.model", model)
        if tokens:
            if tokens.get("prompt_tokens"):
                span.set_attribute("llm.tokens.prompt", tokens["prompt_tokens"])
            if tokens.get("completion_tokens"):
                span.set_attribute("llm.tokens.completion", tokens["completion_tokens"])
            if tokens.get("total_tokens"):
                span.set_attribute("llm.tokens.total", tokens["total_tokens"])

    def end_stage_span(
        self,
        span: Any,
        status: str = "completed",
        error: str | None = None,
        duration_ms: int | None = None,
    ) -> None:
        """End a stage span with appropriate status."""
        if span is None:
            return

        from opentelemetry import trace

        if status == "failed" or error:
            span.set_status(trace.Status(trace.StatusCode.ERROR, error or "failed"))
        else:
            span.set_status(trace.Status(trace.StatusCode.OK))

        if duration_ms is not None:
            span.set_attribute("stage.duration_ms", duration_ms)

        span.end()

    def end_pipeline_span(
        self,
        span: Any,
        status: str = "completed",
        error: str | None = None,
        duration_ms: int | None = None,
    ) -> None:
        """End a pipeline span with appropriate status."""
        if span is None:
            return

        from opentelemetry import trace

        if status == "failed" or error:
            span.set_status(trace.Status(trace.StatusCode.ERROR, error or "failed"))
            span.set_attribute("pipeline.status", "failed")
        else:
            span.set_status(trace.Status(trace.StatusCode.OK))
            span.set_attribute("pipeline.status", status)

        if duration_ms is not None:
            span.set_attribute("pipeline.duration_ms", duration_ms)

        span.end()


def extract_trace_context(headers: dict[str, str]) -> dict[str, str] | None:
    """Extract W3C trace context from HTTP headers.

    Returns the traceparent header value if valid, None otherwise.
    """
    traceparent = headers.get(OTEL_TRACE_CONTEXT_HEADER, "")
    if not traceparent or not traceparent.startswith(W3C_TRACE_VERSION):
        return None
    return {"traceparent": traceparent}


def inject_trace_context(headers: dict[str, str], span: Any) -> dict[str, str]:
    """Inject current span's trace context into HTTP headers."""
    if span is None:
        return headers

    from opentelemetry import trace

    ctx = trace.get_current_span()
    if ctx:
        headers[OTEL_TRACE_CONTEXT_HEADER] = format_traceparent(ctx)
    return headers


def format_traceparent(span: Any) -> str:
    """Format span context as W3C traceparent header value."""
    ctx = span.get_span_context()
    return f"{W3C_TRACE_VERSION}-{ctx.trace_id:032x}-{ctx.span_id:016x}-{ctx.trace_flags:02x}"
