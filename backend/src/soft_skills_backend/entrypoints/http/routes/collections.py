"""Collection browse, creator workflows, and discovery endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query, Request

from soft_skills_backend.entrypoints.http.dependencies import (
    get_catalog_service,
    optional_actor,
    require_actor,
)
from soft_skills_backend.entrypoints.http.schemas import ApiEnvelope, ok_response
from soft_skills_backend.modules.catalog import (
    ChatCollectionGenerationCommand,
    ChatPromptItemGenerationCommand,
    CollectionCreateCommand,
    CollectionGenerationView,
    CollectionLifecycleCommand,
    CollectionListFilters,
    CollectionUpdateCommand,
    CollectionView,
    PromptItemCreateCommand,
    PromptItemGenerationView,
    PromptItemUpdateCommand,
    PromptItemView,
    ScenarioCreateCommand,
    ScenarioUpdateCommand,
    ScenarioView,
    StructuredCollectionGenerationCommand,
    StructuredPromptItemGenerationCommand,
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
    saved_only: bool = Query(default=False),
    discovery_tier: str | None = Query(default=None),
    author_user_id: str | None = Query(default=None),
) -> ApiEnvelope[list[CollectionView]]:
    service = get_catalog_service(request)
    actor = optional_actor(request)
    filters = CollectionListFilters(
        difficulty=difficulty,
        skill_slug=skill_slug,
        competency_slug=competency_slug,
        include_private=include_private,
        saved_only=saved_only,
        discovery_tier=discovery_tier,
        author_user_id=author_user_id,
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


@router.post("/generate/structured", response_model=ApiEnvelope[CollectionGenerationView])
async def generate_structured_draft(
    request: Request, command: StructuredCollectionGenerationCommand
) -> ApiEnvelope[CollectionGenerationView]:
    actor = require_actor(request)
    service = get_catalog_service(request)
    correlation = _correlation_from_request(request)
    payload = await service.generate_structured_draft(
        actor,
        request_id=correlation.request_id,
        trace_id=correlation.trace_id,
        workflow_id=correlation.workflow_id,
        command=command,
    )
    return ok_response(request, payload)


@router.post("/generate/chat", response_model=ApiEnvelope[CollectionGenerationView])
async def generate_chat_draft(
    request: Request, command: ChatCollectionGenerationCommand
) -> ApiEnvelope[CollectionGenerationView]:
    actor = require_actor(request)
    service = get_catalog_service(request)
    correlation = _correlation_from_request(request)
    payload = await service.generate_chat_draft(
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


@router.patch("/{collection_id}", response_model=ApiEnvelope[CollectionView])
async def update_collection(
    request: Request, collection_id: str, command: CollectionUpdateCommand
) -> ApiEnvelope[CollectionView]:
    actor = require_actor(request)
    service = get_catalog_service(request)
    correlation = _correlation_from_request(request)
    payload = await service.update_collection(
        actor,
        request_id=correlation.request_id,
        trace_id=correlation.trace_id,
        workflow_id=correlation.workflow_id,
        collection_id=collection_id,
        command=command,
    )
    return ok_response(request, payload)


@router.post("/{collection_id}/save", response_model=ApiEnvelope[CollectionView])
async def save_collection(
    request: Request, collection_id: str
) -> ApiEnvelope[CollectionView]:
    actor = require_actor(request)
    service = get_catalog_service(request)
    correlation = _correlation_from_request(request)
    payload = await service.save_collection(
        actor,
        request_id=correlation.request_id,
        trace_id=correlation.trace_id,
        workflow_id=correlation.workflow_id,
        collection_id=collection_id,
    )
    return ok_response(request, payload)


@router.delete("/{collection_id}/save", response_model=ApiEnvelope[CollectionView])
async def unsave_collection(
    request: Request, collection_id: str
) -> ApiEnvelope[CollectionView]:
    actor = require_actor(request)
    service = get_catalog_service(request)
    correlation = _correlation_from_request(request)
    payload = await service.unsave_collection(
        actor,
        request_id=correlation.request_id,
        trace_id=correlation.trace_id,
        workflow_id=correlation.workflow_id,
        collection_id=collection_id,
    )
    return ok_response(request, payload)


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


@router.post(
    "/{collection_id}/generate/prompt-items/structured",
    response_model=ApiEnvelope[PromptItemGenerationView],
)
async def generate_prompt_items_structured(
    request: Request,
    collection_id: str,
    command: StructuredPromptItemGenerationCommand,
) -> ApiEnvelope[PromptItemGenerationView]:
    actor = require_actor(request)
    service = get_catalog_service(request)
    correlation = _correlation_from_request(request)
    payload = await service.generate_prompt_items_structured(
        actor,
        request_id=correlation.request_id,
        trace_id=correlation.trace_id,
        workflow_id=correlation.workflow_id,
        collection_id=collection_id,
        command=command,
    )
    return ok_response(request, payload)


@router.post(
    "/{collection_id}/generate/prompt-items/chat",
    response_model=ApiEnvelope[PromptItemGenerationView],
)
async def generate_prompt_items_chat(
    request: Request,
    collection_id: str,
    command: ChatPromptItemGenerationCommand,
) -> ApiEnvelope[PromptItemGenerationView]:
    actor = require_actor(request)
    service = get_catalog_service(request)
    correlation = _correlation_from_request(request)
    payload = await service.generate_prompt_items_chat(
        actor,
        request_id=correlation.request_id,
        trace_id=correlation.trace_id,
        workflow_id=correlation.workflow_id,
        collection_id=collection_id,
        command=command,
    )
    return ok_response(request, payload)


@router.patch(
    "/{collection_id}/prompt-items/{prompt_item_id}",
    response_model=ApiEnvelope[PromptItemView],
)
async def update_prompt_item(
    request: Request,
    collection_id: str,
    prompt_item_id: str,
    command: PromptItemUpdateCommand,
) -> ApiEnvelope[PromptItemView]:
    actor = require_actor(request)
    service = get_catalog_service(request)
    correlation = _correlation_from_request(request)
    payload = await service.update_prompt_item(
        actor,
        request_id=correlation.request_id,
        trace_id=correlation.trace_id,
        workflow_id=correlation.workflow_id,
        collection_id=collection_id,
        prompt_item_id=prompt_item_id,
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


@router.patch(
    "/{collection_id}/scenarios/{scenario_id}",
    response_model=ApiEnvelope[ScenarioView],
)
async def update_scenario(
    request: Request,
    collection_id: str,
    scenario_id: str,
    command: ScenarioUpdateCommand,
) -> ApiEnvelope[ScenarioView]:
    actor = require_actor(request)
    service = get_catalog_service(request)
    correlation = _correlation_from_request(request)
    payload = await service.update_scenario(
        actor,
        request_id=correlation.request_id,
        trace_id=correlation.trace_id,
        workflow_id=correlation.workflow_id,
        collection_id=collection_id,
        scenario_id=scenario_id,
        command=command,
    )
    return ok_response(request, payload)
