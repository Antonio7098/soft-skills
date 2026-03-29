"""Organisation view contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field


class OrganisationView(BaseModel):
    """Organisation details."""

    id: str
    name: str
    slug: str
    created_at: str
    updated_at: str


class OrganisationMemberView(BaseModel):
    """Organisation membership details."""

    organisation_id: str
    user_id: str
    role: str
    joined_at: str


class OrganisationListView(BaseModel):
    """Compact organisation listing."""

    id: str
    name: str
    slug: str
    member_count: int = 0


class OrgSkillView(BaseModel):
    """Org-specific skill view."""

    slug: str
    name: str
    description: str
    organisation_id: str


class OrgCompetencyView(BaseModel):
    """Org-specific competency view."""

    slug: str
    name: str
    description: str
    skill_slugs: list[str] = Field(default_factory=list)
    organisation_id: str


class OrgRubricView(BaseModel):
    """Org-specific rubric view."""

    rubric_id: str
    family: str
    version: str
    content_type: str
    schema_version: str
    name: str
    criteria: list[str] = Field(default_factory=list)
    organisation_id: str
