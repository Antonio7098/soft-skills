"""Built-in prompt definitions seeded into the prompt registry."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from soft_skills_backend.config import Settings
from soft_skills_backend.modules.assistant.workflows.prompting import assistant_prompt_templates
from soft_skills_backend.modules.catalog.domain.models import (
    GeneratedCollectionBlueprint,
    GeneratedPromptItemDraft,
    GeneratedPromptItemPlanBatch,
    GeneratedScenarioQuestionDraft,
    GeneratedScenarioDraft,
    GeneratedScenarioShellDraft,
)
from soft_skills_backend.modules.catalog.workflows.generation.prompt_library import (
    catalog_generation_prompt_templates,
)


@dataclass(frozen=True, slots=True)
class BuiltinPromptDefinition:
    """One built-in prompt version that must exist in the registry."""

    name: str
    version: str
    prompt_type: str
    template: str
    variables_schema: dict[str, Any]
    output_schema: dict[str, Any] | None
    status: str = "published"


def built_in_prompt_definitions(settings: Settings) -> list[BuiltinPromptDefinition]:
    """Return the built-in prompts for assistant and catalog generation flows."""

    assistant_output_schemas = {
        "assistant_orchestrator": None,
        "assistant_final_response": None,
    }
    catalog_output_schemas = {
        "creator-collection-structured-blueprint": GeneratedCollectionBlueprint.model_json_schema(),
        "creator-collection-chat-blueprint": GeneratedCollectionBlueprint.model_json_schema(),
        "creator-prompt-items-structured-plan": GeneratedPromptItemPlanBatch.model_json_schema(),
        "creator-prompt-items-chat-plan": GeneratedPromptItemPlanBatch.model_json_schema(),
        "creator-prompt-item-worker": GeneratedPromptItemDraft.model_json_schema(),
        "creator-scenario-shell-worker": GeneratedScenarioShellDraft.model_json_schema(),
        "creator-scenario-question-worker": GeneratedScenarioQuestionDraft.model_json_schema(),
    }

    definitions: list[BuiltinPromptDefinition] = []
    for template in assistant_prompt_templates():
        definitions.append(
            BuiltinPromptDefinition(
                name=template.name,
                version=template.version,
                prompt_type="assistant",
                template=template.template,
                variables_schema=_variables_schema_for_template(template.template),
                output_schema=assistant_output_schemas.get(template.name),
            )
        )
    for template in catalog_generation_prompt_templates(settings):
        definitions.append(
            BuiltinPromptDefinition(
                name=template.name,
                version=template.version,
                prompt_type="generation",
                template=template.template,
                variables_schema=_variables_schema_for_template(template.template),
                output_schema=catalog_output_schemas.get(template.name),
            )
        )
    return definitions


def _variables_schema_for_template(template: str) -> dict[str, Any]:
    variables = sorted(set(re.findall(r"\{(\w+)\}", template)))
    return {
        "type": "object",
        "properties": {name: {"type": "string"} for name in variables},
        "required": variables,
    }
