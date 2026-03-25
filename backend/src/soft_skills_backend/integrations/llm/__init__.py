"""LLM provider integrations."""

from soft_skills_backend.integrations.llm.openai_compatible import (
    OpenAICompatibleLLMProvider,
    ResolvedLLMProviderConfig,
    resolve_llm_provider_config,
)

__all__ = [
    "OpenAICompatibleLLMProvider",
    "ResolvedLLMProviderConfig",
    "resolve_llm_provider_config",
]
