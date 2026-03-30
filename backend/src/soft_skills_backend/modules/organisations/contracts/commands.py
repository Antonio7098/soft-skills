"""Organisation command contracts."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class CreateOrganisationCommand(BaseModel):
    """Create a new organisation."""

    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=64)

    @field_validator("name", "slug")
    @classmethod
    def _strip_whitespace(cls, value: str) -> str:
        return value.strip()

    @field_validator("slug")
    @classmethod
    def _validate_slug(cls, value: str) -> str:
        cleaned = value.lower().replace("_", "-")
        if not cleaned.replace("-", "").isalnum():
            raise ValueError("slug must be alphanumeric with optional hyphens")
        return cleaned


class UpdateOrganisationCommand(BaseModel):
    """Update an existing organisation."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = Field(default=None, min_length=1, max_length=64)

    @field_validator("name", "slug")
    @classmethod
    def _strip_whitespace(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip()

    @field_validator("slug")
    @classmethod
    def _validate_slug(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.lower().replace("_", "-")
        if not cleaned.replace("-", "").isalnum():
            raise ValueError("slug must be alphanumeric with optional hyphens")
        return cleaned


class AddMemberCommand(BaseModel):
    """Add a member to an organisation."""

    user_id: str = Field(..., min_length=1)
    role: str = Field(..., pattern="^(admin|member)$")

    @field_validator("user_id")
    @classmethod
    def _strip_user_id(cls, value: str) -> str:
        return value.strip()


class UpdateMemberCommand(BaseModel):
    """Update a member's role in an organisation."""

    role: str = Field(..., pattern="^(admin|member)$")


class CreateOrgSkillCommand(BaseModel):
    """Create an org-specific skill."""

    slug: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=255)
    description: str


class UpdateOrgSkillCommand(BaseModel):
    """Update an org-specific skill."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class CreateOrgCompetencyCommand(BaseModel):
    """Create an org-specific competency."""

    slug: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=255)
    description: str
    skill_slugs: list[str] = Field(default_factory=list)


class UpdateOrgCompetencyCommand(BaseModel):
    """Update an org-specific competency."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    skill_slugs: list[str] | None = None


class CreateOrgRubricCommand(BaseModel):
    """Create an org-specific rubric."""

    rubric_id: str = Field(..., min_length=1, max_length=128)
    skill_slug: str = Field(..., min_length=1, max_length=64)
    version: str = Field(..., min_length=1, max_length=32)
    content_type: str = Field(..., min_length=1, max_length=64)
    schema_version: str = Field(..., min_length=1, max_length=32)
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None)
    criteria: list[dict[str, Any]] = Field(default_factory=list)


class UpdateOrgRubricCommand(BaseModel):
    """Update an org-specific rubric."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None)
