"""Skill, competency, and rubric endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request

from soft_skills_backend.api.dependencies import get_taxonomy_service, require_admin_actor
from soft_skills_backend.api.schemas import ApiEnvelope, ok_response
from soft_skills_backend.application.taxonomy import TaxonomySnapshot

router = APIRouter()


@router.get("/catalog", response_model=ApiEnvelope[TaxonomySnapshot])
async def get_catalog(request: Request) -> ApiEnvelope[TaxonomySnapshot]:
    service = get_taxonomy_service(request)
    return ok_response(request, service.snapshot())


@router.post("/bootstrap-canon", response_model=ApiEnvelope[TaxonomySnapshot])
async def bootstrap_catalog(request: Request) -> ApiEnvelope[TaxonomySnapshot]:
    require_admin_actor(request)
    service = get_taxonomy_service(request)
    return ok_response(request, service.bootstrap())
