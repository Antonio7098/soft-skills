"""Adapters for Stageflow observability protocols."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from soft_skills_backend.platform.observability.events import PipelineRunLog, ProviderCallLog
from soft_skills_backend.shared.ports import PipelineRunRepository, ProviderCallRepository


class DatabasePipelineRunLogger:
    """Persist Stageflow pipeline run lifecycle metadata."""

    def __init__(self, repository: PipelineRunRepository) -> None:
        self._repository = repository

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
        self._repository.upsert(
            PipelineRunLog(
                pipeline_run_id=str(pipeline_run_id),
                pipeline_name=pipeline_name,
                topology=topology,
                execution_mode=execution_mode,
                user_id=None if user_id is None else str(user_id),
                status="running",
                request_id=request_id,
                trace_id=trace_id,
                started_at=datetime.now(UTC),
            )
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
        started_at = finished_at if duration_ms <= 0 else finished_at
        self._repository.upsert(
            PipelineRunLog(
                pipeline_run_id=str(pipeline_run_id),
                pipeline_name=pipeline_name,
                status=status,
                request_id=request_id,
                trace_id=trace_id,
                stage_results=stage_results,
                started_at=started_at,
                finished_at=finished_at,
            )
        )

    async def log_run_failed(
        self,
        *,
        pipeline_run_id: object,
        pipeline_name: str,
        error: str,
        stage: str | None,
        request_id: str | None = None,
        trace_id: str | None = None,
        **_: object,
    ) -> None:
        self._repository.upsert(
            PipelineRunLog(
                pipeline_run_id=str(pipeline_run_id),
                pipeline_name=pipeline_name,
                status="failed",
                request_id=request_id,
                trace_id=trace_id,
                error=error,
                failed_stage=stage,
                finished_at=datetime.now(UTC),
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
        **metrics: object,
    ) -> None:
        self._repository.upsert(
            ProviderCallLog(
                call_id=str(call_id),
                operation=str(metrics.get("operation", "unknown")),
                provider=str(metrics.get("provider", "unknown")),
                model_id=None if metrics.get("model_id") is None else str(metrics["model_id"]),
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
            )
        )
