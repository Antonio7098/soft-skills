"""Admin-to-learner relationship rules."""

from __future__ import annotations

from soft_skills_backend.shared.errors import domain_error, validation_error

ALLOWED_ADMIN_RELATIONSHIP_TYPES: set[str] = {"manager", "educator", "coach"}


def validate_admin_relationship_type(relationship_type: str) -> None:
    """Validate the admin relationship type."""

    if relationship_type not in ALLOWED_ADMIN_RELATIONSHIP_TYPES:
        raise validation_error(
            "Unsupported admin relationship type",
            code="SS-VALIDATION-051",
            details={"relationship_type": relationship_type},
        )


def validate_admin_relationship_target(*, learner_user_id: str, admin_user_id: str) -> None:
    """Prevent nonsensical self-relationships."""

    if learner_user_id == admin_user_id:
        raise domain_error(
            "Admin relationship target must be a different learner",
            code="SS-DOMAIN-031",
            details={"learner_user_id": learner_user_id, "admin_user_id": admin_user_id},
        )
