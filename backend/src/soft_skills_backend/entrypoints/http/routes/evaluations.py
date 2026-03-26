"""Evaluation endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query, Request

from soft_skills_backend.entrypoints.http.dependencies import (
    get_evaluation_service,
    require_admin_actor,
)
from soft_skills_backend.entrypoints.http.schemas import ApiEnvelope, ok_response
from soft_skills_backend.modules.evaluation import (
    EvaluationRunCommand,
    EvaluationRunView,
    EvaluationSuiteView,
)

router = APIRouter()


@router.get("/suites", response_model=ApiEnvelope[list[EvaluationSuiteView]])
async def list_evaluation_suites(
    request: Request,
) -> ApiEnvelope[list[EvaluationSuiteView]]:
    actor = require_admin_actor(request)
    service = get_evaluation_service(request)
    return ok_response(request, service.list_suites(actor))


@router.get("/runs", response_model=ApiEnvelope[list[EvaluationRunView]])
async def list_evaluation_runs(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
) -> ApiEnvelope[list[EvaluationRunView]]:
    actor = require_admin_actor(request)
    service = get_evaluation_service(request)
    return ok_response(request, service.list_runs(actor, limit=limit))


@router.get("/runs/{run_id}", response_model=ApiEnvelope[EvaluationRunView])
async def get_evaluation_run(
    request: Request,
    run_id: str,
) -> ApiEnvelope[EvaluationRunView]:
    actor = require_admin_actor(request)
    service = get_evaluation_service(request)
    return ok_response(request, service.get_run(actor, run_id))


@router.post("/runs", response_model=ApiEnvelope[EvaluationRunView])
async def execute_evaluation_run(
    request: Request,
    command: EvaluationRunCommand,
) -> ApiEnvelope[EvaluationRunView]:
    actor = require_admin_actor(request)
    service = get_evaluation_service(request)
    payload = await service.execute(
        actor,
        request_id=getattr(request.state, "request_id", ""),
        trace_id=getattr(request.state, "trace_id", ""),
        workflow_id=getattr(request.state, "workflow_id", "") or f"evaluation:{command.suite_id}",
        command=command,
    )
    return ok_response(request, payload)
