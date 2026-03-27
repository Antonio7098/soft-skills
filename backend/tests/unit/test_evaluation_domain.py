from __future__ import annotations

import pytest

from soft_skills_backend.modules.evaluation.domain.evaluation import (
    EvaluationCaseOutcome,
    build_marking_computation,
    load_marking_golden_dataset,
    load_quick_practice_golden_dataset,
    select_cases,
    suite_definition,
)
from soft_skills_backend.shared.errors import AppError


def test_select_cases_filters_the_versioned_golden_dataset() -> None:
    dataset = load_marking_golden_dataset()

    selected = select_cases(
        dataset=dataset,
        case_ids=["scenario-launch-tradeoff-02", "interview-pushback-01"],
    )

    assert [case.case_id for case in selected] == [
        "scenario-launch-tradeoff-02",
        "interview-pushback-01",
    ]


def test_quick_practice_suite_loads_its_own_dataset() -> None:
    dataset = load_quick_practice_golden_dataset()

    assert dataset.dataset_version == "quick-practice-golden-dataset.v1"
    assert [case.case_id for case in dataset.cases] == [
        "quick-reset-deadline-01",
        "quick-vague-reassurance-02",
    ]


def test_select_cases_rejects_unknown_case_ids() -> None:
    dataset = load_marking_golden_dataset()

    with pytest.raises(AppError) as exc_info:
        select_cases(dataset=dataset, case_ids=["missing-case"])

    assert exc_info.value.code == "SS-VALIDATION-045"


def test_build_marking_computation_aggregates_metrics_by_model() -> None:
    dataset = load_marking_golden_dataset()
    selected = select_cases(dataset=dataset, case_ids=["interview-pushback-01"])

    computation = build_marking_computation(
        suite=suite_definition("marking_benchmark_v1"),
        dataset=dataset,
        selected_cases=selected,
        model_slugs=["model-a", "model-b"],
        case_results=[
            EvaluationCaseOutcome(
                case_id="model-a:stakeholder-reset-01",
                case_label="Case A",
                status="passed",
                metrics={
                    "latency_ms": 100,
                    "prompt_tokens": 120,
                    "completion_tokens": 40,
                    "total_tokens": 160,
                    "estimated_cost_usd": 0.0,
                    "overall_score_abs_error": 0.0,
                    "skill_score_abs_error_mean": 0.0,
                    "evidence_coverage_rate": 1.0,
                    "accepted_output": True,
                },
                detail_payload={"evaluated_model_slug": "model-a"},
            ),
            EvaluationCaseOutcome(
                case_id="model-b:stakeholder-reset-01",
                case_label="Case B",
                status="failed",
                metrics={
                    "latency_ms": 200,
                    "prompt_tokens": 140,
                    "completion_tokens": 55,
                    "total_tokens": 195,
                    "estimated_cost_usd": 0.0,
                    "overall_score_abs_error": 1.0,
                    "skill_score_abs_error_mean": 0.5,
                    "evidence_coverage_rate": 1.0,
                    "accepted_output": False,
                },
                detail_payload={"evaluated_model_slug": "model-b"},
            ),
        ],
    )

    assert computation.passed is False
    assert computation.summary["dataset_version"] == "marking-golden-dataset.v2"
    assert computation.aggregate_metrics["case_count"] == 2
    assert computation.aggregate_metrics["passed_case_count"] == 1
    assert computation.aggregate_metrics["pass_rate"] == 0.5
    assert computation.aggregate_metrics["total_tokens"] == 355
    assert computation.aggregate_metrics["model_summaries"]["model-a"]["pass_rate"] == 1.0
    assert computation.aggregate_metrics["model_summaries"]["model-b"]["pass_rate"] == 0.0
