"""Workflow events CRUD endpoints."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Query, Request

from soft_skills_backend.entrypoints.http.dependencies import get_container, require_admin_actor
from soft_skills_backend.entrypoints.http.schemas import ApiEnvelope, ok_response
from soft_skills_backend.modules.events import EventsService
from soft_skills_backend.modules.events.contracts import (
    PaginatedWorkflowEventsView,
    UpdateWorkflowEventCommand,
    WorkflowEventView,
)

router = APIRouter()


def get_events_service(request: Request) -> EventsService:
    return get_container(request).events_service


@router.get("", response_model=ApiEnvelope[PaginatedWorkflowEventsView])
async def list_events(
    request: Request,
    event_type: str | None = Query(default=None),
    trace_id: str | None = Query(default=None),
    workflow_id: str | None = Query(default=None),
    request_id: str | None = Query(default=None),
    error_code: str | None = Query(default=None),
    user_id: str | None = Query(default=None, description="Filter by user ID"),
    search: str | None = Query(
        default=None,
        description="Regex search across event_type, trace_id, workflow_id, request_id, error_code, user_id",
    ),
    from_date: datetime | None = Query(
        default=None, description="Filter events from this date (inclusive)"
    ),
    to_date: datetime | None = Query(
        default=None, description="Filter events up to this date (inclusive)"
    ),
    sort_by: str | None = Query(
        default=None,
        description="Sort field: event_type, trace_id, workflow_id, error_code, occurred_at, user_id",
    ),
    sort_order: str | None = Query(default="desc", description="Sort direction: asc or desc"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> ApiEnvelope[PaginatedWorkflowEventsView]:
    actor = await require_admin_actor(request)
    service = get_events_service(request)
    return ok_response(
        request,
        service.list_events(
            actor,
            event_type=event_type,
            trace_id=trace_id,
            workflow_id=workflow_id,
            request_id=request_id,
            error_code=error_code,
            user_id=user_id,
            search=search,
            from_date=from_date,
            to_date=to_date,
            sort_by=sort_by,
            sort_order=sort_order,
            offset=offset,
            limit=limit,
        ),
    )


@router.get("/{event_id}", response_model=ApiEnvelope[WorkflowEventView])
async def get_event(request: Request, event_id: str) -> ApiEnvelope[WorkflowEventView]:
    actor = await require_admin_actor(request)
    service = get_events_service(request)
    result = service.get_event(actor, event_id)
    if result is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Event not found")
    return ok_response(request, result)


@router.patch("/{event_id}", response_model=ApiEnvelope[WorkflowEventView])
async def update_event(
    request: Request,
    event_id: str,
    command: UpdateWorkflowEventCommand,
) -> ApiEnvelope[WorkflowEventView]:
    actor = await require_admin_actor(request)
    service = get_events_service(request)
    result = service.update_event(actor, event_id, command)
    if result is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Event not found")
    return ok_response(request, result)


@router.delete("/{event_id}", response_model=ApiEnvelope[dict[str, str]])
async def delete_event(request: Request, event_id: str) -> ApiEnvelope[dict[str, str]]:
    actor = await require_admin_actor(request)
    service = get_events_service(request)
    deleted = service.delete_event(actor, event_id)
    if not deleted:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Event not found")
    return ok_response(request, {"status": "deleted"})
