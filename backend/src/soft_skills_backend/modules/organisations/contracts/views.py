"""Organisation view contracts."""

from __future__ import annotations

from pydantic import BaseModel


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
