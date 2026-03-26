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
    LearnerAnalyticsView,
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
