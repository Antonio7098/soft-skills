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
export type PracticeRunStatus = 'active' | 'completed' | 'abandoned';
export type PracticeRunItemType = 'prompt_item' | 'scenario';
