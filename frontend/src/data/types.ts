// ---------------------------------------------------------------------------
// Domain types aligned with backend schemas (application/*.py, domain/*.py)
// ---------------------------------------------------------------------------

// --- Enums ----------------------------------------------------------------

export type PracticeType = 'quick_practice';
export type SessionStatus = 'active' | 'completed' | 'failed';
export type AttemptStatus =
  | 'prompt_delivered'
  | 'submitted'
  | 'assessing'
  | 'assessed'
  | 'assessment_rejected'
  | 'assessment_failed';
export type AssessmentValidationStatus = 'validated' | 'rejected';
export type Difficulty = 'introductory' | 'intermediate' | 'advanced';
export type LifecycleState =
  | 'draft'
  | 'review'
  | 'published_private'
  | 'published_public'
  | 'archived';
export type VerificationState = 'unverified' | 'verified' | 'rejected';
export type PromptType = 'quick_practice_prompt' | 'interview_prompt' | 'scenario_step';
export type DiscoveryTier = 'private' | 'global_public' | 'org_public' | 'standard_public';
export type SourceType = 'manual' | 'generated_structured' | 'generated_chat';
export type RubricType = 'quick_practice' | 'interview' | 'scenario';

// --- Identity -------------------------------------------------------------

export interface LearnerProfileView {
  readonly target_role: string | null;
  readonly goals: string[];
  readonly practice_preferences: Record<string, string>;
}

export interface UserView {
  readonly id: string;
  readonly email: string;
  readonly display_name: string;
  readonly role: string;
  readonly auth_provider: string;
  readonly created_at: string;
  readonly profile: LearnerProfileView;
}

// --- Taxonomy --------------------------------------------------------------

export interface SkillView {
  readonly slug: string;
  readonly name: string;
  readonly description: string;
}

export interface CompetencyView {
  readonly slug: string;
  readonly name: string;
  readonly description: string;
  readonly skill_slugs: string[];
}

export interface RubricView {
  readonly rubric_id: string;
  readonly family: string;
  readonly version: string;
  readonly content_type: string;
  readonly schema_version: string;
  readonly name: string;
}

export interface RubricLevel {
  readonly description: string;
  readonly examples: string[];
}

export interface RubricCriterionView {
  readonly id: string;
  readonly rubric_id: string;
  readonly rubric_version: string;
  readonly criterion_ref: string;
  readonly skill_slug: string;
  readonly title: string;
  readonly description: string;
  readonly weight: number;
  readonly required: boolean;
  readonly position: number;
  readonly levels: Record<string, RubricLevel>;
}

export interface TaxonomySnapshot {
  readonly skills: SkillView[];
  readonly competencies: CompetencyView[];
  readonly rubrics: RubricView[];
  readonly rubric_criteria: RubricCriterionView[];
}

// --- Catalog ---------------------------------------------------------------

export interface MockCompanyView {
  readonly id: string;
  readonly name: string;
  readonly industry: string;
  readonly operating_context: string;
}

export interface MockPersonView {
  readonly id: string;
  readonly name: string;
  readonly role: string;
  readonly goals: string[];
  readonly communication_style: string;
  readonly relationship_to_scenario: string;
}

export interface PromptItemView {
  readonly id: string;
  readonly prompt_type: PromptType;
  readonly title: string;
  readonly prompt_text: string;
  readonly difficulty: Difficulty;
  readonly lifecycle_state: LifecycleState;
  readonly target_skill_slugs: string[];
  readonly rubric_id: string;
}

export interface ScenarioView {
  readonly id: string;
  readonly title: string;
  readonly business_context: string;
  readonly learner_objective: string;
  readonly constraints: string[];
  readonly stakeholder_tensions: string[];
  readonly lifecycle_state: LifecycleState;
  readonly target_skill_slugs: string[];
  readonly rubric_id: string;
  readonly mock_company: MockCompanyView | null;
  readonly mock_people: MockPersonView[];
}

export interface CollectionView {
  readonly id: string;
  readonly author_user_id: string;
  readonly organisation_id: string | null;
  readonly title: string;
  readonly summary: string;
  readonly target_audience: string;
  readonly difficulty: Difficulty;
  readonly lifecycle_state: LifecycleState;
  readonly verification_state: VerificationState;
  readonly discovery_tier: DiscoveryTier;
  readonly source_type: SourceType;
  readonly content_format_mix: string[];
  readonly target_skill_slugs: string[];
  readonly target_competency_slugs: string[];
  readonly rubric_ids: string[];
  readonly save_count: number;
  readonly saved_by_actor: boolean;
  readonly avg_rating: number | null;
  readonly rating_count: number;
  readonly rated_by_actor: number | null;
  readonly featured: boolean;
  readonly last_generation_artifact_id: string | null;
  readonly created_at: string;
  readonly updated_at: string;
  readonly prompt_items: PromptItemView[];
  readonly scenarios: ScenarioView[];
}

export interface CollectionListFilters {
  readonly difficulty?: Difficulty;
  readonly skill_slug?: string;
  readonly competency_slug?: string;
  readonly include_private?: boolean;
  readonly saved_only?: boolean;
  readonly discovery_tier?: DiscoveryTier;
  readonly author_user_id?: string;
  readonly organisation_id?: string;
}

// --- Practice --------------------------------------------------------------

export interface EvidenceItem {
  readonly quote: string;
  readonly explanation: string;
}

export interface PerSkillAssessment {
  readonly skill_slug: string;
  readonly score: number;
  readonly rationale: string;
  readonly evidence: EvidenceItem[];
}

export interface AssessmentAggregationOutput {
  readonly summary: string;
  readonly next_actions: string[];
}

export interface AssessmentArtifact {
  readonly prompt_version: string;
  readonly rubric_id: string;
  readonly rubric_version: string;
  readonly provider: string;
  readonly model_slug: string;
  readonly schema_version: string;
  readonly config_version: string;
  readonly overall_score: number;
  readonly summary: string;
  readonly per_skill_assessments: PerSkillAssessment[];
  readonly strengths: string[];
  readonly weaknesses: string[];
  readonly next_actions: string[];
  readonly raw_payload: Record<string, unknown>;
}

export interface QuickPracticePromptView {
  readonly content_item_id: string;
  readonly prompt_type: PromptType;
  readonly title: string;
  readonly prompt_text: string;
  readonly difficulty: Difficulty;
  readonly delivery_version: string;
  readonly target_skill_slugs: string[];
  readonly rubric_id: string;
  readonly rubric_version: string;
}

export interface QuickPracticeAssessmentView {
  readonly assessment_id: string;
  readonly attempt_id: string;
  readonly session_id: string;
  readonly validation_status: AssessmentValidationStatus;
  readonly prompt_version: string;
  readonly rubric_id: string;
  readonly rubric_version: string;
  readonly schema_version: string;
  readonly config_version: string;
  readonly provider: string;
  readonly model_slug: string;
  readonly overall_score: number | null;
  readonly per_skill_assessments: PerSkillAssessment[];
  readonly summary: string;
  readonly strengths: string[];
  readonly weaknesses: string[];
  readonly next_actions: string[];
  readonly trace_id: string;
  readonly pipeline_run_id: string;
  readonly rejection_code: string | null;
  readonly created_at: string;
  readonly raw_payload: Record<string, unknown>;
}

export interface AttemptView {
  readonly id: string;
  readonly session_id: string;
  readonly workflow_id: string;
  readonly status: AttemptStatus;
  readonly response_mode: string;
  readonly response_text: string | null;
  readonly last_error_code: string | null;
  readonly submitted_at: string | null;
  readonly assessed_at: string | null;
  readonly prompt: QuickPracticePromptView;
  readonly assessment: QuickPracticeAssessmentView | null;
}

export interface QuickPracticeSessionView {
  readonly session_id: string;
  readonly attempt_id: string;
  readonly workflow_id: string;
  readonly status: SessionStatus;
  readonly prompt: QuickPracticePromptView;
  readonly started_at: string;
  readonly trace_id: string;
}

// --- Commands --------------------------------------------------------------

export interface RegisterUserCommand {
  readonly email: string;
  readonly display_name: string;
  readonly role?: string;
  readonly target_role?: string;
  readonly goals?: string[];
  readonly practice_preferences?: Record<string, string>;
}

export interface UpdateProfileCommand {
  readonly target_role?: string | null;
  readonly goals?: string[] | null;
  readonly practice_preferences?: Record<string, string> | null;
}

export interface CollectionCreateCommand {
  readonly title: string;
  readonly summary: string;
  readonly target_audience: string;
  readonly difficulty: Difficulty;
  readonly content_format_mix?: string[];
  readonly target_skill_slugs: string[];
  readonly target_competency_slugs: string[];
  readonly rubric_ids: string[];
  readonly organisation_id?: string | null;
}

export interface PromptItemCreateCommand {
  readonly prompt_type: PromptType;
  readonly title: string;
  readonly prompt_text: string;
  readonly difficulty: Difficulty;
  readonly target_skill_slugs: string[];
  readonly rubric_id: string;
}

export interface MockCompanyInput {
  readonly name: string;
  readonly industry: string;
  readonly operating_context: string;
}

export interface MockPersonInput {
  readonly name: string;
  readonly role: string;
  readonly goals?: string[];
  readonly communication_style: string;
  readonly relationship_to_scenario: string;
}

export interface ScenarioCreateCommand {
  readonly title: string;
  readonly business_context: string;
  readonly learner_objective: string;
  readonly constraints?: string[];
  readonly stakeholder_tensions?: string[];
  readonly target_skill_slugs: string[];
  readonly rubric_id: string;
  readonly mock_company?: MockCompanyInput | null;
  readonly mock_people?: MockPersonInput[];
}

export interface StartQuickPracticeSessionCommand {
  readonly prompt_item_id: string;
}

export interface SubmitAttemptCommand {
  readonly response_text: string;
}

// --- Interview & Scenario sessions ----------------------------------------

export interface InterviewTurn {
  readonly turn_number: number;
  readonly question: string;
  readonly response: string;
}

export interface InterviewSessionView {
  readonly session_id: string;
  readonly attempt_id: string;
  readonly status: SessionStatus;
  readonly total_turns: number;
  readonly current_turn: number;
  readonly current_question: string;
  readonly competency_context: string;
  readonly history: InterviewTurn[];
  readonly target_skill_slugs: string[];
  readonly difficulty: Difficulty;
  readonly started_at: string;
}

export interface ScenarioStepEntry {
  readonly step_number: number;
  readonly prompt: string;
  readonly response: string;
}

export interface ScenarioSessionView {
  readonly session_id: string;
  readonly attempt_id: string;
  readonly status: SessionStatus;
  readonly scenario: ScenarioView;
  readonly total_steps: number;
  readonly current_step: number;
  readonly current_prompt_text: string;
  readonly history: ScenarioStepEntry[];
  readonly started_at: string;
}

// --- Derived view types (not in backend, useful for frontend) -------------

export interface CompetencyProgressView {
  readonly slug: string;
  readonly name: string;
  readonly description: string;
  readonly skills: SkillProgressView[];
  readonly overall_score: number;
  readonly confidence: 'low' | 'medium' | 'high';
}

export interface SkillProgressView {
  readonly slug: string;
  readonly name: string;
  readonly score: number;
  readonly evidence_count: number;
  readonly trend: 'up' | 'down' | 'stable';
}

export interface AttemptHistoryItem {
  readonly id: string;
  readonly session_id: string;
  readonly title: string;
  readonly practice_type: PracticeType;
  readonly score: number;
  readonly skill_slugs: string[];
  readonly created_at: string;
  readonly status: AttemptStatus;
}

// --- Practice Run (Aggregate) -----------------------------------------------

export type PracticeRunStatus = 'active' | 'completed' | 'abandoned';
export type PracticeRunItemType = 'prompt_item' | 'scenario';

export interface PracticeRunItemSummary {
  readonly id: string;
  readonly item_type: PracticeRunItemType;
  readonly title: string;
  readonly difficulty: Difficulty;
  readonly target_skill_slugs: string[];
  readonly status: 'pending' | 'active' | 'completed' | 'skipped';
}

export interface PracticeRunSummary {
  readonly total_items: number;
  readonly completed_items: number;
  readonly overall_score: number | null;
  readonly score_distribution: Record<string, number>;
  readonly skill_breakdown: Record<string, { avg_score: number; count: number }>;
  readonly practice_type_breakdown: Record<string, number>;
}

export interface PracticeRunView {
  readonly id: string;
  readonly user_id: string;
  readonly title: string;
  readonly status: PracticeRunStatus;
  readonly items: PracticeRunItemSummary[];
  readonly summary: PracticeRunSummary;
  readonly created_at: string;
  readonly updated_at: string;
  readonly completed_at: string | null;
}

export interface PracticeSessionView {
  readonly id: string;
  readonly practice_run_id: string;
  readonly sequence_index: number;
  readonly content_item_id: string;
  readonly content_item_type: PracticeRunItemType;
  readonly attempt_id: string;
  readonly status: SessionStatus;
  readonly score: number | null;
  readonly started_at: string;
  readonly completed_at: string | null;
}

export interface StartPracticeRunCommand {
  readonly title: string;
  readonly selected_items: readonly {
    readonly item_id: string;
    readonly item_type: PracticeRunItemType;
  }[];
}

export interface SubmitAttemptCommand {
  readonly response_text: string;
}

// --- Content Generation -----------------------------------------------------

export interface GenerationCounts {
  readonly quick_practice_prompt_count: number;
  readonly interview_prompt_count: number;
  readonly scenario_count: number;
  readonly scenario_artifact_count: number;
}

export interface StructuredCollectionGenerationCommand {
  readonly title_hint: string | null;
  readonly target_audience: string;
  readonly difficulty: Difficulty;
  readonly content_format_mix: string[];
  readonly target_skill_slugs: string[];
  readonly target_competency_slugs: string[];
  readonly rubric_ids: string[];
  readonly domain: string;
  readonly workplace_context: string;
  readonly scenario_theme: string;
  readonly realism_notes?: string[];
  readonly counts: GenerationCounts;
}

export interface ChatCollectionGenerationCommand {
  readonly prompt: string;
  readonly target_audience: string;
  readonly difficulty: Difficulty;
  readonly content_format_mix: string[];
  readonly target_skill_slugs: string[];
  readonly target_competency_slugs: string[];
  readonly rubric_ids: string[];
  readonly counts: GenerationCounts;
}

export interface ContentGenerationArtifactView {
  readonly id: string;
  readonly generation_mode: string;
  readonly prompt_version: string;
  readonly schema_version: string;
  readonly config_version: string;
  readonly provider: string;
  readonly model_slug: string;
  readonly created_at: string;
}

export interface CollectionGenerationView {
  readonly collection: CollectionView;
  readonly generation_artifact_id: string;
  readonly generation_mode: string;
  readonly prompt_version: string;
  readonly provider: string;
  readonly model_slug: string;
}

// --- Admin: Users & User Management ------------------------------------------

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

// --- Admin: Learners & Relationships -----------------------------------------

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

// --- Admin: Analytics Overview ----------------------------------------------

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

// --- Admin: Collections & Verification ---------------------------------------

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
  readonly collection: CollectionView;
  readonly latest_review: CollectionVerificationReviewView | null;
  readonly history: CollectionVerificationReviewView[];
}

// --- Admin: Evaluation Dashboard ---------------------------------------------

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

// --- Admin: Prompts ----------------------------------------------------------

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
  readonly version_a: string;
  readonly version_b: string;
  readonly template_a: string;
  readonly template_b: string;
  readonly variables_schema_a: Record<string, unknown>;
  readonly variables_schema_b: Record<string, unknown>;
  readonly metrics_a: PromptAnalyticsView | null;
  readonly metrics_b: PromptAnalyticsView | null;
}

// --- Admin: Pipelines --------------------------------------------------------

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
  readonly stage_metrics: PipelineStageMetricsView[];
}

// --- Admin: Rubrics ----------------------------------------------------------

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

export interface RubricCriterionView {
  readonly criterion_ref: string;
  readonly skill_slug: string;
  readonly title: string;
  readonly description: string;
  readonly weight: number;
  readonly required: boolean;
  readonly position: number;
  readonly levels: RubricLevelView[];
}

export interface RubricView {
  readonly rubric_id: string;
  readonly family: string;
  readonly version: string;
  readonly content_type: string;
  readonly schema_version: string;
  readonly name: string;
  readonly criteria: RubricCriterionView[];
}

// --- Admin: Audit & Events --------------------------------------------------

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

// --- Generation Streaming ----------------------------------------------------

export type GenerationStage =
  | 'pending'
  | 'input_guard'
  | 'blueprint_transform'
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

export interface GenerationProgressState {
  readonly status: 'idle' | 'started' | 'streaming' | 'completed' | 'failed' | 'cancelled';
  readonly generation_id: string | null;
  readonly stream_token: string | null;
  readonly stages_completed: GenerationStage[];
  readonly current_stage: GenerationStage | null;
  readonly progress_percent: number;
  readonly blueprint: BlueprintInfo | null;
  readonly prompt_items: PromptItemDraft[];
  readonly collection: CollectionView | null;
  readonly error: string | null;
}
