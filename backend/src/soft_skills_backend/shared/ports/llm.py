"""Shared LLM provider contracts."""

from __future__ import annotations

from typing import Protocol

from soft_skills_backend.shared.ports.models import ProviderCompletion
from soft_skills_backend.shared.ports.telemetry import ProviderCallContext


class LLMProvider(Protocol):
    """Swappable low-level provider contract for JSON completions."""

    @property
    def provider_name(self) -> str: ...

    @property
    def model_slug(self) -> str: ...

    async def complete_json(
        self,
        *,
        messages: list[dict[str, str]],
        call_context: ProviderCallContext,
    ) -> ProviderCompletion: ...


__all__ = ["LLMProvider", "ProviderCallContext", "ProviderCompletion"]
