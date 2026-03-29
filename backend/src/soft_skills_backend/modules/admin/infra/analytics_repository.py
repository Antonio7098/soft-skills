"""Admin learner and cohort analytics queries."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

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
    TelemetryErrorBreakdownView,
    TelemetryLatencyBucketView,
    TelemetryOverviewView,
    TelemetryPipelineHealthView,
    TelemetryProviderMetricView,
    TelemetryTraceListView,
    TelemetryTraceView,
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
            thirty_days_ago = datetime.utcnow().replace(
                hour=0, minute=0, second=0, microsecond=0
            ) - timedelta(days=30)
            active_learner_ids: set[str] = set()
            for session_record in sessions:
                created_at = session_record.created_at
                if created_at.tzinfo is not None:
                    created_at = created_at.replace(tzinfo=None)
                if created_at >= thirty_days_ago:
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

    def get_telemetry_overview(
        self,
        organisation_id: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> TelemetryOverviewView:
        from soft_skills_backend.modules.admin.contracts.views import (
            TelemetryErrorBreakdownView,
            TelemetryLatencyBucketView,
            TelemetryOverviewView,
            TelemetryPipelineHealthView,
            TelemetryProviderMetricView,
        )

        with self._session_factory() as session:
            base_filter = self._build_date_filter(
                WorkflowEventRecord.occurred_at, from_date, to_date
            )
            provider_filter = self._build_date_filter(
                ProviderCallRecord.created_at, from_date, to_date
            )
            pipeline_filter = self._build_date_filter(
                PipelineRunRecord.started_at, from_date, to_date
            )

            provider_calls = session.query(ProviderCallRecord).filter(provider_filter).all()
            pipeline_runs = session.query(PipelineRunRecord).filter(pipeline_filter).all()
            workflow_events = session.query(WorkflowEventRecord).filter(base_filter).all()

            if organisation_id:
                trace_ids = self._organisation_trace_ids(session, organisation_id)
                provider_calls = [
                    c for c in provider_calls if c.trace_id and c.trace_id in trace_ids
                ]
                pipeline_runs = [p for p in pipeline_runs if p.trace_id and p.trace_id in trace_ids]
                workflow_events = [
                    e
                    for e in workflow_events
                    if e.organisation_id == organisation_id
                    or (e.trace_id and e.trace_id in trace_ids)
                ]

            total_provider_calls = len(provider_calls)
            total_pipeline_runs = len(pipeline_runs)
            total_workflow_events = len(workflow_events)

            success_calls = [c for c in provider_calls if c.success]
            success_pipeline = [p for p in pipeline_runs if p.status == "completed"]

            provider_call_success_rate = (
                round(len(success_calls) / total_provider_calls * 100, 2)
                if total_provider_calls > 0
                else None
            )
            pipeline_success_rate = (
                round(len(success_pipeline) / total_pipeline_runs * 100, 2)
                if total_pipeline_runs > 0
                else None
            )

            all_latencies = [c.latency_ms for c in provider_calls if c.latency_ms is not None]
            avg_provider_latency = (
                round(sum(all_latencies) / len(all_latencies), 2) if all_latencies else None
            )

            total_errors = len([e for e in workflow_events if e.error_code])
            error_rate = (
                round(total_errors / total_workflow_events * 100, 2)
                if total_workflow_events > 0
                else None
            )

            provider_metrics = self._build_provider_metrics(provider_calls)
            pipeline_health = self._build_pipeline_health(pipeline_runs)
            error_breakdown = self._build_error_breakdown(workflow_events)
            latency_distribution = self._build_latency_distribution(provider_calls)

            return TelemetryOverviewView(
                organisation_id=organisation_id,
                from_date=from_date.isoformat() if from_date else None,
                to_date=to_date.isoformat() if to_date else None,
                total_provider_calls=total_provider_calls,
                provider_call_success_rate=provider_call_success_rate,
                avg_provider_latency_ms=avg_provider_latency,
                total_pipeline_runs=total_pipeline_runs,
                pipeline_success_rate=pipeline_success_rate,
                total_workflow_events=total_workflow_events,
                total_errors=total_errors,
                error_rate=error_rate,
                provider_metrics=provider_metrics,
                pipeline_health=pipeline_health,
                error_breakdown=error_breakdown,
                latency_distribution=latency_distribution,
            )

    def list_telemetry_traces(
        self,
        organisation_id: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> TelemetryTraceListView:
        from soft_skills_backend.modules.admin.contracts.views import (
            TelemetryTraceListItemView,
            TelemetryTraceListView,
        )

        with self._session_factory() as session:
            if organisation_id:
                trace_ids = self._organisation_trace_ids(session, organisation_id)
                events_query = session.query(WorkflowEventRecord).filter(
                    WorkflowEventRecord.trace_id.in_(trace_ids)
                )
            else:
                events_query = session.query(WorkflowEventRecord)

            if from_date:
                events_query = events_query.filter(WorkflowEventRecord.occurred_at >= from_date)
            if to_date:
                events_query = events_query.filter(WorkflowEventRecord.occurred_at <= to_date)

            total = events_query.count()
            events = (
                events_query.order_by(WorkflowEventRecord.occurred_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            trace_ids_set = {e.trace_id for e in events if e.trace_id}
            pipeline_runs = (
                session.query(PipelineRunRecord)
                .filter(PipelineRunRecord.trace_id.in_(trace_ids_set))
                .all()
            )
            provider_calls = (
                session.query(ProviderCallRecord)
                .filter(ProviderCallRecord.trace_id.in_(trace_ids_set))
                .all()
            )

            pipeline_by_trace = {p.trace_id: p for p in pipeline_runs if p.trace_id}
            trace_spans: dict[str, int] = {tid: 0 for tid in trace_ids_set}
            for pc in provider_calls:
                if pc.trace_id:
                    trace_spans[pc.trace_id] = trace_spans.get(pc.trace_id, 0) + 1

            traces: list[TelemetryTraceListItemView] = []
            for event in events:
                if not event.trace_id:
                    continue
                pipeline_run = pipeline_by_trace.get(event.trace_id)
                duration = None
                if pipeline_run and pipeline_run.started_at and pipeline_run.finished_at:
                    duration = int(
                        (pipeline_run.finished_at - pipeline_run.started_at).total_seconds() * 1000
                    )

                traces.append(
                    TelemetryTraceListItemView(
                        trace_id=event.trace_id,
                        organisation_id=event.organisation_id,
                        operation_name=pipeline_run.pipeline_name if pipeline_run else None,
                        service_name=None,
                        duration_ms=duration,
                        started_at=pipeline_run.started_at.isoformat()
                        if pipeline_run and pipeline_run.started_at
                        else None,
                        error_count=1 if event.error_code else 0,
                        span_count=trace_spans.get(event.trace_id, 0),
                    )
                )

            unique_traces = {t.trace_id: t for t in traces}.values()
            trace_list = sorted(unique_traces, key=lambda x: x.started_at or "", reverse=True)

            return TelemetryTraceListView(
                traces=list(trace_list)[offset : offset + limit],
                total=len(trace_list),
                offset=offset,
                limit=limit,
            )

    def get_telemetry_trace(self, trace_id: str) -> TelemetryTraceView | None:
        from soft_skills_backend.modules.admin.contracts.views import (
            TelemetryTraceSpanView,
            TelemetryTraceView,
        )

        with self._session_factory() as session:
            pipeline_runs = (
                session.query(PipelineRunRecord)
                .filter(PipelineRunRecord.trace_id == trace_id)
                .all()
            )
            provider_calls = (
                session.query(ProviderCallRecord)
                .filter(ProviderCallRecord.trace_id == trace_id)
                .all()
            )
            workflow_events = (
                session.query(WorkflowEventRecord)
                .filter(WorkflowEventRecord.trace_id == trace_id)
                .all()
            )

            if not pipeline_runs and not provider_calls and not workflow_events:
                return None

            spans: list[TelemetryTraceSpanView] = []
            error_count = 0
            started_at: datetime | None = None
            completed_at: datetime | None = None

            for pr in pipeline_runs:
                if pr.started_at:
                    started_at = (
                        pr.started_at if started_at is None else min(started_at, pr.started_at)
                    )
                if pr.finished_at:
                    completed_at = (
                        pr.finished_at
                        if completed_at is None
                        else max(completed_at, pr.finished_at)
                    )
                if pr.error:
                    error_count += 1
                spans.append(
                    TelemetryTraceSpanView(
                        span_id=pr.pipeline_run_id,
                        operation_name=f"pipeline.{pr.pipeline_name}",
                        service_name="stageflow",
                        start_time=pr.started_at.isoformat() if pr.started_at else None,
                        end_time=pr.finished_at.isoformat() if pr.finished_at else None,
                        duration_ms=int((pr.finished_at - pr.started_at).total_seconds() * 1000)
                        if pr.started_at and pr.finished_at
                        else None,
                        status_code=pr.status,
                        error=pr.error,
                    )
                )

            for pc in provider_calls:
                if pc.created_at:
                    started_at = (
                        pc.created_at if started_at is None else min(started_at, pc.created_at)
                    )
                if not pc.success and pc.error:
                    error_count += 1
                spans.append(
                    TelemetryTraceSpanView(
                        span_id=pc.call_id,
                        operation_name=f"provider.{pc.operation}",
                        service_name=pc.provider,
                        start_time=pc.created_at.isoformat() if pc.created_at else None,
                        duration_ms=pc.latency_ms,
                        status_code="ok" if pc.success else "error",
                        error=pc.error if not pc.success else None,
                    )
                )

            for we in workflow_events:
                if we.occurred_at:
                    started_at = (
                        we.occurred_at if started_at is None else min(started_at, we.occurred_at)
                    )
                if we.error_code:
                    error_count += 1

            total_duration_ms = None
            if started_at and completed_at:
                total_duration_ms = int((completed_at - started_at).total_seconds() * 1000)

            workflow_event = workflow_events[0] if workflow_events else None

            return TelemetryTraceView(
                trace_id=trace_id,
                organisation_id=workflow_event.organisation_id if workflow_event else None,
                spans=spans,
                total_duration_ms=total_duration_ms,
                started_at=started_at.isoformat() if started_at else None,
                completed_at=completed_at.isoformat() if completed_at else None,
                error_count=error_count,
                span_count=len(spans),
            )

    def _build_provider_metrics(
        self, provider_calls: list[ProviderCallRecord]
    ) -> list[TelemetryProviderMetricView]:
        from soft_skills_backend.modules.admin.contracts.views import TelemetryProviderMetricView

        by_provider_model: dict[tuple[str, str | None, str], list[ProviderCallRecord]] = {}
        for pc in provider_calls:
            key = (pc.provider, pc.model_id, pc.operation)
            by_provider_model.setdefault(key, []).append(pc)

        metrics: list[TelemetryProviderMetricView] = []
        for (provider, model_id, operation), records in by_provider_model.items():
            latencies = [r.latency_ms for r in records if r.latency_ms is not None]
            sorted_latencies = sorted(latencies) if latencies else []
            p50_idx = len(sorted_latencies) // 2
            p95_idx = int(len(sorted_latencies) * 0.95)
            p99_idx = int(len(sorted_latencies) * 0.99)

            success_count = sum(1 for r in records if r.success)
            metrics.append(
                TelemetryProviderMetricView(
                    provider=provider,
                    model_slug=model_id,
                    operation=operation,
                    call_count=len(records),
                    success_count=success_count,
                    failure_count=len(records) - success_count,
                    success_rate=round(success_count / len(records) * 100, 2) if records else None,
                    avg_latency_ms=round(sum(latencies) / len(latencies), 2) if latencies else None,
                    p50_latency_ms=sorted_latencies[p50_idx] if sorted_latencies else None,
                    p95_latency_ms=sorted_latencies[p95_idx] if sorted_latencies else None,
                    p99_latency_ms=sorted_latencies[p99_idx] if sorted_latencies else None,
                    total_tokens=sum(
                        r.metrics.get("prompt_tokens", 0) + r.metrics.get("completion_tokens", 0)
                        for r in records
                    ),
                )
            )
        return metrics

    def _build_pipeline_health(
        self, pipeline_runs: list[PipelineRunRecord]
    ) -> list[TelemetryPipelineHealthView]:
        from soft_skills_backend.modules.admin.contracts.views import TelemetryPipelineHealthView

        by_pipeline: dict[str, list[PipelineRunRecord]] = {}
        for pr in pipeline_runs:
            by_pipeline.setdefault(pr.pipeline_name, []).append(pr)

        health: list[TelemetryPipelineHealthView] = []
        for pipeline_name, records in by_pipeline.items():
            success_count = sum(1 for r in records if r.status == "completed")
            durations = [
                int((r.finished_at - r.started_at).total_seconds() * 1000)
                for r in records
                if r.started_at and r.finished_at
            ]
            last_run = max((r.started_at for r in records if r.started_at), default=None)

            health.append(
                TelemetryPipelineHealthView(
                    pipeline_name=pipeline_name,
                    total_runs=len(records),
                    success_count=success_count,
                    failure_count=len(records) - success_count,
                    cancel_count=sum(1 for r in records if r.status == "cancelled"),
                    success_rate=round(success_count / len(records) * 100, 2) if records else None,
                    avg_duration_ms=round(sum(durations) / len(durations), 2)
                    if durations
                    else None,
                    error_rate=round((len(records) - success_count) / len(records) * 100, 2)
                    if records
                    else None,
                    last_run_at=last_run.isoformat() if last_run else None,
                )
            )
        return health

    def _build_error_breakdown(
        self, workflow_events: list[WorkflowEventRecord]
    ) -> list[TelemetryErrorBreakdownView]:
        from soft_skills_backend.modules.admin.contracts.views import TelemetryErrorBreakdownView

        error_events = [e for e in workflow_events if e.error_code or e.payload.get("error")]
        if not error_events:
            return []

        by_code: dict[str, list[WorkflowEventRecord]] = {}
        for e in error_events:
            code = e.error_code or e.payload.get("error_type", "unknown") or "unknown"
            by_code.setdefault(code, []).append(e)

        total = len(error_events)
        breakdown: list[TelemetryErrorBreakdownView] = []
        for code, events in by_code.items():
            examples = [
                str(e.payload.get("error", e.payload.get("root_cause", "")))[:100]
                for e in events[:3]
            ]
            breakdown.append(
                TelemetryErrorBreakdownView(
                    error_code=code,
                    error_type=events[0].payload.get("error_type", code) if events else code,
                    count=len(events),
                    percentage=round(len(events) / total * 100, 2) if total else 0.0,
                    examples=examples,
                )
            )
        return sorted(breakdown, key=lambda x: x.count, reverse=True)

    def _build_latency_distribution(
        self, provider_calls: list[ProviderCallRecord]
    ) -> list[TelemetryLatencyBucketView]:
        from soft_skills_backend.modules.admin.contracts.views import TelemetryLatencyBucketView

        buckets = [50, 100, 200, 500, 1000, 2000, 5000, 10000]
        latencies = sorted([c.latency_ms for c in provider_calls if c.latency_ms is not None])
        if not latencies:
            return []

        total = len(latencies)
        distribution: list[TelemetryLatencyBucketView] = []
        bucket_idx = 0

        for latency in latencies:
            while bucket_idx < len(buckets) - 1 and latency > buckets[bucket_idx]:
                bucket_idx += 1
            bucket_val = buckets[bucket_idx] if bucket_idx < len(buckets) else buckets[-1] * 2
            distribution.append(
                TelemetryLatencyBucketView(bucket_ms=bucket_val, count=1, percentage=0.0)
            )

        bucket_counts: dict[int, int] = {}
        for d in distribution:
            bucket_counts[d.bucket_ms] = bucket_counts.get(d.bucket_ms, 0) + 1

        return [
            TelemetryLatencyBucketView(
                bucket_ms=ms,
                count=count,
                percentage=round(count / total * 100, 2),
            )
            for ms, count in sorted(bucket_counts.items())
        ]

    def _build_date_filter(
        self, column: Any, from_date: datetime | None, to_date: datetime | None
    ) -> Any:
        from sqlalchemy import and_

        filters = []
        if from_date:
            filters.append(column >= from_date)
        if to_date:
            filters.append(column <= to_date)
        return and_(*filters) if filters else True

    def _organisation_trace_ids(self, session: Session, organisation_id: str) -> set[str]:
        learner_ids = [
            m.user_id
            for m in session.query(OrganisationMembershipRecord)
            .filter(OrganisationMembershipRecord.organisation_id == organisation_id)
            .all()
        ]

        traces: set[str] = set()
        for record in session.query(PipelineRunRecord).all():
            if record.user_id and record.user_id in learner_ids and record.trace_id:
                traces.add(record.trace_id)
            if record.trace_id:
                traces.add(record.trace_id)

        for record in session.query(ProviderCallRecord).all():
            if record.trace_id:
                traces.add(record.trace_id)

        return traces
