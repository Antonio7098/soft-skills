"""Catalog authoring and browse services."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.application.auth import Actor
from soft_skills_backend.domain.errors import auth_error, domain_error, validation_error
from soft_skills_backend.observability.events import WorkflowEvent
from soft_skills_backend.persistence.models import (
    CollectionRecord,
    CompetencyRecord,
    CompetencySkillMapRecord,
    MockCompanyRecord,
    MockPersonRecord,
    PromptItemRecord,
    RubricRecord,
    ScenarioRecord,
    SkillRecord,
)
from soft_skills_backend.persistence.repositories import SqlAlchemyWorkflowEventRepository

ALLOWED_COLLECTION_STATES: set[str] = {
    "draft",
    "review",
    "published_private",
    "published_public",
    "archived",
}
ALLOWED_VERIFICATION_STATES: set[str] = {"unverified", "verified", "rejected"}
ALLOWED_PROMPT_TYPES: dict[str, str] = {
    "quick_practice_prompt": "quick_practice_prompt",
    "interview_prompt": "interview_prompt",
}
ALLOWED_SCENARIO_CONTENT_TYPE = "scenario_step"
ALLOWED_DIFFICULTIES: set[str] = {"introductory", "intermediate", "advanced"}
ALLOWED_COLLECTION_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"review", "published_private", "archived"},
    "review": {"draft", "published_private", "published_public", "archived"},
    "published_private": {"review", "published_public", "archived"},
    "published_public": {"review", "archived"},
    "archived": set(),
}


class CollectionCreateCommand(BaseModel):
    title: str
    summary: str
    target_audience: str
    difficulty: str
    content_format_mix: list[str] = Field(default_factory=list)
    target_skill_slugs: list[str]
    target_competency_slugs: list[str]
    rubric_ids: list[str]


class CollectionLifecycleCommand(BaseModel):
    lifecycle_state: str
    verification_state: str | None = None


class PromptItemCreateCommand(BaseModel):
    prompt_type: str
    title: str
    prompt_text: str
    difficulty: str
    target_skill_slugs: list[str]
    rubric_id: str


class MockCompanyInput(BaseModel):
    name: str
    industry: str
    operating_context: str


class MockPersonInput(BaseModel):
    name: str
    role: str
    goals: list[str] = Field(default_factory=list)
    communication_style: str
    relationship_to_scenario: str


class ScenarioCreateCommand(BaseModel):
    title: str
    business_context: str
    learner_objective: str
    constraints: list[str] = Field(default_factory=list)
    stakeholder_tensions: list[str] = Field(default_factory=list)
    target_skill_slugs: list[str]
    rubric_id: str
    mock_company: MockCompanyInput | None = None
    mock_people: list[MockPersonInput] = Field(default_factory=list)


class MockCompanyView(BaseModel):
    id: str
    name: str
    industry: str
    operating_context: str


class MockPersonView(BaseModel):
    id: str
    name: str
    role: str
    goals: list[str]
    communication_style: str
    relationship_to_scenario: str


class PromptItemView(BaseModel):
    id: str
    prompt_type: str
    title: str
    prompt_text: str
    difficulty: str
    lifecycle_state: str
    target_skill_slugs: list[str]
    rubric_id: str


class ScenarioView(BaseModel):
    id: str
    title: str
    business_context: str
    learner_objective: str
    constraints: list[str]
    stakeholder_tensions: list[str]
    lifecycle_state: str
    target_skill_slugs: list[str]
    rubric_id: str
    mock_company: MockCompanyView | None = None
    mock_people: list[MockPersonView] = Field(default_factory=list)


class CollectionView(BaseModel):
    id: str
    author_user_id: str
    title: str
    summary: str
    target_audience: str
    difficulty: str
    lifecycle_state: str
    verification_state: str
    content_format_mix: list[str]
    target_skill_slugs: list[str]
    target_competency_slugs: list[str]
    rubric_ids: list[str]
    prompt_items: list[PromptItemView] = Field(default_factory=list)
    scenarios: list[ScenarioView] = Field(default_factory=list)


class CollectionListFilters(BaseModel):
    difficulty: str | None = None
    skill_slug: str | None = None
    competency_slug: str | None = None
    include_private: bool = True


class CatalogService:
    """Authoring and browse behavior for collections and assessable content."""

    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        workflow_events: SqlAlchemyWorkflowEventRepository,
    ) -> None:
        self._session_factory = session_factory
        self._workflow_events = workflow_events

    def create_collection(self, actor: Actor, command: CollectionCreateCommand) -> CollectionView:
        with self._session_factory() as session:
            self._validate_collection_command(session, command)
            now = datetime.now(UTC)
            collection = CollectionRecord(
                id=uuid4().hex,
                author_user_id=actor.user_id,
                title=command.title,
                summary=command.summary,
                target_audience=command.target_audience,
                difficulty=command.difficulty,
                lifecycle_state="draft",
                verification_state="unverified",
                content_format_mix=command.content_format_mix,
                target_skill_slugs=command.target_skill_slugs,
                target_competency_slugs=command.target_competency_slugs,
                rubric_ids=command.rubric_ids,
                created_at=now,
                updated_at=now,
            )
            session.add(collection)
            session.commit()
            collection_id = collection.id

        self._record_event(
            "catalog.collection.created.v1",
            actor.user_id,
            {"collection_id": collection_id, "author_user_id": actor.user_id},
        )
        return self.get_collection(actor, collection_id)

    def list_collections(self, actor: Actor | None, filters: CollectionListFilters) -> list[CollectionView]:
        with self._session_factory() as session:
            query = session.query(CollectionRecord)
            if filters.difficulty is not None:
                query = query.filter(CollectionRecord.difficulty == filters.difficulty)
            records = query.order_by(CollectionRecord.created_at.desc()).all()
            visible = [
                record
                for record in records
                if self._can_view_collection(actor, record, filters.include_private)
                and (filters.skill_slug is None or filters.skill_slug in record.target_skill_slugs)
                and (
                    filters.competency_slug is None
                    or filters.competency_slug in record.target_competency_slugs
                )
            ]
            return [self._build_collection_view(session, record) for record in visible]

    def get_collection(self, actor: Actor | None, collection_id: str) -> CollectionView:
        with self._session_factory() as session:
            record = session.get(CollectionRecord, collection_id)
            if record is None:
                raise domain_error(
                    "Collection was not found",
                    code="SS-DOMAIN-005",
                    status_code=404,
                    details={"collection_id": collection_id},
                )
            if not self._can_view_collection(actor, record, include_private=True):
                raise auth_error(
                    "Collection is not visible to this actor",
                    code="SS-AUTH-004",
                    status_code=403,
                    details={"collection_id": collection_id},
                )
            return self._build_collection_view(session, record)

    def update_collection_lifecycle(
        self, actor: Actor, collection_id: str, command: CollectionLifecycleCommand
    ) -> CollectionView:
        with self._session_factory() as session:
            record = session.get(CollectionRecord, collection_id)
            if record is None:
                raise domain_error(
                    "Collection was not found",
                    code="SS-DOMAIN-005",
                    status_code=404,
                    details={"collection_id": collection_id},
                )
            self._require_collection_owner_or_admin(actor, record)
            self._validate_lifecycle_transition(session, actor, record, command)
            record.lifecycle_state = command.lifecycle_state
            if command.verification_state is not None:
                record.verification_state = command.verification_state
            record.updated_at = datetime.now(UTC)
            session.commit()

        self._record_event(
            "catalog.collection.lifecycle_changed.v1",
            actor.user_id,
            {
                "collection_id": collection_id,
                "lifecycle_state": command.lifecycle_state,
                "verification_state": command.verification_state,
            },
        )
        return self.get_collection(actor, collection_id)

    def add_prompt_item(
        self, actor: Actor, collection_id: str, command: PromptItemCreateCommand
    ) -> PromptItemView:
        with self._session_factory() as session:
            collection = session.get(CollectionRecord, collection_id)
            if collection is None:
                raise domain_error(
                    "Collection was not found",
                    code="SS-DOMAIN-005",
                    status_code=404,
                    details={"collection_id": collection_id},
                )
            self._require_collection_owner_or_admin(actor, collection)
            self._validate_prompt_command(session, collection, command)
            record = PromptItemRecord(
                id=uuid4().hex,
                collection_id=collection_id,
                author_user_id=actor.user_id,
                prompt_type=command.prompt_type,
                title=command.title,
                prompt_text=command.prompt_text,
                difficulty=command.difficulty,
                lifecycle_state="draft",
                target_skill_slugs=command.target_skill_slugs,
                rubric_id=command.rubric_id,
            )
            session.add(record)
            collection.updated_at = datetime.now(UTC)
            session.commit()
            prompt_id = record.id

        self._record_event(
            "catalog.prompt_item.created.v1",
            actor.user_id,
            {"collection_id": collection_id, "prompt_item_id": prompt_id},
        )
        return self.get_collection(actor, collection_id).prompt_items[-1]

    def add_scenario(
        self, actor: Actor, collection_id: str, command: ScenarioCreateCommand
    ) -> ScenarioView:
        with self._session_factory() as session:
            collection = session.get(CollectionRecord, collection_id)
            if collection is None:
                raise domain_error(
                    "Collection was not found",
                    code="SS-DOMAIN-005",
                    status_code=404,
                    details={"collection_id": collection_id},
                )
            self._require_collection_owner_or_admin(actor, collection)
            self._validate_scenario_command(session, collection, command)
            scenario = ScenarioRecord(
                id=uuid4().hex,
                collection_id=collection_id,
                author_user_id=actor.user_id,
                title=command.title,
                business_context=command.business_context,
                learner_objective=command.learner_objective,
                constraints=command.constraints,
                stakeholder_tensions=command.stakeholder_tensions,
                lifecycle_state="draft",
                target_skill_slugs=command.target_skill_slugs,
                rubric_id=command.rubric_id,
            )
            session.add(scenario)
            session.flush()
            if command.mock_company is not None:
                company = MockCompanyRecord(
                    id=uuid4().hex,
                    scenario_id=scenario.id,
                    name=command.mock_company.name,
                    industry=command.mock_company.industry,
                    operating_context=command.mock_company.operating_context,
                )
                session.add(company)
                session.flush()
                company_id = company.id
            else:
                company_id = None
            for person in command.mock_people:
                session.add(
                    MockPersonRecord(
                        id=uuid4().hex,
                        scenario_id=scenario.id,
                        mock_company_id=company_id,
                        name=person.name,
                        role=person.role,
                        goals=person.goals,
                        communication_style=person.communication_style,
                        relationship_to_scenario=person.relationship_to_scenario,
                    )
                )
            collection.updated_at = datetime.now(UTC)
            session.commit()
            scenario_id = scenario.id

        self._record_event(
            "catalog.scenario.created.v1",
            actor.user_id,
            {"collection_id": collection_id, "scenario_id": scenario_id},
        )
        return self.get_collection(actor, collection_id).scenarios[-1]

    def _record_event(self, event_type: str, request_id: str, payload: dict[str, Any]) -> None:
        self._workflow_events.record(
            WorkflowEvent(
                event_type=event_type,
                request_id=request_id,
                workflow_id=payload.get("collection_id") or payload.get("scenario_id"),
                payload=payload,
            )
        )

    def _build_collection_view(self, session: Session, record: CollectionRecord) -> CollectionView:
        prompt_items = [
            PromptItemView(
                id=item.id,
                prompt_type=item.prompt_type,
                title=item.title,
                prompt_text=item.prompt_text,
                difficulty=item.difficulty,
                lifecycle_state=item.lifecycle_state,
                target_skill_slugs=list(item.target_skill_slugs),
                rubric_id=item.rubric_id,
            )
            for item in session.query(PromptItemRecord)
            .filter(PromptItemRecord.collection_id == record.id)
            .order_by(PromptItemRecord.created_at)
            .all()
        ]
        scenarios: list[ScenarioView] = []
        scenario_records = (
            session.query(ScenarioRecord)
            .filter(ScenarioRecord.collection_id == record.id)
            .order_by(ScenarioRecord.created_at)
            .all()
        )
        for scenario in scenario_records:
            company_record = (
                session.query(MockCompanyRecord)
                .filter(MockCompanyRecord.scenario_id == scenario.id)
                .one_or_none()
            )
            people_records = (
                session.query(MockPersonRecord)
                .filter(MockPersonRecord.scenario_id == scenario.id)
                .order_by(MockPersonRecord.name)
                .all()
            )
            scenarios.append(
                ScenarioView(
                    id=scenario.id,
                    title=scenario.title,
                    business_context=scenario.business_context,
                    learner_objective=scenario.learner_objective,
                    constraints=list(scenario.constraints),
                    stakeholder_tensions=list(scenario.stakeholder_tensions),
                    lifecycle_state=scenario.lifecycle_state,
                    target_skill_slugs=list(scenario.target_skill_slugs),
                    rubric_id=scenario.rubric_id,
                    mock_company=None
                    if company_record is None
                    else MockCompanyView(
                        id=company_record.id,
                        name=company_record.name,
                        industry=company_record.industry,
                        operating_context=company_record.operating_context,
                    ),
                    mock_people=[
                        MockPersonView(
                            id=person.id,
                            name=person.name,
                            role=person.role,
                            goals=list(person.goals),
                            communication_style=person.communication_style,
                            relationship_to_scenario=person.relationship_to_scenario,
                        )
                        for person in people_records
                    ],
                )
            )

        return CollectionView(
            id=record.id,
            author_user_id=record.author_user_id,
            title=record.title,
            summary=record.summary,
            target_audience=record.target_audience,
            difficulty=record.difficulty,
            lifecycle_state=record.lifecycle_state,
            verification_state=record.verification_state,
            content_format_mix=list(record.content_format_mix),
            target_skill_slugs=list(record.target_skill_slugs),
            target_competency_slugs=list(record.target_competency_slugs),
            rubric_ids=list(record.rubric_ids),
            prompt_items=prompt_items,
            scenarios=scenarios,
        )

    def _can_view_collection(
        self, actor: Actor | None, record: CollectionRecord, include_private: bool
    ) -> bool:
        if record.lifecycle_state == "published_public":
            return True
        if not include_private:
            return False
        if actor is None:
            return False
        return actor.is_admin or actor.user_id == record.author_user_id

    def _require_collection_owner_or_admin(self, actor: Actor, collection: CollectionRecord) -> None:
        if actor.is_admin or actor.user_id == collection.author_user_id:
            return
        raise auth_error(
            "Only the collection owner or an admin can modify this collection",
            code="SS-AUTH-005",
            status_code=403,
            details={"collection_id": collection.id},
        )

    def _validate_collection_command(self, session: Session, command: CollectionCreateCommand) -> None:
        self._validate_difficulty(command.difficulty)
        if not command.target_skill_slugs:
            raise validation_error(
                "Collections must target at least one skill",
                code="SS-VALIDATION-003",
            )
        if not command.target_competency_slugs:
            raise validation_error(
                "Collections must target at least one competency",
                code="SS-VALIDATION-004",
            )
        self._require_existing_skills(session, command.target_skill_slugs)
        self._require_existing_competencies(session, command.target_competency_slugs)
        self._require_existing_rubrics(session, command.rubric_ids)
        self._require_skill_competency_alignment(
            session, command.target_skill_slugs, command.target_competency_slugs
        )

    def _validate_prompt_command(
        self, session: Session, collection: CollectionRecord, command: PromptItemCreateCommand
    ) -> None:
        self._validate_difficulty(command.difficulty)
        if command.prompt_type not in ALLOWED_PROMPT_TYPES:
            raise validation_error(
                "Unsupported prompt type",
                code="SS-VALIDATION-005",
                details={"prompt_type": command.prompt_type},
            )
        self._require_existing_skills(session, command.target_skill_slugs)
        self._require_existing_rubrics(session, [command.rubric_id])
        rubric = session.get(RubricRecord, command.rubric_id)
        if rubric is None:
            raise validation_error("Rubric was not found", details={"rubric_id": command.rubric_id})
        expected_content_type = ALLOWED_PROMPT_TYPES[command.prompt_type]
        if rubric.content_type != expected_content_type:
            raise validation_error(
                "Prompt type and rubric content type do not match",
                code="SS-VALIDATION-006",
                details={"prompt_type": command.prompt_type, "rubric_id": command.rubric_id},
            )
        if not set(command.target_skill_slugs).issubset(set(collection.target_skill_slugs)):
            raise validation_error(
                "Prompt item skills must be a subset of the collection skills",
                code="SS-VALIDATION-007",
            )

    def _validate_scenario_command(
        self, session: Session, collection: CollectionRecord, command: ScenarioCreateCommand
    ) -> None:
        self._require_existing_skills(session, command.target_skill_slugs)
        self._require_existing_rubrics(session, [command.rubric_id])
        rubric = session.get(RubricRecord, command.rubric_id)
        if rubric is None:
            raise validation_error("Rubric was not found", details={"rubric_id": command.rubric_id})
        if rubric.content_type != ALLOWED_SCENARIO_CONTENT_TYPE:
            raise validation_error(
                "Scenario rubric must target scenario steps",
                code="SS-VALIDATION-008",
                details={"rubric_id": command.rubric_id},
            )
        if not set(command.target_skill_slugs).issubset(set(collection.target_skill_slugs)):
            raise validation_error(
                "Scenario skills must be a subset of the collection skills",
                code="SS-VALIDATION-009",
            )

    def _validate_lifecycle_transition(
        self,
        session: Session,
        actor: Actor,
        collection: CollectionRecord,
        command: CollectionLifecycleCommand,
    ) -> None:
        if command.lifecycle_state not in ALLOWED_COLLECTION_STATES:
            raise validation_error(
                "Unsupported lifecycle state",
                code="SS-VALIDATION-010",
                details={"state": command.lifecycle_state},
            )
        allowed_next_states = ALLOWED_COLLECTION_TRANSITIONS.get(collection.lifecycle_state, set())
        if command.lifecycle_state not in allowed_next_states and command.lifecycle_state != collection.lifecycle_state:
            raise domain_error(
                "Invalid lifecycle transition",
                code="SS-DOMAIN-006",
                details={
                    "current_state": collection.lifecycle_state,
                    "next_state": command.lifecycle_state,
                },
            )
        if command.verification_state is not None:
            if command.verification_state not in ALLOWED_VERIFICATION_STATES:
                raise validation_error(
                    "Unsupported verification state",
                    code="SS-VALIDATION-011",
                    details={"verification_state": command.verification_state},
                )
            if command.verification_state == "verified" and not actor.is_admin:
                raise auth_error(
                    "Only admins can verify collections",
                    code="SS-AUTH-006",
                    status_code=403,
                )
        if command.lifecycle_state == "published_public":
            prompt_count = (
                session.query(PromptItemRecord).filter(PromptItemRecord.collection_id == collection.id).count()
            )
            scenario_count = (
                session.query(ScenarioRecord).filter(ScenarioRecord.collection_id == collection.id).count()
            )
            if prompt_count + scenario_count == 0:
                raise domain_error(
                    "Collections cannot be published without at least one content item",
                    code="SS-DOMAIN-007",
                )

    def _validate_difficulty(self, difficulty: str) -> None:
        if difficulty not in ALLOWED_DIFFICULTIES:
            raise validation_error(
                "Unsupported difficulty level",
                code="SS-VALIDATION-012",
                details={"difficulty": difficulty},
            )

    def _require_existing_skills(self, session: Session, skill_slugs: list[str]) -> None:
        existing = {
            record.slug
            for record in session.query(SkillRecord).filter(SkillRecord.slug.in_(skill_slugs)).all()
        }
        missing = sorted(set(skill_slugs) - existing)
        if missing:
            raise validation_error(
                "Unknown skill mapping",
                code="SS-VALIDATION-013",
                details={"missing_skills": missing},
            )

    def _require_existing_competencies(self, session: Session, competency_slugs: list[str]) -> None:
        existing = {
            record.slug
            for record in session.query(CompetencyRecord)
            .filter(CompetencyRecord.slug.in_(competency_slugs))
            .all()
        }
        missing = sorted(set(competency_slugs) - existing)
        if missing:
            raise validation_error(
                "Unknown competency mapping",
                code="SS-VALIDATION-014",
                details={"missing_competencies": missing},
            )

    def _require_existing_rubrics(self, session: Session, rubric_ids: list[str]) -> None:
        existing = {
            record.rubric_id
            for record in session.query(RubricRecord).filter(RubricRecord.rubric_id.in_(rubric_ids)).all()
        }
        missing = sorted(set(rubric_ids) - existing)
        if missing:
            raise validation_error(
                "Unknown rubric mapping",
                code="SS-VALIDATION-015",
                details={"missing_rubrics": missing},
            )

    def _require_skill_competency_alignment(
        self, session: Session, skill_slugs: list[str], competency_slugs: list[str]
    ) -> None:
        pairs = {
            (record.competency_slug, record.skill_slug)
            for record in session.query(CompetencySkillMapRecord)
            .filter(CompetencySkillMapRecord.competency_slug.in_(competency_slugs))
            .all()
        }
        uncovered = [
            skill_slug
            for skill_slug in skill_slugs
            if all((competency_slug, skill_slug) not in pairs for competency_slug in competency_slugs)
        ]
        if uncovered:
            raise validation_error(
                "Skills must align with selected competencies",
                code="SS-VALIDATION-016",
                details={"uncovered_skills": uncovered},
            )
