"""Progress endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request

from soft_skills_backend.entrypoints.http.dependencies import (
    get_progression_service,
    require_actor,
    require_admin_actor,
)
from soft_skills_backend.entrypoints.http.schemas import ApiEnvelope, ok_response
from soft_skills_backend.modules.progression import (
    ProgressDashboardView,
    ProgressRecalculationCommand,
    ProgressRecalculationView,
    RecommendationView,
)

router = APIRouter()


@router.get("/me", response_model=ApiEnvelope[ProgressDashboardView])
async def get_my_progress(request: Request) -> ApiEnvelope[ProgressDashboardView]:
    actor = require_actor(request)
    service = get_progression_service(request)
    return ok_response(request, service.get_dashboard(actor, actor.user_id))


@router.get("/me/recommendations", response_model=ApiEnvelope[RecommendationView])
async def get_my_recommendations(request: Request) -> ApiEnvelope[RecommendationView]:
    actor = require_actor(request)
    service = get_progression_service(request)
    return ok_response(request, service.get_recommendation(actor, actor.user_id))


@router.post("/recalculate", response_model=ApiEnvelope[ProgressRecalculationView])
async def recalculate_progress(
    request: Request,
    command: ProgressRecalculationCommand,
) -> ApiEnvelope[ProgressRecalculationView]:
    actor = require_admin_actor(request)
    service = get_progression_service(request)
    payload = await service.recalculate(
        actor,
        request_id=getattr(request.state, "request_id", ""),
        trace_id=getattr(request.state, "trace_id", ""),
        workflow_id=getattr(request.state, "workflow_id", "") or f"progress-recalc:{command.learner_id}",
        command=command,
    )
    return ok_response(request, payload)
