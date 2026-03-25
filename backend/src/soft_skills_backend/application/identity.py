"""Identity and learner profile services."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.domain.errors import domain_error
from soft_skills_backend.observability.events import WorkflowEvent
from soft_skills_backend.persistence.models import LearnerProfileRecord, UserAccountRecord
from soft_skills_backend.persistence.repositories import SqlAlchemyWorkflowEventRepository


class RegisterUserCommand(BaseModel):
    """Account creation payload."""

    email: str
    display_name: str
    role: str = "standard_user"
    target_role: str | None = None
    goals: list[str] = Field(default_factory=list)
    practice_preferences: dict[str, str] = Field(default_factory=dict)


class UpdateProfileCommand(BaseModel):
    """Profile patch payload."""

    target_role: str | None = None
    goals: list[str] | None = None
    practice_preferences: dict[str, str] | None = None


class LearnerProfileView(BaseModel):
    """Learner profile response."""

    target_role: str | None = None
    goals: list[str] = Field(default_factory=list)
    practice_preferences: dict[str, str] = Field(default_factory=dict)


class UserView(BaseModel):
    """User response payload."""

    id: str
    email: str
    display_name: str
    role: str
    auth_provider: str
    created_at: datetime
    profile: LearnerProfileView


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
                role=command.role,
                auth_provider="internal",
                auth_subject=command.email,
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
                payload={"user_id": user.id, "role": user.role},
                request_id=user.id,
                workflow_id=user.id,
            )
        )
        return self.get_user(user.id)

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
            return UserView(
                id=user.id,
                email=user.email,
                display_name=user.display_name,
                role=user.role,
                auth_provider=user.auth_provider,
                created_at=user.created_at,
                profile=LearnerProfileView(
                    target_role=profile.target_role,
                    goals=list(profile.goals),
                    practice_preferences=dict(profile.practice_preferences),
                ),
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
            )
        )
        return self.get_user(user_id)
