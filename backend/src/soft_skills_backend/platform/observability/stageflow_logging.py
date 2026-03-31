"""Adapters for Stageflow observability protocols."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from pydantic import BaseModel, Field

from soft_skills_backend.platform.observability.events import (
    PipelineRunLog,
    ProviderCallLog,
    WorkflowEvent,
)
from soft_skills_backend.platform.providers.openrouter_pricing import calculate_cost
from soft_skills_backend.shared.errors import AppError, ErrorCategory
from soft_skills_backend.shared.ports import (
    PipelineRunRepository,
    ProviderCallRepository,
    WorkflowEventRepository,
)

if TYPE_CHECKING:
    from soft_skills_backend.shared.ports.repositories import PipelineExecutionTraceRepository


class PipelineErrorSummary(BaseModel):
    error_type: str
    error_code: str | None = None
    category: str | None = None
    stage_name: str | None = None
    pipeline_name: str | None = None
    root_cause: str | None = None
    is_retryable: bool = False
    context: dict[str, Any] = Field(default_factory=dict)


def summarize_pipeline_error(
    error: str | Exception,
    *,
    stage_name: str | None = None,
    pipeline_name: str | None = None,
) -> PipelineErrorSummary:
    error_type = type(error).__name__ if isinstance(error, Exception) else "UnknownError"
    error_code: str | None = None
    category: str | None = None
    root_cause: str | None = None
    is_retryable = False
    context: dict[str, Any] = {}

    if isinstance(error, AppError):
        error_code = error.code
        category = error.category.value
        root_cause = error.message
        is_retryable = error.category in (ErrorCategory.PROVIDER, ErrorCategory.PERSISTENCE)
        context = dict(error.details) if error.details else {}
    elif isinstance(error, Exception):
        root_cause = str(error)
        error_type = type(error).__name__
        if "timeout" in root_cause.lower():
            is_retryable = True
    else:
        root_cause = str(error)

    return PipelineErrorSummary(
        error_type=error_type,
        error_code=error_code,
        category=category,
        stage_name=stage_name,
        pipeline_name=pipeline_name,
        root_cause=root_cause,
        is_retryable=is_retryable,
        context=context,
    )


def format_error_for_persistence(error: str | Exception) -> str:
    """Preserve the actionable message from structured errors when available."""

    if isinstance(error, AppError):
        reason = error.details.get("reason") if error.details else None
        if isinstance(reason, str) and reason.strip():
            return f"{error.code}: {reason}"
        return str(error)
    if isinstance(error, Exception):
        return str(error)
    return error


class DatabasePipelineRunLogger:
    """Persist Stageflow pipeline run lifecycle metadata."""

    def __init__(
        self,
        repository: PipelineRunRepository,
        workflow_events: WorkflowEventRepository | None = None,
        execution_trace_repository: PipelineExecutionTraceRepository | None = None,
    ) -> None:
        self._repository = repository
        self._workflow_events = workflow_events
        self._execution_trace_repository = execution_trace_repository
        self._stage_timings: dict[str, list[dict[str, Any]]] = {}

    async def log_run_started(
        self,
        *,
        pipeline_run_id: object,
        pipeline_name: str,
        topology: str | None,
        execution_mode: str | None,
        user_id: object,
        request_id: str | None = None,
        trace_id: str | None = None,
        **_: object,
    ) -> None:
        run_id_str = str(pipeline_run_id)
        now = datetime.now(UTC)
        self._stage_timings[run_id_str] = []
        self._repository.upsert(
            PipelineRunLog(
                pipeline_run_id=run_id_str,
                pipeline_name=pipeline_name,
                topology=topology,
                execution_mode=execution_mode,
                user_id=None if user_id is None else str(user_id),
                status="running",
                request_id=request_id,
                trace_id=trace_id,
                started_at=now,
            )
        )

    def log_stage_timing(
        self,
        *,
        pipeline_run_id: str,
        stage_name: str,
        event_type: str,
        timestamp: datetime,
        duration_ms: int | None = None,
        status: str | None = None,
        error: str | None = None,
    ) -> None:
        """Record a stage execution event for trace storage."""
        if pipeline_run_id in self._stage_timings:
            self._stage_timings[pipeline_run_id].append(
                {
                    "stage_name": stage_name,
                    "event_type": event_type,
                    "timestamp": timestamp.isoformat(),
                    "duration_ms": duration_ms,
                    "status": status,
                    "error": error,
                }
            )

    async def log_run_completed(
        self,
        *,
        pipeline_run_id: object,
        pipeline_name: str,
        duration_ms: int,
        status: str,
        stage_results: dict[str, Any],
        request_id: str | None = None,
        trace_id: str | None = None,
        **_: object,
    ) -> None:
        finished_at = datetime.now(UTC)
        started_at = (
            finished_at
            if duration_ms <= 0
            else datetime.fromtimestamp(finished_at.timestamp() - duration_ms / 1000, tz=UTC)
        )
        run_id_str = str(pipeline_run_id)
        self._repository.upsert(
            PipelineRunLog(
                pipeline_run_id=run_id_str,
                pipeline_name=pipeline_name,
                status=status,
                request_id=request_id,
                trace_id=trace_id,
                stage_results=stage_results,
                started_at=started_at,
                finished_at=finished_at,
            )
        )
        if self._execution_trace_repository is not None:
            execution_sequence = self._stage_timings.pop(run_id_str, [])
            if not execution_sequence and stage_results:
                execution_sequence = [
                    {
                        "stage_name": stage_name,
                        "event_type": "stage.completed",
                        "timestamp": finished_at.isoformat(),
                        "duration_ms": stage_results.get(stage_name, {}).get("duration_ms"),
                        "status": status if status == "completed" else "failed",
                        "error": None,
                    }
                    for stage_name in stage_results
                ]
            from soft_skills_backend.platform.db.models import PipelineExecutionTraceRecord

            trace_record = PipelineExecutionTraceRecord(
                pipeline_run_id=run_id_str,
                pipeline_name=pipeline_name,
                execution_sequence=execution_sequence,
                total_duration_ms=duration_ms,
                started_at=started_at,
                completed_at=finished_at,
            )
            self._execution_trace_repository.upsert(trace_record)

    async def log_run_failed(
        self,
        *,
        pipeline_run_id: object,
        pipeline_name: str,
        error: str | Exception,
        stage: str | None,
        request_id: str | None = None,
        trace_id: str | None = None,
        **_: object,
    ) -> None:
        persisted_error = format_error_for_persistence(error)
        self._repository.upsert(
            PipelineRunLog(
                pipeline_run_id=str(pipeline_run_id),
                pipeline_name=pipeline_name,
                status="failed",
                request_id=request_id,
                trace_id=trace_id,
                error=persisted_error,
                failed_stage=stage,
                finished_at=datetime.now(UTC),
            )
        )
        if self._workflow_events is not None:
            summary = summarize_pipeline_error(
                error,
                stage_name=stage,
                pipeline_name=pipeline_name,
            )
            event_type = (
                f"pipeline.error.{summary.category or 'unknown'}"
                if summary.category
                else "pipeline.error.unknown"
            )
            self._workflow_events.record(
                WorkflowEvent(
                    event_type=event_type,
                    request_id=request_id,
                    trace_id=trace_id,
                    workflow_id=str(pipeline_run_id),
                    error_code=summary.error_code,
                    payload=summary.model_dump(),
                )
            )


class DatabaseProviderCallLogger:
    """Persist provider call start and end records."""

    def __init__(self, repository: ProviderCallRepository) -> None:
        self._repository = repository

    async def log_call_start(
        self,
        *,
        operation: str,
        provider: str,
        model_id: str | None,
        pipeline_run_id: object | None = None,
        request_id: str | None = None,
        trace_id: str | None = None,
        **_: object,
    ) -> str:
        call_id = uuid4().hex
        self._repository.upsert(
            ProviderCallLog(
                call_id=call_id,
                operation=operation,
                provider=provider,
                model_id=model_id,
                success=False,
                pipeline_run_id=None if pipeline_run_id is None else str(pipeline_run_id),
                request_id=request_id,
                trace_id=trace_id,
            )
        )
        return call_id

    async def log_call_end(
        self,
        call_id: object,
        *,
        success: bool,
        latency_ms: int,
        error: str | None = None,
        **metrics: dict[str, object],
    ) -> None:
        # Extract usage metrics
        usage = metrics.get("usage", {})
        if isinstance(usage, dict):
            prompt_tokens = int(usage.get("prompt_tokens", 0))
            completion_tokens = int(usage.get("completion_tokens", 0))
        else:
            prompt_tokens = 0
            completion_tokens = 0

        # Calculate cost
        model_id = metrics.get("model_id")
        cost_usd = 0.0
        if model_id and prompt_tokens + completion_tokens > 0:
            cost_usd = calculate_cost(str(model_id), prompt_tokens, completion_tokens)

        self._repository.upsert(
            ProviderCallLog(
                call_id=str(call_id),
                operation=str(metrics.get("operation", "unknown")),
                provider=str(metrics.get("provider", "unknown")),
                model_id=None if model_id is None else str(model_id),
                success=success,
                latency_ms=latency_ms,
                error=error,
                pipeline_run_id=None
                if metrics.get("pipeline_run_id") is None
                else str(metrics["pipeline_run_id"]),
                request_id=None
                if metrics.get("request_id") is None
                else str(metrics["request_id"]),
                trace_id=None if metrics.get("trace_id") is None else str(metrics["trace_id"]),
                metrics={key: value for key, value in metrics.items() if value is not None},
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost_usd=cost_usd,
            )
        )
