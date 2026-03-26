"""Validation rules for the app-agnostic marking engine."""

from __future__ import annotations

import re

from soft_skills_backend.engines.marking.contracts.models import (
    CandidateResponse,
    MarkingDecision,
    PromptContract,
    RubricDefinition,
)
from soft_skills_backend.shared.errors import scoring_error, validation_error


def validate_marking_decision(
    *,
    prompt: PromptContract,
    response: CandidateResponse,
    rubric: RubricDefinition,
    decision: MarkingDecision,
) -> None:
    """Validate a finalized marking decision against the canonical contracts."""

    if decision.prompt_id != prompt.prompt_id:
        raise validation_error(
            "Marking decision prompt_id did not match the prompt contract",
            code="SS-VALIDATION-034",
            details={"expected_prompt_id": prompt.prompt_id, "observed_prompt_id": decision.prompt_id},
        )
    if decision.response_id != response.response_id:
        raise validation_error(
            "Marking decision response_id did not match the response contract",
            code="SS-VALIDATION-035",
            details={
                "expected_response_id": response.response_id,
                "observed_response_id": decision.response_id,
            },
        )
    if decision.prompt_version != prompt.prompt_version:
        raise validation_error(
            "Marking decision prompt_version did not match the prompt contract",
            code="SS-VALIDATION-036",
            details={
                "expected_prompt_version": prompt.prompt_version,
                "observed_prompt_version": decision.prompt_version,
            },
        )
    if decision.rubric_id != rubric.rubric_id or decision.rubric_version != rubric.rubric_version:
        raise validation_error(
            "Marking decision rubric metadata did not match the rubric contract",
            code="SS-VALIDATION-037",
            details={
                "expected_rubric_id": rubric.rubric_id,
                "observed_rubric_id": decision.rubric_id,
                "expected_rubric_version": rubric.rubric_version,
                "observed_rubric_version": decision.rubric_version,
            },
        )

    criterion_refs = {criterion.criterion_ref for criterion in rubric.criteria if criterion.required}
    observed_refs = [judgment.criterion_ref for judgment in decision.criterion_judgments]
    if len(set(observed_refs)) != len(observed_refs):
        raise scoring_error(
            "Marking decision repeated a criterion judgment",
            code="SS-SCORING-010",
            details={"criterion_refs": observed_refs},
        )
    if set(observed_refs) != criterion_refs:
        raise scoring_error(
            "Marking decision did not cover the rubric criteria",
            code="SS-SCORING-011",
            details={
                "expected_criteria": sorted(criterion_refs),
                "observed_criteria": sorted(observed_refs),
            },
        )

    normalized_response = _normalize_text(response.content)
    for judgment in decision.criterion_judgments:
        if judgment.score < rubric.scale.minimum_score or judgment.score > rubric.scale.maximum_score:
            raise scoring_error(
                "Criterion score fell outside the rubric scale",
                code="SS-SCORING-012",
                details={
                    "criterion_ref": judgment.criterion_ref,
                    "score": judgment.score,
                    "minimum_score": rubric.scale.minimum_score,
                    "maximum_score": rubric.scale.maximum_score,
                },
            )
        for evidence in judgment.evidence:
            if evidence.criterion_ref != judgment.criterion_ref:
                raise scoring_error(
                    "Evidence criterion_ref did not match its judgment",
                    code="SS-SCORING-013",
                    details={
                        "judgment_criterion_ref": judgment.criterion_ref,
                        "evidence_criterion_ref": evidence.criterion_ref,
                    },
                )
            if len(evidence.quote.strip()) < 6 or _normalize_text(evidence.quote) not in normalized_response:
                raise scoring_error(
                    "Evidence must quote the candidate response directly",
                    code="SS-SCORING-014",
                    details={"criterion_ref": judgment.criterion_ref, "quote": evidence.quote},
                )

    if decision.overall_score < rubric.scale.minimum_score or decision.overall_score > rubric.scale.maximum_score:
        raise scoring_error(
            "Overall score fell outside the rubric scale",
            code="SS-SCORING-015",
            details={
                "overall_score": decision.overall_score,
                "minimum_score": rubric.scale.minimum_score,
                "maximum_score": rubric.scale.maximum_score,
            },
        )

    overlapping_feedback = _normalized_overlap(decision.strengths, decision.weaknesses)
    if overlapping_feedback:
        raise scoring_error(
            "Strengths and weaknesses contradicted each other",
            code="SS-SCORING-016",
            details={"overlap": sorted(overlapping_feedback)},
        )

    average_score = sum(judgment.score for judgment in decision.criterion_judgments) / len(
        decision.criterion_judgments
    )
    if abs(decision.overall_score - round(average_score)) > 1:
        raise scoring_error(
            "Overall score was inconsistent with criterion-level scores",
            code="SS-SCORING-017",
            details={
                "overall_score": decision.overall_score,
                "average_criterion_score": average_score,
            },
        )


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _normalized_overlap(left: list[str], right: list[str]) -> set[str]:
    return {_normalize_text(value) for value in left} & {_normalize_text(value) for value in right}
