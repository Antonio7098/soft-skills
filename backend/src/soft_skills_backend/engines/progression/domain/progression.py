"""Domain logic for the app-agnostic progression engine."""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from soft_skills_backend.engines.progression.contracts.models import (
    AggregateDefinition,
    AggregateState,
    AssessmentDimensionScore,
    AssessmentEvent,
    ComputedProgressionSnapshot,
    DimensionContribution,
    DimensionState,
    PriorProgressState,
    ProgressionEngineConfig,
)
from soft_skills_backend.shared.errors import domain_error


@dataclass(frozen=True, slots=True)
class _DimensionAggregate:
    dimension_ref: str
    score: float
    confidence: float
    evidence_count: int
    recent_evidence_count: int
    streak: int
    last_assessment_at: datetime | None
    contributions: tuple[DimensionContribution, ...]


def compute_progression_snapshot(
    *,
    assessments: list[AssessmentEvent],
    dimension_refs: list[str],
    aggregate_definitions: list[AggregateDefinition],
    previous_state: PriorProgressState | None,
    config: ProgressionEngineConfig,
    now: datetime,
) -> ComputedProgressionSnapshot:
    """Build deterministic dimension and aggregate state from validated history."""

    if not assessments:
        raise domain_error(
            "Progression requires at least one validated assessment",
            code="SS-DOMAIN-017",
            status_code=404,
        )

    dimension_state_map = {
        aggregate.dimension_ref: aggregate
        for aggregate in (
            _compute_dimension_aggregate(
                dimension_ref=dimension_ref,
                assessments=assessments,
                previous_state=previous_state,
                config=config,
                now=now,
            )
            for dimension_ref in dimension_refs
        )
    }
    dimension_states = [
        DimensionState(
            dimension_ref=dimension_ref,
            score=_round(aggregate.score),
            confidence=_round(aggregate.confidence),
            confidence_band=_confidence_band(aggregate.confidence),
            evidence_count=aggregate.evidence_count,
            recent_evidence_count=aggregate.recent_evidence_count,
            streak=aggregate.streak,
            delta=_round(
                aggregate.score
                - (
                    previous_state.dimension_scores.get(dimension_ref, 0.0)
                    if previous_state
                    else 0.0
                )
            ),
            last_assessment_at=(
                None
                if aggregate.last_assessment_at is None
                else aggregate.last_assessment_at.isoformat()
            ),
            contributions=list(aggregate.contributions),
        )
        for dimension_ref, aggregate in sorted(dimension_state_map.items())
    ]

    gate_rules_by_aggregate: dict[str, list[tuple[str, float, float]]] = defaultdict(list)
    for rule in config.aggregate_gate_rules:
        gate_rules_by_aggregate[rule.aggregate_ref].append(
            (rule.dimension_ref, rule.floor, rule.ceiling)
        )

    aggregate_states: list[AggregateState] = []
    for definition in aggregate_definitions:
        raw_score = 0.0
        raw_confidence = 0.0
        gating_reasons: list[str] = []
        for dimension_ref, weight in definition.dimension_weights.items():
            aggregate = dimension_state_map[dimension_ref]
            raw_score += aggregate.score * weight
            raw_confidence += aggregate.confidence * weight
        score = raw_score
        for dimension_ref, floor, ceiling in gate_rules_by_aggregate.get(
            definition.aggregate_ref, []
        ):
            gate_aggregate = dimension_state_map.get(dimension_ref)
            if gate_aggregate is None:
                continue
            if gate_aggregate.score < floor and score > ceiling:
                score = ceiling
                gating_reasons.append(f"{dimension_ref}_floor")
        prior_score = (
            previous_state.aggregate_scores.get(definition.aggregate_ref, 0.0)
            if previous_state
            else 0.0
        )
        aggregate_states.append(
            AggregateState(
                aggregate_ref=definition.aggregate_ref,
                score=_round(score),
                confidence=_round(raw_confidence),
                confidence_band=_confidence_band(raw_confidence),
                delta=_round(score - prior_score),
                gating_applied=bool(gating_reasons),
                gating_reasons=gating_reasons,
                supporting_dimension_refs=sorted(definition.dimension_weights),
            )
        )

    weak_dimension_refs = [
        state.dimension_ref
        for state in dimension_states
        if state.evidence_count > 0 and state.score < config.weak_dimension_threshold
    ]
    stagnating_dimension_refs = [
        state.dimension_ref
        for state in dimension_states
        if state.evidence_count >= config.confidence_profile.min_recent_evidence
        and state.score < config.stagnation_score_threshold
        and abs(state.delta) < config.stagnation_delta_threshold
    ]
    coverage_gap_dimension_refs = [
        state.dimension_ref
        for state in dimension_states
        if state.evidence_count < config.confidence_profile.min_recent_evidence
    ]
    return ComputedProgressionSnapshot(
        weak_dimension_refs=weak_dimension_refs,
        stagnating_dimension_refs=stagnating_dimension_refs,
        coverage_gap_dimension_refs=coverage_gap_dimension_refs,
        dimension_states=dimension_states,
        aggregate_states=sorted(aggregate_states, key=lambda item: item.aggregate_ref),
    )


def diff_summary(
    *,
    previous_state: PriorProgressState | None,
    snapshot: ComputedProgressionSnapshot,
) -> dict[str, float | int | str]:
    """Build a compact replay audit summary."""

    if previous_state is None:
        return {
            "changed_dimension_count": len(snapshot.dimension_states),
            "changed_aggregate_count": len(snapshot.aggregate_states),
            "mode": "bootstrap",
        }
    changed_dimension_count = sum(
        1
        for state in snapshot.dimension_states
        if not math.isclose(
            state.score,
            previous_state.dimension_scores.get(state.dimension_ref, 0.0),
            abs_tol=0.001,
        )
    )
    changed_aggregate_count = sum(
        1
        for state in snapshot.aggregate_states
        if not math.isclose(
            state.score,
            previous_state.aggregate_scores.get(state.aggregate_ref, 0.0),
            abs_tol=0.001,
        )
    )
    lowest_dimension = min(snapshot.dimension_states, key=lambda item: item.score).dimension_ref
    return {
        "changed_dimension_count": changed_dimension_count,
        "changed_aggregate_count": changed_aggregate_count,
        "mode": "replay",
        "lowest_dimension": lowest_dimension,
    }


def _compute_dimension_aggregate(
    *,
    dimension_ref: str,
    assessments: list[AssessmentEvent],
    previous_state: PriorProgressState | None,
    config: ProgressionEngineConfig,
    now: datetime,
) -> _DimensionAggregate:
    del previous_state
    now = _as_utc(now)
    matching_scores: list[tuple[AssessmentEvent, AssessmentDimensionScore]] = []
    for assessment in assessments:
        for score in assessment.dimension_scores:
            if score.dimension_ref == dimension_ref:
                matching_scores.append((assessment, score))
                break
    if not matching_scores:
        return _DimensionAggregate(
            dimension_ref=dimension_ref,
            score=0.0,
            confidence=0.0,
            evidence_count=0,
            recent_evidence_count=0,
            streak=0,
            last_assessment_at=None,
            contributions=(),
        )

    total_weight = 0.0
    weighted_score = 0.0
    recent_evidence_count = 0
    streak = 0
    contributions: list[DimensionContribution] = []
    for assessment, score_signal in sorted(matching_scores, key=lambda item: item[0].created_at):
        assessment_at = _as_utc(assessment.created_at)
        weight = _decay_weight(assessment_at=assessment_at, now=now, config=config)
        total_weight += weight
        weighted_score += score_signal.normalized_score * weight
        if assessment_at >= now - timedelta(days=config.confidence_profile.recent_window_days):
            recent_evidence_count += 1
        if score_signal.normalized_score >= 0.60:
            streak += 1
        else:
            streak = 0
        contributions.append(
            DimensionContribution(
                assessment_id=assessment.assessment_id,
                attempt_ref=assessment.attempt_ref,
                normalized_score=_round(score_signal.normalized_score),
                weight=_round(weight),
                contributed_at=assessment_at.isoformat(),
                prompt_version=assessment.prompt_version,
                rubric_version=assessment.rubric_version,
                trace_id=assessment.trace_id,
                quotes=[
                    evidence.quote
                    for evidence in assessment.evidence
                    if evidence.dimension_ref == dimension_ref
                ],
            )
        )
    computed_score = weighted_score / total_weight if total_weight else 0.0
    last_assessment_at = _as_utc(matching_scores[-1][0].created_at)
    confidence = _confidence(
        evidence_count=len(matching_scores),
        recent_evidence_count=recent_evidence_count,
        last_assessment_at=last_assessment_at,
        config=config,
        now=now,
    )
    return _DimensionAggregate(
        dimension_ref=dimension_ref,
        score=computed_score,
        confidence=confidence,
        evidence_count=len(matching_scores),
        recent_evidence_count=recent_evidence_count,
        streak=streak,
        last_assessment_at=last_assessment_at,
        contributions=tuple(reversed(contributions)),
    )


def _decay_weight(
    *,
    assessment_at: datetime,
    now: datetime,
    config: ProgressionEngineConfig,
) -> float:
    assessment_at = _as_utc(assessment_at)
    now = _as_utc(now)
    age_days = max(0, (now - assessment_at).days)
    if age_days >= config.decay_profile.retention_window_days:
        return config.decay_profile.minimum_weight
    slope = (1.0 - config.decay_profile.minimum_weight) / config.decay_profile.retention_window_days
    return max(config.decay_profile.minimum_weight, 1.0 - age_days * slope)


def _confidence(
    *,
    evidence_count: int,
    recent_evidence_count: int,
    last_assessment_at: datetime,
    config: ProgressionEngineConfig,
    now: datetime,
) -> float:
    last_assessment_at = _as_utc(last_assessment_at)
    now = _as_utc(now)
    evidence_ratio = min(1.0, evidence_count / config.confidence_profile.min_total_evidence)
    recent_ratio = min(1.0, recent_evidence_count / config.confidence_profile.min_recent_evidence)
    age_days = max(0, (now - last_assessment_at).days)
    recency = max(0.0, 1.0 - (age_days / config.decay_profile.retention_window_days))
    return min(1.0, evidence_ratio * 0.45 + recent_ratio * 0.35 + recency * 0.20)


def _confidence_band(confidence: float) -> str:
    if confidence >= 0.75:
        return "high"
    if confidence >= 0.40:
        return "medium"
    return "low"


def _round(value: float) -> float:
    return round(value, 4)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
