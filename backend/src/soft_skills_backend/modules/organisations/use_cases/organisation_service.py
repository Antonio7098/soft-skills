"""Organisation application service."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import cast

from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.modules.catalog.contracts.prompt_item_commands import (
    PromptItemCreateCommand,
    PromptItemUpdateCommand,
)
from soft_skills_backend.modules.catalog.contracts.prompt_item_views import PromptItemView
from soft_skills_backend.modules.catalog.contracts.scenario_commands import (
    ScenarioCreateCommand,
    ScenarioUpdateCommand,
)
from soft_skills_backend.modules.catalog.contracts.scenario_views import ScenarioView
from soft_skills_backend.modules.catalog.domain.validators import (
    validate_prompt_command,
    validate_scenario_command,
)
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
    OrganisationListView,
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
    PromptItemRecord,
    RubricRecord,
    ScenarioRecord,
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

    def list_organisations_for_user(self, actor: Actor) -> list[OrganisationListView]:
        """List all organisations the user belongs to."""
        with self._repo._session_factory() as session:
            memberships = (
                session.query(OrganisationMembershipRecord).filter_by(user_id=actor.user_id).all()
            )
            orgs = []
            for m in memberships:
                org = session.get(OrganisationRecord, m.organisation_id)
                if org:
                    member_count = (
                        session.query(OrganisationMembershipRecord)
                        .filter_by(organisation_id=org.id)
                        .count()
                    )
                    orgs.append(
                        OrganisationListView(
                            id=org.id,
                            name=org.name,
                            slug=org.slug,
                            member_count=member_count,
                        )
                    )
            return orgs

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
            id=command.rubric_id,
            skill_slug=command.skill_slug,
            content_type=command.content_type,
            schema_version=command.schema_version,
            name=command.name,
            description=command.description,
            organisation_id=organisation_id,
        )
        created = self._repo.create_rubric(rubric)

        return OrgRubricView(
            rubric_id=created.id,
            skill_slug=created.skill_slug,
            content_type=created.content_type,
            schema_version=created.schema_version,
            name=created.name,
            description=created.description,
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
            rubric_id=rubric.id,
            skill_slug=rubric.skill_slug,
            content_type=rubric.content_type,
            schema_version=rubric.schema_version,
            name=rubric.name,
            description=rubric.description,
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
                rubric_id=r.id,
                skill_slug=r.skill_slug,
                content_type=r.content_type,
                schema_version=r.schema_version,
                name=r.name,
                description=r.description,
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
        if command.description is not None:
            rubric.description = command.description

        updated = self._repo.update_rubric(rubric)

        return OrgRubricView(
            rubric_id=updated.id,
            skill_slug=updated.skill_slug,
            content_type=updated.content_type,
            schema_version=updated.schema_version,
            name=updated.name,
            description=updated.description,
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

    def create_org_prompt_item(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        organisation_id: str,
        command: PromptItemCreateCommand,
    ) -> PromptItemView:
        """Create an org-specific standalone prompt item."""
        require_org_admin(actor, organisation_id)

        with self._repo._session_factory() as session:
            validate_prompt_command(session, None, command)

        prompt_item = PromptItemRecord(
            id=_generate_id(),
            collection_id=None,
            author_user_id=actor.user_id,
            organisation_id=organisation_id,
            prompt_type=command.prompt_type,
            title=command.title,
            prompt_text=command.prompt_text,
            difficulty=command.difficulty,
            lifecycle_state="draft",
            target_skill_slugs=list(command.target_skill_slugs),
            rubric_id=command.rubric_id,
            created_at=_utcnow(),
            updated_at=_utcnow(),
        )
        created = self._repo.create_prompt_item(prompt_item)

        return PromptItemView(
            id=created.id,
            prompt_type=created.prompt_type,
            title=created.title,
            prompt_text=created.prompt_text,
            difficulty=created.difficulty,
            lifecycle_state=created.lifecycle_state,
            target_skill_slugs=created.target_skill_slugs,
            rubric_id=created.rubric_id,
            organisation_id=organisation_id,
        )

    def get_org_prompt_item(
        self,
        actor: Actor,
        organisation_id: str,
        prompt_item_id: str,
    ) -> PromptItemView:
        """Get an org-specific standalone prompt item."""
        require_org_admin(actor, organisation_id)

        prompt_item = self._repo.get_prompt_item(organisation_id, prompt_item_id)
        if prompt_item is None:
            raise domain_error(
                "Org prompt item not found",
                code="SS-ORG-006",
                status_code=404,
                details={"organisation_id": organisation_id, "prompt_item_id": prompt_item_id},
            )

        return PromptItemView(
            id=prompt_item.id,
            prompt_type=prompt_item.prompt_type,
            title=prompt_item.title,
            prompt_text=prompt_item.prompt_text,
            difficulty=prompt_item.difficulty,
            lifecycle_state=prompt_item.lifecycle_state,
            target_skill_slugs=prompt_item.target_skill_slugs,
            rubric_id=prompt_item.rubric_id,
            organisation_id=cast(str, prompt_item.organisation_id),
        )

    def list_org_prompt_items(
        self,
        actor: Actor,
        organisation_id: str,
    ) -> list[PromptItemView]:
        """List org-specific standalone prompt items."""
        require_org_admin(actor, organisation_id)

        prompt_items = self._repo.list_prompt_items(organisation_id)
        return [
            PromptItemView(
                id=p.id,
                prompt_type=p.prompt_type,
                title=p.title,
                prompt_text=p.prompt_text,
                difficulty=p.difficulty,
                lifecycle_state=p.lifecycle_state,
                target_skill_slugs=p.target_skill_slugs,
                rubric_id=p.rubric_id,
                organisation_id=cast(str, p.organisation_id),
            )
            for p in prompt_items
        ]

    def update_org_prompt_item(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        organisation_id: str,
        prompt_item_id: str,
        command: PromptItemUpdateCommand,
    ) -> PromptItemView:
        """Update an org-specific standalone prompt item."""
        require_org_admin(actor, organisation_id)

        prompt_item = self._repo.get_prompt_item(organisation_id, prompt_item_id)
        if prompt_item is None:
            raise domain_error(
                "Org prompt item not found",
                code="SS-ORG-006",
                status_code=404,
                details={"organisation_id": organisation_id, "prompt_item_id": prompt_item_id},
            )

        with self._repo._session_factory() as session:
            validate_prompt_command(session, None, command)

        if command.prompt_type is not None:
            prompt_item.prompt_type = command.prompt_type
        if command.title is not None:
            prompt_item.title = command.title
        if command.prompt_text is not None:
            prompt_item.prompt_text = command.prompt_text
        if command.difficulty is not None:
            prompt_item.difficulty = command.difficulty
        if command.target_skill_slugs is not None:
            prompt_item.target_skill_slugs = list(command.target_skill_slugs)
        if command.rubric_id is not None:
            prompt_item.rubric_id = command.rubric_id
        prompt_item.updated_at = _utcnow()

        updated = self._repo.update_prompt_item(prompt_item)

        return PromptItemView(
            id=updated.id,
            prompt_type=updated.prompt_type,
            title=updated.title,
            prompt_text=updated.prompt_text,
            difficulty=updated.difficulty,
            lifecycle_state=updated.lifecycle_state,
            target_skill_slugs=updated.target_skill_slugs,
            rubric_id=updated.rubric_id,
            organisation_id=cast(str, updated.organisation_id),
        )

    def delete_org_prompt_item(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        organisation_id: str,
        prompt_item_id: str,
    ) -> None:
        """Delete an org-specific standalone prompt item."""
        require_org_admin(actor, organisation_id)

        prompt_item = self._repo.get_prompt_item(organisation_id, prompt_item_id)
        if prompt_item is None:
            raise domain_error(
                "Org prompt item not found",
                code="SS-ORG-006",
                status_code=404,
                details={"organisation_id": organisation_id, "prompt_item_id": prompt_item_id},
            )

        self._repo.delete_prompt_item(organisation_id, prompt_item_id)

    def create_org_scenario(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        organisation_id: str,
        command: ScenarioCreateCommand,
    ) -> ScenarioView:
        """Create an org-specific standalone scenario."""
        require_org_admin(actor, organisation_id)

        with self._repo._session_factory() as session:
            validate_scenario_command(session, None, command)

        scenario = ScenarioRecord(
            id=_generate_id(),
            collection_id=None,
            author_user_id=actor.user_id,
            organisation_id=organisation_id,
            title=command.title,
            business_context=command.business_context,
            learner_objective=command.learner_objective,
            constraints=list(command.constraints),
            stakeholder_tensions=list(command.stakeholder_tensions),
            questions=list(command.questions),
            lifecycle_state="draft",
            target_skill_slugs=list(command.target_skill_slugs),
            rubric_id=command.rubric_id,
            created_at=_utcnow(),
            updated_at=_utcnow(),
        )
        created = self._repo.create_scenario(scenario)

        return ScenarioView(
            id=created.id,
            title=created.title,
            business_context=created.business_context,
            learner_objective=created.learner_objective,
            constraints=created.constraints,
            stakeholder_tensions=created.stakeholder_tensions,
            questions=list(created.questions),
            lifecycle_state=created.lifecycle_state,
            target_skill_slugs=created.target_skill_slugs,
            rubric_id=created.rubric_id,
            supporting_artifacts=[],
            mock_company=None,
            mock_people=[],
            organisation_id=organisation_id,
        )

    def get_org_scenario(
        self,
        actor: Actor,
        organisation_id: str,
        scenario_id: str,
    ) -> ScenarioView:
        """Get an org-specific standalone scenario."""
        require_org_admin(actor, organisation_id)

        scenario = self._repo.get_scenario(organisation_id, scenario_id)
        if scenario is None:
            raise domain_error(
                "Org scenario not found",
                code="SS-ORG-007",
                status_code=404,
                details={"organisation_id": organisation_id, "scenario_id": scenario_id},
            )

        return ScenarioView(
            id=scenario.id,
            title=scenario.title,
            business_context=scenario.business_context,
            learner_objective=scenario.learner_objective,
            constraints=scenario.constraints,
            stakeholder_tensions=scenario.stakeholder_tensions,
            questions=list(scenario.questions),
            lifecycle_state=scenario.lifecycle_state,
            target_skill_slugs=scenario.target_skill_slugs,
            rubric_id=scenario.rubric_id,
            supporting_artifacts=[],
            mock_company=None,
            mock_people=[],
            organisation_id=cast(str, scenario.organisation_id),
        )

    def list_org_scenarios(
        self,
        actor: Actor,
        organisation_id: str,
    ) -> list[ScenarioView]:
        """List org-specific standalone scenarios."""
        require_org_admin(actor, organisation_id)

        scenarios = self._repo.list_scenarios(organisation_id)
        return [
            ScenarioView(
                id=s.id,
                title=s.title,
                business_context=s.business_context,
                learner_objective=s.learner_objective,
                constraints=s.constraints,
                stakeholder_tensions=s.stakeholder_tensions,
                questions=list(s.questions),
                lifecycle_state=s.lifecycle_state,
                target_skill_slugs=s.target_skill_slugs,
                rubric_id=s.rubric_id,
                supporting_artifacts=[],
                mock_company=None,
                mock_people=[],
                organisation_id=cast(str, s.organisation_id),
            )
            for s in scenarios
        ]

    def update_org_scenario(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        organisation_id: str,
        scenario_id: str,
        command: ScenarioUpdateCommand,
    ) -> ScenarioView:
        """Update an org-specific standalone scenario."""
        require_org_admin(actor, organisation_id)

        scenario = self._repo.get_scenario(organisation_id, scenario_id)
        if scenario is None:
            raise domain_error(
                "Org scenario not found",
                code="SS-ORG-007",
                status_code=404,
                details={"organisation_id": organisation_id, "scenario_id": scenario_id},
            )

        with self._repo._session_factory() as session:
            validate_scenario_command(session, None, command)

        if command.title is not None:
            scenario.title = command.title
        if command.business_context is not None:
            scenario.business_context = command.business_context
        if command.learner_objective is not None:
            scenario.learner_objective = command.learner_objective
        if command.constraints is not None:
            scenario.constraints = list(command.constraints)
        if command.stakeholder_tensions is not None:
            scenario.stakeholder_tensions = list(command.stakeholder_tensions)
        if command.target_skill_slugs is not None:
            scenario.target_skill_slugs = list(command.target_skill_slugs)
        if command.questions is not None:
            scenario.questions = list(command.questions)
        if command.rubric_id is not None:
            scenario.rubric_id = command.rubric_id
        scenario.updated_at = _utcnow()

        updated = self._repo.update_scenario(scenario)

        return ScenarioView(
            id=updated.id,
            title=updated.title,
            business_context=updated.business_context,
            learner_objective=updated.learner_objective,
            constraints=updated.constraints,
            stakeholder_tensions=updated.stakeholder_tensions,
            questions=list(updated.questions),
            lifecycle_state=updated.lifecycle_state,
            target_skill_slugs=updated.target_skill_slugs,
            rubric_id=updated.rubric_id,
            supporting_artifacts=[],
            mock_company=None,
            mock_people=[],
            organisation_id=cast(str, updated.organisation_id),
        )

    def delete_org_scenario(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        organisation_id: str,
        scenario_id: str,
    ) -> None:
        """Delete an org-specific standalone scenario."""
        require_org_admin(actor, organisation_id)

        scenario = self._repo.get_scenario(organisation_id, scenario_id)
        if scenario is None:
            raise domain_error(
                "Org scenario not found",
                code="SS-ORG-007",
                status_code=404,
                details={"organisation_id": organisation_id, "scenario_id": scenario_id},
            )

        self._repo.delete_scenario(organisation_id, scenario_id)
