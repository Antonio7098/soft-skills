"""Organisation application service."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.modules.organisations.contracts.commands import (
    AddMemberCommand,
    CreateOrganisationCommand,
    UpdateMemberCommand,
    UpdateOrganisationCommand,
)
from soft_skills_backend.modules.organisations.contracts.views import (
    OrganisationMemberView,
    OrganisationView,
)
from soft_skills_backend.modules.organisations.domain.validators import (
    require_org_admin,
    require_unique_org_membership,
    validate_membership_role,
    validate_slug_uniqueness,
)
from soft_skills_backend.modules.organisations.infra.organisation_repository import (
    OrganisationRepository,
)
from soft_skills_backend.platform.db.models import (
    OrganisationMembershipRecord,
    OrganisationRecord,
)
from soft_skills_backend.platform.db.repositories import SqlAlchemyWorkflowEventRepository
from soft_skills_backend.shared.auth import Actor
from soft_skills_backend.shared.errors import domain_error


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _generate_id() -> str:
    return uuid.uuid4().hex[:32]


class OrganisationService:
    """Organisation management facade."""

    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        workflow_events: SqlAlchemyWorkflowEventRepository,
    ) -> None:
        self._repo = OrganisationRepository(
            session_factory=session_factory,
            workflow_events=workflow_events,
        )

    def create_organisation(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        command: CreateOrganisationCommand,
    ) -> OrganisationView:
        """Create a new organisation and make the creator the first admin."""
        with self._repo._session_factory() as session:
            validate_slug_uniqueness(session, command.slug)

        org = OrganisationRecord(
            id=_generate_id(),
            name=command.name,
            slug=command.slug,
            created_at=_utcnow(),
            updated_at=_utcnow(),
        )
        created_org = self._repo.create(org)

        membership = OrganisationMembershipRecord(
            organisation_id=created_org.id,
            user_id=actor.user_id,
            role="admin",
            joined_at=_utcnow(),
        )
        self._repo.add_member(membership)

        return OrganisationView(
            id=created_org.id,
            name=created_org.name,
            slug=created_org.slug,
            created_at=created_org.created_at.isoformat(),
            updated_at=created_org.updated_at.isoformat(),
        )

    def get_organisation(
        self,
        actor: Actor,
        organisation_id: str,
    ) -> OrganisationView:
        """Get organisation details."""
        org = self._repo.get_by_id(organisation_id)
        if org is None:
            raise domain_error(
                "Organisation not found",
                code="SS-ORG-001",
                status_code=404,
                details={"organisation_id": organisation_id},
            )
        return OrganisationView(
            id=org.id,
            name=org.name,
            slug=org.slug,
            created_at=org.created_at.isoformat(),
            updated_at=org.updated_at.isoformat(),
        )

    def update_organisation(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        organisation_id: str,
        command: UpdateOrganisationCommand,
    ) -> OrganisationView:
        """Update organisation details."""
        require_org_admin(actor, organisation_id)

        org = self._repo.get_by_id(organisation_id)
        if org is None:
            raise domain_error(
                "Organisation not found",
                code="SS-ORG-001",
                status_code=404,
                details={"organisation_id": organisation_id},
            )

        if command.name is not None:
            org.name = command.name
        if command.slug is not None:
            with self._repo._session_factory() as session:
                validate_slug_uniqueness(session, command.slug, exclude_org_id=organisation_id)
            org.slug = command.slug

        org.updated_at = _utcnow()
        updated_org = self._repo.update(org)

        return OrganisationView(
            id=updated_org.id,
            name=updated_org.name,
            slug=updated_org.slug,
            created_at=updated_org.created_at.isoformat(),
            updated_at=updated_org.updated_at.isoformat(),
        )

    def list_members(
        self,
        actor: Actor,
        organisation_id: str,
    ) -> list[OrganisationMemberView]:
        """List organisation members."""
        require_org_admin(actor, organisation_id)

        org = self._repo.get_by_id(organisation_id)
        if org is None:
            raise domain_error(
                "Organisation not found",
                code="SS-ORG-001",
                status_code=404,
                details={"organisation_id": organisation_id},
            )

        memberships = self._repo.list_members(organisation_id)
        return [
            OrganisationMemberView(
                organisation_id=m.organisation_id,
                user_id=m.user_id,
                role=m.role,
                joined_at=m.joined_at.isoformat(),
            )
            for m in memberships
        ]

    def add_member(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        organisation_id: str,
        command: AddMemberCommand,
    ) -> OrganisationMemberView:
        """Add a member to an organisation."""
        require_org_admin(actor, organisation_id)

        org = self._repo.get_by_id(organisation_id)
        if org is None:
            raise domain_error(
                "Organisation not found",
                code="SS-ORG-001",
                status_code=404,
                details={"organisation_id": organisation_id},
            )

        with self._repo._session_factory() as session:
            require_unique_org_membership(session, organisation_id, command.user_id)
        validate_membership_role(command.role)

        membership = OrganisationMembershipRecord(
            organisation_id=organisation_id,
            user_id=command.user_id,
            role=command.role,
            joined_at=_utcnow(),
        )
        created = self._repo.add_member(membership)

        return OrganisationMemberView(
            organisation_id=created.organisation_id,
            user_id=created.user_id,
            role=created.role,
            joined_at=created.joined_at.isoformat(),
        )

    def update_member(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        organisation_id: str,
        user_id: str,
        command: UpdateMemberCommand,
    ) -> OrganisationMemberView:
        """Update a member's role."""
        require_org_admin(actor, organisation_id)

        membership = self._repo.get_member(organisation_id, user_id)
        if membership is None:
            raise domain_error(
                "Organisation member not found",
                code="SS-ORG-002",
                status_code=404,
                details={"organisation_id": organisation_id, "user_id": user_id},
            )

        validate_membership_role(command.role)
        membership.role = command.role
        updated = self._repo.update_member(membership)

        return OrganisationMemberView(
            organisation_id=updated.organisation_id,
            user_id=updated.user_id,
            role=updated.role,
            joined_at=updated.joined_at.isoformat(),
        )

    def remove_member(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        organisation_id: str,
        user_id: str,
    ) -> None:
        """Remove a member from an organisation."""
        require_org_admin(actor, organisation_id)

        membership = self._repo.get_member(organisation_id, user_id)
        if membership is None:
            raise domain_error(
                "Organisation member not found",
                code="SS-ORG-002",
                status_code=404,
                details={"organisation_id": organisation_id, "user_id": user_id},
            )

        if membership.role == "admin":
            admin_count = sum(
                1
                for m in self._repo.list_members(organisation_id)
                if m.role == "admin" and m.user_id != user_id
            )
            if admin_count == 0:
                raise domain_error(
                    "Cannot remove the last admin from an organisation",
                    code="SS-DOMAIN-027",
                    details={"organisation_id": organisation_id},
                )

        self._repo.remove_member(organisation_id, user_id)
