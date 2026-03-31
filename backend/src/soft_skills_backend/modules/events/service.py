"""Events service with organisation scoping."""

from __future__ import annotations

from soft_skills_backend.modules.events.contracts import (
    PaginatedWorkflowEventsView,
    UpdateWorkflowEventCommand,
    WorkflowEventListView,
    WorkflowEventView,
)
from soft_skills_backend.platform.db.repositories import SqlAlchemyWorkflowEventRepository
from soft_skills_backend.shared.auth import Actor
from soft_skills_backend.shared.errors import auth_error


class EventsService:
    def __init__(self, workflow_events: SqlAlchemyWorkflowEventRepository) -> None:
        self._workflow_events = workflow_events

    def list_events(
        self,
        actor: Actor,
        *,
        event_type: str | None = None,
        trace_id: str | None = None,
        workflow_id: str | None = None,
        request_id: str | None = None,
        error_code: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> PaginatedWorkflowEventsView:
        records = self._workflow_events.list_(
            event_type=event_type,
            trace_id=trace_id,
            workflow_id=workflow_id,
            request_id=request_id,
            error_code=error_code,
            organisation_id=actor.organisation_id,
            offset=offset,
            limit=limit,
        )
        total = self._workflow_events.count(
            event_type=event_type,
            trace_id=trace_id,
            workflow_id=workflow_id,
            request_id=request_id,
            error_code=error_code,
            organisation_id=actor.organisation_id,
        )
        items = [
            WorkflowEventListView(
                event_id=r.event_id,
                event_type=r.event_type,
                request_id=r.request_id,
                trace_id=r.trace_id,
                workflow_id=r.workflow_id,
                error_code=r.error_code,
                occurred_at=r.occurred_at.isoformat(),
            )
            for r in records
        ]
        return PaginatedWorkflowEventsView(
            items=items,
            total=total,
            offset=offset,
            limit=limit,
        )

    def get_event(self, actor: Actor, event_id: str) -> WorkflowEventView | None:
        record = self._workflow_events.get_by_id(event_id)
        if record is None:
            return None
        if (
            actor.organisation_id is not None
            and record.organisation_id is not None
            and record.organisation_id != actor.organisation_id
        ):
            raise auth_error(
                "Event is not in your organisation",
                code="SS-AUTH-004",
                status_code=403,
                details={"event_id": event_id, "organisation_id": actor.organisation_id},
            )
        return WorkflowEventView(
            event_id=record.event_id,
            event_type=record.event_type,
            request_id=record.request_id,
            trace_id=record.trace_id,
            workflow_id=record.workflow_id,
            error_code=record.error_code,
            payload=record.payload or {},
            occurred_at=record.occurred_at.isoformat(),
        )

    def update_event(
        self,
        actor: Actor,
        event_id: str,
        command: UpdateWorkflowEventCommand,
    ) -> WorkflowEventView | None:
        record = self._workflow_events.get_by_id(event_id)
        if record is None:
            return None
        if (
            actor.organisation_id is not None
            and record.organisation_id is not None
            and record.organisation_id != actor.organisation_id
        ):
            raise auth_error(
                "Event is not in your organisation",
                code="SS-AUTH-004",
                status_code=403,
                details={"event_id": event_id, "organisation_id": actor.organisation_id},
            )
        updated = self._workflow_events.update(
            event_id,
            error_code=command.error_code,
            payload=command.payload,
        )
        if updated is None:
            return None
        return WorkflowEventView(
            event_id=updated.event_id,
            event_type=updated.event_type,
            request_id=updated.request_id,
            trace_id=updated.trace_id,
            workflow_id=updated.workflow_id,
            error_code=updated.error_code,
            payload=updated.payload or {},
            occurred_at=updated.occurred_at.isoformat(),
        )

    def delete_event(self, actor: Actor, event_id: str) -> bool:
        record = self._workflow_events.get_by_id(event_id)
        if record is None:
            return False
        if (
            actor.organisation_id is not None
            and record.organisation_id is not None
            and record.organisation_id != actor.organisation_id
        ):
            raise auth_error(
                "Event is not in your organisation",
                code="SS-AUTH-004",
                status_code=403,
                details={"event_id": event_id, "organisation_id": actor.organisation_id},
            )
        return self._workflow_events.delete(event_id)
