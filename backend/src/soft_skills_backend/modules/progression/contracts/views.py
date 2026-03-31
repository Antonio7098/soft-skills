from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SkillContributionView(BaseModel):
    """Explainability ledger item for one assessment contribution."""

    assessment_id: str
    attempt_id: str
    normalized_score: float
    weight: float
    contributed_at: str
    prompt_version: str
    rubric_version: str
    trace_id: str
    quotes: list[str] = Field(default_factory=list)


class SkillProgressView(BaseModel):
    """Learner-facing skill progress state."""

    skill_slug: str
    score: float
    confidence: float
    confidence_band: str
    evidence_count: int
    recent_evidence_count: int
    streak: int
    delta: float
    last_assessment_at: str | None = None
    contributing_assessments: list[SkillContributionView] = Field(default_factory=list)


class CompetencyProgressView(BaseModel):
    """Aggregated competency state."""

    competency_slug: str
    score: float
    confidence: float
    confidence_band: str
    delta: float
    gating_applied: bool = False
    gating_reasons: list[str] = Field(default_factory=list)
    supporting_skill_slugs: list[str] = Field(default_factory=list)


class ProgressSnapshotView(BaseModel):
    """Persisted progression snapshot."""

    snapshot_id: str
    learner_id: str
    source_assessment_id: str
    created_at: str
    engine_version: str
    schema_version: str
    config_version: str
    evidence_ledger_schema_version: str
    trace_id: str
    weak_skill_slugs: list[str] = Field(default_factory=list)
    stagnating_skill_slugs: list[str] = Field(default_factory=list)
    coverage_gap_skill_slugs: list[str] = Field(default_factory=list)
    skill_states: list[SkillProgressView] = Field(default_factory=list)
    competency_states: list[CompetencyProgressView] = Field(default_factory=list)


class RecommendedContentView(BaseModel):
    """One ranked recommendation candidate."""

    content_id: str
    content_type: str
    collection_id: str
    title: str
    difficulty: str
    score: float
    component_breakdown: dict[str, float] = Field(default_factory=dict)
    reasons: list[str] = Field(default_factory=list)
    cooldown_expires_at: str | None = None
    verification_state: str
    target_skill_slugs: list[str] = Field(default_factory=list)
    target_competency_slugs: list[str] = Field(default_factory=list)


class RecommendationView(BaseModel):
    """Persisted recommendation artifact."""

    recommendation_id: str
    learner_id: str
    progress_snapshot_id: str
    generated_at: str
    engine_version: str
    schema_version: str
    config_version: str
    trace_id: str
    context_snapshot_id: str
    candidate_count: int
    items: list[RecommendedContentView] = Field(default_factory=list)
    alternatives: list[RecommendedContentView] = Field(default_factory=list)


class ProgressDashboardView(BaseModel):
    """Current learner progress and recommendations."""

    snapshot: ProgressSnapshotView
    recommendation: RecommendationView


class ProgressRecalculationView(BaseModel):
    """Audit payload for a replay/recalculation run."""

    recalculation_id: str
    learner_id: str
    reason: str
    status: str
    started_at: str
    completed_at: str | None = None
    assessment_count: int
    previous_snapshot_id: str | None = None
    next_snapshot_id: str | None = None
    next_recommendation_id: str | None = None
    config_version: str
    diff_summary: dict[str, float | int | str] = Field(default_factory=dict)


class SkillHistoryPointView(BaseModel):
    """Single skill state at a point in time."""

    skill_slug: str
    score: float
    confidence: float
    confidence_band: str
    evidence_count: int
    delta: float
    recorded_at: str


class CompetencyHistoryPointView(BaseModel):
    """Single competency state at a point in time."""

    competency_slug: str
    score: float
    confidence: float
    confidence_band: str
    delta: float
    recorded_at: str


class ProgressHistorySnapshotView(BaseModel):
    """Lightweight snapshot for history list."""

    snapshot_id: str
    recorded_at: str
    source_assessment_id: str
    skill_states: list[SkillHistoryPointView] = Field(default_factory=list)
    competency_states: list[CompetencyHistoryPointView] = Field(default_factory=list)
    weak_skill_slugs: list[str] = Field(default_factory=list)
    stagnating_skill_slugs: list[str] = Field(default_factory=list)
    coverage_gap_skill_slugs: list[str] = Field(default_factory=list)


class ProgressHistoryView(BaseModel):
    """Collection of progress snapshots over time."""

    learner_id: str
    snapshots: list[ProgressHistorySnapshotView] = Field(default_factory=list)
    from_date: str | None = None
    to_date: str | None = None


class SkillTimelinePointView(BaseModel):
    """Single data point for a skill timeline."""

    recorded_at: str
    score: float
    confidence: float
    evidence_count: int
    delta: float
    source_assessment_id: str


class SkillTimelineView(BaseModel):
    """Time-series data for a specific skill."""

    skill_slug: str
    skill_name: str
    points: list[SkillTimelinePointView] = Field(default_factory=list)
    from_date: str | None = None
    to_date: str | None = None
    overall_change: float = 0.0
    trend: Literal["improving", "declining", "stable"] = "stable"
