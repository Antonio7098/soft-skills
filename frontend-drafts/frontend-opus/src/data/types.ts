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

export interface TaxonomySnapshot {
  readonly skills: SkillView[];
  readonly competencies: CompetencyView[];
  readonly rubrics: RubricView[];
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

export interface SkillScore {
  readonly skill_slug: string;
  readonly score: number;
  readonly rationale: string;
}

export interface EvidenceItem {
  readonly skill_slug: string;
  readonly quote: string;
  readonly explanation: string;
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
  readonly skill_scores: SkillScore[];
  readonly evidence: EvidenceItem[];
  readonly rationale: string | null;
  readonly strengths: string[];
  readonly weaknesses: string[];
  readonly next_actions: string[];
  readonly trace_id: string;
  readonly pipeline_run_id: string;
  readonly rejection_code: string | null;
  readonly created_at: string;
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
