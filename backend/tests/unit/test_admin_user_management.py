"""Unit tests for admin user management service."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from soft_skills_backend.modules.admin.contracts.commands import (
    AdminAddUserCommand,
    AdminUserRoleCommand,
    AdminUserStatusCommand,
    BulkUserOperationCommand,
)
from soft_skills_backend.modules.admin.use_cases.admin_service import AdminService
from soft_skills_backend.platform.db.models import (
    OrganisationMembershipRecord,
    UserAccountRecord,
    WorkflowEventRecord,
)
from soft_skills_backend.shared.auth import Actor


class TestAdminUserRoleCommand:
    """Unit tests for AdminUserRoleCommand validation."""

    def test_valid_admin_role(self) -> None:
        cmd = AdminUserRoleCommand(role="admin")
        assert cmd.role == "admin"

    def test_valid_member_role(self) -> None:
        cmd = AdminUserRoleCommand(role="member")
        assert cmd.role == "member"

    def test_role_normalized_to_lowercase(self) -> None:
        cmd = AdminUserRoleCommand(role="ADMIN")
        assert cmd.role == "admin"

    def test_role_with_whitespace_normalized(self) -> None:
        cmd = AdminUserRoleCommand(role="  member  ")
        assert cmd.role == "member"

    def test_invalid_role_raises(self) -> None:
        with pytest.raises(ValueError, match="role must be 'admin' or 'member'"):
            AdminUserRoleCommand(role="superadmin")

    def test_empty_role_raises(self) -> None:
        with pytest.raises(ValueError, match="role must be 'admin' or 'member'"):
            AdminUserRoleCommand(role="")

    def test_role_with_only_whitespace_raises(self) -> None:
        with pytest.raises(ValueError, match="role must be 'admin' or 'member'"):
            AdminUserRoleCommand(role="   ")


class TestAdminUserStatusCommand:
    """Unit tests for AdminUserStatusCommand validation."""

    def test_valid_active_status(self) -> None:
        cmd = AdminUserStatusCommand(is_active=True)
        assert cmd.is_active is True

    def test_valid_inactive_status(self) -> None:
        cmd = AdminUserStatusCommand(is_active=False)
        assert cmd.is_active is False


class TestAdminAddUserCommand:
    """Unit tests for AdminAddUserCommand validation."""

    def test_valid_email(self) -> None:
        cmd = AdminAddUserCommand(email="user@example.com")
        assert cmd.email == "user@example.com"

    def test_email_normalized_to_lowercase(self) -> None:
        cmd = AdminAddUserCommand(email="User@EXAMPLE.COM")
        assert cmd.email == "user@example.com"

    def test_email_with_whitespace_normalized(self) -> None:
        cmd = AdminAddUserCommand(email="  user@example.com  ")
        assert cmd.email == "user@example.com"

    def test_default_role_is_member(self) -> None:
        cmd = AdminAddUserCommand(email="user@example.com")
        assert cmd.role == "member"

    def test_valid_admin_role(self) -> None:
        cmd = AdminAddUserCommand(email="user@example.com", role="admin")
        assert cmd.role == "admin"

    def test_invalid_email_raises(self) -> None:
        with pytest.raises(ValueError, match="email must be a valid email address"):
            AdminAddUserCommand(email="not-an-email")

    def test_empty_email_raises(self) -> None:
        with pytest.raises(ValueError, match="email must not be blank"):
            AdminAddUserCommand(email="")

    def test_email_with_only_whitespace_raises(self) -> None:
        with pytest.raises(ValueError, match="email must not be blank"):
            AdminAddUserCommand(email="   ")

    def test_invalid_role_raises(self) -> None:
        with pytest.raises(ValueError, match="role must be 'admin' or 'member'"):
            AdminAddUserCommand(email="user@example.com", role="superadmin")


class TestBulkUserOperationCommand:
    """Unit tests for BulkUserOperationCommand validation."""

    def test_valid_suspend_operation(self) -> None:
        cmd = BulkUserOperationCommand(
            user_ids=["user1", "user2"],
            operation="suspend",
        )
        assert cmd.operation == "suspend"

    def test_valid_activate_operation(self) -> None:
        cmd = BulkUserOperationCommand(
            user_ids=["user1", "user2"],
            operation="activate",
        )
        assert cmd.operation == "activate"

    def test_valid_change_role_operation(self) -> None:
        cmd = BulkUserOperationCommand(
            user_ids=["user1", "user2"],
            operation="change_role",
            payload={"role": "admin"},
        )
        assert cmd.operation == "change_role"
        assert cmd.payload == {"role": "admin"}

    def test_valid_export_operation(self) -> None:
        cmd = BulkUserOperationCommand(
            user_ids=["user1"],
            operation="export",
        )
        assert cmd.operation == "export"

    def test_operation_normalized_to_lowercase(self) -> None:
        cmd = BulkUserOperationCommand(
            user_ids=["user1"],
            operation="SUSPEND",
        )
        assert cmd.operation == "suspend"

    def test_empty_user_ids_raises(self) -> None:
        with pytest.raises(Exception, match="user_ids"):
            BulkUserOperationCommand(user_ids=[], operation="suspend")

    def test_invalid_operation_raises(self) -> None:
        with pytest.raises(
            ValueError, match="operation must be one of: suspend, activate, change_role, export"
        ):
            BulkUserOperationCommand(
                user_ids=["user1"],
                operation="delete",
            )


class TestAdminServiceUserManagement:
    """Unit tests for AdminService user management methods."""

    @pytest.fixture
    def mock_session_factory(self):
        """Create a mock session factory."""
        return MagicMock()

    @pytest.fixture
    def mock_workflow_events(self):
        """Create a mock workflow events repository."""
        return MagicMock()

    @pytest.fixture
    def admin_service(self, mock_session_factory, mock_workflow_events):
        """Create an AdminService instance with mocked dependencies."""
        return AdminService(
            session_factory=mock_session_factory,
            workflow_events=mock_workflow_events,
        )

    @pytest.fixture
    def actor_with_org(self):
        """Create an actor with organisation context."""
        return Actor(
            user_id="admin-user-id",
            email="admin@example.com",
            organisation_id="org-123",
            organisation_role="admin",
        )

    @pytest.fixture
    def actor_without_org(self):
        """Create an actor without organisation context."""
        return Actor(
            user_id="admin-user-id",
            email="admin@example.com",
            organisation_id=None,
            organisation_role=None,
        )

    def test_update_user_role_requires_organisation(self, admin_service, actor_without_org) -> None:
        """update_user_role should raise error when actor has no org context."""
        with pytest.raises(Exception) as exc_info:
            admin_service.update_user_role(
                actor_without_org,
                "user-123",
                AdminUserRoleCommand(role="member"),
            )
        assert "SS-AUTH-010" in str(exc_info.value)
        assert "Organisation context is required" in str(exc_info.value)

    def test_add_user_to_org_requires_organisation(self, admin_service, actor_without_org) -> None:
        """add_user_to_org should raise error when actor has no org context."""
        with pytest.raises(Exception) as exc_info:
            admin_service.add_user_to_org(
                actor_without_org,
                AdminAddUserCommand(email="newuser@example.com"),
            )
        assert "SS-AUTH-010" in str(exc_info.value)
        assert "Organisation context is required" in str(exc_info.value)


class TestActor:
    """Unit tests for Actor dataclass."""

    def test_actor_is_org_admin_when_role_is_admin(self) -> None:
        actor = Actor(
            user_id="user-1",
            email="admin@example.com",
            organisation_id="org-1",
            organisation_role="admin",
        )
        assert actor.is_org_admin is True

    def test_actor_is_not_org_admin_when_role_is_member(self) -> None:
        actor = Actor(
            user_id="user-1",
            email="member@example.com",
            organisation_id="org-1",
            organisation_role="member",
        )
        assert actor.is_org_admin is False

    def test_actor_is_not_org_admin_when_no_org_context(self) -> None:
        actor = Actor(
            user_id="user-1",
            email="user@example.com",
            organisation_id=None,
            organisation_role=None,
        )
        assert actor.is_org_admin is False

    def test_actor_with_no_role_is_not_org_admin(self) -> None:
        actor = Actor(
            user_id="user-1",
            email="user@example.com",
            organisation_id="org-1",
            organisation_role=None,
        )
        assert actor.is_org_admin is False
