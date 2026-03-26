"""Domain logic for the app-agnostic recommendation engine."""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime, timedelta

from soft_skills_backend.engines.progression.contracts.models import (
    ComputedProgressionSnapshot,
    DimensionState,
)
from soft_skills_backend.engines.recommendation.contracts.models import (
    CandidateItem,
    ComputedRecommendation,
    LearnerContext,
    RecommendationEngineConfig,
    RecommendedCandidate,
)
from soft_skills_backend.shared.errors import validation_error


def compute_recommendation(
    *,
    learner: LearnerContext,
    snapshot: ComputedProgressionSnapshot,
    candidates: list[CandidateItem],
    config: RecommendationEngineConfig,
    now: datetime,
) -> ComputedRecommendation:
    """Score visible content candidates against the current snapshot."""

    if not candidates:
        raise validation_error(
            "Recommendation generation requires at least one candidate",
            code="SS-VALIDATION-031",
            status_code=422,
        )

    dimension_map = {state.dimension_ref: state for state in snapshot.dimension_states}
    aggregate_map = {state.aggregate_ref: state for state in snapshot.aggregate_states}
    goal_tokens = _goal_tokens(learner)
    ranked: list[tuple[float, RecommendedCandidate]] = []
    for candidate in candidates:
        if not candidate.target_dimension_refs:
            continue
        if config.allowed_lifecycle_states and candidate.lifecycle_state not in set(
            config.allowed_lifecycle_states
        ):
            continue
        if (
            candidate.difficulty in set(config.advanced_difficulty_labels)
            and candidate.target_aggregate_refs
        ):
            readiness = max(
                (
                    aggregate_map[aggregate_ref].score
                    for aggregate_ref in candidate.target_aggregate_refs
                    if aggregate_ref in aggregate_map
                ),
                default=0.0,
            )
            if readiness < config.advanced_readiness_threshold:
                continue

        components = _recommendation_components(
            candidate=candidate,
            dimension_map=dimension_map,
            goal_tokens=goal_tokens,
            config=config,
            now=now,
        )
        total = (
            config.weights.dimension_deficit_alignment * components["dimension_deficit_alignment"]
            + config.weights.stagnation_relief * components["stagnation_relief"]
            + config.weights.coverage_gap_fit * components["coverage_gap_fit"]
            + config.weights.goal_alignment * components["goal_alignment"]
            + config.weights.verification_boost * components["verification_boost"]
            - components["recent_repeat_penalty"]
        )
        ranked.append(
            (
                total,
                RecommendedCandidate(
                    content_ref=candidate.content_ref,
                    content_type=candidate.content_type,
                    collection_ref=candidate.collection_ref,
                    title=candidate.title,
                    difficulty=candidate.difficulty,
                    score=_round(total),
                    component_breakdown={key: _round(value) for key, value in components.items()},
                    reasons=_reason_codes(candidate, dimension_map, goal_tokens, config),
                    cooldown_expires_at=_cooldown_expires_at(candidate, config, now),
                    verification_state=candidate.verification_state,
                    target_dimension_refs=list(candidate.target_dimension_refs),
                    target_aggregate_refs=list(candidate.target_aggregate_refs),
                ),
            )
        )

    ranked.sort(key=lambda item: (-item[0], item[1].title, item[1].content_ref))
    selected = [item for _, item in ranked if item.score > config.minimum_score][
        : config.max_recommendations
    ]
    alternatives = [
        item
        for _, item in ranked[config.max_recommendations :]
        if item.score > config.minimum_score
    ][: config.max_alternatives]
    if not selected:
        raise validation_error(
            "Recommendation generation produced no valid candidates",
            code="SS-VALIDATION-032",
            status_code=422,
        )
    context_snapshot_id = hashlib.sha256(
        "|".join(
            [
                learner.entity_ref,
                ",".join(sorted(snapshot.weak_dimension_refs)),
                ",".join(sorted(candidate.content_ref for candidate in candidates)),
            ]
        ).encode("utf-8")
    ).hexdigest()[:24]
    return ComputedRecommendation(
        context_snapshot_id=context_snapshot_id,
        candidate_count=len(ranked),
        items=selected,
        alternatives=alternatives,
    )


def _recommendation_components(
    *,
    candidate: CandidateItem,
    dimension_map: dict[str, DimensionState],
    goal_tokens: set[str],
    config: RecommendationEngineConfig,
    now: datetime,
) -> dict[str, float]:
    now = _as_utc(now)
    overlapping_states = [
        dimension_map[dimension_ref]
        for dimension_ref in candidate.target_dimension_refs
        if dimension_ref in dimension_map
    ]
    deficit_values = [
        (1 - state.score) * max(state.confidence, 0.35)
        for state in overlapping_states
        if state.evidence_count > 0
    ]
    stagnation_values = [
        1 - state.score
        for state in overlapping_states
        if abs(state.delta) < 0.05 and state.evidence_count >= 2
    ]
    coverage_values = [1 - min(1.0, state.evidence_count / 2) for state in overlapping_states]
    verification_boost = 0.5 if candidate.verification_state in set(config.verified_states) else 0.0
    repeat_penalty = 0.0
    if candidate.last_attempted_at is not None:
        last_attempted_at = _as_utc(candidate.last_attempted_at)
        if last_attempted_at >= now - timedelta(hours=config.cooldown_hours):
            repeat_penalty = config.immediate_repeat_penalty
        else:
            repeat_penalty = min(
                config.repeat_penalty_cap,
                candidate.attempt_count * config.repeat_penalty_per_attempt,
            )
    return {
        "dimension_deficit_alignment": _average(deficit_values),
        "stagnation_relief": _average(stagnation_values),
        "coverage_gap_fit": _average(coverage_values),
        "goal_alignment": _goal_alignment(candidate, goal_tokens),
        "verification_boost": verification_boost,
        "recent_repeat_penalty": repeat_penalty,
    }


def _reason_codes(
    candidate: CandidateItem,
    dimension_map: dict[str, DimensionState],
    goal_tokens: set[str],
    config: RecommendationEngineConfig,
) -> list[str]:
    reasons: list[str] = []
    weak_overlap = sorted(
        (
            state
            for state in (
                dimension_map.get(dimension_ref)
                for dimension_ref in candidate.target_dimension_refs
            )
            if state is not None and state.evidence_count > 0 and state.score < 0.65
        ),
        key=lambda state: (state.score, state.dimension_ref),
    )
    if weak_overlap:
        reasons.append(f"weak_dimension:{weak_overlap[0].dimension_ref}")
    stagnating_overlap = sorted(
        (
            state
            for state in (
                dimension_map.get(dimension_ref)
                for dimension_ref in candidate.target_dimension_refs
            )
            if state is not None and state.evidence_count >= 2 and abs(state.delta) < 0.05
        ),
        key=lambda state: (state.score, state.dimension_ref),
    )
    if stagnating_overlap:
        reasons.append(f"stagnation:{stagnating_overlap[0].dimension_ref}")
    coverage_overlap = sorted(
        (
            state
            for state in (
                dimension_map.get(dimension_ref)
                for dimension_ref in candidate.target_dimension_refs
            )
            if state is not None and state.evidence_count < 2
        ),
        key=lambda state: (state.evidence_count, state.dimension_ref),
    )
    if coverage_overlap:
        reasons.append(f"coverage_gap:{coverage_overlap[0].dimension_ref}")
    matched_goal_token = _matched_goal_token(candidate, goal_tokens)
    if matched_goal_token is not None:
        reasons.append(f"goal_match:{matched_goal_token}")
    if candidate.verification_state in set(config.verified_states):
        reasons.append("verified_content")
    return reasons


def _cooldown_expires_at(
    candidate: CandidateItem,
    config: RecommendationEngineConfig,
    now: datetime,
) -> str | None:
    if candidate.last_attempted_at is None:
        return None
    expires_at = _as_utc(candidate.last_attempted_at) + timedelta(hours=config.cooldown_hours)
    now = _as_utc(now)
    if expires_at <= now:
        return None
    return expires_at.isoformat()


def _goal_alignment(candidate: CandidateItem, goal_tokens: set[str]) -> float:
    if not goal_tokens:
        return 0.0
    haystack = _candidate_text(candidate)
    matched = goal_tokens & haystack
    if not matched:
        return 0.0
    return min(1.0, len(matched) / max(1, len(goal_tokens)))


def _matched_goal_token(candidate: CandidateItem, goal_tokens: set[str]) -> str | None:
    matches = sorted(goal_tokens & _candidate_text(candidate))
    return matches[0] if matches else None


def _candidate_text(candidate: CandidateItem) -> set[str]:
    text = " ".join(
        [
            candidate.title,
            candidate.summary,
            candidate.difficulty,
            " ".join(candidate.target_dimension_refs),
            " ".join(candidate.target_aggregate_refs),
        ]
    )
    return _tokenize(text)


def _goal_tokens(learner: LearnerContext) -> set[str]:
    tokens = set()
    if learner.target_role:
        tokens |= _tokenize(learner.target_role)
    for goal in learner.goals:
        tokens |= _tokenize(goal)
    return tokens


def _tokenize(value: str) -> set[str]:
    return {token for token in re.split(r"[^a-z0-9]+", value.lower()) if len(token) >= 4}


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _round(value: float) -> float:
    return round(value, 4)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
