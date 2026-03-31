export interface AdminUserView {
  readonly user_id: string;
  readonly email: string;
  readonly display_name: string;
  readonly auth_provider: string;
  readonly is_active: boolean;
  readonly organisation_id: string | null;
  readonly organisation_role: string | null;
  readonly created_at: string | null;
}

export interface AdminUserListView {
  readonly users: AdminUserView[];
  readonly total: number;
  readonly offset: number;
  readonly limit: number;
}

export interface BulkOperationResultView {
  readonly operation: string;
  readonly requested_count: number;
  readonly success_count: number;
  readonly failure_count: number;
  readonly failed_user_ids: string[];
  readonly processed?: number;
}

export interface UserSessionView {
  readonly session_id: string;
  readonly practice_type: string;
  readonly content_item_id: string;
  readonly status: string;
  readonly created_at: string | null;
  readonly completed_at: string | null;
}

export interface UserAttemptSummaryView {
  readonly attempt_id: string;
  readonly session_id: string;
  readonly practice_type: string;
  readonly content_item_id: string;
  readonly content_item_type: string;
  readonly status: string;
  readonly overall_score: number | null;
  readonly submitted_at: string | null;
  readonly assessed_at: string | null;
}

export interface UserLoginEventView {
  readonly event_type: string;
  readonly occurred_at: string | null;
  readonly trace_id: string | null;
}

export interface UserActivityView {
  readonly user_id: string;
  readonly email: string;
  readonly display_name: string;
  readonly organisation_id: string | null;
  readonly organisation_role: string | null;
  readonly total_sessions: number;
  readonly total_attempts: number;
  readonly recent_sessions: UserSessionView[];
  readonly recent_attempts: UserAttemptSummaryView[];
  readonly recent_logins: UserLoginEventView[];
}

export interface UsageTrendPointView {
  readonly bucket_date: string;
  readonly sessions_started: number;
  readonly attempts_submitted: number;
  readonly assessments_validated: number;
  readonly assessments_rejected: number;
}

export interface ProviderUsageView {
  readonly provider: string;
  readonly model_slug: string | null;
  readonly call_count: number;
  readonly success_count: number;
  readonly failure_count: number;
  readonly avg_latency_ms: number | null;
}

export interface UsageSummaryView {
  readonly total_sessions: number;
  readonly total_attempts: number;
  readonly submitted_attempts: number;
  readonly assessed_attempts: number;
  readonly validated_assessments: number;
  readonly rejected_assessments: number;
  readonly workflow_event_count: number;
  readonly pipeline_run_count: number;
  readonly provider_call_count: number;
  readonly avg_validated_score: number | null;
  readonly last_activity_at: string | null;
}

export interface AdminAttemptSummaryView {
  readonly attempt_id: string;
  readonly session_id: string;
  readonly practice_type: string;
  readonly content_item_id: string;
  readonly content_item_type: string;
  readonly status: string;
  readonly overall_score: number | null;
  readonly submitted_at: string | null;
  readonly assessed_at: string | null;
}

export interface LearnerAnalyticsView {
  readonly learner_id: string;
  readonly target_role: string | null;
  readonly latest_progress_snapshot_id: string | null;
  readonly latest_recommendation_id: string | null;
  readonly weak_skill_slugs: string[];
  readonly stagnating_skill_slugs: string[];
  readonly coverage_gap_skill_slugs: string[];
  readonly usage: UsageSummaryView;
  readonly recent_attempts: AdminAttemptSummaryView[];
  readonly usage_trend: UsageTrendPointView[];
  readonly provider_summary: ProviderUsageView[];
}

export interface AdminLearnerRelationshipView {
  readonly learner_user_id: string;
  readonly admin_user_id: string;
  readonly relationship_type: string;
  readonly created_at: string;
  readonly updated_at: string;
}

export interface SkillClusterView {
  readonly skill_slug: string;
  readonly learner_count: number;
}

export interface SkillAverageView {
  readonly skill_slug: string;
  readonly avg_score: number;
  readonly learner_count: number;
}

export interface AnalyticsOverviewView {
  readonly total_learners: number;
  readonly active_learners_30d: number;
  readonly total_sessions: number;
  readonly total_attempts: number;
  readonly submitted_attempts: number;
  readonly validated_assessments: number;
  readonly rejected_assessments: number;
  readonly avg_validated_score: number | null;
  readonly overall_usage_trend: UsageTrendPointView[];
  readonly top_weak_skills: SkillClusterView[];
  readonly cohort_breakdown: { cohort_key: string; learner_count: number }[];
  readonly provider_summary: ProviderUsageView[];
}

export interface CohortAnalyticsView {
  readonly cohort_key: string;
  readonly learner_count: number;
  readonly usage: UsageSummaryView;
  readonly weak_skill_clusters: SkillClusterView[];
  readonly average_skill_scores: SkillAverageView[];
  readonly usage_trend: UsageTrendPointView[];
  readonly provider_summary: ProviderUsageView[];
}

export interface CohortComparisonView {
  readonly cohorts: CohortAnalyticsView[];
  readonly run_count: number;
}

export interface CollectionVerificationQueueItemView {
  readonly collection_id: string;
  readonly author_user_id: string;
  readonly title: string;
  readonly lifecycle_state: string;
  readonly verification_state: string;
  readonly discovery_tier: string;
  readonly source_type: string;
  readonly prompt_item_count: number;
  readonly scenario_count: number;
  readonly created_at: string;
  readonly updated_at: string;
  readonly latest_reviewed_at: string | null;
  readonly latest_reviewer_user_id: string | null;
  readonly latest_note: string | null;
}

export interface CollectionVerificationReviewView {
  readonly reviewer_user_id: string;
  readonly verification_state: string;
  readonly note: string | null;
  readonly reviewed_at: string;
}

export interface CollectionVerificationAuditView {
  readonly collection: import('./catalog').CollectionView;
  readonly latest_review: CollectionVerificationReviewView | null;
  readonly history: CollectionVerificationReviewView[];
}

export interface EvaluationSuiteView {
  readonly suite_id: string;
  readonly name: string;
  readonly suite_type: string;
  readonly description: string | null;
  readonly created_at: string;
  readonly updated_at: string;
}

export interface EvaluationRunView {
  readonly evaluation_run_id: string;
  readonly suite_id: string;
  readonly suite_type: string;
  readonly status: string;
  readonly passed: boolean;
  readonly pass_rate: number | null;
  readonly avg_latency_ms: number | null;
  readonly total_tokens: number;
  readonly case_count: number;
  readonly model_slugs: string[];
  readonly started_at: string;
  readonly completed_at: string | null;
}

export interface EvalPassFailRateView {
  readonly passed: number;
  readonly failed: number;
  readonly pass_rate: number;
}

export interface EvaluationDashboardView {
  readonly total_runs: number;
  readonly pass_fail: { passed: number; failed: number; pass_rate: number };
  readonly latency_percentiles: { p50_ms: number; p95_ms: number; p99_ms: number };
  readonly error_breakdown: { error_code: string; count: number; percentage: number }[];
  readonly total_cases: number;
  readonly total_tokens: number;
  readonly estimated_cost_usd: number | null;
  readonly suite_breakdown: Record<string, EvalPassFailRateView>;
  readonly from_date: string | null;
  readonly to_date: string | null;
}

export interface EvaluationComparisonView {
  readonly runs: {
    readonly evaluation_run_id: string;
    readonly suite_id: string;
    readonly suite_type: string;
    readonly passed: boolean;
    readonly pass_rate: number | null;
    readonly avg_latency_ms: number | null;
    readonly total_tokens: number;
    readonly case_count: number;
    readonly model_slugs: string[];
    readonly started_at: string;
  }[];
  readonly run_count: number;
  readonly total_cases: number;
  readonly avg_pass_rate: number | null;
  readonly avg_latency_ms: number | null;
}

export interface BenchmarkDashboardView {
  readonly models: {
    readonly model_slug: string;
    readonly provider: string | null;
    readonly run_count: number;
    readonly passed_count: number;
    readonly failed_count: number;
    readonly pass_rate: number | null;
    readonly avg_latency_ms: number | null;
    readonly total_prompt_tokens: number;
    readonly total_completion_tokens: number;
    readonly total_tokens: number;
    readonly estimated_cost_usd: number | null;
  }[];
  readonly total_runs: number;
  readonly total_cases: number;
  readonly from_date: string | null;
  readonly to_date: string | null;
}

export interface EvaluationCaseDetailView {
  readonly case_id: string;
  readonly case_label: string;
  readonly status: string;
  readonly error_code: string | null;
  readonly suite_id: string;
  readonly suite_type: string;
  readonly suite_version: string;
  readonly evaluation_run_id: string;
  readonly passed: boolean;
  readonly metrics: Record<string, unknown>;
  readonly detail_payload: Record<string, unknown>;
  readonly started_at: string;
  readonly completed_at: string | null;
}

export interface ProviderModelPricing {
  readonly prompt_price_per_1m: number | null;
  readonly completion_price_per_1m: number | null;
}

export interface ProviderModel {
  readonly id: string;
  readonly name: string;
  readonly provider: string;
  readonly pricing: ProviderModelPricing | null;
}

export interface PromptSummaryView {
  readonly name: string;
  readonly prompt_type: string;
  readonly latest_version: string;
  readonly status: string;
  readonly created_at: string;
}

export interface PromptVersionView {
  readonly id: number;
  readonly name: string;
  readonly version: string;
  readonly prompt_type: string;
  readonly template: string;
  readonly variables_schema: Record<string, unknown>;
  readonly output_schema: Record<string, unknown> | null;
  readonly status: string;
  readonly parent_version_id: number | null;
  readonly created_at: string;
  readonly updated_at: string;
}

export interface PromptAnalyticsView {
  readonly prompt_version_id: number;
  readonly name: string;
  readonly version: string;
  readonly render_count: number;
  readonly success_count: number;
  readonly failure_count: number;
  readonly avg_latency_ms: number | null;
  readonly total_tokens: number;
  readonly last_rendered_at: string | null;
}

export interface PromptCompareView {
  readonly name: string;
  readonly version_a: PromptVersionView;
  readonly version_b: PromptVersionView;
  readonly diff_summary: string | null;
}

export interface PipelineDefinitionView {
  readonly pipeline_name: string;
  readonly topology: string | null;
  readonly description: string | null;
  readonly stage_count: number;
  readonly created_at: string | null;
  readonly updated_at: string | null;
}

export interface PipelineDAGStageView {
  readonly name: string;
  readonly kind: string;
  readonly dependencies: string[];
  readonly runner_class: string | null;
  readonly description: string | null;
}

export interface PipelineDAGView {
  readonly pipeline_name: string;
  readonly topology: string | null;
  readonly description: string | null;
  readonly stages: PipelineDAGStageView[];
}

export interface PipelineRunSummaryView {
  readonly pipeline_run_id: string;
  readonly pipeline_name: string;
  readonly status: string;
  readonly execution_mode: string | null;
  readonly user_id: string | null;
  readonly request_id: string | null;
  readonly trace_id: string | null;
  readonly error: string | null;
  readonly failed_stage: string | null;
  readonly started_at: string | null;
  readonly finished_at: string | null;
  readonly duration_ms: number | null;
}

export interface PipelineTraceEventView {
  readonly stage_name: string;
  readonly event_type: string;
  readonly timestamp: string;
  readonly duration_ms: number | null;
  readonly status: string | null;
  readonly error: string | null;
}

export interface PipelineTraceView {
  readonly pipeline_run_id: string;
  readonly pipeline_name: string;
  readonly execution_sequence: PipelineTraceEventView[];
  readonly total_duration_ms: number;
  readonly started_at: string | null;
  readonly completed_at: string | null;
}

export interface PipelineStageMetricsView {
  readonly stage_name: string;
  readonly invocation_count: number;
  readonly success_count: number;
  readonly failure_count: number;
  readonly skip_count: number;
  readonly cancel_count: number;
  readonly retry_count: number;
  readonly avg_duration_ms: number | null;
  readonly p50_duration_ms: number | null;
  readonly p95_duration_ms: number | null;
  readonly p99_duration_ms: number | null;
}

export interface PipelineMetricsView {
  readonly pipeline_name: string;
  readonly total_runs: number;
  readonly success_count: number;
  readonly failure_count: number;
  readonly cancel_count: number;
  readonly success_rate: number;
  readonly avg_duration_ms: number;
  readonly p95_duration_ms: number;
  readonly stage_metrics: PipelineStageMetricsView[];
}

export interface RubricLevelView {
  readonly level: number;
  readonly description: string;
  readonly examples: string[];
}

export interface RubricCriterionInput {
  readonly criterion_ref: string;
  readonly skill_slug: string;
  readonly title: string;
  readonly description: string;
  readonly weight: number;
  readonly required: boolean;
  readonly position: number;
  readonly levels: RubricLevelView[];
}

export interface RubricCriterionAdminView {
  readonly criterion_ref: string;
  readonly skill_slug: string;
  readonly title: string;
  readonly description: string;
  readonly weight: number;
  readonly required: boolean;
  readonly position: number;
  readonly levels: RubricLevelView[];
}

export interface RubricAdminView {
  readonly rubric_id: string;
  readonly family: string;
  readonly version: string;
  readonly content_type: string;
  readonly schema_version: string;
  readonly name: string;
  readonly criteria: RubricCriterionAdminView[];
}

export interface WorkflowEventView {
  readonly event_id: string;
  readonly event_type: string;
  readonly request_id: string | null;
  readonly trace_id: string | null;
  readonly workflow_id: string | null;
  readonly error_code: string | null;
  readonly payload: Record<string, unknown>;
  readonly occurred_at: string;
}

export interface PaginatedWorkflowEventsView {
  readonly items: WorkflowEventView[];
  readonly total: number;
  readonly offset: number;
  readonly limit: number;
}

export interface AdminPromptAuditView {
  readonly prompt_version: string;
  readonly template: string;
}

export interface AdminSkillScoreView {
  readonly skill_slug: string;
  readonly score: number;
  readonly rationale: string;
}

export interface AdminAssessmentAuditView {
  readonly assessment_id: string;
  readonly validation_status: string;
  readonly prompt_version: string;
  readonly rubric_id: string;
  readonly rubric_version: string;
  readonly schema_version: string;
  readonly config_version: string;
  readonly provider: string;
  readonly model_slug: string;
  readonly overall_score: number | null;
  readonly rejection_code: string | null;
  readonly trace_id: string;
  readonly pipeline_run_id: string;
  readonly evidence_count: number;
  readonly strengths_count: number;
  readonly weaknesses_count: number;
  readonly next_actions_count: number;
  readonly evidence_quotes: string[];
  readonly strengths: string[];
  readonly weaknesses: string[];
  readonly next_actions: string[];
  readonly skill_scores: AdminSkillScoreView[];
  readonly created_at: string;
}

export interface PipelineRunAuditView {
  readonly pipeline_run_id: string;
  readonly pipeline_name: string;
  readonly status: string;
  readonly started_at: string;
  readonly completed_at: string | null;
}

export interface ProviderCallAuditView {
  readonly call_id: string;
  readonly provider: string;
  readonly model_slug: string | null;
  readonly operation: string;
  readonly latency_ms: number | null;
  readonly success: boolean;
  readonly error_code: string | null;
  readonly trace_id: string | null;
}

export interface WorkflowEventAuditView {
  readonly event_id: string;
  readonly event_type: string;
  readonly occurred_at: string;
  readonly payload: Record<string, unknown>;
}

export interface AttemptAuditView {
  readonly attempt: AdminAttemptSummaryView;
  readonly response_visibility: string;
  readonly access_relationship: AdminLearnerRelationshipView | null;
  readonly prompt: AdminPromptAuditView;
  readonly response_text: string | null;
  readonly assessment: AdminAssessmentAuditView | null;
  readonly latest_progress_snapshot_id: string | null;
  readonly latest_recommendation_id: string | null;
  readonly workflow_events: WorkflowEventAuditView[];
  readonly pipeline_runs: PipelineRunAuditView[];
  readonly provider_calls: ProviderCallAuditView[];
}

export type GenerationStage =
  | 'pending'
  | 'input_guard'
  | 'blueprint_transform'
  | 'blueprint_llm_transform'
  | 'blueprint_guard'
  | 'prompt_items_work'
  | 'scenarios_work'
  | 'assemble_transform'
  | 'output_guard'
  | 'persistence_work'
  | 'completed'
  | 'failed'
  | 'cancelled';

export interface GenerationStreamEvent {
  readonly event_id: string;
  readonly generation_id: string;
  readonly type: 'started' | 'progress' | 'completed' | 'failed';
  readonly stage: GenerationStage;
  readonly sequence_number: number;
  readonly emitted_at: string;
  readonly progress_percent: number;
  readonly payload: Record<string, unknown>;
}

export interface GenerationStartedView {
  readonly generation_id: string;
  readonly stream_token: string;
  readonly mode: 'structured' | 'chat';
}

export interface GenerationStreamCallbacks {
  readonly onEvent?: (event: GenerationStreamEvent) => void;
  readonly onCompleted?: (payload: Record<string, unknown>) => void;
  readonly onFailed?: (payload: Record<string, unknown>) => void;
  readonly onError?: (error: string) => void;
  readonly onClose?: () => void;
}

export interface BlueprintInfo {
  readonly title: string;
  readonly summary: string;
  readonly prompt_items_count: number;
  readonly scenarios_count: number;
  readonly model_slug: string;
}

export interface PromptItemDraft {
  readonly title: string;
  readonly prompt_type: string;
  readonly difficulty: string;
}

export interface GenerationActivityItem {
  readonly id: string;
  readonly stage: GenerationStage;
  readonly message: string;
  readonly timestamp: string;
}

export interface GenerationProgressState {
  readonly status: 'idle' | 'started' | 'streaming' | 'completed' | 'failed' | 'cancelled';
  readonly generation_id: string | null;
  readonly stream_token: string | null;
  readonly stages_completed: GenerationStage[];
  readonly current_stage: GenerationStage | null;
  readonly progress_percent: number;
  readonly blueprint: BlueprintInfo | null;
  readonly prompt_items: PromptItemDraft[];
  readonly activity: GenerationActivityItem[];
  readonly collection: import('./catalog').CollectionView | null;
  readonly error: string | null;
}

export interface TelemetryProviderMetricView {
  readonly provider: string;
  readonly model_slug: string | null;
  readonly operation: string;
  readonly call_count: number;
  readonly success_count: number;
  readonly failure_count: number;
  readonly success_rate: number | null;
  readonly avg_latency_ms: number | null;
  readonly p50_latency_ms: number | null;
  readonly p95_latency_ms: number | null;
  readonly p99_latency_ms: number | null;
  readonly total_tokens: number;
}

export interface TelemetryPipelineHealthView {
  readonly pipeline_name: string;
  readonly total_runs: number;
  readonly success_count: number;
  readonly failure_count: number;
  readonly cancel_count: number;
  readonly success_rate: number | null;
  readonly avg_duration_ms: number | null;
  readonly error_rate: number | null;
  readonly last_run_at: string | null;
}

export interface TelemetryErrorBreakdownView {
  readonly error_code: string | null;
  readonly error_type: string;
  readonly count: number;
  readonly percentage: number;
  readonly examples: string[];
}

export interface TelemetryLatencyBucketView {
  readonly bucket_ms: number;
  readonly count: number;
  readonly percentage: number;
}

export interface TelemetryOverviewView {
  readonly organisation_id: string | null;
  readonly from_date: string | null;
  readonly to_date: string | null;
  readonly total_provider_calls: number;
  readonly provider_call_success_rate: number | null;
  readonly avg_provider_latency_ms: number | null;
  readonly total_pipeline_runs: number;
  readonly pipeline_success_rate: number | null;
  readonly total_workflow_events: number;
  readonly total_errors: number;
  readonly error_rate: number | null;
  readonly provider_metrics: TelemetryProviderMetricView[];
  readonly pipeline_health: TelemetryPipelineHealthView[];
  readonly error_breakdown: TelemetryErrorBreakdownView[];
  readonly latency_distribution: TelemetryLatencyBucketView[];
}

export interface TelemetryTraceSpanView {
  readonly span_id: string | null;
  readonly parent_span_id: string | null;
  readonly operation_name: string;
  readonly service_name: string | null;
  readonly start_time: string | null;
  readonly end_time: string | null;
  readonly duration_ms: number | null;
  readonly status_code: string | null;
  readonly error: string | null;
  readonly attributes: Record<string, unknown>;
}

export interface TelemetryTraceView {
  readonly trace_id: string;
  readonly organisation_id: string | null;
  readonly spans: TelemetryTraceSpanView[];
  readonly total_duration_ms: number | null;
  readonly started_at: string | null;
  readonly completed_at: string | null;
  readonly error_count: number;
  readonly span_count: number;
}

export interface TelemetryTraceListItemView {
  readonly trace_id: string;
  readonly organisation_id: string | null;
  readonly operation_name: string | null;
  readonly service_name: string | null;
  readonly duration_ms: number | null;
  readonly started_at: string | null;
  readonly error_count: number;
  readonly span_count: number;
}

export interface TelemetryTraceListView {
  readonly traces: TelemetryTraceListItemView[];
  readonly total: number;
  readonly offset: number;
  readonly limit: number;
}
