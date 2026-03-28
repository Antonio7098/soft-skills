"""Prompt library smoke contracts."""

from __future__ import annotations

from pydantic import BaseModel


class PromptLibrarySmokeResult(BaseModel):
    """Result from a prompt library smoke run."""

    status: str
    prompt_name: str | None = None
    prompt_version: str | None = None
    prompt_type: str | None = None
    template_length: int | None = None
    variables_schema_fields: int | None = None
    render_latency_ms: int | None = None
    render_tokens: int | None = None
    lineage_prompt_version_id: int | None = None
    parent_version_id: int | None = None
