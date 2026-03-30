"""Pydantic domain models for parent-child prompt/rubric versioning."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PromptVersion(BaseModel):
    """Child prompt version entity."""

    id: int
    prompt_id: str
    version: str
    template: str
    variables_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] | None = None
    status: str = "draft"
    parent_version_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class RubricVersion(BaseModel):
    """Child rubric version entity with embedded criteria."""

    id: int
    rubric_id: str
    version: str
    criteria: list[dict[str, Any]] = Field(default_factory=list)
    status: str = "draft"
    created_at: datetime | None = None
    updated_at: datetime | None = None
