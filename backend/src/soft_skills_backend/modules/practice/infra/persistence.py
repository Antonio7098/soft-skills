"""Practice runtime persistence mutations."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from stageflow.core import StageContext

from soft_skills_backend.config import Settings
from soft_skills_backend.engines.config import load_marking_runtime_config
from soft_skills_backend.modules.practice.domain.practice import (
    AssessmentValidationStatus,
    AttemptStatus,
    PracticeRunStatus,
    SessionStatus,
    ensure_attempt_transition,
)
from soft_skills_backend.modules.practice.models import (
    AttemptGuardPayload,
    PracticeRunTransformPayload,
    PracticeSessionView,
    SessionTransformPayload,
    ValidatedAssessmentPayload,
)
from soft_skills_backend.platform.db.models import (
    AssessmentRecord,
    AssessmentSkillEvidenceRecord,
    AssessmentSkillResultRecord,
    AttemptRecord,
    PracticeRunRecord,
    PracticeSessionRecord,
)
from soft_skills_backend.platform.workflows.stageflow import (
    StageflowStageResult,
    metadata_value,
    pipeline_run_id_from_context,
    request_id_from_context,
)
from soft_skills_backend.shared.auth import Actor
from soft_skills_backend.shared.errors import (
    AppError,
    domain_error,
    get_typed_error_event_type,
    persistence_error,
)

from ..contracts.views import build_attempt_view, build_practice_run_view, utcnow, utcnow_iso
from .events import PracticeEventRecorder


def persist_session_start(
    *,
    session_factory: sessionmaker[Session],
    events: PracticeEventRecorder,
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


def persist_practice_run_start(
    *,
    session_factory: sessionmaker[Session],
    events: PracticeEventRecorder,
    ctx: StageContext,
    actor: Actor,
    transform_payload: PracticeRunTransformPayload,
) -> StageflowStageResult:
    try:
        with session_factory() as session:
            session.add(
                PracticeRunRecord(
                    id=transform_payload.run_id,
                    user_id=actor.user_id,
                    workflow_id=transform_payload.workflow_id,
                    status=PracticeRunStatus.ACTIVE.value,
                    total_items=len(transform_payload.items),
                    completed_items=0,
                    validated_items=0,
                    failed_items=0,
                )
            )
            for item in transform_payload.items:
                session.add(
                    PracticeSessionRecord(
                        id=item.session_id,
                        user_id=actor.user_id,
                        practice_type=item.prompt.practice_type.value,
                        content_item_id=item.prompt.content_item_id,
                        content_item_type=item.prompt.content_item_type,
                        practice_run_id=transform_payload.run_id,
                        sequence_index=item.position,
                        workflow_id=transform_payload.workflow_id,
                        status=SessionStatus.ACTIVE.value,
                        delivery_version=item.prompt.delivery_version,
                        rubric_id=item.prompt.rubric_id,
                        rubric_version=item.prompt.rubric_version,
                        prompt_payload=item.prompt.model_dump(mode="json"),
                        last_attempt_id=item.attempt_id,
                    )
                )
                session.add(
                    AttemptRecord(
                        id=item.attempt_id,
                        session_id=item.session_id,
                        user_id=actor.user_id,
                        workflow_id=transform_payload.workflow_id,
                        practice_type=item.prompt.practice_type.value,
                        content_item_id=item.prompt.content_item_id,
                        content_item_type=item.prompt.content_item_type,
                        status=AttemptStatus.PROMPT_DELIVERED.value,
                        response_mode=item.prompt.response_mode,
                        delivery_version=item.prompt.delivery_version,
                        rubric_id=item.prompt.rubric_id,
                        rubric_version=item.prompt.rubric_version,
                    )
                )
            session.commit()
            run = session.get(PracticeRunRecord, transform_payload.run_id)
            if run is None:
                raise domain_error(
                    "Practice run was not found after persistence",
                    code="SS-DOMAIN-018",
                    status_code=500,
                    details={"run_id": transform_payload.run_id},
                )
            view = build_practice_run_view(session, run)
    except SQLAlchemyError as exc:
        raise persistence_error(
            "Practice run could not be persisted",
            code="SS-PERSISTENCE-006",
            details={"run_id": transform_payload.run_id},
        ) from exc

    events.record(
        event_type="practice.run_started.v1",
        request_id=request_id_from_context(ctx),
        trace_id=metadata_value(ctx, "trace_id"),
        workflow_id=metadata_value(ctx, "workflow_id"),
        payload={
            "run_id": transform_payload.run_id,
            "user_id": actor.user_id,
            "total_items": len(transform_payload.items),
        },
    )
    for item in transform_payload.items:
        events.record(
            event_type="practice.session_started.v1",
            request_id=request_id_from_context(ctx),
            trace_id=metadata_value(ctx, "trace_id"),
            workflow_id=metadata_value(ctx, "workflow_id"),
            payload={
                "run_id": transform_payload.run_id,
                "session_id": item.session_id,
                "attempt_id": item.attempt_id,
                "user_id": actor.user_id,
                "practice_type": item.prompt.practice_type.value,
                "content_item_id": item.prompt.content_item_id,
                "content_item_type": item.prompt.content_item_type,
                "prompt_version": item.prompt.delivery_version,
                "rubric_version": item.prompt.rubric_version,
                "sequence_index": item.position,
            },
        )
        events.record(
            event_type="practice.prompt_delivered.v1",
            request_id=request_id_from_context(ctx),
            trace_id=metadata_value(ctx, "trace_id"),
            workflow_id=metadata_value(ctx, "workflow_id"),
            payload={
                "run_id": transform_payload.run_id,
                "session_id": item.session_id,
                "attempt_id": item.attempt_id,
                "practice_type": item.prompt.practice_type.value,
                "content_item_id": item.prompt.content_item_id,
                "content_item_type": item.prompt.content_item_type,
                "prompt_version": item.prompt.delivery_version,
                "sequence_index": item.position,
            },
        )
    return StageflowStageResult(
        payload=view,
        summary={"run_id": view.run_id, "total_items": view.total_items},
    )


def persist_attempt_submission(
    *,
    session_factory: sessionmaker[Session],
    events: PracticeEventRecorder,
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
    events: PracticeEventRecorder,
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
            for per_skill in assessment.per_skill_assessments:
                session.add(
                    AssessmentSkillResultRecord(
                        assessment_id=assessment_id,
                        skill_slug=per_skill.skill_slug,
                        score=per_skill.score,
                        rationale=per_skill.rationale,
                    )
                )
                for evidence_item in per_skill.evidence:
                    session.add(
                        AssessmentSkillEvidenceRecord(
                            assessment_id=assessment_id,
                            skill_slug=per_skill.skill_slug,
                            quote=evidence_item.quote,
                            explanation=evidence_item.explanation,
                        )
                    )
            attempt.status = AttemptStatus.ASSESSED.value
            attempt.assessment_id = assessment_id
            attempt.assessed_at = utcnow()
            attempt.last_error_code = None
            practice_session.status = SessionStatus.COMPLETED.value
            practice_session.completed_at = utcnow()
            if practice_session.practice_run_id is not None:
                _refresh_practice_run_progress(session, practice_session.practice_run_id)
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
    events: PracticeEventRecorder,
    attempt_id: str,
    request_id: str,
    trace_id: str,
    provider_name: str,
    model_slug: str,
    rejection_code: str,
    raw_payload: dict[str, Any],
) -> None:
    del settings
    config = load_marking_runtime_config()
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
                prompt_version=config.prompt_version,
                rubric_id=attempt.rubric_id,
                rubric_version=attempt.rubric_version,
                schema_version=config.output_schema_version,
                config_version=config.config_version,
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
        if practice_session.practice_run_id is not None:
            _refresh_practice_run_progress(session, practice_session.practice_run_id)
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
    events: PracticeEventRecorder,
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
        if practice_session.practice_run_id is not None:
            _refresh_practice_run_progress(session, practice_session.practice_run_id)
        session.commit()

    events.record(
        event_type=get_typed_error_event_type(error),
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


def _refresh_practice_run_progress(session: Session, run_id: str) -> None:
    run = session.get(PracticeRunRecord, run_id)
    if run is None:
        return
    session_records = (
        session.query(PracticeSessionRecord)
        .filter(PracticeSessionRecord.practice_run_id == run_id)
        .all()
    )
    attempt_statuses = [
        attempt.status
        for practice_session in session_records
        if (attempt := session.get(AttemptRecord, practice_session.last_attempt_id)) is not None
    ]
    completed_items = sum(
        status
        in {
            AttemptStatus.ASSESSED.value,
            AttemptStatus.ASSESSMENT_REJECTED.value,
            AttemptStatus.ASSESSMENT_FAILED.value,
        }
        for status in attempt_statuses
    )
    validated_items = sum(status == AttemptStatus.ASSESSED.value for status in attempt_statuses)
    failed_items = sum(
        status in {AttemptStatus.ASSESSMENT_REJECTED.value, AttemptStatus.ASSESSMENT_FAILED.value}
        for status in attempt_statuses
    )
    run.completed_items = completed_items
    run.validated_items = validated_items
    run.failed_items = failed_items
    if completed_items >= run.total_items:
        run.status = PracticeRunStatus.COMPLETED.value
        if run.completed_at is None:
            run.completed_at = utcnow()
    else:
        run.status = PracticeRunStatus.ACTIVE.value
        run.completed_at = None
