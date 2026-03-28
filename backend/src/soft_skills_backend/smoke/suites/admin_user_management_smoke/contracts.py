"""Admin user management smoke result contracts."""

from __future__ import annotations

from pydantic import BaseModel


class AdminUserManagementSmokeResult(BaseModel):
    """Result of the admin user management smoke suite."""

    organisation_id: str
    admin_user_id: str
    member_user_id: str
    listed_users_count: int
    listed_users_total: int
    get_user_email: str
    updated_role: str
    suspended_user_id: str
    activated_user_id: str
    added_user_email: str
    added_user_id: str
    bulk_suspend_count: int
    bulk_activate_count: int
    user_activity_user_id: str
    user_activity_total_sessions: int
