"""Collection browse and draft-authoring endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query, Request

from soft_skills_backend.entrypoints.http.dependencies import (
    get_catalog_service,
    optional_actor,
    require_actor,
)
from soft_skills_backend.entrypoints.http.schemas import ApiEnvelope, ok_response
from soft_skills_backend.modules.catalog import (
    CollectionCreateCommand,
    CollectionLifecycleCommand,
    CollectionListFilters,
    CollectionView,
    PromptItemCreateCommand,
    PromptItemView,
    ScenarioCreateCommand,
    ScenarioView,
)
from soft_skills_backend.modules.practice.models import PracticeCorrelation

router = APIRouter()


def _correlation_from_request(request: Request) -> PracticeCorrelation:
    return PracticeCorrelation(
        request_id=getattr(request.state, "request_id", ""),
        trace_id=getattr(request.state, "trace_id", ""),
        workflow_id=getattr(request.state, "workflow_id", None),
    )


@router.get("", response_model=ApiEnvelope[list[CollectionView]])
async def list_collections(
    request: Request,
    difficulty: str | None = Query(default=None),
    skill_slug: str | None = Query(default=None),
    competency_slug: str | None = Query(default=None),
    include_private: bool = Query(default=True),
) -> ApiEnvelope[list[CollectionView]]:
    service = get_catalog_service(request)
    actor = optional_actor(request)
    filters = CollectionListFilters(
        difficulty=difficulty,
        skill_slug=skill_slug,
        competency_slug=competency_slug,
        include_private=include_private,
    )
    return ok_response(request, service.list_collections(actor, filters))


@router.post("", response_model=ApiEnvelope[CollectionView])
async def create_collection(
    request: Request, command: CollectionCreateCommand
) -> ApiEnvelope[CollectionView]:
    actor = require_actor(request)
    service = get_catalog_service(request)
    correlation = _correlation_from_request(request)
    payload = await service.create_collection(
        actor,
        request_id=correlation.request_id,
        trace_id=correlation.trace_id,
        workflow_id=correlation.workflow_id,
        command=command,
    )
    return ok_response(request, payload)


@router.get("/{collection_id}", response_model=ApiEnvelope[CollectionView])
async def get_collection(request: Request, collection_id: str) -> ApiEnvelope[CollectionView]:
    actor = optional_actor(request)
    service = get_catalog_service(request)
    return ok_response(request, service.get_collection(actor, collection_id))


@router.patch("/{collection_id}/lifecycle", response_model=ApiEnvelope[CollectionView])
async def update_collection_lifecycle(
    request: Request, collection_id: str, command: CollectionLifecycleCommand
) -> ApiEnvelope[CollectionView]:
    actor = require_actor(request)
    service = get_catalog_service(request)
    correlation = _correlation_from_request(request)
    payload = await service.update_collection_lifecycle(
        actor,
        request_id=correlation.request_id,
        trace_id=correlation.trace_id,
        workflow_id=correlation.workflow_id,
        collection_id=collection_id,
        command=command,
    )
    return ok_response(request, payload)


@router.post("/{collection_id}/prompt-items", response_model=ApiEnvelope[PromptItemView])
async def add_prompt_item(
    request: Request, collection_id: str, command: PromptItemCreateCommand
) -> ApiEnvelope[PromptItemView]:
    actor = require_actor(request)
    service = get_catalog_service(request)
    correlation = _correlation_from_request(request)
    payload = await service.add_prompt_item(
        actor,
        request_id=correlation.request_id,
        trace_id=correlation.trace_id,
        workflow_id=correlation.workflow_id,
        collection_id=collection_id,
        command=command,
    )
    return ok_response(request, payload)


@router.post("/{collection_id}/scenarios", response_model=ApiEnvelope[ScenarioView])
async def add_scenario(
    request: Request, collection_id: str, command: ScenarioCreateCommand
) -> ApiEnvelope[ScenarioView]:
    actor = require_actor(request)
    service = get_catalog_service(request)
    correlation = _correlation_from_request(request)
    payload = await service.add_scenario(
        actor,
        request_id=correlation.request_id,
        trace_id=correlation.trace_id,
        workflow_id=correlation.workflow_id,
        collection_id=collection_id,
        command=command,
    )
    return ok_response(request, payload)
