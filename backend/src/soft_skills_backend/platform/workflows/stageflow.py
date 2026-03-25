"""Shared Stageflow helpers for application services."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, TypeVar, cast
from uuid import uuid4

from stageflow.api import Pipeline, PipelineContext
from stageflow.core import StageContext, StageOutput
from stageflow.observability.wide_events import WideEventEmitter
from stageflow.pipeline.dag import UnifiedStageExecutionError
from stageflow.pipeline.guard_retry import GuardRetryStrategy
from stageflow.pipeline.idempotency import IdempotencyInterceptor, InMemoryIdempotencyStore
from stageflow.pipeline.results import PipelineResults

from soft_skills_backend.platform.workflows.stageflow_runtime import StageflowRuntime
from soft_skills_backend.shared.errors import orchestration_error

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class StageflowStageResult:
    """Typed stage payload paired with summary metadata for observability."""

    payload: Any
    summary: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class StageflowPipelineSupport:
    """Resolved Stageflow runtime dependencies for application pipelines."""

    event_sink: Any
    get_default_interceptors: Callable[..., list[Any]]
    pipeline_run_logger: Any
    wide_event_emitter: WideEventEmitter = field(default_factory=WideEventEmitter)
    idempotency_store: InMemoryIdempotencyStore = field(default_factory=InMemoryIdempotencyStore)

    @classmethod
    def from_runtime(cls, stageflow_runtime: StageflowRuntime) -> StageflowPipelineSupport:
        runtime_objects = stageflow_runtime.runtime_objects
        assert runtime_objects is not None
        return cls(
            event_sink=runtime_objects["event_sink"],
            get_default_interceptors=runtime_objects["get_default_interceptors"],
            pipeline_run_logger=runtime_objects["pipeline_run_logger"],
        )

    def interceptors(self, *, scoped_idempotency: bool) -> list[Any]:
        """Build the interceptor stack for a production pipeline."""

        if not scoped_idempotency:
            return self.get_default_interceptors(include_auth=False)
        interceptors = self.get_default_interceptors(
            include_auth=False,
            include_idempotency=False,
        )
        interceptors.insert(1, StageScopedIdempotencyInterceptor(store=self.idempotency_store))
        return interceptors


def ok_output(result: StageflowStageResult) -> StageOutput:
    """Encode a stage result into the Stageflow output contract."""

    return StageOutput.ok(data={"payload": result.payload, "summary": result.summary})


def payload_from_inputs(ctx: StageContext, stage_name: str) -> Any:
    """Read a dependency payload from Stageflow stage inputs."""

    return ctx.inputs.require_from(stage_name, "payload")


def payload_from_results(results: PipelineResults, stage_name: str, *, expected_type: type[T]) -> T:
    """Read a payload from pipeline results with a concrete expected type."""

    payload = results.require_ok(stage_name).data["payload"]
    if not isinstance(payload, expected_type):
        raise orchestration_error(
            "Stageflow payload type did not match the expected contract",
            details={
                "stage_name": stage_name,
                "expected_type": expected_type.__name__,
                "actual_type": type(payload).__name__,
            },
        )
    return cast(T, payload)


def summary_from_output(output: StageOutput) -> dict[str, Any]:
    """Extract observability summary fields from a Stageflow output."""

    summary = output.data.get("summary", {})
    return summary if isinstance(summary, dict) else {}


def pipeline_run_id_from_context(ctx: StageContext) -> str:
    """Resolve the current pipeline run id from Stageflow context."""

    if ctx.pipeline_run_id is None:
        raise orchestration_error("Stageflow pipeline run id was not populated")
    return str(ctx.pipeline_run_id)


def request_id_from_context(ctx: StageContext) -> str:
    """Resolve the request id from Stageflow context."""

    if ctx.request_id is None:
        raise orchestration_error("Stageflow request id was not populated")
    return str(ctx.request_id)


def user_id_from_context(ctx: StageContext) -> str:
    """Resolve the user id from Stageflow context."""

    if ctx.snapshot.user_id is None:
        raise orchestration_error("Stageflow user id was not populated")
    return str(ctx.snapshot.user_id)


def metadata_value(ctx: StageContext, key: str) -> str:
    """Read required application correlation metadata from Stageflow snapshot metadata."""

    value = ctx.snapshot.metadata.get(key)
    if value is None:
        raise orchestration_error(
            "Stageflow metadata did not include a required application field",
            details={"key": key},
        )
    return str(value)


async def run_logged_pipeline(
    support: StageflowPipelineSupport,
    pipeline: Pipeline,
    *,
    request_id: str,
    trace_id: str,
    workflow_id: str,
    user_id: str,
    execution_mode: str,
    service: str,
    session_id: str | None = None,
    idempotency_key: str | None = None,
    idempotency_params: dict[str, Any] | None = None,
    guard_retry_strategy: GuardRetryStrategy | None = None,
) -> PipelineResults:
    """Run a Stageflow pipeline with shared correlation, logging, and wide-event wiring."""

    pipeline_run_id = uuid4().hex
    started_at = datetime.now(UTC)
    ctx_data: dict[str, Any] = {}
    if idempotency_key is not None:
        ctx_data["idempotency_key"] = idempotency_key
    if idempotency_params is not None:
        ctx_data["idempotency_params"] = idempotency_params

    ctx = PipelineContext.create(
        pipeline_run_id=cast(Any, pipeline_run_id),
        request_id=cast(Any, request_id),
        session_id=cast(Any, session_id or workflow_id),
        user_id=cast(Any, user_id),
        topology=pipeline.name,
        execution_mode=execution_mode,
        metadata={
            "trace_id": trace_id,
            "workflow_id": workflow_id,
        },
        event_sink=support.event_sink,
        service=service,
        data=ctx_data,
    )
    await support.pipeline_run_logger.log_run_started(
        pipeline_run_id=pipeline_run_id,
        pipeline_name=pipeline.name,
        topology=pipeline.name,
        execution_mode=execution_mode,
        user_id=user_id,
        request_id=request_id,
        trace_id=trace_id,
    )
    try:
        results = await pipeline.run(
            ctx,
            interceptors=support.interceptors(scoped_idempotency=idempotency_key is not None),
            guard_retry_strategy=guard_retry_strategy,
            emit_stage_wide_events=True,
            emit_pipeline_wide_event=True,
            wide_event_emitter=support.wide_event_emitter,
        )
    except UnifiedStageExecutionError as exc:
        await support.pipeline_run_logger.log_run_failed(
            pipeline_run_id=pipeline_run_id,
            pipeline_name=pipeline.name,
            error=str(exc.original),
            stage=exc.stage,
            request_id=request_id,
            trace_id=trace_id,
        )
        raise exc.original from exc
    except Exception as exc:
        await support.pipeline_run_logger.log_run_failed(
            pipeline_run_id=pipeline_run_id,
            pipeline_name=pipeline.name,
            error=str(exc),
            stage=None,
            request_id=request_id,
            trace_id=trace_id,
        )
        raise orchestration_error(
            "Stageflow pipeline execution failed unexpectedly",
            code="SS-ORCHESTRATION-005",
            details={"pipeline_name": pipeline.name, "reason": str(exc)},
        ) from exc

    finished_at = datetime.now(UTC)
    await support.pipeline_run_logger.log_run_completed(
        pipeline_run_id=pipeline_run_id,
        pipeline_name=pipeline.name,
        duration_ms=int((finished_at - started_at).total_seconds() * 1000),
        status="completed",
        stage_results=_stage_summaries(pipeline, results),
        request_id=request_id,
        trace_id=trace_id,
    )
    return results


def _stage_summaries(pipeline: Pipeline, results: PipelineResults) -> dict[str, Any]:
    return {
        stage_name: {
            "kind": pipeline.stages[stage_name].kind.value,
            **summary_from_output(output),
        }
        for stage_name, output in results.items()
    }


class StageScopedIdempotencyInterceptor(IdempotencyInterceptor):
    """Scope Stageflow idempotency keys by stage name for multi-stage DAGs."""

    _ACTIVE_KEY = "_stageflow.idempotency.active_key"

    def __init__(self, *, store: InMemoryIdempotencyStore) -> None:
        super().__init__(
            store=store,
            key_extractor=lambda ctx: cast(str | None, ctx.data.get(self._ACTIVE_KEY)),
        )

    async def before(self, stage_name: str, ctx: PipelineContext) -> Any:
        base_key = ctx.data.get("idempotency_key")
        if base_key:
            ctx.data[self._ACTIVE_KEY] = f"{stage_name}:{base_key}"
        return await super().before(stage_name, ctx)

    async def after(self, stage_name: str, result: Any, ctx: PipelineContext) -> None:
        try:
            await super().after(stage_name, result, ctx)
        finally:
            ctx.data.pop(self._ACTIVE_KEY, None)

    async def on_error(self, stage_name: str, error: Exception, ctx: PipelineContext) -> Any:
        try:
            return await super().on_error(stage_name, error, ctx)
        finally:
            ctx.data.pop(self._ACTIVE_KEY, None)
