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
  readonly title: string;
  readonly summary: string;
  readonly target_audience: string;
  readonly difficulty: Difficulty;
  readonly lifecycle_state: LifecycleState;
  readonly verification_state: VerificationState;
  readonly content_format_mix: string[];
  readonly target_skill_slugs: string[];
  readonly target_competency_slugs: string[];
  readonly rubric_ids: string[];
  readonly prompt_items: PromptItemView[];
  readonly scenarios: ScenarioView[];
}

export interface CollectionListFilters {
  readonly difficulty?: Difficulty;
  readonly skill_slug?: string;
  readonly competency_slug?: string;
  readonly include_private?: boolean;
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
