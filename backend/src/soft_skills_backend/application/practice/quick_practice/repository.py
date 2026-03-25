"""Practice runtime repository facade."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session, sessionmaker
from stageflow.core import StageContext

from soft_skills_backend.application._shared.stageflow import StageflowStageResult
from soft_skills_backend.application.auth import Actor
from soft_skills_backend.application.practice.models import (
    AttemptGuardPayload,
    AttemptView,
    SessionTransformPayload,
    StartInputPayload,
    ValidatedAssessmentPayload,
)
from soft_skills_backend.config import Settings
from soft_skills_backend.domain.errors import AppError, auth_error, domain_error
from soft_skills_backend.domain.practice import PRACTICE_DELIVERY_VERSIONS, PracticeType
from soft_skills_backend.persistence.models import AttemptRecord
from soft_skills_backend.persistence.repositories import SqlAlchemyWorkflowEventRepository

from .events import QuickPracticeEventRecorder
from .persistence import (
    mark_attempt_assessing,
    mark_attempt_failed,
    persist_assessment,
    persist_attempt_submission,
    persist_rejected_assessment,
    persist_session_start,
)
from .queries import (
    load_attempt_ownership,
    load_learner_context,
    load_resolved_attempt,
    load_start_prompt_context,
    load_submit_guard,
)
from .views import build_attempt_view

DELIVERY_VERSION = PRACTICE_DELIVERY_VERSIONS[PracticeType.QUICK_PRACTICE]


class QuickPracticeRepository:
    """Coordinate focused practice persistence helpers."""

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
    ) -> StageflowStageResult:
        return load_start_prompt_context(self._session_factory, actor, start_input)

    def load_learner_context(self, user_id: str) -> StageflowStageResult:
        return load_learner_context(self._session_factory, user_id)

    def persist_session_start(
        self,
        *,
        ctx: StageContext,
        actor: Actor,
        transform_payload: SessionTransformPayload,
    ) -> StageflowStageResult:
        return persist_session_start(
            session_factory=self._session_factory,
            events=self._events,
            ctx=ctx,
            actor=actor,
            transform_payload=transform_payload,
        )

    def load_attempt_ownership(self, attempt_id: str) -> AttemptRecord:
        return load_attempt_ownership(self._session_factory, attempt_id)

    def load_submit_guard(
        self,
        *,
        actor: Actor,
        attempt_id: str,
        response_text: str,
    ) -> StageflowStageResult:
        return load_submit_guard(
            self._session_factory,
            actor=actor,
            attempt_id=attempt_id,
            response_text=response_text,
        )

    def load_resolved_attempt(self, guard: AttemptGuardPayload) -> StageflowStageResult:
        return load_resolved_attempt(self._session_factory, guard)

    def persist_attempt_submission(
        self,
        *,
        ctx: StageContext,
        guard: AttemptGuardPayload,
    ) -> StageflowStageResult:
        return persist_attempt_submission(
            session_factory=self._session_factory,
            events=self._events,
            ctx=ctx,
            guard=guard,
        )

    def mark_attempt_assessing(self, guard: AttemptGuardPayload) -> StageflowStageResult:
        return mark_attempt_assessing(
            session_factory=self._session_factory,
            guard=guard,
        )

    def persist_assessment(
        self,
        *,
        ctx: StageContext,
        guard: AttemptGuardPayload,
        assessment: ValidatedAssessmentPayload,
    ) -> StageflowStageResult:
        return persist_assessment(
            session_factory=self._session_factory,
            events=self._events,
            ctx=ctx,
            guard=guard,
            assessment=assessment,
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
        persist_rejected_assessment(
            session_factory=self._session_factory,
            settings=self._settings,
            events=self._events,
            attempt_id=attempt_id,
            request_id=request_id,
            trace_id=trace_id,
            provider_name=provider_name,
            model_slug=model_slug,
            rejection_code=rejection_code,
            raw_payload=raw_payload,
        )

    def mark_attempt_failed(
        self,
        *,
        attempt_id: str,
        request_id: str,
        trace_id: str,
        error: AppError,
    ) -> None:
        mark_attempt_failed(
            session_factory=self._session_factory,
            events=self._events,
            attempt_id=attempt_id,
            request_id=request_id,
            trace_id=trace_id,
            error=error,
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
