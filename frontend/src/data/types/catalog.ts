import type {
  Difficulty,
  LifecycleState,
  DiscoveryTier,
  SourceType,
  PromptType,
} from './shared';

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
  readonly organisation_id?: string;
}

export interface ScenarioView {
  readonly id: string;
  readonly title: string;
  readonly prompt_text: string;
  readonly questions: string[];
  readonly business_context: string;
  readonly learner_objective: string;
  readonly constraints: string[];
  readonly stakeholder_tensions: string[];
  readonly lifecycle_state: LifecycleState;
  readonly target_skill_slugs: string[];
  readonly rubric_id: string;
  readonly mock_company: MockCompanyView | null;
  readonly mock_people: MockPersonView[];
  readonly organisation_id?: string;
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
  readonly verification_state: string;
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
  readonly prompt_text: string;
  readonly business_context: string;
  readonly learner_objective: string;
  readonly constraints?: string[];
  readonly stakeholder_tensions?: string[];
  readonly target_skill_slugs: string[];
  readonly rubric_id: string;
  readonly mock_company?: MockCompanyInput | null;
  readonly mock_people?: MockPersonInput[];
}

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
  readonly target_skill_slugs?: string[];
  readonly target_competency_slugs?: string[];
  readonly rubric_ids?: string[];
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
