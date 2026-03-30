"""Admin-agent audit and history repository."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.platform.db.models import WorkflowEventRecord


class AdminAgentRepository:
    """Persist and load admin-agent audit artifacts from workflow events."""

    RESPONSE_EVENT_TYPE = "admin.agent.response.completed.v1"

    def __init__(self, *, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def list_conversation_history(
        self,
        *,
        conversation_id: str,
        organisation_id: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        with self._session_factory() as session:
            records = (
                session.query(WorkflowEventRecord)
                .filter(
                    WorkflowEventRecord.workflow_id == conversation_id,
                    WorkflowEventRecord.organisation_id == organisation_id,
                    WorkflowEventRecord.event_type == self.RESPONSE_EVENT_TYPE,
                )
                .order_by(WorkflowEventRecord.occurred_at.desc())
                .limit(limit)
                .all()
            )
        history: list[dict[str, Any]] = []
        for record in reversed(records):
            history.append(
                {
                    "question": record.payload.get("question"),
                    "response_preview": record.payload.get("response_preview"),
                    "sql": record.payload.get("sql"),
                    "row_count": record.payload.get("row_count"),
                }
            )
        return history

    def record_event(
        self,
        *,
        event_type: str,
        request_id: str,
        trace_id: str,
        workflow_id: str,
        organisation_id: str,
        payload: dict[str, Any],
        error_code: str | None = None,
    ) -> None:
        with self._session_factory() as session:
            session.add(
                WorkflowEventRecord(
                    event_id=uuid4().hex,
                    event_type=event_type,
                    request_id=request_id,
                    trace_id=trace_id,
                    workflow_id=workflow_id,
                    error_code=error_code,
                    organisation_id=organisation_id,
                    payload=payload,
                    occurred_at=datetime.now(UTC),
                )
            )
            session.commit()
