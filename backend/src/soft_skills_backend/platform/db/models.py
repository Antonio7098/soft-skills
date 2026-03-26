"""Persistence models for foundational observability artifacts."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Integer, String, Text
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
    source_type: Mapped[str] = mapped_column(String(32), index=True, default="manual")
    last_generation_artifact_id: Mapped[str | None] = mapped_column(
        String(32), index=True, nullable=True
    )
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
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


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


class PracticeSessionRecord(Base):
    """Durable practice session state."""

    __tablename__ = "practice_sessions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(32), index=True)
    practice_type: Mapped[str] = mapped_column(String(32), index=True)
    content_item_id: Mapped[str] = mapped_column(String(32), index=True)
    content_item_type: Mapped[str] = mapped_column(String(32))
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
