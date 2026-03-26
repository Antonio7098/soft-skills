"""Catalog event recording helpers."""

from __future__ import annotations

from typing import Any

from soft_skills_backend.platform.db.repositories import SqlAlchemyWorkflowEventRepository
from soft_skills_backend.platform.observability.events import WorkflowEvent


class CatalogEventRecorder:
    """Record catalog workflow events with stable workflow IDs."""

    def __init__(self, workflow_events: SqlAlchemyWorkflowEventRepository) -> None:
        self._workflow_events = workflow_events

    def record(
        self,
        event_type: str,
        *,
        request_id: str | None,
        trace_id: str | None,
        workflow_id: str | None,
        payload: dict[str, Any],
        error_code: str | None = None,
    ) -> None:
        self._workflow_events.record(
            WorkflowEvent(
                event_type=event_type,
                request_id=request_id,
                trace_id=trace_id,
                workflow_id=workflow_id
                or payload.get("collection_id")
                or payload.get("scenario_id")
                or payload.get("generation_artifact_id"),
                error_code=error_code,
                payload=payload,
            )
        )
