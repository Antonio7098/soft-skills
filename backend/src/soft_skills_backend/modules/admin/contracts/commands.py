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


class CreatePromptCommand(BaseModel):
    """Create a new prompt version."""

    name: str
    version: str
    prompt_type: str
    template: str
    variables_schema: dict[str, object]
    output_schema: dict[str, object] | None = None
    parent_version_id: int | None = None


class UpdatePromptCommand(BaseModel):
    """Update an existing draft prompt version."""

    template: str | None = None
    variables_schema: dict[str, object] | None = None
    output_schema: dict[str, object] | None = None


class PublishPromptCommand(BaseModel):
    """Publish a prompt version."""

    pass


class ArchivePromptCommand(BaseModel):
    """Archive a prompt version."""

    pass


class ComparePromptsCommand(BaseModel):
    """Compare two versions of the same prompt."""

    name: str
    version_a: str
    version_b: str


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
    """Create a new rubric with initial version."""

    rubric_id: str
    skill_slug: str
    organisation_id: str | None = None
    name: str
    description: str | None = None
    content_type: str
    schema_version: str
    version: str
    criteria: list[RubricCriterionCommand] = Field(min_length=1)


class UpdateRubricCommand(BaseModel):
    """Update an existing rubric."""

    name: str | None = None
    description: str | None = None


class CreateRubricVersionCommand(BaseModel):
    """Create a new rubric version."""

    version: str
    criteria: list[RubricCriterionCommand] = Field(min_length=1)


class RubricCriterionUpdateCommand(BaseModel):
    """Update a rubric criterion (embedded in version)."""

    criterion_ref: str
    title: str | None = None
    description: str | None = None
    weight: float | None = Field(default=None, gt=0)
    required: bool | None = None
    position: int | None = None
    levels: list[RubricCriterionLevelCommand] | None = None


class CreateRubricCriterionCommand(BaseModel):
    """Add a new criterion to an existing rubric version."""

    criterion_ref: str
    skill_slug: str
    title: str
    description: str
    weight: float = Field(default=1.0, gt=0)
    required: bool = True
    position: int = 0
    levels: list[RubricCriterionLevelCommand] = Field(min_length=1)


class AdminUserRoleCommand(BaseModel):
    """Change user role within an organisation."""

    role: str

    @field_validator("role")
    @classmethod
    def _require_valid_role(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in ("admin", "member"):
            raise ValueError("role must be 'admin' or 'member'")
        return cleaned


class AdminUserStatusCommand(BaseModel):
    """Toggle user active status."""

    is_active: bool


class AdminAddUserCommand(BaseModel):
    """Add a user to an organisation."""

    email: str
    role: str = "member"

    @field_validator("email")
    @classmethod
    def _require_valid_email(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if not cleaned:
            raise ValueError("email must not be blank")
        if "@" not in cleaned:
            raise ValueError("email must be a valid email address")
        return cleaned

    @field_validator("role")
    @classmethod
    def _require_valid_role(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in ("admin", "member"):
            raise ValueError("role must be 'admin' or 'member'")
        return cleaned


class BulkUserOperationCommand(BaseModel):
    """Bulk user operations."""

    user_ids: list[str] = Field(min_length=1, max_length=100)
    operation: str
    payload: dict[str, object] | None = None

    @field_validator("operation")
    @classmethod
    def _require_valid_operation(cls, value: str) -> str:
        cleaned = value.strip().lower()
        valid_operations = ("suspend", "activate", "change_role", "export")
        if cleaned not in valid_operations:
            raise ValueError(f"operation must be one of: {', '.join(valid_operations)}")
        return cleaned

    @field_validator("user_ids")
    @classmethod
    def _require_user_ids(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("user_ids must not be empty")
        return value
