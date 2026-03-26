"""Admin verification rules."""

from __future__ import annotations

from soft_skills_backend.shared.errors import domain_error, validation_error

ALLOWED_ADMIN_VERIFICATION_STATES: set[str] = {"unverified", "verified", "rejected"}


def validate_admin_verification_transition(
    *,
    lifecycle_state: str,
    current_state: str,
    next_state: str,
    note: str | None,
    collection_id: str,
) -> None:
    """Validate a collection verification transition."""

    if next_state not in ALLOWED_ADMIN_VERIFICATION_STATES:
        raise validation_error(
            "Unsupported admin verification state",
            code="SS-VALIDATION-049",
            details={"verification_state": next_state},
        )
    if lifecycle_state != "published_public":
        raise domain_error(
            "Only publicly published collections can be reviewed",
            code="SS-DOMAIN-029",
            details={"collection_id": collection_id, "lifecycle_state": lifecycle_state},
        )
    if next_state == current_state:
        raise domain_error(
            "Collection is already in the requested verification state",
            code="SS-DOMAIN-027",
            details={"collection_id": collection_id, "verification_state": current_state},
        )
    if next_state == "rejected" and note is None:
        raise validation_error(
            "Rejected verification decisions require an audit note",
            code="SS-VALIDATION-050",
            details={"collection_id": collection_id},
        )
