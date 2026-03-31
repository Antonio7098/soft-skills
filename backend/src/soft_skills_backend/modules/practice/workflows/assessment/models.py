"""Assessment domain models."""

from __future__ import annotations

from pydantic import BaseModel, Field

from soft_skills_backend.engines.marking.contracts.models import (
    PromptTemplate as EnginePromptTemplate,
)
from soft_skills_backend.engines.marking.contracts.models import (
    RenderedPrompt as EngineRenderedPrompt,
)
from soft_skills_backend.modules.practice.domain.practice import (
    AssessmentDraft,
    PerSkillAssessment,
    PracticeType,
)

PromptTemplate = EnginePromptTemplate
RenderedPrompt = EngineRenderedPrompt


class LearnerContextPayload(BaseModel):
    """Learner enrichment data."""

    target_role: str | None = None
    goals: list[str] = Field(default_factory=list)
    prior_assessed_attempts: int = 0


class PracticeArtifactView(BaseModel):
    """Artifact included in a practice prompt."""

    artifact_id: str
    artifact_type: str
    title: str
    body: str


class ScenarioCompanyView(BaseModel):
    """Scenario company context."""

    name: str
    industry: str
    operating_context: str


class ScenarioActorView(BaseModel):
    """Scenario stakeholder context."""

    name: str
    role: str
    goals: list[str] = Field(default_factory=list)
    communication_style: str
    relationship_to_scenario: str


class ScenarioContextView(BaseModel):
    """Scenario-specific prompt context."""

    business_context: str
    learner_objective: str
    constraints: list[str] = Field(default_factory=list)
    stakeholder_tensions: list[str] = Field(default_factory=list)
    mock_company: ScenarioCompanyView | None = None
    mock_people: list[ScenarioActorView] = Field(default_factory=list)
    artifacts: list[PracticeArtifactView] = Field(default_factory=list)


class InterviewContextView(BaseModel):
    """Interview-specific prompt context."""

    competency_context: str | None = None
    interviewer_perspective: str | None = None


class PracticePromptView(BaseModel):
    """Prompt delivery payload."""

    practice_type: PracticeType
    content_item_id: str
    content_item_type: str
    prompt_type: str
    title: str
    prompt_text: str
    difficulty: str
    delivery_version: str
    response_mode: str = "text"
    target_skill_slugs: list[str]
    rubric_id: str
    rubric_version: str
    scenario_context: ScenarioContextView | None = None
    interview_context: InterviewContextView | None = None


AssessmentPromptView = PracticePromptView


class ResolvedAttemptPayload(BaseModel):
    """Attempt plus prompt/rubric metadata for assessment."""

    attempt_id: str
    session_id: str
    workflow_id: str
    response_text: str
    prompt: PracticePromptView


class AssessmentTransformPayload(BaseModel):
    """Typed provider output before domain validation."""

    draft: AssessmentDraft
    per_skill_assessments: list[PerSkillAssessment] = Field(default_factory=list)
    raw_payload: dict[str, object]
    model_slug: str
    schema_version: str
    usage: dict[str, int] = Field(default_factory=dict)


class AssessmentAggregationOutput(BaseModel):
    """Aggregation LLM output after per-skill validation."""

    summary: str
    next_actions: list[str] = Field(min_length=1)
