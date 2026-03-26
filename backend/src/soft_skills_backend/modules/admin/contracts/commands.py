"""Admin command contracts."""

from __future__ import annotations

from pydantic import BaseModel, field_validator


class AdminCollectionVerificationCommand(BaseModel):
    """Explicit admin verification transition request."""

    verification_state: str
    note: str | None = None

    @field_validator("verification_state")
    @classmethod
    def _require_state(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("verification_state must not be blank")
        return cleaned

    @field_validator("note")
    @classmethod
    def _normalize_note(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class AdminLearnerRelationshipCommand(BaseModel):
    """Admin-to-learner relationship assignment."""

    relationship_type: str

    @field_validator("relationship_type")
    @classmethod
    def _require_relationship_type(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("relationship_type must not be blank")
        return cleaned
