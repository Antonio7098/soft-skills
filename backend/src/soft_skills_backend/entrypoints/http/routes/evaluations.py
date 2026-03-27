"""Evaluation endpoints."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Query, Request

from soft_skills_backend.entrypoints.http.dependencies import (
    get_evaluation_service,
    require_actor,
)
from soft_skills_backend.entrypoints.http.schemas import ApiEnvelope, ok_response
from soft_skills_backend.modules.evaluation import (
    BenchmarkDashboardView,
    EvaluationCaseDetailView,
    EvaluationComparisonView,
    EvaluationDashboardView,
    EvaluationRunCommand,
    EvaluationRunView,
    EvaluationSuiteView,
)

router = APIRouter()


@router.get("/suites", response_model=ApiEnvelope[list[EvaluationSuiteView]])
async def list_evaluation_suites(
    request: Request,
) -> ApiEnvelope[list[EvaluationSuiteView]]:
    actor = require_actor(request)
    service = get_evaluation_service(request)
    return ok_response(request, service.list_suites(actor))


@router.get("/runs", response_model=ApiEnvelope[list[EvaluationRunView]])
async def list_evaluation_runs(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
) -> ApiEnvelope[list[EvaluationRunView]]:
    actor = require_actor(request)
    service = get_evaluation_service(request)
    return ok_response(request, service.list_runs(actor, limit=limit))


@router.get("/runs/compare", response_model=ApiEnvelope[EvaluationComparisonView])
async def compare_evaluation_runs(
    request: Request,
    run_ids: str | None = Query(default=None),
    from_date: datetime | None = Query(default=None),
    to_date: datetime | None = Query(default=None),
) -> ApiEnvelope[EvaluationComparisonView]:
    actor = require_actor(request)
    service = get_evaluation_service(request)
    run_id_list = [rid.strip() for rid in run_ids.split(",")] if run_ids else None
    return ok_response(
        request,
        service.compare_runs(actor, run_ids=run_id_list, from_date=from_date, to_date=to_date),
    )


@router.get("/runs/{run_id}", response_model=ApiEnvelope[EvaluationRunView])
async def get_evaluation_run(
    request: Request,
    run_id: str,
) -> ApiEnvelope[EvaluationRunView]:
    actor = require_actor(request)
    service = get_evaluation_service(request)
    return ok_response(request, service.get_run(actor, run_id))


@router.post("/runs", response_model=ApiEnvelope[EvaluationRunView])
async def execute_evaluation_run(
    request: Request,
    command: EvaluationRunCommand,
) -> ApiEnvelope[EvaluationRunView]:
    actor = require_actor(request)
    service = get_evaluation_service(request)
    payload = await service.execute(
        actor,
        request_id=getattr(request.state, "request_id", ""),
        trace_id=getattr(request.state, "trace_id", ""),
        workflow_id=getattr(request.state, "workflow_id", "") or f"evaluation:{command.suite_id}",
        command=command,
    )
    return ok_response(request, payload)


@router.get("/dashboard", response_model=ApiEnvelope[EvaluationDashboardView])
async def get_evaluation_dashboard(
    request: Request,
    from_date: datetime | None = Query(default=None),
    to_date: datetime | None = Query(default=None),
) -> ApiEnvelope[EvaluationDashboardView]:
    actor = require_actor(request)
    service = get_evaluation_service(request)
    return ok_response(request, service.get_dashboard(actor, from_date=from_date, to_date=to_date))


@router.get("/benchmark", response_model=ApiEnvelope[BenchmarkDashboardView])
async def get_benchmark_dashboard(
    request: Request,
    from_date: datetime | None = Query(default=None),
    to_date: datetime | None = Query(default=None),
) -> ApiEnvelope[BenchmarkDashboardView]:
    actor = require_actor(request)
    service = get_evaluation_service(request)
    return ok_response(
        request,
        service.get_benchmark_dashboard(actor, from_date=from_date, to_date=to_date),
    )


@router.get("/cases/{case_id}", response_model=ApiEnvelope[EvaluationCaseDetailView])
async def get_evaluation_case_detail(
    request: Request,
    case_id: str,
) -> ApiEnvelope[EvaluationCaseDetailView]:
    actor = require_actor(request)
    service = get_evaluation_service(request)
    return ok_response(request, service.get_case_detail(actor, case_id))
