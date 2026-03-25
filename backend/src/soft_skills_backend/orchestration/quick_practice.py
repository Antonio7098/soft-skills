"""Explicit DAG executor for quick-practice pipelines."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from soft_skills_backend.application.ports import PipelineRunRepository
from soft_skills_backend.domain.errors import AppError, orchestration_error
from soft_skills_backend.observability.events import PipelineRunLog

StageHandler = Callable[["PipelineExecutionContext", dict[str, Any]], Any]


@dataclass(frozen=True, slots=True)
class PipelineStage:
    """Stage metadata for the fallback DAG executor."""

    name: str
    kind: str
    dependencies: tuple[str, ...] = ()
    handler: StageHandler | None = None


@dataclass(frozen=True, slots=True)
class PipelineDefinition:
    """Named pipeline with explicit stage ordering and dependencies."""

    name: str
    stages: tuple[PipelineStage, ...]
    topology: str = "dag"
    execution_mode: str = "fallback"


@dataclass(frozen=True, slots=True)
class PipelineExecutionContext:
    """Correlation data carried across all stages."""

    pipeline_run_id: str
    pipeline_name: str
    request_id: str
    trace_id: str
    workflow_id: str
    user_id: str


@dataclass(frozen=True, slots=True)
class StageExecutionResult:
    """Single stage outcome."""

    payload: Any
    summary: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PipelineExecutionResult:
    """Completed pipeline outputs."""

    context: PipelineExecutionContext
    stages: dict[str, StageExecutionResult]

    def payload_for(self, stage_name: str) -> Any:
        return self.stages[stage_name].payload


class QuickPracticePipelineExecutor:
    """Persisted DAG executor used when Stageflow is unavailable."""

    def __init__(self, pipeline_runs: PipelineRunRepository) -> None:
        self._pipeline_runs = pipeline_runs

    async def run(
        self,
        definition: PipelineDefinition,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str,
        user_id: str,
    ) -> PipelineExecutionResult:
        start_time = datetime.now(UTC)
        pipeline_ctx = PipelineExecutionContext(
            pipeline_run_id=uuid4().hex,
            pipeline_name=definition.name,
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id,
            user_id=user_id,
        )
        self._pipeline_runs.upsert(
            PipelineRunLog(
                pipeline_run_id=pipeline_ctx.pipeline_run_id,
                pipeline_name=definition.name,
                topology=definition.topology,
                execution_mode=definition.execution_mode,
                status="running",
                request_id=request_id,
                trace_id=trace_id,
                user_id=user_id,
                started_at=start_time,
            )
        )

        pending = {stage.name: stage for stage in definition.stages}
        completed: dict[str, StageExecutionResult] = {}
        try:
            while pending:
                ready = [
                    stage
                    for stage in pending.values()
                    if all(dependency in completed for dependency in stage.dependencies)
                ]
                if not ready:
                    raise orchestration_error(
                        "Pipeline dependencies could not be resolved",
                        code="SS-ORCHESTRATION-003",
                        details={"pipeline_name": definition.name},
                    )

                for stage in ready:
                    if stage.handler is None:
                        raise orchestration_error(
                            "Pipeline stage is missing a handler",
                            code="SS-ORCHESTRATION-004",
                            details={"pipeline_name": definition.name, "stage_name": stage.name},
                        )
                    dependency_payloads = {
                        dependency: completed[dependency].payload for dependency in stage.dependencies
                    }
                    result = stage.handler(pipeline_ctx, dependency_payloads)
                    if hasattr(result, "__await__"):
                        result = await result
                    completed[stage.name] = result
                    del pending[stage.name]
        except AppError:
            self._record_failure(definition, pipeline_ctx, completed, start_time)
            raise
        except Exception as exc:
            if hasattr(exc, "app_error"):
                self._record_failure(definition, pipeline_ctx, completed, start_time, exc)
                raise
            self._record_failure(definition, pipeline_ctx, completed, start_time, exc)
            raise orchestration_error(
                "Quick-practice pipeline execution failed unexpectedly",
                code="SS-ORCHESTRATION-005",
                details={"pipeline_name": definition.name, "reason": str(exc)},
            ) from exc

        finished_at = datetime.now(UTC)
        self._pipeline_runs.upsert(
            PipelineRunLog(
                pipeline_run_id=pipeline_ctx.pipeline_run_id,
                pipeline_name=definition.name,
                topology=definition.topology,
                execution_mode=definition.execution_mode,
                status="completed",
                request_id=request_id,
                trace_id=trace_id,
                user_id=user_id,
                stage_results=_stage_summaries(definition, completed),
                started_at=start_time,
                finished_at=finished_at,
            )
        )
        return PipelineExecutionResult(context=pipeline_ctx, stages=completed)

    def _record_failure(
        self,
        definition: PipelineDefinition,
        context: PipelineExecutionContext,
        completed: dict[str, StageExecutionResult],
        started_at: datetime,
        error: Exception | None = None,
    ) -> None:
        completed_stage_names = tuple(completed.keys())
        failed_stage = next(
            (stage.name for stage in definition.stages if stage.name not in completed_stage_names),
            None,
        )
        self._pipeline_runs.upsert(
            PipelineRunLog(
                pipeline_run_id=context.pipeline_run_id,
                pipeline_name=definition.name,
                topology=definition.topology,
                execution_mode=definition.execution_mode,
                status="failed",
                request_id=context.request_id,
                trace_id=context.trace_id,
                user_id=context.user_id,
                error=None if error is None else str(error),
                failed_stage=failed_stage,
                stage_results=_stage_summaries(definition, completed),
                started_at=started_at,
                finished_at=datetime.now(UTC),
            )
        )


def _stage_summaries(
    definition: PipelineDefinition,
    completed: dict[str, StageExecutionResult],
) -> dict[str, Any]:
    stage_kind_lookup = {stage.name: stage.kind for stage in definition.stages}
    return {
        stage_name: {
            "kind": stage_kind_lookup[stage_name],
            **result.summary,
        }
        for stage_name, result in completed.items()
    }
