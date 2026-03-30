"""Shared LLM provider contracts."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol

from soft_skills_backend.shared.ports.models import (
    JsonSchemaResponseFormat,
    ProviderCompletion,
    ProviderToolCompletion,
    ProviderToolDefinition,
    ProviderTextChunk,
)
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
        messages: list[dict[str, object]],
        call_context: ProviderCallContext,
        response_schema: JsonSchemaResponseFormat | None = None,
        timeout_seconds: float | None = None,
    ) -> ProviderCompletion: ...

    async def complete_with_tools(
        self,
        *,
        messages: list[dict[str, object]],
        tools: list[ProviderToolDefinition],
        call_context: ProviderCallContext,
        timeout_seconds: float | None = None,
        tool_choice: str | None = None,
    ) -> ProviderToolCompletion: ...

    def stream_text(
        self,
        *,
        messages: list[dict[str, object]],
        call_context: ProviderCallContext,
    ) -> AsyncIterator[ProviderTextChunk]: ...


__all__ = [
    "LLMProvider",
    "ProviderCallContext",
    "ProviderCompletion",
    "ProviderToolCompletion",
    "ProviderToolDefinition",
    "ProviderTextChunk",
]
