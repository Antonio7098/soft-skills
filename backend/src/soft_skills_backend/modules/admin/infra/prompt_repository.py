"""Prompt registry persistence with parent-child model."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.platform.db.models import (
    PromptRecord,
    PromptRenderEventRecord,
    PromptRenderMetricsRecord,
    PromptVersionRecord,
)

if TYPE_CHECKING:
    from soft_skills_backend.modules.admin.domain.builtin_prompts import BuiltinPromptDefinition


class PromptRepository:
    """Persist and retrieve prompt version records with parent-child model."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory
        self._builtins_seeded = False

    def _get_or_create_prompt_record(
        self,
        session: Session,
        name: str,
        prompt_type: str,
        organisation_id: str | None = None,
    ) -> PromptRecord:
        """Get or create a PromptRecord parent and return it."""
        existing = (
            session.query(PromptRecord)
            .filter(
                PromptRecord.name == name,
                PromptRecord.organisation_id == organisation_id,
            )
            .first()
        )
        if existing is not None:
            return existing

        record = PromptRecord(
            id=name,
            name=name,
            prompt_type=prompt_type,
            organisation_id=organisation_id,
            variables_schema={},
        )
        session.add(record)
        return record

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
        organisation_id: str | None = None,
    ) -> PromptVersionRecord:
        with self._session_factory() as session:
            prompt_record = self._get_or_create_prompt_record(
                session, name, prompt_type, organisation_id
            )
            record = PromptVersionRecord(
                prompt_id=prompt_record.id,
                version=version,
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
                prompt_record = self._get_or_create_prompt_record(
                    session, definition.name, definition.prompt_type
                )
                existing = (
                    session.query(PromptVersionRecord)
                    .filter(
                        PromptVersionRecord.prompt_id == prompt_record.id,
                        PromptVersionRecord.version == definition.version,
                    )
                    .first()
                )
                if existing is not None:
                    continue
                session.add(
                    PromptVersionRecord(
                        prompt_id=prompt_record.id,
                        version=definition.version,
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
            prompt_record = session.query(PromptRecord).filter(PromptRecord.name == name).first()
            if prompt_record is None:
                return None
            return (
                session.query(PromptVersionRecord)
                .filter(
                    PromptVersionRecord.prompt_id == prompt_record.id,
                    PromptVersionRecord.version == version,
                )
                .first()
            )

    def get_by_id(self, id: int) -> PromptVersionRecord | None:
        with self._session_factory() as session:
            return session.get(PromptVersionRecord, id)

    def get_prompt_type(self, name: str) -> str:
        with self._session_factory() as session:
            prompt_record = session.query(PromptRecord).filter(PromptRecord.name == name).first()
            if prompt_record is None:
                return ""
            return prompt_record.prompt_type

    def list_by_name(self, name: str) -> list[PromptVersionRecord]:
        with self._session_factory() as session:
            prompt_record = session.query(PromptRecord).filter(PromptRecord.name == name).first()
            if prompt_record is None:
                return []
            return (
                session.query(PromptVersionRecord)
                .filter(PromptVersionRecord.prompt_id == prompt_record.id)
                .order_by(PromptVersionRecord.version.desc())
                .all()
            )

    def list_latest_by_name(self) -> list[PromptVersionRecord]:
        with self._session_factory() as session:
            prompt_records = session.query(PromptRecord).all()
            result: list[PromptVersionRecord] = []
            for prompt_record in prompt_records:
                latest = (
                    session.query(PromptVersionRecord)
                    .filter(
                        PromptVersionRecord.prompt_id == prompt_record.id,
                        PromptVersionRecord.status == "published",
                    )
                    .order_by(PromptVersionRecord.version.desc())
                    .first()
                )
                if latest is not None:
                    result.append(latest)
            return result

    def list_all_names(self) -> list[tuple[str, str, PromptVersionRecord]]:
        with self._session_factory() as session:
            result: list[tuple[str, str, PromptVersionRecord]] = []
            prompt_records = session.query(PromptRecord).all()
            for prompt_record in prompt_records:
                latest = (
                    session.query(PromptVersionRecord)
                    .filter(
                        PromptVersionRecord.prompt_id == prompt_record.id,
                        PromptVersionRecord.status == "published",
                    )
                    .order_by(PromptVersionRecord.version.desc())
                    .first()
                )
                if latest is not None:
                    result.append((prompt_record.name, prompt_record.prompt_type, latest))
            return result

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
