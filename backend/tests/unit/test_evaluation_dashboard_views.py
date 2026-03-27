"""Tests for evaluation dashboard views and models."""

from __future__ import annotations

from soft_skills_backend.modules.evaluation.contracts.views import (
    BenchmarkDashboardView,
    EvalErrorBreakdownView,
    EvalLatencyPercentilesView,
    EvalPassFailRateView,
    EvaluationCaseDetailView,
    EvaluationComparisonPointView,
    EvaluationComparisonView,
    EvaluationDashboardView,
    ModelPerformanceView,
)


def test_eval_pass_fail_rate_view_defaults() -> None:
    view = EvalPassFailRateView()
    assert view.total_runs == 0
    assert view.passed_runs == 0
    assert view.failed_runs == 0
    assert view.pass_rate == 0.0


def test_eval_pass_fail_rate_view_with_data() -> None:
    view = EvalPassFailRateView(total_runs=10, passed_runs=7, failed_runs=3, pass_rate=0.7)
    assert view.total_runs == 10
    assert view.passed_runs == 7
    assert view.failed_runs == 3
    assert view.pass_rate == 0.7


def test_eval_latency_percentiles_view_defaults() -> None:
    view = EvalLatencyPercentilesView()
    assert view.p50_ms is None
    assert view.p95_ms is None
    assert view.p99_ms is None
    assert view.avg_ms is None


def test_eval_latency_percentiles_view_with_data() -> None:
    view = EvalLatencyPercentilesView(p50_ms=100.0, p95_ms=200.0, p99_ms=300.0, avg_ms=150.5)
    assert view.p50_ms == 100.0
    assert view.p95_ms == 200.0
    assert view.p99_ms == 300.0
    assert view.avg_ms == 150.5


def test_eval_error_breakdown_view_defaults() -> None:
    view = EvalErrorBreakdownView(error_code="none")
    assert view.error_code == "none"
    assert view.count == 0
    assert view.percentage == 0.0


def test_eval_error_breakdown_view_with_data() -> None:
    view = EvalErrorBreakdownView(error_code="SS-PROVIDER-001", count=5, percentage=0.25)
    assert view.error_code == "SS-PROVIDER-001"
    assert view.count == 5
    assert view.percentage == 0.25


def test_evaluation_dashboard_view_defaults() -> None:
    view = EvaluationDashboardView()
    assert view.total_runs == 0
    assert isinstance(view.pass_fail, EvalPassFailRateView)
    assert isinstance(view.latency_percentiles, EvalLatencyPercentilesView)
    assert view.error_breakdown == []
    assert view.total_cases == 0
    assert view.total_tokens == 0
    assert view.estimated_cost_usd is None
    assert view.suite_breakdown == {}
    assert view.from_date is None
    assert view.to_date is None


def test_evaluation_dashboard_view_with_data() -> None:
    view = EvaluationDashboardView(
        total_runs=20,
        pass_fail=EvalPassFailRateView(
            total_runs=20, passed_runs=15, failed_runs=5, pass_rate=0.75
        ),
        latency_percentiles=EvalLatencyPercentilesView(
            p50_ms=100.0, p95_ms=200.0, p99_ms=300.0, avg_ms=150.0
        ),
        error_breakdown=[
            EvalErrorBreakdownView(error_code="SS-PROVIDER-001", count=2, percentage=0.1),
            EvalErrorBreakdownView(error_code="SS-PROVIDER-002", count=1, percentage=0.05),
        ],
        total_cases=40,
        total_tokens=10000,
        estimated_cost_usd=0.50,
        suite_breakdown={
            "marking_benchmark_v1": EvalPassFailRateView(
                total_runs=10, passed_runs=8, failed_runs=2, pass_rate=0.8
            ),
        },
        from_date="2026-01-01T00:00:00",
        to_date="2026-03-01T00:00:00",
    )
    assert view.total_runs == 20
    assert view.pass_fail.pass_rate == 0.75
    assert view.total_cases == 40
    assert view.total_tokens == 10000
    assert len(view.error_breakdown) == 2
    assert "marking_benchmark_v1" in view.suite_breakdown


def test_evaluation_comparison_point_view_defaults() -> None:
    view = EvaluationComparisonPointView(
        evaluation_run_id="run-123",
        suite_id="marking_benchmark_v1",
        suite_type="marking_golden_dataset",
        passed=True,
        started_at="2026-01-15T10:00:00",
    )
    assert view.evaluation_run_id == "run-123"
    assert view.suite_id == "marking_benchmark_v1"
    assert view.passed is True
    assert view.pass_rate is None
    assert view.avg_latency_ms is None
    assert view.total_tokens == 0
    assert view.case_count == 0
    assert view.model_slugs == []


def test_evaluation_comparison_view_defaults() -> None:
    view = EvaluationComparisonView()
    assert view.runs == []
    assert view.run_count == 0
    assert view.total_cases == 0
    assert view.avg_pass_rate is None
    assert view.avg_latency_ms is None


def test_evaluation_comparison_view_with_data() -> None:
    view = EvaluationComparisonView(
        runs=[
            EvaluationComparisonPointView(
                evaluation_run_id="run-1",
                suite_id="marking_benchmark_v1",
                suite_type="marking_golden_dataset",
                passed=True,
                pass_rate=0.8,
                avg_latency_ms=150.0,
                total_tokens=1000,
                case_count=5,
                model_slugs=["model-a"],
                started_at="2026-01-15T10:00:00",
            ),
        ],
        run_count=1,
        total_cases=5,
        avg_pass_rate=0.8,
        avg_latency_ms=150.0,
    )
    assert view.run_count == 1
    assert view.total_cases == 5
    assert view.avg_pass_rate == 0.8
    assert view.runs[0].evaluation_run_id == "run-1"


def test_model_performance_view_defaults() -> None:
    view = ModelPerformanceView(model_slug="model-a")
    assert view.model_slug == "model-a"
    assert view.provider is None
    assert view.run_count == 0
    assert view.passed_count == 0
    assert view.failed_count == 0
    assert view.pass_rate is None
    assert view.avg_latency_ms is None
    assert view.total_prompt_tokens == 0
    assert view.total_completion_tokens == 0
    assert view.total_tokens == 0
    assert view.estimated_cost_usd is None


def test_model_performance_view_with_data() -> None:
    view = ModelPerformanceView(
        model_slug="gpt-4",
        provider="openai",
        run_count=10,
        passed_count=8,
        failed_count=2,
        pass_rate=0.8,
        avg_latency_ms=250.5,
        total_prompt_tokens=5000,
        total_completion_tokens=2000,
        total_tokens=7000,
        estimated_cost_usd=0.35,
    )
    assert view.model_slug == "gpt-4"
    assert view.provider == "openai"
    assert view.run_count == 10
    assert view.passed_count == 8
    assert view.failed_count == 2
    assert view.pass_rate == 0.8
    assert view.total_tokens == 7000


def test_benchmark_dashboard_view_defaults() -> None:
    view = BenchmarkDashboardView()
    assert view.models == []
    assert view.total_runs == 0
    assert view.total_cases == 0
    assert view.from_date is None
    assert view.to_date is None


def test_benchmark_dashboard_view_with_data() -> None:
    view = BenchmarkDashboardView(
        models=[
            ModelPerformanceView(
                model_slug="gpt-4", provider="openai", run_count=5, passed_count=4, failed_count=1
            ),
            ModelPerformanceView(
                model_slug="claude-3",
                provider="anthropic",
                run_count=5,
                passed_count=5,
                failed_count=0,
            ),
        ],
        total_runs=10,
        total_cases=50,
        from_date="2026-01-01T00:00:00",
        to_date="2026-03-01T00:00:00",
    )
    assert len(view.models) == 2
    assert view.total_runs == 10
    assert view.total_cases == 50
    assert view.models[0].model_slug == "gpt-4"
    assert view.models[1].model_slug == "claude-3"


def test_evaluation_case_detail_view_defaults() -> None:
    view = EvaluationCaseDetailView(
        case_id="case-123",
        case_label="Test Case",
        status="passed",
        suite_id="marking_benchmark_v1",
        suite_type="marking_golden_dataset",
        suite_version="v1",
        evaluation_run_id="run-456",
        passed=True,
        started_at="2026-01-15T10:00:00",
    )
    assert view.case_id == "case-123"
    assert view.status == "passed"
    assert view.error_code is None
    assert view.metrics == {}
    assert view.detail_payload == {}


def test_evaluation_case_detail_view_with_data() -> None:
    view = EvaluationCaseDetailView(
        case_id="case-789",
        case_label="Interview Pushback Case",
        status="passed",
        error_code=None,
        suite_id="marking_benchmark_v1",
        suite_type="marking_golden_dataset",
        suite_version="evaluation-suite.marking-golden.v3",
        evaluation_run_id="run-999",
        passed=True,
        metrics={
            "latency_ms": 150,
            "prompt_tokens": 120,
            "completion_tokens": 40,
            "total_tokens": 160,
            "pass_rate": 1.0,
        },
        detail_payload={
            "evaluated_model_slug": "model-a",
            "overall_score_abs_error": 0.0,
        },
        started_at="2026-01-15T10:00:00",
        completed_at="2026-01-15T10:00:15",
    )
    assert view.case_id == "case-789"
    assert view.status == "passed"
    assert view.passed is True
    assert view.metrics["total_tokens"] == 160
    assert view.detail_payload["evaluated_model_slug"] == "model-a"
    assert view.completed_at == "2026-01-15T10:00:15"
