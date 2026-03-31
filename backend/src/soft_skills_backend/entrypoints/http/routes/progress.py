"""Progress endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request

from soft_skills_backend.entrypoints.http.dependencies import (
    get_progression_service,
    require_actor,
)
from soft_skills_backend.entrypoints.http.schemas import ApiEnvelope, ok_response
from soft_skills_backend.modules.progression import (
    ProgressDashboardView,
    ProgressHistoryView,
    ProgressRecalculationCommand,
    ProgressRecalculationView,
    RecommendationView,
    SkillTimelineView,
)

router = APIRouter()


@router.get("/me", response_model=ApiEnvelope[ProgressDashboardView])
async def get_my_progress(request: Request) -> ApiEnvelope[ProgressDashboardView]:
    actor = await require_actor(request)
    service = get_progression_service(request)
    return ok_response(request, service.get_dashboard(actor, actor.user_id))


@router.get("/me/recommendations", response_model=ApiEnvelope[RecommendationView])
async def get_my_recommendations(request: Request) -> ApiEnvelope[RecommendationView]:
    actor = await require_actor(request)
    service = get_progression_service(request)
    return ok_response(request, service.get_recommendation(actor, actor.user_id))


@router.get("/me/history", response_model=ApiEnvelope[ProgressHistoryView])
async def get_my_progress_history(
    request: Request,
    from_date: str | None = None,
    to_date: str | None = None,
    limit: int = 100,
) -> ApiEnvelope[ProgressHistoryView]:
    """Fetch historical progress snapshots for visualization."""
    actor = await require_actor(request)
    service = get_progression_service(request)
    return ok_response(
        request,
        service.get_progress_history(
            actor, actor.user_id, from_date=from_date, to_date=to_date, limit=limit
        ),
    )


@router.get("/me/timeline/{skill_slug}", response_model=ApiEnvelope[SkillTimelineView])
async def get_my_skill_timeline(
    request: Request,
    skill_slug: str,
    from_date: str | None = None,
    to_date: str | None = None,
    limit: int = 100,
) -> ApiEnvelope[SkillTimelineView]:
    """Fetch time-series data for a specific skill."""
    actor = await require_actor(request)
    service = get_progression_service(request)
    return ok_response(
        request,
        service.get_skill_timeline(
            actor, actor.user_id, skill_slug, from_date=from_date, to_date=to_date, limit=limit
        ),
    )


@router.post("/recalculate", response_model=ApiEnvelope[ProgressRecalculationView])
async def recalculate_progress(
    request: Request,
    command: ProgressRecalculationCommand,
) -> ApiEnvelope[ProgressRecalculationView]:
    actor = await require_actor(request)
    service = get_progression_service(request)
    payload = await service.recalculate(
        actor,
        request_id=getattr(request.state, "request_id", ""),
        trace_id=getattr(request.state, "trace_id", ""),
        workflow_id=getattr(request.state, "workflow_id", "")
        or f"progress-recalc:{command.learner_id}",
        command=command,
    )
    return ok_response(request, payload)
