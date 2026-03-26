"""Organisation domain validators."""

from __future__ import annotations

from soft_skills_backend.platform.db.models import OrganisationMembershipRecord, OrganisationRecord
from soft_skills_backend.shared.auth import Actor
from soft_skills_backend.shared.errors import auth_error, validation_error


def validate_slug_uniqueness(session, slug: str, exclude_org_id: str | None = None) -> None:
    """Ensure slug is unique across organisations."""
    query = session.query(OrganisationRecord).filter(OrganisationRecord.slug == slug)
    if exclude_org_id:
        query = query.filter(OrganisationRecord.id != exclude_org_id)
    existing = query.first()
    if existing is not None:
        raise validation_error(
            "Organisation slug is already taken",
            code="SS-VALIDATION-066",
            details={"slug": slug},
        )


def require_org_admin(actor: Actor, organisation_id: str) -> None:
    """Require actor to be an admin of the specified organisation."""
    if actor.organisation_id == organisation_id and actor.is_org_admin:
        return
    raise auth_error(
        "Organisation admin access is required",
        code="SS-AUTH-006",
        status_code=403,
        details={"organisation_id": organisation_id},
    )


def require_org_member(actor: Actor, organisation_id: str) -> None:
    """Require actor to be a member of the specified organisation."""
    if actor.organisation_id == organisation_id and actor.organisation_role is not None:
        return
    raise auth_error(
        "Organisation membership is required",
        code="SS-AUTH-007",
        status_code=403,
        details={"organisation_id": organisation_id},
    )


def require_unique_org_membership(session, organisation_id: str, user_id: str) -> None:
    """Ensure user is not already a member of the organisation."""
    existing = (
        session.query(OrganisationMembershipRecord)
        .filter(
            OrganisationMembershipRecord.organisation_id == organisation_id,
            OrganisationMembershipRecord.user_id == user_id,
        )
        .first()
    )
    if existing is not None:
        raise validation_error(
            "User is already a member of this organisation",
            code="SS-VALIDATION-067",
            details={"organisation_id": organisation_id, "user_id": user_id},
        )


def validate_membership_role(role: str) -> None:
    """Validate membership role value."""
    if role not in ("admin", "member"):
        raise validation_error(
            "Invalid membership role",
            code="SS-VALIDATION-068",
            details={"role": role},
        )
