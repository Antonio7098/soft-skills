"""Repository ports used by application services."""

from __future__ import annotations

from typing import Protocol

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
