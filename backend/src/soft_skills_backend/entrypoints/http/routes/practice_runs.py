"""Aggregate practice run endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request

from soft_skills_backend.entrypoints.http.dependencies import get_practice_service, require_actor
from soft_skills_backend.entrypoints.http.routes.attempts import _correlation_from_request
from soft_skills_backend.entrypoints.http.schemas import ApiEnvelope, ok_response
from soft_skills_backend.modules.practice.models import (
    PracticeRunListItemView,
    PracticeRunView,
    StartPracticeRunCommand,
)

router = APIRouter()


@router.post("", response_model=ApiEnvelope[PracticeRunView])
async def start_practice_run(
    request: Request,
    command: StartPracticeRunCommand,
) -> ApiEnvelope[PracticeRunView]:
    actor = require_actor(request)
    service = get_practice_service(request)
    payload = await service.start_practice_run(actor, _correlation_from_request(request), command)
    return ok_response(request, payload)


@router.get("", response_model=ApiEnvelope[list[PracticeRunListItemView]])
async def list_practice_runs(request: Request) -> ApiEnvelope[list[PracticeRunListItemView]]:
    actor = require_actor(request)
    service = get_practice_service(request)
    return ok_response(request, service.list_practice_runs(actor))


@router.get("/{run_id}", response_model=ApiEnvelope[PracticeRunView])
async def get_practice_run(request: Request, run_id: str) -> ApiEnvelope[PracticeRunView]:
    actor = require_actor(request)
    service = get_practice_service(request)
    return ok_response(request, service.get_practice_run(actor, run_id))
