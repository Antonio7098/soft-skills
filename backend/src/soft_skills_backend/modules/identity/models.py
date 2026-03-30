"""Identity domain models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RegisterUserCommand(BaseModel):
    """Account creation payload."""

    email: str
    display_name: str
    password: str = Field(default="password123", min_length=8)
    target_role: str | None = None
    goals: list[str] = Field(default_factory=list)
    practice_preferences: dict[str, str] = Field(default_factory=dict)


class LoginUserCommand(BaseModel):
    """Credential sign-in payload."""

    email: str
    password: str = Field(min_length=8)


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
    auth_provider: str
    created_at: datetime
    profile: LearnerProfileView


class DeleteAccountResult(BaseModel):
    """Account deletion payload."""

    deleted_user_id: str
    status: str
