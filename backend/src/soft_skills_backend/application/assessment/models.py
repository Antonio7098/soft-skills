"""Assessment domain models."""

from __future__ import annotations

from pydantic import BaseModel, Field

from soft_skills_backend.domain.practice import QuickPracticeAssessmentDraft


class PromptTemplate(BaseModel):
    """Versioned prompt template."""

    name: str
    version: str
    template: str


class RenderedPrompt(BaseModel):
    """Rendered prompt payload with version metadata."""

    name: str
    version: str
    content: str


class LearnerContextPayload(BaseModel):
    """Learner enrichment data."""

    target_role: str | None = None
    goals: list[str] = Field(default_factory=list)
    prior_assessed_attempts: int = 0


class QuickPracticePromptView(BaseModel):
    """Prompt delivery payload."""

    content_item_id: str
    prompt_type: str
    title: str
    prompt_text: str
    difficulty: str
    delivery_version: str
    target_skill_slugs: list[str]
    rubric_id: str
    rubric_version: str


class ResolvedAttemptPayload(BaseModel):
    """Attempt plus prompt/rubric metadata for assessment."""

    attempt_id: str
    session_id: str
    workflow_id: str
    response_text: str
    prompt: QuickPracticePromptView


class AssessmentTransformPayload(BaseModel):
    """Typed provider output before domain validation."""

    draft: QuickPracticeAssessmentDraft
    raw_payload: dict[str, object]
    model_slug: str
    schema_version: str
