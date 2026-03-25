"""Authentication boundary and actor resolution."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Request
from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.domain.errors import auth_error
from soft_skills_backend.persistence.models import UserAccountRecord


@dataclass(slots=True)
class Actor:
    """Authenticated actor resolved at the request boundary."""

    user_id: str
    role: str
    email: str

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


class HeaderAuthProvider:
    """Simple request-bound auth provider for the MVP foundation."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def optional_actor(self, request: Request) -> Actor | None:
        user_id = request.headers.get("X-User-ID")
        if not user_id:
            return None
        with self._session_factory() as session:
            record = session.get(UserAccountRecord, user_id)
            if record is None:
                raise auth_error(
                    "Authenticated user was not found",
                    code="SS-AUTH-002",
                    status_code=401,
                    details={"user_id": user_id},
                )
            return Actor(user_id=record.id, role=record.role, email=record.email)

    def require_actor(self, request: Request) -> Actor:
        actor = self.optional_actor(request)
        if actor is None:
            raise auth_error("Authentication is required", details={"header": "X-User-ID"})
        return actor

    def require_admin(self, request: Request) -> Actor:
        actor = self.require_actor(request)
        if not actor.is_admin:
            raise auth_error(
                "Admin access is required",
                code="SS-AUTH-003",
                status_code=403,
                details={"user_id": actor.user_id},
            )
        return actor
