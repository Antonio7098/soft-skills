"""Groq LLM provider implementation."""

from __future__ import annotations

from typing import Any, ClassVar

from soft_skills_backend.config import LLMTaskKind, Settings
from soft_skills_backend.platform.providers.llm.openai_compatible import (
    OpenAICompatibleLLMProvider,
)


class GroqLLMProvider(OpenAICompatibleLLMProvider):
    """Groq API provider using OpenAI-compatible endpoints.

    Groq provides fast LLM inference with OpenAI-compatible API.
    See https://docs.groq.com for more information.
    """

    provider_name: ClassVar[str] = "groq"
    base_url: ClassVar[str] = "https://api.groq.com/openai/v1"
    default_model_slug: ClassVar[str] = "llama-3.3-70b-versatile"
    backup_model_slug: ClassVar[str | None] = "llama-3.1-8b-instant"
    supports_structured_outputs: ClassVar[bool] = True

    def _get_api_key(self, settings: Settings) -> str | None:
        return settings.groq_api_key or settings.provider_api_key

    def _get_base_url(self, settings: Settings) -> str:
        return settings.groq_base_url or self.base_url

    def _get_model_slug(self, settings: Settings, task: LLMTaskKind | None) -> str:
        if task is not None:
            model = self._get_task_model(settings, task)
            if model:
                return model
        return settings.groq_default_model or self.default_model_slug

    def _get_task_model(self, settings: Settings, task: LLMTaskKind) -> str | None:
        match task:
            case LLMTaskKind.ASSISTANT:
                return settings.groq_llm_assistant_model
            case LLMTaskKind.ADMIN_AGENT:
                return settings.groq_llm_admin_agent_model
            case LLMTaskKind.MARKING_PER_SKILL:
                return settings.groq_llm_marking_per_skill_model
            case LLMTaskKind.MARKING_AGGREGATION:
                return settings.groq_llm_marking_aggregation_model
            case LLMTaskKind.CREATOR_BLUEPRINT:
                return settings.groq_llm_creator_blueprint_model
            case LLMTaskKind.CREATOR_PROMPT_ITEM:
                return settings.groq_llm_creator_prompt_item_model
            case LLMTaskKind.CREATOR_SCENARIO:
                return settings.groq_llm_creator_scenario_model
        return None

    def _get_backup_model_slug(self, settings: Settings) -> str | None:
        return settings.groq_default_backup_model or self.backup_model_slug

    def _resolve_provider_name(self, settings: Settings) -> str:
        return self.provider_name


__all__ = ["GroqLLMProvider"]
