"""Practice domain rules and typed assessment artifacts."""

from __future__ import annotations

import re
from collections.abc import Iterable
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator

from soft_skills_backend.shared.errors import domain_error, scoring_error


class PracticeType(StrEnum):
    """Supported practice modes."""

    QUICK_PRACTICE = "quick_practice"
    INTERVIEW = "interview"
    SCENARIO = "scenario"


PRACTICE_DELIVERY_VERSIONS: dict[PracticeType, str] = {
    PracticeType.QUICK_PRACTICE: "quick-practice.delivery.v1",
    PracticeType.INTERVIEW: "interview.delivery.v1",
    PracticeType.SCENARIO: "scenario.delivery.v1",
}


class SessionStatus(StrEnum):
    """Practice session lifecycle."""

    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class AttemptStatus(StrEnum):
    """Attempt lifecycle for the first vertical slice."""

    PROMPT_DELIVERED = "prompt_delivered"
    SUBMITTED = "submitted"
    ASSESSING = "assessing"
    ASSESSED = "assessed"
    ASSESSMENT_REJECTED = "assessment_rejected"
    ASSESSMENT_FAILED = "assessment_failed"


ALLOWED_ATTEMPT_TRANSITIONS: dict[AttemptStatus, set[AttemptStatus]] = {
    AttemptStatus.PROMPT_DELIVERED: {AttemptStatus.SUBMITTED},
    AttemptStatus.SUBMITTED: {AttemptStatus.ASSESSING},
    AttemptStatus.ASSESSING: {
        AttemptStatus.ASSESSED,
        AttemptStatus.ASSESSMENT_REJECTED,
        AttemptStatus.ASSESSMENT_FAILED,
    },
    AttemptStatus.ASSESSED: set(),
    AttemptStatus.ASSESSMENT_REJECTED: set(),
    AttemptStatus.ASSESSMENT_FAILED: set(),
}


class AssessmentValidationStatus(StrEnum):
    """Assessment artifact validation state."""

    VALIDATED = "validated"
    REJECTED = "rejected"


class SkillScore(BaseModel):
    """Skill-level assessment score."""

    skill_slug: str
    score: int = Field(ge=1, le=5)
    rationale: str

    @field_validator("skill_slug", "rationale")
    @classmethod
    def _require_non_blank_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Value must not be blank")
        return cleaned


class EvidenceItem(BaseModel):
    """Evidence item tied to the learner response."""

    skill_slug: str
    quote: str
    explanation: str

    @field_validator("skill_slug", "quote", "explanation")
    @classmethod
    def _require_non_blank_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Value must not be blank")
        return cleaned


class QuickPracticeAssessmentDraft(BaseModel):
    """Structured assessment payload expected from the marking model."""

    prompt_version: str
    rubric_version: str
    provider: str
    model_slug: str
    overall_score: int = Field(ge=1, le=5)
    rationale: str
    skill_scores: list[SkillScore] = Field(min_length=1)
    evidence: list[EvidenceItem] = Field(min_length=1)
    strengths: list[str] = Field(min_length=1)
    weaknesses: list[str] = Field(min_length=1)
    next_actions: list[str] = Field(min_length=1)

    @field_validator(
        "prompt_version",
        "rubric_version",
        "provider",
        "model_slug",
        "rationale",
        mode="before",
    )
    @classmethod
    def _strip_scalar_text(cls, value: object) -> object:
        if isinstance(value, str):
            cleaned = value.strip()
            if not cleaned:
                raise ValueError("Value must not be blank")
            return cleaned
        return value

    @field_validator("strengths", "weaknesses", "next_actions", mode="after")
    @classmethod
    def _strip_text_lists(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values if value.strip()]
        if not cleaned:
            raise ValueError("List must contain at least one non-blank item")
        return cleaned


def ensure_attempt_transition(current_status: str, next_status: AttemptStatus) -> None:
    """Reject invalid attempt lifecycle transitions."""

    try:
        current = AttemptStatus(current_status)
    except ValueError as exc:
        raise domain_error(
            "Attempt is in an unknown lifecycle state",
            code="SS-DOMAIN-008",
            status_code=500,
            details={"current_status": current_status},
        ) from exc

    allowed = ALLOWED_ATTEMPT_TRANSITIONS[current]
    if next_status in allowed:
        return

    raise domain_error(
        "Invalid attempt lifecycle transition",
        code="SS-DOMAIN-009",
        details={"current_status": current.value, "next_status": next_status.value},
    )


def validate_assessment_draft(
    *,
    response_text: str,
    required_skill_slugs: Iterable[str],
    draft: QuickPracticeAssessmentDraft,
) -> None:
    """Enforce explainability and scoring guards before persistence."""

    expected_skills = list(dict.fromkeys(required_skill_slugs))
    observed_skills = [score.skill_slug for score in draft.skill_scores]
    if len(set(observed_skills)) != len(observed_skills):
        raise scoring_error(
            "Assessment output repeated a skill score",
            code="SS-SCORING-001",
            details={"observed_skills": observed_skills},
        )
    if set(observed_skills) != set(expected_skills):
        raise scoring_error(
            "Assessment output did not cover the expected skills",
            code="SS-SCORING-002",
            details={
                "expected_skills": expected_skills,
                "observed_skills": observed_skills,
            },
        )

    response_normalized = _normalize_text(response_text)
    for item in draft.evidence:
        if item.skill_slug not in expected_skills:
            raise scoring_error(
                "Evidence referenced an unexpected skill",
                code="SS-SCORING-003",
                details={"skill_slug": item.skill_slug},
            )
        if len(item.quote.strip()) < 6 or _normalize_text(item.quote) not in response_normalized:
            raise scoring_error(
                "Evidence must quote the learner response directly",
                code="SS-SCORING-004",
                details={"quote": item.quote},
            )

    overlapping_feedback = _normalized_overlap(draft.strengths, draft.weaknesses)
    if overlapping_feedback:
        raise scoring_error(
            "Assessment strengths and weaknesses contradicted each other",
            code="SS-SCORING-005",
            details={"overlap": sorted(overlapping_feedback)},
        )

    average_score = sum(score.score for score in draft.skill_scores) / len(draft.skill_scores)
    if abs(draft.overall_score - round(average_score)) > 1:
        raise scoring_error(
            "Overall score was inconsistent with skill-level scores",
            code="SS-SCORING-006",
            details={"overall_score": draft.overall_score, "average_skill_score": average_score},
        )


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _normalized_overlap(left: Iterable[str], right: Iterable[str]) -> set[str]:
    return {_normalize_text(value) for value in left} & {_normalize_text(value) for value in right}
