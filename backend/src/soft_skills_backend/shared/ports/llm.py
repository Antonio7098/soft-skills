"""Shared LLM provider contracts."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol

from soft_skills_backend.shared.ports.models import ProviderCompletion, ProviderTextChunk
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

    def stream_text(
        self,
        *,
        messages: list[dict[str, str]],
        call_context: ProviderCallContext,
    ) -> AsyncIterator[ProviderTextChunk]: ...


__all__ = ["LLMProvider", "ProviderCallContext", "ProviderCompletion", "ProviderTextChunk"]
