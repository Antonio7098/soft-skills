"""Admin command contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


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


class AdminFeatureCollectionCommand(BaseModel):
    """Admin feature/highlight collection request."""

    featured: bool


class RubricCriterionLevelCommand(BaseModel):
    """One scored rubric level."""

    level: int = Field(ge=1, le=5)
    description: str
    examples: list[str] = Field(min_length=1)


class RubricCriterionCommand(BaseModel):
    """One rubric criterion definition."""

    criterion_ref: str
    skill_slug: str
    title: str
    description: str
    weight: float = Field(default=1.0, gt=0)
    required: bool = True
    position: int = 0
    levels: list[RubricCriterionLevelCommand] = Field(min_length=1)


class CreateRubricCommand(BaseModel):
    """Create a new rubric."""

    rubric_id: str
    family: str
    version: str
    content_type: str
    schema_version: str
    name: str
    criteria: list[RubricCriterionCommand] = Field(min_length=1)


class UpdateRubricCommand(BaseModel):
    """Update an existing rubric."""

    family: str | None = None
    version: str | None = None
    name: str | None = None


class RubricCriterionUpdateCommand(BaseModel):
    """Update a rubric criterion."""

    title: str | None = None
    description: str | None = None
    weight: float | None = Field(default=None, gt=0)
    required: bool | None = None
    position: int | None = None
    levels: list[RubricCriterionLevelCommand] | None = None


class CreateRubricCriterionCommand(BaseModel):
    """Add a new criterion to an existing rubric."""

    criterion_ref: str
    skill_slug: str
    title: str
    description: str
    weight: float = Field(default=1.0, gt=0)
    required: bool = True
    position: int = 0
    levels: list[RubricCriterionLevelCommand] = Field(min_length=1)
