"""Authentication boundary and actor resolution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, TypedDict

from fastapi import Request
from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.platform.db.models import OrganisationMembershipRecord, UserAccountRecord
from soft_skills_backend.shared.errors import auth_error

if TYPE_CHECKING:
    from soft_skills_backend.platform.db.repositories import SqlAlchemyWorkflowEventRepository


class ProviderSession(TypedDict):
    """Normalized session data from any provider."""

    user_id: str
    email: str
    org_id: str | None
    org_role: str | None


class AuthAdapter(Protocol):
    """Swappable auth provider interface."""

    async def get_actor(self, request: Request) -> Actor | None:
        """Resolve authenticated actor from request, or None if not authenticated."""

    async def validate_session(self, token: str) -> ProviderSession | None:
        """Validate provider-specific token and return session info."""

    async def require_actor(self, request: Request) -> Actor:
        """Require authenticated actor or raise auth error."""

    async def require_org_admin(self, request: Request) -> Actor:
        """Require org admin actor or raise auth error."""


@dataclass(slots=True)
class Actor:
    """Authenticated actor resolved at the request boundary."""

    user_id: str
    email: str
    organisation_id: str | None = None
    organisation_role: str | None = None

    @property
    def is_org_admin(self) -> bool:
        return self.organisation_role == "admin"


class HeaderAuthProvider:
    """Request-bound auth provider with optional organisation context."""

    def __init__(
        self,
        session_factory: sessionmaker[Session],
        workflow_events: SqlAlchemyWorkflowEventRepository | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._workflow_events = workflow_events

    def _record_auth_event(
        self,
        event_type: str,
        *,
        user_id: str,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Record an authentication event to workflow events."""
        if self._workflow_events is None:
            return
        from soft_skills_backend.platform.observability.events import WorkflowEvent

        event = WorkflowEvent(
            event_type=event_type,
            request_id=None,
            trace_id=None,
            workflow_id=None,
            error_code=error_code,
            payload={"user_id": user_id, **(details or {})},
            organisation_id=user_id,
        )
        self._workflow_events.record(event)

    def _resolve_organisation_context(
        self, session: Session, user_id: str, org_id: str | None
    ) -> tuple[str | None, str | None]:
        """Resolve organisation context from header and membership lookup."""
        if not org_id:
            return None, None
        membership = (
            session.query(OrganisationMembershipRecord)
            .filter(
                OrganisationMembershipRecord.organisation_id == org_id,
                OrganisationMembershipRecord.user_id == user_id,
            )
            .first()
        )
        if not membership:
            return None, None
        return membership.organisation_id, membership.role

    async def validate_session(self, token: str) -> ProviderSession | None:
        """Native/header provider does not validate tokens - returns None."""
        return None

    async def get_actor(self, request: Request) -> Actor | None:
        """Resolve authenticated actor from request, or None if not authenticated."""
        user_id = request.headers.get("X-User-ID")
        if not user_id:
            return None
        org_id = request.headers.get("X-Organisation-ID")
        with self._session_factory() as session:
            record = session.get(UserAccountRecord, user_id)
            if record is None:
                self._record_auth_event(
                    "auth.login.failed.v1",
                    user_id=user_id,
                    error_code="SS-AUTH-002",
                    details={"reason": "user_not_found"},
                )
                raise auth_error(
                    "Authenticated user was not found",
                    code="SS-AUTH-002",
                    status_code=401,
                    details={"user_id": user_id},
                )
            self._record_auth_event(
                "auth.login.success.v1",
                user_id=user_id,
            )
            org_context = self._resolve_organisation_context(session, user_id, org_id)
            return Actor(
                user_id=record.id,
                email=record.email,
                organisation_id=org_context[0],
                organisation_role=org_context[1],
            )

    async def require_actor(self, request: Request) -> Actor:
        """Require authenticated actor or raise auth error."""
        user_id = request.headers.get("X-User-ID")
        if not user_id:
            self._record_auth_event(
                "auth.login.failed.v1",
                user_id=None,
                error_code="SS-AUTH-001",
                details={"reason": "missing_header"},
            )
            raise auth_error("Authentication is required", details={"header": "X-User-ID"})
        actor = await self.get_actor(request)
        if actor is None:
            raise auth_error("Authentication is required", details={"header": "X-User-ID"})
        return actor

    async def require_org_admin(self, request: Request) -> Actor:
        """Require org admin actor or raise auth error."""
        actor = await self.require_actor(request)
        if not actor.is_org_admin:
            self._record_auth_event(
                "auth.access_denied.v1",
                user_id=actor.user_id,
                error_code="SS-AUTH-004",
                details={"organisation_id": actor.organisation_id},
            )
            raise auth_error(
                "Organisation admin access is required",
                code="SS-AUTH-004",
                status_code=403,
                details={"user_id": actor.user_id, "organisation_id": actor.organisation_id},
            )
        return actor
