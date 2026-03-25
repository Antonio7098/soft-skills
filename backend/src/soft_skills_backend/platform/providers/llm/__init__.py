"""LLM provider integrations."""

from soft_skills_backend.platform.providers.llm.openai_compatible import (
    OpenAICompatibleLLMProvider,
    ResolvedLLMProviderConfig,
    resolve_llm_provider_config,
)

__all__ = [
    "OpenAICompatibleLLMProvider",
    "ResolvedLLMProviderConfig",
    "resolve_llm_provider_config",
]
