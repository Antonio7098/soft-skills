"""Durable generation stream persistence."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.modules.catalog.contracts.stream import (
    GenerationStage,
    GenerationStreamEvent,
)
from soft_skills_backend.platform.db.models import (
    GenerationStreamEventRecord,
    GenerationStreamRecord,
)
from soft_skills_backend.shared.auth import Actor
from soft_skills_backend.shared.errors import domain_error


def _now() -> datetime:
    return datetime.now(UTC)


class GenerationStreamRepository:
    """Persist generation sessions and ordered stream events."""

    def __init__(self, *, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def create_generation(
        self,
        *,
        actor: Actor,
        generation_id: str,
        stream_token: str,
        mode: str,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
    ) -> None:
        now = _now()
        with self._session_factory() as session:
            session.add(
                GenerationStreamRecord(
                    generation_id=generation_id,
                    user_id=actor.user_id,
                    request_id=request_id or None,
                    trace_id=trace_id or None,
                    workflow_id=workflow_id,
                    mode=mode,
                    stream_token=stream_token,
                    status="pending",
                    cancel_reason=None,
                    error_message=None,
                    collection_id=None,
                    generation_artifact_id=None,
                    created_at=now,
                    started_at=None,
                    completed_at=None,
                    cancelled_at=None,
                )
            )
            session.commit()

    def get_generation_by_stream_token(self, stream_token: str) -> GenerationStreamRecord:
        with self._session_factory() as session:
            record = (
                session.query(GenerationStreamRecord)
                .filter(GenerationStreamRecord.stream_token == stream_token)
                .one_or_none()
            )
            if record is None:
                raise domain_error(
                    "Generation stream token was not found",
                    code="SS-DOMAIN-301",
                    status_code=404,
                    details={"stream_token": stream_token},
                )
            session.expunge(record)
            return record

    def list_stream_events(
        self,
        *,
        stream_token: str,
        after_sequence: int | None = None,
    ) -> list[GenerationStreamEvent]:
        with self._session_factory() as session:
            generation = (
                session.query(GenerationStreamRecord)
                .filter(GenerationStreamRecord.stream_token == stream_token)
                .one_or_none()
            )
            if generation is None:
                raise domain_error(
                    "Generation stream token was not found",
                    code="SS-DOMAIN-301",
                    status_code=404,
                    details={"stream_token": stream_token},
                )
            query = (
                session.query(GenerationStreamEventRecord)
                .filter(GenerationStreamEventRecord.generation_id == generation.generation_id)
                .order_by(GenerationStreamEventRecord.sequence_number.asc())
            )
            if after_sequence is not None:
                query = query.filter(GenerationStreamEventRecord.sequence_number > after_sequence)
            records = query.all()
            return [
                GenerationStreamEvent(
                    event_id=record.event_id,
                    generation_id=record.generation_id,
                    type=record.event_type,
                    stage=GenerationStage(record.stage),
                    sequence_number=record.sequence_number,
                    emitted_at=record.emitted_at,
                    progress_percent=record.progress_percent,
                    payload=dict(record.payload),
                )
                for record in records
            ]

    def append_event(self, *, stream_token: str, event: GenerationStreamEvent) -> None:
        with self._session_factory() as session:
            generation = self._load_generation_by_token(session, stream_token)
            session.add(
                GenerationStreamEventRecord(
                    event_id=event.event_id,
                    generation_id=generation.generation_id,
                    user_id=generation.user_id,
                    sequence_number=event.sequence_number,
                    event_type=event.type,
                    stage=event.stage.value,
                    progress_percent=event.progress_percent,
                    payload=event.payload,
                    emitted_at=event.emitted_at,
                )
            )
            session.commit()

    def mark_running(self, *, generation_id: str) -> None:
        now = _now()
        with self._session_factory() as session:
            generation = self._load_generation(session, generation_id)
            generation.status = "running"
            generation.started_at = generation.started_at or now
            session.commit()

    def mark_completed(
        self,
        *,
        generation_id: str,
        collection_id: str,
        generation_artifact_id: str,
    ) -> None:
        now = _now()
        with self._session_factory() as session:
            generation = self._load_generation(session, generation_id)
            generation.status = "completed"
            generation.collection_id = collection_id
            generation.generation_artifact_id = generation_artifact_id
            generation.completed_at = now
            session.commit()

    def mark_failed(self, *, generation_id: str, error_message: str) -> None:
        now = _now()
        with self._session_factory() as session:
            generation = self._load_generation(session, generation_id)
            generation.status = "failed"
            generation.error_message = error_message
            generation.completed_at = now
            session.commit()

    def request_cancel(self, *, stream_token: str, reason: str) -> GenerationStreamRecord:
        now = _now()
        with self._session_factory() as session:
            generation = self._load_generation_by_token(session, stream_token)
            if generation.status in {"completed", "failed", "cancelled"}:
                session.expunge(generation)
                return generation
            generation.status = "cancelling"
            generation.cancel_reason = reason
            generation.cancelled_at = generation.cancelled_at or now
            session.commit()
            session.refresh(generation)
            session.expunge(generation)
            return generation

    def mark_cancelled(self, *, generation_id: str, reason: str) -> None:
        now = _now()
        with self._session_factory() as session:
            generation = self._load_generation(session, generation_id)
            generation.status = "cancelled"
            generation.cancel_reason = reason
            generation.cancelled_at = now
            session.commit()

    def get_cancel_reason(self, *, generation_id: str) -> str | None:
        with self._session_factory() as session:
            generation = self._load_generation(session, generation_id)
            if generation.status != "cancelling":
                return None
            return generation.cancel_reason or "user_requested"

    def _load_generation(self, session: Session, generation_id: str) -> GenerationStreamRecord:
        record = session.get(GenerationStreamRecord, generation_id)
        if record is None:
            raise domain_error(
                "Generation was not found",
                code="SS-DOMAIN-302",
                status_code=404,
                details={"generation_id": generation_id},
            )
        return record

    def _load_generation_by_token(
        self, session: Session, stream_token: str
    ) -> GenerationStreamRecord:
        record = (
            session.query(GenerationStreamRecord)
            .filter(GenerationStreamRecord.stream_token == stream_token)
            .one_or_none()
        )
        if record is None:
            raise domain_error(
                "Generation stream token was not found",
                code="SS-DOMAIN-301",
                status_code=404,
                details={"stream_token": stream_token},
            )
        return record
