"""SQLAlchemy repository adapters."""

from __future__ import annotations

import re
from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.platform.db.models import (
    PipelineDefinitionRecord,
    PipelineExecutionTraceRecord,
    PipelineRunRecord,
    ProviderCallRecord,
    StageDefinitionRecord,
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
                    user_id=event.user_id,
                    payload=event.payload,
                    occurred_at=event.occurred_at,
                )
            )
            session.commit()

    VALID_SORT_FIELDS = frozenset(
        {"event_type", "trace_id", "workflow_id", "error_code", "occurred_at", "user_id"}
    )

    def list_(
        self,
        *,
        event_type: str | None = None,
        trace_id: str | None = None,
        workflow_id: str | None = None,
        request_id: str | None = None,
        error_code: str | None = None,
        user_id: str | None = None,
        organisation_id: str | None = None,
        search: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        sort_by: str | None = None,
        sort_order: str | None = None,
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
            if user_id is not None:
                query = query.filter(WorkflowEventRecord.user_id == user_id)
            if organisation_id is not None:
                query = query.filter(
                    (WorkflowEventRecord.organisation_id == organisation_id)
                    | (WorkflowEventRecord.organisation_id.is_(None))
                )
            if search:
                query = self._apply_search(query, search)
            if from_date is not None:
                query = query.filter(WorkflowEventRecord.occurred_at >= from_date)
            if to_date is not None:
                query = query.filter(WorkflowEventRecord.occurred_at <= to_date)
            order_col = self._resolve_sort_column(sort_by)
            if sort_order and sort_order.lower() == "asc":
                query = query.order_by(order_col.asc())
            else:
                query = query.order_by(order_col.desc())
            return query.offset(offset).limit(limit).all()

    def count(
        self,
        *,
        event_type: str | None = None,
        trace_id: str | None = None,
        workflow_id: str | None = None,
        request_id: str | None = None,
        error_code: str | None = None,
        user_id: str | None = None,
        organisation_id: str | None = None,
        search: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
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
            if user_id is not None:
                query = query.filter(WorkflowEventRecord.user_id == user_id)
            if organisation_id is not None:
                query = query.filter(
                    (WorkflowEventRecord.organisation_id == organisation_id)
                    | (WorkflowEventRecord.organisation_id.is_(None))
                )
            if search:
                query = self._apply_search(query, search)
            if from_date is not None:
                query = query.filter(WorkflowEventRecord.occurred_at >= from_date)
            if to_date is not None:
                query = query.filter(WorkflowEventRecord.occurred_at <= to_date)
            return query.count()

    def _apply_search(self, query, pattern: str):
        search_columns = [
            WorkflowEventRecord.event_type,
            WorkflowEventRecord.trace_id,
            WorkflowEventRecord.workflow_id,
            WorkflowEventRecord.request_id,
            WorkflowEventRecord.error_code,
            WorkflowEventRecord.user_id,
        ]
        try:
            compiled = re.compile(pattern, re.IGNORECASE)
        except re.error:
            return query.filter(WorkflowEventRecord.event_type == "__never_match_invalid_regex__")
        conditions = [col.regexp_match(pattern) for col in search_columns]
        return query.filter(or_(*conditions))

    def _resolve_sort_column(self, sort_by: str | None):
        column_map = {
            "event_type": WorkflowEventRecord.event_type,
            "trace_id": WorkflowEventRecord.trace_id,
            "workflow_id": WorkflowEventRecord.workflow_id,
            "error_code": WorkflowEventRecord.error_code,
            "occurred_at": WorkflowEventRecord.occurred_at,
            "user_id": WorkflowEventRecord.user_id,
        }
        if sort_by and sort_by in self.VALID_SORT_FIELDS:
            return column_map[sort_by]
        return WorkflowEventRecord.occurred_at

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

    def list_by_pipeline(
        self, pipeline_name: str, *, offset: int = 0, limit: int = 50
    ) -> list[PipelineRunRecord]:
        """List pipeline runs for a specific pipeline."""
        with self._session_factory() as session:
            return (
                session.query(PipelineRunRecord)
                .filter(PipelineRunRecord.pipeline_name == pipeline_name)
                .order_by(PipelineRunRecord.started_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )


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
                    prompt_tokens=log.prompt_tokens,
                    completion_tokens=log.completion_tokens,
                    cost_usd=log.cost_usd,
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
                record.prompt_tokens = log.prompt_tokens
                record.completion_tokens = log.completion_tokens
                record.cost_usd = log.cost_usd
            session.commit()


class SqlAlchemyPipelineDefinitionRepository:
    """Persist and retrieve pipeline definition records."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def upsert(self, record: PipelineDefinitionRecord) -> None:
        with self._session_factory() as session:
            existing = session.get(PipelineDefinitionRecord, record.pipeline_name)
            if existing is None:
                session.add(record)
            else:
                existing.topology = record.topology
                existing.description = record.description
                existing.stage_definitions = record.stage_definitions
                existing.updated_at = record.updated_at
            session.commit()

    def get_by_name(self, pipeline_name: str) -> PipelineDefinitionRecord | None:
        with self._session_factory() as session:
            return session.get(PipelineDefinitionRecord, pipeline_name)

    def list_all(self) -> list[PipelineDefinitionRecord]:
        with self._session_factory() as session:
            return (
                session.query(PipelineDefinitionRecord)
                .order_by(PipelineDefinitionRecord.pipeline_name)
                .all()
            )

    def delete(self, pipeline_name: str) -> bool:
        with self._session_factory() as session:
            record = session.get(PipelineDefinitionRecord, pipeline_name)
            if record is None:
                return False
            session.delete(record)
            session.commit()
            return True


class SqlAlchemyStageDefinitionRepository:
    """Persist and retrieve stage definition records."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def upsert_batch(self, pipeline_name: str, stages: list[StageDefinitionRecord]) -> None:
        with self._session_factory() as session:
            session.query(StageDefinitionRecord).filter(
                StageDefinitionRecord.pipeline_name == pipeline_name
            ).delete()
            for stage in stages:
                session.add(stage)
            session.commit()

    def get_by_pipeline(self, pipeline_name: str) -> list[StageDefinitionRecord]:
        with self._session_factory() as session:
            return (
                session.query(StageDefinitionRecord)
                .filter(StageDefinitionRecord.pipeline_name == pipeline_name)
                .order_by(StageDefinitionRecord.id)
                .all()
            )


class SqlAlchemyPipelineExecutionTraceRepository:
    """Persist and retrieve pipeline execution traces."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def upsert(self, record: PipelineExecutionTraceRecord) -> None:
        with self._session_factory() as session:
            existing = session.get(PipelineExecutionTraceRecord, record.pipeline_run_id)
            if existing is None:
                session.add(record)
            else:
                existing.pipeline_name = record.pipeline_name
                existing.execution_sequence = record.execution_sequence
                existing.total_duration_ms = record.total_duration_ms
                existing.started_at = record.started_at
                existing.completed_at = record.completed_at
            session.commit()

    def get_by_run_id(self, pipeline_run_id: str) -> PipelineExecutionTraceRecord | None:
        with self._session_factory() as session:
            return session.get(PipelineExecutionTraceRecord, pipeline_run_id)

    def get_by_pipeline(
        self, pipeline_name: str, *, offset: int = 0, limit: int = 50
    ) -> list[PipelineExecutionTraceRecord]:
        with self._session_factory() as session:
            return (
                session.query(PipelineExecutionTraceRecord)
                .filter(PipelineExecutionTraceRecord.pipeline_name == pipeline_name)
                .order_by(PipelineExecutionTraceRecord.started_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
