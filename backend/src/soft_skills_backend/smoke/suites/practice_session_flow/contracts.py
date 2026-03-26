"""Practice-session flow smoke contracts."""

from __future__ import annotations

from pydantic import BaseModel


class PracticeSessionAttemptSmokeResult(BaseModel):
    """Result of one practice session/attempt flow."""

    practice_type: str
    session_id: str
    attempt_id: str
    attempt_status: str
    assessment_id: str | None = None


class PracticeSessionFlowSmokeResult(BaseModel):
    """Result of the practice-session flow smoke."""

    status: str
    results: list[PracticeSessionAttemptSmokeResult]
