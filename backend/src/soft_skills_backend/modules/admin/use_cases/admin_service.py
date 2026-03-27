"""Admin application facade."""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.modules.admin.contracts.commands import (
    AdminCollectionVerificationCommand,
    AdminFeatureCollectionCommand,
    AdminLearnerRelationshipCommand,
    CreateRubricCommand,
    CreateRubricCriterionCommand,
    RubricCriterionUpdateCommand,
    UpdateRubricCommand,
)
from soft_skills_backend.modules.admin.contracts.views import (
    AdminLearnerRelationshipView,
    AttemptAuditView,
    CohortAnalyticsView,
    CollectionVerificationAuditView,
    CollectionVerificationQueueItemView,
    LearnerAnalyticsView,
    PipelineDAGView,
    PipelineDefinitionView,
    PipelineMetricsView,
    PipelineRunSummaryView,
    PipelineTraceView,
    RubricView,
    StageDefinitionView,
    StageExecutionEventView,
    StageMetricsView,
)
from soft_skills_backend.modules.admin.infra.analytics_repository import AdminAnalyticsRepository
from soft_skills_backend.modules.admin.infra.audit_repository import AdminAuditRepository
from soft_skills_backend.modules.admin.infra.relationship_repository import (
    AdminRelationshipRepository,
)
from soft_skills_backend.modules.admin.infra.rubric_admin_repository import RubricAdminRepository
from soft_skills_backend.modules.admin.infra.verification_repository import (
    AdminVerificationRepository,
)
from soft_skills_backend.modules.catalog.contracts.collection_views import CollectionView
from soft_skills_backend.modules.catalog.contracts.views import build_collection_view
from soft_skills_backend.platform.db.models import CollectionRecord
from soft_skills_backend.platform.db.repositories import (
    SqlAlchemyPipelineDefinitionRepository,
    SqlAlchemyPipelineExecutionTraceRepository,
    SqlAlchemyPipelineRunRepository,
    SqlAlchemyStageDefinitionRepository,
    SqlAlchemyWorkflowEventRepository,
)
from soft_skills_backend.shared.auth import Actor


class AdminService:
    """Feature facade for admin-only verification, analytics, and audit APIs."""

    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        workflow_events: SqlAlchemyWorkflowEventRepository,
        pipeline_definitions: SqlAlchemyPipelineDefinitionRepository | None = None,
        stage_definitions: SqlAlchemyStageDefinitionRepository | None = None,
        pipeline_execution_traces: SqlAlchemyPipelineExecutionTraceRepository | None = None,
        pipeline_runs: SqlAlchemyPipelineRunRepository | None = None,
    ) -> None:
        relationships = AdminRelationshipRepository(session_factory=session_factory)
        self._verification = AdminVerificationRepository(
            session_factory=session_factory,
            workflow_events=workflow_events,
        )
        self._analytics = AdminAnalyticsRepository(session_factory=session_factory)
        self._relationships = relationships
        self._audit = AdminAuditRepository(
            session_factory=session_factory,
            relationships=relationships,
        )
        self._rubrics = RubricAdminRepository(session_factory=session_factory)
        self._pipeline_definitions = pipeline_definitions
        self._stage_definitions = stage_definitions
        self._pipeline_execution_traces = pipeline_execution_traces
        self._pipeline_runs = pipeline_runs

    def list_collection_verification_queue(
        self, actor: Actor
    ) -> list[CollectionVerificationQueueItemView]:
        return self._verification.list_verification_queue(organisation_id=actor.organisation_id)

    def get_collection_verification(
        self,
        actor: Actor,
        collection_id: str,
    ) -> CollectionVerificationAuditView:
        return self._verification.get_collection_verification(
            collection_id, organisation_id=actor.organisation_id
        )

    def update_collection_verification(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        collection_id: str,
        command: AdminCollectionVerificationCommand,
    ) -> CollectionVerificationAuditView:
        return self._verification.update_verification(
            actor,
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id,
            collection_id=collection_id,
            command=command,
        )

    def get_learner_analytics(self, actor: Actor, learner_id: str) -> LearnerAnalyticsView:
        return self._analytics.get_learner_analytics(
            learner_id, organisation_id=actor.organisation_id
        )

    def get_cohort_analytics(self, actor: Actor, target_role: str | None) -> CohortAnalyticsView:
        return self._analytics.get_cohort_analytics(
            target_role, organisation_id=actor.organisation_id
        )

    def get_attempt_audit(self, actor: Actor, attempt_id: str) -> AttemptAuditView:
        return self._audit.get_attempt_audit(actor, attempt_id)

    def get_learner_relationship(
        self,
        actor: Actor,
        learner_id: str,
    ) -> AdminLearnerRelationshipView | None:
        return self._relationships.get_relationship(
            admin_user_id=actor.user_id,
            learner_user_id=learner_id,
        )

    def upsert_learner_relationship(
        self,
        actor: Actor,
        *,
        learner_id: str,
        command: AdminLearnerRelationshipCommand,
    ) -> AdminLearnerRelationshipView:
        return self._relationships.upsert_relationship(
            actor,
            learner_user_id=learner_id,
            command=command,
        )

    def delete_learner_relationship(self, actor: Actor, *, learner_id: str) -> None:
        self._relationships.delete_relationship(actor, learner_user_id=learner_id)

    def feature_collection(
        self,
        actor: Actor,
        collection_id: str,
        command: AdminFeatureCollectionCommand,
    ) -> CollectionView:
        with self._verification._session_factory() as session:
            record = session.get(CollectionRecord, collection_id)
            if record is None:
                from soft_skills_backend.shared.errors import domain_error

                raise domain_error(
                    "Collection was not found",
                    code="SS-DOMAIN-005",
                    status_code=404,
                    details={"collection_id": collection_id},
                )
            if record.organisation_id != actor.organisation_id:
                from soft_skills_backend.shared.errors import auth_error

                raise auth_error(
                    "Collection does not belong to this organisation",
                    code="SS-AUTH-008",
                    status_code=403,
                    details={"collection_id": collection_id},
                )
            record.featured = command.featured
            session.commit()
            return build_collection_view(session, record, actor=actor)

    def list_rubrics(self, actor: Actor) -> list[RubricView]:
        return self._rubrics.list_rubrics()

    def get_rubric(self, actor: Actor, rubric_id: str) -> RubricView:
        return self._rubrics.get_rubric(rubric_id)

    def create_rubric(self, actor: Actor, command: CreateRubricCommand) -> RubricView:
        return self._rubrics.create_rubric(command)

    def update_rubric(
        self, actor: Actor, rubric_id: str, command: UpdateRubricCommand
    ) -> RubricView:
        return self._rubrics.update_rubric(rubric_id, command)

    def delete_rubric(self, actor: Actor, rubric_id: str) -> None:
        self._rubrics.delete_rubric(rubric_id)

    def create_rubric_criterion(
        self, actor: Actor, rubric_id: str, command: CreateRubricCriterionCommand
    ) -> RubricView:
        return self._rubrics.create_criterion(rubric_id, command)

    def update_rubric_criterion(
        self,
        actor: Actor,
        rubric_id: str,
        criterion_ref: str,
        command: RubricCriterionUpdateCommand,
    ) -> RubricView:
        return self._rubrics.update_criterion(rubric_id, criterion_ref, command)

    def delete_rubric_criterion(
        self, actor: Actor, rubric_id: str, criterion_ref: str
    ) -> RubricView:
        return self._rubrics.delete_criterion(rubric_id, criterion_ref)

    def list_pipelines(self, actor: Actor) -> list[PipelineDefinitionView]:
        """List all registered pipeline definitions."""
        if self._pipeline_definitions is None:
            return []
        records = self._pipeline_definitions.list_all()
        return [
            PipelineDefinitionView(
                pipeline_name=r.pipeline_name,
                topology=r.topology,
                description=r.description,
                stage_count=len(r.stage_definitions),
                created_at=r.created_at.isoformat() if r.created_at else None,
                updated_at=r.updated_at.isoformat() if r.updated_at else None,
            )
            for r in records
        ]

    def get_pipeline_dag(self, actor: Actor, pipeline_name: str) -> PipelineDAGView | None:
        """Get full pipeline DAG with stages and dependencies."""
        if self._pipeline_definitions is None or self._stage_definitions is None:
            return None
        definition = self._pipeline_definitions.get_by_name(pipeline_name)
        if definition is None:
            return None
        stage_records = self._stage_definitions.get_by_pipeline(pipeline_name)
        stages = [
            StageDefinitionView(
                name=s.stage_name,
                kind=s.stage_kind,
                dependencies=s.dependencies,
                runner_class=s.runner_class,
                description=s.description,
            )
            for s in stage_records
        ]
        return PipelineDAGView(
            pipeline_name=definition.pipeline_name,
            topology=definition.topology,
            description=definition.description,
            stages=stages,
        )

    def list_pipeline_runs(
        self, actor: Actor, pipeline_name: str, *, offset: int = 0, limit: int = 50
    ) -> list[PipelineRunSummaryView]:
        """List recent runs for a pipeline."""
        if self._pipeline_execution_traces is None or self._pipeline_runs is None:
            return []
        trace_records = self._pipeline_execution_traces.get_by_pipeline(
            pipeline_name, offset=offset, limit=limit
        )
        run_records = self._pipeline_runs.list_by_pipeline(
            pipeline_name, offset=offset, limit=limit
        )
        run_map = {r.pipeline_run_id: r for r in run_records}
        result = []
        for trace in trace_records:
            run = run_map.get(trace.pipeline_run_id)
            result.append(
                PipelineRunSummaryView(
                    pipeline_run_id=trace.pipeline_run_id,
                    pipeline_name=trace.pipeline_name,
                    status=run.status if run else "unknown",
                    execution_mode=run.execution_mode if run else None,
                    user_id=run.user_id if run else None,
                    request_id=run.request_id if run else None,
                    trace_id=run.trace_id if run else None,
                    error=None,
                    failed_stage=run.failed_stage if run else None,
                    started_at=trace.started_at.isoformat() if trace.started_at else None,
                    finished_at=trace.completed_at.isoformat() if trace.completed_at else None,
                    duration_ms=trace.total_duration_ms,
                )
            )
        return result

    def get_pipeline_trace(
        self, actor: Actor, pipeline_name: str, pipeline_run_id: str
    ) -> PipelineTraceView | None:
        """Get execution trace for a specific pipeline run."""
        if self._pipeline_execution_traces is None:
            return None
        trace = self._pipeline_execution_traces.get_by_run_id(pipeline_run_id)
        if trace is None or trace.pipeline_name != pipeline_name:
            return None
        events = [
            StageExecutionEventView(
                stage_name=e.get("stage_name", ""),
                event_type=e.get("event_type", ""),
                timestamp=e.get("timestamp", ""),
                duration_ms=e.get("duration_ms"),
                status=e.get("status"),
                error=e.get("error"),
            )
            for e in trace.execution_sequence
        ]
        return PipelineTraceView(
            pipeline_run_id=trace.pipeline_run_id,
            pipeline_name=trace.pipeline_name,
            execution_sequence=events,
            total_duration_ms=trace.total_duration_ms,
            started_at=trace.started_at.isoformat() if trace.started_at else None,
            completed_at=trace.completed_at.isoformat() if trace.completed_at else None,
        )

    def get_pipeline_metrics(self, actor: Actor, pipeline_name: str) -> PipelineMetricsView | None:
        """Get aggregate stage metrics for a pipeline."""
        if self._pipeline_execution_traces is None or self._pipeline_runs is None:
            return None
        runs = self._pipeline_runs.list_by_pipeline(pipeline_name, offset=0, limit=1000)
        if not runs:
            return PipelineMetricsView(pipeline_name=pipeline_name, total_runs=0)
        traces = self._pipeline_execution_traces.get_by_pipeline(
            pipeline_name, offset=0, limit=1000
        )
        traces_by_run_id = {t.pipeline_run_id: t for t in traces}
        success_count = sum(1 for r in runs if r.status == "completed")
        failure_count = sum(1 for r in runs if r.status == "failed")
        cancel_count = sum(1 for r in runs if r.status == "cancelled")

        invocation_counts: dict[str, int] = {}
        success_counts: dict[str, int] = {}
        failure_counts: dict[str, int] = {}
        skip_counts: dict[str, int] = {}
        cancel_counts: dict[str, int] = {}
        retry_counts: dict[str, int] = {}
        stage_durations: dict[str, list[int]] = {}

        for run in runs:
            trace = traces_by_run_id.get(run.pipeline_run_id)
            if trace is None:
                continue
            for event in trace.execution_sequence:
                stage_name = event.get("stage_name", "unknown")
                if stage_name not in invocation_counts:
                    invocation_counts[stage_name] = 0
                    success_counts[stage_name] = 0
                    failure_counts[stage_name] = 0
                    skip_counts[stage_name] = 0
                    cancel_counts[stage_name] = 0
                    retry_counts[stage_name] = 0
                    stage_durations[stage_name] = []
                invocation_counts[stage_name] += 1
                status = event.get("status", "unknown")
                if status == "completed":
                    success_counts[stage_name] += 1
                elif status == "failed":
                    failure_counts[stage_name] += 1
                elif status == "skipped":
                    skip_counts[stage_name] += 1
                elif status == "cancelled":
                    cancel_counts[stage_name] += 1
                duration = event.get("duration_ms")
                if duration is not None:
                    stage_durations[stage_name].append(duration)

        stage_metrics_views = []
        for stage_name in invocation_counts:
            durations = sorted(stage_durations.get(stage_name, []))
            p50_idx = len(durations) // 2
            p95_idx = int(len(durations) * 0.95)
            p99_idx = int(len(durations) * 0.99)
            avg_duration = sum(durations) / len(durations) if durations else None
            stage_metrics_views.append(
                StageMetricsView(
                    stage_name=stage_name,
                    invocation_count=invocation_counts[stage_name],
                    success_count=success_counts[stage_name],
                    failure_count=failure_counts[stage_name],
                    skip_count=skip_counts[stage_name],
                    cancel_count=cancel_counts[stage_name],
                    retry_count=retry_counts[stage_name],
                    avg_duration_ms=avg_duration,
                    p50_duration_ms=durations[p50_idx] if durations else None,
                    p95_duration_ms=durations[p95_idx] if durations else None,
                    p99_duration_ms=durations[p99_idx] if durations else None,
                )
            )
        return PipelineMetricsView(
            pipeline_name=pipeline_name,
            total_runs=len(runs),
            success_count=success_count,
            failure_count=failure_count,
            cancel_count=cancel_count,
            stage_metrics=stage_metrics_views,
        )
