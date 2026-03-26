"""Catalog domain models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator


class ScenarioSupportingArtifactInput(BaseModel):
    artifact_type: str
    title: str
    body: str


class MockCompanyInput(BaseModel):
    name: str
    industry: str
    operating_context: str


class MockPersonInput(BaseModel):
    name: str
    role: str
    goals: list[str] = Field(default_factory=list)
    communication_style: str
    relationship_to_scenario: str


class ScenarioCreateCommand(BaseModel):
    title: str
    business_context: str
    learner_objective: str
    constraints: list[str] = Field(default_factory=list)
    stakeholder_tensions: list[str] = Field(default_factory=list)
    target_skill_slugs: list[str]
    rubric_id: str
    mock_company: MockCompanyInput | None = None
    mock_people: list[MockPersonInput] = Field(default_factory=list)
    supporting_artifacts: list[ScenarioSupportingArtifactInput] = Field(default_factory=list)


class ScenarioUpdateCommand(ScenarioCreateCommand):
    pass


class ScenarioSupportingArtifactView(BaseModel):
    id: str
    artifact_type: str
    title: str
    body: str


class MockCompanyView(BaseModel):
    id: str
    name: str
    industry: str
    operating_context: str


class MockPersonView(BaseModel):
    id: str
    name: str
    role: str
    goals: list[str]
    communication_style: str
    relationship_to_scenario: str


class ScenarioView(BaseModel):
    id: str
    title: str
    business_context: str
    learner_objective: str
    constraints: list[str]
    stakeholder_tensions: list[str]
    lifecycle_state: str
    target_skill_slugs: list[str]
    rubric_id: str
    supporting_artifacts: list[ScenarioSupportingArtifactView] = Field(default_factory=list)
    mock_company: MockCompanyView | None = None
    mock_people: list[MockPersonView] = Field(default_factory=list)


class PromptItemCreateCommand(BaseModel):
    prompt_type: str
    title: str
    prompt_text: str
    difficulty: str
    target_skill_slugs: list[str]
    rubric_id: str


class PromptItemUpdateCommand(PromptItemCreateCommand):
    pass


class PromptItemView(BaseModel):
    id: str
    prompt_type: str
    title: str
    prompt_text: str
    difficulty: str
    lifecycle_state: str
    target_skill_slugs: list[str]
    rubric_id: str


class CollectionCreateCommand(BaseModel):
    title: str
    summary: str
    target_audience: str
    difficulty: str
    content_format_mix: list[str] = Field(default_factory=list)
    target_skill_slugs: list[str]
    target_competency_slugs: list[str]
    rubric_ids: list[str]
    organisation_id: str | None = None


class CollectionUpdateCommand(CollectionCreateCommand):
    pass


class CollectionLifecycleCommand(BaseModel):
    lifecycle_state: str
    verification_state: str | None = None


class CollectionSaveCommand(BaseModel):
    saved: bool


class CollectionListFilters(BaseModel):
    difficulty: str | None = None
    skill_slug: str | None = None
    competency_slug: str | None = None
    include_private: bool = True
    saved_only: bool = False
    discovery_tier: str | None = None
    author_user_id: str | None = None
    organisation_id: str | None = None


class CollectionView(BaseModel):
    id: str
    author_user_id: str
    organisation_id: str | None = None
    title: str
    summary: str
    target_audience: str
    difficulty: str
    lifecycle_state: str
    verification_state: str
    discovery_tier: str
    source_type: str
    content_format_mix: list[str]
    target_skill_slugs: list[str]
    target_competency_slugs: list[str]
    rubric_ids: list[str]
    save_count: int = 0
    saved_by_actor: bool = False
    last_generation_artifact_id: str | None = None
    prompt_items: list[PromptItemView] = Field(default_factory=list)
    scenarios: list[ScenarioView] = Field(default_factory=list)


class CollectionGenerationCounts(BaseModel):
    quick_practice_prompt_count: int = Field(default=0, ge=0, le=3)
    interview_prompt_count: int = Field(default=0, ge=0, le=3)
    scenario_count: int = Field(default=0, ge=0, le=2)
    scenario_artifact_count: int = Field(default=0, ge=0, le=3)

    @model_validator(mode="after")
    def validate_non_empty(self) -> CollectionGenerationCounts:
        if (
            self.quick_practice_prompt_count + self.interview_prompt_count + self.scenario_count
            <= 0
        ):
            raise ValueError("At least one generated content item is required")
        return self


class StructuredCollectionGenerationCommand(BaseModel):
    title_hint: str | None = None
    target_audience: str
    difficulty: str
    content_format_mix: list[str]
    target_skill_slugs: list[str]
    target_competency_slugs: list[str]
    rubric_ids: list[str]
    domain: str
    workplace_context: str
    scenario_theme: str
    realism_notes: list[str] = Field(default_factory=list)
    counts: CollectionGenerationCounts


class ChatCollectionGenerationCommand(BaseModel):
    prompt: str
    target_audience: str
    difficulty: str
    content_format_mix: list[str]
    target_skill_slugs: list[str]
    target_competency_slugs: list[str]
    rubric_ids: list[str]
    counts: CollectionGenerationCounts


class PromptItemGenerationCounts(BaseModel):
    quick_practice_prompt_count: int = Field(default=0, ge=0, le=6)
    interview_prompt_count: int = Field(default=0, ge=0, le=6)

    @model_validator(mode="after")
    def validate_non_empty(self) -> PromptItemGenerationCounts:
        if self.quick_practice_prompt_count + self.interview_prompt_count <= 0:
            raise ValueError("At least one generated prompt item is required")
        return self


class StructuredPromptItemGenerationCommand(BaseModel):
    title_hint: str | None = None
    workplace_context: str
    generation_focus: str
    realism_notes: list[str] = Field(default_factory=list)
    target_skill_slugs: list[str] = Field(default_factory=list)
    counts: PromptItemGenerationCounts


class ChatPromptItemGenerationCommand(BaseModel):
    prompt: str
    target_skill_slugs: list[str] = Field(default_factory=list)
    counts: PromptItemGenerationCounts


class GeneratedPromptItemPlan(BaseModel):
    prompt_type: str
    title_hint: str
    generation_brief: str
    difficulty: str
    target_skill_slugs: list[str]
    rubric_id: str


class GeneratedScenarioPlan(BaseModel):
    title_hint: str
    generation_brief: str
    target_skill_slugs: list[str]
    rubric_id: str
    supporting_artifact_count: int = Field(default=0, ge=0, le=3)


class GeneratedCollectionBlueprint(BaseModel):
    prompt_version: str
    provider: str
    model_slug: str
    title: str
    summary: str
    prompt_items: list[GeneratedPromptItemPlan] = Field(default_factory=list)
    scenarios: list[GeneratedScenarioPlan] = Field(default_factory=list)


class GeneratedPromptItemPlanBatch(BaseModel):
    prompt_version: str
    provider: str
    model_slug: str
    prompt_items: list[GeneratedPromptItemPlan] = Field(default_factory=list)


class GeneratedPromptItemDraft(BaseModel):
    prompt_type: str
    title: str
    prompt_text: str
    difficulty: str
    target_skill_slugs: list[str]
    rubric_id: str


class GeneratedScenarioDraft(BaseModel):
    title: str
    business_context: str
    learner_objective: str
    constraints: list[str] = Field(default_factory=list)
    stakeholder_tensions: list[str] = Field(default_factory=list)
    target_skill_slugs: list[str]
    rubric_id: str
    mock_company: MockCompanyInput | None = None
    mock_people: list[MockPersonInput] = Field(default_factory=list)
    supporting_artifacts: list[ScenarioSupportingArtifactInput] = Field(default_factory=list)


class GeneratedCollectionDraft(BaseModel):
    prompt_version: str
    provider: str
    model_slug: str
    title: str
    summary: str
    target_audience: str
    difficulty: str
    content_format_mix: list[str]
    target_skill_slugs: list[str]
    target_competency_slugs: list[str]
    rubric_ids: list[str]
    prompt_items: list[GeneratedPromptItemDraft] = Field(default_factory=list)
    scenarios: list[GeneratedScenarioDraft] = Field(default_factory=list)


class CollectionGenerationView(BaseModel):
    collection: CollectionView
    generation_artifact_id: str
    generation_mode: str
    prompt_version: str
    provider: str
    model_slug: str


class GenerationWorkerArtifact(BaseModel):
    pipeline_name: str
    child_run_id: str
    correlation_id: str
    prompt_version: str
    provider: str
    model_slug: str
    usage: dict[str, int] = Field(default_factory=dict)
    output_payload: dict[str, Any] = Field(default_factory=dict)
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class GenerationManifest(BaseModel):
    planner: GenerationWorkerArtifact | None = None
    prompt_items: list[GenerationWorkerArtifact] = Field(default_factory=list)
    scenarios: list[GenerationWorkerArtifact] = Field(default_factory=list)


class PromptItemGenerationView(BaseModel):
    collection: CollectionView
    prompt_items: list[PromptItemView] = Field(default_factory=list)
    generation_artifact_id: str
    generation_mode: str
    prompt_version: str
    provider: str
    model_slug: str
