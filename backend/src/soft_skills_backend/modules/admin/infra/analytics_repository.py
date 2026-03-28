"""Admin learner and cohort analytics queries."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.modules.admin.contracts.views import (
    AdminAttemptSummaryView,
    AnalyticsOverviewView,
    CohortAnalyticsView,
    CohortComparisonView,
    LearnerAnalyticsView,
    ProviderUsageView,
    SkillAverageView,
    SkillClusterView,
    UsageSummaryView,
    UsageTrendPointView,
)
from soft_skills_backend.modules.admin.domain.analytics import (
    build_average_skill_scores,
    build_provider_summary,
    build_skill_clusters,
    build_usage_trend_points,
)
from soft_skills_backend.platform.db.models import (
    AssessmentRecord,
    AttemptRecord,
    LearnerProfileRecord,
    OrganisationMembershipRecord,
    PipelineRunRecord,
    PracticeSessionRecord,
    ProgressionSnapshotRecord,
    ProviderCallRecord,
    RecommendationArtifactRecord,
    WorkflowEventRecord,
)
from soft_skills_backend.shared.errors import domain_error


class AdminAnalyticsRepository:
    """Read learner and cohort analytics from durable artifacts."""

    def __init__(self, *, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def get_learner_analytics(
        self,
        learner_id: str,
        organisation_id: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> LearnerAnalyticsView:
        with self._session_factory() as session:
            learner = session.get(LearnerProfileRecord, learner_id)
            if learner is None:
                raise domain_error(
                    "Learner analytics target was not found",
                    code="SS-DOMAIN-030",
                    status_code=404,
                    details={"learner_id": learner_id},
                )
            if organisation_id is not None:
                membership = (
                    session.query(OrganisationMembershipRecord)
                    .filter(
                        OrganisationMembershipRecord.user_id == learner_id,
                        OrganisationMembershipRecord.organisation_id == organisation_id,
                    )
                    .first()
                )
                if membership is None:
                    raise domain_error(
                        "Learner is not in your organisation",
                        code="SS-AUTH-004",
                        status_code=403,
                        details={"learner_id": learner_id, "organisation_id": organisation_id},
                    )
            sessions = self._sessions(session, [learner_id], from_date=from_date, to_date=to_date)
            attempts = self._attempts(session, [learner_id], from_date=from_date, to_date=to_date)
            assessments = self._assessments(
                session, [learner_id], from_date=from_date, to_date=to_date
            )
            latest_snapshots = self._latest_snapshots(session, [learner_id])
            latest_recommendations = self._latest_recommendations(session, [learner_id])
            traces, workflows = self._lineage_keys(
                sessions=sessions,
                attempts=attempts,
                snapshots=list(latest_snapshots.values()),
                recommendations=list(latest_recommendations.values()),
            )
            workflow_events = self._workflow_events(session, traces, workflows)
            pipeline_runs = self._pipeline_runs(session, learner_ids=[learner_id], trace_ids=traces)
            provider_calls = self._provider_calls(
                session,
                trace_ids=traces,
                pipeline_run_ids=[record.pipeline_run_id for record in pipeline_runs],
            )
            latest_snapshot = latest_snapshots.get(learner_id)
            latest_recommendation = latest_recommendations.get(learner_id)
            assessment_by_id = {record.id: record for record in assessments}
            usage = self._usage_summary(
                sessions=sessions,
                attempts=attempts,
                assessments=assessments,
                workflow_events=workflow_events,
                pipeline_runs=pipeline_runs,
                provider_calls=provider_calls,
            )
            trend_points = build_usage_trend_points(
                session_timestamps=[record.created_at for record in sessions],
                submitted_attempt_timestamps=[
                    record.submitted_at for record in attempts if record.submitted_at is not None
                ],
                validated_assessment_timestamps=[
                    record.created_at
                    for record in assessments
                    if record.validation_status == "validated"
                ],
                rejected_assessment_timestamps=[
                    record.created_at
                    for record in assessments
                    if record.validation_status == "rejected"
                ],
            )
            return LearnerAnalyticsView(
                learner_id=learner_id,
                target_role=learner.target_role,
                latest_progress_snapshot_id=None if latest_snapshot is None else latest_snapshot.id,
                latest_recommendation_id=None
                if latest_recommendation is None
                else latest_recommendation.id,
                weak_skill_slugs=[]
                if latest_snapshot is None
                else list(latest_snapshot.snapshot_payload.get("weak_skill_slugs", [])),
                stagnating_skill_slugs=[]
                if latest_snapshot is None
                else list(latest_snapshot.snapshot_payload.get("stagnating_skill_slugs", [])),
                coverage_gap_skill_slugs=[]
                if latest_snapshot is None
                else list(latest_snapshot.snapshot_payload.get("coverage_gap_skill_slugs", [])),
                usage=usage,
                recent_attempts=[
                    self._attempt_summary(
                        record,
                        assessment_by_id.get(record.assessment_id)
                        if record.assessment_id
                        else None,
                    )
                    for record in attempts[:5]
                ],
                usage_trend=[UsageTrendPointView.model_validate(point) for point in trend_points],
                provider_summary=[
                    ProviderUsageView.model_validate(summary)
                    for summary in build_provider_summary(provider_calls)
                ],
            )

    def get_cohort_analytics(
        self,
        target_role: str | None,
        organisation_id: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> CohortAnalyticsView:
        with self._session_factory() as session:
            learner_ids = self._cohort_learner_ids(session, target_role, organisation_id)
            sessions = self._sessions(session, learner_ids, from_date=from_date, to_date=to_date)
            attempts = self._attempts(session, learner_ids, from_date=from_date, to_date=to_date)
            assessments = self._assessments(
                session, learner_ids, from_date=from_date, to_date=to_date
            )
            latest_snapshots = self._latest_snapshots(session, learner_ids)
            latest_recommendations = self._latest_recommendations(session, learner_ids)
            traces, workflows = self._lineage_keys(
                sessions=sessions,
                attempts=attempts,
                snapshots=list(latest_snapshots.values()),
                recommendations=list(latest_recommendations.values()),
            )
            workflow_events = self._workflow_events(session, traces, workflows)
            pipeline_runs = self._pipeline_runs(session, learner_ids=learner_ids, trace_ids=traces)
            provider_calls = self._provider_calls(
                session,
                trace_ids=traces,
                pipeline_run_ids=[record.pipeline_run_id for record in pipeline_runs],
            )
            usage = self._usage_summary(
                sessions=sessions,
                attempts=attempts,
                assessments=assessments,
                workflow_events=workflow_events,
                pipeline_runs=pipeline_runs,
                provider_calls=provider_calls,
            )
            trend_points = build_usage_trend_points(
                session_timestamps=[record.created_at for record in sessions],
                submitted_attempt_timestamps=[
                    record.submitted_at for record in attempts if record.submitted_at is not None
                ],
                validated_assessment_timestamps=[
                    record.created_at
                    for record in assessments
                    if record.validation_status == "validated"
                ],
                rejected_assessment_timestamps=[
                    record.created_at
                    for record in assessments
                    if record.validation_status == "rejected"
                ],
            )
            snapshot_payloads = [record.snapshot_payload for record in latest_snapshots.values()]
            return CohortAnalyticsView(
                cohort_key=target_role or "all",
                learner_count=len(learner_ids),
                usage=usage,
                weak_skill_clusters=[
                    SkillClusterView.model_validate(item)
                    for item in build_skill_clusters(
                        [list(payload.get("weak_skill_slugs", [])) for payload in snapshot_payloads]
                    )
                ],
                average_skill_scores=[
                    SkillAverageView.model_validate(item)
                    for item in build_average_skill_scores(snapshot_payloads)
                ],
                usage_trend=[UsageTrendPointView.model_validate(point) for point in trend_points],
                provider_summary=[
                    ProviderUsageView.model_validate(summary)
                    for summary in build_provider_summary(provider_calls)
                ],
            )

    def get_analytics_overview(
        self,
        organisation_id: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> AnalyticsOverviewView:
        with self._session_factory() as session:
            learner_ids = self._cohort_learner_ids(
                session, target_role=None, organisation_id=organisation_id
            )
            sessions = self._sessions(session, learner_ids, from_date=from_date, to_date=to_date)
            attempts = self._attempts(session, learner_ids, from_date=from_date, to_date=to_date)
            assessments = self._assessments(
                session, learner_ids, from_date=from_date, to_date=to_date
            )
            latest_snapshots = self._latest_snapshots(session, learner_ids)
            traces, workflows = self._lineage_keys(
                sessions=sessions,
                attempts=attempts,
                snapshots=list(latest_snapshots.values()),
                recommendations=[],
            )
            workflow_events = self._workflow_events(session, traces, workflows)
            pipeline_runs = self._pipeline_runs(session, learner_ids=learner_ids, trace_ids=traces)
            provider_calls = self._provider_calls(
                session,
                trace_ids=traces,
                pipeline_run_ids=[record.pipeline_run_id for record in pipeline_runs],
            )
            usage = self._usage_summary(
                sessions=sessions,
                attempts=attempts,
                assessments=assessments,
                workflow_events=workflow_events,
                pipeline_runs=pipeline_runs,
                provider_calls=provider_calls,
            )
            trend_points = build_usage_trend_points(
                session_timestamps=[record.created_at for record in sessions],
                submitted_attempt_timestamps=[
                    record.submitted_at for record in attempts if record.submitted_at is not None
                ],
                validated_assessment_timestamps=[
                    record.created_at
                    for record in assessments
                    if record.validation_status == "validated"
                ],
                rejected_assessment_timestamps=[
                    record.created_at
                    for record in assessments
                    if record.validation_status == "rejected"
                ],
            )
            snapshot_payloads = [record.snapshot_payload for record in latest_snapshots.values()]
            thirty_days_ago = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
            thirty_days_ago = thirty_days_ago.replace(
                day=thirty_days_ago.day - 30 if thirty_days_ago.day > 30 else 1
            )
            active_learner_ids: set[str] = set()
            for session_record in sessions:
                if session_record.created_at >= thirty_days_ago:
                    active_learner_ids.add(session_record.user_id)
            target_role_counts: dict[str, int] = {}
            for learner_id in learner_ids:
                profile = session.get(LearnerProfileRecord, learner_id)
                if profile and profile.target_role:
                    target_role_counts[profile.target_role] = (
                        target_role_counts.get(profile.target_role, 0) + 1
                    )
            cohort_breakdown: list[dict[str, int | str]] = [
                {"cohort_key": role, "learner_count": count}
                for role, count in sorted(target_role_counts.items(), key=lambda x: -x[1])
            ]
            return AnalyticsOverviewView(
                total_learners=len(learner_ids),
                active_learners_30d=len(active_learner_ids),
                total_sessions=usage.total_sessions,
                total_attempts=usage.total_attempts,
                submitted_attempts=usage.submitted_attempts,
                validated_assessments=usage.validated_assessments,
                rejected_assessments=usage.rejected_assessments,
                avg_validated_score=usage.avg_validated_score,
                overall_usage_trend=[
                    UsageTrendPointView.model_validate(point) for point in trend_points
                ],
                top_weak_skills=[
                    SkillClusterView.model_validate(item)
                    for item in build_skill_clusters(
                        [list(payload.get("weak_skill_slugs", [])) for payload in snapshot_payloads]
                    )[:5]
                ],
                cohort_breakdown=cohort_breakdown,
                provider_summary=[
                    ProviderUsageView.model_validate(summary)
                    for summary in build_provider_summary(provider_calls)
                ],
            )

    def get_cohort_comparison(
        self,
        cohort_keys: list[str],
        organisation_id: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> CohortComparisonView:
        cohorts = []
        for target_role in cohort_keys:
            cohort_view = self.get_cohort_analytics(
                target_role=target_role,
                organisation_id=organisation_id,
                from_date=from_date,
                to_date=to_date,
            )
            cohorts.append(cohort_view)
        return CohortComparisonView(
            cohorts=cohorts,
            comparison_timestamp=datetime.now(UTC).isoformat(),
        )

    def _cohort_learner_ids(
        self, session: Session, target_role: str | None, organisation_id: str | None = None
    ) -> list[str]:
        query = session.query(LearnerProfileRecord)
        if target_role is not None:
            query = query.filter(LearnerProfileRecord.target_role == target_role)
        profiles = query.all()
        learner_ids = [profile.user_id for profile in profiles]
        if organisation_id is not None:
            memberships = (
                session.query(OrganisationMembershipRecord.user_id)
                .filter(
                    OrganisationMembershipRecord.organisation_id == organisation_id,
                    OrganisationMembershipRecord.user_id.in_(learner_ids),
                )
                .all()
            )
            org_member_ids = {m.user_id for m in memberships}
            learner_ids = [lid for lid in learner_ids if lid in org_member_ids]
        return sorted(learner_ids)

    def _sessions(
        self,
        session: Session,
        learner_ids: list[str],
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[PracticeSessionRecord]:
        if not learner_ids:
            return []
        query = session.query(PracticeSessionRecord).filter(
            PracticeSessionRecord.user_id.in_(learner_ids)
        )
        if from_date is not None:
            query = query.filter(PracticeSessionRecord.created_at >= from_date)
        if to_date is not None:
            query = query.filter(PracticeSessionRecord.created_at <= to_date)
        return query.order_by(PracticeSessionRecord.created_at.desc()).all()

    def _attempts(
        self,
        session: Session,
        learner_ids: list[str],
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[AttemptRecord]:
        if not learner_ids:
            return []
        query = session.query(AttemptRecord).filter(AttemptRecord.user_id.in_(learner_ids))
        if from_date is not None:
            query = query.filter(AttemptRecord.created_at >= from_date)
        if to_date is not None:
            query = query.filter(AttemptRecord.created_at <= to_date)
        return query.order_by(AttemptRecord.created_at.desc()).all()

    def _assessments(
        self,
        session: Session,
        learner_ids: list[str],
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[AssessmentRecord]:
        if not learner_ids:
            return []
        query = session.query(AssessmentRecord).filter(AssessmentRecord.user_id.in_(learner_ids))
        if from_date is not None:
            query = query.filter(AssessmentRecord.created_at >= from_date)
        if to_date is not None:
            query = query.filter(AssessmentRecord.created_at <= to_date)
        return query.order_by(AssessmentRecord.created_at.desc()).all()

    def _latest_snapshots(
        self,
        session: Session,
        learner_ids: list[str],
    ) -> dict[str, ProgressionSnapshotRecord]:
        if not learner_ids:
            return {}
        records = (
            session.query(ProgressionSnapshotRecord)
            .filter(ProgressionSnapshotRecord.learner_id.in_(learner_ids))
            .order_by(ProgressionSnapshotRecord.created_at.desc())
            .all()
        )
        latest: dict[str, ProgressionSnapshotRecord] = {}
        for record in records:
            latest.setdefault(record.learner_id, record)
        return latest

    def _latest_recommendations(
        self,
        session: Session,
        learner_ids: list[str],
    ) -> dict[str, RecommendationArtifactRecord]:
        if not learner_ids:
            return {}
        records = (
            session.query(RecommendationArtifactRecord)
            .filter(RecommendationArtifactRecord.learner_id.in_(learner_ids))
            .order_by(RecommendationArtifactRecord.created_at.desc())
            .all()
        )
        latest: dict[str, RecommendationArtifactRecord] = {}
        for record in records:
            latest.setdefault(record.learner_id, record)
        return latest

    def _lineage_keys(
        self,
        *,
        sessions: list[PracticeSessionRecord],
        attempts: list[AttemptRecord],
        snapshots: list[ProgressionSnapshotRecord],
        recommendations: list[RecommendationArtifactRecord],
    ) -> tuple[set[str], set[str]]:
        trace_ids = {
            value
            for value in [
                *(attempt.trace_id for attempt in attempts),
                *(snapshot.trace_id for snapshot in snapshots),
                *(recommendation.trace_id for recommendation in recommendations),
            ]
            if value
        }
        workflow_ids = {
            value
            for value in [
                *(session.workflow_id for session in sessions),
                *(attempt.workflow_id for attempt in attempts),
                *(snapshot.workflow_id for snapshot in snapshots),
                *(recommendation.workflow_id for recommendation in recommendations),
            ]
            if value
        }
        return trace_ids, workflow_ids

    def _workflow_events(
        self,
        session: Session,
        trace_ids: set[str],
        workflow_ids: set[str],
    ) -> list[WorkflowEventRecord]:
        records = session.query(WorkflowEventRecord).all()
        return [
            record
            for record in records
            if (record.trace_id and record.trace_id in trace_ids)
            or (record.workflow_id and record.workflow_id in workflow_ids)
        ]

    def _pipeline_runs(
        self,
        session: Session,
        *,
        learner_ids: list[str],
        trace_ids: set[str],
    ) -> list[PipelineRunRecord]:
        records = session.query(PipelineRunRecord).all()
        learner_id_set = set(learner_ids)
        return [
            record
            for record in records
            if (record.user_id and record.user_id in learner_id_set)
            or (record.trace_id and record.trace_id in trace_ids)
        ]

    def _provider_calls(
        self,
        session: Session,
        *,
        trace_ids: set[str],
        pipeline_run_ids: list[str],
    ) -> list[ProviderCallRecord]:
        records = session.query(ProviderCallRecord).all()
        pipeline_run_id_set = set(pipeline_run_ids)
        return [
            record
            for record in records
            if (record.trace_id and record.trace_id in trace_ids)
            or (record.pipeline_run_id and record.pipeline_run_id in pipeline_run_id_set)
        ]

    def _usage_summary(
        self,
        *,
        sessions: list[PracticeSessionRecord],
        attempts: list[AttemptRecord],
        assessments: list[AssessmentRecord],
        workflow_events: list[WorkflowEventRecord],
        pipeline_runs: list[PipelineRunRecord],
        provider_calls: list[ProviderCallRecord],
    ) -> UsageSummaryView:
        validated_scores = [
            record.overall_score
            for record in assessments
            if record.validation_status == "validated" and record.overall_score is not None
        ]
        last_activity_candidates: list[datetime] = [record.created_at for record in sessions]
        last_activity_candidates.extend(record.created_at for record in attempts)
        last_activity_candidates.extend(
            record.submitted_at for record in attempts if record.submitted_at is not None
        )
        last_activity_candidates.extend(
            record.assessed_at for record in attempts if record.assessed_at is not None
        )
        last_activity_candidates.extend(record.created_at for record in assessments)
        last_activity_at = (
            None if not last_activity_candidates else max(last_activity_candidates).isoformat()
        )
        return UsageSummaryView(
            total_sessions=len(sessions),
            total_attempts=len(attempts),
            submitted_attempts=sum(1 for record in attempts if record.submitted_at is not None),
            assessed_attempts=sum(1 for record in attempts if record.status == "assessed"),
            validated_assessments=sum(
                1 for record in assessments if record.validation_status == "validated"
            ),
            rejected_assessments=sum(
                1 for record in assessments if record.validation_status == "rejected"
            ),
            workflow_event_count=len(workflow_events),
            pipeline_run_count=len(pipeline_runs),
            provider_call_count=len(provider_calls),
            avg_validated_score=None
            if not validated_scores
            else round(sum(validated_scores) / len(validated_scores), 2),
            last_activity_at=last_activity_at,
        )

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
