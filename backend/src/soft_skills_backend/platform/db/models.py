"""Persistence models for foundational observability artifacts."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from soft_skills_backend.platform.db.base import Base


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
    organisation_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
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
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(nullable=True)


class UserAccountRecord(Base):
    """Authenticated user account."""

    __tablename__ = "user_accounts"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255))
    auth_provider: Mapped[str] = mapped_column(String(64))
    auth_subject: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class OrganisationRecord(Base):
    """Organisation providing tenant isolation."""

    __tablename__ = "organisations"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class OrganisationMembershipRecord(Base):
    """Organisation membership linking users to organisations."""

    __tablename__ = "organisation_memberships"

    organisation_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    role: Mapped[str] = mapped_column(String(32))
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (Index("ix_organisation_memberships_user_id", "user_id"),)


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
    __table_args__ = (UniqueConstraint("slug", "organisation_id", name="uq_skill_org_slug"),)

    slug: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    organisation_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("organisations.id"), index=True, nullable=True
    )


class CompetencyRecord(Base):
    """Platform-defined competency."""

    __tablename__ = "competencies"
    __table_args__ = (UniqueConstraint("slug", "organisation_id", name="uq_competency_org_slug"),)

    slug: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    organisation_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("organisations.id"), index=True, nullable=True
    )


class CompetencySkillMapRecord(Base):
    """Mapping between competencies and skills."""

    __tablename__ = "competency_skill_map"

    competency_slug: Mapped[str] = mapped_column(String(64), primary_key=True)
    skill_slug: Mapped[str] = mapped_column(String(64), primary_key=True)
    weight: Mapped[float]


class OrganisationSkillMapRecord(Base):
    """Mapping between org competencies and org skills (overrides canon for that org)."""

    __tablename__ = "org_skill_maps"
    __table_args__ = (
        UniqueConstraint(
            "organisation_id", "competency_slug", "skill_slug", name="uq_org_skill_map"
        ),
        Index("ix_org_skill_maps_org", "organisation_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organisation_id: Mapped[str] = mapped_column(String(32), index=True)
    competency_slug: Mapped[str] = mapped_column(String(64), index=True)
    skill_slug: Mapped[str] = mapped_column(String(64), index=True)
    weight: Mapped[float]


class OrganisationPromptConfigRecord(Base):
    """Org-level prompt config override by task_kind."""

    __tablename__ = "organisation_prompt_configs"

    organisation_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    task_kind: Mapped[str] = mapped_column(String(32), primary_key=True)
    prompt_id: Mapped[str] = mapped_column(String(32), nullable=False)
    prompt_version_id: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class OrganisationRubricConfigRecord(Base):
    """Org-level rubric config override by skill_slug."""

    __tablename__ = "organisation_rubric_configs"

    organisation_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    skill_slug: Mapped[str] = mapped_column(String(64), primary_key=True)
    rubric_id: Mapped[str] = mapped_column(String(32), nullable=False)
    rubric_version_id: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class RubricRecord(Base):
    """Parent rubric entity (new parent-child model)."""

    __tablename__ = "rubrics"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    skill_slug: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    organisation_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("organisations.id"), index=True, nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_type: Mapped[str] = mapped_column(String(64), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        UniqueConstraint("skill_slug", "organisation_id", name="uq_rubric_skill_org"),
    )


class RubricVersionRecord(Base):
    """Child rubric version entity with embedded criteria."""

    __tablename__ = "rubric_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rubric_id: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    criteria: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        UniqueConstraint("rubric_id", "version", name="uq_rubric_version_rubric_version"),
    )


class CollectionRecord(Base):
    """Collection browsing and authoring unit."""

    __tablename__ = "collections"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    author_user_id: Mapped[str] = mapped_column(String(32), index=True)
    organisation_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("organisations.id"), index=True, nullable=True
    )
    title: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str] = mapped_column(Text)
    target_audience: Mapped[str] = mapped_column(String(255))
    difficulty: Mapped[str] = mapped_column(String(32), index=True)
    lifecycle_state: Mapped[str] = mapped_column(String(32), index=True)
    verification_state: Mapped[str] = mapped_column(String(32), index=True)
    source_type: Mapped[str] = mapped_column(String(32), index=True, default="manual")
    last_generation_artifact_id: Mapped[str | None] = mapped_column(
        String(32), index=True, nullable=True
    )
    content_format_mix: Mapped[list[str]] = mapped_column(JSON, default=list)
    target_skill_slugs: Mapped[list[str]] = mapped_column(JSON, default=list)
    target_competency_slugs: Mapped[list[str]] = mapped_column(JSON, default=list)
    rubric_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    avg_rating: Mapped[float | None] = mapped_column(Integer, nullable=True)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    featured: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class PromptItemRecord(Base):
    """Quick practice or interview prompt item."""

    __tablename__ = "prompt_items"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    collection_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    author_user_id: Mapped[str] = mapped_column(String(32), index=True)
    organisation_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("organisations.id"), index=True, nullable=True
    )
    prompt_type: Mapped[str] = mapped_column(String(32), index=True)
    title: Mapped[str] = mapped_column(String(255))
    prompt_text: Mapped[str] = mapped_column(Text)
    difficulty: Mapped[str] = mapped_column(String(32))
    lifecycle_state: Mapped[str] = mapped_column(String(32), index=True)
    target_skill_slugs: Mapped[list[str]] = mapped_column(JSON, default=list)
    rubric_id: Mapped[str] = mapped_column(String(128), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ScenarioRecord(Base):
    """Scenario authoring record."""

    __tablename__ = "scenarios"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    collection_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    author_user_id: Mapped[str] = mapped_column(String(32), index=True)
    organisation_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("organisations.id"), index=True, nullable=True
    )
    title: Mapped[str] = mapped_column(String(255))
    business_context: Mapped[str] = mapped_column(Text)
    learner_objective: Mapped[str] = mapped_column(Text)
    constraints: Mapped[list[str]] = mapped_column(JSON, default=list)
    stakeholder_tensions: Mapped[list[str]] = mapped_column(JSON, default=list)
    questions: Mapped[list[str]] = mapped_column(JSON, default=list)
    lifecycle_state: Mapped[str] = mapped_column(String(32), index=True)
    target_skill_slugs: Mapped[list[str]] = mapped_column(JSON, default=list)
    rubric_id: Mapped[str] = mapped_column(String(128), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


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


class ScenarioSupportingArtifactRecord(Base):
    """Scenario supporting artifacts persisted for authoring and replay."""

    __tablename__ = "scenario_supporting_artifacts"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    scenario_id: Mapped[str] = mapped_column(String(32), index=True)
    artifact_type: Mapped[str] = mapped_column(String(32), index=True)
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class CollectionSaveRecord(Base):
    """Saved collection state for later reuse."""

    __tablename__ = "collection_saves"

    user_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    collection_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    saved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class CollectionRatingRecord(Base):
    """User rating for a collection."""

    __tablename__ = "collection_ratings"

    user_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    collection_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    rating: Mapped[int] = mapped_column(Integer, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class CollectionVerificationReviewRecord(Base):
    """Durable admin verification transition audit."""

    __tablename__ = "collection_verification_reviews"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    collection_id: Mapped[str] = mapped_column(String(32), index=True)
    reviewer_user_id: Mapped[str] = mapped_column(String(32), index=True)
    previous_verification_state: Mapped[str] = mapped_column(String(32))
    next_verification_state: Mapped[str] = mapped_column(String(32), index=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    workflow_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class AdminLearnerRelationshipRecord(Base):
    """Explicit admin-to-learner access relationship."""

    __tablename__ = "admin_learner_relationships"

    learner_user_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    admin_user_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    relationship_type: Mapped[str] = mapped_column(String(32), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ContentGenerationArtifactRecord(Base):
    """Validated LLM generation artifact for creator workflows."""

    __tablename__ = "content_generation_artifacts"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    collection_id: Mapped[str] = mapped_column(String(32), index=True)
    author_user_id: Mapped[str] = mapped_column(String(32), index=True)
    generation_mode: Mapped[str] = mapped_column(String(32), index=True)
    prompt_version: Mapped[str] = mapped_column(String(64), index=True)
    schema_version: Mapped[str] = mapped_column(String(64))
    config_version: Mapped[str] = mapped_column(String(64), index=True)
    provider: Mapped[str] = mapped_column(String(64), index=True)
    model_slug: Mapped[str] = mapped_column(String(128))
    request_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    workflow_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    input_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    output_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class PromptRecord(Base):
    """Parent prompt entity."""

    __tablename__ = "prompts"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    organisation_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_type: Mapped[str] = mapped_column(String(32), nullable=False)
    variables_schema: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (UniqueConstraint("organisation_id", "name", name="uq_prompt_org_name"),)


class PromptVersionRecord(Base):
    """Database-backed versioned prompt template (child of PromptRecord)."""

    __tablename__ = "prompt_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prompt_id: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    version: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    template: Mapped[str] = mapped_column(Text, nullable=False)
    variables_schema: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    output_schema: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(32), index=True, nullable=False, default="draft")
    parent_version_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        UniqueConstraint("prompt_id", "version", name="uq_prompt_version_prompt_version"),
    )


class PromptRenderMetricsRecord(Base):
    """Aggregated prompt render metrics by prompt version."""

    __tablename__ = "prompt_render_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prompt_version_id: Mapped[int] = mapped_column(Integer, index=True)
    render_count: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    last_rendered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("ix_prompt_render_metrics_version_id", "prompt_version_id", unique=True),
    )


class PromptRenderEventRecord(Base):
    """One prompt render event for lineage and audit."""

    __tablename__ = "prompt_render_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    prompt_version_id: Mapped[int] = mapped_column(Integer, index=True)
    success: Mapped[bool] = mapped_column(Boolean)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    rendered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class PracticeRunRecord(Base):
    """Durable aggregate practice run state."""

    __tablename__ = "practice_runs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(32), index=True)
    workflow_id: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    total_items: Mapped[int] = mapped_column(Integer)
    completed_items: Mapped[int] = mapped_column(Integer, default=0)
    validated_items: Mapped[int] = mapped_column(Integer, default=0)
    failed_items: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PracticeSessionRecord(Base):
    """Durable practice session state."""

    __tablename__ = "practice_sessions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(32), index=True)
    practice_type: Mapped[str] = mapped_column(String(32), index=True)
    content_item_id: Mapped[str] = mapped_column(String(32), index=True)
    content_item_type: Mapped[str] = mapped_column(String(32))
    practice_run_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    sequence_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    workflow_id: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    delivery_version: Mapped[str] = mapped_column(String(64))
    rubric_id: Mapped[str] = mapped_column(String(128), index=True)
    rubric_version: Mapped[str] = mapped_column(String(32))
    prompt_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    last_attempt_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AttemptRecord(Base):
    """Durable learner attempt state."""

    __tablename__ = "attempts"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(32), index=True)
    user_id: Mapped[str] = mapped_column(String(32), index=True)
    workflow_id: Mapped[str] = mapped_column(String(64), index=True)
    practice_type: Mapped[str] = mapped_column(String(32), index=True)
    content_item_id: Mapped[str] = mapped_column(String(32), index=True)
    content_item_type: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), index=True)
    response_mode: Mapped[str] = mapped_column(String(32))
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    delivery_version: Mapped[str] = mapped_column(String(64))
    rubric_id: Mapped[str] = mapped_column(String(128), index=True)
    rubric_version: Mapped[str] = mapped_column(String(32))
    assessment_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    last_error_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    assessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AssessmentRecord(Base):
    """Validated or rejected assessment artifact."""

    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    attempt_id: Mapped[str] = mapped_column(String(32), index=True)
    session_id: Mapped[str] = mapped_column(String(32), index=True)
    user_id: Mapped[str] = mapped_column(String(32), index=True)
    workflow_id: Mapped[str] = mapped_column(String(64), index=True)
    practice_type: Mapped[str] = mapped_column(String(32), index=True)
    validation_status: Mapped[str] = mapped_column(String(32), index=True)
    prompt_version: Mapped[str] = mapped_column(String(64))
    rubric_id: Mapped[str] = mapped_column(String(128), index=True)
    rubric_version: Mapped[str] = mapped_column(String(32))
    schema_version: Mapped[str] = mapped_column(String(64))
    config_version: Mapped[str] = mapped_column(String(64))
    provider: Mapped[str] = mapped_column(String(64), index=True)
    model_slug: Mapped[str] = mapped_column(String(128), index=True)
    overall_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    skill_scores: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    strengths: Mapped[list[str]] = mapped_column(JSON, default=list)
    weaknesses: Mapped[list[str]] = mapped_column(JSON, default=list)
    next_actions: Mapped[list[str]] = mapped_column(JSON, default=list)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    rejection_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    trace_id: Mapped[str] = mapped_column(String(32), index=True)
    pipeline_run_id: Mapped[str] = mapped_column(String(32), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class AssessmentSkillResultRecord(Base):
    """Stored per-skill assessment result."""

    __tablename__ = "assessment_skill_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    assessment_id: Mapped[str] = mapped_column(String(32), index=True)
    skill_slug: Mapped[str] = mapped_column(String(64), index=True)
    score: Mapped[int] = mapped_column(Integer)
    rationale: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class AssessmentSkillEvidenceRecord(Base):
    """Stored evidence item for one skill result."""

    __tablename__ = "assessment_skill_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    assessment_id: Mapped[str] = mapped_column(String(32), index=True)
    skill_slug: Mapped[str] = mapped_column(String(64), index=True)
    quote: Mapped[str] = mapped_column(Text)
    explanation: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ProgressionSnapshotRecord(Base):
    """Persisted learner progression snapshot."""

    __tablename__ = "progression_snapshots"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    learner_id: Mapped[str] = mapped_column(String(32), index=True)
    source_assessment_id: Mapped[str] = mapped_column(String(32), index=True)
    trace_id: Mapped[str] = mapped_column(String(32), index=True)
    workflow_id: Mapped[str] = mapped_column(String(64), index=True)
    engine_version: Mapped[str] = mapped_column(String(64))
    schema_version: Mapped[str] = mapped_column(String(64))
    config_version: Mapped[str] = mapped_column(String(64), index=True)
    evidence_ledger_schema_version: Mapped[str] = mapped_column(String(64))
    previous_snapshot_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    snapshot_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class RecommendationArtifactRecord(Base):
    """Persisted recommendation artifact."""

    __tablename__ = "recommendation_artifacts"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    learner_id: Mapped[str] = mapped_column(String(32), index=True)
    progress_snapshot_id: Mapped[str] = mapped_column(String(32), index=True)
    trace_id: Mapped[str] = mapped_column(String(32), index=True)
    workflow_id: Mapped[str] = mapped_column(String(64), index=True)
    engine_version: Mapped[str] = mapped_column(String(64))
    schema_version: Mapped[str] = mapped_column(String(64))
    config_version: Mapped[str] = mapped_column(String(64), index=True)
    context_snapshot_id: Mapped[str] = mapped_column(String(64), index=True)
    candidate_count: Mapped[int]
    artifact_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class AssistantSessionRecord(Base):
    """Durable assistant chat session state."""

    __tablename__ = "assistant_sessions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(32), index=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    metadata_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class AssistantTurnRecord(Base):
    """Durable assistant turn execution state."""

    __tablename__ = "assistant_turns"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(32), index=True)
    user_id: Mapped[str] = mapped_column(String(32), index=True)
    request_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    workflow_id: Mapped[str] = mapped_column(String(64), index=True)
    pipeline_run_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    stream_token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_message_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    assistant_message_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    last_error_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    cancel_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    tool_call_count: Mapped[int] = mapped_column(Integer, default=0)
    metadata_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AssistantMessageRecord(Base):
    """Durable assistant conversation message."""

    __tablename__ = "assistant_messages"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(32), index=True)
    turn_id: Mapped[str] = mapped_column(String(32), index=True)
    user_id: Mapped[str] = mapped_column(String(32), index=True)
    role: Mapped[str] = mapped_column(String(32), index=True)
    content: Mapped[str] = mapped_column(Text)
    metadata_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class AssistantToolCallRecord(Base):
    """Durable assistant tool call lifecycle."""

    __tablename__ = "assistant_tool_calls"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(32), index=True)
    turn_id: Mapped[str] = mapped_column(String(32), index=True)
    user_id: Mapped[str] = mapped_column(String(32), index=True)
    tool_name: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    args_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    result_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    child_run_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AssistantApprovalRequestRecord(Base):
    """Durable assistant human-approval request lifecycle."""

    __tablename__ = "assistant_approval_requests"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(32), index=True)
    turn_id: Mapped[str] = mapped_column(String(32), index=True)
    tool_call_id: Mapped[str] = mapped_column(String(32), index=True)
    user_id: Mapped[str] = mapped_column(String(32), index=True)
    tool_name: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    approval_message: Mapped[str] = mapped_column(Text)
    payload_summary: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_by_user_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AssistantStreamEventRecord(Base):
    """Durable ordered assistant stream event."""

    __tablename__ = "assistant_stream_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    session_id: Mapped[str] = mapped_column(String(32), index=True)
    turn_id: Mapped[str] = mapped_column(String(32), index=True)
    user_id: Mapped[str] = mapped_column(String(32), index=True)
    sequence_number: Mapped[int] = mapped_column(Integer)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    emitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ProgressRecalculationRecord(Base):
    """Replay and recalculation audit run."""

    __tablename__ = "progress_recalculations"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    learner_id: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    reason: Mapped[str] = mapped_column(Text)
    trace_id: Mapped[str] = mapped_column(String(32), index=True)
    workflow_id: Mapped[str] = mapped_column(String(64), index=True)
    config_version: Mapped[str] = mapped_column(String(64), index=True)
    previous_snapshot_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    next_snapshot_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    next_recommendation_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    diff_summary: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class EvaluationSuiteRecord(Base):
    """Registered evaluation suite metadata."""

    __tablename__ = "evaluation_suites"

    suite_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    suite_type: Mapped[str] = mapped_column(String(64), index=True)
    suite_version: Mapped[str] = mapped_column(String(128))
    benchmark_set_version: Mapped[str | None] = mapped_column(String(128), nullable=True)
    description: Mapped[str] = mapped_column(Text)
    requires_learner_id: Mapped[bool]
    definition_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class EvaluationRunRecord(Base):
    """Persisted evaluation execution."""

    __tablename__ = "evaluation_runs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    suite_id: Mapped[str] = mapped_column(String(128), index=True)
    suite_type: Mapped[str] = mapped_column(String(64), index=True)
    suite_version: Mapped[str] = mapped_column(String(128))
    benchmark_set_version: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    triggered_by_user_id: Mapped[str] = mapped_column(String(32), index=True)
    learner_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    workflow_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    pipeline_run_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    subject_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    subject_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    passed: Mapped[bool]
    aggregate_metrics: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    summary: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class EvaluationCaseResultRecord(Base):
    """Per-case evaluation result persistence."""

    __tablename__ = "evaluation_case_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    evaluation_run_id: Mapped[str] = mapped_column(String(32), index=True)
    case_id: Mapped[str] = mapped_column(String(128), index=True)
    case_label: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), index=True)
    error_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    detail_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ReleaseGateDecisionRecord(Base):
    """Persisted release decision linked to an evaluation run."""

    __tablename__ = "release_gate_decisions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    evaluation_run_id: Mapped[str] = mapped_column(String(32), index=True)
    decided_by_user_id: Mapped[str] = mapped_column(String(32), index=True)
    request_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    workflow_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    subject_type: Mapped[str] = mapped_column(String(64), index=True)
    subject_ref: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    summary: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class CircuitBreakerRecord(Base):
    """Persisted circuit breaker state for multi-worker deployments."""

    __tablename__ = "circuit_breakers"

    name: Mapped[str] = mapped_column(String(128), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    last_failure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class PipelineDefinitionRecord(Base):
    """Static pipeline DAG definition discovered at startup."""

    __tablename__ = "pipeline_definitions"

    pipeline_name: Mapped[str] = mapped_column(String(128), primary_key=True)
    topology: Mapped[str | None] = mapped_column(String(128), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    stage_definitions: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )


class StageDefinitionRecord(Base):
    """Individual stage metadata within a pipeline DAG."""

    __tablename__ = "stage_definitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pipeline_name: Mapped[str] = mapped_column(String(128), index=True)
    stage_name: Mapped[str] = mapped_column(String(128))
    stage_kind: Mapped[str] = mapped_column(String(32))
    dependencies: Mapped[list[str]] = mapped_column(JSON, default=list)
    runner_class: Mapped[str | None] = mapped_column(String(128), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_stage_definitions_pipeline_stage", "pipeline_name", "stage_name", unique=True),
    )


class PipelineExecutionTraceRecord(Base):
    """Actual pipeline execution trace for visualization replay."""

    __tablename__ = "pipeline_execution_traces"

    pipeline_run_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    pipeline_name: Mapped[str] = mapped_column(String(128), index=True)
    execution_sequence: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    total_duration_ms: Mapped[int]
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
