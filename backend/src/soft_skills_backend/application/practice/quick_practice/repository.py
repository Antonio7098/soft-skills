"""Quick-practice persistence and query helpers."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.application.assessment.models import (
    LearnerContextPayload,
    QuickPracticePromptView,
    ResolvedAttemptPayload,
)
from soft_skills_backend.application.auth import Actor
from soft_skills_backend.application.practice.models import (
    AttemptGuardPayload,
    AttemptView,
    PromptContextPayload,
    QuickPracticeSessionView,
    SessionTransformPayload,
    StartInputPayload,
    ValidatedAssessmentPayload,
)
from soft_skills_backend.config import Settings
from soft_skills_backend.domain.errors import (
    AppError,
    auth_error,
    domain_error,
    persistence_error,
    validation_error,
)
from soft_skills_backend.domain.practice import (
    AssessmentValidationStatus,
    AttemptStatus,
    PracticeType,
    SessionStatus,
    ensure_attempt_transition,
)
from soft_skills_backend.orchestration.quick_practice import (
    PipelineExecutionContext,
    StageExecutionResult,
)
from soft_skills_backend.persistence.models import (
    AssessmentRecord,
    AttemptRecord,
    CollectionRecord,
    PracticeSessionRecord,
    PromptItemRecord,
    RubricRecord,
)
from soft_skills_backend.persistence.repositories import SqlAlchemyWorkflowEventRepository

from .events import QuickPracticeEventRecorder
from .views import build_attempt_view, can_use_collection, utcnow, utcnow_iso

DELIVERY_VERSION = "quick-practice.delivery.v1"


class QuickPracticeRepository:
    """Durable state and observability operations for quick practice."""

    def __init__(
        self,
        *,
        settings: Settings,
        session_factory: sessionmaker[Session],
        workflow_events: SqlAlchemyWorkflowEventRepository,
    ) -> None:
        self._settings = settings
        self._session_factory = session_factory
        self._events = QuickPracticeEventRecorder(workflow_events)

    def load_start_prompt_context(
        self,
        actor: Actor,
        start_input: StartInputPayload,
    ) -> StageExecutionResult:
        with self._session_factory() as session:
            prompt = session.get(PromptItemRecord, start_input.prompt_item_id)
            if prompt is None:
                raise domain_error(
                    "Prompt item was not found",
                    code="SS-DOMAIN-011",
                    status_code=404,
                    details={"prompt_item_id": start_input.prompt_item_id},
                )
            if prompt.prompt_type != "quick_practice_prompt":
                raise validation_error(
                    "Only quick-practice prompt items can start a quick-practice session",
                    code="SS-VALIDATION-021",
                    details={"prompt_type": prompt.prompt_type},
                )

            collection = session.get(CollectionRecord, prompt.collection_id)
            if collection is None:
                raise domain_error(
                    "Prompt item collection was not found",
                    code="SS-DOMAIN-012",
                    status_code=404,
                    details={"collection_id": prompt.collection_id},
                )
            if not can_use_collection(actor, collection):
                raise auth_error(
                    "Prompt item is not visible to this actor",
                    code="SS-AUTH-008",
                    status_code=403,
                    details={"prompt_item_id": prompt.id},
                )

            rubric = session.get(RubricRecord, prompt.rubric_id)
            if rubric is None:
                raise validation_error(
                    "Prompt item rubric was not found",
                    code="SS-VALIDATION-022",
                    details={"rubric_id": prompt.rubric_id},
                )
            if rubric.content_type != prompt.prompt_type:
                raise validation_error(
                    "Prompt item rubric mapping is invalid",
                    code="SS-VALIDATION-023",
                    details={"prompt_item_id": prompt.id, "rubric_id": rubric.rubric_id},
                )

            payload = PromptContextPayload(
                content_item_id=prompt.id,
                content_item_type=prompt.prompt_type,
                prompt_type=prompt.prompt_type,
                title=prompt.title,
                prompt_text=prompt.prompt_text,
                difficulty=prompt.difficulty,
                target_skill_slugs=list(prompt.target_skill_slugs),
                rubric_id=rubric.rubric_id,
                rubric_version=rubric.version,
            )
            return StageExecutionResult(
                payload=payload,
                summary={"content_item_id": prompt.id, "rubric_id": rubric.rubric_id},
            )

    def load_learner_context(self, user_id: str) -> StageExecutionResult:
        return _load_learner_context(self._session_factory, user_id)

    def persist_session_start(
        self,
        *,
        ctx: PipelineExecutionContext,
        actor: Actor,
        transform_payload: SessionTransformPayload,
    ) -> StageExecutionResult:
        try:
            with self._session_factory() as session:
                session.add(
                    PracticeSessionRecord(
                        id=transform_payload.session_id,
                        user_id=actor.user_id,
                        practice_type=PracticeType.QUICK_PRACTICE.value,
                        content_item_id=transform_payload.prompt.content_item_id,
                        content_item_type=transform_payload.prompt.prompt_type,
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
                        practice_type=PracticeType.QUICK_PRACTICE.value,
                        content_item_id=transform_payload.prompt.content_item_id,
                        content_item_type=transform_payload.prompt.prompt_type,
                        status=AttemptStatus.PROMPT_DELIVERED.value,
                        response_mode="text",
                        delivery_version=transform_payload.prompt.delivery_version,
                        rubric_id=transform_payload.prompt.rubric_id,
                        rubric_version=transform_payload.prompt.rubric_version,
                    )
                )
                session.commit()
        except SQLAlchemyError as exc:
            raise persistence_error(
                "Quick-practice session could not be persisted",
                code="SS-PERSISTENCE-002",
                details={"session_id": transform_payload.session_id},
            ) from exc

        self.record_event(
            event_type="practice.session_started.v1",
            request_id=ctx.request_id,
            trace_id=ctx.trace_id,
            workflow_id=ctx.workflow_id,
            payload={
                "session_id": transform_payload.session_id,
                "attempt_id": transform_payload.attempt_id,
                "user_id": actor.user_id,
                "prompt_item_id": transform_payload.prompt.content_item_id,
                "prompt_version": transform_payload.prompt.delivery_version,
                "rubric_version": transform_payload.prompt.rubric_version,
            },
        )
        self.record_event(
            event_type="practice.prompt_delivered.v1",
            request_id=ctx.request_id,
            trace_id=ctx.trace_id,
            workflow_id=ctx.workflow_id,
            payload={
                "session_id": transform_payload.session_id,
                "attempt_id": transform_payload.attempt_id,
                "prompt_item_id": transform_payload.prompt.content_item_id,
                "prompt_version": transform_payload.prompt.delivery_version,
            },
        )
        view = QuickPracticeSessionView(
            session_id=transform_payload.session_id,
            attempt_id=transform_payload.attempt_id,
            workflow_id=transform_payload.workflow_id,
            status=SessionStatus.ACTIVE,
            prompt=transform_payload.prompt,
            started_at=utcnow_iso(),
            trace_id=ctx.trace_id,
        )
        return StageExecutionResult(
            payload=view,
            summary={"session_id": view.session_id, "attempt_id": view.attempt_id},
        )

    def load_attempt_ownership(self, attempt_id: str) -> AttemptRecord:
        with self._session_factory() as session:
            attempt = session.get(AttemptRecord, attempt_id)
            if attempt is None:
                raise domain_error(
                    "Attempt was not found",
                    code="SS-DOMAIN-010",
                    status_code=404,
                    details={"attempt_id": attempt_id},
                )
            return attempt

    def load_submit_guard(
        self,
        *,
        actor: Actor,
        attempt_id: str,
        response_text: str,
    ) -> StageExecutionResult:
        with self._session_factory() as session:
            attempt = session.get(AttemptRecord, attempt_id)
            if attempt is None:
                raise domain_error(
                    "Attempt was not found",
                    code="SS-DOMAIN-010",
                    status_code=404,
                    details={"attempt_id": attempt_id},
                )
            if attempt.user_id != actor.user_id and not actor.is_admin:
                raise auth_error(
                    "Attempt is not visible to this actor",
                    code="SS-AUTH-007",
                    status_code=403,
                    details={"attempt_id": attempt_id},
                )
            ensure_attempt_transition(attempt.status, AttemptStatus.SUBMITTED)
            payload = AttemptGuardPayload(
                attempt_id=attempt.id,
                session_id=attempt.session_id,
                workflow_id=attempt.workflow_id,
                response_text=response_text,
            )
            return StageExecutionResult(
                payload=payload,
                summary={"attempt_id": attempt.id, "session_id": attempt.session_id},
            )

    def load_resolved_attempt(self, guard: AttemptGuardPayload) -> StageExecutionResult:
        return _load_resolved_attempt(self._session_factory, guard)

    def persist_attempt_submission(
        self,
        *,
        ctx: PipelineExecutionContext,
        guard: AttemptGuardPayload,
    ) -> StageExecutionResult:
        try:
            with self._session_factory() as session:
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
                attempt.trace_id = ctx.trace_id
                attempt.last_error_code = None
                session.commit()
        except SQLAlchemyError as exc:
            raise persistence_error(
                "Attempt submission could not be persisted",
                code="SS-PERSISTENCE-003",
                details={"attempt_id": guard.attempt_id},
            ) from exc

        self.record_event(
            event_type="practice.attempt_submitted.v1",
            request_id=ctx.request_id,
            trace_id=ctx.trace_id,
            workflow_id=ctx.workflow_id,
            payload={"attempt_id": guard.attempt_id, "session_id": guard.session_id},
        )
        return StageExecutionResult(
            payload=guard,
            summary={"attempt_id": guard.attempt_id, "status": AttemptStatus.SUBMITTED.value},
        )

    def mark_attempt_assessing(self, guard: AttemptGuardPayload) -> StageExecutionResult:
        try:
            with self._session_factory() as session:
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
        return StageExecutionResult(
            payload=guard,
            summary={"attempt_id": guard.attempt_id, "status": AttemptStatus.ASSESSING.value},
        )

    def persist_assessment(
        self,
        *,
        ctx: PipelineExecutionContext,
        guard: AttemptGuardPayload,
        assessment: ValidatedAssessmentPayload,
    ) -> StageExecutionResult:
        assessment_id = uuid4().hex
        try:
            with self._session_factory() as session:
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
                        practice_type=PracticeType.QUICK_PRACTICE.value,
                        validation_status=AssessmentValidationStatus.VALIDATED.value,
                        prompt_version=assessment.prompt_version,
                        rubric_id=assessment.rubric_id,
                        rubric_version=assessment.rubric_version,
                        schema_version=assessment.schema_version,
                        config_version=assessment.config_version,
                        provider=assessment.provider,
                        model_slug=assessment.model_slug,
                        overall_score=assessment.overall_score,
                        skill_scores=[
                            item.model_dump(mode="json") for item in assessment.skill_scores
                        ],
                        evidence=[item.model_dump(mode="json") for item in assessment.evidence],
                        rationale=assessment.rationale,
                        strengths=assessment.strengths,
                        weaknesses=assessment.weaknesses,
                        next_actions=assessment.next_actions,
                        raw_payload=assessment.raw_payload,
                        rejection_code=None,
                        trace_id=ctx.trace_id,
                        pipeline_run_id=ctx.pipeline_run_id,
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

        self.record_event(
            event_type="assessment.validated.v1",
            request_id=ctx.request_id,
            trace_id=ctx.trace_id,
            workflow_id=ctx.workflow_id,
            payload={
                "assessment_id": assessment_id,
                "attempt_id": guard.attempt_id,
                "session_id": guard.session_id,
                "overall_score": assessment.overall_score,
                "prompt_version": assessment.prompt_version,
                "rubric_version": assessment.rubric_version,
                "provider": assessment.provider,
                "model_slug": assessment.model_slug,
            },
        )
        return StageExecutionResult(
            payload=attempt_view,
            summary={"assessment_id": assessment_id, "status": AttemptStatus.ASSESSED.value},
        )

    def persist_rejected_assessment(
        self,
        *,
        attempt_id: str,
        request_id: str,
        trace_id: str,
        provider_name: str,
        model_slug: str,
        rejection_code: str,
        raw_payload: dict[str, Any],
    ) -> None:
        with self._session_factory() as session:
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
                    practice_type=PracticeType.QUICK_PRACTICE.value,
                    validation_status=AssessmentValidationStatus.REJECTED.value,
                    prompt_version=self._settings.assessment_prompt_version,
                    rubric_id=attempt.rubric_id,
                    rubric_version=attempt.rubric_version,
                    schema_version=self._settings.assessment_output_schema_version,
                    config_version=self._settings.scoring_config_version,
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

        self.record_event(
            event_type="assessment.rejected.v1",
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=attempt.workflow_id,
            payload={
                "attempt_id": attempt_id,
                "session_id": attempt.session_id,
                "error_code": rejection_code,
            },
            error_code=rejection_code,
        )

    def mark_attempt_failed(
        self,
        *,
        attempt_id: str,
        request_id: str,
        trace_id: str,
        error: AppError,
    ) -> None:
        with self._session_factory() as session:
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

        self.record_event(
            event_type="workflow.failed.v1",
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=attempt.workflow_id,
            payload={
                "attempt_id": attempt_id,
                "session_id": attempt.session_id,
                "error_code": error.code,
            },
            error_code=error.code,
        )

    def get_attempt(self, actor: Actor, attempt_id: str) -> AttemptView:
        with self._session_factory() as session:
            attempt = session.get(AttemptRecord, attempt_id)
            if attempt is None:
                raise domain_error(
                    "Attempt was not found",
                    code="SS-DOMAIN-010",
                    status_code=404,
                    details={"attempt_id": attempt_id},
                )
            if attempt.user_id != actor.user_id and not actor.is_admin:
                raise auth_error(
                    "Attempt is not visible to this actor",
                    code="SS-AUTH-007",
                    status_code=403,
                    details={"attempt_id": attempt_id},
                )
            return build_attempt_view(session, attempt)

    def record_event(
        self,
        *,
        event_type: str,
        request_id: str,
        trace_id: str,
        workflow_id: str,
        payload: dict[str, Any],
        error_code: str | None = None,
    ) -> None:
        self._events.record(
            event_type=event_type,
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id,
            payload=payload,
            error_code=error_code,
        )

    @property
    def settings(self) -> Settings:
        return self._settings


def _load_learner_context(
    session_factory: sessionmaker[Session],
    user_id: str,
) -> StageExecutionResult:
    """Load learner profile and prior quick-practice history."""

    from soft_skills_backend.persistence.models import AttemptRecord, LearnerProfileRecord

    with session_factory() as session:
        profile = session.get(LearnerProfileRecord, user_id)
        if profile is None:
            raise domain_error(
                "Learner profile is missing",
                code="SS-DOMAIN-004",
                status_code=500,
                details={"user_id": user_id},
            )
        prior_assessed_attempts = (
            session.query(AttemptRecord)
            .filter(
                AttemptRecord.user_id == user_id,
                AttemptRecord.status == AttemptStatus.ASSESSED.value,
            )
            .count()
        )
        return StageExecutionResult(
            payload=LearnerContextPayload(
                target_role=profile.target_role,
                goals=list(profile.goals),
                prior_assessed_attempts=prior_assessed_attempts,
            ),
            summary={"prior_assessed_attempts": prior_assessed_attempts},
        )


def _load_resolved_attempt(
    session_factory: sessionmaker[Session],
    guard: AttemptGuardPayload,
) -> StageExecutionResult:
    """Load the persisted prompt snapshot plus rubric metadata for assessment."""

    from soft_skills_backend.persistence.models import PracticeSessionRecord, RubricRecord

    with session_factory() as session:
        practice_session = session.get(PracticeSessionRecord, guard.session_id)
        if practice_session is None:
            raise domain_error(
                "Practice session was not found",
                code="SS-DOMAIN-013",
                status_code=404,
                details={"session_id": guard.session_id},
            )
        rubric = session.get(RubricRecord, practice_session.rubric_id)
        if rubric is None:
            raise validation_error(
                "Practice session rubric was not found",
                code="SS-VALIDATION-024",
                details={"rubric_id": practice_session.rubric_id},
            )
        prompt = QuickPracticePromptView.model_validate(practice_session.prompt_payload)
        if not prompt.rubric_version:
            raise validation_error(
                "Practice session prompt payload is missing rubric version metadata",
                code="SS-VALIDATION-025",
                details={"session_id": guard.session_id},
            )
        return StageExecutionResult(
            payload=ResolvedAttemptPayload(
                attempt_id=guard.attempt_id,
                session_id=guard.session_id,
                workflow_id=guard.workflow_id,
                response_text=guard.response_text,
                prompt=prompt.model_copy(update={"rubric_version": rubric.version}),
            ),
            summary={"attempt_id": guard.attempt_id, "rubric_id": rubric.rubric_id},
        )
