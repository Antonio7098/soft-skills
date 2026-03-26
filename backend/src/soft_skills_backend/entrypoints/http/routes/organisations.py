"""Organisation management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request

from soft_skills_backend.entrypoints.http.dependencies import (
    get_organisation_service,
    require_actor,
    require_org_admin_actor,
)
from soft_skills_backend.entrypoints.http.schemas import ApiEnvelope, ok_response
from soft_skills_backend.modules.organisations import (
    AddMemberCommand,
    CreateOrganisationCommand,
    OrganisationMemberView,
    OrganisationView,
    UpdateMemberCommand,
    UpdateOrganisationCommand,
)
from soft_skills_backend.modules.practice.models import PracticeCorrelation


def _correlation_from_request(request: Request) -> PracticeCorrelation:
    return PracticeCorrelation(
        request_id=getattr(request.state, "request_id", ""),
        trace_id=getattr(request.state, "trace_id", ""),
        workflow_id=getattr(request.state, "workflow_id", None),
    )


router = APIRouter()


@router.post("", response_model=ApiEnvelope[OrganisationView])
async def create_organisation(
    request: Request, command: CreateOrganisationCommand
) -> ApiEnvelope[OrganisationView]:
    actor = require_actor(request)
    service = get_organisation_service(request)
    correlation = _correlation_from_request(request)
    payload = service.create_organisation(
        actor,
        request_id=correlation.request_id,
        trace_id=correlation.trace_id,
        workflow_id=correlation.workflow_id,
        command=command,
    )
    return ok_response(request, payload)


@router.get("/{organisation_id}", response_model=ApiEnvelope[OrganisationView])
async def get_organisation(request: Request, organisation_id: str) -> ApiEnvelope[OrganisationView]:
    actor = require_actor(request)
    service = get_organisation_service(request)
    return ok_response(request, service.get_organisation(actor, organisation_id))


@router.patch("/{organisation_id}", response_model=ApiEnvelope[OrganisationView])
async def update_organisation(
    request: Request, organisation_id: str, command: UpdateOrganisationCommand
) -> ApiEnvelope[OrganisationView]:
    actor = require_org_admin_actor(request)
    service = get_organisation_service(request)
    correlation = _correlation_from_request(request)
    payload = service.update_organisation(
        actor,
        request_id=correlation.request_id,
        trace_id=correlation.trace_id,
        workflow_id=correlation.workflow_id,
        organisation_id=organisation_id,
        command=command,
    )
    return ok_response(request, payload)


@router.get("/{organisation_id}/members", response_model=ApiEnvelope[list[OrganisationMemberView]])
async def list_members(
    request: Request, organisation_id: str
) -> ApiEnvelope[list[OrganisationMemberView]]:
    actor = require_org_admin_actor(request)
    service = get_organisation_service(request)
    return ok_response(request, service.list_members(actor, organisation_id))


@router.post("/{organisation_id}/members", response_model=ApiEnvelope[OrganisationMemberView])
async def add_member(
    request: Request, organisation_id: str, command: AddMemberCommand
) -> ApiEnvelope[OrganisationMemberView]:
    actor = require_org_admin_actor(request)
    service = get_organisation_service(request)
    correlation = _correlation_from_request(request)
    payload = service.add_member(
        actor,
        request_id=correlation.request_id,
        trace_id=correlation.trace_id,
        workflow_id=correlation.workflow_id,
        organisation_id=organisation_id,
        command=command,
    )
    return ok_response(request, payload)


@router.patch(
    "/{organisation_id}/members/{user_id}", response_model=ApiEnvelope[OrganisationMemberView]
)
async def update_member(
    request: Request,
    organisation_id: str,
    user_id: str,
    command: UpdateMemberCommand,
) -> ApiEnvelope[OrganisationMemberView]:
    actor = require_org_admin_actor(request)
    service = get_organisation_service(request)
    correlation = _correlation_from_request(request)
    payload = service.update_member(
        actor,
        request_id=correlation.request_id,
        trace_id=correlation.trace_id,
        workflow_id=correlation.workflow_id,
        organisation_id=organisation_id,
        user_id=user_id,
        command=command,
    )
    return ok_response(request, payload)


@router.delete("/{organisation_id}/members/{user_id}")
async def remove_member(request: Request, organisation_id: str, user_id: str) -> ApiEnvelope[None]:
    actor = require_org_admin_actor(request)
    service = get_organisation_service(request)
    correlation = _correlation_from_request(request)
    service.remove_member(
        actor,
        request_id=correlation.request_id,
        trace_id=correlation.trace_id,
        workflow_id=correlation.workflow_id,
        organisation_id=organisation_id,
        user_id=user_id,
    )
    return ok_response(request, None)
