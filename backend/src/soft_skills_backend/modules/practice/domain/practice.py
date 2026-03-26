"""Practice domain rules and typed assessment artifacts."""

from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator

from soft_skills_backend.engines.marking import (
    CandidateResponse,
    CriterionResultInput,
    EvidenceReference,
    PromptContract,
    RubricCriterion,
    RubricDefinition,
    RubricScale,
    build_marking_decision,
    validate_marking_decision,
)
from soft_skills_backend.shared.errors import AppError, domain_error, scoring_error


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


class AssessmentDraft(BaseModel):
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
    draft: AssessmentDraft,
) -> None:
    """Enforce explainability and scoring guards before persistence."""

    expected_skills = list(dict.fromkeys(required_skill_slugs))
    response_normalized = _normalize_text(response_text)
    evidence_by_skill: dict[str, list[EvidenceReference]] = {}
    prompt = PromptContract(
        prompt_id="quick-practice-prompt",
        prompt_version=draft.prompt_version,
        prompt_type="quick_practice_prompt",
        prompt_text="validation-only",
        response_mode="text",
        rubric_id="quick-practice-rubric",
    )
    rubric = RubricDefinition(
        rubric_id="quick-practice-rubric",
        rubric_version=draft.rubric_version,
        scale=RubricScale(minimum_score=1, maximum_score=5),
        criteria=[
            RubricCriterion(
                criterion_ref=skill_slug,
                description=f"Validate criterion coverage for {skill_slug}.",
            )
            for skill_slug in expected_skills
        ],
    )
    for evidence in draft.evidence:
        if evidence.skill_slug not in expected_skills:
            raise scoring_error(
                "Evidence referenced an unexpected skill",
                code="SS-SCORING-003",
                details={"skill_slug": evidence.skill_slug},
            )
        if len(evidence.quote.strip()) < 6 or _normalize_text(evidence.quote) not in response_normalized:
            raise scoring_error(
                "Evidence must quote the learner response directly",
                code="SS-SCORING-004",
                details={"quote": evidence.quote},
            )
        evidence_by_skill.setdefault(evidence.skill_slug, []).append(
            EvidenceReference(
                criterion_ref=evidence.skill_slug,
                quote=evidence.quote,
                explanation=evidence.explanation,
            )
        )
    try:
        decision = build_marking_decision(
            marking_id="assessment-draft",
            prompt=prompt,
            response_id="candidate-response",
            rubric=rubric,
            engine_version="marking-engine.v1",
            provider=draft.provider,
            model_slug=draft.model_slug,
            overall_score=draft.overall_score,
            criterion_results=[
                CriterionResultInput(
                    criterion_ref=skill_score.skill_slug,
                    score=skill_score.score,
                    rationale=skill_score.rationale,
                )
                for skill_score in draft.skill_scores
            ],
            evidence=[item for group in evidence_by_skill.values() for item in group],
            rationale=draft.rationale,
            strengths=list(draft.strengths),
            weaknesses=list(draft.weaknesses),
            next_actions=list(draft.next_actions),
            trace_id="draft-validation",
            created_at=datetime.now(UTC),
        )
        validate_marking_decision(
            prompt=prompt,
            response=CandidateResponse(
                response_id="candidate-response",
                prompt_id="quick-practice-prompt",
                actor_id="learner",
                response_mode="text",
                content=response_text,
                submitted_at=datetime.now(UTC),
            ),
            rubric=rubric,
            decision=decision,
        )
    except ValueError as exc:
        raise scoring_error(
            "Assessment output did not satisfy the canonical marking contract",
            code="SS-SCORING-018",
            details={"reason": str(exc)},
        ) from exc
    except AppError as exc:
        raise _map_marking_validation_error(exc) from exc


def _map_marking_validation_error(exc: AppError) -> AppError:
    mapping = {
        "SS-SCORING-010": ("Assessment output repeated a skill score", "SS-SCORING-001"),
        "SS-SCORING-011": (
            "Assessment output did not cover the expected skills",
            "SS-SCORING-002",
        ),
        "SS-SCORING-014": (
            "Evidence must quote the learner response directly",
            "SS-SCORING-004",
        ),
        "SS-SCORING-016": (
            "Assessment strengths and weaknesses contradicted each other",
            "SS-SCORING-005",
        ),
        "SS-SCORING-017": (
            "Overall score was inconsistent with skill-level scores",
            "SS-SCORING-006",
        ),
    }
    message, code = mapping.get(exc.code, (exc.message, exc.code))
    return scoring_error(
        message,
        code=code,
        status_code=exc.status_code,
        details=exc.details,
    )


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())

