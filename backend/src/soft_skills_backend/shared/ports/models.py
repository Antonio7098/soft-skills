"""Ports domain models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ProviderCompletion(BaseModel):
    """Provider response normalized for structured validation."""

    content: str | dict[str, Any]
    model_slug: str
    usage: dict[str, int] = Field(default_factory=dict)
    raw_response: dict[str, Any] = Field(default_factory=dict)


class ProviderTextChunk(BaseModel):
    """Provider text-stream chunk normalized for live token delivery."""

    delta: str
    model_slug: str | None = None
    usage: dict[str, int] = Field(default_factory=dict)
    raw_event: dict[str, Any] = Field(default_factory=dict)
    done: bool = False
