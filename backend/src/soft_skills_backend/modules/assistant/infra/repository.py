"""Assistant persistence and read-model access."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.modules.assistant.contracts.stream import AssistantStreamEvent
from soft_skills_backend.modules.assistant.contracts.views import (
    AssistantApprovalView,
    AssistantMessageView,
    AssistantSessionView,
    AssistantToolCallView,
    AssistantTurnView,
)
from soft_skills_backend.modules.assistant.domain.models import (
    AssistantApprovalStatus,
    AssistantMessageRole,
    AssistantSessionStatus,
    AssistantToolCallStatus,
    AssistantTurnStatus,
    is_turn_terminal,
)
from soft_skills_backend.modules.identity.models import LearnerProfileView
from soft_skills_backend.platform.db.models import (
    AssistantMessageRecord,
    AssistantApprovalRequestRecord,
    AssistantSessionRecord,
    AssistantStreamEventRecord,
    AssistantToolCallRecord,
    AssistantTurnRecord,
    LearnerProfileRecord,
    UserAccountRecord,
)
from soft_skills_backend.platform.db.repositories import SqlAlchemyWorkflowEventRepository
from soft_skills_backend.platform.observability.events import WorkflowEvent
from soft_skills_backend.shared.auth import Actor
from soft_skills_backend.shared.errors import auth_error, domain_error


class AssistantRepository:
    """Coordinate assistant durability and focused read queries."""

    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        workflow_events: SqlAlchemyWorkflowEventRepository,
    ) -> None:
        self._session_factory = session_factory
        self._workflow_events = workflow_events

    def create_session(
        self,
        *,
        actor: Actor,
        title: str | None,
        request_id: str,
        trace_id: str,
    ) -> AssistantSessionView:
        now = datetime.now(UTC)
        record = AssistantSessionRecord(
            id=uuid4().hex,
            user_id=actor.user_id,
            title=title,
            status=AssistantSessionStatus.ACTIVE.value,
            metadata_payload={},
            created_at=now,
            updated_at=now,
        )
        with self._session_factory() as session:
            session.add(record)
            session.commit()
            session.refresh(record)
        self._record_event(
            event_type="assistant.session.created.v1",
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=record.id,
            payload={"session_id": record.id, "user_id": actor.user_id},
            organisation_id=actor.organisation_id,
        )
        return self.get_session(actor, record.id)

    def get_session(self, actor: Actor, session_id: str) -> AssistantSessionView:
        with self._session_factory() as session:
            record = self._load_owned_session(session, actor, session_id)
            return self._build_session_view(session, record)

    def list_sessions(self, actor: Actor) -> list[AssistantSessionView]:
        with self._session_factory() as session:
            records = (
                session.query(AssistantSessionRecord)
                .filter(AssistantSessionRecord.user_id == actor.user_id)
                .order_by(
                    AssistantSessionRecord.updated_at.desc(),
                    AssistantSessionRecord.created_at.desc(),
                )
                .all()
            )
            return [self._build_session_view(session, record) for record in records]

    def create_turn(
        self,
        *,
        actor: Actor,
        session_id: str,
        request_id: str,
        trace_id: str,
        workflow_id: str,
        message_text: str,
    ) -> AssistantTurnView:
        now = datetime.now(UTC)
        stream_token = uuid4().hex + uuid4().hex
        turn_id = uuid4().hex
        user_message_id = uuid4().hex
        with self._session_factory() as session:
            session_record = self._load_owned_session(session, actor, session_id)
            turn_record = AssistantTurnRecord(
                id=turn_id,
                session_id=session_id,
                user_id=actor.user_id,
                request_id=request_id,
                trace_id=trace_id,
                workflow_id=workflow_id,
                pipeline_run_id=None,
                status=AssistantTurnStatus.PENDING.value,
                stream_token=stream_token,
                user_message_id=user_message_id,
                assistant_message_id=None,
                last_error_code=None,
                cancel_reason=None,
                tool_call_count=0,
                metadata_payload={},
                created_at=now,
                started_at=None,
                completed_at=None,
                cancelled_at=None,
            )
            message_record = AssistantMessageRecord(
                id=user_message_id,
                session_id=session_id,
                turn_id=turn_id,
                user_id=actor.user_id,
                role=AssistantMessageRole.USER.value,
                content=message_text,
                metadata_payload={},
                created_at=now,
            )
            session_record.updated_at = now
            if not session_record.title:
                session_record.title = message_text[:80]
            session.add(turn_record)
            session.add(message_record)
            session.commit()
        self._record_event(
            event_type="assistant.turn.created.v1",
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id,
            payload={"session_id": session_id, "turn_id": turn_id, "user_id": actor.user_id},
            organisation_id=actor.organisation_id,
        )
        return self.get_turn(actor, turn_id)

    def get_turn(self, actor: Actor, turn_id: str) -> AssistantTurnView:
        with self._session_factory() as session:
            record = self._load_owned_turn(session, actor, turn_id)
            return self._build_turn_view(session, record)

    def get_turn_by_stream_token(self, stream_token: str) -> AssistantTurnView:
        with self._session_factory() as session:
            record = (
                session.query(AssistantTurnRecord)
                .filter(AssistantTurnRecord.stream_token == stream_token)
                .one_or_none()
            )
            if record is None:
                raise domain_error(
                    "Assistant stream token was not found",
                    code="SS-DOMAIN-201",
                    status_code=404,
                    details={"stream_token": stream_token},
                )
            return self._build_turn_view(session, record)

    def list_stream_events(
        self,
        *,
        stream_token: str,
        after_sequence: int | None = None,
    ) -> list[AssistantStreamEvent]:
        with self._session_factory() as session:
            turn = (
                session.query(AssistantTurnRecord)
                .filter(AssistantTurnRecord.stream_token == stream_token)
                .one_or_none()
            )
            if turn is None:
                raise domain_error(
                    "Assistant stream token was not found",
                    code="SS-DOMAIN-201",
                    status_code=404,
                    details={"stream_token": stream_token},
                )
            query = (
                session.query(AssistantStreamEventRecord)
                .filter(AssistantStreamEventRecord.turn_id == turn.id)
                .order_by(AssistantStreamEventRecord.sequence_number.asc())
            )
            if after_sequence is not None:
                query = query.filter(AssistantStreamEventRecord.sequence_number > after_sequence)
            records = query.all()
            return [
                AssistantStreamEvent(
                    event_id=record.event_id,
                    session_id=record.session_id,
                    turn_id=record.turn_id,
                    trace_id=turn.trace_id,
                    workflow_id=turn.workflow_id,
                    type=record.event_type,
                    sequence_number=record.sequence_number,
                    emitted_at=record.emitted_at,
                    payload=dict(record.payload),
                )
                for record in records
            ]

    def load_history(
        self, *, actor: Actor, session_id: str, limit: int = 20
    ) -> list[AssistantMessageView]:
        with self._session_factory() as session:
            self._load_owned_session(session, actor, session_id)
            records = (
                session.query(AssistantMessageRecord)
                .filter(AssistantMessageRecord.session_id == session_id)
                .order_by(AssistantMessageRecord.created_at.desc())
                .limit(limit)
                .all()
            )
            return [self._build_message_view(record) for record in reversed(records)]

    def load_session_metadata(self, *, actor: Actor, session_id: str) -> dict[str, Any]:
        with self._session_factory() as session:
            record = self._load_owned_session(session, actor, session_id)
            return dict(record.metadata_payload)

    def update_session_metadata(
        self,
        *,
        actor: Actor,
        session_id: str,
        metadata_payload: dict[str, Any],
    ) -> None:
        with self._session_factory() as session:
            record = self._load_owned_session(session, actor, session_id)
            record.metadata_payload = dict(metadata_payload)
            record.updated_at = datetime.now(UTC)
            session.commit()

    def list_messages(self, *, actor: Actor, session_id: str) -> list[AssistantMessageView]:
        with self._session_factory() as session:
            self._load_owned_session(session, actor, session_id)
            records = (
                session.query(AssistantMessageRecord)
                .filter(AssistantMessageRecord.session_id == session_id)
                .order_by(AssistantMessageRecord.created_at.asc())
                .all()
            )
            return [self._build_message_view(record) for record in records]

    def load_profile(self, user_id: str) -> dict[str, Any]:
        with self._session_factory() as session:
            user = session.get(UserAccountRecord, user_id)
            profile = session.get(LearnerProfileRecord, user_id)
            if user is None or profile is None:
                raise domain_error(
                    "Learner profile was not found",
                    code="SS-DOMAIN-202",
                    status_code=404,
                    details={"user_id": user_id},
                )
            return {
                "user": {
                    "id": user.id,
                    "display_name": user.display_name,
                    "email": user.email,
                    # User accounts no longer carry a first-class role; mirror the
                    # learner profile target role for prompt compatibility.
                    "role": profile.target_role,
                },
                "profile": LearnerProfileView(
                    target_role=profile.target_role,
                    goals=list(profile.goals),
                    practice_preferences=dict(profile.practice_preferences),
                ).model_dump(mode="json"),
            }

    def mark_turn_running(self, *, turn_id: str, pipeline_run_id: str) -> AssistantTurnView:
        now = datetime.now(UTC)
        with self._session_factory() as session:
            record = self._load_turn(session, turn_id)
            record.status = AssistantTurnStatus.RUNNING.value
            record.pipeline_run_id = pipeline_run_id
            record.started_at = now
            session_record = session.get(AssistantSessionRecord, record.session_id)
            if session_record is not None:
                session_record.updated_at = now
            session.commit()
            return self._build_turn_view(session, record)

    def request_cancel(
        self, *, actor: Actor | None, turn_id: str, reason: str
    ) -> AssistantTurnView:
        now = datetime.now(UTC)
        with self._session_factory() as session:
            record = self._load_turn(session, turn_id)
            if actor is not None and record.user_id != actor.user_id:
                raise auth_error(
                    "Assistant turn is not visible to this actor",
                    code="SS-AUTH-201",
                    status_code=403,
                    details={"turn_id": turn_id},
                )
            if is_turn_terminal(record.status):
                return self._build_turn_view(session, record)
            record.status = AssistantTurnStatus.CANCELLING.value
            record.cancel_reason = reason
            session_record = session.get(AssistantSessionRecord, record.session_id)
            if session_record is not None:
                session_record.updated_at = now
            session.commit()
            return self._build_turn_view(session, record)

    def mark_turn_completed(
        self,
        *,
        turn_id: str,
        assistant_message: str,
        metadata: dict[str, Any] | None = None,
    ) -> AssistantTurnView:
        now = datetime.now(UTC)
        metadata_payload = metadata or {}
        with self._session_factory() as session:
            record = self._load_turn(session, turn_id)
            assistant_message_id = uuid4().hex
            session.add(
                AssistantMessageRecord(
                    id=assistant_message_id,
                    session_id=record.session_id,
                    turn_id=record.id,
                    user_id=record.user_id,
                    role=AssistantMessageRole.ASSISTANT.value,
                    content=assistant_message,
                    metadata_payload=metadata_payload,
                    created_at=now,
                )
            )
            record.assistant_message_id = assistant_message_id
            record.status = AssistantTurnStatus.COMPLETED.value
            record.completed_at = now
            session_record = session.get(AssistantSessionRecord, record.session_id)
            if session_record is not None:
                session_record.updated_at = now
            session.commit()
            return self._build_turn_view(session, record)

    def mark_turn_cancelled(self, *, turn_id: str, reason: str) -> AssistantTurnView:
        now = datetime.now(UTC)
        with self._session_factory() as session:
            record = self._load_turn(session, turn_id)
            record.status = AssistantTurnStatus.CANCELLED.value
            record.cancel_reason = reason
            record.cancelled_at = now
            session_record = session.get(AssistantSessionRecord, record.session_id)
            if session_record is not None:
                session_record.updated_at = now
            session.commit()
            return self._build_turn_view(session, record)

    def mark_turn_failed(self, *, turn_id: str, error_code: str, reason: str) -> AssistantTurnView:
        now = datetime.now(UTC)
        with self._session_factory() as session:
            record = self._load_turn(session, turn_id)
            record.status = AssistantTurnStatus.FAILED.value
            record.last_error_code = error_code
            record.cancel_reason = reason
            record.completed_at = now
            session_record = session.get(AssistantSessionRecord, record.session_id)
            if session_record is not None:
                session_record.updated_at = now
            session.commit()
            return self._build_turn_view(session, record)

    def create_tool_call(
        self,
        *,
        turn_id: str,
        tool_name: str,
        args_payload: dict[str, Any],
        waiting_for_approval: bool = False,
    ) -> AssistantToolCallView:
        now = datetime.now(UTC)
        with self._session_factory() as session:
            turn = self._load_turn(session, turn_id)
            record = AssistantToolCallRecord(
                id=uuid4().hex,
                session_id=turn.session_id,
                turn_id=turn_id,
                user_id=turn.user_id,
                tool_name=tool_name,
                status=(
                    AssistantToolCallStatus.PENDING_APPROVAL.value
                    if waiting_for_approval
                    else AssistantToolCallStatus.RUNNING.value
                ),
                args_payload=args_payload,
                result_payload=None,
                error_code=None,
                error_message=None,
                child_run_id=None,
                started_at=now,
                completed_at=None,
            )
            turn.tool_call_count += 1
            session.add(record)
            session.commit()
            return self._build_tool_call_view(record)

    def mark_tool_call_running(self, *, tool_call_id: str) -> AssistantToolCallView:
        with self._session_factory() as session:
            record = self._load_tool_call(session, tool_call_id)
            record.status = AssistantToolCallStatus.RUNNING.value
            session.commit()
            return self._build_tool_call_view(record)

    def complete_tool_call(
        self,
        *,
        tool_call_id: str,
        result_payload: dict[str, Any],
        child_run_id: str | None = None,
    ) -> AssistantToolCallView:
        with self._session_factory() as session:
            record = self._load_tool_call(session, tool_call_id)
            record.status = AssistantToolCallStatus.COMPLETED.value
            record.result_payload = result_payload
            record.child_run_id = child_run_id
            record.completed_at = datetime.now(UTC)
            session.commit()
            return self._build_tool_call_view(record)

    def fail_tool_call(
        self,
        *,
        tool_call_id: str,
        error_code: str,
        error_message: str,
        child_run_id: str | None = None,
        cancelled: bool = False,
    ) -> AssistantToolCallView:
        with self._session_factory() as session:
            record = self._load_tool_call(session, tool_call_id)
            record.status = (
                AssistantToolCallStatus.CANCELLED.value
                if cancelled
                else AssistantToolCallStatus.FAILED.value
            )
            record.error_code = error_code
            record.error_message = error_message
            record.child_run_id = child_run_id
            record.completed_at = datetime.now(UTC)
            session.commit()
            return self._build_tool_call_view(record)

    def create_stream_event(
        self,
        *,
        turn_id: str,
        event_type: str,
        payload: dict[str, Any],
        emitted_at: datetime | None = None,
    ) -> AssistantStreamEvent:
        event_time = emitted_at or datetime.now(UTC)
        with self._session_factory() as session:
            turn = self._load_turn(session, turn_id)
            current_max = (
                session.query(AssistantStreamEventRecord.sequence_number)
                .filter(AssistantStreamEventRecord.turn_id == turn_id)
                .order_by(AssistantStreamEventRecord.sequence_number.desc())
                .first()
            )
            next_sequence = (
                1 if current_max is None or current_max[0] is None else int(current_max[0]) + 1
            )
            record = AssistantStreamEventRecord(
                event_id=uuid4().hex,
                session_id=turn.session_id,
                turn_id=turn_id,
                user_id=turn.user_id,
                sequence_number=next_sequence,
                event_type=event_type,
                payload=payload,
                emitted_at=event_time,
            )
            session.add(record)
            session.commit()
            return AssistantStreamEvent(
                event_id=record.event_id,
                session_id=record.session_id,
                turn_id=record.turn_id,
                trace_id=turn.trace_id,
                workflow_id=turn.workflow_id,
                type=record.event_type,
                sequence_number=record.sequence_number,
                emitted_at=record.emitted_at,
                payload=dict(record.payload),
            )

    def create_approval_request(
        self,
        *,
        tool_call_id: str,
        approval_message: str,
        payload_summary: dict[str, Any],
        timeout_seconds: float,
    ) -> AssistantApprovalView:
        now = datetime.now(UTC)
        expires_at = now if timeout_seconds <= 0 else now + timedelta(seconds=timeout_seconds)
        with self._session_factory() as session:
            tool_call = self._load_tool_call(session, tool_call_id)
            record = AssistantApprovalRequestRecord(
                id=uuid4().hex,
                session_id=tool_call.session_id,
                turn_id=tool_call.turn_id,
                tool_call_id=tool_call.id,
                user_id=tool_call.user_id,
                tool_name=tool_call.tool_name,
                status=AssistantApprovalStatus.PENDING.value,
                approval_message=approval_message,
                payload_summary=payload_summary,
                decision_reason=None,
                decided_by_user_id=None,
                requested_at=now,
                expires_at=expires_at,
                decided_at=None,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
        self._record_event(
            event_type="assistant.approval.requested.v1",
            request_id=None,
            trace_id=None,
            workflow_id=record.turn_id,
            payload={
                "approval_request_id": record.id,
                "turn_id": record.turn_id,
                "tool_call_id": record.tool_call_id,
                "tool_name": record.tool_name,
                "status": record.status,
            },
            organisation_id=record.user_id,
        )
        return self._build_approval_view(record)

    def get_approval(self, actor: Actor, request_id: str) -> AssistantApprovalView:
        with self._session_factory() as session:
            record = self._load_owned_approval(session, actor, request_id)
            return self._build_approval_view(record)

    def get_approval_for_system(self, request_id: str) -> AssistantApprovalView:
        with self._session_factory() as session:
            record = self._load_approval(session, request_id)
            return self._build_approval_view(record)

    def list_approvals(
        self,
        *,
        actor: Actor,
        status: AssistantApprovalStatus | None = None,
        session_id: str | None = None,
        turn_id: str | None = None,
    ) -> list[AssistantApprovalView]:
        with self._session_factory() as session:
            query = session.query(AssistantApprovalRequestRecord).filter(
                AssistantApprovalRequestRecord.user_id == actor.user_id
            )
            if status is not None:
                query = query.filter(AssistantApprovalRequestRecord.status == status.value)
            if session_id is not None:
                query = query.filter(AssistantApprovalRequestRecord.session_id == session_id)
            if turn_id is not None:
                query = query.filter(AssistantApprovalRequestRecord.turn_id == turn_id)
            records = query.order_by(
                AssistantApprovalRequestRecord.requested_at.desc(),
                AssistantApprovalRequestRecord.id.desc(),
            ).all()
            return [self._build_approval_view(record) for record in records]

    def resolve_approval_request(
        self,
        *,
        actor: Actor | None,
        request_id: str,
        status: AssistantApprovalStatus,
        reason: str | None,
    ) -> AssistantApprovalView:
        now = datetime.now(UTC)
        with self._session_factory() as session:
            record = self._load_approval(session, request_id)
            if actor is not None and record.user_id != actor.user_id:
                raise auth_error(
                    "Assistant approval request is not visible to this actor",
                    code="SS-AUTH-203",
                    status_code=403,
                    details={"approval_request_id": request_id},
                )
            if AssistantApprovalStatus(record.status) is not AssistantApprovalStatus.PENDING:
                raise domain_error(
                    "Assistant approval request is no longer pending",
                    code="SS-DOMAIN-206",
                    status_code=409,
                    details={"approval_request_id": request_id, "status": record.status},
                )
            record.status = status.value
            record.decision_reason = reason
            record.decided_by_user_id = None if actor is None else actor.user_id
            record.decided_at = now
            session.commit()
            session.refresh(record)
        self._record_event(
            event_type="assistant.approval.decided.v1",
            request_id=None,
            trace_id=None,
            workflow_id=record.turn_id,
            payload={
                "approval_request_id": record.id,
                "turn_id": record.turn_id,
                "tool_call_id": record.tool_call_id,
                "tool_name": record.tool_name,
                "status": record.status,
                "decided_by_user_id": record.decided_by_user_id,
                "reason": reason,
            },
            organisation_id=record.user_id,
        )
        return self._build_approval_view(record)

    def _load_owned_session(
        self,
        session: Session,
        actor: Actor,
        session_id: str,
    ) -> AssistantSessionRecord:
        record = session.get(AssistantSessionRecord, session_id)
        if record is None:
            raise domain_error(
                "Assistant session was not found",
                code="SS-DOMAIN-203",
                status_code=404,
                details={"session_id": session_id},
            )
        if record.user_id != actor.user_id:
            raise auth_error(
                "Assistant session is not visible to this actor",
                code="SS-AUTH-202",
                status_code=403,
                details={"session_id": session_id},
            )
        return record

    def _load_owned_turn(self, session: Session, actor: Actor, turn_id: str) -> AssistantTurnRecord:
        record = self._load_turn(session, turn_id)
        if record.user_id != actor.user_id:
            raise auth_error(
                "Assistant turn is not visible to this actor",
                code="SS-AUTH-201",
                status_code=403,
                details={"turn_id": turn_id},
            )
        return record

    def _load_turn(self, session: Session, turn_id: str) -> AssistantTurnRecord:
        record = session.get(AssistantTurnRecord, turn_id)
        if record is None:
            raise domain_error(
                "Assistant turn was not found",
                code="SS-DOMAIN-204",
                status_code=404,
                details={"turn_id": turn_id},
            )
        return record

    def _load_tool_call(self, session: Session, tool_call_id: str) -> AssistantToolCallRecord:
        record = session.get(AssistantToolCallRecord, tool_call_id)
        if record is None:
            raise domain_error(
                "Assistant tool call was not found",
                code="SS-DOMAIN-205",
                status_code=404,
                details={"tool_call_id": tool_call_id},
            )
        return record

    def _load_approval(self, session: Session, request_id: str) -> AssistantApprovalRequestRecord:
        record = session.get(AssistantApprovalRequestRecord, request_id)
        if record is None:
            raise domain_error(
                "Assistant approval request was not found",
                code="SS-DOMAIN-207",
                status_code=404,
                details={"approval_request_id": request_id},
            )
        return record

    def _load_owned_approval(
        self, session: Session, actor: Actor, request_id: str
    ) -> AssistantApprovalRequestRecord:
        record = self._load_approval(session, request_id)
        if record.user_id != actor.user_id:
            raise auth_error(
                "Assistant approval request is not visible to this actor",
                code="SS-AUTH-203",
                status_code=403,
                details={"approval_request_id": request_id},
            )
        return record

    def _build_session_view(
        self, session: Session, record: AssistantSessionRecord
    ) -> AssistantSessionView:
        turns = (
            session.query(AssistantTurnRecord)
            .filter(AssistantTurnRecord.session_id == record.id)
            .order_by(AssistantTurnRecord.created_at.asc())
            .all()
        )
        messages = (
            session.query(AssistantMessageRecord)
            .filter(AssistantMessageRecord.session_id == record.id)
            .order_by(AssistantMessageRecord.created_at.asc())
            .all()
        )
        return AssistantSessionView(
            id=record.id,
            user_id=record.user_id,
            title=record.title,
            status=AssistantSessionStatus(record.status),
            created_at=record.created_at,
            updated_at=record.updated_at,
            turns=[self._build_turn_view(session, turn) for turn in turns],
            messages=[self._build_message_view(message) for message in messages],
        )

    def _build_turn_view(self, session: Session, record: AssistantTurnRecord) -> AssistantTurnView:
        messages = (
            session.query(AssistantMessageRecord)
            .filter(AssistantMessageRecord.turn_id == record.id)
            .order_by(AssistantMessageRecord.created_at.asc())
            .all()
        )
        tool_calls = (
            session.query(AssistantToolCallRecord)
            .filter(AssistantToolCallRecord.turn_id == record.id)
            .order_by(AssistantToolCallRecord.started_at.asc())
            .all()
        )
        approval_records = (
            session.query(AssistantApprovalRequestRecord)
            .filter(AssistantApprovalRequestRecord.turn_id == record.id)
            .order_by(AssistantApprovalRequestRecord.requested_at.asc())
            .all()
        )
        latest_approval_by_tool_call_id = {
            approval.tool_call_id: approval for approval in approval_records
        }
        return AssistantTurnView(
            id=record.id,
            session_id=record.session_id,
            workflow_id=record.workflow_id,
            request_id=record.request_id,
            trace_id=record.trace_id,
            pipeline_run_id=record.pipeline_run_id,
            status=AssistantTurnStatus(record.status),
            stream_token=record.stream_token,
            last_error_code=record.last_error_code,
            cancel_reason=record.cancel_reason,
            created_at=record.created_at,
            started_at=record.started_at,
            completed_at=record.completed_at,
            cancelled_at=record.cancelled_at,
            user_message_id=record.user_message_id,
            assistant_message_id=record.assistant_message_id,
            messages=[self._build_message_view(message) for message in messages],
            tool_calls=[
                self._build_tool_call_view(
                    tool_call,
                    approval=latest_approval_by_tool_call_id.get(tool_call.id),
                )
                for tool_call in tool_calls
            ],
        )

    def _build_message_view(self, record: AssistantMessageRecord) -> AssistantMessageView:
        return AssistantMessageView(
            id=record.id,
            turn_id=record.turn_id,
            role=AssistantMessageRole(record.role),
            content=record.content,
            metadata=dict(record.metadata_payload),
            created_at=record.created_at,
        )

    def _build_tool_call_view(
        self,
        record: AssistantToolCallRecord,
        *,
        approval: AssistantApprovalRequestRecord | None = None,
    ) -> AssistantToolCallView:
        return AssistantToolCallView(
            id=record.id,
            turn_id=record.turn_id,
            tool_name=record.tool_name,
            status=AssistantToolCallStatus(record.status),
            args=dict(record.args_payload),
            result=None if record.result_payload is None else dict(record.result_payload),
            error_code=record.error_code,
            error_message=record.error_message,
            child_run_id=record.child_run_id,
            started_at=record.started_at,
            completed_at=record.completed_at,
            current_approval=(None if approval is None else self._build_approval_view(approval)),
        )

    def _build_approval_view(self, record: AssistantApprovalRequestRecord) -> AssistantApprovalView:
        return AssistantApprovalView(
            id=record.id,
            session_id=record.session_id,
            turn_id=record.turn_id,
            tool_call_id=record.tool_call_id,
            tool_name=record.tool_name,
            status=AssistantApprovalStatus(record.status),
            approval_message=record.approval_message,
            payload_summary=dict(record.payload_summary),
            decision_reason=record.decision_reason,
            decided_by_user_id=record.decided_by_user_id,
            requested_at=record.requested_at,
            expires_at=record.expires_at,
            decided_at=record.decided_at,
        )

    def _record_event(
        self,
        *,
        event_type: str,
        request_id: str | None,
        trace_id: str | None,
        workflow_id: str | None,
        payload: dict[str, Any],
        organisation_id: str | None = None,
    ) -> None:
        self._workflow_events.record(
            WorkflowEvent(
                event_type=event_type,
                request_id=request_id,
                trace_id=trace_id,
                workflow_id=workflow_id,
                payload=payload,
                organisation_id=organisation_id,
            )
        )
