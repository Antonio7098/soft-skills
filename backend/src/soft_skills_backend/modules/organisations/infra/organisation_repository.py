"""Organisation persistence."""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.platform.db.models import (
    OrganisationMembershipRecord,
    OrganisationRecord,
)
from soft_skills_backend.platform.db.repositories import SqlAlchemyWorkflowEventRepository


class OrganisationRepository:
    """Organisation persistence operations."""

    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        workflow_events: SqlAlchemyWorkflowEventRepository,
    ) -> None:
        self._session_factory = session_factory
        self._workflow_events = workflow_events

    def create(self, org: OrganisationRecord) -> OrganisationRecord:
        """Persist a new organisation."""
        with self._session_factory() as session:
            session.add(org)
            session.commit()
            session.refresh(org)
            return org

    def get_by_id(self, org_id: str) -> OrganisationRecord | None:
        """Fetch organisation by ID."""
        with self._session_factory() as session:
            return session.get(OrganisationRecord, org_id)

    def get_by_slug(self, slug: str) -> OrganisationRecord | None:
        """Fetch organisation by slug."""
        with self._session_factory() as session:
            return session.query(OrganisationRecord).filter(OrganisationRecord.slug == slug).first()

    def update(self, org: OrganisationRecord) -> OrganisationRecord:
        """Update an existing organisation."""
        with self._session_factory() as session:
            session.add(org)
            session.commit()
            session.refresh(org)
            return org

    def add_member(self, membership: OrganisationMembershipRecord) -> OrganisationMembershipRecord:
        """Add a member to an organisation."""
        with self._session_factory() as session:
            session.add(membership)
            session.commit()
            session.refresh(membership)
            return membership

    def get_member(self, organisation_id: str, user_id: str) -> OrganisationMembershipRecord | None:
        """Get a specific membership record."""
        with self._session_factory() as session:
            return (
                session.query(OrganisationMembershipRecord)
                .filter(
                    OrganisationMembershipRecord.organisation_id == organisation_id,
                    OrganisationMembershipRecord.user_id == user_id,
                )
                .first()
            )

    def list_members(self, organisation_id: str) -> list[OrganisationMembershipRecord]:
        """List all members of an organisation."""
        with self._session_factory() as session:
            return (
                session.query(OrganisationMembershipRecord)
                .filter(OrganisationMembershipRecord.organisation_id == organisation_id)
                .all()
            )

    def update_member(
        self, membership: OrganisationMembershipRecord
    ) -> OrganisationMembershipRecord:
        """Update a membership record."""
        with self._session_factory() as session:
            session.add(membership)
            session.commit()
            session.refresh(membership)
            return membership

    def remove_member(self, organisation_id: str, user_id: str) -> None:
        """Remove a member from an organisation."""
        with self._session_factory() as session:
            session.query(OrganisationMembershipRecord).filter(
                OrganisationMembershipRecord.organisation_id == organisation_id,
                OrganisationMembershipRecord.user_id == user_id,
            ).delete()
            session.commit()

    def count_members(self, organisation_id: str) -> int:
        """Count members in an organisation."""
        with self._session_factory() as session:
            return (
                session.query(OrganisationMembershipRecord)
                .filter(OrganisationMembershipRecord.organisation_id == organisation_id)
                .count()
            )
