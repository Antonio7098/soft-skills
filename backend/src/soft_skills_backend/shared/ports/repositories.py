"""Repository ports used by application services."""

from __future__ import annotations

from typing import Protocol

from soft_skills_backend.platform.db.models import (
    PipelineDefinitionRecord,
    PipelineExecutionTraceRecord,
    StageDefinitionRecord,
)
from soft_skills_backend.platform.observability.events import (
    PipelineRunLog,
    ProviderCallLog,
    WorkflowEvent,
)


class WorkflowEventRepository(Protocol):
    """Durable storage for structured events."""

    def record(self, event: WorkflowEvent) -> None: ...


class PipelineRunRepository(Protocol):
    """Durable storage for Stageflow pipeline run metadata."""

    def upsert(self, log: PipelineRunLog) -> None: ...


class ProviderCallRepository(Protocol):
    """Durable storage for provider call telemetry."""

    def upsert(self, log: ProviderCallLog) -> None: ...


class PipelineDefinitionRepository(Protocol):
    """Durable storage for pipeline definition records."""

    def upsert(self, record: PipelineDefinitionRecord) -> None: ...
    def get_by_name(self, pipeline_name: str) -> PipelineDefinitionRecord | None: ...
    def list_all(self) -> list[PipelineDefinitionRecord]: ...


class StageDefinitionRepository(Protocol):
    """Durable storage for stage definition records."""

    def upsert_batch(self, pipeline_name: str, stages: list[StageDefinitionRecord]) -> None: ...
    def get_by_pipeline(self, pipeline_name: str) -> list[StageDefinitionRecord]: ...


class PipelineExecutionTraceRepository(Protocol):
    """Durable storage for pipeline execution traces."""

    def upsert(self, record: PipelineExecutionTraceRecord) -> None: ...
    def get_by_run_id(self, pipeline_run_id: str) -> PipelineExecutionTraceRecord | None: ...
    def get_by_pipeline(
        self, pipeline_name: str, *, offset: int = 0, limit: int = 50
    ) -> list[PipelineExecutionTraceRecord]: ...
