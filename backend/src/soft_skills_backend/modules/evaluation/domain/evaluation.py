"""Provider-backed golden-dataset evaluation definitions for marking models."""

from __future__ import annotations

import json
from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from statistics import fmean
from typing import Any

from pydantic import BaseModel, Field, model_validator

from soft_skills_backend.modules.practice.domain.practice import PracticeType
from soft_skills_backend.modules.practice.workflows.assessment.models import (
    InterviewContextView,
    ScenarioContextView,
)
from soft_skills_backend.shared.errors import validation_error

_ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / "artifacts"


class EvaluationSuiteType(StrEnum):
    """Supported evaluation suite types."""

    MARKING_GOLDEN_DATASET = "marking_golden_dataset"


class EvaluationCaseOutcome(BaseModel):
    """Per-case evaluation outcome."""

    case_id: str
    case_label: str
    status: str
    error_code: str | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    detail_payload: dict[str, Any] = Field(default_factory=dict)


class EvaluationComputation(BaseModel):
    """Computed evaluation run before persistence IDs are assigned."""

    suite_id: str
    suite_type: str
    suite_version: str
    benchmark_set_version: str | None = None
    passed: bool
    aggregate_metrics: dict[str, Any] = Field(default_factory=dict)
    summary: dict[str, Any] = Field(default_factory=dict)
    case_results: list[EvaluationCaseOutcome] = Field(default_factory=list)


class BuiltinEvaluationSuite(BaseModel):
    """Registered built-in suite definition."""

    suite_id: str
    suite_type: EvaluationSuiteType
    suite_version: str
    benchmark_set_version: str
    description: str


class ScoreBand(BaseModel):
    """Accepted numeric band for a golden expectation."""

    minimum: int
    maximum: int

    @model_validator(mode="after")
    def validate_bounds(self) -> ScoreBand:
        if self.minimum > self.maximum:
            raise ValueError("minimum must be <= maximum")
        return self


class GoldenPromptDefinition(BaseModel):
    """Prompt payload for one golden marking case."""

    practice_type: PracticeType
    prompt_type: str
    title: str
    prompt_text: str
    difficulty: str
    target_skill_slugs: list[str] = Field(default_factory=list)
    rubric_id: str
    rubric_version: str
    scenario_context: ScenarioContextView | None = None
    interview_context: InterviewContextView | None = None


class GoldenLearnerContext(BaseModel):
    """Learner context supplied to the evaluator prompt."""

    target_role: str | None = None
    goals: list[str] = Field(default_factory=list)
    prior_assessed_attempts: int = 0


class GoldenMarkingCase(BaseModel):
    """One reviewed golden dataset entry."""

    case_id: str
    label: str
    prompt: GoldenPromptDefinition
    response_text: str
    learner_context: GoldenLearnerContext = Field(default_factory=GoldenLearnerContext)
    expected_overall_score: ScoreBand
    expected_skill_scores: dict[str, ScoreBand] = Field(default_factory=dict)
    minimum_evidence_coverage: float = Field(default=1.0, ge=0.0, le=1.0)
    tags: list[str] = Field(default_factory=list)


class GoldenDataset(BaseModel):
    """Versioned marking golden dataset."""

    dataset_id: str
    dataset_version: str
    schema_version: str
    cases: list[GoldenMarkingCase] = Field(default_factory=list)


class ModelPricingEntry(BaseModel):
    """Token pricing for one model."""

    model_slug: str
    input_cost_per_1k_usd: float
    output_cost_per_1k_usd: float


class ModelPricingRegistry(BaseModel):
    """Versioned pricing registry."""

    registry_version: str
    entries: list[ModelPricingEntry] = Field(default_factory=list)


_BUILTIN_SUITES: tuple[BuiltinEvaluationSuite, ...] = (
    BuiltinEvaluationSuite(
        suite_id="marking_benchmark_v1",
        suite_type=EvaluationSuiteType.MARKING_GOLDEN_DATASET,
        suite_version="evaluation-suite.marking-golden.v2",
        benchmark_set_version="marking-golden-dataset.v1",
        description=(
            "Provider-backed marking evaluation over the reviewed golden dataset, "
            "persisting model quality, latency, token, and cost metrics."
        ),
    ),
)


def builtin_suites() -> tuple[BuiltinEvaluationSuite, ...]:
    return _BUILTIN_SUITES


def suite_definition(suite_id: str) -> BuiltinEvaluationSuite:
    normalized = suite_id.strip()
    for suite in _BUILTIN_SUITES:
        if suite.suite_id == normalized:
            return suite
    raise validation_error(
        "Evaluation suite was not found",
        code="SS-VALIDATION-041",
        status_code=404,
        details={"suite_id": suite_id},
    )


@lru_cache(maxsize=1)
def load_marking_golden_dataset() -> GoldenDataset:
    return GoldenDataset.model_validate(
        json.loads((_ARTIFACTS_DIR / "marking_golden_dataset.v1.json").read_text(encoding="utf-8"))
    )


@lru_cache(maxsize=1)
def load_model_pricing_registry() -> ModelPricingRegistry:
    return ModelPricingRegistry.model_validate(
        json.loads((_ARTIFACTS_DIR / "model_pricing.v1.json").read_text(encoding="utf-8"))
    )


def select_cases(*, dataset: GoldenDataset, case_ids: list[str]) -> list[GoldenMarkingCase]:
    if not case_ids:
        return list(dataset.cases)
    selected: list[GoldenMarkingCase] = []
    cases_by_id = {case.case_id: case for case in dataset.cases}
    missing: list[str] = []
    for case_id in case_ids:
        case = cases_by_id.get(case_id)
        if case is None:
            missing.append(case_id)
            continue
        selected.append(case)
    if missing:
        raise validation_error(
            "One or more golden dataset case_ids were not found",
            code="SS-VALIDATION-045",
            details={"missing_case_ids": missing, "dataset_version": dataset.dataset_version},
        )
    return selected


def build_marking_computation(
    *,
    suite: BuiltinEvaluationSuite,
    dataset: GoldenDataset,
    selected_cases: list[GoldenMarkingCase],
    model_slugs: list[str],
    case_results: list[EvaluationCaseOutcome],
) -> EvaluationComputation:
    passed = bool(case_results) and all(result.status == "passed" for result in case_results)
    model_summaries = {
        model_slug: _aggregate_metrics(
            [
                result
                for result in case_results
                if str(result.detail_payload.get("evaluated_model_slug")) == model_slug
            ]
        )
        for model_slug in model_slugs
    }
    aggregate_metrics = _aggregate_metrics(case_results)
    aggregate_metrics["model_summaries"] = model_summaries
    return EvaluationComputation(
        suite_id=suite.suite_id,
        suite_type=suite.suite_type.value,
        suite_version=suite.suite_version,
        benchmark_set_version=dataset.dataset_version,
        passed=passed,
        aggregate_metrics=aggregate_metrics,
        summary={
            "dataset_id": dataset.dataset_id,
            "dataset_version": dataset.dataset_version,
            "schema_version": dataset.schema_version,
            "selected_case_ids": [case.case_id for case in selected_cases],
            "model_slugs": list(model_slugs),
            "selected_case_count": len(selected_cases),
            "execution_count": len(case_results),
        },
        case_results=case_results,
    )


def estimate_cost_usd(
    *,
    model_slug: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> float | None:
    if model_slug.endswith(":free"):
        return 0.0
    for entry in load_model_pricing_registry().entries:
        if entry.model_slug == model_slug:
            prompt_cost = (prompt_tokens / 1000.0) * entry.input_cost_per_1k_usd
            completion_cost = (completion_tokens / 1000.0) * entry.output_cost_per_1k_usd
            return round(prompt_cost + completion_cost, 6)
    return None


def _aggregate_metrics(results: list[EvaluationCaseOutcome]) -> dict[str, Any]:
    if not results:
        return {
            "case_count": 0,
            "passed_case_count": 0,
            "pass_rate": 0.0,
            "average_latency_ms": 0.0,
            "average_overall_score_abs_error": None,
            "average_skill_score_abs_error_mean": None,
            "average_evidence_coverage_rate": None,
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "total_tokens": 0,
            "estimated_cost_usd": 0.0,
        }

    def _metric_numbers(key: str) -> list[float]:
        values = [result.metrics.get(key) for result in results]
        return [float(value) for value in values if isinstance(value, (int, float))]

    passed_case_count = sum(1 for result in results if result.status == "passed")
    prompt_tokens = int(sum(_metric_numbers("prompt_tokens")))
    completion_tokens = int(sum(_metric_numbers("completion_tokens")))
    total_tokens = int(sum(_metric_numbers("total_tokens")))
    costs = _metric_numbers("estimated_cost_usd")
    return {
        "case_count": len(results),
        "passed_case_count": passed_case_count,
        "pass_rate": round(passed_case_count / max(1, len(results)), 4),
        "average_latency_ms": round(fmean(_metric_numbers("latency_ms")), 2),
        "average_overall_score_abs_error": _rounded_mean(_metric_numbers("overall_score_abs_error")),
        "average_skill_score_abs_error_mean": _rounded_mean(
            _metric_numbers("skill_score_abs_error_mean")
        ),
        "average_evidence_coverage_rate": _rounded_mean(
            _metric_numbers("evidence_coverage_rate")
        ),
        "validation_error_rate": round(
            sum(
                1
                for result in results
                if result.metrics.get("accepted_output") is False
            )
            / max(1, len(results)),
            4,
        ),
        "total_prompt_tokens": prompt_tokens,
        "total_completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "estimated_cost_usd": round(sum(costs), 6) if costs else None,
    }


def _rounded_mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(fmean(values), 4)

