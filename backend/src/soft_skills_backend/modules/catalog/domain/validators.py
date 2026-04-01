"""Catalog permission and validation helpers."""

from __future__ import annotations

from typing import cast

from sqlalchemy.orm import Session

from soft_skills_backend.modules.catalog.contracts.collection_commands import (
    ChatCollectionGenerationCommand,
    CollectionCreateCommand,
    CollectionLifecycleCommand,
    CollectionListFilters,
    CollectionRateCommand,
    CollectionUpdateCommand,
    StructuredCollectionGenerationCommand,
)
from soft_skills_backend.modules.catalog.contracts.prompt_item_commands import (
    ChatPromptItemGenerationCommand,
    PromptItemCreateCommand,
    PromptItemUpdateCommand,
    StructuredPromptItemGenerationCommand,
)
from soft_skills_backend.modules.catalog.contracts.scenario_commands import (
    ScenarioCreateCommand,
    ScenarioUpdateCommand,
)
from soft_skills_backend.modules.catalog.domain.constants import (
    ALLOWED_COLLECTION_SOURCE_TYPES,
    ALLOWED_COLLECTION_STATES,
    ALLOWED_COLLECTION_TRANSITIONS,
    ALLOWED_DIFFICULTIES,
    ALLOWED_DISCOVERY_TIERS,
    ALLOWED_PROMPT_TYPES,
    ALLOWED_SCENARIO_ARTIFACT_TYPES,
    ALLOWED_SCENARIO_CONTENT_TYPE,
)
from soft_skills_backend.platform.db.models import (
    CollectionRecord,
    CollectionSaveRecord,
    CompetencyRecord,
    CompetencySkillMapRecord,
    MockCompanyRecord,
    MockPersonRecord,
    PromptItemRecord,
    RubricRecord,
    ScenarioRecord,
    ScenarioSupportingArtifactRecord,
    SkillRecord,
)
from soft_skills_backend.shared.auth import Actor
from soft_skills_backend.shared.errors import auth_error, domain_error, validation_error


def discovery_tier_for_collection(record: CollectionRecord) -> str:
    if record.lifecycle_state != "published_public":
        return "private"
    if record.organisation_id is None and record.verification_state == "verified":
        return "global_public"
    if record.organisation_id is not None:
        return "org_public"
    return "standard_public"


def can_view_collection(
    actor: Actor | None, record: CollectionRecord, include_private: bool
) -> bool:
    # Global hub published collections are visible to everyone (verified = global_public, not verified = standard_public)
    if record.organisation_id is None and record.lifecycle_state == "published_public":
        return True
    # Org published collections are visible to org members only
    if record.organisation_id is not None and record.lifecycle_state == "published_public":
        if actor is not None and actor.organisation_id == record.organisation_id:
            return True
        return actor is not None and actor.user_id == record.author_user_id
    # For non-published collections, check auth
    if not include_private or actor is None:
        return False
    # Author can always see their own collection
    if actor.user_id == record.author_user_id:
        return True
    return actor.is_org_admin and actor.organisation_id == record.organisation_id


def require_visible_collection(actor: Actor, record: CollectionRecord) -> None:
    if can_view_collection(actor, record, include_private=True):
        return
    raise auth_error(
        "Collection is not visible to this actor",
        code="SS-AUTH-004",
        status_code=403,
        details={"collection_id": record.id},
    )


def require_collection_owner_or_admin(actor: Actor, collection: CollectionRecord) -> None:
    if actor.user_id == collection.author_user_id:
        return
    if actor.is_org_admin and actor.organisation_id == collection.organisation_id:
        return
    raise auth_error(
        "Only the collection owner or an org admin can modify this collection",
        code="SS-AUTH-005",
        status_code=403,
        details={"collection_id": collection.id},
    )


def validate_collection_filters(filters: CollectionListFilters) -> None:
    if filters.discovery_tier is not None and filters.discovery_tier not in ALLOWED_DISCOVERY_TIERS:
        raise validation_error(
            "Unsupported discovery tier",
            code="SS-VALIDATION-034",
            details={"discovery_tier": filters.discovery_tier},
        )


def validate_collection_command(
    session: Session, command: CollectionCreateCommand | CollectionUpdateCommand
) -> None:
    validate_difficulty(command.difficulty)
    if not command.content_format_mix:
        raise validation_error(
            "Collections must declare at least one content format",
            code="SS-VALIDATION-035",
        )
    unsupported_formats = sorted(
        {
            format_slug
            for format_slug in command.content_format_mix
            if format_slug not in {*ALLOWED_PROMPT_TYPES.values(), ALLOWED_SCENARIO_CONTENT_TYPE}
        }
    )
    if unsupported_formats:
        raise validation_error(
            "Unsupported content format",
            code="SS-VALIDATION-036",
            details={"unsupported_formats": unsupported_formats},
        )
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
    require_existing_skills(session, command.target_skill_slugs, command.organisation_id)
    require_existing_competencies(session, command.target_competency_slugs, command.organisation_id)
    require_existing_rubrics(session, command.rubric_ids, command.organisation_id)
    require_skill_competency_alignment(
        session,
        command.target_skill_slugs,
        command.target_competency_slugs,
        command.organisation_id,
    )
    require_rubric_content_alignment(
        session, command.content_format_mix, command.rubric_ids, command.organisation_id
    )


def validate_prompt_command(
    session: Session,
    collection: CollectionRecord | None,
    command: PromptItemCreateCommand | PromptItemUpdateCommand,
) -> None:
    is_update = isinstance(command, PromptItemUpdateCommand)
    if command.difficulty is not None:
        validate_difficulty(command.difficulty)
    if command.prompt_type is not None:
        if command.prompt_type not in ALLOWED_PROMPT_TYPES:
            raise validation_error(
                "Unsupported prompt type",
                code="SS-VALIDATION-005",
                details={"prompt_type": command.prompt_type},
            )
    if command.target_skill_slugs is not None:
        require_existing_skills(session, command.target_skill_slugs, command.organisation_id)
    if command.rubric_id is not None:
        require_existing_rubrics(session, [command.rubric_id], command.organisation_id)
        rubric = session.get(RubricRecord, command.rubric_id)
        if rubric is None:
            raise validation_error("Rubric was not found", details={"rubric_id": command.rubric_id})
        if command.prompt_type is not None:
            expected_content_type = ALLOWED_PROMPT_TYPES[command.prompt_type]
            if rubric.content_type != expected_content_type:
                raise validation_error(
                    "Prompt type and rubric content type do not match",
                    code="SS-VALIDATION-006",
                    details={"prompt_type": command.prompt_type, "rubric_id": command.rubric_id},
                )
    if collection is not None and command.prompt_type is not None and not is_update:
        if command.target_skill_slugs is not None:
            if not set(command.target_skill_slugs).issubset(set(collection.target_skill_slugs)):
                raise validation_error(
                    "Prompt item skills must be a subset of the collection skills",
                    code="SS-VALIDATION-007",
                )
        if command.prompt_type not in collection.content_format_mix:
            raise validation_error(
                "Prompt item type must be enabled on the collection",
                code="SS-VALIDATION-037",
                details={"prompt_type": command.prompt_type, "collection_id": collection.id},
            )


def validate_scenario_command(
    session: Session,
    collection: CollectionRecord | None,
    command: ScenarioCreateCommand | ScenarioUpdateCommand,
) -> None:
    is_update = isinstance(command, ScenarioUpdateCommand)
    prompt_text = getattr(command, "prompt_text", None)
    if prompt_text is not None and not prompt_text.strip():
        raise validation_error(
            "Scenario prompt text is required",
            code="SS-VALIDATION-088",
        )
    if command.target_skill_slugs is not None:
        require_existing_skills(session, command.target_skill_slugs, command.organisation_id)
    if command.rubric_id is not None:
        require_existing_rubrics(session, [command.rubric_id], command.organisation_id)
        rubric = session.get(RubricRecord, command.rubric_id)
        if rubric is None:
            raise validation_error("Rubric was not found", details={"rubric_id": command.rubric_id})
        if rubric.content_type != ALLOWED_SCENARIO_CONTENT_TYPE:
            raise validation_error(
                "Scenario rubric must target scenario steps",
                code="SS-VALIDATION-008",
                details={"rubric_id": command.rubric_id},
            )
    if collection is not None and not is_update:
        if command.target_skill_slugs is not None:
            if not set(command.target_skill_slugs).issubset(set(collection.target_skill_slugs)):
                raise validation_error(
                    "Scenario skills must be a subset of the collection skills",
                    code="SS-VALIDATION-009",
                )
        if ALLOWED_SCENARIO_CONTENT_TYPE not in collection.content_format_mix:
            raise validation_error(
                "Scenario content must be enabled on the collection",
                code="SS-VALIDATION-038",
                details={"collection_id": collection.id},
            )
    if command.supporting_artifacts is not None:
        validate_supporting_artifacts(cast(list[object], command.supporting_artifacts))
    if not is_update or (
        is_update and (command.mock_company is not None or command.mock_people is not None)
    ):
        validate_mock_world(command)


def validate_generation_request(
    session: Session,
    command: StructuredCollectionGenerationCommand | ChatCollectionGenerationCommand,
) -> None:
    skill_count = session.query(SkillRecord).filter(SkillRecord.organisation_id.is_(None)).count()
    competency_count = (
        session.query(CompetencyRecord)
        .filter(CompetencyRecord.organisation_id.is_(None))
        .count()
    )
    rubric_count = session.query(RubricRecord).filter(RubricRecord.organisation_id.is_(None)).count()
    if skill_count == 0 or competency_count == 0 or rubric_count == 0:
        raise validation_error(
            "Generation cannot start because the taxonomy catalog is empty. Seed skills, competencies, and rubrics before generating a collection.",
            code="SS-VALIDATION-071",
            details={
                "skills": skill_count,
                "competencies": competency_count,
                "rubrics": rubric_count,
            },
        )
    validate_collection_command(
        session,
        CollectionCreateCommand(
            title=(
                command.title_hint
                if isinstance(command, StructuredCollectionGenerationCommand) and command.title_hint
                else "Generated draft"
            ),
            summary="Generated draft",
            target_audience=command.target_audience,
            difficulty=command.difficulty,
            content_format_mix=command.content_format_mix,
            target_skill_slugs=command.target_skill_slugs,
            target_competency_slugs=command.target_competency_slugs,
            rubric_ids=command.rubric_ids,
        ),
    )
    if (
        command.counts.quick_practice_prompt_count
        and "quick_practice_prompt" not in command.content_format_mix
    ):
        raise validation_error(
            "Quick-practice prompt generation requires the matching content format",
            code="SS-VALIDATION-039",
        )
    if (
        command.counts.interview_prompt_count
        and "interview_prompt" not in command.content_format_mix
    ):
        raise validation_error(
            "Interview prompt generation requires the matching content format",
            code="SS-VALIDATION-040",
        )
    if (
        command.counts.scenario_count
        and ALLOWED_SCENARIO_CONTENT_TYPE not in command.content_format_mix
    ):
        raise validation_error(
            "Scenario generation requires the scenario content format",
            code="SS-VALIDATION-041",
        )
    if command.counts.scenario_artifact_count and command.counts.scenario_count == 0:
        raise validation_error(
            "Scenario supporting artifacts require at least one scenario",
            code="SS-VALIDATION-042",
        )


def validate_prompt_item_generation_request(
    session: Session,
    collection: CollectionRecord,
    command: StructuredPromptItemGenerationCommand | ChatPromptItemGenerationCommand,
) -> list[str]:
    requested_skill_slugs = (
        list(command.target_skill_slugs)
        if command.target_skill_slugs
        else list(collection.target_skill_slugs)
    )
    require_existing_skills(session, requested_skill_slugs)
    if not set(requested_skill_slugs).issubset(set(collection.target_skill_slugs)):
        raise validation_error(
            "Generated prompt item skills must be a subset of the collection skills",
            code="SS-VALIDATION-059",
            details={"collection_id": collection.id},
        )
    if (
        command.counts.quick_practice_prompt_count
        and "quick_practice_prompt" not in collection.content_format_mix
    ):
        raise validation_error(
            "Quick-practice prompt generation requires the collection to enable quick-practice prompts",
            code="SS-VALIDATION-060",
            details={"collection_id": collection.id},
        )
    if (
        command.counts.interview_prompt_count
        and "interview_prompt" not in collection.content_format_mix
    ):
        raise validation_error(
            "Interview prompt generation requires the collection to enable interview prompts",
            code="SS-VALIDATION-061",
            details={"collection_id": collection.id},
        )

    compatible_content_types = {
        record.content_type
        for record in session.query(RubricRecord)
        .filter(RubricRecord.id.in_(collection.rubric_ids))
        .all()
    }
    if (
        command.counts.quick_practice_prompt_count
        and "quick_practice_prompt" not in compatible_content_types
    ):
        raise validation_error(
            "The collection does not have a quick-practice rubric available for generated prompt items",
            code="SS-VALIDATION-062",
            details={"collection_id": collection.id},
        )
    if command.counts.interview_prompt_count and "interview_prompt" not in compatible_content_types:
        raise validation_error(
            "The collection does not have an interview rubric available for generated prompt items",
            code="SS-VALIDATION-063",
            details={"collection_id": collection.id},
        )
    return requested_skill_slugs


def validate_generated_prompt_item_uniqueness(
    *,
    existing_prompt_items: list[PromptItemRecord],
    generated_commands: list[PromptItemCreateCommand],
) -> None:
    existing_titles = {_normalize_prompt_text(record.title) for record in existing_prompt_items}
    existing_bodies = {
        _normalize_prompt_text(record.prompt_text) for record in existing_prompt_items
    }
    seen_titles: set[str] = set()
    seen_bodies: set[str] = set()

    for command in generated_commands:
        normalized_title = _normalize_prompt_text(command.title)
        normalized_body = _normalize_prompt_text(command.prompt_text)
        if normalized_title in seen_titles or normalized_body in seen_bodies:
            raise validation_error(
                "Generated prompt items must be unique within the batch",
                code="SS-VALIDATION-064",
            )
        if normalized_title in existing_titles or normalized_body in existing_bodies:
            raise validation_error(
                "Generated prompt items must not duplicate existing collection prompt items",
                code="SS-VALIDATION-065",
            )
        seen_titles.add(normalized_title)
        seen_bodies.add(normalized_body)


def validate_collection_source_type(source_type: str) -> None:
    if source_type not in ALLOWED_COLLECTION_SOURCE_TYPES:
        raise validation_error(
            "Unsupported collection source type",
            code="SS-VALIDATION-043",
            details={"source_type": source_type},
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
        raise validation_error(
            "Collection verification must use the admin verification workflow",
            code="SS-VALIDATION-048",
            details={"collection_id": collection.id},
        )
    if command.lifecycle_state == "published_public":
        validate_collection_publishability(session, collection)


def validate_collection_publishability(session: Session, collection: CollectionRecord) -> None:
    prompt_records = (
        session.query(PromptItemRecord)
        .filter(PromptItemRecord.collection_id == collection.id)
        .all()
    )
    scenario_records = (
        session.query(ScenarioRecord).filter(ScenarioRecord.collection_id == collection.id).all()
    )
    if len(prompt_records) + len(scenario_records) == 0:
        raise domain_error(
            "Collections cannot be published without at least one content item",
            code="SS-DOMAIN-007",
        )
    available_formats = {record.prompt_type for record in prompt_records}
    if scenario_records:
        available_formats.add(ALLOWED_SCENARIO_CONTENT_TYPE)
    missing_formats = sorted(set(collection.content_format_mix) - available_formats)
    if missing_formats:
        raise domain_error(
            "Collections cannot be published while declared formats are missing content",
            code="SS-DOMAIN-023",
            details={"missing_formats": missing_formats, "collection_id": collection.id},
        )


def validate_collection_save(
    session: Session,
    actor: Actor,
    collection: CollectionRecord,
) -> None:
    require_visible_collection(actor, collection)
    if actor.user_id == collection.author_user_id:
        raise domain_error(
            "Authors do not need to save their own collections",
            code="SS-DOMAIN-024",
            details={"collection_id": collection.id},
        )
    existing = session.get(
        CollectionSaveRecord,
        {"user_id": actor.user_id, "collection_id": collection.id},
    )
    if existing is not None:
        raise domain_error(
            "Collection is already saved",
            code="SS-DOMAIN-025",
            details={"collection_id": collection.id},
        )


def validate_collection_unsave(
    session: Session,
    actor: Actor,
    collection: CollectionRecord,
) -> None:
    existing = session.get(
        CollectionSaveRecord,
        {"user_id": actor.user_id, "collection_id": collection.id},
    )
    if existing is None:
        raise domain_error(
            "Collection is not currently saved",
            code="SS-DOMAIN-026",
            details={"collection_id": collection.id},
        )


def validate_collection_rate(
    session: Session,
    actor: Actor,
    collection: CollectionRecord,
    command: CollectionRateCommand,
) -> None:
    if command.rating < 1 or command.rating > 5:
        raise validation_error(
            "Rating must be between 1 and 5",
            code="SS-VALIDATION-066",
            details={"rating": command.rating},
        )


def validate_collection_unrate(
    session: Session,
    actor: Actor,
    collection: CollectionRecord,
) -> None:
    from soft_skills_backend.platform.db.models import CollectionRatingRecord

    existing = session.get(
        CollectionRatingRecord,
        {"user_id": actor.user_id, "collection_id": collection.id},
    )
    if existing is None:
        raise domain_error(
            "Collection is not currently rated by this user",
            code="SS-DOMAIN-027",
            details={"collection_id": collection.id},
        )


def validate_difficulty(difficulty: str) -> None:
    if difficulty not in ALLOWED_DIFFICULTIES:
        raise validation_error(
            "Unsupported difficulty level",
            code="SS-VALIDATION-012",
            details={"difficulty": difficulty},
        )


def validate_supporting_artifacts(artifacts: list[object]) -> None:
    unsupported_types = sorted(
        {
            str(
                getattr(artifact, "artifact_type", None)
                or cast(dict[str, object], artifact)["artifact_type"]
            )
            for artifact in artifacts
            if (
                getattr(artifact, "artifact_type", None)
                or cast(dict[str, object], artifact)["artifact_type"]
            )
            not in ALLOWED_SCENARIO_ARTIFACT_TYPES
        }
    )
    if unsupported_types:
        raise validation_error(
            "Unsupported scenario supporting artifact type",
            code="SS-VALIDATION-044",
            details={"unsupported_artifact_types": unsupported_types},
        )


def validate_mock_world(command: ScenarioCreateCommand | ScenarioUpdateCommand) -> None:
    if command.mock_people and command.mock_company is None:
        raise validation_error(
            "Scenario mock people require a mock company context",
            code="SS-VALIDATION-045",
        )
    people_names = [person.name.strip().lower() for person in command.mock_people]
    duplicates = sorted({name for name in people_names if people_names.count(name) > 1})
    if duplicates:
        raise validation_error(
            "Scenario mock people must be unique",
            code="SS-VALIDATION-046",
            details={"duplicate_people": duplicates},
        )


def require_existing_skills(
    session: Session, skill_slugs: list[str], organisation_id: str | None = None
) -> None:
    query = session.query(SkillRecord).filter(SkillRecord.slug.in_(skill_slugs))
    if organisation_id is not None:
        query = query.filter(
            (SkillRecord.organisation_id.is_(None))
            | (SkillRecord.organisation_id == organisation_id)
        )
    elif organisation_id is None:
        query = query.filter(SkillRecord.organisation_id.is_(None))
    existing = {record.slug for record in query.all()}
    missing = sorted(set(skill_slugs) - existing)
    if missing:
        raise validation_error(
            "Unknown skill mapping",
            code="SS-VALIDATION-013",
            details={"missing_skills": missing},
        )


def require_existing_competencies(
    session: Session, competency_slugs: list[str], organisation_id: str | None = None
) -> None:
    query = session.query(CompetencyRecord).filter(CompetencyRecord.slug.in_(competency_slugs))
    if organisation_id is not None:
        query = query.filter(
            (CompetencyRecord.organisation_id.is_(None))
            | (CompetencyRecord.organisation_id == organisation_id)
        )
    elif organisation_id is None:
        query = query.filter(CompetencyRecord.organisation_id.is_(None))
    existing = {record.slug for record in query.all()}
    missing = sorted(set(competency_slugs) - existing)
    if missing:
        raise validation_error(
            "Unknown competency mapping",
            code="SS-VALIDATION-014",
            details={"missing_competencies": missing},
        )


def require_existing_rubrics(
    session: Session, rubric_ids: list[str], organisation_id: str | None = None
) -> None:
    query = session.query(RubricRecord).filter(RubricRecord.id.in_(rubric_ids))
    if organisation_id is not None:
        query = query.filter(
            (RubricRecord.organisation_id.is_(None))
            | (RubricRecord.organisation_id == organisation_id)
        )
    elif organisation_id is None:
        query = query.filter(RubricRecord.organisation_id.is_(None))
    existing = {record.id for record in query.all()}
    missing = sorted(set(rubric_ids) - existing)
    if missing:
        raise validation_error(
            "Unknown rubric mapping",
            code="SS-VALIDATION-015",
            details={"missing_rubrics": missing},
        )


def require_skill_competency_alignment(
    session: Session,
    skill_slugs: list[str],
    competency_slugs: list[str],
    organisation_id: str | None = None,
) -> None:
    pairs = {
        (record.competency_slug, record.skill_slug)
        for record in session.query(CompetencySkillMapRecord)
        .filter(CompetencySkillMapRecord.competency_slug.in_(competency_slugs))
        .all()
    }
    if organisation_id is not None:
        from soft_skills_backend.platform.db.models import (
            CompetencyRecord,
            OrganisationSkillMapRecord,
        )

        canon_competencies = {
            record.slug
            for record in session.query(CompetencyRecord)
            .filter(CompetencyRecord.organisation_id.is_(None))
            .all()
        }
        for comp_slug in competency_slugs:
            if comp_slug in canon_competencies:
                continue
            org_comp_pairs = {
                (record.competency_slug, record.skill_slug)
                for record in session.query(OrganisationSkillMapRecord)
                .filter(
                    OrganisationSkillMapRecord.organisation_id == organisation_id,
                    OrganisationSkillMapRecord.competency_slug == comp_slug,
                )
                .all()
            }
            pairs = pairs | org_comp_pairs
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


def require_rubric_content_alignment(
    session: Session,
    content_format_mix: list[str],
    rubric_ids: list[str],
    organisation_id: str | None = None,
) -> None:
    query = session.query(RubricRecord).filter(RubricRecord.id.in_(rubric_ids))
    if organisation_id is not None:
        query = query.filter(
            (RubricRecord.organisation_id.is_(None))
            | (RubricRecord.organisation_id == organisation_id)
        )
    elif organisation_id is None:
        query = query.filter(RubricRecord.organisation_id.is_(None))
    rubrics = {record.id: record for record in query.all()}
    expected_types = set(content_format_mix)
    actual_types = {record.content_type for record in rubrics.values()}
    missing_types = sorted(expected_types - actual_types)
    if missing_types:
        raise validation_error(
            "Collection rubrics must cover every declared content format",
            code="SS-VALIDATION-047",
            details={"missing_rubric_content_types": missing_types},
        )


def clear_scenario_children(session: Session, scenario_id: str) -> None:
    session.query(ScenarioSupportingArtifactRecord).filter(
        ScenarioSupportingArtifactRecord.scenario_id == scenario_id
    ).delete()
    session.query(MockPersonRecord).filter(MockPersonRecord.scenario_id == scenario_id).delete()
    session.query(MockCompanyRecord).filter(MockCompanyRecord.scenario_id == scenario_id).delete()


def _normalize_prompt_text(value: str) -> str:
    return " ".join(value.strip().lower().split())
