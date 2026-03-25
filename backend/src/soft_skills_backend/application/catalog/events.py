"""Catalog event recording helpers."""

from __future__ import annotations

from typing import Any

from soft_skills_backend.observability.events import WorkflowEvent
from soft_skills_backend.persistence.repositories import SqlAlchemyWorkflowEventRepository


class CatalogEventRecorder:
    """Record catalog workflow events with stable workflow IDs."""

    def __init__(self, workflow_events: SqlAlchemyWorkflowEventRepository) -> None:
        self._workflow_events = workflow_events

    def record(self, event_type: str, request_id: str, payload: dict[str, Any]) -> None:
        self._workflow_events.record(
            WorkflowEvent(
                event_type=event_type,
                request_id=request_id,
                workflow_id=payload.get("collection_id") or payload.get("scenario_id"),
                payload=payload,
            )
        )
