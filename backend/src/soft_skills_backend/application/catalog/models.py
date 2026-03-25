"""Catalog domain models."""

from __future__ import annotations

from pydantic import BaseModel, Field


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
    mock_company: MockCompanyView | None = None
    mock_people: list[MockPersonView] = Field(default_factory=list)


class PromptItemCreateCommand(BaseModel):
    prompt_type: str
    title: str
    prompt_text: str
    difficulty: str
    target_skill_slugs: list[str]
    rubric_id: str


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


class CollectionLifecycleCommand(BaseModel):
    lifecycle_state: str
    verification_state: str | None = None


class CollectionListFilters(BaseModel):
    difficulty: str | None = None
    skill_slug: str | None = None
    competency_slug: str | None = None
    include_private: bool = True


class CollectionView(BaseModel):
    id: str
    author_user_id: str
    title: str
    summary: str
    target_audience: str
    difficulty: str
    lifecycle_state: str
    verification_state: str
    content_format_mix: list[str]
    target_skill_slugs: list[str]
    target_competency_slugs: list[str]
    rubric_ids: list[str]
    prompt_items: list[PromptItemView] = Field(default_factory=list)
    scenarios: list[ScenarioView] = Field(default_factory=list)
