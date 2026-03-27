"""Contracts for eval dashboard smoke suite."""

from __future__ import annotations

from pydantic import BaseModel


class EvalDashboardRunsResult(BaseModel):
    """Result data for one evaluation run in dashboard smoke."""

    evaluation_run_id: str
    suite_id: str
    passed: bool


class EvalDashboardSmokeResult(BaseModel):
    """Result from the eval dashboard smoke suite."""

    status: str
    evaluation_run_id: str
    dashboard_total_runs: int
    benchmark_total_runs: int
    benchmark_model_count: int
    comparison_run_count: int
