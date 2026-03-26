"""Assessment marking smoke result contracts."""

from __future__ import annotations

from pydantic import BaseModel


class AssessmentMarkingSmokeResult(BaseModel):
    """Result of one assessment-marking smoke suite."""

    status: str
    practice_type: str
    attempt_id: str
    attempt_status: str
    provider: str | None = None
    model_slug: str | None = None
    assessment_id: str | None = None
    overall_score: int | None = None
    error_code: str | None = None
