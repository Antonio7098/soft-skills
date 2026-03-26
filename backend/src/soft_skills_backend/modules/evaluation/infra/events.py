"""Evaluation event recording helpers."""

from __future__ import annotations

from typing import Any

from soft_skills_backend.platform.db.repositories import SqlAlchemyWorkflowEventRepository
from soft_skills_backend.platform.observability.events import WorkflowEvent
from soft_skills_backend.platform.observability.logging import get_logger


class EvaluationEventRecorder:
    """Structured event recorder for evaluation workflows."""

    def __init__(self, workflow_events: SqlAlchemyWorkflowEventRepository) -> None:
        self._workflow_events = workflow_events
        self._logger = get_logger("soft_skills_backend.evaluation")

    def record(
        self,
        *,
        event_type: str,
        request_id: str,
        trace_id: str,
        workflow_id: str,
        payload: dict[str, Any],
        error_code: str | None = None,
    ) -> None:
        self._logger.info(
            event_type,
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id,
            **payload,
        )
        self._workflow_events.record(
            WorkflowEvent(
                event_type=event_type,
                request_id=request_id,
                trace_id=trace_id,
                workflow_id=workflow_id,
                error_code=error_code,
                payload=payload,
            )
        )
