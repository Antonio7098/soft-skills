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
