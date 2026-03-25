"""Practice attempt endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request

from soft_skills_backend.api.dependencies import get_practice_service, require_actor
from soft_skills_backend.api.schemas import ApiEnvelope, ok_response
from soft_skills_backend.application.practice.quick_practice import (
    AttemptView,
    PracticeCorrelation,
    QuickPracticeSessionView,
    StartInterviewSessionCommand,
    StartQuickPracticeSessionCommand,
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


@router.post("/quick-practice/sessions", response_model=ApiEnvelope[QuickPracticeSessionView])
async def start_quick_practice_session(
    request: Request,
    command: StartQuickPracticeSessionCommand,
) -> ApiEnvelope[QuickPracticeSessionView]:
    actor = require_actor(request)
    service = get_practice_service(request)
    payload = await service.start_session(actor, _correlation_from_request(request), command)
    return ok_response(request, payload)


@router.post("/interview/sessions", response_model=ApiEnvelope[QuickPracticeSessionView])
async def start_interview_session(
    request: Request,
    command: StartInterviewSessionCommand,
) -> ApiEnvelope[QuickPracticeSessionView]:
    actor = require_actor(request)
    service = get_practice_service(request)
    payload = await service.start_interview_session(
        actor,
        _correlation_from_request(request),
        command,
    )
    return ok_response(request, payload)


@router.post("/scenario/sessions", response_model=ApiEnvelope[QuickPracticeSessionView])
async def start_scenario_session(
    request: Request,
    command: StartScenarioSessionCommand,
) -> ApiEnvelope[QuickPracticeSessionView]:
    actor = require_actor(request)
    service = get_practice_service(request)
    payload = await service.start_scenario_session(
        actor,
        _correlation_from_request(request),
        command,
    )
    return ok_response(request, payload)


@router.post("/{attempt_id}/submit", response_model=ApiEnvelope[AttemptView])
async def submit_attempt(
    request: Request,
    attempt_id: str,
    command: SubmitAttemptCommand,
) -> ApiEnvelope[AttemptView]:
    actor = require_actor(request)
    service = get_practice_service(request)
    payload = await service.submit_attempt(
        actor,
        _correlation_from_request(request),
        attempt_id,
        command,
    )
    return ok_response(request, payload)


@router.get("/{attempt_id}", response_model=ApiEnvelope[AttemptView])
async def get_attempt(request: Request, attempt_id: str) -> ApiEnvelope[AttemptView]:
    actor = require_actor(request)
    service = get_practice_service(request)
    return ok_response(request, service.get_attempt(actor, attempt_id))
