"""Organisation command contracts."""

from __future__ import annotations

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
