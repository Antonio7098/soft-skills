"""Stageflow integration boundary."""

from __future__ import annotations

import importlib
import importlib.util
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from soft_skills_backend.application.ports import PipelineRunRepository, ProviderCallRepository
from soft_skills_backend.config import Settings
from soft_skills_backend.domain.errors import orchestration_error
from soft_skills_backend.observability.event_sink import DurableEventSink
from soft_skills_backend.observability.stageflow_logging import (
    DatabasePipelineRunLogger,
    DatabaseProviderCallLogger,
)


class SoftSkillsStageKind(StrEnum):
    """Stable stage kinds even before Stageflow is installed."""

    GUARD = "GUARD"
    ENRICH = "ENRICH"
    ROUTE = "ROUTE"
    TRANSFORM = "TRANSFORM"
    WORK = "WORK"
    AGENT = "AGENT"


@dataclass(slots=True)
class StageflowRuntime:
    """Resolved Stageflow runtime capabilities."""

    installed: bool
    pipeline_type_name: str = "Pipeline"
    pipeline_context_type_name: str = "PipelineContext"
    stage_kinds: tuple[str, ...] = tuple(kind.value for kind in SoftSkillsStageKind)
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
    missing_reason: str | None = None
    runtime_objects: dict[str, Any] | None = None

    def require_installed(self) -> None:
        """Raise a stable error if Stageflow is required but unavailable."""

        if not self.installed:
            raise orchestration_error(
                "Stageflow runtime is not installed",
                code="SS-ORCHESTRATION-002",
                details={"missing_reason": self.missing_reason},
            )


def build_stageflow_runtime(
    settings: Settings,
    *,
    event_sink: DurableEventSink,
    pipeline_runs: PipelineRunRepository,
    provider_calls: ProviderCallRepository,
) -> StageflowRuntime:
    """Build a runtime wrapper around Stageflow if it is installed."""

    if importlib.util.find_spec("stageflow") is None:
        runtime = StageflowRuntime(
            installed=False,
            missing_reason="Install `stageflow-core` to enable pipeline execution.",
        )
        if settings.stageflow_required:
            runtime.require_installed()
        return runtime

    stageflow_module = importlib.import_module("stageflow")
    stageflow_advanced_module = importlib.import_module("stageflow.advanced")
    stageflow_api_module = importlib.import_module("stageflow.api")

    backpressure_aware_event_sink_cls = stageflow_module.BackpressureAwareEventSink
    get_default_interceptors = stageflow_advanced_module.get_default_interceptors
    pipeline_cls = stageflow_api_module.Pipeline
    pipeline_context_cls = stageflow_api_module.PipelineContext
    stage_kind_enum = stageflow_api_module.StageKind

    pipeline_run_logger = DatabasePipelineRunLogger(pipeline_runs)
    provider_call_logger = DatabaseProviderCallLogger(provider_calls)
    buffered_sink = backpressure_aware_event_sink_cls(
        downstream=event_sink,
        max_queue_size=settings.stageflow_event_queue_size,
    )

    return StageflowRuntime(
        installed=True,
        pipeline_type_name=pipeline_cls.__name__,
        pipeline_context_type_name=pipeline_context_cls.__name__,
        stage_kinds=tuple(kind.name for kind in stage_kind_enum),
        default_interceptor_names=tuple(
            interceptor.__class__.__name__
            for interceptor in get_default_interceptors(include_auth=False)
        ),
        runtime_objects={
            "pipeline_cls": pipeline_cls,
            "pipeline_context_cls": pipeline_context_cls,
            "get_default_interceptors": get_default_interceptors,
            "event_sink": buffered_sink,
            "pipeline_run_logger": pipeline_run_logger,
            "provider_call_logger": provider_call_logger,
        },
    )
