"""Contracts for the app-agnostic marking engine."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


def _default_rubric_levels() -> list[RubricLevel]:
    return [
        RubricLevel(level=1, description="Poor demonstration.", examples=["Weak evidence."]),
        RubricLevel(level=2, description="Limited demonstration.", examples=["Partial evidence."]),
        RubricLevel(level=3, description="Adequate demonstration.", examples=["Acceptable evidence."]),
        RubricLevel(level=4, description="Strong demonstration.", examples=["Strong evidence."]),
        RubricLevel(level=5, description="Excellent demonstration.", examples=["Compelling evidence."]),
    ]


class PromptTemplate(BaseModel):
    """Versioned prompt template used to render an evaluator prompt."""

    name: str
    version: str
    template: str


class RenderedPrompt(BaseModel):
    """Resolved prompt payload with stable version metadata."""

    name: str
    version: str
    content: str


class PromptArtifact(BaseModel):
    """Optional structured context supplied alongside a prompt."""

    artifact_id: str
    artifact_type: str
    title: str
    body: str


class PromptContract(BaseModel):
    """Versioned marking prompt contract."""

    prompt_id: str
    prompt_version: str
    prompt_type: str
    prompt_text: str
    response_mode: str
    rubric_id: str
    artifacts: list[PromptArtifact] = Field(default_factory=list)
    domain_tags: list[str] = Field(default_factory=list)

    @field_validator(
        "prompt_id",
        "prompt_version",
        "prompt_type",
        "prompt_text",
        "response_mode",
        "rubric_id",
    )
    @classmethod
    def _require_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Value must not be blank")
        return cleaned


class CandidateResponse(BaseModel):
    """Canonical response contract submitted for marking."""

    response_id: str
    prompt_id: str
    actor_id: str
    response_mode: str
    content: str
    submitted_at: datetime

    @field_validator("response_id", "prompt_id", "actor_id", "response_mode", "content")
    @classmethod
    def _require_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Value must not be blank")
        return cleaned


class RubricScale(BaseModel):
    """Numeric scale used by a rubric."""

    minimum_score: int
    maximum_score: int


class RubricLevel(BaseModel):
    """One scored rubric level with examples."""

    level: int = Field(ge=1)
    description: str
    examples: list[str] = Field(min_length=1)

    @field_validator("description")
    @classmethod
    def _require_description(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Value must not be blank")
        return cleaned

    @field_validator("examples", mode="after")
    @classmethod
    def _clean_examples(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values if value.strip()]
        if not cleaned:
            raise ValueError("List must contain at least one non-blank item")
        return cleaned


class RubricCriterion(BaseModel):
    """One rubric criterion."""

    criterion_ref: str
    title: str | None = None
    description: str
    weight: float = Field(default=1.0, gt=0)
    required: bool = True
    levels: list[RubricLevel] = Field(default_factory=_default_rubric_levels, min_length=1)

    @field_validator("criterion_ref", "description")
    @classmethod
    def _require_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Value must not be blank")
        return cleaned

    @field_validator("title")
    @classmethod
    def _clean_optional_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class RubricDefinition(BaseModel):
    """Versioned rubric contract."""

    rubric_id: str
    rubric_version: str
    scale: RubricScale
    criteria: list[RubricCriterion] = Field(min_length=1)

    @field_validator("rubric_id", "rubric_version")
    @classmethod
    def _require_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Value must not be blank")
        return cleaned


class EvidenceReference(BaseModel):
    """Response-linked evidence supporting a judgment."""

    criterion_ref: str
    quote: str
    explanation: str

    @field_validator("criterion_ref", "quote", "explanation")
    @classmethod
    def _require_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Value must not be blank")
        return cleaned


class CriterionJudgment(BaseModel):
    """Judgment for a single rubric criterion."""

    criterion_ref: str
    score: int
    rationale: str
    evidence: list[EvidenceReference] = Field(min_length=1)

    @field_validator("criterion_ref", "rationale")
    @classmethod
    def _require_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Value must not be blank")
        return cleaned


class MarkingDecision(BaseModel):
    """Finalized generic marking decision contract."""

    marking_id: str
    response_id: str
    prompt_id: str
    prompt_version: str
    rubric_id: str
    rubric_version: str
    engine_version: str
    provider: str
    model_slug: str
    overall_score: int
    criterion_judgments: list[CriterionJudgment] = Field(min_length=1)
    rationale: str
    strengths: list[str] = Field(min_length=1)
    weaknesses: list[str] = Field(min_length=1)
    next_actions: list[str] = Field(min_length=1)
    trace_id: str
    created_at: datetime

    @field_validator(
        "marking_id",
        "response_id",
        "prompt_id",
        "prompt_version",
        "rubric_id",
        "rubric_version",
        "engine_version",
        "provider",
        "model_slug",
        "rationale",
        "trace_id",
    )
    @classmethod
    def _require_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Value must not be blank")
        return cleaned

    @field_validator("strengths", "weaknesses", "next_actions", mode="after")
    @classmethod
    def _clean_lists(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values if value.strip()]
        if not cleaned:
            raise ValueError("List must contain at least one non-blank item")
        return cleaned
