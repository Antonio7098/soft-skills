"""Organisation persistence."""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

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
from soft_skills_backend.shared.errors import domain_error


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

    def create_skill(self, skill: SkillRecord) -> SkillRecord:
        """Persist a new org-specific skill."""
        with self._session_factory() as session:
            existing = (
                session.query(SkillRecord)
                .filter(
                    SkillRecord.organisation_id == skill.organisation_id,
                    SkillRecord.slug == skill.slug,
                )
                .first()
            )
            if existing is not None:
                raise domain_error(
                    "Skill already exists",
                    code="SS-ORG-001",
                    status_code=409,
                    details={"slug": skill.slug, "organisation_id": skill.organisation_id},
                )
            session.add(skill)
            session.commit()
            session.refresh(skill)
            return skill

    def get_skill(self, organisation_id: str, slug: str) -> SkillRecord | None:
        """Fetch an org-specific skill by slug."""
        with self._session_factory() as session:
            return (
                session.query(SkillRecord)
                .filter(
                    SkillRecord.organisation_id == organisation_id,
                    SkillRecord.slug == slug,
                )
                .first()
            )

    def list_skills(self, organisation_id: str) -> list[SkillRecord]:
        """List all skills for an organisation."""
        with self._session_factory() as session:
            return (
                session.query(SkillRecord)
                .filter(SkillRecord.organisation_id == organisation_id)
                .order_by(SkillRecord.name)
                .all()
            )

    def update_skill(self, skill: SkillRecord) -> SkillRecord:
        """Update an org-specific skill."""
        with self._session_factory() as session:
            session.add(skill)
            session.commit()
            session.refresh(skill)
            return skill

    def delete_skill(self, organisation_id: str, slug: str) -> None:
        """Delete an org-specific skill."""
        with self._session_factory() as session:
            session.query(SkillRecord).filter(
                SkillRecord.organisation_id == organisation_id,
                SkillRecord.slug == slug,
            ).delete()
            session.commit()

    def create_competency(self, competency: CompetencyRecord) -> CompetencyRecord:
        """Persist a new org-specific competency."""
        with self._session_factory() as session:
            existing = (
                session.query(CompetencyRecord)
                .filter(
                    CompetencyRecord.organisation_id == competency.organisation_id,
                    CompetencyRecord.slug == competency.slug,
                )
                .first()
            )
            if existing is not None:
                raise domain_error(
                    "Competency already exists",
                    code="SS-ORG-002",
                    status_code=409,
                    details={
                        "slug": competency.slug,
                        "organisation_id": competency.organisation_id,
                    },
                )
            session.add(competency)
            session.commit()
            session.refresh(competency)
            return competency

    def get_competency(self, organisation_id: str, slug: str) -> CompetencyRecord | None:
        """Fetch an org-specific competency by slug."""
        with self._session_factory() as session:
            return (
                session.query(CompetencyRecord)
                .filter(
                    CompetencyRecord.organisation_id == organisation_id,
                    CompetencyRecord.slug == slug,
                )
                .first()
            )

    def list_competencies(self, organisation_id: str) -> list[CompetencyRecord]:
        """List all competencies for an organisation."""
        with self._session_factory() as session:
            return (
                session.query(CompetencyRecord)
                .filter(CompetencyRecord.organisation_id == organisation_id)
                .order_by(CompetencyRecord.name)
                .all()
            )

    def update_competency(self, competency: CompetencyRecord) -> CompetencyRecord:
        """Update an org-specific competency."""
        with self._session_factory() as session:
            session.add(competency)
            session.commit()
            session.refresh(competency)
            return competency

    def delete_competency(self, organisation_id: str, slug: str) -> None:
        """Delete an org-specific competency."""
        with self._session_factory() as session:
            session.query(CompetencyRecord).filter(
                CompetencyRecord.organisation_id == organisation_id,
                CompetencyRecord.slug == slug,
            ).delete()
            session.commit()

    def get_org_skill_maps(self, organisation_id: str) -> list[OrganisationSkillMapRecord]:
        """Get org competency-skill mappings."""
        with self._session_factory() as session:
            return (
                session.query(OrganisationSkillMapRecord)
                .filter(OrganisationSkillMapRecord.organisation_id == organisation_id)
                .all()
            )

    def upsert_org_skill_map(
        self, mapping: OrganisationSkillMapRecord
    ) -> OrganisationSkillMapRecord:
        """Insert or update an org skill map."""
        with self._session_factory() as session:
            existing = (
                session.query(OrganisationSkillMapRecord)
                .filter(
                    OrganisationSkillMapRecord.organisation_id == mapping.organisation_id,
                    OrganisationSkillMapRecord.competency_slug == mapping.competency_slug,
                    OrganisationSkillMapRecord.skill_slug == mapping.skill_slug,
                )
                .first()
            )
            if existing:
                existing.weight = mapping.weight
                session.add(existing)
                session.commit()
                session.refresh(existing)
                return existing
            else:
                session.add(mapping)
                session.commit()
                session.refresh(mapping)
                return mapping

    def delete_org_skill_maps_for_competency(
        self, organisation_id: str, competency_slug: str
    ) -> None:
        """Delete all org skill maps for a competency."""
        with self._session_factory() as session:
            session.query(OrganisationSkillMapRecord).filter(
                OrganisationSkillMapRecord.organisation_id == organisation_id,
                OrganisationSkillMapRecord.competency_slug == competency_slug,
            ).delete()
            session.commit()

    def create_rubric(self, rubric: RubricRecord) -> RubricRecord:
        """Persist a new org-specific rubric."""
        with self._session_factory() as session:
            existing = (
                session.query(RubricRecord)
                .filter(
                    RubricRecord.organisation_id == rubric.organisation_id,
                    RubricRecord.rubric_id == rubric.rubric_id,
                )
                .first()
            )
            if existing is not None:
                raise domain_error(
                    "Rubric already exists",
                    code="SS-ORG-003",
                    status_code=409,
                    details={
                        "rubric_id": rubric.rubric_id,
                        "organisation_id": rubric.organisation_id,
                    },
                )
            session.add(rubric)
            session.commit()
            session.refresh(rubric)
            return rubric

    def get_rubric(self, organisation_id: str, rubric_id: str) -> RubricRecord | None:
        """Fetch an org-specific rubric by rubric_id."""
        with self._session_factory() as session:
            return (
                session.query(RubricRecord)
                .filter(
                    RubricRecord.organisation_id == organisation_id,
                    RubricRecord.rubric_id == rubric_id,
                )
                .first()
            )

    def list_rubrics(self, organisation_id: str) -> list[RubricRecord]:
        """List all rubrics for an organisation."""
        with self._session_factory() as session:
            return (
                session.query(RubricRecord)
                .filter(RubricRecord.organisation_id == organisation_id)
                .order_by(RubricRecord.rubric_id)
                .all()
            )

    def update_rubric(self, rubric: RubricRecord) -> RubricRecord:
        """Update an org-specific rubric."""
        with self._session_factory() as session:
            session.add(rubric)
            session.commit()
            session.refresh(rubric)
            return rubric

    def delete_rubric(self, organisation_id: str, rubric_id: str) -> None:
        """Delete an org-specific rubric."""
        with self._session_factory() as session:
            session.query(RubricRecord).filter(
                RubricRecord.organisation_id == organisation_id,
                RubricRecord.rubric_id == rubric_id,
            ).delete()
            session.commit()

    def create_prompt_item(self, prompt_item: PromptItemRecord) -> PromptItemRecord:
        """Persist a new org-specific prompt item."""
        with self._session_factory() as session:
            session.add(prompt_item)
            session.commit()
            session.refresh(prompt_item)
            return prompt_item

    def get_prompt_item(self, organisation_id: str, prompt_item_id: str) -> PromptItemRecord | None:
        """Fetch an org-specific prompt item by id."""
        with self._session_factory() as session:
            return (
                session.query(PromptItemRecord)
                .filter(
                    PromptItemRecord.organisation_id == organisation_id,
                    PromptItemRecord.id == prompt_item_id,
                )
                .first()
            )

    def list_prompt_items(self, organisation_id: str) -> list[PromptItemRecord]:
        """List all prompt items for an organisation."""
        with self._session_factory() as session:
            return (
                session.query(PromptItemRecord)
                .filter(PromptItemRecord.organisation_id == organisation_id)
                .order_by(PromptItemRecord.created_at.desc())
                .all()
            )

    def update_prompt_item(self, prompt_item: PromptItemRecord) -> PromptItemRecord:
        """Update an org-specific prompt item."""
        with self._session_factory() as session:
            session.add(prompt_item)
            session.commit()
            session.refresh(prompt_item)
            return prompt_item

    def delete_prompt_item(self, organisation_id: str, prompt_item_id: str) -> None:
        """Delete an org-specific prompt item."""
        with self._session_factory() as session:
            session.query(PromptItemRecord).filter(
                PromptItemRecord.organisation_id == organisation_id,
                PromptItemRecord.id == prompt_item_id,
            ).delete()
            session.commit()

    def create_scenario(self, scenario: ScenarioRecord) -> ScenarioRecord:
        """Persist a new org-specific scenario."""
        with self._session_factory() as session:
            session.add(scenario)
            session.commit()
            session.refresh(scenario)
            return scenario

    def get_scenario(self, organisation_id: str, scenario_id: str) -> ScenarioRecord | None:
        """Fetch an org-specific scenario by id."""
        with self._session_factory() as session:
            return (
                session.query(ScenarioRecord)
                .filter(
                    ScenarioRecord.organisation_id == organisation_id,
                    ScenarioRecord.id == scenario_id,
                )
                .first()
            )

    def list_scenarios(self, organisation_id: str) -> list[ScenarioRecord]:
        """List all scenarios for an organisation."""
        with self._session_factory() as session:
            return (
                session.query(ScenarioRecord)
                .filter(ScenarioRecord.organisation_id == organisation_id)
                .order_by(ScenarioRecord.created_at.desc())
                .all()
            )

    def update_scenario(self, scenario: ScenarioRecord) -> ScenarioRecord:
        """Update an org-specific scenario."""
        with self._session_factory() as session:
            session.add(scenario)
            session.commit()
            session.refresh(scenario)
            return scenario

    def delete_scenario(self, organisation_id: str, scenario_id: str) -> None:
        """Delete an org-specific scenario."""
        with self._session_factory() as session:
            session.query(ScenarioRecord).filter(
                ScenarioRecord.organisation_id == organisation_id,
                ScenarioRecord.id == scenario_id,
            ).delete()
            session.commit()
