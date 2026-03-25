"""Practice domain models."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from soft_skills_backend.application.assessment.models import QuickPracticePromptView
from soft_skills_backend.domain.practice import (
    AssessmentValidationStatus,
    AttemptStatus,
    EvidenceItem,
    SessionStatus,
    SkillScore,
)


class PracticeCorrelation(BaseModel):
    """Request-bound correlation fields."""

    request_id: str
    trace_id: str
    workflow_id: str | None = None


class StartInputPayload(BaseModel):
    """Validated start input."""

    prompt_item_id: str


class PromptContextPayload(BaseModel):
    """Prompt and rubric context resolved from persistence."""

    content_item_id: str
    content_item_type: str
    prompt_type: str
    title: str
    prompt_text: str
    difficulty: str
    target_skill_slugs: list[str]
    rubric_id: str
    rubric_version: str


class SessionTransformPayload(BaseModel):
    """Payload prepared for session persistence."""

    session_id: str
    attempt_id: str
    workflow_id: str
    prompt: QuickPracticePromptView


class AttemptGuardPayload(BaseModel):
    """Validated attempt submission context."""

    attempt_id: str
    session_id: str
    workflow_id: str
    response_text: str


class ValidatedAssessmentPayload(BaseModel):
    """Assessment artifact ready for durable persistence."""

    prompt_version: str
    rubric_id: str
    rubric_version: str
    provider: str
    model_slug: str
    schema_version: str
    config_version: str
    overall_score: int
    rationale: str
    skill_scores: list[SkillScore]
    evidence: list[EvidenceItem]
    strengths: list[str]
    weaknesses: list[str]
    next_actions: list[str]
    raw_payload: dict[str, object]


class QuickPracticeSessionView(BaseModel):
    """Session start response."""

    session_id: str
    attempt_id: str
    workflow_id: str
    status: SessionStatus
    prompt: QuickPracticePromptView
    started_at: str
    trace_id: str


class QuickPracticeAssessmentView(BaseModel):
    """Learner-facing assessment artifact."""

    assessment_id: str
    attempt_id: str
    session_id: str
    validation_status: AssessmentValidationStatus
    prompt_version: str
    rubric_id: str
    rubric_version: str
    schema_version: str
    config_version: str
    provider: str
    model_slug: str
    overall_score: int | None = None
    skill_scores: list[SkillScore] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    rationale: str | None = None
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    trace_id: str
    pipeline_run_id: str
    rejection_code: str | None = None
    created_at: str


class QuickPracticeAttemptView(BaseModel):
    """Attempt API view."""

    id: str
    session_id: str
    workflow_id: str
    status: AttemptStatus
    response_mode: str
    response_text: str | None = None
    last_error_code: str | None = None
    submitted_at: str | None = None
    assessed_at: str | None = None
    prompt: QuickPracticePromptView
    assessment: QuickPracticeAssessmentView | None = None


class StartQuickPracticeSessionCommand(BaseModel):
    """Quick-practice session start payload."""

    prompt_item_id: str

    @field_validator("prompt_item_id")
    @classmethod
    def _require_prompt_item_id(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("prompt_item_id must not be blank")
        return cleaned


class SubmitAttemptCommand(BaseModel):
    """Attempt submission payload."""

    response_text: str

    @field_validator("response_text")
    @classmethod
    def _require_response_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("response_text must not be blank")
        return cleaned


AttemptView = QuickPracticeAttemptView
