"""Organisation application service."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import cast

from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.modules.organisations.contracts.commands import (
    AddMemberCommand,
    CreateOrganisationCommand,
    CreateOrgCompetencyCommand,
    CreateOrgRubricCommand,
    CreateOrgSkillCommand,
    UpdateMemberCommand,
    UpdateOrganisationCommand,
    UpdateOrgCompetencyCommand,
    UpdateOrgRubricCommand,
    UpdateOrgSkillCommand,
)
from soft_skills_backend.modules.organisations.contracts.views import (
    OrganisationMemberView,
    OrganisationView,
    OrgCompetencyView,
    OrgRubricView,
    OrgSkillView,
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
    CompetencyRecord,
    OrganisationMembershipRecord,
    OrganisationRecord,
    OrganisationSkillMapRecord,
    RubricRecord,
    SkillRecord,
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

    def create_org_skill(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        organisation_id: str,
        command: CreateOrgSkillCommand,
    ) -> OrgSkillView:
        """Create an org-specific skill."""
        require_org_admin(actor, organisation_id)

        skill = SkillRecord(
            slug=command.slug,
            name=command.name,
            description=command.description,
            organisation_id=organisation_id,
        )
        created = self._repo.create_skill(skill)

        return OrgSkillView(
            slug=created.slug,
            name=created.name,
            description=created.description,
            organisation_id=cast(str, created.organisation_id),
        )

    def get_org_skill(
        self,
        actor: Actor,
        organisation_id: str,
        skill_slug: str,
    ) -> OrgSkillView:
        """Get an org-specific skill."""
        require_org_admin(actor, organisation_id)

        skill = self._repo.get_skill(organisation_id, skill_slug)
        if skill is None:
            raise domain_error(
                "Org skill not found",
                code="SS-ORG-003",
                status_code=404,
                details={"organisation_id": organisation_id, "skill_slug": skill_slug},
            )

        return OrgSkillView(
            slug=skill.slug,
            name=skill.name,
            description=skill.description,
            organisation_id=cast(str, skill.organisation_id),
        )

    def list_org_skills(
        self,
        actor: Actor,
        organisation_id: str,
    ) -> list[OrgSkillView]:
        """List org-specific skills."""
        require_org_admin(actor, organisation_id)

        skills = self._repo.list_skills(organisation_id)
        return [
            OrgSkillView(
                slug=s.slug,
                name=s.name,
                description=s.description,
                organisation_id=cast(str, s.organisation_id),
            )
            for s in skills
        ]

    def update_org_skill(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        organisation_id: str,
        skill_slug: str,
        command: UpdateOrgSkillCommand,
    ) -> OrgSkillView:
        """Update an org-specific skill."""
        require_org_admin(actor, organisation_id)

        skill = self._repo.get_skill(organisation_id, skill_slug)
        if skill is None:
            raise domain_error(
                "Org skill not found",
                code="SS-ORG-003",
                status_code=404,
                details={"organisation_id": organisation_id, "skill_slug": skill_slug},
            )

        if command.name is not None:
            skill.name = command.name
        if command.description is not None:
            skill.description = command.description

        updated = self._repo.update_skill(skill)

        return OrgSkillView(
            slug=updated.slug,
            name=updated.name,
            description=updated.description,
            organisation_id=cast(str, updated.organisation_id),
        )

    def delete_org_skill(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        organisation_id: str,
        skill_slug: str,
    ) -> None:
        """Delete an org-specific skill."""
        require_org_admin(actor, organisation_id)

        skill = self._repo.get_skill(organisation_id, skill_slug)
        if skill is None:
            raise domain_error(
                "Org skill not found",
                code="SS-ORG-003",
                status_code=404,
                details={"organisation_id": organisation_id, "skill_slug": skill_slug},
            )

        self._repo.delete_skill(organisation_id, skill_slug)

    def create_org_competency(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        organisation_id: str,
        command: CreateOrgCompetencyCommand,
    ) -> OrgCompetencyView:
        """Create an org-specific competency."""
        require_org_admin(actor, organisation_id)

        competency = CompetencyRecord(
            slug=command.slug,
            name=command.name,
            description=command.description,
            organisation_id=organisation_id,
        )
        created = self._repo.create_competency(competency)

        for skill_slug in command.skill_slugs:
            mapping = OrganisationSkillMapRecord(
                organisation_id=organisation_id,
                competency_slug=command.slug,
                skill_slug=skill_slug,
                weight=1.0,
            )
            self._repo.upsert_org_skill_map(mapping)

        return OrgCompetencyView(
            slug=created.slug,
            name=created.name,
            description=created.description,
            skill_slugs=command.skill_slugs,
            organisation_id=cast(str, created.organisation_id),
        )

    def get_org_competency(
        self,
        actor: Actor,
        organisation_id: str,
        competency_slug: str,
    ) -> OrgCompetencyView:
        """Get an org-specific competency."""
        require_org_admin(actor, organisation_id)

        competency = self._repo.get_competency(organisation_id, competency_slug)
        if competency is None:
            raise domain_error(
                "Org competency not found",
                code="SS-ORG-004",
                status_code=404,
                details={"organisation_id": organisation_id, "competency_slug": competency_slug},
            )

        org_maps = self._repo.get_org_skill_maps(organisation_id)
        skill_slugs = [m.skill_slug for m in org_maps if m.competency_slug == competency_slug]

        return OrgCompetencyView(
            slug=competency.slug,
            name=competency.name,
            description=competency.description,
            skill_slugs=skill_slugs,
            organisation_id=cast(str, competency.organisation_id),
        )

    def list_org_competencies(
        self,
        actor: Actor,
        organisation_id: str,
    ) -> list[OrgCompetencyView]:
        """List org-specific competencies."""
        require_org_admin(actor, organisation_id)

        competencies = self._repo.list_competencies(organisation_id)
        org_maps = self._repo.get_org_skill_maps(organisation_id)
        skill_maps_by_comp: dict[str, list[str]] = {}
        for m in org_maps:
            skill_maps_by_comp.setdefault(m.competency_slug, []).append(m.skill_slug)

        return [
            OrgCompetencyView(
                slug=c.slug,
                name=c.name,
                description=c.description,
                skill_slugs=skill_maps_by_comp.get(c.slug, []),
                organisation_id=cast(str, c.organisation_id),
            )
            for c in competencies
        ]

    def update_org_competency(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        organisation_id: str,
        competency_slug: str,
        command: UpdateOrgCompetencyCommand,
    ) -> OrgCompetencyView:
        """Update an org-specific competency."""
        require_org_admin(actor, organisation_id)

        competency = self._repo.get_competency(organisation_id, competency_slug)
        if competency is None:
            raise domain_error(
                "Org competency not found",
                code="SS-ORG-004",
                status_code=404,
                details={"organisation_id": organisation_id, "competency_slug": competency_slug},
            )

        if command.name is not None:
            competency.name = command.name
        if command.description is not None:
            competency.description = command.description

        if command.skill_slugs is not None:
            self._repo.delete_org_skill_maps_for_competency(organisation_id, competency_slug)
            for skill_slug in command.skill_slugs:
                mapping = OrganisationSkillMapRecord(
                    organisation_id=organisation_id,
                    competency_slug=competency_slug,
                    skill_slug=skill_slug,
                    weight=1.0,
                )
                self._repo.upsert_org_skill_map(mapping)

        updated = self._repo.update_competency(competency)

        org_maps = self._repo.get_org_skill_maps(organisation_id)
        skill_slugs = [m.skill_slug for m in org_maps if m.competency_slug == competency_slug]

        return OrgCompetencyView(
            slug=updated.slug,
            name=updated.name,
            description=updated.description,
            skill_slugs=skill_slugs,
            organisation_id=cast(str, updated.organisation_id),
        )

    def delete_org_competency(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        organisation_id: str,
        competency_slug: str,
    ) -> None:
        """Delete an org-specific competency."""
        require_org_admin(actor, organisation_id)

        competency = self._repo.get_competency(organisation_id, competency_slug)
        if competency is None:
            raise domain_error(
                "Org competency not found",
                code="SS-ORG-004",
                status_code=404,
                details={"organisation_id": organisation_id, "competency_slug": competency_slug},
            )

        self._repo.delete_org_skill_maps_for_competency(organisation_id, competency_slug)
        self._repo.delete_competency(organisation_id, competency_slug)

    def create_org_rubric(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        organisation_id: str,
        command: CreateOrgRubricCommand,
    ) -> OrgRubricView:
        """Create an org-specific rubric."""
        require_org_admin(actor, organisation_id)

        rubric = RubricRecord(
            rubric_id=command.rubric_id,
            family=command.family,
            version=command.version,
            content_type=command.content_type,
            schema_version=command.schema_version,
            name=command.name,
            criteria=command.criteria,
            organisation_id=organisation_id,
        )
        created = self._repo.create_rubric(rubric)

        return OrgRubricView(
            rubric_id=created.rubric_id,
            family=created.family,
            version=created.version,
            content_type=created.content_type,
            schema_version=created.schema_version,
            name=created.name,
            criteria=created.criteria,
            organisation_id=cast(str, created.organisation_id),
        )

    def get_org_rubric(
        self,
        actor: Actor,
        organisation_id: str,
        rubric_id: str,
    ) -> OrgRubricView:
        """Get an org-specific rubric."""
        require_org_admin(actor, organisation_id)

        rubric = self._repo.get_rubric(organisation_id, rubric_id)
        if rubric is None:
            raise domain_error(
                "Org rubric not found",
                code="SS-ORG-005",
                status_code=404,
                details={"organisation_id": organisation_id, "rubric_id": rubric_id},
            )

        return OrgRubricView(
            rubric_id=rubric.rubric_id,
            family=rubric.family,
            version=rubric.version,
            content_type=rubric.content_type,
            schema_version=rubric.schema_version,
            name=rubric.name,
            criteria=rubric.criteria,
            organisation_id=cast(str, rubric.organisation_id),
        )

    def list_org_rubrics(
        self,
        actor: Actor,
        organisation_id: str,
    ) -> list[OrgRubricView]:
        """List org-specific rubrics."""
        require_org_admin(actor, organisation_id)

        rubrics = self._repo.list_rubrics(organisation_id)
        return [
            OrgRubricView(
                rubric_id=r.rubric_id,
                family=r.family,
                version=r.version,
                content_type=r.content_type,
                schema_version=r.schema_version,
                name=r.name,
                criteria=r.criteria,
                organisation_id=cast(str, r.organisation_id),
            )
            for r in rubrics
        ]

    def update_org_rubric(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        organisation_id: str,
        rubric_id: str,
        command: UpdateOrgRubricCommand,
    ) -> OrgRubricView:
        """Update an org-specific rubric."""
        require_org_admin(actor, organisation_id)

        rubric = self._repo.get_rubric(organisation_id, rubric_id)
        if rubric is None:
            raise domain_error(
                "Org rubric not found",
                code="SS-ORG-005",
                status_code=404,
                details={"organisation_id": organisation_id, "rubric_id": rubric_id},
            )

        if command.name is not None:
            rubric.name = command.name
        if command.criteria is not None:
            rubric.criteria = command.criteria

        updated = self._repo.update_rubric(rubric)

        return OrgRubricView(
            rubric_id=updated.rubric_id,
            family=updated.family,
            version=updated.version,
            content_type=updated.content_type,
            schema_version=updated.schema_version,
            name=updated.name,
            criteria=updated.criteria,
            organisation_id=cast(str, updated.organisation_id),
        )

    def delete_org_rubric(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        organisation_id: str,
        rubric_id: str,
    ) -> None:
        """Delete an org-specific rubric."""
        require_org_admin(actor, organisation_id)

        rubric = self._repo.get_rubric(organisation_id, rubric_id)
        if rubric is None:
            raise domain_error(
                "Org rubric not found",
                code="SS-ORG-005",
                status_code=404,
                details={"organisation_id": organisation_id, "rubric_id": rubric_id},
            )

        self._repo.delete_rubric(organisation_id, rubric_id)
