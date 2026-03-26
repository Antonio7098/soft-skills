"""Progression and recommendation domain logic."""

from __future__ import annotations

import hashlib
import math
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from pydantic import BaseModel, Field

from soft_skills_backend.modules.progression.contracts.views import (
    CompetencyProgressView,
    RecommendedContentView,
    SkillContributionView,
    SkillProgressView,
)
from soft_skills_backend.shared.errors import domain_error, validation_error

PROGRESSION_ENGINE_VERSION = "progression-engine.v1"
PROGRESSION_SCHEMA_VERSION = "progression-snapshot.v1"
PROGRESSION_EVIDENCE_LEDGER_SCHEMA_VERSION = "progression-evidence-ledger.v1"
PROGRESSION_CONFIG_VERSION = "progress-config-2026-03"

RECOMMENDATION_ENGINE_VERSION = "recommendation-engine.v1"
RECOMMENDATION_SCHEMA_VERSION = "recommendation-output.v1"
RECOMMENDATION_CONFIG_VERSION = "rec-config-2026-03"

MIN_RECENT_EVIDENCE = 2
MIN_TOTAL_EVIDENCE = 3
RECENT_WINDOW_DAYS = 30
RETENTION_WINDOW_DAYS = 180
COOLDOWN_HOURS = 12
MAX_RECOMMENDATIONS = 3
MAX_ALTERNATIVES = 2

COMPETENCY_GATING_RULES: dict[str, tuple[tuple[str, float, float], ...]] = {
    "stakeholder-management": (("expectation-setting", 0.40, 0.60),),
}


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


@dataclass(frozen=True, slots=True)
class _SkillAggregate:
    skill_slug: str
    score: float
    confidence: float
    evidence_count: int
    recent_evidence_count: int
    streak: int
    last_assessment_at: datetime | None
    contributions: tuple[SkillContributionView, ...]


def compute_progress_snapshot(
    *,
    assessments: list[AssessmentSignal],
    skill_slugs: list[str],
    competency_definitions: list[CompetencyDefinition],
    previous_state: PriorProgressState | None,
    now: datetime,
) -> ComputedProgressSnapshot:
    """Build deterministic skill and competency state from validated history."""

    if not assessments:
        raise domain_error(
            "Progression requires at least one validated assessment",
            code="SS-DOMAIN-017",
            status_code=404,
        )

    skill_state_map = {
        aggregate.skill_slug: aggregate
        for aggregate in (
            _compute_skill_aggregate(
                skill_slug=skill_slug,
                assessments=assessments,
                previous_state=previous_state,
                now=now,
            )
            for skill_slug in skill_slugs
        )
    }
    skill_states = [
        SkillProgressView(
            skill_slug=skill_slug,
            score=_round(aggregate.score),
            confidence=_round(aggregate.confidence),
            confidence_band=_confidence_band(aggregate.confidence),
            evidence_count=aggregate.evidence_count,
            recent_evidence_count=aggregate.recent_evidence_count,
            streak=aggregate.streak,
            delta=_round(
                aggregate.score - (previous_state.skill_scores.get(skill_slug, 0.0) if previous_state else 0.0)
            ),
            last_assessment_at=(
                None if aggregate.last_assessment_at is None else aggregate.last_assessment_at.isoformat()
            ),
            contributing_assessments=list(aggregate.contributions),
        )
        for skill_slug, aggregate in sorted(skill_state_map.items())
    ]

    competency_states: list[CompetencyProgressView] = []
    for definition in competency_definitions:
        raw_score = 0.0
        raw_confidence = 0.0
        gating_reasons: list[str] = []
        for skill_slug, weight in definition.skill_weights.items():
            aggregate = skill_state_map[skill_slug]
            raw_score += aggregate.score * weight
            raw_confidence += aggregate.confidence * weight
        score = raw_score
        for skill_slug, floor, ceiling in COMPETENCY_GATING_RULES.get(definition.competency_slug, ()):
            aggregate = skill_state_map.get(skill_slug)
            if aggregate is None:
                continue
            if aggregate.score < floor and score > ceiling:
                score = ceiling
                gating_reasons.append(f"{skill_slug}_floor")
        prior_score = previous_state.competency_scores.get(definition.competency_slug, 0.0) if previous_state else 0.0
        competency_states.append(
            CompetencyProgressView(
                competency_slug=definition.competency_slug,
                score=_round(score),
                confidence=_round(raw_confidence),
                confidence_band=_confidence_band(raw_confidence),
                delta=_round(score - prior_score),
                gating_applied=bool(gating_reasons),
                gating_reasons=gating_reasons,
                supporting_skill_slugs=sorted(definition.skill_weights),
            )
        )

    weak_skill_slugs = [
        state.skill_slug
        for state in skill_states
        if state.evidence_count > 0 and state.score < 0.65
    ]
    stagnating_skill_slugs = [
        state.skill_slug
        for state in skill_states
        if state.evidence_count >= 2 and state.score < 0.75 and abs(state.delta) < 0.05
    ]
    coverage_gap_skill_slugs = [
        state.skill_slug
        for state in skill_states
        if state.evidence_count < MIN_RECENT_EVIDENCE
    ]
    return ComputedProgressSnapshot(
        weak_skill_slugs=weak_skill_slugs,
        stagnating_skill_slugs=stagnating_skill_slugs,
        coverage_gap_skill_slugs=coverage_gap_skill_slugs,
        skill_states=skill_states,
        competency_states=sorted(competency_states, key=lambda item: item.competency_slug),
    )


def compute_recommendation(
    *,
    learner: LearnerProfileInput,
    snapshot: ComputedProgressSnapshot,
    candidates: list[CatalogCandidate],
    now: datetime,
) -> ComputedRecommendation:
    """Score visible content candidates against the current snapshot."""

    if not candidates:
        raise validation_error(
            "Recommendation generation requires at least one candidate",
            code="SS-VALIDATION-031",
            status_code=422,
        )

    skill_map = {state.skill_slug: state for state in snapshot.skill_states}
    competency_map = {state.competency_slug: state for state in snapshot.competency_states}
    goal_tokens = _goal_tokens(learner)
    ranked: list[tuple[float, RecommendedContentView]] = []
    for candidate in candidates:
        if not candidate.rubric_id or not candidate.target_skill_slugs:
            continue
        if candidate.lifecycle_state not in {"published_public", "published_private", "draft", "review"}:
            continue
        if candidate.difficulty == "advanced" and candidate.target_competency_slugs:
            readiness = max(
                (competency_map.get(slug).score for slug in candidate.target_competency_slugs if slug in competency_map),
                default=0.0,
            )
            if readiness < 0.45:
                continue

        components = _recommendation_components(
            candidate=candidate,
            skill_map=skill_map,
            goal_tokens=goal_tokens,
            now=now,
        )
        total = (
            0.40 * components["skill_deficit_alignment"]
            + 0.20 * components["stagnation_relief"]
            + 0.15 * components["coverage_gap_fit"]
            + 0.15 * components["goal_alignment"]
            + 0.10 * components["verification_boost"]
            - components["recent_repeat_penalty"]
        )
        ranked.append(
            (
                total,
                RecommendedContentView(
                    content_id=candidate.content_id,
                    content_type=candidate.content_type,
                    collection_id=candidate.collection_id,
                    title=candidate.title,
                    difficulty=candidate.difficulty,
                    score=_round(total),
                    component_breakdown={key: _round(value) for key, value in components.items()},
                    reasons=_reason_codes(candidate, skill_map, goal_tokens),
                    cooldown_expires_at=_cooldown_expires_at(candidate, now),
                    verification_state=candidate.verification_state,
                    target_skill_slugs=list(candidate.target_skill_slugs),
                    target_competency_slugs=list(candidate.target_competency_slugs),
                ),
            )
        )

    ranked.sort(key=lambda item: (-item[0], item[1].title, item[1].content_id))
    selected = [item for _, item in ranked if item.score > 0][:MAX_RECOMMENDATIONS]
    alternatives = [item for _, item in ranked[MAX_RECOMMENDATIONS:] if item.score > 0][:MAX_ALTERNATIVES]
    if not selected:
        raise validation_error(
            "Recommendation generation produced no valid candidates",
            code="SS-VALIDATION-032",
            status_code=422,
        )
    context_snapshot_id = hashlib.sha256(
        "|".join(
            [
                learner.learner_id,
                ",".join(sorted(snapshot.weak_skill_slugs)),
                ",".join(sorted(candidate.content_id for candidate in candidates)),
            ]
        ).encode("utf-8")
    ).hexdigest()[:24]
    return ComputedRecommendation(
        context_snapshot_id=context_snapshot_id,
        candidate_count=len(ranked),
        items=selected,
        alternatives=alternatives,
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
        if not math.isclose(state.score, previous_state.skill_scores.get(state.skill_slug, 0.0), abs_tol=0.001)
    )
    changed_competency_count = sum(
        1
        for state in snapshot.competency_states
        if not math.isclose(
            state.score,
            previous_state.competency_scores.get(state.competency_slug, 0.0),
            abs_tol=0.001,
        )
    )
    top_skill = min(snapshot.skill_states, key=lambda item: item.score).skill_slug
    return {
        "changed_skill_count": changed_skill_count,
        "changed_competency_count": changed_competency_count,
        "mode": "replay",
        "lowest_skill": top_skill,
    }


def _compute_skill_aggregate(
    *,
    skill_slug: str,
    assessments: list[AssessmentSignal],
    previous_state: PriorProgressState | None,
    now: datetime,
) -> _SkillAggregate:
    now = _as_utc(now)
    matching_scores: list[tuple[AssessmentSignal, AssessmentSkillScoreSignal]] = []
    for assessment in assessments:
        for score in assessment.skill_scores:
            if score.skill_slug == skill_slug:
                matching_scores.append((assessment, score))
                break
    if not matching_scores:
        return _SkillAggregate(
            skill_slug=skill_slug,
            score=0.0,
            confidence=0.0,
            evidence_count=0,
            recent_evidence_count=0,
            streak=0,
            last_assessment_at=None,
            contributions=tuple(),
        )

    total_weight = 0.0
    weighted_score = 0.0
    recent_evidence_count = 0
    streak = 0
    contributions: list[SkillContributionView] = []
    for assessment, score_signal in sorted(matching_scores, key=lambda item: item[0].created_at):
        assessment_at = _as_utc(assessment.created_at)
        normalized = normalize_score(score_signal.score)
        weight = _decay_weight(assessment_at, now)
        total_weight += weight
        weighted_score += normalized * weight
        if assessment_at >= now - timedelta(days=RECENT_WINDOW_DAYS):
            recent_evidence_count += 1
        if normalized >= 0.60:
            streak += 1
        else:
            streak = 0
        contributions.append(
            SkillContributionView(
                assessment_id=assessment.assessment_id,
                attempt_id=assessment.attempt_id,
                normalized_score=_round(normalized),
                weight=_round(weight),
                contributed_at=assessment_at.isoformat(),
                prompt_version=assessment.prompt_version,
                rubric_version=assessment.rubric_version,
                trace_id=assessment.trace_id,
                quotes=[
                    evidence.quote
                    for evidence in assessment.evidence
                    if evidence.skill_slug == skill_slug
                ],
            )
        )
    score = weighted_score / total_weight if total_weight else 0.0
    last_assessment_at = _as_utc(matching_scores[-1][0].created_at)
    confidence = _confidence(
        evidence_count=len(matching_scores),
        recent_evidence_count=recent_evidence_count,
        last_assessment_at=last_assessment_at,
        now=now,
    )
    return _SkillAggregate(
        skill_slug=skill_slug,
        score=score,
        confidence=confidence,
        evidence_count=len(matching_scores),
        recent_evidence_count=recent_evidence_count,
        streak=streak,
        last_assessment_at=last_assessment_at,
        contributions=tuple(reversed(contributions)),
    )


def normalize_score(score: int) -> float:
    """Map rubric 1-5 scores onto the canonical 0-1 scale."""

    return max(0.0, min(1.0, (score - 1) / 4))


def _decay_weight(assessment_at: datetime, now: datetime) -> float:
    assessment_at = _as_utc(assessment_at)
    now = _as_utc(now)
    age_days = max(0, (now - assessment_at).days)
    if age_days >= RETENTION_WINDOW_DAYS:
        return 0.35
    return max(0.35, 1.0 - (age_days / RETENTION_WINDOW_DAYS) * 0.65)


def _confidence(
    *,
    evidence_count: int,
    recent_evidence_count: int,
    last_assessment_at: datetime,
    now: datetime,
) -> float:
    last_assessment_at = _as_utc(last_assessment_at)
    now = _as_utc(now)
    evidence_ratio = min(1.0, evidence_count / MIN_TOTAL_EVIDENCE)
    recent_ratio = min(1.0, recent_evidence_count / MIN_RECENT_EVIDENCE)
    age_days = max(0, (now - last_assessment_at).days)
    recency = max(0.0, 1.0 - (age_days / RETENTION_WINDOW_DAYS))
    return min(1.0, evidence_ratio * 0.45 + recent_ratio * 0.35 + recency * 0.20)


def _confidence_band(confidence: float) -> str:
    if confidence >= 0.75:
        return "high"
    if confidence >= 0.40:
        return "medium"
    return "low"


def _recommendation_components(
    *,
    candidate: CatalogCandidate,
    skill_map: dict[str, SkillProgressView],
    goal_tokens: set[str],
    now: datetime,
) -> dict[str, float]:
    now = _as_utc(now)
    overlapping_states = [
        skill_map[skill_slug]
        for skill_slug in candidate.target_skill_slugs
        if skill_slug in skill_map
    ]
    deficit_values = [
        (1 - state.score) * max(state.confidence, 0.35)
        for state in overlapping_states
        if state.evidence_count > 0
    ]
    stagnation_values = [
        1 - state.score
        for state in overlapping_states
        if state.skill_slug and state.skill_slug and abs(state.delta) < 0.05 and state.evidence_count >= 2
    ]
    coverage_values = [
        1 - min(1.0, state.evidence_count / MIN_RECENT_EVIDENCE)
        for state in overlapping_states
    ]
    verification_boost = 0.5 if candidate.verification_state == "verified" else 0.0
    repeat_penalty = 0.0
    if candidate.last_attempted_at is not None:
        last_attempted_at = _as_utc(candidate.last_attempted_at)
        if last_attempted_at >= now - timedelta(hours=COOLDOWN_HOURS):
            repeat_penalty = 0.08
        else:
            repeat_penalty = min(0.08, candidate.attempt_count * 0.02)
    return {
        "skill_deficit_alignment": _average(deficit_values),
        "stagnation_relief": _average(stagnation_values),
        "coverage_gap_fit": _average(coverage_values),
        "goal_alignment": _goal_alignment(candidate, goal_tokens),
        "verification_boost": verification_boost,
        "recent_repeat_penalty": repeat_penalty,
    }


def _reason_codes(
    candidate: CatalogCandidate,
    skill_map: dict[str, SkillProgressView],
    goal_tokens: set[str],
) -> list[str]:
    reasons: list[str] = []
    weak_overlap = sorted(
        (
            state for state in (skill_map.get(skill_slug) for skill_slug in candidate.target_skill_slugs)
            if state is not None and state.evidence_count > 0 and state.score < 0.65
        ),
        key=lambda state: (state.score, state.skill_slug),
    )
    if weak_overlap:
        reasons.append(f"weak_skill:{weak_overlap[0].skill_slug}")
    stagnating_overlap = sorted(
        (
            state for state in (skill_map.get(skill_slug) for skill_slug in candidate.target_skill_slugs)
            if state is not None and state.evidence_count >= 2 and abs(state.delta) < 0.05
        ),
        key=lambda state: (state.score, state.skill_slug),
    )
    if stagnating_overlap:
        reasons.append(f"stagnation:{stagnating_overlap[0].skill_slug}")
    coverage_overlap = sorted(
        (
            state for state in (skill_map.get(skill_slug) for skill_slug in candidate.target_skill_slugs)
            if state is not None and state.evidence_count < MIN_RECENT_EVIDENCE
        ),
        key=lambda state: (state.evidence_count, state.skill_slug),
    )
    if coverage_overlap:
        reasons.append(f"coverage_gap:{coverage_overlap[0].skill_slug}")
    matched_goal_token = _matched_goal_token(candidate, goal_tokens)
    if matched_goal_token is not None:
        reasons.append(f"goal_match:{matched_goal_token}")
    if candidate.verification_state == "verified":
        reasons.append("verified_content")
    return reasons


def _cooldown_expires_at(candidate: CatalogCandidate, now: datetime) -> str | None:
    if candidate.last_attempted_at is None:
        return None
    expires_at = _as_utc(candidate.last_attempted_at) + timedelta(hours=COOLDOWN_HOURS)
    now = _as_utc(now)
    if expires_at <= now:
        return None
    return expires_at.isoformat()


def _goal_alignment(candidate: CatalogCandidate, goal_tokens: set[str]) -> float:
    if not goal_tokens:
        return 0.0
    haystack = _candidate_text(candidate)
    matched = goal_tokens & haystack
    if not matched:
        return 0.0
    return min(1.0, len(matched) / max(1, len(goal_tokens)))


def _matched_goal_token(candidate: CatalogCandidate, goal_tokens: set[str]) -> str | None:
    matches = sorted(goal_tokens & _candidate_text(candidate))
    return matches[0] if matches else None


def _candidate_text(candidate: CatalogCandidate) -> set[str]:
    text = " ".join(
        [
            candidate.title,
            candidate.summary,
            candidate.difficulty,
            " ".join(candidate.target_skill_slugs),
            " ".join(candidate.target_competency_slugs),
        ]
    )
    return _tokenize(text)


def _goal_tokens(learner: LearnerProfileInput) -> set[str]:
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
