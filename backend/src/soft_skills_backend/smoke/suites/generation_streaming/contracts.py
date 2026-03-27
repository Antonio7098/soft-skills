"""Contracts for generation streaming smoke results."""

from __future__ import annotations

from pydantic import BaseModel


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
    final_status: str | None = None
    error: str | None = None
