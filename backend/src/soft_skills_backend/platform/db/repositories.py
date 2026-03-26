"""SQLAlchemy repository adapters."""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.platform.db.models import (
    PipelineRunRecord,
    ProviderCallRecord,
    WorkflowEventRecord,
)
from soft_skills_backend.platform.observability.events import (
    PipelineRunLog,
    ProviderCallLog,
    WorkflowEvent,
)


class SqlAlchemyWorkflowEventRepository:
    """Persist workflow events."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def record(self, event: WorkflowEvent) -> None:
        with self._session_factory() as session:
            session.add(
                WorkflowEventRecord(
                    event_id=event.event_id,
                    event_type=event.event_type,
                    request_id=event.request_id,
                    trace_id=event.trace_id,
                    workflow_id=event.workflow_id,
                    error_code=event.error_code,
                    organisation_id=event.organisation_id,
                    payload=event.payload,
                    occurred_at=event.occurred_at,
                )
            )
            session.commit()

    def list_(
        self,
        *,
        event_type: str | None = None,
        trace_id: str | None = None,
        workflow_id: str | None = None,
        request_id: str | None = None,
        error_code: str | None = None,
        organisation_id: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[WorkflowEventRecord]:
        with self._session_factory() as session:
            query = session.query(WorkflowEventRecord)
            if event_type is not None:
                query = query.filter(WorkflowEventRecord.event_type == event_type)
            if trace_id is not None:
                query = query.filter(WorkflowEventRecord.trace_id == trace_id)
            if workflow_id is not None:
                query = query.filter(WorkflowEventRecord.workflow_id == workflow_id)
            if request_id is not None:
                query = query.filter(WorkflowEventRecord.request_id == request_id)
            if error_code is not None:
                query = query.filter(WorkflowEventRecord.error_code == error_code)
            if organisation_id is not None:
                # Include events for this org AND global events (organisation_id IS NULL)
                query = query.filter(
                    (WorkflowEventRecord.organisation_id == organisation_id)
                    | (WorkflowEventRecord.organisation_id.is_(None))
                )
            return (
                query.order_by(WorkflowEventRecord.occurred_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

    def count(
        self,
        *,
        event_type: str | None = None,
        trace_id: str | None = None,
        workflow_id: str | None = None,
        request_id: str | None = None,
        error_code: str | None = None,
        organisation_id: str | None = None,
    ) -> int:
        with self._session_factory() as session:
            query = session.query(WorkflowEventRecord)
            if event_type is not None:
                query = query.filter(WorkflowEventRecord.event_type == event_type)
            if trace_id is not None:
                query = query.filter(WorkflowEventRecord.trace_id == trace_id)
            if workflow_id is not None:
                query = query.filter(WorkflowEventRecord.workflow_id == workflow_id)
            if request_id is not None:
                query = query.filter(WorkflowEventRecord.request_id == request_id)
            if error_code is not None:
                query = query.filter(WorkflowEventRecord.error_code == error_code)
            if organisation_id is not None:
                # Include events for this org AND global events (organisation_id IS NULL)
                query = query.filter(
                    (WorkflowEventRecord.organisation_id == organisation_id)
                    | (WorkflowEventRecord.organisation_id.is_(None))
                )
            return query.count()

    def get_by_id(self, event_id: str) -> WorkflowEventRecord | None:
        with self._session_factory() as session:
            return (
                session.query(WorkflowEventRecord)
                .filter(WorkflowEventRecord.event_id == event_id)
                .first()
            )

    def update(
        self,
        event_id: str,
        *,
        error_code: str | None = None,
        payload: dict[str, object] | None = None,
    ) -> WorkflowEventRecord | None:
        with self._session_factory() as session:
            record = (
                session.query(WorkflowEventRecord)
                .filter(WorkflowEventRecord.event_id == event_id)
                .first()
            )
            if record is None:
                return None
            if error_code is not None:
                record.error_code = error_code
            if payload is not None:
                record.payload = payload
            session.commit()
            session.refresh(record)
            return record

    def delete(self, event_id: str) -> bool:
        with self._session_factory() as session:
            record = (
                session.query(WorkflowEventRecord)
                .filter(WorkflowEventRecord.event_id == event_id)
                .first()
            )
            if record is None:
                return False
            session.delete(record)
            session.commit()
            return True


class SqlAlchemyPipelineRunRepository:
    """Persist pipeline run lifecycle records."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def upsert(self, log: PipelineRunLog) -> None:
        with self._session_factory() as session:
            record = session.get(PipelineRunRecord, log.pipeline_run_id)
            if record is None:
                record = PipelineRunRecord(
                    pipeline_run_id=log.pipeline_run_id,
                    pipeline_name=log.pipeline_name,
                    topology=log.topology,
                    execution_mode=log.execution_mode,
                    status=log.status,
                    request_id=log.request_id,
                    trace_id=log.trace_id,
                    user_id=log.user_id,
                    error=log.error,
                    failed_stage=log.failed_stage,
                    stage_results=log.stage_results,
                    started_at=log.started_at,
                    finished_at=log.finished_at,
                )
                session.add(record)
            else:
                record.pipeline_name = log.pipeline_name
                record.topology = log.topology
                record.execution_mode = log.execution_mode
                record.status = log.status
                record.request_id = log.request_id
                record.trace_id = log.trace_id
                record.user_id = log.user_id
                record.error = log.error
                record.failed_stage = log.failed_stage
                record.stage_results = log.stage_results
                record.started_at = log.started_at
                record.finished_at = log.finished_at
            session.commit()


class SqlAlchemyProviderCallRepository:
    """Persist provider call telemetry."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def upsert(self, log: ProviderCallLog) -> None:
        with self._session_factory() as session:
            record = session.query(ProviderCallRecord).filter_by(call_id=log.call_id).one_or_none()
            if record is None:
                record = ProviderCallRecord(
                    call_id=log.call_id,
                    operation=log.operation,
                    provider=log.provider,
                    model_id=log.model_id,
                    success=log.success,
                    latency_ms=log.latency_ms,
                    error=log.error,
                    pipeline_run_id=log.pipeline_run_id,
                    request_id=log.request_id,
                    trace_id=log.trace_id,
                    metrics=log.metrics,
                    created_at=log.created_at,
                )
                session.add(record)
            else:
                record.operation = log.operation
                record.provider = log.provider
                record.model_id = log.model_id
                record.success = log.success
                record.latency_ms = log.latency_ms
                record.error = log.error
                record.pipeline_run_id = log.pipeline_run_id
                record.request_id = log.request_id
                record.trace_id = log.trace_id
                record.metrics = log.metrics
                record.created_at = log.created_at
            session.commit()
