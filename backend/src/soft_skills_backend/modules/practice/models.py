"""Practice domain models."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from soft_skills_backend.modules.practice.domain.practice import (
    AssessmentValidationStatus,
    AttemptStatus,
    EvidenceItem,
    PracticeType,
    SessionStatus,
    SkillScore,
)
from soft_skills_backend.modules.practice.workflows.assessment.models import (
    InterviewContextView,
    PracticeArtifactView,
    PracticePromptView,
)


class PracticeCorrelation(BaseModel):
    """Request-bound correlation fields."""

    request_id: str
    trace_id: str
    workflow_id: str | None = None


class StartInputPayload(BaseModel):
    """Validated start input."""

    practice_type: PracticeType
    content_item_id: str
    interview_context: InterviewContextView | None = None
    artifacts: list[PracticeArtifactView] = Field(default_factory=list)


class PromptContextPayload(BaseModel):
    """Prompt and rubric context resolved from persistence."""

    prompt: PracticePromptView


class SessionTransformPayload(BaseModel):
    """Payload prepared for session persistence."""

    session_id: str
    attempt_id: str
    workflow_id: str
    prompt: PracticePromptView


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


class PracticeSessionView(BaseModel):
    """Session start response."""

    session_id: str
    attempt_id: str
    workflow_id: str
    status: SessionStatus
    prompt: PracticePromptView
    started_at: str
    trace_id: str


class PracticeAssessmentView(BaseModel):
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


class PracticeAttemptView(BaseModel):
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
    prompt: PracticePromptView
    assessment: PracticeAssessmentView | None = None


class StartPracticeSessionCommand(BaseModel):
    """Quick-practice session start payload."""

    prompt_item_id: str

    @field_validator("prompt_item_id")
    @classmethod
    def _require_prompt_item_id(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("prompt_item_id must not be blank")
        return cleaned


class StartInterviewSessionCommand(BaseModel):
    """Interview session start payload."""

    prompt_item_id: str
    competency_context: str | None = None
    interviewer_perspective: str | None = None

    @field_validator("prompt_item_id")
    @classmethod
    def _require_prompt_item_id(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("prompt_item_id must not be blank")
        return cleaned

    @field_validator("competency_context", "interviewer_perspective")
    @classmethod
    def _normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class ScenarioArtifactInput(BaseModel):
    """Scenario artifact provided at runtime."""

    artifact_type: str
    title: str
    body: str

    @field_validator("artifact_type", "title", "body")
    @classmethod
    def _require_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("artifact fields must not be blank")
        return cleaned


class StartScenarioSessionCommand(BaseModel):
    """Scenario session start payload."""

    scenario_id: str
    artifacts: list[ScenarioArtifactInput] = Field(default_factory=list)

    @field_validator("scenario_id")
    @classmethod
    def _require_scenario_id(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("scenario_id must not be blank")
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

AttemptView = PracticeAttemptView
