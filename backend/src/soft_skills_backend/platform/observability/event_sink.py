"""Durable event sink for backend observability artifacts."""

from __future__ import annotations

from typing import Any

from soft_skills_backend.platform.observability.events import WorkflowEvent
from soft_skills_backend.shared.ports import WorkflowEventRepository


class DurableEventSink:
    """Persist Stageflow-compatible events into durable storage."""

    def __init__(self, repository: WorkflowEventRepository) -> None:
        self._repository = repository

    async def emit(self, *, type: str, data: dict[str, Any] | None = None) -> None:
        self._repository.record(
            WorkflowEvent(
                event_type=type,
                payload=data or {},
                request_id=(data or {}).get("request_id"),
                trace_id=(data or {}).get("trace_id"),
                workflow_id=(data or {}).get("workflow_id"),
                error_code=(data or {}).get("error_code"),
            )
        )

    def try_emit(self, *, type: str, data: dict[str, Any] | None = None) -> bool:
        self._repository.record(
            WorkflowEvent(
                event_type=type,
                payload=data or {},
                request_id=(data or {}).get("request_id"),
                trace_id=(data or {}).get("trace_id"),
                workflow_id=(data or {}).get("workflow_id"),
                error_code=(data or {}).get("error_code"),
            )
        )
        return True
