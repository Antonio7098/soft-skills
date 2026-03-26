"""Admin attempt audit queries."""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.modules.admin.contracts.views import (
    AdminAssessmentAuditView,
    AdminAssessmentSkillScoreView,
    AdminLearnerRelationshipView,
    AdminAttemptSummaryView,
    AdminPromptAuditView,
    AttemptAuditView,
    PipelineRunAuditView,
    ProviderCallAuditView,
    WorkflowEventAuditView,
)
from soft_skills_backend.modules.admin.infra.relationship_repository import (
    AdminRelationshipRepository,
)
from soft_skills_backend.modules.practice.workflows.assessment.models import PracticePromptView
from soft_skills_backend.platform.db.models import (
    AssessmentRecord,
    AttemptRecord,
    PipelineRunRecord,
    PracticeSessionRecord,
    ProgressionSnapshotRecord,
    ProviderCallRecord,
    RecommendationArtifactRecord,
    WorkflowEventRecord,
)
from soft_skills_backend.shared.auth import Actor
from soft_skills_backend.shared.errors import domain_error


class AdminAuditRepository:
    """Expose redacted audit and replay surfaces."""

    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        relationships: AdminRelationshipRepository,
    ) -> None:
        self._session_factory = session_factory
        self._relationships = relationships

    def get_attempt_audit(self, actor: Actor, attempt_id: str) -> AttemptAuditView:
        with self._session_factory() as session:
            attempt = session.get(AttemptRecord, attempt_id)
            if attempt is None:
                raise domain_error(
                    "Attempt was not found",
                    code="SS-DOMAIN-010",
                    status_code=404,
                    details={"attempt_id": attempt_id},
                )
            practice_session = session.get(PracticeSessionRecord, attempt.session_id)
            if practice_session is None:
                raise domain_error(
                    "Practice session was not found",
                    code="SS-DOMAIN-013",
                    status_code=404,
                    details={"session_id": attempt.session_id},
                )
            assessment = (
                None if attempt.assessment_id is None else session.get(AssessmentRecord, attempt.assessment_id)
            )
            latest_snapshot = (
                session.query(ProgressionSnapshotRecord)
                .filter(ProgressionSnapshotRecord.learner_id == attempt.user_id)
                .order_by(ProgressionSnapshotRecord.created_at.desc())
                .first()
            )
            latest_recommendation = (
                session.query(RecommendationArtifactRecord)
                .filter(RecommendationArtifactRecord.learner_id == attempt.user_id)
                .order_by(RecommendationArtifactRecord.created_at.desc())
                .first()
            )
            relationship = self._relationships.get_relationship(
                admin_user_id=actor.user_id,
                learner_user_id=attempt.user_id,
            )
            prompt = PracticePromptView.model_validate(practice_session.prompt_payload)
            workflow_events = self._workflow_events(
                session,
                attempt=attempt,
                assessment=assessment,
            )
            pipeline_runs = self._pipeline_runs(session, attempt=attempt, assessment=assessment)
            provider_calls = self._provider_calls(
                session,
                attempt=attempt,
                assessment=assessment,
                pipeline_run_ids=[run.pipeline_run_id for run in pipeline_runs],
            )
            return AttemptAuditView(
                attempt=self._attempt_summary(attempt, assessment),
                response_visibility=self._response_visibility(relationship),
                access_relationship=relationship,
                prompt=AdminPromptAuditView(
                    title=prompt.title,
                    content_item_id=prompt.content_item_id,
                    content_item_type=prompt.content_item_type,
                    prompt_type=prompt.prompt_type,
                    difficulty=prompt.difficulty,
                    delivery_version=prompt.delivery_version,
                    rubric_id=prompt.rubric_id,
                    rubric_version=prompt.rubric_version,
                    target_skill_slugs=list(prompt.target_skill_slugs),
                ),
                response_text=attempt.response_text if relationship is not None else None,
                assessment=None
                if assessment is None
                else self._assessment_audit(assessment, relationship),
                latest_progress_snapshot_id=None
                if latest_snapshot is None
                else latest_snapshot.id,
                latest_recommendation_id=None
                if latest_recommendation is None
                else latest_recommendation.id,
                workflow_events=workflow_events,
                pipeline_runs=pipeline_runs,
                provider_calls=provider_calls,
            )

    def _workflow_events(
        self,
        session: Session,
        *,
        attempt: AttemptRecord,
        assessment: AssessmentRecord | None,
    ) -> list[WorkflowEventAuditView]:
        records = session.query(WorkflowEventRecord).order_by(WorkflowEventRecord.occurred_at.desc()).all()
        results: list[WorkflowEventAuditView] = []
        for record in records:
            payload = record.payload or {}
            if not self._matches_attempt(
                trace_id=attempt.trace_id,
                workflow_id=attempt.workflow_id,
                attempt_id=attempt.id,
                assessment_id=None if assessment is None else assessment.id,
                record_trace_id=record.trace_id,
                record_workflow_id=record.workflow_id,
                payload=payload,
            ):
                continue
            results.append(
                WorkflowEventAuditView(
                    event_id=record.event_id,
                    event_type=record.event_type,
                    request_id=record.request_id,
                    trace_id=record.trace_id,
                    workflow_id=record.workflow_id,
                    error_code=record.error_code,
                    payload=dict(payload),
                    occurred_at=record.occurred_at.isoformat(),
                )
            )
        return results

    def _pipeline_runs(
        self,
        session: Session,
        *,
        attempt: AttemptRecord,
        assessment: AssessmentRecord | None,
    ) -> list[PipelineRunAuditView]:
        records = session.query(PipelineRunRecord).order_by(PipelineRunRecord.started_at.desc()).all()
        results: list[PipelineRunAuditView] = []
        for record in records:
            if (
                (attempt.trace_id and record.trace_id == attempt.trace_id)
                or (assessment is not None and record.pipeline_run_id == assessment.pipeline_run_id)
            ):
                results.append(
                    PipelineRunAuditView(
                        pipeline_run_id=record.pipeline_run_id,
                        pipeline_name=record.pipeline_name,
                        status=record.status,
                        topology=record.topology,
                        execution_mode=record.execution_mode,
                        request_id=record.request_id,
                        trace_id=record.trace_id,
                        user_id=record.user_id,
                        failed_stage=record.failed_stage,
                        error=record.error,
                        stage_results=dict(record.stage_results),
                        started_at=record.started_at.isoformat(),
                        finished_at=None
                        if record.finished_at is None
                        else record.finished_at.isoformat(),
                    )
                )
        return results

    def _provider_calls(
        self,
        session: Session,
        *,
        attempt: AttemptRecord,
        assessment: AssessmentRecord | None,
        pipeline_run_ids: list[str],
    ) -> list[ProviderCallAuditView]:
        records = session.query(ProviderCallRecord).order_by(ProviderCallRecord.created_at.desc()).all()
        results: list[ProviderCallAuditView] = []
        for record in records:
            if not (
                (attempt.trace_id and record.trace_id == attempt.trace_id)
                or (record.pipeline_run_id is not None and record.pipeline_run_id in pipeline_run_ids)
                or (assessment is not None and record.pipeline_run_id == assessment.pipeline_run_id)
            ):
                continue
            results.append(
                ProviderCallAuditView(
                    call_id=record.call_id,
                    operation=record.operation,
                    provider=record.provider,
                    model_slug=record.model_id,
                    success=record.success,
                    latency_ms=record.latency_ms,
                    error=record.error,
                    pipeline_run_id=record.pipeline_run_id,
                    request_id=record.request_id,
                    trace_id=record.trace_id,
                    metrics=dict(record.metrics),
                    created_at=record.created_at.isoformat(),
                )
            )
        return results

    def _attempt_summary(
        self,
        attempt: AttemptRecord,
        assessment: AssessmentRecord | None,
    ) -> AdminAttemptSummaryView:
        return AdminAttemptSummaryView(
            attempt_id=attempt.id,
            learner_id=attempt.user_id,
            session_id=attempt.session_id,
            workflow_id=attempt.workflow_id,
            practice_type=attempt.practice_type,
            content_item_id=attempt.content_item_id,
            content_item_type=attempt.content_item_type,
            status=attempt.status,
            assessment_id=None if assessment is None else assessment.id,
            validation_status=None if assessment is None else assessment.validation_status,
            overall_score=None if assessment is None else assessment.overall_score,
            trace_id=attempt.trace_id,
            pipeline_run_id=None if assessment is None else assessment.pipeline_run_id,
            submitted_at=None if attempt.submitted_at is None else attempt.submitted_at.isoformat(),
            assessed_at=None if attempt.assessed_at is None else attempt.assessed_at.isoformat(),
            created_at=attempt.created_at.isoformat(),
        )

    def _assessment_audit(
        self,
        assessment: AssessmentRecord,
        relationship: AdminLearnerRelationshipView | None = None,
    ) -> AdminAssessmentAuditView:
        return AdminAssessmentAuditView(
            assessment_id=assessment.id,
            validation_status=assessment.validation_status,
            prompt_version=assessment.prompt_version,
            rubric_id=assessment.rubric_id,
            rubric_version=assessment.rubric_version,
            schema_version=assessment.schema_version,
            config_version=assessment.config_version,
            provider=assessment.provider,
            model_slug=assessment.model_slug,
            overall_score=assessment.overall_score,
            rejection_code=assessment.rejection_code,
            trace_id=assessment.trace_id,
            pipeline_run_id=assessment.pipeline_run_id,
            evidence_count=len(assessment.evidence),
            strengths_count=len(assessment.strengths),
            weaknesses_count=len(assessment.weaknesses),
            next_actions_count=len(assessment.next_actions),
            evidence_quotes=[]
            if relationship is None
            else [str(item["quote"]) for item in assessment.evidence if item.get("quote")],
            strengths=[] if relationship is None else list(assessment.strengths),
            weaknesses=[] if relationship is None else list(assessment.weaknesses),
            next_actions=[] if relationship is None else list(assessment.next_actions),
            skill_scores=[
                AdminAssessmentSkillScoreView(
                    skill_slug=str(item["skill_slug"]),
                    score=int(item["score"]),
                    rationale=str(item["rationale"]),
                )
                for item in assessment.skill_scores
            ],
            created_at=assessment.created_at.isoformat(),
        )

    def _response_visibility(
        self,
        relationship: AdminLearnerRelationshipView | None,
    ) -> str:
        if relationship is None:
            return "redacted_without_relationship_mapping"
        return f"full_via_{relationship.relationship_type}_relationship"

    def _matches_attempt(
        self,
        *,
        trace_id: str | None,
        workflow_id: str,
        attempt_id: str,
        assessment_id: str | None,
        record_trace_id: str | None,
        record_workflow_id: str | None,
        payload: dict[str, object],
    ) -> bool:
        return bool(
            (trace_id and record_trace_id == trace_id)
            or record_workflow_id == workflow_id
            or payload.get("attempt_id") == attempt_id
            or (assessment_id is not None and payload.get("assessment_id") == assessment_id)
        )
