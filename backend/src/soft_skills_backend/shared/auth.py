"""Authentication boundary and actor resolution."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Request
from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.platform.db.models import OrganisationMembershipRecord, UserAccountRecord
from soft_skills_backend.shared.errors import auth_error


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

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

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

    def optional_actor(self, request: Request) -> Actor | None:
        user_id = request.headers.get("X-User-ID")
        if not user_id:
            return None
        org_id = request.headers.get("X-Organisation-ID")
        with self._session_factory() as session:
            record = session.get(UserAccountRecord, user_id)
            if record is None:
                raise auth_error(
                    "Authenticated user was not found",
                    code="SS-AUTH-002",
                    status_code=401,
                    details={"user_id": user_id},
                )
            org_context = self._resolve_organisation_context(session, user_id, org_id)
            return Actor(
                user_id=record.id,
                email=record.email,
                organisation_id=org_context[0],
                organisation_role=org_context[1],
            )

    def require_actor(self, request: Request) -> Actor:
        actor = self.optional_actor(request)
        if actor is None:
            raise auth_error("Authentication is required", details={"header": "X-User-ID"})
        return actor

    def require_org_admin(self, request: Request) -> Actor:
        actor = self.require_actor(request)
        if not actor.is_org_admin:
            raise auth_error(
                "Organisation admin access is required",
                code="SS-AUTH-004",
                status_code=403,
                details={"user_id": actor.user_id, "organisation_id": actor.organisation_id},
            )
        return actor
