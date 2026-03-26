"""Validation helpers for catalog generation workflows."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy.orm import Session

from soft_skills_backend.engines.config.models import CatalogGenerationRuntimeConfig
from soft_skills_backend.modules.catalog.contracts.collection_commands import (
    ChatCollectionGenerationCommand,
    CollectionCreateCommand,
    StructuredCollectionGenerationCommand,
)
from soft_skills_backend.modules.catalog.contracts.prompt_item_commands import (
    PromptItemCreateCommand,
)
from soft_skills_backend.modules.catalog.contracts.scenario_commands import ScenarioCreateCommand
from soft_skills_backend.modules.catalog.domain.models import (
    GeneratedCollectionBlueprint,
    GeneratedCollectionDraft,
    GeneratedPromptItemPlanBatch,
)
from soft_skills_backend.modules.catalog.domain.validators import (
    validate_collection_command,
    validate_generated_prompt_item_uniqueness,
    validate_prompt_command,
    validate_scenario_command,
)
from soft_skills_backend.platform.db.models import CollectionRecord
from soft_skills_backend.shared.errors import validation_error
from soft_skills_backend.shared.ports.llm import LLMProvider


def validate_collection_blueprint(
    *,
    config: CatalogGenerationRuntimeConfig,
    llm_provider: LLMProvider,
    blueprint: GeneratedCollectionBlueprint,
    resolved_model_slug: str,
    structured_command: StructuredCollectionGenerationCommand | None,
    chat_command: ChatCollectionGenerationCommand | None,
) -> None:
    expected_prompt_version = (
        config.structured_prompt_version
        if structured_command is not None
        else config.chat_prompt_version
    )
    if blueprint.prompt_version != expected_prompt_version:
        raise validation_error(
            "Generated blueprint prompt version did not match the requested contract",
            code="SS-VALIDATION-049",
            details={"expected": expected_prompt_version, "actual": blueprint.prompt_version},
        )
    if blueprint.provider != llm_provider.provider_name:
        raise validation_error(
            "Generated blueprint provider did not match the executing provider",
            code="SS-VALIDATION-057",
            details={"expected": llm_provider.provider_name, "actual": blueprint.provider},
        )
    if blueprint.model_slug != resolved_model_slug:
        raise validation_error(
            "Generated blueprint model slug did not match the executing model",
            code="SS-VALIDATION-058",
            details={"expected": resolved_model_slug, "actual": blueprint.model_slug},
        )
    prompt_count = (
        structured_command.counts.quick_practice_prompt_count + structured_command.counts.interview_prompt_count
        if structured_command is not None
        else cast(ChatCollectionGenerationCommand, chat_command).counts.quick_practice_prompt_count
        + cast(ChatCollectionGenerationCommand, chat_command).counts.interview_prompt_count
    )
    scenario_count = (
        structured_command.counts.scenario_count
        if structured_command is not None
        else cast(ChatCollectionGenerationCommand, chat_command).counts.scenario_count
    )
    if len(blueprint.prompt_items) != prompt_count:
        raise validation_error(
            "Generated blueprint prompt count did not match the request",
            code="SS-VALIDATION-054",
            details={"expected": prompt_count, "actual": len(blueprint.prompt_items)},
        )
    if len(blueprint.scenarios) != scenario_count:
        raise validation_error(
            "Generated blueprint scenario count did not match the request",
            code="SS-VALIDATION-055",
            details={"expected": scenario_count, "actual": len(blueprint.scenarios)},
        )


def validate_generated_collection_draft(
    session: Session,
    *,
    config: CatalogGenerationRuntimeConfig,
    draft: GeneratedCollectionDraft,
    structured_command: StructuredCollectionGenerationCommand | None,
    chat_command: ChatCollectionGenerationCommand | None,
) -> None:
    source_command = structured_command or cast(ChatCollectionGenerationCommand, chat_command)
    validate_collection_command(
        session,
        CollectionCreateCommand(
            title=draft.title,
            summary=draft.summary,
            target_audience=draft.target_audience,
            difficulty=draft.difficulty,
            content_format_mix=list(draft.content_format_mix),
            target_skill_slugs=list(draft.target_skill_slugs),
            target_competency_slugs=list(draft.target_competency_slugs),
            rubric_ids=list(draft.rubric_ids),
        ),
    )
    collection_record = CollectionRecord(
        id="draft",
        author_user_id="draft",
        title=draft.title,
        summary=draft.summary,
        target_audience=draft.target_audience,
        difficulty=draft.difficulty,
        lifecycle_state="draft",
        verification_state="unverified",
        source_type="manual",
        last_generation_artifact_id=None,
        content_format_mix=list(draft.content_format_mix),
        target_skill_slugs=list(draft.target_skill_slugs),
        target_competency_slugs=list(draft.target_competency_slugs),
        rubric_ids=list(draft.rubric_ids),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    prompt_commands = [
        PromptItemCreateCommand.model_validate(prompt_item.model_dump()) for prompt_item in draft.prompt_items
    ]
    for prompt_command in prompt_commands:
        validate_prompt_command(session, collection_record, prompt_command)
    validate_generated_prompt_item_uniqueness(
        existing_prompt_items=[],
        generated_commands=prompt_commands,
    )
    for scenario in draft.scenarios:
        validate_scenario_command(
            session,
            collection_record,
            ScenarioCreateCommand.model_validate(scenario.model_dump()),
        )
    expected_prompt_version = (
        config.structured_prompt_version
        if structured_command is not None
        else config.chat_prompt_version
    )
    if draft.prompt_version != expected_prompt_version:
        raise validation_error(
            "Generated draft prompt version did not match the requested contract",
            code="SS-VALIDATION-072",
            details={"expected": expected_prompt_version, "actual": draft.prompt_version},
        )
    if list(draft.content_format_mix) != list(source_command.content_format_mix):
        raise validation_error(
            "Generated draft content formats drifted from the request",
            code="SS-VALIDATION-050",
        )
    if list(draft.target_skill_slugs) != list(source_command.target_skill_slugs):
        raise validation_error("Generated draft target skills drifted from the request", code="SS-VALIDATION-051")
    if list(draft.target_competency_slugs) != list(source_command.target_competency_slugs):
        raise validation_error(
            "Generated draft target competencies drifted from the request",
            code="SS-VALIDATION-052",
        )
    if list(draft.rubric_ids) != list(source_command.rubric_ids):
        raise validation_error("Generated draft rubrics drifted from the request", code="SS-VALIDATION-053")


def validate_prompt_item_plan_batch(
    *,
    config: CatalogGenerationRuntimeConfig,
    llm_provider: LLMProvider,
    batch: GeneratedPromptItemPlanBatch,
    mode: str,
    resolved_model_slug: str,
    counts: dict[str, Any],
) -> None:
    expected_prompt_version = (
        config.prompt_item_structured_prompt_version
        if mode == "prompt_items_structured"
        else config.prompt_item_chat_prompt_version
    )
    if batch.prompt_version != expected_prompt_version:
        raise validation_error(
            "Generated prompt-item plan prompt version did not match the requested contract",
            code="SS-VALIDATION-073",
            details={"expected": expected_prompt_version, "actual": batch.prompt_version},
        )
    if batch.provider != llm_provider.provider_name:
        raise validation_error(
            "Generated prompt-item plan provider did not match the executing provider",
            code="SS-VALIDATION-074",
            details={"expected": llm_provider.provider_name, "actual": batch.provider},
        )
    if batch.model_slug != resolved_model_slug:
        raise validation_error(
            "Generated prompt-item plan model slug did not match the executing model",
            code="SS-VALIDATION-075",
            details={"expected": resolved_model_slug, "actual": batch.model_slug},
        )
    expected_total = int(counts["quick_practice_prompt_count"]) + int(counts["interview_prompt_count"])
    if len(batch.prompt_items) != expected_total:
        raise validation_error(
            "Generated prompt-item plan count did not match the request",
            code="SS-VALIDATION-076",
            details={"expected": expected_total, "actual": len(batch.prompt_items)},
        )
    actual_quick = sum(1 for item in batch.prompt_items if item.prompt_type == "quick_practice_prompt")
    actual_interview = sum(1 for item in batch.prompt_items if item.prompt_type == "interview_prompt")
    if actual_quick != int(counts["quick_practice_prompt_count"]) or actual_interview != int(counts["interview_prompt_count"]):
        raise validation_error(
            "Generated prompt-item plan distribution did not match the request",
            code="SS-VALIDATION-077",
            details={
                "expected_quick_practice_prompt_count": counts["quick_practice_prompt_count"],
                "actual_quick_practice_prompt_count": actual_quick,
                "expected_interview_prompt_count": counts["interview_prompt_count"],
                "actual_interview_prompt_count": actual_interview,
            },
        )
