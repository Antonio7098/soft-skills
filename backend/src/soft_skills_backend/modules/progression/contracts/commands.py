"""Progression command contracts."""

from __future__ import annotations

from pydantic import BaseModel, field_validator


class ProgressRecalculationCommand(BaseModel):
    """Admin-triggered replay request for a learner."""

    learner_id: str
    reason: str

    @field_validator("learner_id", "reason")
    @classmethod
    def _require_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Value must not be blank")
        return cleaned
