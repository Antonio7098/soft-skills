"""Contracts for the app-agnostic recommendation engine."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class LearnerContext(BaseModel):
    """Recommendation-relevant learner context."""

    entity_ref: str
    target_role: str | None = None
    goals: list[str] = Field(default_factory=list)
    persona_tags: list[str] = Field(default_factory=list)


class CandidateItem(BaseModel):
    """Recommendation-ready content candidate."""

    content_ref: str
    content_type: str
    collection_ref: str
    title: str
    summary: str
    difficulty: str
    verification_state: str
    target_dimension_refs: list[str] = Field(default_factory=list)
    target_aggregate_refs: list[str] = Field(default_factory=list)
    lifecycle_state: str
    attempt_count: int = 0
    last_attempted_at: datetime | None = None


class RecommendationWeights(BaseModel):
    """Weighted scoring components."""

    dimension_deficit_alignment: float = Field(ge=0.0)
    stagnation_relief: float = Field(ge=0.0)
    coverage_gap_fit: float = Field(ge=0.0)
    goal_alignment: float = Field(ge=0.0)
    verification_boost: float = Field(ge=0.0)


class RecommendationEngineConfig(BaseModel):
    """Versioned config artifact for the recommendation engine."""

    engine_version: str
    schema_version: str
    config_version: str
    weights: RecommendationWeights
    cooldown_hours: int = Field(default=12, ge=1)
    max_recommendations: int = Field(default=3, ge=1)
    max_alternatives: int = Field(default=2, ge=0)
    minimum_score: float = 0.0
    allowed_lifecycle_states: list[str] = Field(default_factory=list)
    verified_states: list[str] = Field(default_factory=list)
    advanced_difficulty_labels: list[str] = Field(default_factory=list)
    advanced_readiness_threshold: float = Field(default=0.45, ge=0.0, le=1.0)
    immediate_repeat_penalty: float = Field(default=0.08, ge=0.0)
    repeat_penalty_cap: float = Field(default=0.08, ge=0.0)
    repeat_penalty_per_attempt: float = Field(default=0.02, ge=0.0)


class RecommendedCandidate(BaseModel):
    """One ranked recommendation candidate."""

    content_ref: str
    content_type: str
    collection_ref: str
    title: str
    difficulty: str
    score: float
    component_breakdown: dict[str, float] = Field(default_factory=dict)
    reasons: list[str] = Field(default_factory=list)
    cooldown_expires_at: str | None = None
    verification_state: str
    target_dimension_refs: list[str] = Field(default_factory=list)
    target_aggregate_refs: list[str] = Field(default_factory=list)


class ComputedRecommendation(BaseModel):
    """Computed recommendation artifact before persistence IDs are assigned."""

    context_snapshot_id: str
    candidate_count: int
    items: list[RecommendedCandidate]
    alternatives: list[RecommendedCandidate]
