"""Prompt registry persistence."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.platform.db.models import (
    PromptRenderEventRecord,
    PromptRenderMetricsRecord,
    PromptVersionRecord,
)

if TYPE_CHECKING:
    from soft_skills_backend.modules.admin.domain.builtin_prompts import BuiltinPromptDefinition


class PromptRepository:
    """Persist and retrieve prompt version records."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory
        self._builtins_seeded = False

    def create(
        self,
        name: str,
        version: str,
        prompt_type: str,
        template: str,
        variables_schema: dict[str, Any],
        output_schema: dict[str, Any] | None,
        status: str,
        parent_version_id: int | None = None,
    ) -> PromptVersionRecord:
        with self._session_factory() as session:
            record = PromptVersionRecord(
                name=name,
                version=version,
                prompt_type=prompt_type,
                template=template,
                variables_schema=variables_schema,
                output_schema=output_schema,
                status=status,
                parent_version_id=parent_version_id,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record

    def ensure_seeded(self, definitions: list[BuiltinPromptDefinition]) -> None:
        if self._builtins_seeded:
            return
        with self._session_factory() as session:
            for definition in definitions:
                existing = (
                    session.query(PromptVersionRecord)
                    .filter(
                        PromptVersionRecord.name == definition.name,
                        PromptVersionRecord.version == definition.version,
                    )
                    .first()
                )
                if existing is not None:
                    continue
                session.add(
                    PromptVersionRecord(
                        name=definition.name,
                        version=definition.version,
                        prompt_type=definition.prompt_type,
                        template=definition.template,
                        variables_schema=definition.variables_schema,
                        output_schema=definition.output_schema,
                        status=definition.status,
                    )
                )
            session.commit()
        self._builtins_seeded = True

    def get_by_name_version(self, name: str, version: str) -> PromptVersionRecord | None:
        with self._session_factory() as session:
            return (
                session.query(PromptVersionRecord)
                .filter(
                    PromptVersionRecord.name == name,
                    PromptVersionRecord.version == version,
                )
                .first()
            )

    def get_by_id(self, id: int) -> PromptVersionRecord | None:
        with self._session_factory() as session:
            return session.get(PromptVersionRecord, id)

    def list_by_name(self, name: str) -> list[PromptVersionRecord]:
        with self._session_factory() as session:
            return (
                session.query(PromptVersionRecord)
                .filter(PromptVersionRecord.name == name)
                .order_by(PromptVersionRecord.version.desc())
                .all()
            )

    def list_latest_by_name(self) -> list[PromptVersionRecord]:
        with self._session_factory() as session:
            subquery = (
                session.query(
                    PromptVersionRecord.name,
                    PromptVersionRecord.version,
                )
                .filter(PromptVersionRecord.status == "published")
                .order_by(PromptVersionRecord.name, PromptVersionRecord.version.desc())
                .distinct(PromptVersionRecord.name)
            ).subquery()

            query = session.query(PromptVersionRecord).join(
                subquery,
                (PromptVersionRecord.name == subquery.c.name)
                & (PromptVersionRecord.version == subquery.c.version),
            )
            return query.all()

    def list_all_names(self) -> list[tuple[str, PromptVersionRecord]]:
        with self._session_factory() as session:
            records = (
                session.query(PromptVersionRecord)
                .filter(PromptVersionRecord.status == "published")
                .order_by(PromptVersionRecord.name, PromptVersionRecord.version.desc())
                .all()
            )
            name_to_latest: dict[str, PromptVersionRecord] = {}
            for record in records:
                if record.name not in name_to_latest:
                    name_to_latest[record.name] = record
            return list(name_to_latest.items())

    def update(
        self,
        id: int,
        template: str | None = None,
        variables_schema: dict[str, Any] | None = None,
        output_schema: dict[str, Any] | None = None,
        status: str | None = None,
    ) -> PromptVersionRecord | None:
        with self._session_factory() as session:
            record = session.get(PromptVersionRecord, id)
            if record is None:
                return None
            if template is not None:
                record.template = template
            if variables_schema is not None:
                record.variables_schema = variables_schema
            if output_schema is not None:
                record.output_schema = output_schema
            if status is not None:
                record.status = status
            record.updated_at = datetime.now(UTC)
            session.commit()
            session.refresh(record)
            return record

    def get_render_metrics(self, prompt_version_id: int) -> PromptRenderMetricsRecord | None:
        with self._session_factory() as session:
            return (
                session.query(PromptRenderMetricsRecord)
                .filter(PromptRenderMetricsRecord.prompt_version_id == prompt_version_id)
                .first()
            )

    def upsert_render_metrics(
        self,
        prompt_version_id: int,
        render_count: int,
        success_count: int,
        failure_count: int,
        avg_latency_ms: float | None,
        total_tokens: int,
    ) -> PromptRenderMetricsRecord:
        with self._session_factory() as session:
            record = (
                session.query(PromptRenderMetricsRecord)
                .filter(PromptRenderMetricsRecord.prompt_version_id == prompt_version_id)
                .first()
            )
            if record is None:
                record = PromptRenderMetricsRecord(
                    prompt_version_id=prompt_version_id,
                    render_count=render_count,
                    success_count=success_count,
                    failure_count=failure_count,
                    avg_latency_ms=avg_latency_ms,
                    total_tokens=total_tokens,
                    last_rendered_at=datetime.now(UTC),
                )
                session.add(record)
            else:
                record.render_count = render_count
                record.success_count = success_count
                record.failure_count = failure_count
                record.avg_latency_ms = avg_latency_ms
                record.total_tokens = total_tokens
                record.last_rendered_at = datetime.now(UTC)
            session.commit()
            session.refresh(record)
            return record

    def record_render_event(
        self,
        event_id: str,
        prompt_version_id: int,
        success: bool,
        latency_ms: int | None,
        tokens: int | None,
        error_code: str | None,
        trace_id: str | None,
    ) -> PromptRenderEventRecord:
        with self._session_factory() as session:
            record = PromptRenderEventRecord(
                event_id=event_id,
                prompt_version_id=prompt_version_id,
                success=success,
                latency_ms=latency_ms,
                tokens=tokens,
                error_code=error_code,
                trace_id=trace_id,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record

    def list_render_events(
        self,
        prompt_version_id: int,
        offset: int = 0,
        limit: int = 50,
    ) -> list[PromptRenderEventRecord]:
        with self._session_factory() as session:
            return (
                session.query(PromptRenderEventRecord)
                .filter(PromptRenderEventRecord.prompt_version_id == prompt_version_id)
                .order_by(PromptRenderEventRecord.rendered_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
