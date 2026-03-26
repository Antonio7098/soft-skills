"""Soft-skills adapters over the app-agnostic progression and recommendation engines."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from soft_skills_backend.engines.config import (
    load_progression_engine_config,
    load_recommendation_engine_config,
)
from soft_skills_backend.engines.progression import (
    AggregateDefinition as EngineAggregateDefinition,
)
from soft_skills_backend.engines.progression import (
    AssessmentDimensionScore as EngineAssessmentDimensionScore,
)
from soft_skills_backend.engines.progression import (
    AssessmentEvent as EngineAssessmentEvent,
)
from soft_skills_backend.engines.progression import (
    AssessmentEvidenceReference as EngineAssessmentEvidenceReference,
)
from soft_skills_backend.engines.progression import (
    ComputedProgressionSnapshot as EngineComputedProgressionSnapshot,
)
from soft_skills_backend.engines.progression import (
    PriorProgressState as EnginePriorProgressState,
)
from soft_skills_backend.engines.progression import (
    compute_progression_snapshot as compute_generic_progression_snapshot,
)
from soft_skills_backend.engines.recommendation import (
    CandidateItem as EngineCandidateItem,
)
from soft_skills_backend.engines.recommendation import (
    LearnerContext as EngineLearnerContext,
)
from soft_skills_backend.engines.recommendation import (
    RecommendedCandidate,
)
from soft_skills_backend.engines.recommendation import (
    compute_recommendation as compute_generic_recommendation,
)
from soft_skills_backend.modules.progression.contracts.views import (
    CompetencyProgressView,
    RecommendedContentView,
    SkillContributionView,
    SkillProgressView,
)

PROGRESSION_ENGINE_CONFIG = load_progression_engine_config()
RECOMMENDATION_ENGINE_CONFIG = load_recommendation_engine_config()

PROGRESSION_ENGINE_VERSION = PROGRESSION_ENGINE_CONFIG.engine_version
PROGRESSION_SCHEMA_VERSION = PROGRESSION_ENGINE_CONFIG.schema_version
PROGRESSION_EVIDENCE_LEDGER_SCHEMA_VERSION = (
    PROGRESSION_ENGINE_CONFIG.evidence_ledger_schema_version
)
PROGRESSION_CONFIG_VERSION = PROGRESSION_ENGINE_CONFIG.config_version

RECOMMENDATION_ENGINE_VERSION = RECOMMENDATION_ENGINE_CONFIG.engine_version
RECOMMENDATION_SCHEMA_VERSION = RECOMMENDATION_ENGINE_CONFIG.schema_version
RECOMMENDATION_CONFIG_VERSION = RECOMMENDATION_ENGINE_CONFIG.config_version


class AssessmentSkillScoreSignal(BaseModel):
    """Canonical score signal from a validated assessment."""

    skill_slug: str
    score: int


class AssessmentEvidenceSignal(BaseModel):
    """Evidence signal from a validated assessment."""

    skill_slug: str
    quote: str
    explanation: str


class AssessmentSignal(BaseModel):
    """Canonical validated assessment input."""

    assessment_id: str
    attempt_id: str
    learner_id: str
    created_at: datetime
    prompt_version: str
    rubric_version: str
    trace_id: str
    skill_scores: list[AssessmentSkillScoreSignal] = Field(default_factory=list)
    evidence: list[AssessmentEvidenceSignal] = Field(default_factory=list)


class LearnerProfileInput(BaseModel):
    """Recommendation-relevant learner profile."""

    learner_id: str
    target_role: str | None = None
    goals: list[str] = Field(default_factory=list)


class CompetencyDefinition(BaseModel):
    """Competency-to-skill mapping."""

    competency_slug: str
    skill_weights: dict[str, float] = Field(default_factory=dict)


class CatalogCandidate(BaseModel):
    """Recommendation-ready content candidate."""

    content_id: str
    content_type: str
    collection_id: str
    title: str
    summary: str
    difficulty: str
    verification_state: str
    target_skill_slugs: list[str] = Field(default_factory=list)
    target_competency_slugs: list[str] = Field(default_factory=list)
    rubric_id: str
    lifecycle_state: str
    attempt_count: int = 0
    last_attempted_at: datetime | None = None


class PriorProgressState(BaseModel):
    """Previous persisted scores used for delta reporting."""

    snapshot_id: str
    skill_scores: dict[str, float] = Field(default_factory=dict)
    competency_scores: dict[str, float] = Field(default_factory=dict)


class ComputedProgressSnapshot(BaseModel):
    """Computed snapshot before persistence IDs are assigned."""

    weak_skill_slugs: list[str]
    stagnating_skill_slugs: list[str]
    coverage_gap_skill_slugs: list[str]
    skill_states: list[SkillProgressView]
    competency_states: list[CompetencyProgressView]


class ComputedRecommendation(BaseModel):
    """Computed recommendation artifact before persistence IDs are assigned."""

    context_snapshot_id: str
    candidate_count: int
    items: list[RecommendedContentView]
    alternatives: list[RecommendedContentView]


def compute_progress_snapshot(
    *,
    assessments: list[AssessmentSignal],
    skill_slugs: list[str],
    competency_definitions: list[CompetencyDefinition],
    previous_state: PriorProgressState | None,
    now: datetime,
) -> ComputedProgressSnapshot:
    """Build deterministic skill and competency state from validated history."""

    computed = compute_generic_progression_snapshot(
        assessments=[_to_engine_assessment(assessment) for assessment in assessments],
        dimension_refs=skill_slugs,
        aggregate_definitions=[
            EngineAggregateDefinition(
                aggregate_ref=definition.competency_slug,
                dimension_weights=dict(definition.skill_weights),
            )
            for definition in competency_definitions
        ],
        previous_state=_to_engine_prior_state(previous_state),
        config=PROGRESSION_ENGINE_CONFIG,
        now=now,
    )
    return _from_engine_progress_snapshot(computed)


def compute_recommendation(
    *,
    learner: LearnerProfileInput,
    snapshot: ComputedProgressSnapshot,
    candidates: list[CatalogCandidate],
    now: datetime,
) -> ComputedRecommendation:
    """Score visible content candidates against the current snapshot."""

    computed = compute_generic_recommendation(
        learner=EngineLearnerContext(
            entity_ref=learner.learner_id,
            target_role=learner.target_role,
            goals=list(learner.goals),
        ),
        snapshot=_to_engine_snapshot(snapshot),
        candidates=[
            EngineCandidateItem(
                content_ref=candidate.content_id,
                content_type=candidate.content_type,
                collection_ref=candidate.collection_id,
                title=candidate.title,
                summary=candidate.summary,
                difficulty=candidate.difficulty,
                verification_state=candidate.verification_state,
                target_dimension_refs=list(candidate.target_skill_slugs),
                target_aggregate_refs=list(candidate.target_competency_slugs),
                lifecycle_state=candidate.lifecycle_state,
                attempt_count=candidate.attempt_count,
                last_attempted_at=candidate.last_attempted_at,
            )
            for candidate in candidates
            if candidate.rubric_id
        ],
        config=RECOMMENDATION_ENGINE_CONFIG,
        now=now,
    )
    return ComputedRecommendation(
        context_snapshot_id=computed.context_snapshot_id,
        candidate_count=computed.candidate_count,
        items=[_from_engine_recommendation_item(item) for item in computed.items],
        alternatives=[_from_engine_recommendation_item(item) for item in computed.alternatives],
    )


def build_prior_progress_state(snapshot_payload: dict[str, object] | None) -> PriorProgressState | None:
    """Normalize a persisted snapshot payload into delta-comparison state."""

    if not snapshot_payload:
        return None
    snapshot_id = str(snapshot_payload.get("snapshot_id", "")).strip()
    if not snapshot_id:
        return None
    skill_scores = {
        str(item["skill_slug"]): float(item["score"])
        for item in snapshot_payload.get("skill_states", [])
        if isinstance(item, dict) and "skill_slug" in item and "score" in item
    }
    competency_scores = {
        str(item["competency_slug"]): float(item["score"])
        for item in snapshot_payload.get("competency_states", [])
        if isinstance(item, dict) and "competency_slug" in item and "score" in item
    }
    return PriorProgressState(
        snapshot_id=snapshot_id,
        skill_scores=skill_scores,
        competency_scores=competency_scores,
    )


def diff_summary(
    *,
    previous_state: PriorProgressState | None,
    snapshot: ComputedProgressSnapshot,
) -> dict[str, float | int | str]:
    """Build a compact replay audit summary."""

    if previous_state is None:
        return {
            "changed_skill_count": len(snapshot.skill_states),
            "changed_competency_count": len(snapshot.competency_states),
            "mode": "bootstrap",
        }
    changed_skill_count = sum(
        1
        for state in snapshot.skill_states
        if abs(state.score - previous_state.skill_scores.get(state.skill_slug, 0.0)) > 0.001
    )
    changed_competency_count = sum(
        1
        for state in snapshot.competency_states
        if abs(state.score - previous_state.competency_scores.get(state.competency_slug, 0.0))
        > 0.001
    )
    top_skill = min(snapshot.skill_states, key=lambda item: item.score).skill_slug
    return {
        "changed_skill_count": changed_skill_count,
        "changed_competency_count": changed_competency_count,
        "mode": "replay",
        "lowest_skill": top_skill,
    }


def normalize_score(score: int) -> float:
    """Map rubric 1-5 scores onto the canonical 0-1 scale."""

    return max(0.0, min(1.0, (score - 1) / 4))


def _to_engine_assessment(assessment: AssessmentSignal) -> EngineAssessmentEvent:
    return EngineAssessmentEvent(
        assessment_id=assessment.assessment_id,
        attempt_ref=assessment.attempt_id,
        entity_ref=assessment.learner_id,
        created_at=assessment.created_at,
        prompt_version=assessment.prompt_version,
        rubric_version=assessment.rubric_version,
        trace_id=assessment.trace_id,
        dimension_scores=[
            EngineAssessmentDimensionScore(
                dimension_ref=score.skill_slug,
                normalized_score=normalize_score(score.score),
            )
            for score in assessment.skill_scores
        ],
        evidence=[
            EngineAssessmentEvidenceReference(
                dimension_ref=evidence.skill_slug,
                quote=evidence.quote,
                explanation=evidence.explanation,
            )
            for evidence in assessment.evidence
        ],
    )


def _to_engine_prior_state(previous_state: PriorProgressState | None) -> EnginePriorProgressState | None:
    if previous_state is None:
        return None
    return EnginePriorProgressState(
        snapshot_id=previous_state.snapshot_id,
        dimension_scores=dict(previous_state.skill_scores),
        aggregate_scores=dict(previous_state.competency_scores),
    )


def _to_engine_snapshot(snapshot: ComputedProgressSnapshot) -> EngineComputedProgressionSnapshot:
    return EngineComputedProgressionSnapshot(
        weak_dimension_refs=list(snapshot.weak_skill_slugs),
        stagnating_dimension_refs=list(snapshot.stagnating_skill_slugs),
        coverage_gap_dimension_refs=list(snapshot.coverage_gap_skill_slugs),
        dimension_states=[
            _to_engine_dimension_state(skill_state) for skill_state in snapshot.skill_states
        ],
        aggregate_states=[
            _to_engine_aggregate_state(competency_state)
            for competency_state in snapshot.competency_states
        ],
    )


def _to_engine_dimension_state(skill_state: SkillProgressView):
    from soft_skills_backend.engines.progression.contracts.models import (
        DimensionContribution,
        DimensionState,
    )

    return DimensionState(
        dimension_ref=skill_state.skill_slug,
        score=skill_state.score,
        confidence=skill_state.confidence,
        confidence_band=skill_state.confidence_band,
        evidence_count=skill_state.evidence_count,
        recent_evidence_count=skill_state.recent_evidence_count,
        streak=skill_state.streak,
        delta=skill_state.delta,
        last_assessment_at=skill_state.last_assessment_at,
        contributions=[
            DimensionContribution(
                assessment_id=contribution.assessment_id,
                attempt_ref=contribution.attempt_id,
                normalized_score=contribution.normalized_score,
                weight=contribution.weight,
                contributed_at=contribution.contributed_at,
                prompt_version=contribution.prompt_version,
                rubric_version=contribution.rubric_version,
                trace_id=contribution.trace_id,
                quotes=list(contribution.quotes),
            )
            for contribution in skill_state.contributing_assessments
        ],
    )


def _to_engine_aggregate_state(competency_state: CompetencyProgressView):
    from soft_skills_backend.engines.progression.contracts.models import AggregateState

    return AggregateState(
        aggregate_ref=competency_state.competency_slug,
        score=competency_state.score,
        confidence=competency_state.confidence,
        confidence_band=competency_state.confidence_band,
        delta=competency_state.delta,
        gating_applied=competency_state.gating_applied,
        gating_reasons=list(competency_state.gating_reasons),
        supporting_dimension_refs=list(competency_state.supporting_skill_slugs),
    )


def _from_engine_progress_snapshot(computed: EngineComputedProgressionSnapshot) -> ComputedProgressSnapshot:
    return ComputedProgressSnapshot(
        weak_skill_slugs=list(computed.weak_dimension_refs),
        stagnating_skill_slugs=list(computed.stagnating_dimension_refs),
        coverage_gap_skill_slugs=list(computed.coverage_gap_dimension_refs),
        skill_states=[
            SkillProgressView(
                skill_slug=state.dimension_ref,
                score=state.score,
                confidence=state.confidence,
                confidence_band=state.confidence_band,
                evidence_count=state.evidence_count,
                recent_evidence_count=state.recent_evidence_count,
                streak=state.streak,
                delta=state.delta,
                last_assessment_at=state.last_assessment_at,
                contributing_assessments=[
                    SkillContributionView(
                        assessment_id=contribution.assessment_id,
                        attempt_id=contribution.attempt_ref,
                        normalized_score=contribution.normalized_score,
                        weight=contribution.weight,
                        contributed_at=contribution.contributed_at,
                        prompt_version=contribution.prompt_version,
                        rubric_version=contribution.rubric_version,
                        trace_id=contribution.trace_id,
                        quotes=list(contribution.quotes),
                    )
                    for contribution in state.contributions
                ],
            )
            for state in computed.dimension_states
        ],
        competency_states=[
            CompetencyProgressView(
                competency_slug=state.aggregate_ref,
                score=state.score,
                confidence=state.confidence,
                confidence_band=state.confidence_band,
                delta=state.delta,
                gating_applied=state.gating_applied,
                gating_reasons=list(state.gating_reasons),
                supporting_skill_slugs=list(state.supporting_dimension_refs),
            )
            for state in computed.aggregate_states
        ],
    )


def _from_engine_recommendation_item(item: RecommendedCandidate) -> RecommendedContentView:
    return RecommendedContentView(
        content_id=item.content_ref,
        content_type=item.content_type,
        collection_id=item.collection_ref,
        title=item.title,
        difficulty=item.difficulty,
        score=item.score,
        component_breakdown=_rename_component_breakdown(item.component_breakdown),
        reasons=[_rename_reason(reason) for reason in item.reasons],
        cooldown_expires_at=item.cooldown_expires_at,
        verification_state=item.verification_state,
        target_skill_slugs=list(item.target_dimension_refs),
        target_competency_slugs=list(item.target_aggregate_refs),
    )


def _rename_component_breakdown(components: dict[str, float]) -> dict[str, float]:
    renamed: dict[str, float] = {}
    for key, value in components.items():
        if key == "dimension_deficit_alignment":
            renamed["skill_deficit_alignment"] = value
            continue
        renamed[key] = value
    return renamed


def _rename_reason(reason: str) -> str:
    if reason.startswith("weak_dimension:"):
        return reason.replace("weak_dimension:", "weak_skill:", 1)
    return reason
