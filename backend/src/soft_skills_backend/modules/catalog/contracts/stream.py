"""Generation websocket event contracts."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class GenerationStage(StrEnum):
    PENDING = "pending"
    INPUT_GUARD = "input_guard"
    BLUEPRINT_TRANSFORM = "blueprint_transform"
    BLUEPRINT_GUARD = "blueprint_guard"
    PROMPT_ITEMS_WORK = "prompt_items_work"
    SCENARIOS_WORK = "scenarios_work"
    ASSEMBLE_TRANSFORM = "assemble_transform"
    OUTPUT_GUARD = "output_guard"
    PERSISTENCE_WORK = "persistence_work"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class GenerationStreamEvent(BaseModel):
    event_id: str
    generation_id: str
    type: str
    stage: GenerationStage
    sequence_number: int
    emitted_at: datetime
    progress_percent: float = 0.0
    payload: dict[str, Any] = Field(default_factory=dict)


class GenerationControlMessage(BaseModel):
    action: str
    reason: str | None = None
