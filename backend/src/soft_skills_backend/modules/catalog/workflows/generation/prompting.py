"""Prompt request builders and LLM execution helpers for catalog generation."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any, cast

from stageflow.agent.security import PromptSecurityError, PromptSecurityPolicy

from soft_skills_backend.engines.config.models import CatalogGenerationRuntimeConfig
from soft_skills_backend.modules.admin.workflows.prompt_render_stage import PromptRenderRequest
from soft_skills_backend.modules.catalog.contracts.collection_commands import (
    ChatCollectionGenerationCommand,
    StructuredCollectionGenerationCommand,
)
from soft_skills_backend.modules.catalog.contracts.prompt_item_commands import (
    ChatPromptItemGenerationCommand,
    StructuredPromptItemGenerationCommand,
)
from soft_skills_backend.modules.catalog.domain.constants import (
    ALLOWED_PROMPT_TYPES,
    ALLOWED_SCENARIO_ARTIFACT_TYPES,
)
from soft_skills_backend.modules.catalog.domain.models import GeneratedCollectionBlueprint
from soft_skills_backend.modules.practice.workflows.assessment import (
    StructuredOutputRejectionError,
    TypedLLMOutput,
    TypedLLMResult,
)
from soft_skills_backend.platform.db.models import CollectionRecord, PromptItemRecord
from soft_skills_backend.platform.providers.llm.prompts import (
    CREATOR_COLLECTION_BLUEPRINT_OUTPUT_FORMAT,
    CREATOR_PROMPT_ITEM_PLAN_OUTPUT_FORMAT,
)
from soft_skills_backend.platform.workflows.stageflow import (
    metadata_value,
    pipeline_run_id_from_context,
    request_id_from_context,
    user_id_from_context,
)
from soft_skills_backend.shared.errors import validation_error
from soft_skills_backend.shared.ports.llm import LLMProvider
from soft_skills_backend.shared.ports.telemetry import ProviderCallContext


def build_collection_blueprint_prompt_request(
    *,
    config: CatalogGenerationRuntimeConfig,
    llm_provider: LLMProvider,
    prompt_security_policy: PromptSecurityPolicy,
    structured_command: StructuredCollectionGenerationCommand | None,
    chat_command: ChatCollectionGenerationCommand | None,
    taxonomy_context: str,
    sanitize_text: Callable[[str], str],
) -> PromptRenderRequest:
    """Build the prompt render request for collection blueprint planning."""

    if structured_command is not None:
        return PromptRenderRequest(
            name=config.structured_prompt_name,
            version=config.structured_prompt_version,
            variables={
                "title_hint": structured_command.title_hint or "none",
                "target_audience": structured_command.target_audience,
                "difficulty": structured_command.difficulty,
                "content_format_mix": ", ".join(structured_command.content_format_mix),
                "target_skill_slugs": ", ".join(structured_command.target_skill_slugs),
                "target_competency_slugs": ", ".join(structured_command.target_competency_slugs),
                "rubric_ids": ", ".join(structured_command.rubric_ids),
                "taxonomy_context": taxonomy_context,
                "domain": structured_command.domain,
                "workplace_context": structured_command.workplace_context,
                "scenario_theme": structured_command.scenario_theme,
                "realism_notes": sanitize_text(json.dumps(structured_command.realism_notes)),
                "prompt_counts": json.dumps(
                    {
                        "quick_practice_prompt_count": structured_command.counts.quick_practice_prompt_count,
                        "interview_prompt_count": structured_command.counts.interview_prompt_count,
                    },
                    sort_keys=True,
                ),
                "scenario_count": structured_command.counts.scenario_count,
                "scenario_artifact_count": structured_command.counts.scenario_artifact_count,
                "allowed_prompt_types": ", ".join(sorted(ALLOWED_PROMPT_TYPES)),
                "allowed_artifact_types": ", ".join(sorted(ALLOWED_SCENARIO_ARTIFACT_TYPES)),
                "output_format": CREATOR_COLLECTION_BLUEPRINT_OUTPUT_FORMAT.format(
                    prompt_version=config.structured_prompt_version,
                    provider=llm_provider.provider_name,
                    model_slug=llm_provider.model_slug,
                ),
            },
        )

    assert chat_command is not None
    try:
        user_message, _ = prompt_security_policy.build_user_message(chat_command.prompt)
    except PromptSecurityError as exc:
        raise validation_error(
            "Chat generation prompt was blocked by the prompt-security policy",
            code="SS-VALIDATION-048",
            details=exc.report.to_dict(),
        ) from exc
    return PromptRenderRequest(
        name=config.chat_prompt_name,
        version=config.chat_prompt_version,
        variables={
            "target_audience": chat_command.target_audience,
            "difficulty": chat_command.difficulty,
            "content_format_mix": ", ".join(chat_command.content_format_mix),
            "target_skill_slugs": ", ".join(chat_command.target_skill_slugs),
            "target_competency_slugs": ", ".join(chat_command.target_competency_slugs),
            "rubric_ids": ", ".join(chat_command.rubric_ids),
            "taxonomy_context": taxonomy_context,
            "requested_counts": json.dumps(chat_command.counts.model_dump(mode="json"), sort_keys=True),
            "allowed_prompt_types": ", ".join(sorted(ALLOWED_PROMPT_TYPES)),
            "allowed_artifact_types": ", ".join(sorted(ALLOWED_SCENARIO_ARTIFACT_TYPES)),
            "user_prompt": user_message["content"],
            "output_format": CREATOR_COLLECTION_BLUEPRINT_OUTPUT_FORMAT.format(
                prompt_version=config.chat_prompt_version,
                provider=llm_provider.provider_name,
                model_slug=llm_provider.model_slug,
            ),
        },
    )


async def generate_collection_blueprint_from_prompt(
    *,
    ctx: Any,
    config: CatalogGenerationRuntimeConfig,
    llm_provider: LLMProvider,
    blueprint_output: TypedLLMOutput,
    rendered_prompt: Any,
    structured_command: StructuredCollectionGenerationCommand | None,
) -> TypedLLMResult:
    """Run the collection blueprint LLM call from a registry-rendered prompt."""

    operation = (
        "catalog_structured_blueprint_generation"
        if structured_command is not None
        else "catalog_chat_blueprint_generation"
    )
    prompt_version = (
        config.structured_prompt_version
        if structured_command is not None
        else config.chat_prompt_version
    )
    try:
        typed_result = await blueprint_output.generate(
            llm_provider,
            messages=[
                {
                    "role": "system",
                    "content": "Plan a realistic SoftSkills collection blueprint. Return JSON only.",
                },
                {"role": "user", "content": rendered_prompt.content},
            ],
            call_context=ProviderCallContext(
                operation=operation,
                request_id=request_id_from_context(ctx),
                trace_id=metadata_value(ctx, "trace_id"),
                pipeline_run_id=pipeline_run_id_from_context(ctx),
                workflow_id=metadata_value(ctx, "workflow_id"),
                user_id=user_id_from_context(ctx),
            ),
        )
    except StructuredOutputRejectionError as exc:
        raise validation_error(
            exc.app_error.message,
            code=exc.app_error.code,
            details={**(dict(exc.app_error.details or {})), "raw_payload": exc.raw_payload},
        ) from exc
    blueprint = cast(GeneratedCollectionBlueprint, typed_result.parsed)
    if blueprint.prompt_version != prompt_version:
        raise validation_error(
            "Generated blueprint prompt version did not match the requested contract",
            code="SS-VALIDATION-049",
            details={"expected": prompt_version, "actual": blueprint.prompt_version},
        )
    return typed_result


def build_prompt_item_plan_prompt_request(
    *,
    config: CatalogGenerationRuntimeConfig,
    llm_provider: LLMProvider,
    prompt_security_policy: PromptSecurityPolicy,
    collection: CollectionRecord,
    existing_prompt_items: list[PromptItemRecord],
    structured_command: StructuredPromptItemGenerationCommand | None,
    chat_command: ChatPromptItemGenerationCommand | None,
    requested_skill_slugs: list[str],
    compatible_rubric_ids: list[str],
    sanitize_text: Callable[[str], str],
) -> PromptRenderRequest:
    """Build the prompt render request for prompt-item planning."""

    common_variables: dict[str, object] = {
        "collection_title": collection.title,
        "collection_summary": collection.summary,
        "target_audience": collection.target_audience,
        "difficulty": collection.difficulty,
        "allowed_prompt_types": ", ".join(
            format_slug
            for format_slug in collection.content_format_mix
            if format_slug in ALLOWED_PROMPT_TYPES
        ),
        "collection_skill_slugs": ", ".join(collection.target_skill_slugs),
        "compatible_rubric_ids": ", ".join(compatible_rubric_ids),
        "existing_prompt_fingerprints": json.dumps(
            [{"title": item.title, "prompt_type": item.prompt_type} for item in existing_prompt_items],
            sort_keys=True,
        ),
        "requested_skill_slugs": ", ".join(requested_skill_slugs),
    }
    if structured_command is not None:
        return PromptRenderRequest(
            name=config.prompt_item_structured_prompt_name,
            version=config.prompt_item_structured_prompt_version,
            variables={
                **common_variables,
                "title_hint": structured_command.title_hint or "none",
                "workplace_context": structured_command.workplace_context,
                "generation_focus": structured_command.generation_focus,
                "realism_notes": sanitize_text(json.dumps(structured_command.realism_notes)),
                "requested_counts": json.dumps(
                    structured_command.counts.model_dump(mode="json"), sort_keys=True
                ),
                "output_format": CREATOR_PROMPT_ITEM_PLAN_OUTPUT_FORMAT.format(
                    prompt_version=config.prompt_item_structured_prompt_version,
                    provider=llm_provider.provider_name,
                    model_slug=llm_provider.model_slug,
                ),
            },
        )

    assert chat_command is not None
    try:
        user_message, _ = prompt_security_policy.build_user_message(chat_command.prompt)
    except PromptSecurityError as exc:
        raise validation_error(
            "Prompt-item generation prompt was blocked by the prompt-security policy",
            code="SS-VALIDATION-066",
            details=exc.report.to_dict(),
        ) from exc
    return PromptRenderRequest(
        name=config.prompt_item_chat_prompt_name,
        version=config.prompt_item_chat_prompt_version,
        variables={
            **common_variables,
            "requested_counts": json.dumps(chat_command.counts.model_dump(mode="json"), sort_keys=True),
            "user_prompt": user_message["content"],
            "output_format": CREATOR_PROMPT_ITEM_PLAN_OUTPUT_FORMAT.format(
                prompt_version=config.prompt_item_chat_prompt_version,
                provider=llm_provider.provider_name,
                model_slug=llm_provider.model_slug,
            ),
        },
    )


async def generate_prompt_item_plan_batch_from_prompt(
    *,
    ctx: Any,
    structured_command: StructuredPromptItemGenerationCommand | None,
    config: CatalogGenerationRuntimeConfig,
    llm_provider: LLMProvider,
    prompt_item_plan_output: TypedLLMOutput,
    rendered_prompt: Any,
) -> TypedLLMResult:
    """Run the prompt-item planning LLM call from a registry-rendered prompt."""

    operation = (
        "catalog_prompt_item_structured_planning"
        if structured_command is not None
        else "catalog_prompt_item_chat_planning"
    )
    try:
        return await prompt_item_plan_output.generate(
            llm_provider,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Plan realistic SoftSkills prompt items for an existing collection. "
                        "Return JSON only."
                    ),
                },
                {"role": "user", "content": rendered_prompt.content},
            ],
            call_context=ProviderCallContext(
                operation=operation,
                request_id=request_id_from_context(ctx),
                trace_id=metadata_value(ctx, "trace_id"),
                pipeline_run_id=pipeline_run_id_from_context(ctx),
                workflow_id=metadata_value(ctx, "workflow_id"),
                user_id=user_id_from_context(ctx),
            ),
        )
    except StructuredOutputRejectionError as exc:
        raise validation_error(
            exc.app_error.message,
            code=exc.app_error.code,
            details={**(dict(exc.app_error.details or {})), "raw_payload": exc.raw_payload},
        ) from exc
