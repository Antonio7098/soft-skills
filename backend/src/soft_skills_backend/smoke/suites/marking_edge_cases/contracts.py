"""Marking edge case smoke result contracts."""

from __future__ import annotations

from pydantic import BaseModel


class MarkingEdgeCaseSmokeResult(BaseModel):
    """Result of marking edge case smoke suite."""

    status: str
    test_name: str
    practice_type: str
    attempt_id: str | None = None
    attempt_status: str | None = None
    assessment_id: str | None = None
    overall_score: int | None = None
    error_code: str | None = None
    error_details: dict | None = None


class MarkingEmptyResponseSmokeResult(MarkingEdgeCaseSmokeResult):
    """Result for empty response edge case test."""


class MarkingLongResponseSmokeResult(MarkingEdgeCaseSmokeResult):
    """Result for very long response edge case test."""


class MarkingSpecialCharsResponseSmokeResult(MarkingEdgeCaseSmokeResult):
    """Result for special characters in response edge case test."""


class MarkingSqlInjectionAttemptSmokeResult(MarkingEdgeCaseSmokeResult):
    """Result for SQL injection attempt in response edge case test."""


class MarkingRapidSubmissionSmokeResult(MarkingEdgeCaseSmokeResult):
    """Result for rapid multiple submissions edge case test."""


class MarkingRepeatedSubmissionSmokeResult(MarkingEdgeCaseSmokeResult):
    """Result for repeated identical submissions edge case test."""
