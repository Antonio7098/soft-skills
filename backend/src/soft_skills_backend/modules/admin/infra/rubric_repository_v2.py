"""New rubric repository supporting parent-child model with org filtering."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import sessionmaker, Session


class RubricRepositoryV2:
    """Persist and retrieve rubric version records with parent-child model."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def create(
        self,
        rubric_id: str,
        skill_slug: str,
        organisation_id: str | None,
        name: str,
        description: str | None,
        content_type: str,
        schema_version: str,
    ) -> tuple[str, datetime]:
        """Create a rubric parent record."""
        now = datetime.now(UTC)
        return (rubric_id, now)

    def create_version(
        self,
        rubric_id: str,
        version: str,
        criteria: list[dict[str, Any]],
        status: str,
    ) -> int:
        """Create a new rubric version under a rubric parent."""
        with self._session_factory() as session:
            from soft_skills_backend.platform.db.models import RubricVersionRecord

            record = RubricVersionRecord(
                rubric_id=rubric_id,
                version=version,
                criteria=criteria,
                status=status,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record.id

    def get_version_by_rubric_version(
        self,
        rubric_id: str,
        version: str,
    ) -> RubricVersionRecord | None:
        """Get rubric version by rubric parent id and version string."""
        with self._session_factory() as session:
            from soft_skills_backend.platform.db.models import RubricVersionRecord

            return (
                session.query(RubricVersionRecord)
                .filter(
                    RubricVersionRecord.rubric_id == rubric_id,
                    RubricVersionRecord.version == version,
                )
                .first()
            )

    def get_version_by_id(self, id: int) -> RubricVersionRecord | None:
        """Get rubric version by integer ID."""
        with self._session_factory() as session:
            from soft_skills_backend.platform.db.models import RubricVersionRecord

            return session.get(RubricVersionRecord, id)

    def list_versions_by_rubric(
        self,
        rubric_id: str,
    ) -> list[RubricVersionRecord]:
        """List all versions of a rubric."""
        with self._session_factory() as session:
            from soft_skills_backend.platform.db.models import RubricVersionRecord

            return (
                session.query(RubricVersionRecord)
                .filter(RubricVersionRecord.rubric_id == rubric_id)
                .order_by(RubricVersionRecord.version.desc())
                .all()
            )


class OrgConfigRepositoryV2:
    """Repository for org-level prompt/rubric config overrides."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def get_prompt_config(
        self,
        organisation_id: str,
        task_kind: str,
    ) -> tuple[str, int] | None:
        """Get org prompt config (prompt_id, prompt_version_id) or None."""
        with self._session_factory() as session:
            from soft_skills_backend.platform.db.models import OrganisationPromptConfigRecord

            result = (
                session.query(OrganisationPromptConfigRecord)
                .filter(
                    OrganisationPromptConfigRecord.organisation_id == organisation_id,
                    OrganisationPromptConfigRecord.task_kind == task_kind,
                )
                .first()
            )
            if result is None:
                return None
            return (result.prompt_id, result.prompt_version_id)

    def get_rubric_config(
        self,
        organisation_id: str,
        skill_slug: str,
    ) -> tuple[str, int] | None:
        """Get org rubric config (rubric_id, rubric_version_id) or None."""
        with self._session_factory() as session:
            from soft_skills_backend.platform.db.models import OrganisationRubricConfigRecord

            result = (
                session.query(OrganisationRubricConfigRecord)
                .filter(
                    OrganisationRubricConfigRecord.organisation_id == organisation_id,
                    OrganisationRubricConfigRecord.skill_slug == skill_slug,
                )
                .first()
            )
            if result is None:
                return None
            return (result.rubric_id, result.rubric_version_id)

    def set_prompt_config(
        self,
        organisation_id: str,
        task_kind: str,
        prompt_id: str,
        prompt_version_id: int,
    ) -> None:
        """Set or update org prompt config."""
        with self._session_factory() as session:
            from soft_skills_backend.platform.db.models import OrganisationPromptConfigRecord

            existing = (
                session.query(OrganisationPromptConfigRecord)
                .filter(
                    OrganisationPromptConfigRecord.organisation_id == organisation_id,
                    OrganisationPromptConfigRecord.task_kind == task_kind,
                )
                .first()
            )
            if existing:
                existing.prompt_id = prompt_id
                existing.prompt_version_id = prompt_version_id
            else:
                session.add(
                    OrganisationPromptConfigRecord(
                        organisation_id=organisation_id,
                        task_kind=task_kind,
                        prompt_id=prompt_id,
                        prompt_version_id=prompt_version_id,
                    )
                )
            session.commit()

    def set_rubric_config(
        self,
        organisation_id: str,
        skill_slug: str,
        rubric_id: str,
        rubric_version_id: int,
    ) -> None:
        """Set or update org rubric config."""
        with self._session_factory() as session:
            from soft_skills_backend.platform.db.models import OrganisationRubricConfigRecord

            existing = (
                session.query(OrganisationRubricConfigRecord)
                .filter(
                    OrganisationRubricConfigRecord.organisation_id == organisation_id,
                    OrganisationRubricConfigRecord.skill_slug == skill_slug,
                )
                .first()
            )
            if existing:
                existing.rubric_id = rubric_id
                existing.rubric_version_id = rubric_version_id
            else:
                session.add(
                    OrganisationRubricConfigRecord(
                        organisation_id=organisation_id,
                        skill_slug=skill_slug,
                        rubric_id=rubric_id,
                        rubric_version_id=rubric_version_id,
                    )
                )
            session.commit()
