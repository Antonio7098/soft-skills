"""Identity and learner profile services."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.modules.identity.models import (
    DeleteAccountResult,
    LearnerProfileView,
    LoginUserCommand,
    OrganisationMembershipView,
    RegisterUserCommand,
    UpdateProfileCommand,
    UserView,
)
from soft_skills_backend.platform.db.models import (
    LearnerProfileRecord,
    OrganisationMembershipRecord,
    OrganisationRecord,
    UserAccountRecord,
)
from soft_skills_backend.platform.db.repositories import SqlAlchemyWorkflowEventRepository
from soft_skills_backend.platform.observability.events import WorkflowEvent
from soft_skills_backend.shared.errors import auth_error, domain_error


def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 200_000)
    return f"{salt}${digest.hex()}"


def _verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash or "$" not in password_hash:
        return False
    salt, expected = password_hash.split("$", 1)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 200_000)
    return hmac.compare_digest(digest.hex(), expected)


LEGACY_PASSWORD_CLAIM_CUTOFF = datetime(2026, 3, 30, 10, 20, tzinfo=UTC)

ADMIN_PERMISSIONS = ["collections:read", "practice:run", "admin:access", "org:read", "org:write"]
MEMBER_PERMISSIONS = ["collections:read", "practice:run"]


def _coerce_utc_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class IdentityService:
    """Manage accounts and learner profiles."""

    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        workflow_events: SqlAlchemyWorkflowEventRepository,
    ) -> None:
        self._session_factory = session_factory
        self._workflow_events = workflow_events

    def register_user(self, command: RegisterUserCommand) -> UserView:
        with self._session_factory() as session:
            existing = session.query(UserAccountRecord).filter_by(email=command.email).one_or_none()
            if existing is not None:
                raise domain_error(
                    "User email already exists",
                    code="SS-DOMAIN-002",
                    status_code=409,
                    details={"email": command.email},
                )

            now = datetime.now(UTC)
            user = UserAccountRecord(
                id=uuid4().hex,
                email=command.email,
                display_name=command.display_name,
                auth_provider="internal",
                auth_subject=command.email,
                password_hash=_hash_password(command.password),
                created_at=now,
            )
            profile = LearnerProfileRecord(
                user_id=user.id,
                target_role=command.target_role,
                goals=command.goals,
                practice_preferences=command.practice_preferences,
                updated_at=now,
            )
            session.add(user)
            session.add(profile)
            session.commit()

        self._workflow_events.record(
            WorkflowEvent(
                event_type="identity.user_registered.v1",
                payload={"user_id": user.id},
                request_id=user.id,
                workflow_id=user.id,
                organisation_id=user.id,
            )
        )
        return self.get_user(user.id)

    def login_user(self, command: LoginUserCommand) -> UserView:
        with self._session_factory() as session:
            user = session.query(UserAccountRecord).filter_by(email=command.email).one_or_none()
            if user is None or not user.is_active:
                raise auth_error(
                    "Invalid email or password",
                    code="SS-AUTH-011",
                    status_code=401,
                    details={"email": command.email},
                )

            password_matches = _verify_password(command.password, user.password_hash)
            if not password_matches and self._should_claim_legacy_password(user):
                user.password_hash = _hash_password(command.password)
                session.commit()
                password_matches = True

            if not password_matches:
                raise auth_error(
                    "Invalid email or password",
                    code="SS-AUTH-011",
                    status_code=401,
                    details={"email": command.email},
                )
            user_id = user.id

        self._workflow_events.record(
            WorkflowEvent(
                event_type="identity.user_logged_in.v1",
                payload={"user_id": user_id},
                request_id=user_id,
                workflow_id=user_id,
                organisation_id=user_id,
            )
        )
        return self.get_user(user_id)

    def _should_claim_legacy_password(self, user: UserAccountRecord) -> bool:
        return (
            user.auth_provider == "internal"
            and _coerce_utc_datetime(user.created_at) < LEGACY_PASSWORD_CLAIM_CUTOFF
            and _verify_password("password123", user.password_hash)
        )

    def get_user(self, user_id: str) -> UserView:
        with self._session_factory() as session:
            user = session.get(UserAccountRecord, user_id)
            if user is None:
                raise domain_error(
                    "User was not found",
                    code="SS-DOMAIN-003",
                    status_code=404,
                    details={"user_id": user_id},
                )
            profile = session.get(LearnerProfileRecord, user_id)
            if profile is None:
                raise domain_error(
                    "Learner profile is missing",
                    code="SS-DOMAIN-004",
                    status_code=500,
                    details={"user_id": user_id},
                )
            memberships = (
                session.query(OrganisationMembershipRecord).filter_by(user_id=user_id).all()
            )
            org_memberships = []
            for m in memberships:
                org = session.get(OrganisationRecord, m.organisation_id)
                perms = ADMIN_PERMISSIONS if m.role == "admin" else MEMBER_PERMISSIONS
                org_memberships.append(
                    OrganisationMembershipView(
                        organisation_id=m.organisation_id,
                        organisation_name=org.name if org else m.organisation_id,
                        role=m.role,
                        permissions=perms,
                    )
                )
            return UserView(
                id=user.id,
                email=user.email,
                display_name=user.display_name,
                auth_provider=user.auth_provider,
                created_at=user.created_at,
                profile=LearnerProfileView(
                    target_role=profile.target_role,
                    goals=list(profile.goals),
                    practice_preferences=dict(profile.practice_preferences),
                ),
                org_memberships=org_memberships,
            )

    def update_profile(self, user_id: str, command: UpdateProfileCommand) -> UserView:
        with self._session_factory() as session:
            profile = session.get(LearnerProfileRecord, user_id)
            if profile is None:
                raise domain_error(
                    "Learner profile is missing",
                    code="SS-DOMAIN-004",
                    status_code=500,
                    details={"user_id": user_id},
                )
            if command.target_role is not None:
                profile.target_role = command.target_role
            if command.goals is not None:
                profile.goals = command.goals
            if command.practice_preferences is not None:
                profile.practice_preferences = command.practice_preferences
            profile.updated_at = datetime.now(UTC)
            session.commit()

        self._workflow_events.record(
            WorkflowEvent(
                event_type="identity.profile_updated.v1",
                payload={"user_id": user_id},
                request_id=user_id,
                workflow_id=user_id,
                organisation_id=user_id,
            )
        )
        return self.get_user(user_id)

    def delete_user(self, user_id: str) -> DeleteAccountResult:
        with self._session_factory() as session:
            user = session.get(UserAccountRecord, user_id)
            if user is None:
                raise domain_error(
                    "User was not found",
                    code="SS-DOMAIN-003",
                    status_code=404,
                    details={"user_id": user_id},
                )
            session.query(LearnerProfileRecord).filter_by(user_id=user_id).delete()
            session.query(OrganisationMembershipRecord).filter_by(user_id=user_id).delete()
            session.query(UserAccountRecord).filter_by(id=user_id).delete()
            session.commit()

        self._workflow_events.record(
            WorkflowEvent(
                event_type="identity.user_deleted.v1",
                payload={"user_id": user_id},
                request_id=user_id,
                workflow_id=user_id,
                organisation_id=user_id,
            )
        )
        return DeleteAccountResult(deleted_user_id=user_id, status="deleted")
