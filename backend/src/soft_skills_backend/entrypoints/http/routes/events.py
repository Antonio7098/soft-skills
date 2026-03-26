"""Workflow events CRUD endpoints."""

from __future__ import annotations

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
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> ApiEnvelope[PaginatedWorkflowEventsView]:
    require_admin_actor(request)
    service = get_events_service(request)
    return ok_response(
        request,
        service.list_events(
            event_type=event_type,
            trace_id=trace_id,
            workflow_id=workflow_id,
            request_id=request_id,
            error_code=error_code,
            offset=offset,
            limit=limit,
        ),
    )


@router.get("/{event_id}", response_model=ApiEnvelope[WorkflowEventView])
async def get_event(request: Request, event_id: str) -> ApiEnvelope[WorkflowEventView]:
    require_admin_actor(request)
    service = get_events_service(request)
    result = service.get_event(event_id)
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
    require_admin_actor(request)
    service = get_events_service(request)
    result = service.update_event(event_id, command)
    if result is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Event not found")
    return ok_response(request, result)


@router.delete("/{event_id}", response_model=ApiEnvelope[dict[str, str]])
async def delete_event(request: Request, event_id: str) -> ApiEnvelope[dict[str, str]]:
    require_admin_actor(request)
    service = get_events_service(request)
    deleted = service.delete_event(event_id)
    if not deleted:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Event not found")
    return ok_response(request, {"status": "deleted"})
