"""Contracts for generation cancellation smoke results."""

from __future__ import annotations

from pydantic import BaseModel


class GenerationCancellationSmokeResult(BaseModel):
    status: str
    generation_mode: str
    generation_id: str | None = None
    stream_token: str | None = None
    stages_received: list[str] | None = None
    cancel_stage: str | None = None
    final_status: str | None = None
    error: str | None = None
