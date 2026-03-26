"""Prompt library registration for catalog generation workflows."""

from __future__ import annotations

from soft_skills_backend.config import Settings
from soft_skills_backend.engines.config import load_catalog_generation_runtime_config
from soft_skills_backend.modules.practice.workflows.assessment import (
    PromptLibrary,
    PromptTemplate,
)
from soft_skills_backend.platform.providers.llm.prompts import (
    CREATOR_CHAT_COLLECTION_BLUEPRINT_PROMPT,
    CREATOR_CHAT_PROMPT_ITEM_PLAN_PROMPT,
    CREATOR_PROMPT_ITEM_WORKER_PROMPT,
    CREATOR_SCENARIO_WORKER_PROMPT,
    CREATOR_STRUCTURED_COLLECTION_BLUEPRINT_PROMPT,
    CREATOR_STRUCTURED_PROMPT_ITEM_PLAN_PROMPT,
)


def build_catalog_generation_prompt_library(settings: Settings) -> PromptLibrary:
    """Build the versioned prompt library for creator generation."""

    del settings
    config = load_catalog_generation_runtime_config()
    library = PromptLibrary()
    library.register(
        PromptTemplate(
            name=config.structured_prompt_name,
            version=config.structured_prompt_version,
            template=CREATOR_STRUCTURED_COLLECTION_BLUEPRINT_PROMPT,
        ),
        make_default=True,
    )
    library.register(
        PromptTemplate(
            name=config.chat_prompt_name,
            version=config.chat_prompt_version,
            template=CREATOR_CHAT_COLLECTION_BLUEPRINT_PROMPT,
        ),
        make_default=True,
    )
    library.register(
        PromptTemplate(
            name=config.prompt_item_structured_prompt_name,
            version=config.prompt_item_structured_prompt_version,
            template=CREATOR_STRUCTURED_PROMPT_ITEM_PLAN_PROMPT,
        ),
        make_default=True,
    )
    library.register(
        PromptTemplate(
            name=config.prompt_item_chat_prompt_name,
            version=config.prompt_item_chat_prompt_version,
            template=CREATOR_CHAT_PROMPT_ITEM_PLAN_PROMPT,
        ),
        make_default=True,
    )
    library.register(
        PromptTemplate(
            name=config.prompt_item_worker_prompt_name,
            version=config.prompt_item_worker_prompt_version,
            template=CREATOR_PROMPT_ITEM_WORKER_PROMPT,
        ),
        make_default=True,
    )
    library.register(
        PromptTemplate(
            name=config.scenario_worker_prompt_name,
            version=config.scenario_worker_prompt_version,
            template=CREATOR_SCENARIO_WORKER_PROMPT,
        ),
        make_default=True,
    )
    return library
