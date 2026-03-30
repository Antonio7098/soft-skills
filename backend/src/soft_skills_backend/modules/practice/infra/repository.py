"""Practice runtime repository facade."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session, sessionmaker
from stageflow.core import StageContext

from soft_skills_backend.config import Settings
from soft_skills_backend.modules.practice.domain.practice import (
    PRACTICE_DELIVERY_VERSIONS,
    PracticeType,
)
from soft_skills_backend.modules.practice.models import (
    AttemptHistoryItemView,
    AttemptGuardPayload,
    AttemptView,
    PracticeRunListItemView,
    PracticeRunTransformPayload,
    PracticeRunView,
    SessionTransformPayload,
    StartInputPayload,
    ValidatedAssessmentPayload,
)
from soft_skills_backend.platform.db.models import AttemptRecord, PracticeRunRecord
from soft_skills_backend.platform.db.repositories import SqlAlchemyWorkflowEventRepository
from soft_skills_backend.platform.observability.events import WorkflowEventRecorder
from soft_skills_backend.platform.workflows.stageflow import StageflowStageResult
from soft_skills_backend.shared.auth import Actor
from soft_skills_backend.shared.errors import AppError, auth_error, domain_error

from ..contracts.views import (
    build_attempt_history_item,
    build_attempt_view,
    build_practice_run_list_item,
    build_practice_run_view,
)
from .persistence import (
    mark_attempt_assessing,
    mark_attempt_failed,
    persist_assessment,
    persist_attempt_submission,
    persist_practice_run_start,
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

DELIVERY_VERSION = PRACTICE_DELIVERY_VERSIONS[PracticeType.QUICK_PRACTICE]


class PracticeRepository:
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
        self._events = WorkflowEventRecorder(
            workflow_events, logger_name="soft_skills_backend.practice"
        )

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

    def persist_practice_run_start(
        self,
        *,
        ctx: StageContext,
        actor: Actor,
        transform_payload: PracticeRunTransformPayload,
    ) -> StageflowStageResult:
        return persist_practice_run_start(
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
            if attempt.user_id != actor.user_id:
                raise auth_error(
                    "Attempt content is only visible to the owning learner",
                    code="SS-AUTH-011",
                    status_code=403,
                    details={"attempt_id": attempt_id},
                )
            return build_attempt_view(session, attempt)

    def list_attempt_history(self, actor: Actor) -> list[AttemptHistoryItemView]:
        with self._session_factory() as session:
            attempts = (
                session.query(AttemptRecord)
                .filter(AttemptRecord.user_id == actor.user_id)
                .order_by(AttemptRecord.created_at.desc())
                .all()
            )
            return [build_attempt_history_item(session, attempt) for attempt in attempts]

    def get_practice_run(self, actor: Actor, run_id: str) -> PracticeRunView:
        with self._session_factory() as session:
            run = session.get(PracticeRunRecord, run_id)
            if run is None:
                raise domain_error(
                    "Practice run was not found",
                    code="SS-DOMAIN-019",
                    status_code=404,
                    details={"run_id": run_id},
                )
            if run.user_id != actor.user_id:
                raise auth_error(
                    "Practice run content is only visible to the owning learner",
                    code="SS-AUTH-013",
                    status_code=403,
                    details={"run_id": run_id},
                )
            return build_practice_run_view(session, run)

    def list_practice_runs(self, actor: Actor) -> list[PracticeRunListItemView]:
        with self._session_factory() as session:
            runs = (
                session.query(PracticeRunRecord)
                .filter(PracticeRunRecord.user_id == actor.user_id)
                .order_by(PracticeRunRecord.created_at.desc())
                .all()
            )
            return [build_practice_run_list_item(session, run) for run in runs]

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
