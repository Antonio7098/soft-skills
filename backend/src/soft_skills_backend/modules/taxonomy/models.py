"""Taxonomy domain models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SkillView(BaseModel):
    slug: str
    name: str
    description: str
    organisation_id: str | None = None


class CompetencyView(BaseModel):
    slug: str
    name: str
    description: str
    skill_slugs: list[str] = Field(default_factory=list)
    organisation_id: str | None = None


class RubricView(BaseModel):
    rubric_id: str
    family: str
    version: str
    content_type: str
    schema_version: str
    name: str
    organisation_id: str | None = None


class TaxonomySnapshot(BaseModel):
    skills: list[SkillView]
    competencies: list[CompetencyView]
    rubrics: list[RubricView]
