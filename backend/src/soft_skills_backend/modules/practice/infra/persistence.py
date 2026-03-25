"""Practice runtime persistence mutations."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from stageflow.core import StageContext

from soft_skills_backend.config import Settings
from soft_skills_backend.modules.practice.domain.practice import (
    AssessmentValidationStatus,
    AttemptStatus,
    SessionStatus,
    ensure_attempt_transition,
)
from soft_skills_backend.modules.practice.models import (
    AttemptGuardPayload,
    PracticeSessionView,
    SessionTransformPayload,
    ValidatedAssessmentPayload,
)
from soft_skills_backend.platform.db.models import (
    AssessmentRecord,
    AttemptRecord,
    PracticeSessionRecord,
)
from soft_skills_backend.platform.workflows.stageflow import (
    StageflowStageResult,
    metadata_value,
    pipeline_run_id_from_context,
    request_id_from_context,
)
from soft_skills_backend.shared.auth import Actor
from soft_skills_backend.shared.errors import AppError, domain_error, persistence_error

from ..contracts.views import build_attempt_view, utcnow, utcnow_iso
from .events import QuickPracticeEventRecorder


def persist_session_start(
    *,
    session_factory: sessionmaker[Session],
    events: QuickPracticeEventRecorder,
    ctx: StageContext,
    actor: Actor,
    transform_payload: SessionTransformPayload,
) -> StageflowStageResult:
    try:
        with session_factory() as session:
            session.add(
                PracticeSessionRecord(
                    id=transform_payload.session_id,
                    user_id=actor.user_id,
                    practice_type=transform_payload.prompt.practice_type.value,
                    content_item_id=transform_payload.prompt.content_item_id,
                    content_item_type=transform_payload.prompt.content_item_type,
                    workflow_id=transform_payload.workflow_id,
                    status=SessionStatus.ACTIVE.value,
                    delivery_version=transform_payload.prompt.delivery_version,
                    rubric_id=transform_payload.prompt.rubric_id,
                    rubric_version=transform_payload.prompt.rubric_version,
                    prompt_payload=transform_payload.prompt.model_dump(mode="json"),
                    last_attempt_id=transform_payload.attempt_id,
                )
            )
            session.add(
                AttemptRecord(
                    id=transform_payload.attempt_id,
                    session_id=transform_payload.session_id,
                    user_id=actor.user_id,
                    workflow_id=transform_payload.workflow_id,
                    practice_type=transform_payload.prompt.practice_type.value,
                    content_item_id=transform_payload.prompt.content_item_id,
                    content_item_type=transform_payload.prompt.content_item_type,
                    status=AttemptStatus.PROMPT_DELIVERED.value,
                    response_mode=transform_payload.prompt.response_mode,
                    delivery_version=transform_payload.prompt.delivery_version,
                    rubric_id=transform_payload.prompt.rubric_id,
                    rubric_version=transform_payload.prompt.rubric_version,
                )
            )
            session.commit()
    except SQLAlchemyError as exc:
        raise persistence_error(
            "Practice session could not be persisted",
            code="SS-PERSISTENCE-002",
            details={"session_id": transform_payload.session_id},
        ) from exc

    events.record(
        event_type="practice.session_started.v1",
        request_id=request_id_from_context(ctx),
        trace_id=metadata_value(ctx, "trace_id"),
        workflow_id=metadata_value(ctx, "workflow_id"),
        payload={
            "session_id": transform_payload.session_id,
            "attempt_id": transform_payload.attempt_id,
            "user_id": actor.user_id,
            "practice_type": transform_payload.prompt.practice_type.value,
            "content_item_id": transform_payload.prompt.content_item_id,
            "content_item_type": transform_payload.prompt.content_item_type,
            "prompt_version": transform_payload.prompt.delivery_version,
            "rubric_version": transform_payload.prompt.rubric_version,
        },
    )
    events.record(
        event_type="practice.prompt_delivered.v1",
        request_id=request_id_from_context(ctx),
        trace_id=metadata_value(ctx, "trace_id"),
        workflow_id=metadata_value(ctx, "workflow_id"),
        payload={
            "session_id": transform_payload.session_id,
            "attempt_id": transform_payload.attempt_id,
            "practice_type": transform_payload.prompt.practice_type.value,
            "content_item_id": transform_payload.prompt.content_item_id,
            "content_item_type": transform_payload.prompt.content_item_type,
            "prompt_version": transform_payload.prompt.delivery_version,
        },
    )
    view = PracticeSessionView(
        session_id=transform_payload.session_id,
        attempt_id=transform_payload.attempt_id,
        workflow_id=transform_payload.workflow_id,
        status=SessionStatus.ACTIVE,
        prompt=transform_payload.prompt,
        started_at=utcnow_iso(),
        trace_id=metadata_value(ctx, "trace_id"),
    )
    return StageflowStageResult(
        payload=view,
        summary={"session_id": view.session_id, "attempt_id": view.attempt_id},
    )


def persist_attempt_submission(
    *,
    session_factory: sessionmaker[Session],
    events: QuickPracticeEventRecorder,
    ctx: StageContext,
    guard: AttemptGuardPayload,
) -> StageflowStageResult:
    try:
        with session_factory() as session:
            attempt = session.get(AttemptRecord, guard.attempt_id)
            if attempt is None:
                raise domain_error(
                    "Attempt was not found",
                    code="SS-DOMAIN-010",
                    status_code=404,
                    details={"attempt_id": guard.attempt_id},
                )
            ensure_attempt_transition(attempt.status, AttemptStatus.SUBMITTED)
            attempt.status = AttemptStatus.SUBMITTED.value
            attempt.response_text = guard.response_text
            attempt.submitted_at = utcnow()
            attempt.trace_id = metadata_value(ctx, "trace_id")
            attempt.last_error_code = None
            session.commit()
    except SQLAlchemyError as exc:
        raise persistence_error(
            "Attempt submission could not be persisted",
            code="SS-PERSISTENCE-003",
            details={"attempt_id": guard.attempt_id},
        ) from exc

    events.record(
        event_type="practice.attempt_submitted.v1",
        request_id=request_id_from_context(ctx),
        trace_id=metadata_value(ctx, "trace_id"),
        workflow_id=metadata_value(ctx, "workflow_id"),
        payload={"attempt_id": guard.attempt_id, "session_id": guard.session_id},
    )
    return StageflowStageResult(
        payload=guard,
        summary={"attempt_id": guard.attempt_id, "status": AttemptStatus.SUBMITTED.value},
    )


def mark_attempt_assessing(
    *,
    session_factory: sessionmaker[Session],
    guard: AttemptGuardPayload,
) -> StageflowStageResult:
    try:
        with session_factory() as session:
            attempt = session.get(AttemptRecord, guard.attempt_id)
            if attempt is None:
                raise domain_error(
                    "Attempt was not found",
                    code="SS-DOMAIN-010",
                    status_code=404,
                    details={"attempt_id": guard.attempt_id},
                )
            ensure_attempt_transition(attempt.status, AttemptStatus.ASSESSING)
            attempt.status = AttemptStatus.ASSESSING.value
            session.commit()
    except SQLAlchemyError as exc:
        raise persistence_error(
            "Attempt assessing state could not be persisted",
            code="SS-PERSISTENCE-004",
            details={"attempt_id": guard.attempt_id},
        ) from exc
    return StageflowStageResult(
        payload=guard,
        summary={"attempt_id": guard.attempt_id, "status": AttemptStatus.ASSESSING.value},
    )


def persist_assessment(
    *,
    session_factory: sessionmaker[Session],
    events: QuickPracticeEventRecorder,
    ctx: StageContext,
    guard: AttemptGuardPayload,
    assessment: ValidatedAssessmentPayload,
) -> StageflowStageResult:
    assessment_id = uuid4().hex
    try:
        with session_factory() as session:
            attempt = session.get(AttemptRecord, guard.attempt_id)
            practice_session = session.get(PracticeSessionRecord, guard.session_id)
            if attempt is None or practice_session is None:
                raise domain_error(
                    "Attempt or practice session was not found",
                    code="SS-DOMAIN-014",
                    status_code=404,
                    details={"attempt_id": guard.attempt_id, "session_id": guard.session_id},
                )
            ensure_attempt_transition(attempt.status, AttemptStatus.ASSESSED)
            session.add(
                AssessmentRecord(
                    id=assessment_id,
                    attempt_id=guard.attempt_id,
                    session_id=guard.session_id,
                    user_id=attempt.user_id,
                    workflow_id=guard.workflow_id,
                    practice_type=attempt.practice_type,
                    validation_status=AssessmentValidationStatus.VALIDATED.value,
                    prompt_version=assessment.prompt_version,
                    rubric_id=assessment.rubric_id,
                    rubric_version=assessment.rubric_version,
                    schema_version=assessment.schema_version,
                    config_version=assessment.config_version,
                    provider=assessment.provider,
                    model_slug=assessment.model_slug,
                    overall_score=assessment.overall_score,
                    skill_scores=[item.model_dump(mode="json") for item in assessment.skill_scores],
                    evidence=[item.model_dump(mode="json") for item in assessment.evidence],
                    rationale=assessment.rationale,
                    strengths=assessment.strengths,
                    weaknesses=assessment.weaknesses,
                    next_actions=assessment.next_actions,
                    raw_payload=assessment.raw_payload,
                    rejection_code=None,
                    trace_id=metadata_value(ctx, "trace_id"),
                    pipeline_run_id=pipeline_run_id_from_context(ctx),
                )
            )
            attempt.status = AttemptStatus.ASSESSED.value
            attempt.assessment_id = assessment_id
            attempt.assessed_at = utcnow()
            attempt.last_error_code = None
            practice_session.status = SessionStatus.COMPLETED.value
            practice_session.completed_at = utcnow()
            session.commit()
            attempt_view = build_attempt_view(session, attempt)
    except SQLAlchemyError as exc:
        raise persistence_error(
            "Assessment artifact could not be persisted",
            code="SS-PERSISTENCE-005",
            details={"attempt_id": guard.attempt_id},
        ) from exc

    events.record(
        event_type="assessment.validated.v1",
        request_id=request_id_from_context(ctx),
        trace_id=metadata_value(ctx, "trace_id"),
        workflow_id=metadata_value(ctx, "workflow_id"),
        payload={
            "assessment_id": assessment_id,
            "attempt_id": guard.attempt_id,
            "session_id": guard.session_id,
            "practice_type": attempt_view.prompt.practice_type.value,
            "overall_score": assessment.overall_score,
            "prompt_version": assessment.prompt_version,
            "rubric_version": assessment.rubric_version,
            "provider": assessment.provider,
            "model_slug": assessment.model_slug,
        },
    )
    return StageflowStageResult(
        payload=attempt_view,
        summary={"assessment_id": assessment_id, "status": AttemptStatus.ASSESSED.value},
    )


def persist_rejected_assessment(
    *,
    session_factory: sessionmaker[Session],
    settings: Settings,
    events: QuickPracticeEventRecorder,
    attempt_id: str,
    request_id: str,
    trace_id: str,
    provider_name: str,
    model_slug: str,
    rejection_code: str,
    raw_payload: dict[str, Any],
) -> None:
    with session_factory() as session:
        attempt = session.get(AttemptRecord, attempt_id)
        if attempt is None:
            return
        practice_session = session.get(PracticeSessionRecord, attempt.session_id)
        if practice_session is None:
            return
        assessment_id = uuid4().hex
        session.add(
            AssessmentRecord(
                id=assessment_id,
                attempt_id=attempt.id,
                session_id=attempt.session_id,
                user_id=attempt.user_id,
                workflow_id=attempt.workflow_id,
                practice_type=attempt.practice_type,
                validation_status=AssessmentValidationStatus.REJECTED.value,
                prompt_version=settings.assessment_prompt_version,
                rubric_id=attempt.rubric_id,
                rubric_version=attempt.rubric_version,
                schema_version=settings.assessment_output_schema_version,
                config_version=settings.scoring_config_version,
                provider=provider_name,
                model_slug=model_slug,
                overall_score=None,
                skill_scores=[],
                evidence=[],
                rationale=None,
                strengths=[],
                weaknesses=[],
                next_actions=[],
                raw_payload=raw_payload,
                rejection_code=rejection_code,
                trace_id=trace_id,
                pipeline_run_id=uuid4().hex,
            )
        )
        attempt.status = AttemptStatus.ASSESSMENT_REJECTED.value
        attempt.assessment_id = assessment_id
        attempt.assessed_at = utcnow()
        attempt.last_error_code = rejection_code
        practice_session.status = SessionStatus.FAILED.value
        practice_session.completed_at = utcnow()
        session.commit()

    events.record(
        event_type="assessment.rejected.v1",
        request_id=request_id,
        trace_id=trace_id,
        workflow_id=attempt.workflow_id,
        payload={
            "attempt_id": attempt_id,
            "session_id": attempt.session_id,
            "practice_type": attempt.practice_type,
            "error_code": rejection_code,
        },
        error_code=rejection_code,
    )


def mark_attempt_failed(
    *,
    session_factory: sessionmaker[Session],
    events: QuickPracticeEventRecorder,
    attempt_id: str,
    request_id: str,
    trace_id: str,
    error: AppError,
) -> None:
    with session_factory() as session:
        attempt = session.get(AttemptRecord, attempt_id)
        if attempt is None:
            return
        practice_session = session.get(PracticeSessionRecord, attempt.session_id)
        if practice_session is None:
            return
        attempt.status = AttemptStatus.ASSESSMENT_FAILED.value
        attempt.last_error_code = error.code
        attempt.assessed_at = utcnow()
        attempt.trace_id = trace_id
        practice_session.status = SessionStatus.FAILED.value
        practice_session.completed_at = utcnow()
        session.commit()

    events.record(
        event_type="workflow.failed.v1",
        request_id=request_id,
        trace_id=trace_id,
        workflow_id=attempt.workflow_id,
        payload={
            "attempt_id": attempt_id,
            "session_id": attempt.session_id,
            "practice_type": attempt.practice_type,
            "error_code": error.code,
        },
        error_code=error.code,
    )
