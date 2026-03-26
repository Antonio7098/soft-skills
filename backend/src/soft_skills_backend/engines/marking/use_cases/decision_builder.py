"""Reusable helpers for building canonical marking decisions."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from pydantic import BaseModel

from soft_skills_backend.engines.marking.contracts.models import (
    CriterionJudgment,
    EvidenceReference,
    MarkingDecision,
    PromptContract,
    RubricDefinition,
)


class CriterionResultInput(BaseModel):
    """Raw criterion result before evidence is attached."""

    criterion_ref: str
    score: int
    rationale: str


def build_marking_decision(
    *,
    marking_id: str,
    prompt: PromptContract,
    response_id: str,
    rubric: RubricDefinition,
    engine_version: str,
    provider: str,
    model_slug: str,
    overall_score: int,
    criterion_results: list[CriterionResultInput],
    evidence: list[EvidenceReference],
    rationale: str,
    strengths: list[str],
    weaknesses: list[str],
    next_actions: list[str],
    trace_id: str,
    created_at: datetime,
) -> MarkingDecision:
    """Build a canonical marking decision from criterion results and evidence."""

    evidence_by_criterion: dict[str, list[EvidenceReference]] = defaultdict(list)
    for item in evidence:
        evidence_by_criterion[item.criterion_ref].append(item)
    return MarkingDecision(
        marking_id=marking_id,
        response_id=response_id,
        prompt_id=prompt.prompt_id,
        prompt_version=prompt.prompt_version,
        rubric_id=rubric.rubric_id,
        rubric_version=rubric.rubric_version,
        engine_version=engine_version,
        provider=provider,
        model_slug=model_slug,
        overall_score=overall_score,
        criterion_judgments=[
            CriterionJudgment(
                criterion_ref=result.criterion_ref,
                score=result.score,
                rationale=result.rationale,
                evidence=evidence_by_criterion.get(result.criterion_ref, []),
            )
            for result in criterion_results
        ],
        rationale=rationale,
        strengths=list(strengths),
        weaknesses=list(weaknesses),
        next_actions=list(next_actions),
        trace_id=trace_id,
        created_at=created_at,
    )
