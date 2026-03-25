"""Persistence models for foundational observability artifacts."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from soft_skills_backend.persistence.base import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class WorkflowEventRecord(Base):
    """Structured event persistence."""

    __tablename__ = "workflow_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    event_type: Mapped[str] = mapped_column(String(128), index=True)
    request_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    workflow_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class PipelineRunRecord(Base):
    """Stageflow pipeline run audit log."""

    __tablename__ = "pipeline_runs"

    pipeline_run_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    pipeline_name: Mapped[str] = mapped_column(String(128), index=True)
    topology: Mapped[str | None] = mapped_column(String(128), nullable=True)
    execution_mode: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    request_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    failed_stage: Mapped[str | None] = mapped_column(String(128), nullable=True)
    stage_results: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ProviderCallRecord(Base):
    """Provider call audit log."""

    __tablename__ = "provider_calls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    call_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    operation: Mapped[str] = mapped_column(String(64), index=True)
    provider: Mapped[str] = mapped_column(String(64), index=True)
    model_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    success: Mapped[bool]
    latency_ms: Mapped[int | None] = mapped_column(nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    pipeline_run_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class UserAccountRecord(Base):
    """Authenticated user account."""

    __tablename__ = "user_accounts"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), index=True)
    auth_provider: Mapped[str] = mapped_column(String(64))
    auth_subject: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class LearnerProfileRecord(Base):
    """Learner profile linked to a user account."""

    __tablename__ = "learner_profiles"

    user_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    target_role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    goals: Mapped[list[str]] = mapped_column(JSON, default=list)
    practice_preferences: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class SkillRecord(Base):
    """Platform-defined skill."""

    __tablename__ = "skills"

    slug: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    description: Mapped[str] = mapped_column(Text)


class CompetencyRecord(Base):
    """Platform-defined competency."""

    __tablename__ = "competencies"

    slug: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    description: Mapped[str] = mapped_column(Text)


class CompetencySkillMapRecord(Base):
    """Mapping between competencies and skills."""

    __tablename__ = "competency_skill_map"

    competency_slug: Mapped[str] = mapped_column(String(64), primary_key=True)
    skill_slug: Mapped[str] = mapped_column(String(64), primary_key=True)
    weight: Mapped[float]


class RubricRecord(Base):
    """Versioned rubric family record."""

    __tablename__ = "rubrics"

    rubric_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    family: Mapped[str] = mapped_column(String(64), index=True)
    version: Mapped[str] = mapped_column(String(32))
    content_type: Mapped[str] = mapped_column(String(64), index=True)
    schema_version: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(255))
    criteria: Mapped[list[str]] = mapped_column(JSON, default=list)


class CollectionRecord(Base):
    """Collection browsing and authoring unit."""

    __tablename__ = "collections"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    author_user_id: Mapped[str] = mapped_column(String(32), index=True)
    title: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str] = mapped_column(Text)
    target_audience: Mapped[str] = mapped_column(String(255))
    difficulty: Mapped[str] = mapped_column(String(32), index=True)
    lifecycle_state: Mapped[str] = mapped_column(String(32), index=True)
    verification_state: Mapped[str] = mapped_column(String(32), index=True)
    content_format_mix: Mapped[list[str]] = mapped_column(JSON, default=list)
    target_skill_slugs: Mapped[list[str]] = mapped_column(JSON, default=list)
    target_competency_slugs: Mapped[list[str]] = mapped_column(JSON, default=list)
    rubric_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class PromptItemRecord(Base):
    """Quick practice or interview prompt item."""

    __tablename__ = "prompt_items"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    collection_id: Mapped[str] = mapped_column(String(32), index=True)
    author_user_id: Mapped[str] = mapped_column(String(32), index=True)
    prompt_type: Mapped[str] = mapped_column(String(32), index=True)
    title: Mapped[str] = mapped_column(String(255))
    prompt_text: Mapped[str] = mapped_column(Text)
    difficulty: Mapped[str] = mapped_column(String(32))
    lifecycle_state: Mapped[str] = mapped_column(String(32), index=True)
    target_skill_slugs: Mapped[list[str]] = mapped_column(JSON, default=list)
    rubric_id: Mapped[str] = mapped_column(String(128), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ScenarioRecord(Base):
    """Scenario authoring record."""

    __tablename__ = "scenarios"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    collection_id: Mapped[str] = mapped_column(String(32), index=True)
    author_user_id: Mapped[str] = mapped_column(String(32), index=True)
    title: Mapped[str] = mapped_column(String(255))
    business_context: Mapped[str] = mapped_column(Text)
    learner_objective: Mapped[str] = mapped_column(Text)
    constraints: Mapped[list[str]] = mapped_column(JSON, default=list)
    stakeholder_tensions: Mapped[list[str]] = mapped_column(JSON, default=list)
    lifecycle_state: Mapped[str] = mapped_column(String(32), index=True)
    target_skill_slugs: Mapped[list[str]] = mapped_column(JSON, default=list)
    rubric_id: Mapped[str] = mapped_column(String(128), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class MockCompanyRecord(Base):
    """Mock company attached to a scenario."""

    __tablename__ = "mock_companies"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    scenario_id: Mapped[str] = mapped_column(String(32), index=True)
    name: Mapped[str] = mapped_column(String(255))
    industry: Mapped[str] = mapped_column(String(255))
    operating_context: Mapped[str] = mapped_column(Text)


class MockPersonRecord(Base):
    """Mock person attached to a scenario."""

    __tablename__ = "mock_people"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    scenario_id: Mapped[str] = mapped_column(String(32), index=True)
    mock_company_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(255))
    goals: Mapped[list[str]] = mapped_column(JSON, default=list)
    communication_style: Mapped[str] = mapped_column(Text)
    relationship_to_scenario: Mapped[str] = mapped_column(Text)
