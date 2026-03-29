"""Admin verification, analytics, and audit endpoints."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Query, Request
from fastapi.responses import StreamingResponse

from soft_skills_backend.entrypoints.http.dependencies import (
    get_admin_service,
    require_admin_actor,
    require_verification_actor,
)
from soft_skills_backend.entrypoints.http.schemas import ApiEnvelope, ok_response
from soft_skills_backend.modules.admin import (
    AdminAddUserCommand,
    AdminCollectionVerificationCommand,
    AdminFeatureCollectionCommand,
    AdminLearnerRelationshipCommand,
    AdminLearnerRelationshipView,
    AdminUserListView,
    AdminUserRoleCommand,
    AdminUserStatusCommand,
    AdminUserView,
    AnalyticsOverviewView,
    ArchivePromptCommand,
    AttemptAuditView,
    BulkOperationResultView,
    BulkUserOperationCommand,
    CohortAnalyticsView,
    CohortComparisonView,
    CollectionVerificationAuditView,
    CollectionVerificationQueueItemView,
    ComparePromptsCommand,
    CreatePromptCommand,
    CreateRubricCommand,
    CreateRubricCriterionCommand,
    LearnerAnalyticsView,
    PipelineDAGView,
    PipelineDefinitionView,
    PipelineMetricsView,
    PipelineRunSummaryView,
    PipelineTraceView,
    PromptAnalyticsView,
    PromptCompareView,
    PromptSummaryView,
    PromptVersionView,
    PublishPromptCommand,
    RubricCriterionUpdateCommand,
    RubricView,
    TelemetryOverviewView,
    TelemetryTraceListView,
    TelemetryTraceView,
    UpdatePromptCommand,
    UpdateRubricCommand,
    UserActivityView,
)
from soft_skills_backend.modules.catalog import CollectionView

router = APIRouter()


@router.get("/users", response_model=ApiEnvelope[AdminUserListView])
async def list_users(
    request: Request,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    search: str | None = Query(default=None),
    role: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
) -> ApiEnvelope[AdminUserListView]:
    """List users with pagination, search, and filters."""
    actor = await require_admin_actor(request)
    service = get_admin_service(request)
    return ok_response(
        request,
        service.list_users(
            actor,
            offset=offset,
            limit=limit,
            search=search,
            role=role,
            is_active=is_active,
        ),
    )


@router.get("/users/{user_id}", response_model=ApiEnvelope[AdminUserView | None])
async def get_user(
    request: Request,
    user_id: str,
) -> ApiEnvelope[AdminUserView | None]:
    """Get a specific user by ID."""
    actor = await require_admin_actor(request)
    service = get_admin_service(request)
    return ok_response(request, service.get_user(actor, user_id))


@router.put("/users/{user_id}/role", response_model=ApiEnvelope[AdminUserView])
async def update_user_role(
    request: Request,
    user_id: str,
    command: AdminUserRoleCommand,
) -> ApiEnvelope[AdminUserView]:
    """Change a user's role within the organisation."""
    actor = await require_admin_actor(request)
    service = get_admin_service(request)
    return ok_response(request, service.update_user_role(actor, user_id, command))


@router.patch("/users/{user_id}/status", response_model=ApiEnvelope[AdminUserView])
async def update_user_status(
    request: Request,
    user_id: str,
    command: AdminUserStatusCommand,
) -> ApiEnvelope[AdminUserView]:
    """Suspend or activate a user."""
    actor = await require_admin_actor(request)
    service = get_admin_service(request)
    return ok_response(request, service.update_user_status(actor, user_id, command))


@router.post("/users", response_model=ApiEnvelope[AdminUserView])
async def add_user_to_org(
    request: Request,
    command: AdminAddUserCommand,
) -> ApiEnvelope[AdminUserView]:
    """Add a user to an organisation."""
    actor = await require_admin_actor(request)
    service = get_admin_service(request)
    return ok_response(request, service.add_user_to_org(actor, command))


@router.post("/users/bulk", response_model=ApiEnvelope[BulkOperationResultView])
async def bulk_user_operation(
    request: Request,
    command: BulkUserOperationCommand,
) -> ApiEnvelope[BulkOperationResultView]:
    """Perform bulk operations on users."""
    actor = await require_admin_actor(request)
    service = get_admin_service(request)
    return ok_response(request, service.bulk_user_operation(actor, command))


@router.get("/users/{user_id}/activity", response_model=ApiEnvelope[UserActivityView | None])
async def get_user_activity(
    request: Request,
    user_id: str,
) -> ApiEnvelope[UserActivityView | None]:
    """Get activity summary for a user."""
    actor = await require_admin_actor(request)
    service = get_admin_service(request)
    return ok_response(request, service.get_user_activity(actor, user_id))


@router.get("/prompts", response_model=ApiEnvelope[list[PromptSummaryView]])
async def list_prompts(
    request: Request,
) -> ApiEnvelope[list[PromptSummaryView]]:
    actor = await require_admin_actor(request)
    service = get_admin_service(request)
    return ok_response(request, service.list_prompts(actor))


@router.get("/prompts/{name}/versions", response_model=ApiEnvelope[list[PromptVersionView]])
async def list_prompt_versions(
    request: Request,
    name: str,
) -> ApiEnvelope[list[PromptVersionView]]:
    actor = await require_admin_actor(request)
    service = get_admin_service(request)
    return ok_response(request, service.list_prompt_versions(actor, name))


@router.get("/prompts/{name}/versions/{version}", response_model=ApiEnvelope[PromptVersionView])
async def get_prompt_version(
    request: Request,
    name: str,
    version: str,
) -> ApiEnvelope[PromptVersionView]:
    actor = await require_admin_actor(request)
    service = get_admin_service(request)
    result = service.get_prompt_version(actor, name, version)
    if result is None:
        from soft_skills_backend.shared.errors import domain_error

        raise domain_error(
            "Prompt version not found",
            code="SS-DOMAIN-009",
            status_code=404,
            details={"name": name, "version": version},
        )
    return ok_response(request, result)


@router.post("/prompts", response_model=ApiEnvelope[PromptVersionView])
async def create_prompt(
    request: Request,
    command: CreatePromptCommand,
) -> ApiEnvelope[PromptVersionView]:
    actor = await require_admin_actor(request)
    service = get_admin_service(request)
    return ok_response(request, service.create_prompt(actor, command))


@router.put("/prompts/{name}/versions/{version}", response_model=ApiEnvelope[PromptVersionView])
async def update_prompt(
    request: Request,
    name: str,
    version: str,
    command: UpdatePromptCommand,
) -> ApiEnvelope[PromptVersionView]:
    actor = await require_admin_actor(request)
    service = get_admin_service(request)
    result = service.update_prompt(actor, name, version, command)
    if result is None:
        from soft_skills_backend.shared.errors import domain_error

        raise domain_error(
            "Prompt version not found",
            code="SS-DOMAIN-009",
            status_code=404,
            details={"name": name, "version": version},
        )
    return ok_response(request, result)


@router.post(
    "/prompts/{name}/versions/{version}/publish", response_model=ApiEnvelope[PromptVersionView]
)
async def publish_prompt(
    request: Request,
    name: str,
    version: str,
    command: PublishPromptCommand,
) -> ApiEnvelope[PromptVersionView]:
    actor = await require_admin_actor(request)
    service = get_admin_service(request)
    result = service.publish_prompt(actor, name, version, command)
    if result is None:
        from soft_skills_backend.shared.errors import domain_error

        raise domain_error(
            "Prompt version not found",
            code="SS-DOMAIN-009",
            status_code=404,
            details={"name": name, "version": version},
        )
    return ok_response(request, result)


@router.post(
    "/prompts/{name}/versions/{version}/archive", response_model=ApiEnvelope[PromptVersionView]
)
async def archive_prompt(
    request: Request,
    name: str,
    version: str,
    command: ArchivePromptCommand,
) -> ApiEnvelope[PromptVersionView]:
    actor = await require_admin_actor(request)
    service = get_admin_service(request)
    result = service.archive_prompt(actor, name, version, command)
    if result is None:
        from soft_skills_backend.shared.errors import domain_error

        raise domain_error(
            "Prompt version not found",
            code="SS-DOMAIN-009",
            status_code=404,
            details={"name": name, "version": version},
        )
    return ok_response(request, result)


@router.get(
    "/prompts/{name}/versions/{version}/analytics",
    response_model=ApiEnvelope[PromptAnalyticsView],
)
async def get_prompt_analytics(
    request: Request,
    name: str,
    version: str,
) -> ApiEnvelope[PromptAnalyticsView]:
    actor = await require_admin_actor(request)
    service = get_admin_service(request)
    result = service.get_prompt_analytics(actor, name, version)
    if result is None:
        from soft_skills_backend.shared.errors import domain_error

        raise domain_error(
            "Prompt version not found",
            code="SS-DOMAIN-009",
            status_code=404,
            details={"name": name, "version": version},
        )
    return ok_response(request, result)


@router.post("/prompts/compare", response_model=ApiEnvelope[PromptCompareView])
async def compare_prompts(
    request: Request,
    command: ComparePromptsCommand,
) -> ApiEnvelope[PromptCompareView]:
    actor = await require_admin_actor(request)
    service = get_admin_service(request)
    result = service.compare_prompts(actor, command)
    if result is None:
        from soft_skills_backend.shared.errors import domain_error

        raise domain_error(
            "One or more prompt versions were not found",
            code="SS-DOMAIN-009",
            status_code=404,
            details={
                "name": command.name,
                "version_a": command.version_a,
                "version_b": command.version_b,
            },
        )
    return ok_response(request, result)


@router.get(
    "/collections/verification-queue",
    response_model=ApiEnvelope[list[CollectionVerificationQueueItemView]],
)
async def list_collection_verification_queue(
    request: Request,
) -> ApiEnvelope[list[CollectionVerificationQueueItemView]]:
    actor = await require_admin_actor(request)
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
    actor = await require_admin_actor(request)
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
    actor = await require_verification_actor(request, collection_id)
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
    from_date: datetime | None = Query(default=None),
    to_date: datetime | None = Query(default=None),
) -> ApiEnvelope[LearnerAnalyticsView]:
    actor = await require_admin_actor(request)
    service = get_admin_service(request)
    return ok_response(
        request, service.get_learner_analytics(actor, learner_id, from_date, to_date)
    )


@router.get(
    "/learners/{learner_id}/relationship",
    response_model=ApiEnvelope[AdminLearnerRelationshipView | None],
)
async def get_learner_relationship(
    request: Request,
    learner_id: str,
) -> ApiEnvelope[AdminLearnerRelationshipView | None]:
    actor = await require_admin_actor(request)
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
    actor = await require_admin_actor(request)
    service = get_admin_service(request)
    return ok_response(
        request, service.upsert_learner_relationship(actor, learner_id=learner_id, command=command)
    )


@router.delete("/learners/{learner_id}/relationship", response_model=ApiEnvelope[dict[str, str]])
async def delete_learner_relationship(
    request: Request,
    learner_id: str,
) -> ApiEnvelope[dict[str, str]]:
    actor = await require_admin_actor(request)
    service = get_admin_service(request)
    service.delete_learner_relationship(actor, learner_id=learner_id)
    return ok_response(request, {"status": "deleted"})


@router.get("/cohorts/analytics", response_model=ApiEnvelope[CohortAnalyticsView])
async def get_cohort_analytics(
    request: Request,
    target_role: str | None = Query(default=None),
    from_date: datetime | None = Query(default=None),
    to_date: datetime | None = Query(default=None),
) -> ApiEnvelope[CohortAnalyticsView]:
    actor = await require_admin_actor(request)
    service = get_admin_service(request)
    return ok_response(
        request, service.get_cohort_analytics(actor, target_role, from_date, to_date)
    )


@router.get("/analytics/overview", response_model=ApiEnvelope[AnalyticsOverviewView])
async def get_analytics_overview(
    request: Request,
    from_date: datetime | None = Query(default=None),
    to_date: datetime | None = Query(default=None),
) -> ApiEnvelope[AnalyticsOverviewView]:
    actor = await require_admin_actor(request)
    service = get_admin_service(request)
    return ok_response(request, service.get_analytics_overview(actor, from_date, to_date))


@router.get("/cohorts/comparison", response_model=ApiEnvelope[CohortComparisonView])
async def get_cohort_comparison(
    request: Request,
    cohort_keys: str | None = Query(default=None),
    from_date: datetime | None = Query(default=None),
    to_date: datetime | None = Query(default=None),
) -> ApiEnvelope[CohortComparisonView]:
    actor = await require_admin_actor(request)
    service = get_admin_service(request)
    cohort_keys_list = [k.strip() for k in cohort_keys.split(",")] if cohort_keys else []
    return ok_response(
        request, service.get_cohort_comparison(actor, cohort_keys_list, from_date, to_date)
    )


@router.get("/analytics/export")
async def export_analytics(
    request: Request,
    format: str = Query(default="json"),
    from_date: datetime | None = Query(default=None),
    to_date: datetime | None = Query(default=None),
) -> StreamingResponse:
    actor = await require_admin_actor(request)
    service = get_admin_service(request)
    overview = service.get_analytics_overview(actor, from_date, to_date)
    if format == "csv":
        csv_lines = [
            "total_learners,active_learners_30d,total_sessions,total_attempts,submitted_attempts,validated_assessments,rejected_assessments,avg_validated_score",
            f"{overview.total_learners},{overview.active_learners_30d},{overview.total_sessions},{overview.total_attempts},{overview.submitted_attempts},{overview.validated_assessments},{overview.rejected_assessments},{overview.avg_validated_score}",
        ]
        content = "\n".join(csv_lines)
        return StreamingResponse(
            iter([content]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=analytics_overview.csv"},
        )

    return StreamingResponse(
        iter([overview.model_dump_json()]),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=analytics_overview.json"},
    )


@router.get("/attempts/{attempt_id}/audit", response_model=ApiEnvelope[AttemptAuditView])
async def get_attempt_audit(
    request: Request,
    attempt_id: str,
) -> ApiEnvelope[AttemptAuditView]:
    actor = await require_admin_actor(request)
    service = get_admin_service(request)
    return ok_response(request, service.get_attempt_audit(actor, attempt_id))


@router.patch("/collections/{collection_id}/feature", response_model=ApiEnvelope[CollectionView])
async def feature_collection(
    request: Request,
    collection_id: str,
    command: AdminFeatureCollectionCommand,
) -> ApiEnvelope[CollectionView]:
    actor = await require_admin_actor(request)
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
    actor = await require_admin_actor(request)
    service = get_admin_service(request)
    return ok_response(request, service.list_rubrics(actor))


@router.get("/rubrics/{rubric_id}", response_model=ApiEnvelope[RubricView])
async def get_rubric(
    request: Request,
    rubric_id: str,
) -> ApiEnvelope[RubricView]:
    actor = await require_admin_actor(request)
    service = get_admin_service(request)
    return ok_response(request, service.get_rubric(actor, rubric_id))


@router.post("/rubrics", response_model=ApiEnvelope[RubricView])
async def create_rubric(
    request: Request,
    command: CreateRubricCommand,
) -> ApiEnvelope[RubricView]:
    actor = await require_admin_actor(request)
    service = get_admin_service(request)
    return ok_response(request, service.create_rubric(actor, command))


@router.patch("/rubrics/{rubric_id}", response_model=ApiEnvelope[RubricView])
async def update_rubric(
    request: Request,
    rubric_id: str,
    command: UpdateRubricCommand,
) -> ApiEnvelope[RubricView]:
    actor = await require_admin_actor(request)
    service = get_admin_service(request)
    return ok_response(request, service.update_rubric(actor, rubric_id, command))


@router.delete("/rubrics/{rubric_id}", response_model=ApiEnvelope[dict[str, str]])
async def delete_rubric(
    request: Request,
    rubric_id: str,
) -> ApiEnvelope[dict[str, str]]:
    actor = await require_admin_actor(request)
    service = get_admin_service(request)
    service.delete_rubric(actor, rubric_id)
    return ok_response(request, {"status": "deleted"})


@router.post("/rubrics/{rubric_id}/criteria", response_model=ApiEnvelope[RubricView])
async def create_rubric_criterion(
    request: Request,
    rubric_id: str,
    command: CreateRubricCriterionCommand,
) -> ApiEnvelope[RubricView]:
    actor = await require_admin_actor(request)
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
    actor = await require_admin_actor(request)
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
    actor = await require_admin_actor(request)
    service = get_admin_service(request)
    return ok_response(request, service.delete_rubric_criterion(actor, rubric_id, criterion_ref))


@router.get("/pipelines", response_model=ApiEnvelope[list[PipelineDefinitionView]])
async def list_pipelines(
    request: Request,
) -> ApiEnvelope[list[PipelineDefinitionView]]:
    actor = await require_admin_actor(request)
    service = get_admin_service(request)
    return ok_response(request, service.list_pipelines(actor))


@router.get("/pipelines/{pipeline_name}", response_model=ApiEnvelope[PipelineDAGView])
async def get_pipeline_dag(
    request: Request,
    pipeline_name: str,
) -> ApiEnvelope[PipelineDAGView]:
    actor = await require_admin_actor(request)
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
    actor = await require_admin_actor(request)
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
    actor = await require_admin_actor(request)
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
    actor = await require_admin_actor(request)
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


@router.get("/telemetry/overview", response_model=ApiEnvelope[TelemetryOverviewView])
async def get_telemetry_overview(
    request: Request,
    organisation_id: str | None = Query(default=None),
    from_date: datetime | None = Query(default=None),
    to_date: datetime | None = Query(default=None),
) -> ApiEnvelope[TelemetryOverviewView]:
    actor = await require_admin_actor(request)
    service = get_admin_service(request)
    return ok_response(
        request,
        service.get_telemetry_overview(
            actor,
            organisation_id=organisation_id,
            from_date=from_date,
            to_date=to_date,
        ),
    )


@router.get("/telemetry/traces", response_model=ApiEnvelope[TelemetryTraceListView])
async def list_telemetry_traces(
    request: Request,
    organisation_id: str | None = Query(default=None),
    from_date: datetime | None = Query(default=None),
    to_date: datetime | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> ApiEnvelope[TelemetryTraceListView]:
    actor = await require_admin_actor(request)
    service = get_admin_service(request)
    return ok_response(
        request,
        service.list_telemetry_traces(
            actor,
            organisation_id=organisation_id,
            from_date=from_date,
            to_date=to_date,
            offset=offset,
            limit=limit,
        ),
    )


@router.get("/telemetry/traces/{trace_id}", response_model=ApiEnvelope[TelemetryTraceView | None])
async def get_telemetry_trace(
    request: Request,
    trace_id: str,
) -> ApiEnvelope[TelemetryTraceView | None]:
    actor = await require_admin_actor(request)
    service = get_admin_service(request)
    result = service.get_telemetry_trace(actor, trace_id)
    if result is None:
        from soft_skills_backend.shared.errors import domain_error

        raise domain_error(
            "Trace not found",
            code="SS-ADMIN-053",
            status_code=404,
            details={"trace_id": trace_id},
        )
    return ok_response(request, result)
