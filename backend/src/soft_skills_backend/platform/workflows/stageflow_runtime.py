"""Stageflow integration boundary."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any

from soft_skills_backend.config import Settings
from soft_skills_backend.platform.observability.event_sink import DurableEventSink
from soft_skills_backend.platform.observability.otel_interceptor import (
    create_otel_interceptor,
)
from soft_skills_backend.platform.observability.stageflow_logging import (
    DatabasePipelineRunLogger,
    DatabaseProviderCallLogger,
)
from soft_skills_backend.platform.observability.telemetry import (
    StageflowTracer,
    build_telemetry_config,
    setup_telemetry,
)
from soft_skills_backend.shared.errors import orchestration_error
from soft_skills_backend.shared.ports import (
    PipelineRunRepository,
    ProviderCallRepository,
    WorkflowEventRepository,
)


@dataclass(slots=True)
class StageflowRuntime:
    """Resolved Stageflow runtime capabilities."""

    installed: bool = True
    pipeline_type_name: str = "Pipeline"
    pipeline_context_type_name: str = "PipelineContext"
    stage_kinds: tuple[str, ...] = ()
    default_interceptor_names: tuple[str, ...] = (
        "TimeoutInterceptor",
        "CircuitBreakerInterceptor",
        "TracingInterceptor",
        "MetricsInterceptor",
        "LoggingInterceptor",
    )
    event_sink_type_name: str = "BackpressureAwareEventSink"
    pipeline_run_logger_type_name: str = "PipelineRunLogger"
    provider_call_logger_type_name: str = "ProviderCallLogger"
    runtime_objects: dict[str, Any] | None = None
    otel_enabled: bool = False
    otel_tracer: StageflowTracer | None = None


def build_stageflow_runtime(
    settings: Settings,
    *,
    event_sink: DurableEventSink,
    pipeline_runs: PipelineRunRepository,
    provider_calls: ProviderCallRepository,
    workflow_events: WorkflowEventRepository,
    execution_trace_repository: Any = None,
) -> StageflowRuntime:
    """Build the mandatory Stageflow runtime wrapper for the application."""

    try:
        stageflow_module = importlib.import_module("stageflow")
        stageflow_advanced_module = importlib.import_module("stageflow.advanced")
        stageflow_api_module = importlib.import_module("stageflow.api")
    except ModuleNotFoundError as exc:
        raise orchestration_error(
            "Stageflow runtime is required but not installed",
            code="SS-ORCHESTRATION-002",
            details={"missing_reason": "Install `stageflow-core` to run the backend."},
        ) from exc

    backpressure_aware_event_sink_cls = stageflow_module.BackpressureAwareEventSink
    get_default_interceptors = stageflow_advanced_module.get_default_interceptors
    pipeline_cls = stageflow_api_module.Pipeline
    pipeline_context_cls = stageflow_api_module.PipelineContext
    stage_kind_enum = stageflow_api_module.StageKind

    pipeline_run_logger = DatabasePipelineRunLogger(
        pipeline_runs,
        workflow_events,
        execution_trace_repository=execution_trace_repository,
    )
    provider_call_logger = DatabaseProviderCallLogger(provider_calls)
    buffered_sink = backpressure_aware_event_sink_cls(
        downstream=event_sink,
        max_queue_size=settings.stageflow_event_queue_size,
    )

    telemetry_config = build_telemetry_config(
        enabled=settings.otel_enabled,
        service_name=settings.otel_service_name,
        otlp_endpoint=settings.otel_exporter_otlp_endpoint,
    )
    otel_tracer_impl = setup_telemetry(telemetry_config)
    otel_tracer = StageflowTracer(tracer=otel_tracer_impl)
    otel_interceptor = create_otel_interceptor(otel_tracer) if otel_tracer_impl else None

    runtime_objects: dict[str, Any] = {
        "pipeline_cls": pipeline_cls,
        "pipeline_context_cls": pipeline_context_cls,
        "get_default_interceptors": get_default_interceptors,
        "event_sink": buffered_sink,
        "pipeline_run_logger": pipeline_run_logger,
        "provider_call_logger": provider_call_logger,
        "otel_tracer": otel_tracer,
        "otel_interceptor": otel_interceptor,
    }

    interceptor_names = [
        interceptor.__class__.__name__
        for interceptor in get_default_interceptors(include_auth=False)
    ]
    if otel_interceptor is not None:
        interceptor_names.append("OpenTelemetryInterceptor")

    return StageflowRuntime(
        installed=True,
        pipeline_type_name=pipeline_cls.__name__,
        pipeline_context_type_name=pipeline_context_cls.__name__,
        stage_kinds=tuple(kind.name for kind in stage_kind_enum),
        default_interceptor_names=tuple(interceptor_names),
        runtime_objects=runtime_objects,
        otel_enabled=settings.otel_enabled,
        otel_tracer=otel_tracer,
    )
