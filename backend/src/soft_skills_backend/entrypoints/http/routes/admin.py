"""Admin verification, analytics, and audit endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query, Request

from soft_skills_backend.entrypoints.http.dependencies import (
    get_admin_service,
    require_admin_actor,
    require_verification_actor,
)
from soft_skills_backend.entrypoints.http.schemas import ApiEnvelope, ok_response
from soft_skills_backend.modules.admin import (
    AdminCollectionVerificationCommand,
    AdminFeatureCollectionCommand,
    AdminLearnerRelationshipCommand,
    AdminLearnerRelationshipView,
    AttemptAuditView,
    CohortAnalyticsView,
    CollectionVerificationAuditView,
    CollectionVerificationQueueItemView,
    CreateRubricCommand,
    CreateRubricCriterionCommand,
    LearnerAnalyticsView,
    PipelineDAGView,
    PipelineDefinitionView,
    PipelineMetricsView,
    PipelineRunSummaryView,
    PipelineTraceView,
    RubricCriterionUpdateCommand,
    RubricView,
    UpdateRubricCommand,
)
from soft_skills_backend.modules.catalog import CollectionView

router = APIRouter()


@router.get(
    "/collections/verification-queue",
    response_model=ApiEnvelope[list[CollectionVerificationQueueItemView]],
)
async def list_collection_verification_queue(
    request: Request,
) -> ApiEnvelope[list[CollectionVerificationQueueItemView]]:
    actor = require_admin_actor(request)
    service = get_admin_service(request)
    return ok_response(request, service.list_collection_verification_queue(actor))


@router.get(
    "/collections/{collection_id}/verification",
    response_model=ApiEnvelope[CollectionVerificationAuditView],
)
async def get_collection_verification(
    request: Request,
    collection_id: str,
) -> ApiEnvelope[CollectionVerificationAuditView]:
    actor = require_admin_actor(request)
    service = get_admin_service(request)
    return ok_response(request, service.get_collection_verification(actor, collection_id))


@router.post(
    "/collections/{collection_id}/verification",
    response_model=ApiEnvelope[CollectionVerificationAuditView],
)
async def update_collection_verification(
    request: Request,
    collection_id: str,
    command: AdminCollectionVerificationCommand,
) -> ApiEnvelope[CollectionVerificationAuditView]:
    actor = require_verification_actor(request, collection_id)
    service = get_admin_service(request)
    payload = service.update_collection_verification(
        actor,
        request_id=getattr(request.state, "request_id", ""),
        trace_id=getattr(request.state, "trace_id", ""),
        workflow_id=getattr(request.state, "workflow_id", None),
        collection_id=collection_id,
        command=command,
    )
    return ok_response(request, payload)


@router.get("/learners/{learner_id}/analytics", response_model=ApiEnvelope[LearnerAnalyticsView])
async def get_learner_analytics(
    request: Request,
    learner_id: str,
) -> ApiEnvelope[LearnerAnalyticsView]:
    actor = require_admin_actor(request)
    service = get_admin_service(request)
    return ok_response(request, service.get_learner_analytics(actor, learner_id))


@router.get(
    "/learners/{learner_id}/relationship",
    response_model=ApiEnvelope[AdminLearnerRelationshipView | None],
)
async def get_learner_relationship(
    request: Request,
    learner_id: str,
) -> ApiEnvelope[AdminLearnerRelationshipView | None]:
    actor = require_admin_actor(request)
    service = get_admin_service(request)
    return ok_response(request, service.get_learner_relationship(actor, learner_id))


@router.put(
    "/learners/{learner_id}/relationship",
    response_model=ApiEnvelope[AdminLearnerRelationshipView],
)
async def upsert_learner_relationship(
    request: Request,
    learner_id: str,
    command: AdminLearnerRelationshipCommand,
) -> ApiEnvelope[AdminLearnerRelationshipView]:
    actor = require_admin_actor(request)
    service = get_admin_service(request)
    return ok_response(
        request, service.upsert_learner_relationship(actor, learner_id=learner_id, command=command)
    )


@router.delete("/learners/{learner_id}/relationship", response_model=ApiEnvelope[dict[str, str]])
async def delete_learner_relationship(
    request: Request,
    learner_id: str,
) -> ApiEnvelope[dict[str, str]]:
    actor = require_admin_actor(request)
    service = get_admin_service(request)
    service.delete_learner_relationship(actor, learner_id=learner_id)
    return ok_response(request, {"status": "deleted"})


@router.get("/cohorts/analytics", response_model=ApiEnvelope[CohortAnalyticsView])
async def get_cohort_analytics(
    request: Request,
    target_role: str | None = Query(default=None),
) -> ApiEnvelope[CohortAnalyticsView]:
    actor = require_admin_actor(request)
    service = get_admin_service(request)
    return ok_response(request, service.get_cohort_analytics(actor, target_role))


@router.get("/attempts/{attempt_id}/audit", response_model=ApiEnvelope[AttemptAuditView])
async def get_attempt_audit(
    request: Request,
    attempt_id: str,
) -> ApiEnvelope[AttemptAuditView]:
    actor = require_admin_actor(request)
    service = get_admin_service(request)
    return ok_response(request, service.get_attempt_audit(actor, attempt_id))


@router.patch("/collections/{collection_id}/feature", response_model=ApiEnvelope[CollectionView])
async def feature_collection(
    request: Request,
    collection_id: str,
    command: AdminFeatureCollectionCommand,
) -> ApiEnvelope[CollectionView]:
    actor = require_admin_actor(request)
    service = get_admin_service(request)
    payload = service.feature_collection(
        actor,
        collection_id=collection_id,
        command=command,
    )
    return ok_response(request, payload)


@router.get("/rubrics", response_model=ApiEnvelope[list[RubricView]])
async def list_rubrics(
    request: Request,
) -> ApiEnvelope[list[RubricView]]:
    actor = require_admin_actor(request)
    service = get_admin_service(request)
    return ok_response(request, service.list_rubrics(actor))


@router.get("/rubrics/{rubric_id}", response_model=ApiEnvelope[RubricView])
async def get_rubric(
    request: Request,
    rubric_id: str,
) -> ApiEnvelope[RubricView]:
    actor = require_admin_actor(request)
    service = get_admin_service(request)
    return ok_response(request, service.get_rubric(actor, rubric_id))


@router.post("/rubrics", response_model=ApiEnvelope[RubricView])
async def create_rubric(
    request: Request,
    command: CreateRubricCommand,
) -> ApiEnvelope[RubricView]:
    actor = require_admin_actor(request)
    service = get_admin_service(request)
    return ok_response(request, service.create_rubric(actor, command))


@router.patch("/rubrics/{rubric_id}", response_model=ApiEnvelope[RubricView])
async def update_rubric(
    request: Request,
    rubric_id: str,
    command: UpdateRubricCommand,
) -> ApiEnvelope[RubricView]:
    actor = require_admin_actor(request)
    service = get_admin_service(request)
    return ok_response(request, service.update_rubric(actor, rubric_id, command))


@router.delete("/rubrics/{rubric_id}", response_model=ApiEnvelope[dict[str, str]])
async def delete_rubric(
    request: Request,
    rubric_id: str,
) -> ApiEnvelope[dict[str, str]]:
    actor = require_admin_actor(request)
    service = get_admin_service(request)
    service.delete_rubric(actor, rubric_id)
    return ok_response(request, {"status": "deleted"})


@router.post("/rubrics/{rubric_id}/criteria", response_model=ApiEnvelope[RubricView])
async def create_rubric_criterion(
    request: Request,
    rubric_id: str,
    command: CreateRubricCriterionCommand,
) -> ApiEnvelope[RubricView]:
    actor = require_admin_actor(request)
    service = get_admin_service(request)
    return ok_response(request, service.create_rubric_criterion(actor, rubric_id, command))


@router.patch(
    "/rubrics/{rubric_id}/criteria/{criterion_ref}", response_model=ApiEnvelope[RubricView]
)
async def update_rubric_criterion(
    request: Request,
    rubric_id: str,
    criterion_ref: str,
    command: RubricCriterionUpdateCommand,
) -> ApiEnvelope[RubricView]:
    actor = require_admin_actor(request)
    service = get_admin_service(request)
    return ok_response(
        request, service.update_rubric_criterion(actor, rubric_id, criterion_ref, command)
    )


@router.delete(
    "/rubrics/{rubric_id}/criteria/{criterion_ref}", response_model=ApiEnvelope[RubricView]
)
async def delete_rubric_criterion(
    request: Request,
    rubric_id: str,
    criterion_ref: str,
) -> ApiEnvelope[RubricView]:
    actor = require_admin_actor(request)
    service = get_admin_service(request)
    return ok_response(request, service.delete_rubric_criterion(actor, rubric_id, criterion_ref))


@router.get("/pipelines", response_model=ApiEnvelope[list[PipelineDefinitionView]])
async def list_pipelines(
    request: Request,
) -> ApiEnvelope[list[PipelineDefinitionView]]:
    actor = require_admin_actor(request)
    service = get_admin_service(request)
    return ok_response(request, service.list_pipelines(actor))


@router.get("/pipelines/{pipeline_name}", response_model=ApiEnvelope[PipelineDAGView])
async def get_pipeline_dag(
    request: Request,
    pipeline_name: str,
) -> ApiEnvelope[PipelineDAGView]:
    actor = require_admin_actor(request)
    service = get_admin_service(request)
    result = service.get_pipeline_dag(actor, pipeline_name)
    if result is None:
        from soft_skills_backend.shared.errors import domain_error

        raise domain_error(
            "Pipeline not found",
            code="SS-ORCHESTRATION-007",
            status_code=404,
            details={"pipeline_name": pipeline_name},
        )
    return ok_response(request, result)


@router.get(
    "/pipelines/{pipeline_name}/runs", response_model=ApiEnvelope[list[PipelineRunSummaryView]]
)
async def list_pipeline_runs(
    request: Request,
    pipeline_name: str,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
) -> ApiEnvelope[list[PipelineRunSummaryView]]:
    actor = require_admin_actor(request)
    service = get_admin_service(request)
    return ok_response(
        request, service.list_pipeline_runs(actor, pipeline_name, offset=offset, limit=limit)
    )


@router.get(
    "/pipelines/{pipeline_name}/runs/{pipeline_run_id}/trace",
    response_model=ApiEnvelope[PipelineTraceView],
)
async def get_pipeline_trace(
    request: Request,
    pipeline_name: str,
    pipeline_run_id: str,
) -> ApiEnvelope[PipelineTraceView]:
    actor = require_admin_actor(request)
    service = get_admin_service(request)
    result = service.get_pipeline_trace(actor, pipeline_name, pipeline_run_id)
    if result is None:
        from soft_skills_backend.shared.errors import domain_error

        raise domain_error(
            "Pipeline trace not found",
            code="SS-ORCHESTRATION-008",
            status_code=404,
            details={"pipeline_name": pipeline_name, "pipeline_run_id": pipeline_run_id},
        )
    return ok_response(request, result)


@router.get("/pipelines/{pipeline_name}/metrics", response_model=ApiEnvelope[PipelineMetricsView])
async def get_pipeline_metrics(
    request: Request,
    pipeline_name: str,
) -> ApiEnvelope[PipelineMetricsView]:
    actor = require_admin_actor(request)
    service = get_admin_service(request)
    result = service.get_pipeline_metrics(actor, pipeline_name)
    if result is None:
        from soft_skills_backend.shared.errors import domain_error

        raise domain_error(
            "Pipeline not found",
            code="SS-ORCHESTRATION-007",
            status_code=404,
            details={"pipeline_name": pipeline_name},
        )
    return ok_response(request, result)
