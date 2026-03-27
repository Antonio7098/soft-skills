"""Deterministic aggregation helpers for per-skill marking."""

from __future__ import annotations

from statistics import fmean

from soft_skills_backend.engines.marking import RubricCriterion
from soft_skills_backend.modules.practice.domain.practice import PerSkillAssessment


def compute_overall_score(
    *,
    criteria: list[RubricCriterion],
    assessments: list[PerSkillAssessment],
) -> int:
    """Compute the rounded weighted mean score."""

    assessment_by_skill = {item.skill_slug: item for item in assessments}
    weighted_scores: list[float] = []
    weights: list[float] = []
    for criterion in criteria:
        assessment = assessment_by_skill.get(criterion.criterion_ref)
        if assessment is None:
            continue
        weighted_scores.append(assessment.score * criterion.weight)
        weights.append(criterion.weight)
    if not weights:
        return round(fmean(item.score for item in assessments))
    return round(sum(weighted_scores) / sum(weights))


def compute_strengths(
    *,
    criteria: list[RubricCriterion],
    assessments: list[PerSkillAssessment],
) -> list[str]:
    """Render grounded strengths from the top-ranked skill results."""

    top_items = _ranked(criteria=criteria, assessments=assessments, reverse=True)
    count = 2 if len(top_items) >= 5 else 1
    strengths: list[str] = []
    for item in top_items[:count]:
        strengths.append(f"{item.skill_slug}: {item.rationale}")
    return strengths or [f"{assessments[0].skill_slug}: {assessments[0].rationale}"]


def compute_weaknesses(
    *,
    criteria: list[RubricCriterion],
    assessments: list[PerSkillAssessment],
) -> list[str]:
    """Render grounded weaknesses from the bottom-ranked skill results."""

    bottom_items = _ranked(criteria=criteria, assessments=assessments, reverse=False)
    count = 2 if len(bottom_items) >= 5 else 1
    weaknesses: list[str] = []
    for item in bottom_items[:count]:
        text = f"{item.skill_slug}: {item.rationale}"
        if item.evidence:
            text += f' (e.g. "{item.evidence[0].quote}")'
        weaknesses.append(text)
    return weaknesses or [f"{assessments[0].skill_slug}: {assessments[0].rationale}"]


def _ranked(
    *,
    criteria: list[RubricCriterion],
    assessments: list[PerSkillAssessment],
    reverse: bool,
) -> list[PerSkillAssessment]:
    weights = {criterion.criterion_ref: criterion.weight for criterion in criteria}
    return sorted(
        assessments,
        key=lambda item: (item.score, weights.get(item.skill_slug, 1.0)),
        reverse=reverse,
    )
