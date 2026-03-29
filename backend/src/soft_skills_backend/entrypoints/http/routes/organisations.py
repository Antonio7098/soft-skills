"""Organisation management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query, Request

from soft_skills_backend.entrypoints.http.dependencies import (
    get_catalog_service,
    get_organisation_service,
    require_actor,
    require_org_admin_actor,
)
from soft_skills_backend.entrypoints.http.schemas import ApiEnvelope, ok_response
from soft_skills_backend.modules.catalog import CollectionListFilters, CollectionView
from soft_skills_backend.modules.organisations import (
    AddMemberCommand,
    CreateOrganisationCommand,
    CreateOrgCompetencyCommand,
    CreateOrgRubricCommand,
    CreateOrgSkillCommand,
    OrganisationMemberView,
    OrganisationView,
    OrgCompetencyView,
    OrgRubricView,
    OrgSkillView,
    UpdateMemberCommand,
    UpdateOrganisationCommand,
    UpdateOrgCompetencyCommand,
    UpdateOrgRubricCommand,
    UpdateOrgSkillCommand,
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
    actor = await require_actor(request)
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
    actor = await require_actor(request)
    service = get_organisation_service(request)
    return ok_response(request, service.get_organisation(actor, organisation_id))


@router.patch("/{organisation_id}", response_model=ApiEnvelope[OrganisationView])
async def update_organisation(
    request: Request, organisation_id: str, command: UpdateOrganisationCommand
) -> ApiEnvelope[OrganisationView]:
    actor = await require_org_admin_actor(request)
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
    actor = await require_org_admin_actor(request)
    service = get_organisation_service(request)
    return ok_response(request, service.list_members(actor, organisation_id))


@router.post("/{organisation_id}/members", response_model=ApiEnvelope[OrganisationMemberView])
async def add_member(
    request: Request, organisation_id: str, command: AddMemberCommand
) -> ApiEnvelope[OrganisationMemberView]:
    actor = await require_org_admin_actor(request)
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
    actor = await require_org_admin_actor(request)
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
    actor = await require_org_admin_actor(request)
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


@router.get("/{organisation_id}/collections", response_model=ApiEnvelope[list[CollectionView]])
async def list_org_collections(
    request: Request,
    organisation_id: str,
    difficulty: str | None = Query(default=None),
    skill_slug: str | None = Query(default=None),
    competency_slug: str | None = Query(default=None),
) -> ApiEnvelope[list[CollectionView]]:
    actor = await require_actor(request)
    service = get_catalog_service(request)
    filters = CollectionListFilters(
        difficulty=difficulty,
        skill_slug=skill_slug,
        competency_slug=competency_slug,
        include_private=False,
        organisation_id=organisation_id,
    )
    return ok_response(request, service.list_collections(actor, filters))


@router.post("/{organisation_id}/skills", response_model=ApiEnvelope[OrgSkillView])
async def create_org_skill(
    request: Request,
    organisation_id: str,
    command: CreateOrgSkillCommand,
) -> ApiEnvelope[OrgSkillView]:
    actor = await require_org_admin_actor(request)
    service = get_organisation_service(request)
    correlation = _correlation_from_request(request)
    payload = service.create_org_skill(
        actor,
        request_id=correlation.request_id,
        trace_id=correlation.trace_id,
        workflow_id=correlation.workflow_id,
        organisation_id=organisation_id,
        command=command,
    )
    return ok_response(request, payload)


@router.get("/{organisation_id}/skills", response_model=ApiEnvelope[list[OrgSkillView]])
async def list_org_skills(
    request: Request,
    organisation_id: str,
) -> ApiEnvelope[list[OrgSkillView]]:
    actor = await require_org_admin_actor(request)
    service = get_organisation_service(request)
    return ok_response(request, service.list_org_skills(actor, organisation_id))


@router.get("/{organisation_id}/skills/{skill_slug}", response_model=ApiEnvelope[OrgSkillView])
async def get_org_skill(
    request: Request,
    organisation_id: str,
    skill_slug: str,
) -> ApiEnvelope[OrgSkillView]:
    actor = await require_org_admin_actor(request)
    service = get_organisation_service(request)
    return ok_response(request, service.get_org_skill(actor, organisation_id, skill_slug))


@router.patch("/{organisation_id}/skills/{skill_slug}", response_model=ApiEnvelope[OrgSkillView])
async def update_org_skill(
    request: Request,
    organisation_id: str,
    skill_slug: str,
    command: UpdateOrgSkillCommand,
) -> ApiEnvelope[OrgSkillView]:
    actor = await require_org_admin_actor(request)
    service = get_organisation_service(request)
    correlation = _correlation_from_request(request)
    payload = service.update_org_skill(
        actor,
        request_id=correlation.request_id,
        trace_id=correlation.trace_id,
        workflow_id=correlation.workflow_id,
        organisation_id=organisation_id,
        skill_slug=skill_slug,
        command=command,
    )
    return ok_response(request, payload)


@router.delete("/{organisation_id}/skills/{skill_slug}")
async def delete_org_skill(
    request: Request,
    organisation_id: str,
    skill_slug: str,
) -> ApiEnvelope[None]:
    actor = await require_org_admin_actor(request)
    service = get_organisation_service(request)
    correlation = _correlation_from_request(request)
    service.delete_org_skill(
        actor,
        request_id=correlation.request_id,
        trace_id=correlation.trace_id,
        workflow_id=correlation.workflow_id,
        organisation_id=organisation_id,
        skill_slug=skill_slug,
    )
    return ok_response(request, None)


@router.post("/{organisation_id}/competencies", response_model=ApiEnvelope[OrgCompetencyView])
async def create_org_competency(
    request: Request,
    organisation_id: str,
    command: CreateOrgCompetencyCommand,
) -> ApiEnvelope[OrgCompetencyView]:
    actor = await require_org_admin_actor(request)
    service = get_organisation_service(request)
    correlation = _correlation_from_request(request)
    payload = service.create_org_competency(
        actor,
        request_id=correlation.request_id,
        trace_id=correlation.trace_id,
        workflow_id=correlation.workflow_id,
        organisation_id=organisation_id,
        command=command,
    )
    return ok_response(request, payload)


@router.get("/{organisation_id}/competencies", response_model=ApiEnvelope[list[OrgCompetencyView]])
async def list_org_competencies(
    request: Request,
    organisation_id: str,
) -> ApiEnvelope[list[OrgCompetencyView]]:
    actor = await require_org_admin_actor(request)
    service = get_organisation_service(request)
    return ok_response(request, service.list_org_competencies(actor, organisation_id))


@router.get(
    "/{organisation_id}/competencies/{competency_slug}",
    response_model=ApiEnvelope[OrgCompetencyView],
)
async def get_org_competency(
    request: Request,
    organisation_id: str,
    competency_slug: str,
) -> ApiEnvelope[OrgCompetencyView]:
    actor = await require_org_admin_actor(request)
    service = get_organisation_service(request)
    return ok_response(request, service.get_org_competency(actor, organisation_id, competency_slug))


@router.patch(
    "/{organisation_id}/competencies/{competency_slug}",
    response_model=ApiEnvelope[OrgCompetencyView],
)
async def update_org_competency(
    request: Request,
    organisation_id: str,
    competency_slug: str,
    command: UpdateOrgCompetencyCommand,
) -> ApiEnvelope[OrgCompetencyView]:
    actor = await require_org_admin_actor(request)
    service = get_organisation_service(request)
    correlation = _correlation_from_request(request)
    payload = service.update_org_competency(
        actor,
        request_id=correlation.request_id,
        trace_id=correlation.trace_id,
        workflow_id=correlation.workflow_id,
        organisation_id=organisation_id,
        competency_slug=competency_slug,
        command=command,
    )
    return ok_response(request, payload)


@router.delete("/{organisation_id}/competencies/{competency_slug}")
async def delete_org_competency(
    request: Request,
    organisation_id: str,
    competency_slug: str,
) -> ApiEnvelope[None]:
    actor = await require_org_admin_actor(request)
    service = get_organisation_service(request)
    correlation = _correlation_from_request(request)
    service.delete_org_competency(
        actor,
        request_id=correlation.request_id,
        trace_id=correlation.trace_id,
        workflow_id=correlation.workflow_id,
        organisation_id=organisation_id,
        competency_slug=competency_slug,
    )
    return ok_response(request, None)


@router.post("/{organisation_id}/rubrics", response_model=ApiEnvelope[OrgRubricView])
async def create_org_rubric(
    request: Request,
    organisation_id: str,
    command: CreateOrgRubricCommand,
) -> ApiEnvelope[OrgRubricView]:
    actor = await require_org_admin_actor(request)
    service = get_organisation_service(request)
    correlation = _correlation_from_request(request)
    payload = service.create_org_rubric(
        actor,
        request_id=correlation.request_id,
        trace_id=correlation.trace_id,
        workflow_id=correlation.workflow_id,
        organisation_id=organisation_id,
        command=command,
    )
    return ok_response(request, payload)


@router.get("/{organisation_id}/rubrics", response_model=ApiEnvelope[list[OrgRubricView]])
async def list_org_rubrics(
    request: Request,
    organisation_id: str,
) -> ApiEnvelope[list[OrgRubricView]]:
    actor = await require_org_admin_actor(request)
    service = get_organisation_service(request)
    return ok_response(request, service.list_org_rubrics(actor, organisation_id))


@router.get("/{organisation_id}/rubrics/{rubric_id}", response_model=ApiEnvelope[OrgRubricView])
async def get_org_rubric(
    request: Request,
    organisation_id: str,
    rubric_id: str,
) -> ApiEnvelope[OrgRubricView]:
    actor = await require_org_admin_actor(request)
    service = get_organisation_service(request)
    return ok_response(request, service.get_org_rubric(actor, organisation_id, rubric_id))


@router.patch("/{organisation_id}/rubrics/{rubric_id}", response_model=ApiEnvelope[OrgRubricView])
async def update_org_rubric(
    request: Request,
    organisation_id: str,
    rubric_id: str,
    command: UpdateOrgRubricCommand,
) -> ApiEnvelope[OrgRubricView]:
    actor = await require_org_admin_actor(request)
    service = get_organisation_service(request)
    correlation = _correlation_from_request(request)
    payload = service.update_org_rubric(
        actor,
        request_id=correlation.request_id,
        trace_id=correlation.trace_id,
        workflow_id=correlation.workflow_id,
        organisation_id=organisation_id,
        rubric_id=rubric_id,
        command=command,
    )
    return ok_response(request, payload)


@router.delete("/{organisation_id}/rubrics/{rubric_id}")
async def delete_org_rubric(
    request: Request,
    organisation_id: str,
    rubric_id: str,
) -> ApiEnvelope[None]:
    actor = await require_org_admin_actor(request)
    service = get_organisation_service(request)
    correlation = _correlation_from_request(request)
    service.delete_org_rubric(
        actor,
        request_id=correlation.request_id,
        trace_id=correlation.trace_id,
        workflow_id=correlation.workflow_id,
        organisation_id=organisation_id,
        rubric_id=rubric_id,
    )
    return ok_response(request, None)
