"""Typed reviewed config artifacts used by engines and engine-backed workflows."""

from __future__ import annotations

from pydantic import BaseModel


class MarkingRuntimeConfig(BaseModel):
    """Reviewed config for the text-practice marking runtime."""

    per_skill_prompt_name: str
    per_skill_prompt_version: str
    aggregation_prompt_name: str
    aggregation_prompt_version: str
    per_skill_output_schema_version: str
    aggregation_output_schema_version: str
    output_schema_version: str
    config_version: str
    engine_version: str
    max_parallel_skill_children: int

    @property
    def prompt_name(self) -> str:
        return self.per_skill_prompt_name

    @property
    def prompt_version(self) -> str:
        return self.per_skill_prompt_version


class CatalogGenerationRuntimeConfig(BaseModel):
    """Reviewed config for creator-generation workflows."""

    structured_prompt_name: str
    structured_prompt_version: str
    chat_prompt_name: str
    chat_prompt_version: str
    prompt_item_structured_prompt_name: str
    prompt_item_structured_prompt_version: str
    prompt_item_chat_prompt_name: str
    prompt_item_chat_prompt_version: str
    prompt_item_worker_prompt_name: str
    prompt_item_worker_prompt_version: str
    scenario_shell_worker_prompt_name: str
    scenario_shell_worker_prompt_version: str
    scenario_question_worker_prompt_name: str
    scenario_question_worker_prompt_version: str
    output_schema_version: str
    config_version: str
    max_parallel_prompt_item_children: int
    max_parallel_scenario_children: int
