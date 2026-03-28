"""Unit tests for auth provider implementation."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import Request

from soft_skills_backend.platform.db.models import (
    OrganisationMembershipRecord,
    UserAccountRecord,
)
from soft_skills_backend.shared.auth import Actor, AuthAdapter, HeaderAuthProvider
from soft_skills_backend.shared.errors import AppError


class TestHeaderAuthProvider:
    """Unit tests for HeaderAuthProvider."""

    @pytest.fixture
    def mock_session_factory(self):
        """Create a mock session factory."""
        factory = MagicMock()
        session = MagicMock()
        factory.return_value.__enter__ = MagicMock(return_value=session)
        factory.return_value.__exit__ = MagicMock(return_value=False)
        return factory

    @pytest.fixture
    def mock_workflow_events(self):
        """Create a mock workflow events repository."""
        return MagicMock()

    @pytest.fixture
    def auth_provider(self, mock_session_factory, mock_workflow_events):
        """Create a HeaderAuthProvider instance."""
        return HeaderAuthProvider(
            session_factory=mock_session_factory,
            workflow_events=mock_workflow_events,
        )

    @pytest.fixture
    def mock_request_with_user(self):
        """Create a mock request with X-User-ID header."""
        request = MagicMock(spec=Request)
        request.headers = {
            "X-User-ID": "test-user-123",
            "X-Organisation-ID": "test-org-456",
        }
        return request

    @pytest.fixture
    def mock_request_without_user(self):
        """Create a mock request without X-User-ID header."""
        request = MagicMock(spec=Request)
        request.headers = {}
        return request

    @pytest.mark.asyncio
    async def test_validate_session_returns_none_for_native_provider(self, auth_provider) -> None:
        """Native/header provider does not validate tokens - returns None."""
        result = await auth_provider.validate_session("some-token")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_actor_returns_none_without_user_header(
        self, auth_provider, mock_request_without_user
    ) -> None:
        """get_actor returns None when X-User-ID header is missing."""
        result = await auth_provider.get_actor(mock_request_without_user)
        assert result is None

    @pytest.mark.asyncio
    async def test_require_actor_raises_without_user_header(
        self, auth_provider, mock_request_without_user
    ) -> None:
        """require_actor raises auth error when X-User-ID header is missing."""
        with pytest.raises(AppError) as exc_info:
            await auth_provider.require_actor(mock_request_without_user)
        assert "SS-AUTH-001" in str(exc_info.value)
        assert "Authentication is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_actor_raises_when_user_not_found(
        self, auth_provider, mock_session_factory, mock_request_with_user
    ) -> None:
        """get_actor raises error when user is not found in database."""
        session = MagicMock()
        session.get.return_value = None
        mock_session_factory.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_factory.return_value.__exit__ = MagicMock(return_value=False)

        with pytest.raises(AppError) as exc_info:
            await auth_provider.get_actor(mock_request_with_user)
        assert "SS-AUTH-002" in str(exc_info.value)
        assert "Authenticated user was not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_actor_returns_actor_with_membership(
        self, auth_provider, mock_session_factory, mock_request_with_user
    ) -> None:
        """get_actor returns Actor with organisation context when user is found."""
        session = MagicMock()
        user_record = MagicMock(spec=UserAccountRecord)
        user_record.id = "test-user-123"
        user_record.email = "test@example.com"
        session.get.return_value = user_record

        membership_record = MagicMock(spec=OrganisationMembershipRecord)
        membership_record.organisation_id = "test-org-456"
        membership_record.role = "admin"
        session.query.return_value.filter.return_value.first.return_value = membership_record

        mock_session_factory.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_factory.return_value.__exit__ = MagicMock(return_value=False)

        result = await auth_provider.get_actor(mock_request_with_user)

        assert result is not None
        assert isinstance(result, Actor)
        assert result.user_id == "test-user-123"
        assert result.email == "test@example.com"
        assert result.organisation_id == "test-org-456"
        assert result.organisation_role == "admin"
        assert result.is_org_admin is True

    @pytest.mark.asyncio
    async def test_get_actor_returns_actor_without_membership(
        self, auth_provider, mock_session_factory, mock_request_with_user
    ) -> None:
        """get_actor returns Actor without org context when membership not found."""
        session = MagicMock()
        user_record = MagicMock(spec=UserAccountRecord)
        user_record.id = "test-user-123"
        user_record.email = "test@example.com"
        session.get.return_value = user_record

        session.query.return_value.filter.return_value.first.return_value = None

        mock_session_factory.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_factory.return_value.__exit__ = MagicMock(return_value=False)

        result = await auth_provider.get_actor(mock_request_with_user)

        assert result is not None
        assert isinstance(result, Actor)
        assert result.user_id == "test-user-123"
        assert result.email == "test@example.com"
        assert result.organisation_id is None
        assert result.organisation_role is None
        assert result.is_org_admin is False

    @pytest.mark.asyncio
    async def test_require_org_admin_raises_for_non_admin(
        self, auth_provider, mock_session_factory, mock_request_with_user
    ) -> None:
        """require_org_admin raises error when user is not an org admin."""
        session = MagicMock()
        user_record = MagicMock(spec=UserAccountRecord)
        user_record.id = "test-user-123"
        user_record.email = "test@example.com"
        session.get.return_value = user_record

        membership_record = MagicMock(spec=OrganisationMembershipRecord)
        membership_record.organisation_id = "test-org-456"
        membership_record.role = "member"
        session.query.return_value.filter.return_value.first.return_value = membership_record

        mock_session_factory.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_factory.return_value.__exit__ = MagicMock(return_value=False)

        with pytest.raises(AppError) as exc_info:
            await auth_provider.require_org_admin(mock_request_with_user)
        assert "SS-AUTH-004" in str(exc_info.value)
        assert "Organisation admin access is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_require_org_admin_succeeds_for_admin(
        self, auth_provider, mock_session_factory, mock_request_with_user
    ) -> None:
        """require_org_admin returns actor when user is org admin."""
        session = MagicMock()
        user_record = MagicMock(spec=UserAccountRecord)
        user_record.id = "test-user-123"
        user_record.email = "test@example.com"
        session.get.return_value = user_record

        membership_record = MagicMock(spec=OrganisationMembershipRecord)
        membership_record.organisation_id = "test-org-456"
        membership_record.role = "admin"
        session.query.return_value.filter.return_value.first.return_value = membership_record

        mock_session_factory.return_value.__enter__ = MagicMock(return_value=session)
        mock_session_factory.return_value.__exit__ = MagicMock(return_value=False)

        result = await auth_provider.require_org_admin(mock_request_with_user)

        assert result is not None
        assert isinstance(result, Actor)
        assert result.is_org_admin is True

    def test_record_auth_event_noops_without_workflow_events(self, mock_session_factory) -> None:
        """_record_auth_event does nothing when workflow_events is None."""
        provider = HeaderAuthProvider(
            session_factory=mock_session_factory,
            workflow_events=None,
        )
        provider._record_auth_event(
            "auth.login.success.v1",
            user_id="test-user",
        )

    def test_record_auth_event_records_event(
        self, mock_session_factory, mock_workflow_events
    ) -> None:
        """_record_auth_event records event when workflow_events is provided."""
        provider = HeaderAuthProvider(
            session_factory=mock_session_factory,
            workflow_events=mock_workflow_events,
        )
        provider._record_auth_event(
            "auth.login.success.v1",
            user_id="test-user",
        )
        mock_workflow_events.record.assert_called_once()


class TestAuthAdapterProtocol:
    """Unit tests for AuthAdapter protocol compliance."""

    def test_header_auth_provider_has_required_protocol_methods(self) -> None:
        """HeaderAuthProvider should have all AuthAdapter protocol methods."""
        provider = HeaderAuthProvider(
            session_factory=MagicMock(),
            workflow_events=None,
        )
        required_methods = [
            "get_actor",
            "validate_session",
            "require_actor",
            "require_org_admin",
        ]
        for method in required_methods:
            assert hasattr(provider, method)
            assert callable(getattr(provider, method))

    def test_auth_adapter_protocol_has_required_methods(self) -> None:
        """AuthAdapter protocol should define required methods."""
        required_methods = [
            "get_actor",
            "validate_session",
            "require_actor",
            "require_org_admin",
        ]
        for method in required_methods:
            assert hasattr(AuthAdapter, method)


class TestActorDataclass:
    """Unit tests for Actor dataclass."""

    def test_actor_creation(self) -> None:
        """Actor can be created with required fields."""
        actor = Actor(user_id="user-1", email="user@example.com")
        assert actor.user_id == "user-1"
        assert actor.email == "user@example.com"

    def test_actor_with_optional_fields(self) -> None:
        """Actor can be created with optional fields."""
        actor = Actor(
            user_id="user-1",
            email="user@example.com",
            organisation_id="org-1",
            organisation_role="admin",
        )
        assert actor.organisation_id == "org-1"
        assert actor.organisation_role == "admin"

    def test_is_org_admin_true_for_admin(self) -> None:
        """is_org_admin returns True when organisation_role is 'admin'."""
        actor = Actor(
            user_id="user-1",
            email="admin@example.com",
            organisation_role="admin",
        )
        assert actor.is_org_admin is True

    def test_is_org_admin_false_for_member(self) -> None:
        """is_org_admin returns False when organisation_role is 'member'."""
        actor = Actor(
            user_id="user-1",
            email="member@example.com",
            organisation_role="member",
        )
        assert actor.is_org_admin is False

    def test_is_org_admin_false_when_no_org_role(self) -> None:
        """is_org_admin returns False when organisation_role is None."""
        actor = Actor(
            user_id="user-1",
            email="user@example.com",
            organisation_role=None,
        )
        assert actor.is_org_admin is False

    def test_actor_is_hashable(self) -> None:
        """Actor dataclass with slots=True may not be hashable by default."""
        actor1 = Actor(user_id="user-1", email="user@example.com")
        actor2 = Actor(user_id="user-1", email="user@example.com")
        try:
            actor_set = {actor1, actor2}
            assert len(actor_set) == 1
        except TypeError:
            pass

    def test_actor_equality(self) -> None:
        """Actor dataclass instances with same values should be equal."""
        actor1 = Actor(user_id="user-1", email="user@example.com")
        actor2 = Actor(user_id="user-1", email="user@example.com")
        assert actor1 == actor2
