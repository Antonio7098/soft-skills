"""Evaluation view contracts."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class EvaluationSuiteView(BaseModel):
    """Registered evaluation suite."""

    suite_id: str
    suite_type: str
    suite_version: str
    benchmark_set_version: str | None = None
    description: str
    requires_learner_id: bool
    definition_payload: dict[str, Any] = Field(default_factory=dict)


class EvaluationCaseResultView(BaseModel):
    """Per-case evaluation outcome."""

    case_id: str
    case_label: str
    status: str
    error_code: str | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    detail_payload: dict[str, Any] = Field(default_factory=dict)


class ReleaseGateDecisionView(BaseModel):
    """Release decision derived from an evaluation run."""

    decision_id: str
    evaluation_run_id: str
    subject_type: str
    subject_ref: str
    status: str
    reason: str
    summary: dict[str, Any] = Field(default_factory=dict)
    created_at: str


class EvaluationRunView(BaseModel):
    """Full persisted evaluation run."""

    evaluation_run_id: str
    suite_id: str
    suite_type: str
    suite_version: str
    benchmark_set_version: str | None = None
    status: str
    passed: bool
    triggered_by_user_id: str
    learner_id: str | None = None
    trace_id: str | None = None
    workflow_id: str | None = None
    pipeline_run_id: str | None = None
    subject_type: str | None = None
    subject_ref: str | None = None
    aggregate_metrics: dict[str, Any] = Field(default_factory=dict)
    summary: dict[str, Any] = Field(default_factory=dict)
    started_at: str
    completed_at: str | None = None
    case_results: list[EvaluationCaseResultView] = Field(default_factory=list)
    release_decision: ReleaseGateDecisionView | None = None


class EvalPassFailRateView(BaseModel):
    """Pass/fail rate breakdown."""

    total_runs: int = 0
    passed_runs: int = 0
    failed_runs: int = 0
    pass_rate: float = 0.0


class EvalLatencyPercentilesView(BaseModel):
    """Latency percentile breakdown."""

    p50_ms: float | None = None
    p95_ms: float | None = None
    p99_ms: float | None = None
    avg_ms: float | None = None


class EvalErrorBreakdownView(BaseModel):
    """Error code breakdown."""

    error_code: str
    count: int = 0
    percentage: float = 0.0


class EvaluationDashboardView(BaseModel):
    """Aggregated evaluation dashboard data."""

    total_runs: int = 0
    pass_fail: EvalPassFailRateView = Field(default_factory=EvalPassFailRateView)
    latency_percentiles: EvalLatencyPercentilesView = Field(
        default_factory=EvalLatencyPercentilesView
    )
    error_breakdown: list[EvalErrorBreakdownView] = Field(default_factory=list)
    total_cases: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float | None = None
    suite_breakdown: dict[str, EvalPassFailRateView] = Field(default_factory=dict)
    from_date: str | None = None
    to_date: str | None = None


class EvaluationComparisonPointView(BaseModel):
    """One run in a historical comparison."""

    evaluation_run_id: str
    suite_id: str
    suite_type: str
    passed: bool
    pass_rate: float | None = None
    avg_latency_ms: float | None = None
    total_tokens: int = 0
    case_count: int = 0
    model_slugs: list[str] = Field(default_factory=list)
    started_at: str


class EvaluationComparisonView(BaseModel):
    """Historical comparison of evaluation runs."""

    runs: list[EvaluationComparisonPointView] = Field(default_factory=list)
    run_count: int = 0
    total_cases: int = 0
    avg_pass_rate: float | None = None
    avg_latency_ms: float | None = None


class ModelPerformanceView(BaseModel):
    """Provider model performance in evaluations."""

    model_slug: str
    provider: str | None = None
    run_count: int = 0
    passed_count: int = 0
    failed_count: int = 0
    pass_rate: float | None = None
    avg_latency_ms: float | None = None
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float | None = None


class BenchmarkDashboardView(BaseModel):
    """Benchmarking dashboard for provider model performance."""

    models: list[ModelPerformanceView] = Field(default_factory=list)
    total_runs: int = 0
    total_cases: int = 0
    from_date: str | None = None
    to_date: str | None = None


class EvaluationCaseDetailView(BaseModel):
    """Detailed view of a single evaluation case."""

    case_id: str
    case_label: str
    status: str
    error_code: str | None = None
    suite_id: str
    suite_type: str
    suite_version: str
    evaluation_run_id: str
    passed: bool
    metrics: dict[str, Any] = Field(default_factory=dict)
    detail_payload: dict[str, Any] = Field(default_factory=dict)
    started_at: str
    completed_at: str | None = None
