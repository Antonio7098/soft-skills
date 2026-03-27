"""Contracts for generation streaming smoke results."""

from __future__ import annotations

from pydantic import BaseModel


class BlueprintPayload(BaseModel):
    title: str | None = None
    summary: str | None = None
    prompt_items_count: int | None = None
    scenarios_count: int | None = None
    model_slug: str | None = None


class PromptItemPayload(BaseModel):
    title: str | None = None
    prompt_type: str | None = None
    difficulty: str | None = None


class GenerationStreamingSmokeResult(BaseModel):
    status: str
    generation_mode: str
    generation_id: str | None = None
    stream_token: str | None = None
    collection_id: str | None = None
    provider: str | None = None
    model_slug: str | None = None
    generation_artifact_id: str | None = None
    stages_received: list[str] | None = None
    blueprint: BlueprintPayload | None = None
    prompt_items: list[PromptItemPayload] | None = None
    final_status: str | None = None
    error: str | None = None
