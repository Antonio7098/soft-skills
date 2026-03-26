"""Organisation smoke result contracts."""

from __future__ import annotations

from pydantic import BaseModel


class OrganisationSmokeResult(BaseModel):
    """Result of the organisation smoke suite."""

    organisation_id: str
    organisation_name: str
    organisation_slug: str
    member_count: int
    admin_id: str
    member_id: str
    updated_org_name: str
    listed_members_count: int
