"""Practice attempt endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request

from soft_skills_backend.entrypoints.http.dependencies import get_practice_service, require_actor
from soft_skills_backend.entrypoints.http.schemas import ApiEnvelope, ok_response
from soft_skills_backend.modules.practice.models import (
    AttemptHistoryItemView,
    AttemptView,
    PracticeCorrelation,
    PracticeSessionView,
    ScenarioSessionView,
    StartInterviewSessionCommand,
    StartPracticeSessionCommand,
    StartScenarioSessionCommand,
    SubmitAttemptCommand,
)

router = APIRouter()


def _correlation_from_request(request: Request) -> PracticeCorrelation:
    return PracticeCorrelation(
        request_id=getattr(request.state, "request_id", ""),
        trace_id=getattr(request.state, "trace_id", ""),
        workflow_id=getattr(request.state, "workflow_id", None),
    )


@router.post("/quick-practice/sessions", response_model=ApiEnvelope[PracticeSessionView])
async def start_quick_practice_session(
    request: Request,
    command: StartPracticeSessionCommand,
) -> ApiEnvelope[PracticeSessionView]:
    actor = await require_actor(request)
    service = get_practice_service(request)
    payload = await service.start_session(actor, _correlation_from_request(request), command)
    return ok_response(request, payload)


@router.post("/interview/sessions", response_model=ApiEnvelope[PracticeSessionView])
async def start_interview_session(
    request: Request,
    command: StartInterviewSessionCommand,
) -> ApiEnvelope[PracticeSessionView]:
    actor = await require_actor(request)
    service = get_practice_service(request)
    payload = await service.start_interview_session(
        actor,
        _correlation_from_request(request),
        command,
    )
    return ok_response(request, payload)


@router.post("/scenario/sessions", response_model=ApiEnvelope[ScenarioSessionView])
async def start_scenario_session(
    request: Request,
    command: StartScenarioSessionCommand,
) -> ApiEnvelope[PracticeSessionView]:
    actor = await require_actor(request)
    service = get_practice_service(request)
    payload = await service.start_scenario_session(
        actor,
        _correlation_from_request(request),
        command,
    )
    return ok_response(request, payload)


@router.post("/scenario/sessions/{session_id}/steps", response_model=ApiEnvelope[ScenarioSessionView])
async def submit_scenario_step(
    request: Request,
    session_id: str,
    command: SubmitAttemptCommand,
) -> ApiEnvelope[ScenarioSessionView]:
    actor = await require_actor(request)
    service = get_practice_service(request)
    payload = await service.submit_scenario_step(
        actor,
        _correlation_from_request(request),
        session_id,
        command,
    )
    return ok_response(request, payload)


@router.post("/{attempt_id}/submit", response_model=ApiEnvelope[AttemptView])
async def submit_attempt(
    request: Request,
    attempt_id: str,
    command: SubmitAttemptCommand,
) -> ApiEnvelope[AttemptView]:
    actor = await require_actor(request)
    service = get_practice_service(request)
    payload = await service.submit_attempt(
        actor,
        _correlation_from_request(request),
        attempt_id,
        command,
    )
    return ok_response(request, payload)


@router.get("/history", response_model=ApiEnvelope[list[AttemptHistoryItemView]])
async def list_attempt_history(request: Request) -> ApiEnvelope[list[AttemptHistoryItemView]]:
    actor = await require_actor(request)
    service = get_practice_service(request)
    return ok_response(request, service.list_attempt_history(actor))


@router.get("/{attempt_id}", response_model=ApiEnvelope[AttemptView])
async def get_attempt(request: Request, attempt_id: str) -> ApiEnvelope[AttemptView]:
    actor = await require_actor(request)
    service = get_practice_service(request)
    return ok_response(request, service.get_attempt(actor, attempt_id))
