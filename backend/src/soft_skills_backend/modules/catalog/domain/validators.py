"""Catalog permission and validation helpers."""

from __future__ import annotations

from sqlalchemy.orm import Session

from soft_skills_backend.modules.catalog.contracts.collection_commands import (
    CollectionCreateCommand,
    CollectionLifecycleCommand,
)
from soft_skills_backend.modules.catalog.contracts.prompt_item_commands import (
    PromptItemCreateCommand,
)
from soft_skills_backend.modules.catalog.contracts.scenario_commands import ScenarioCreateCommand
from soft_skills_backend.platform.db.models import (
    CollectionRecord,
    CompetencyRecord,
    CompetencySkillMapRecord,
    PromptItemRecord,
    RubricRecord,
    ScenarioRecord,
    SkillRecord,
)
from soft_skills_backend.shared.auth import Actor
from soft_skills_backend.shared.errors import auth_error, domain_error, validation_error

from .constants import (
    ALLOWED_COLLECTION_STATES,
    ALLOWED_COLLECTION_TRANSITIONS,
    ALLOWED_DIFFICULTIES,
    ALLOWED_PROMPT_TYPES,
    ALLOWED_SCENARIO_CONTENT_TYPE,
    ALLOWED_VERIFICATION_STATES,
)


def can_view_collection(
    actor: Actor | None, record: CollectionRecord, include_private: bool
) -> bool:
    if record.lifecycle_state == "published_public":
        return True
    if not include_private or actor is None:
        return False
    return actor.is_admin or actor.user_id == record.author_user_id


def require_collection_owner_or_admin(actor: Actor, collection: CollectionRecord) -> None:
    if actor.is_admin or actor.user_id == collection.author_user_id:
        return
    raise auth_error(
        "Only the collection owner or an admin can modify this collection",
        code="SS-AUTH-005",
        status_code=403,
        details={"collection_id": collection.id},
    )


def validate_collection_command(session: Session, command: CollectionCreateCommand) -> None:
    validate_difficulty(command.difficulty)
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
    require_existing_skills(session, command.target_skill_slugs)
    require_existing_competencies(session, command.target_competency_slugs)
    require_existing_rubrics(session, command.rubric_ids)
    require_skill_competency_alignment(
        session, command.target_skill_slugs, command.target_competency_slugs
    )


def validate_prompt_command(
    session: Session, collection: CollectionRecord, command: PromptItemCreateCommand
) -> None:
    validate_difficulty(command.difficulty)
    if command.prompt_type not in ALLOWED_PROMPT_TYPES:
        raise validation_error(
            "Unsupported prompt type",
            code="SS-VALIDATION-005",
            details={"prompt_type": command.prompt_type},
        )
    require_existing_skills(session, command.target_skill_slugs)
    require_existing_rubrics(session, [command.rubric_id])
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


def validate_scenario_command(
    session: Session, collection: CollectionRecord, command: ScenarioCreateCommand
) -> None:
    require_existing_skills(session, command.target_skill_slugs)
    require_existing_rubrics(session, [command.rubric_id])
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


def validate_lifecycle_transition(
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
    if (
        command.lifecycle_state not in allowed_next_states
        and command.lifecycle_state != collection.lifecycle_state
    ):
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
            session.query(PromptItemRecord)
            .filter(PromptItemRecord.collection_id == collection.id)
            .count()
        )
        scenario_count = (
            session.query(ScenarioRecord)
            .filter(ScenarioRecord.collection_id == collection.id)
            .count()
        )
        if prompt_count + scenario_count == 0:
            raise domain_error(
                "Collections cannot be published without at least one content item",
                code="SS-DOMAIN-007",
            )


def validate_difficulty(difficulty: str) -> None:
    if difficulty not in ALLOWED_DIFFICULTIES:
        raise validation_error(
            "Unsupported difficulty level",
            code="SS-VALIDATION-012",
            details={"difficulty": difficulty},
        )


def require_existing_skills(session: Session, skill_slugs: list[str]) -> None:
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


def require_existing_competencies(session: Session, competency_slugs: list[str]) -> None:
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


def require_existing_rubrics(session: Session, rubric_ids: list[str]) -> None:
    existing = {
        record.rubric_id
        for record in session.query(RubricRecord)
        .filter(RubricRecord.rubric_id.in_(rubric_ids))
        .all()
    }
    missing = sorted(set(rubric_ids) - existing)
    if missing:
        raise validation_error(
            "Unknown rubric mapping",
            code="SS-VALIDATION-015",
            details={"missing_rubrics": missing},
        )


def require_skill_competency_alignment(
    session: Session, skill_slugs: list[str], competency_slugs: list[str]
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
