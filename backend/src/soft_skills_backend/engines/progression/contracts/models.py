"""Contracts for the app-agnostic progression engine."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AssessmentDimensionScore(BaseModel):
    """Canonical dimension score from a validated assessment."""

    dimension_ref: str
    normalized_score: float = Field(ge=0.0, le=1.0)


class AssessmentEvidenceReference(BaseModel):
    """Evidence linked to a dimension score."""

    dimension_ref: str
    quote: str
    explanation: str


class AssessmentEvent(BaseModel):
    """Validated assessment event consumed by the progression engine."""

    assessment_id: str
    attempt_ref: str
    entity_ref: str
    created_at: datetime
    prompt_version: str
    rubric_version: str
    trace_id: str
    dimension_scores: list[AssessmentDimensionScore] = Field(default_factory=list)
    evidence: list[AssessmentEvidenceReference] = Field(default_factory=list)


class AggregateDefinition(BaseModel):
    """Weighted aggregate of dimensions."""

    aggregate_ref: str
    dimension_weights: dict[str, float] = Field(default_factory=dict)


class AggregateGateRule(BaseModel):
    """Optional gate preventing an aggregate from exceeding a ceiling."""

    aggregate_ref: str
    dimension_ref: str
    floor: float = Field(ge=0.0, le=1.0)
    ceiling: float = Field(ge=0.0, le=1.0)


class DecayProfileConfig(BaseModel):
    """Decay config applied to historical evidence."""

    retention_window_days: int = Field(default=180, ge=1)
    minimum_weight: float = Field(default=0.35, ge=0.0, le=1.0)


class ConfidenceProfileConfig(BaseModel):
    """Confidence config based on evidence volume and recency."""

    min_recent_evidence: int = Field(default=2, ge=1)
    min_total_evidence: int = Field(default=3, ge=1)
    recent_window_days: int = Field(default=30, ge=1)


class ProgressionEngineConfig(BaseModel):
    """Versioned config artifact for the progression engine."""

    engine_version: str
    schema_version: str
    evidence_ledger_schema_version: str
    config_version: str
    decay_profile: DecayProfileConfig = Field(default_factory=DecayProfileConfig)
    confidence_profile: ConfidenceProfileConfig = Field(default_factory=ConfidenceProfileConfig)
    aggregate_gate_rules: list[AggregateGateRule] = Field(default_factory=list)
    weak_dimension_threshold: float = Field(default=0.65, ge=0.0, le=1.0)
    stagnation_score_threshold: float = Field(default=0.75, ge=0.0, le=1.0)
    stagnation_delta_threshold: float = Field(default=0.05, ge=0.0)


class PriorProgressState(BaseModel):
    """Previous persisted scores used for delta reporting."""

    snapshot_id: str
    dimension_scores: dict[str, float] = Field(default_factory=dict)
    aggregate_scores: dict[str, float] = Field(default_factory=dict)


class DimensionContribution(BaseModel):
    """Explainability ledger item for one assessment contribution."""

    assessment_id: str
    attempt_ref: str
    normalized_score: float
    weight: float
    contributed_at: str
    prompt_version: str
    rubric_version: str
    trace_id: str
    quotes: list[str] = Field(default_factory=list)


class DimensionState(BaseModel):
    """Current state for one dimension."""

    dimension_ref: str
    score: float
    confidence: float
    confidence_band: str
    evidence_count: int
    recent_evidence_count: int
    streak: int
    delta: float
    last_assessment_at: str | None = None
    contributions: list[DimensionContribution] = Field(default_factory=list)


class AggregateState(BaseModel):
    """Current state for one aggregate."""

    aggregate_ref: str
    score: float
    confidence: float
    confidence_band: str
    delta: float
    gating_applied: bool = False
    gating_reasons: list[str] = Field(default_factory=list)
    supporting_dimension_refs: list[str] = Field(default_factory=list)


class ComputedProgressionSnapshot(BaseModel):
    """Computed progression snapshot before persistence IDs are assigned."""

    weak_dimension_refs: list[str] = Field(default_factory=list)
    stagnating_dimension_refs: list[str] = Field(default_factory=list)
    coverage_gap_dimension_refs: list[str] = Field(default_factory=list)
    dimension_states: list[DimensionState] = Field(default_factory=list)
    aggregate_states: list[AggregateState] = Field(default_factory=list)
