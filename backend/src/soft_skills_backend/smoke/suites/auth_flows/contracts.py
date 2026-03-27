"""Auth flows smoke result contracts."""

from __future__ import annotations

from pydantic import BaseModel


class AuthFlowsSmokeResult(BaseModel):
    """Result of the auth flows smoke suite."""

    registered_user_id: str
    registered_email: str
    profile_display_name: str
    profile_goals: list[str]
    updated_target_role: str | None
    missing_header_status: int
    missing_header_error_code: str
    invalid_user_status: int
    invalid_user_error_code: str
    duplicate_email_status: int
    duplicate_email_error_code: str
    org_non_admin_status: int
    org_non_admin_error_code: str
