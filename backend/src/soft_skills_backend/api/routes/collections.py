"""Collection browse and draft-authoring endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query, Request

from soft_skills_backend.api.dependencies import get_catalog_service, optional_actor, require_actor
from soft_skills_backend.api.schemas import ApiEnvelope, ok_response
from soft_skills_backend.application.catalog import (
    CollectionCreateCommand,
    CollectionLifecycleCommand,
    CollectionListFilters,
    CollectionView,
    PromptItemCreateCommand,
    PromptItemView,
    ScenarioCreateCommand,
    ScenarioView,
)

router = APIRouter()


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
    return ok_response(request, service.create_collection(actor, command))


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
    return ok_response(request, service.update_collection_lifecycle(actor, collection_id, command))


@router.post("/{collection_id}/prompt-items", response_model=ApiEnvelope[PromptItemView])
async def add_prompt_item(
    request: Request, collection_id: str, command: PromptItemCreateCommand
) -> ApiEnvelope[PromptItemView]:
    actor = require_actor(request)
    service = get_catalog_service(request)
    return ok_response(request, service.add_prompt_item(actor, collection_id, command))


@router.post("/{collection_id}/scenarios", response_model=ApiEnvelope[ScenarioView])
async def add_scenario(
    request: Request, collection_id: str, command: ScenarioCreateCommand
) -> ApiEnvelope[ScenarioView]:
    actor = require_actor(request)
    service = get_catalog_service(request)
    return ok_response(request, service.add_scenario(actor, collection_id, command))
