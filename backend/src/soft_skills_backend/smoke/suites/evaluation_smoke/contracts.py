"""Evaluation smoke result contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field


class EvaluationSuiteSmokeItem(BaseModel):
    """Result summary for one evaluation suite execution."""

    suite_id: str
    evaluation_run_id: str
    benchmark_set_version: str | None = None
    selected_case_count: int
    case_result_count: int
    passed: bool
    total_tokens: int | None = None


class EvaluationSmokeResult(BaseModel):
    """Result of the evaluation smoke suite."""

    status: str
    available_suite_ids: list[str] = Field(default_factory=list)
    runs: list[EvaluationSuiteSmokeItem] = Field(default_factory=list)
