"""Admin analytics and audit view contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field

from soft_skills_backend.modules.catalog import CollectionView


class CollectionVerificationReviewView(BaseModel):
    """One durable verification decision."""

    review_id: str
    collection_id: str
    reviewer_user_id: str
    previous_verification_state: str
    next_verification_state: str
    note: str | None = None
    request_id: str | None = None
    trace_id: str | None = None
    workflow_id: str | None = None
    occurred_at: str


class PromptSummaryView(BaseModel):
    """Summary of one prompt family."""

    name: str
    prompt_type: str
    latest_version: str
    status: str
    created_at: str


class PromptVersionView(BaseModel):
    """Full details for one prompt version."""

    id: int
    name: str
    version: str
    prompt_type: str
    template: str
    variables_schema: dict[str, object] = Field(default_factory=dict)
    output_schema: dict[str, object] | None = None
    status: str
    parent_version_id: int | None = None
    created_at: str
    updated_at: str


class PromptAnalyticsView(BaseModel):
    """Aggregated render analytics for one prompt version."""

    prompt_version_id: int
    name: str
    version: str
    render_count: int
    success_count: int
    failure_count: int
    avg_latency_ms: float | None = None
    total_tokens: int
    last_rendered_at: str | None = None


class PromptCompareView(BaseModel):
    """A/B comparison payload for two prompt versions."""

    name: str
    version_a: str
    version_b: str
    template_a: str
    template_b: str
    variables_schema_a: dict[str, object] = Field(default_factory=dict)
    variables_schema_b: dict[str, object] = Field(default_factory=dict)
    metrics_a: PromptAnalyticsView | None = None
    metrics_b: PromptAnalyticsView | None = None


class CollectionVerificationQueueItemView(BaseModel):
    """Compact queue view for public collections awaiting review."""

    collection_id: str
    author_user_id: str
    title: str
    lifecycle_state: str
    verification_state: str
    discovery_tier: str
    source_type: str
    prompt_item_count: int
    scenario_count: int
    created_at: str
    updated_at: str
    latest_reviewed_at: str | None = None
    latest_reviewer_user_id: str | None = None
    latest_note: str | None = None


class CollectionVerificationAuditView(BaseModel):
    """Verification response with current collection state and history."""

    collection: CollectionView
    latest_review: CollectionVerificationReviewView | None = None
    history: list[CollectionVerificationReviewView] = Field(default_factory=list)


class AdminLearnerRelationshipView(BaseModel):
    """Explicit admin-to-learner access grant."""

    learner_user_id: str
    admin_user_id: str
    relationship_type: str
    created_at: str
    updated_at: str


class UsageSummaryView(BaseModel):
    """Usage and observability counters."""

    total_sessions: int = 0
    total_attempts: int = 0
    submitted_attempts: int = 0
    assessed_attempts: int = 0
    validated_assessments: int = 0
    rejected_assessments: int = 0
    workflow_event_count: int = 0
    pipeline_run_count: int = 0
    provider_call_count: int = 0
    avg_validated_score: float | None = None
    last_activity_at: str | None = None


class UsageTrendPointView(BaseModel):
    """Daily usage trend point."""

    bucket_date: str
    sessions_started: int = 0
    attempts_submitted: int = 0
    assessments_validated: int = 0
    assessments_rejected: int = 0


class ProviderUsageView(BaseModel):
    """Provider-call aggregate."""

    provider: str
    model_slug: str | None = None
    call_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    avg_latency_ms: float | None = None


class SkillClusterView(BaseModel):
    """One weak-skill cluster summary."""

    skill_slug: str
    learner_count: int


class SkillAverageView(BaseModel):
    """Average skill score across a cohort."""

    skill_slug: str
    avg_score: float
    learner_count: int


class AdminAttemptSummaryView(BaseModel):
    """Sanitized learner attempt summary for admin analytics."""

    attempt_id: str
    learner_id: str
    session_id: str
    workflow_id: str
    practice_type: str
    content_item_id: str
    content_item_type: str
    status: str
    assessment_id: str | None = None
    validation_status: str | None = None
    overall_score: int | None = None
    trace_id: str | None = None
    pipeline_run_id: str | None = None
    submitted_at: str | None = None
    assessed_at: str | None = None
    created_at: str


class LearnerAnalyticsView(BaseModel):
    """Admin learner analytics payload."""

    learner_id: str
    target_role: str | None = None
    latest_progress_snapshot_id: str | None = None
    latest_recommendation_id: str | None = None
    weak_skill_slugs: list[str] = Field(default_factory=list)
    stagnating_skill_slugs: list[str] = Field(default_factory=list)
    coverage_gap_skill_slugs: list[str] = Field(default_factory=list)
    usage: UsageSummaryView
    recent_attempts: list[AdminAttemptSummaryView] = Field(default_factory=list)
    usage_trend: list[UsageTrendPointView] = Field(default_factory=list)
    provider_summary: list[ProviderUsageView] = Field(default_factory=list)


class CohortAnalyticsView(BaseModel):
    """Admin cohort analytics payload."""

    cohort_key: str
    learner_count: int
    usage: UsageSummaryView
    weak_skill_clusters: list[SkillClusterView] = Field(default_factory=list)
    average_skill_scores: list[SkillAverageView] = Field(default_factory=list)
    usage_trend: list[UsageTrendPointView] = Field(default_factory=list)
    provider_summary: list[ProviderUsageView] = Field(default_factory=list)


class AdminPromptAuditView(BaseModel):
    """Prompt context for audit without learner response content."""

    title: str
    content_item_id: str
    content_item_type: str
    prompt_type: str
    difficulty: str
    delivery_version: str
    rubric_id: str
    rubric_version: str
    target_skill_slugs: list[str] = Field(default_factory=list)


class AdminAssessmentSkillScoreView(BaseModel):
    """Skill score summary without quoted learner evidence."""

    skill_slug: str
    score: int
    rationale: str


class AdminAssessmentAuditView(BaseModel):
    """Assessment-critical metadata for admin replay and diagnostics."""

    assessment_id: str
    validation_status: str
    prompt_version: str
    rubric_id: str
    rubric_version: str
    schema_version: str
    config_version: str
    provider: str
    model_slug: str
    overall_score: int | None = None
    rejection_code: str | None = None
    trace_id: str
    pipeline_run_id: str
    evidence_count: int = 0
    strengths_count: int = 0
    weaknesses_count: int = 0
    next_actions_count: int = 0
    evidence_quotes: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    skill_scores: list[AdminAssessmentSkillScoreView] = Field(default_factory=list)
    created_at: str


class WorkflowEventAuditView(BaseModel):
    """Structured event row for audit."""

    event_id: str
    event_type: str
    request_id: str | None = None
    trace_id: str | None = None
    workflow_id: str | None = None
    error_code: str | None = None
    payload: dict[str, object] = Field(default_factory=dict)
    occurred_at: str


class PipelineRunAuditView(BaseModel):
    """Stageflow pipeline run audit row."""

    pipeline_run_id: str
    pipeline_name: str
    status: str
    topology: str | None = None
    execution_mode: str | None = None
    request_id: str | None = None
    trace_id: str | None = None
    user_id: str | None = None
    failed_stage: str | None = None
    error: str | None = None
    stage_results: dict[str, object] = Field(default_factory=dict)
    started_at: str
    finished_at: str | None = None


class ProviderCallAuditView(BaseModel):
    """Provider call audit row."""

    call_id: str
    operation: str
    provider: str
    model_slug: str | None = None
    success: bool
    latency_ms: int | None = None
    error: str | None = None
    pipeline_run_id: str | None = None
    request_id: str | None = None
    trace_id: str | None = None
    metrics: dict[str, object] = Field(default_factory=dict)
    created_at: str


class AttemptAuditView(BaseModel):
    """Admin replay and diagnostics surface for one learner attempt."""

    attempt: AdminAttemptSummaryView
    response_visibility: str
    access_relationship: AdminLearnerRelationshipView | None = None
    prompt: AdminPromptAuditView
    response_text: str | None = None
    assessment: AdminAssessmentAuditView | None = None
    latest_progress_snapshot_id: str | None = None
    latest_recommendation_id: str | None = None
    workflow_events: list[WorkflowEventAuditView] = Field(default_factory=list)
    pipeline_runs: list[PipelineRunAuditView] = Field(default_factory=list)
    provider_calls: list[ProviderCallAuditView] = Field(default_factory=list)


class RubricCriterionLevelView(BaseModel):
    """One scored rubric level."""

    level: int
    description: str
    examples: list[str]


class RubricCriterionView(BaseModel):
    """One rubric criterion."""

    criterion_ref: str
    skill_slug: str
    title: str
    description: str
    weight: float
    required: bool
    position: int
    levels: list[RubricCriterionLevelView]


class RubricView(BaseModel):
    """Rubric definition view."""

    rubric_id: str
    family: str
    version: str
    content_type: str
    schema_version: str
    name: str
    criteria: list[RubricCriterionView] = Field(default_factory=list)


class StageDefinitionView(BaseModel):
    """One stage in a pipeline DAG."""

    name: str
    kind: str
    dependencies: list[str] = Field(default_factory=list)
    runner_class: str | None = None
    description: str | None = None


class PipelineDefinitionView(BaseModel):
    """Pipeline definition for DAG visualization."""

    pipeline_name: str
    topology: str | None = None
    description: str | None = None
    stage_count: int = 0
    created_at: str | None = None
    updated_at: str | None = None


class PipelineDAGView(BaseModel):
    """Full pipeline DAG with stages and dependencies."""

    pipeline_name: str
    topology: str | None = None
    description: str | None = None
    stages: list[StageDefinitionView] = Field(default_factory=list)


class PipelineRunSummaryView(BaseModel):
    """Summary of one pipeline run."""

    pipeline_run_id: str
    pipeline_name: str
    status: str
    execution_mode: str | None = None
    user_id: str | None = None
    request_id: str | None = None
    trace_id: str | None = None
    error: str | None = None
    failed_stage: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    duration_ms: int | None = None


class StageExecutionEventView(BaseModel):
    """One stage execution event in a trace."""

    stage_name: str
    event_type: str
    timestamp: str
    duration_ms: int | None = None
    status: str | None = None
    error: str | None = None


class PipelineTraceView(BaseModel):
    """Full execution trace for visualization replay."""

    pipeline_run_id: str
    pipeline_name: str
    execution_sequence: list[StageExecutionEventView] = Field(default_factory=list)
    total_duration_ms: int
    started_at: str | None = None
    completed_at: str | None = None


class StageMetricsView(BaseModel):
    """Aggregate metrics for one stage."""

    stage_name: str
    invocation_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    skip_count: int = 0
    cancel_count: int = 0
    retry_count: int = 0
    avg_duration_ms: float | None = None
    p50_duration_ms: int | None = None
    p95_duration_ms: int | None = None
    p99_duration_ms: int | None = None


class PipelineMetricsView(BaseModel):
    """Aggregate metrics for a pipeline."""

    pipeline_name: str
    total_runs: int = 0
    success_count: int = 0
    failure_count: int = 0
    cancel_count: int = 0
    stage_metrics: list[StageMetricsView] = Field(default_factory=list)
