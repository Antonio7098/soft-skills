import type {
  Difficulty,
  PracticeType,
  AttemptStatus,
  SessionStatus,
  PromptType,
} from './shared';

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
  readonly validation_status: string;
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

export interface StartQuickPracticeSessionCommand {
  readonly prompt_item_id: string;
}

export interface SubmitAttemptCommand {
  readonly response_text: string;
}

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
  readonly scenario: import('./catalog').ScenarioView;
  readonly total_steps: number;
  readonly current_step: number;
  readonly current_prompt_text: string;
  readonly history: ScenarioStepEntry[];
  readonly started_at: string;
}

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

export interface PracticeRunItemSummary {
  readonly id: string;
  readonly item_type: 'prompt_item' | 'scenario';
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
  readonly run_id: string;
  readonly workflow_id: string;
  readonly status: 'active' | 'completed' | 'abandoned';
  readonly total_items: number;
  readonly completed_items: number;
  readonly validated_items: number;
  readonly failed_items: number;
  readonly current_attempt_id: string | null;
  readonly started_at: string;
  readonly completed_at: string | null;
  readonly items: PracticeRunItemSummary[];
  readonly summary: PracticeRunSummary;
}

export interface PracticeSessionView {
  readonly id: string;
  readonly practice_run_id: string;
  readonly sequence_index: number;
  readonly content_item_id: string;
  readonly content_item_type: 'prompt_item' | 'scenario';
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
    readonly item_type: 'prompt_item' | 'scenario';
    readonly prompt_type?: string;
  }[];
}
