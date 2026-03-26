"""Typed reviewed config artifacts used by engines and engine-backed workflows."""

from __future__ import annotations

from pydantic import BaseModel


class MarkingRuntimeConfig(BaseModel):
    """Reviewed config for the text-practice marking runtime."""

    prompt_name: str
    prompt_version: str
    output_schema_version: str
    config_version: str
    engine_version: str


class CatalogGenerationRuntimeConfig(BaseModel):
    """Reviewed config for creator-generation workflows."""

    structured_prompt_name: str
    structured_prompt_version: str
    chat_prompt_name: str
    chat_prompt_version: str
    output_schema_version: str
    config_version: str
