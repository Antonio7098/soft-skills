"""Admin-to-learner relationship persistence."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.modules.admin.contracts.commands import AdminLearnerRelationshipCommand
from soft_skills_backend.modules.admin.contracts.views import AdminLearnerRelationshipView
from soft_skills_backend.modules.admin.domain.relationships import (
    validate_admin_relationship_target,
    validate_admin_relationship_type,
)
from soft_skills_backend.platform.db.models import (
    AdminLearnerRelationshipRecord,
    LearnerProfileRecord,
)
from soft_skills_backend.shared.auth import Actor
from soft_skills_backend.shared.errors import domain_error


def _utcnow() -> datetime:
    return datetime.now(UTC)


class AdminRelationshipRepository:
    """Manage explicit admin-to-learner access grants."""

    def __init__(self, *, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def get_relationship(
        self,
        *,
        admin_user_id: str,
        learner_user_id: str,
    ) -> AdminLearnerRelationshipView | None:
        with self._session_factory() as session:
            record = session.get(
                AdminLearnerRelationshipRecord,
                {"learner_user_id": learner_user_id, "admin_user_id": admin_user_id},
            )
            return None if record is None else self._to_view(record)

    def upsert_relationship(
        self,
        actor: Actor,
        *,
        learner_user_id: str,
        command: AdminLearnerRelationshipCommand,
    ) -> AdminLearnerRelationshipView:
        validate_admin_relationship_type(command.relationship_type)
        validate_admin_relationship_target(
            learner_user_id=learner_user_id,
            admin_user_id=actor.user_id,
        )
        with self._session_factory() as session:
            learner = session.get(LearnerProfileRecord, learner_user_id)
            if learner is None:
                raise domain_error(
                    "Learner relationship target was not found",
                    code="SS-DOMAIN-030",
                    status_code=404,
                    details={"learner_id": learner_user_id},
                )
            now = _utcnow()
            record = session.get(
                AdminLearnerRelationshipRecord,
                {"learner_user_id": learner_user_id, "admin_user_id": actor.user_id},
            )
            if record is None:
                record = AdminLearnerRelationshipRecord(
                    learner_user_id=learner_user_id,
                    admin_user_id=actor.user_id,
                    relationship_type=command.relationship_type,
                    created_at=now,
                    updated_at=now,
                )
                session.add(record)
            else:
                record.relationship_type = command.relationship_type
                record.updated_at = now
            session.commit()
            return self._to_view(record)

    def delete_relationship(self, actor: Actor, *, learner_user_id: str) -> None:
        with self._session_factory() as session:
            record = session.get(
                AdminLearnerRelationshipRecord,
                {"learner_user_id": learner_user_id, "admin_user_id": actor.user_id},
            )
            if record is None:
                raise domain_error(
                    "Admin relationship was not found",
                    code="SS-DOMAIN-032",
                    status_code=404,
                    details={"learner_id": learner_user_id, "admin_user_id": actor.user_id},
                )
            session.delete(record)
            session.commit()

    def _to_view(self, record: AdminLearnerRelationshipRecord) -> AdminLearnerRelationshipView:
        return AdminLearnerRelationshipView(
            learner_user_id=record.learner_user_id,
            admin_user_id=record.admin_user_id,
            relationship_type=record.relationship_type,
            created_at=record.created_at.isoformat(),
            updated_at=record.updated_at.isoformat(),
        )
