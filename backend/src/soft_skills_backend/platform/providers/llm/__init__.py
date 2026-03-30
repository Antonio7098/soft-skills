"""LLM provider integrations."""

from soft_skills_backend.platform.providers.llm.groq import GroqLLMProvider
from soft_skills_backend.platform.providers.llm.openai_compatible import (
    OpenAICompatibleLLMProvider,
    ResolvedLLMProviderConfig,
    build_llm_provider,
    resolve_llm_provider_config,
)
from soft_skills_backend.platform.providers.llm.openrouter import OpenRouterLLMProvider

__all__ = [
    "OpenAICompatibleLLMProvider",
    "GroqLLMProvider",
    "OpenRouterLLMProvider",
    "ResolvedLLMProviderConfig",
    "build_llm_provider",
    "resolve_llm_provider_config",
]
