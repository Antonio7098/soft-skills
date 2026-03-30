"""New prompt repository supporting parent-child model with org filtering."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session, sessionmaker

if TYPE_CHECKING:
    from uuid import UUID

    from soft_skills_backend.modules.admin.domain.builtin_prompts import BuiltinPromptDefinition


class PromptRepositoryV2:
    """Persist and retrieve prompt version records with parent-child model."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory
        self._builtins_seeded = False

    def get_or_create_prompt(
        self,
        *,
        prompt_id: str,
        organisation_id: str | None = None,
        name: str,
        prompt_type: str,
    ) -> tuple[str, datetime]:
        """Get or create a prompt parent record, return (id, created_at)."""
        with self._session_factory() as session:
            from soft_skills_backend.platform.db.models import PromptVersionRecord

            result = (
                session.query(PromptVersionRecord)
                .filter(
                    PromptVersionRecord.name == name,
                    PromptVersionRecord.prompt_type == prompt_type,
                )
                .first()
            )
            now = datetime.now(UTC)
            if result is None:
                return (name, now)
            return (str(result.id), result.created_at)

    def create_version(
        self,
        prompt_id: str,
        version: str,
        template: str,
        variables_schema: dict[str, Any],
        output_schema: dict[str, Any] | None,
        status: str,
        parent_version_id: int | None = None,
    ) -> int:
        """Create a new prompt version under a prompt parent."""
        with self._session_factory() as session:
            from soft_skills_backend.platform.db.models import PromptVersionRecord

            record = PromptVersionRecord(
                prompt_id=prompt_id,
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
            return record.id

    def ensure_seeded(self, definitions: list[BuiltinPromptDefinition]) -> None:
        """Seed builtin prompts using name-based resolution."""
        if self._builtins_seeded:
            return
        with self._session_factory() as session:
            from soft_skills_backend.platform.db.models import PromptVersionRecord

            for definition in definitions:
                existing = (
                    session.query(PromptVersionRecord)
                    .filter(
                        PromptVersionRecord.version == definition.version,
                        PromptVersionRecord.template == definition.template,
                    )
                    .first()
                )
                if existing is not None:
                    continue
                record = PromptVersionRecord(
                    prompt_id=definition.name,
                    version=definition.version,
                    template=definition.template,
                    variables_schema=definition.variables_schema,
                    output_schema=definition.output_schema,
                    status=definition.status,
                )
                session.add(record)
            session.commit()
        self._builtins_seeded = True

    def get_by_name_version(self, name: str, version: str) -> PromptVersionRecord | None:
        """Get prompt version by parent name and version string."""
        with self._session_factory() as session:
            from soft_skills_backend.platform.db.models import PromptVersionRecord

            return (
                session.query(PromptVersionRecord)
                .filter(
                    PromptVersionRecord.prompt_id == name,
                    PromptVersionRecord.version == version,
                )
                .first()
            )

    def get_by_id(self, id: int) -> PromptVersionRecord | None:
        """Get prompt version by integer ID."""
        with self._session_factory() as session:
            from soft_skills_backend.platform.db.models import PromptVersionRecord

            return session.get(PromptVersionRecord, id)

    def list_by_name(self, name: str) -> list[PromptVersionRecord]:
        """List all versions of a prompt by parent name."""
        with self._session_factory() as session:
            from soft_skills_backend.platform.db.models import PromptVersionRecord

            return (
                session.query(PromptVersionRecord)
                .filter(PromptVersionRecord.prompt_id == name)
                .order_by(PromptVersionRecord.version.desc())
                .all()
            )

    def update_status(
        self,
        id: int,
        status: str,
    ) -> PromptVersionRecord | None:
        """Update the status of a prompt version."""
        with self._session_factory() as session:
            from soft_skills_backend.platform.db.models import PromptVersionRecord

            record = session.get(PromptVersionRecord, id)
            if record is None:
                return None
            record.status = status
            record.updated_at = datetime.now(UTC)
            session.commit()
            session.refresh(record)
            return record


class PromptResolutionService:
    """Resolve prompt names to UUIDs and version IDs at runtime."""

    def __init__(self, repository: PromptRepositoryV2) -> None:
        self._repository = repository
        self._name_to_id: dict[str, str] = {}
        self._initialized = False

    def resolve(self, name: str, version: str) -> tuple[str, int] | None:
        """Resolve name+version to (prompt_id, version_id) pair."""
        if not self._initialized:
            self._refresh()
            self._initialized = True

        prompt_version = self._repository.get_by_name_version(name, version)
        if prompt_version is None:
            return None
        return (prompt_version.prompt_id, prompt_version.id)

    def _refresh(self) -> None:
        """Refresh the name→id cache."""
        from soft_skills_backend.platform.db.models import PromptVersionRecord

        with self._repository._session_factory() as session:
            records = session.query(PromptVersionRecord).all()
            self._name_to_id = {rec.prompt_id: str(rec.id) for rec in records}
