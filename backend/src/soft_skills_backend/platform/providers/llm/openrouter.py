"""OpenRouter LLM provider implementation."""

from __future__ import annotations

from typing import Any, ClassVar

from soft_skills_backend.config import LLMTaskKind, Settings
from soft_skills_backend.platform.providers.llm.openai_compatible import (
    OpenAICompatibleLLMProvider,
)


class OpenRouterLLMProvider(OpenAICompatibleLLMProvider):
    """OpenRouter provider using OpenAI-compatible endpoints.

    OpenRouter aggregates multiple LLM providers behind a unified API.
    See https://openrouter.ai for more information.
    """

    provider_name: ClassVar[str] = "openrouter"
    base_url: ClassVar[str] = "https://openrouter.ai/api/v1"
    default_model_slug: ClassVar[str] = "openai/gpt-4o"
    backup_model_slug: ClassVar[str | None] = None
    supports_structured_outputs: ClassVar[bool] = True

    def _get_api_key(self, settings: Settings) -> str | None:
        return settings.openrouter_api_key or settings.provider_api_key

    def _get_base_url(self, settings: Settings) -> str:
        return settings.openrouter_base_url or self.base_url

    def _get_task_model(self, settings: Settings, task: LLMTaskKind) -> str | None:
        return settings.get_llm_model_for_task(task)

    def _get_backup_model_slug(self, settings: Settings) -> str | None:
        return settings.llm_default_backup_model or self.backup_model_slug

    def _resolve_provider_name(self, settings: Settings) -> str:
        return self.provider_name


__all__ = ["OpenRouterLLMProvider"]
