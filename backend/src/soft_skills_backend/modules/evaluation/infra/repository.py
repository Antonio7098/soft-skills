"""Evaluation repository facade."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from stageflow.core import StageContext

from soft_skills_backend.modules.evaluation.contracts.views import (
    BenchmarkDashboardView,
    EvalErrorBreakdownView,
    EvalLatencyPercentilesView,
    EvalPassFailRateView,
    EvaluationCaseDetailView,
    EvaluationCaseResultView,
    EvaluationComparisonPointView,
    EvaluationComparisonView,
    EvaluationDashboardView,
    EvaluationRunView,
    EvaluationSuiteView,
    ModelPerformanceView,
)
from soft_skills_backend.modules.evaluation.domain.evaluation import (
    BuiltinEvaluationSuite,
    EvaluationComputation,
    builtin_suites,
)
from soft_skills_backend.platform.db.models import (
    EvaluationCaseResultRecord,
    EvaluationRunRecord,
    EvaluationSuiteRecord,
)
from soft_skills_backend.platform.db.repositories import SqlAlchemyWorkflowEventRepository
from soft_skills_backend.platform.observability.events import WorkflowEventRecorder
from soft_skills_backend.platform.workflows.stageflow import (
    metadata_value,
    pipeline_run_id_from_context,
    request_id_from_context,
)
from soft_skills_backend.shared.auth import Actor
from soft_skills_backend.shared.errors import domain_error, persistence_error


def _utcnow() -> datetime:
    return datetime.now(UTC)


class EvaluationRepository:
    """Coordinate evaluation suite queries and persistence."""

    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        workflow_events: SqlAlchemyWorkflowEventRepository,
    ) -> None:
        self._session_factory = session_factory
        self._events = WorkflowEventRecorder(
            workflow_events, logger_name="soft_skills_backend.evaluation"
        )

    def sync_builtin_suites(self) -> None:
        now = _utcnow()
        expected_suite_ids = {suite.suite_id for suite in builtin_suites()}
        with self._session_factory() as session:
            for stale in (
                session.query(EvaluationSuiteRecord)
                .filter(~EvaluationSuiteRecord.suite_id.in_(expected_suite_ids))
                .all()
            ):
                session.delete(stale)
            for suite in builtin_suites():
                record = session.get(EvaluationSuiteRecord, suite.suite_id)
                payload = {
                    "suite_type": suite.suite_type.value,
                    "suite_version": suite.suite_version,
                    "benchmark_set_version": suite.benchmark_set_version,
                }
                if record is None:
                    session.add(
                        EvaluationSuiteRecord(
                            suite_id=suite.suite_id,
                            suite_type=suite.suite_type.value,
                            suite_version=suite.suite_version,
                            benchmark_set_version=suite.benchmark_set_version,
                            description=suite.description,
                            requires_learner_id=False,
                            definition_payload=payload,
                            created_at=now,
                            updated_at=now,
                        )
                    )
                else:
                    record.suite_type = suite.suite_type.value
                    record.suite_version = suite.suite_version
                    record.benchmark_set_version = suite.benchmark_set_version
                    record.description = suite.description
                    record.requires_learner_id = False
                    record.definition_payload = payload
                    record.updated_at = now
            session.commit()

    def list_suites(self) -> list[EvaluationSuiteView]:
        self.sync_builtin_suites()
        with self._session_factory() as session:
            records = (
                session.query(EvaluationSuiteRecord)
                .order_by(EvaluationSuiteRecord.suite_id.asc())
                .all()
            )
            return [
                EvaluationSuiteView(
                    suite_id=record.suite_id,
                    suite_type=record.suite_type,
                    suite_version=record.suite_version,
                    benchmark_set_version=record.benchmark_set_version,
                    description=record.description,
                    requires_learner_id=False,
                    definition_payload=dict(record.definition_payload),
                )
                for record in records
            ]

    def list_runs(self, *, limit: int = 20) -> list[EvaluationRunView]:
        with self._session_factory() as session:
            records = (
                session.query(EvaluationRunRecord)
                .order_by(EvaluationRunRecord.started_at.desc())
                .limit(limit)
                .all()
            )
            return [self._build_run_view(session, record) for record in records]

    def get_run(self, run_id: str) -> EvaluationRunView:
        with self._session_factory() as session:
            record = session.get(EvaluationRunRecord, run_id)
            if record is None:
                raise domain_error(
                    "Evaluation run was not found",
                    code="SS-DOMAIN-022",
                    status_code=404,
                    details={"evaluation_run_id": run_id},
                )
            return self._build_run_view(session, record)

    def persist_run(
        self,
        *,
        ctx: StageContext,
        actor: Actor,
        suite: BuiltinEvaluationSuite,
        computation: EvaluationComputation,
    ) -> EvaluationRunView:
        run_id = uuid4().hex
        started_at = _utcnow()
        try:
            with self._session_factory() as session:
                session.add(
                    EvaluationRunRecord(
                        id=run_id,
                        suite_id=suite.suite_id,
                        suite_type=suite.suite_type.value,
                        suite_version=suite.suite_version,
                        benchmark_set_version=suite.benchmark_set_version,
                        status="completed",
                        triggered_by_user_id=actor.user_id,
                        learner_id=None,
                        request_id=request_id_from_context(ctx),
                        trace_id=metadata_value(ctx, "trace_id"),
                        workflow_id=metadata_value(ctx, "workflow_id"),
                        pipeline_run_id=pipeline_run_id_from_context(ctx),
                        subject_type="golden_dataset",
                        subject_ref=suite.benchmark_set_version,
                        passed=computation.passed,
                        aggregate_metrics=computation.aggregate_metrics,
                        summary=computation.summary,
                        started_at=started_at,
                        completed_at=started_at,
                    )
                )
                session.flush()
                for case in computation.case_results:
                    session.add(
                        EvaluationCaseResultRecord(
                            evaluation_run_id=run_id,
                            case_id=case.case_id,
                            case_label=case.case_label,
                            status=case.status,
                            error_code=case.error_code,
                            metrics=case.metrics,
                            detail_payload=case.detail_payload,
                            created_at=started_at,
                        )
                    )
                session.commit()
        except SQLAlchemyError as exc:
            raise persistence_error(
                "Evaluation run could not be persisted",
                code="SS-PERSISTENCE-008",
                details={"suite_id": suite.suite_id},
            ) from exc
        self._events.record(
            event_type="evaluation.run.completed.v1",
            request_id=request_id_from_context(ctx),
            trace_id=metadata_value(ctx, "trace_id"),
            workflow_id=metadata_value(ctx, "workflow_id"),
            payload={
                "evaluation_run_id": run_id,
                "suite_id": suite.suite_id,
                "suite_type": suite.suite_type.value,
                "passed": computation.passed,
                "case_count": len(computation.case_results),
                "model_slugs": computation.summary.get("model_slugs", []),
                "dataset_version": computation.summary.get("dataset_version"),
            },
        )
        return EvaluationRunView(
            evaluation_run_id=run_id,
            suite_id=suite.suite_id,
            suite_type=suite.suite_type.value,
            suite_version=suite.suite_version,
            benchmark_set_version=suite.benchmark_set_version,
            status="completed",
            passed=computation.passed,
            triggered_by_user_id=actor.user_id,
            learner_id=None,
            trace_id=metadata_value(ctx, "trace_id"),
            workflow_id=metadata_value(ctx, "workflow_id"),
            pipeline_run_id=pipeline_run_id_from_context(ctx),
            subject_type="golden_dataset",
            subject_ref=suite.benchmark_set_version,
            aggregate_metrics=dict(computation.aggregate_metrics),
            summary=dict(computation.summary),
            started_at=started_at.isoformat(),
            completed_at=started_at.isoformat(),
            case_results=[
                EvaluationCaseResultView(
                    case_id=case.case_id,
                    case_label=case.case_label,
                    status=case.status,
                    error_code=case.error_code,
                    metrics=dict(case.metrics),
                    detail_payload=dict(case.detail_payload),
                )
                for case in computation.case_results
            ],
            release_decision=None,
        )

    def record_started(
        self,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str,
        suite_id: str,
        model_slugs: list[str],
        case_ids: list[str],
    ) -> None:
        self._events.record(
            event_type="evaluation.run.started.v1",
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id,
            payload={"suite_id": suite_id, "model_slugs": model_slugs, "case_ids": case_ids},
        )

    def record_failed(
        self,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str,
        suite_id: str,
        model_slugs: list[str],
        error_code: str,
        reason: str,
    ) -> None:
        self._events.record(
            event_type="evaluation.run.failed.v1",
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id,
            error_code=error_code,
            payload={"suite_id": suite_id, "model_slugs": model_slugs, "reason": reason},
        )

    def _build_run_view(self, session: Session, record: EvaluationRunRecord) -> EvaluationRunView:
        case_records = (
            session.query(EvaluationCaseResultRecord)
            .filter(EvaluationCaseResultRecord.evaluation_run_id == record.id)
            .order_by(EvaluationCaseResultRecord.id.asc())
            .all()
        )
        return EvaluationRunView(
            evaluation_run_id=record.id,
            suite_id=record.suite_id,
            suite_type=record.suite_type,
            suite_version=record.suite_version,
            benchmark_set_version=record.benchmark_set_version,
            status=record.status,
            passed=record.passed,
            triggered_by_user_id=record.triggered_by_user_id,
            learner_id=record.learner_id,
            trace_id=record.trace_id,
            workflow_id=record.workflow_id,
            pipeline_run_id=record.pipeline_run_id,
            subject_type=record.subject_type,
            subject_ref=record.subject_ref,
            aggregate_metrics=dict(record.aggregate_metrics),
            summary=dict(record.summary),
            started_at=record.started_at.isoformat(),
            completed_at=None if record.completed_at is None else record.completed_at.isoformat(),
            case_results=[
                EvaluationCaseResultView(
                    case_id=case.case_id,
                    case_label=case.case_label,
                    status=case.status,
                    error_code=case.error_code,
                    metrics=dict(case.metrics),
                    detail_payload=dict(case.detail_payload),
                )
                for case in case_records
            ],
            release_decision=None,
        )

    def get_dashboard(
        self, *, from_date: datetime | None = None, to_date: datetime | None = None
    ) -> EvaluationDashboardView:
        with self._session_factory() as session:
            query = session.query(EvaluationRunRecord)
            if from_date:
                query = query.filter(EvaluationRunRecord.started_at >= from_date)
            if to_date:
                query = query.filter(EvaluationRunRecord.started_at <= to_date)

            total_runs = query.count()
            passed_runs = query.filter(EvaluationRunRecord.passed).count()
            failed_runs = total_runs - passed_runs

            pass_fail = EvalPassFailRateView(
                total_runs=total_runs,
                passed_runs=passed_runs,
                failed_runs=failed_runs,
                pass_rate=round(passed_runs / max(1, total_runs), 4),
            )

            latency_values = [
                float(record.aggregate_metrics.get("average_latency_ms", 0))
                for record in query.all()
                if record.aggregate_metrics.get("average_latency_ms") is not None
            ]
            if latency_values:
                sorted_latencies = sorted(latency_values)
                p50_idx = int(len(sorted_latencies) * 0.50)
                p95_idx = int(len(sorted_latencies) * 0.95)
                p99_idx = int(len(sorted_latencies) * 0.99)
                latency_percentiles = EvalLatencyPercentilesView(
                    p50_ms=round(sorted_latencies[p50_idx], 2)
                    if p50_idx < len(sorted_latencies)
                    else None,
                    p95_ms=round(sorted_latencies[p95_idx], 2)
                    if p95_idx < len(sorted_latencies)
                    else None,
                    p99_ms=round(sorted_latencies[p99_idx], 2)
                    if p99_idx < len(sorted_latencies)
                    else None,
                    avg_ms=round(sum(latency_values) / len(latency_values), 2),
                )
            else:
                latency_percentiles = EvalLatencyPercentilesView()

            error_query = (
                session.query(
                    EvaluationCaseResultRecord.error_code,
                    func.count(EvaluationCaseResultRecord.id).label("count"),
                )
                .join(
                    EvaluationRunRecord,
                    EvaluationCaseResultRecord.evaluation_run_id == EvaluationRunRecord.id,
                )
                .filter(EvaluationCaseResultRecord.error_code.isnot(None))
            )
            if from_date:
                error_query = error_query.filter(EvaluationRunRecord.started_at >= from_date)
            if to_date:
                error_query = error_query.filter(EvaluationRunRecord.started_at <= to_date)

            error_records = error_query.group_by(EvaluationCaseResultRecord.error_code).all()
            total_errors = sum(int(row[1]) for row in error_records)
            error_breakdown = [
                EvalErrorBreakdownView(
                    error_code=row[0] or "unknown",
                    count=int(row[1]),
                    percentage=round(row[1] / max(1, total_errors), 4),
                )
                for row in error_records
            ]

            total_cases = session.query(func.count(EvaluationCaseResultRecord.id)).join(
                EvaluationRunRecord,
                EvaluationCaseResultRecord.evaluation_run_id == EvaluationRunRecord.id,
            )
            if from_date:
                total_cases = total_cases.filter(EvaluationRunRecord.started_at >= from_date)
            if to_date:
                total_cases = total_cases.filter(EvaluationRunRecord.started_at <= to_date)
            total_cases_count = total_cases.scalar() or 0

            total_tokens = sum(
                int(record.aggregate_metrics.get("total_tokens", 0)) for record in query.all()
            )

            suite_breakdown: dict[str, EvalPassFailRateView] = {}
            distinct_suites = query.with_entities(EvaluationRunRecord.suite_id).distinct().all()
            for suite_row in distinct_suites:
                suite_id_val = suite_row[0]
                suite_query = query.filter(EvaluationRunRecord.suite_id == suite_id_val)
                suite_total = suite_query.count()
                suite_passed = suite_query.filter(EvaluationRunRecord.passed).count()
                suite_breakdown[suite_id_val] = EvalPassFailRateView(
                    total_runs=suite_total,
                    passed_runs=suite_passed,
                    failed_runs=suite_total - suite_passed,
                    pass_rate=round(suite_passed / max(1, suite_total), 4),
                )

            from_date_str = from_date.isoformat() if from_date else None
            to_date_str = to_date.isoformat() if to_date else None

            return EvaluationDashboardView(
                total_runs=total_runs,
                pass_fail=pass_fail,
                latency_percentiles=latency_percentiles,
                error_breakdown=error_breakdown,
                total_cases=total_cases_count,
                total_tokens=total_tokens,
                estimated_cost_usd=None,
                suite_breakdown=suite_breakdown,
                from_date=from_date_str,
                to_date=to_date_str,
            )

    def compare_runs(
        self,
        *,
        run_ids: list[str] | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> EvaluationComparisonView:
        with self._session_factory() as session:
            query = session.query(EvaluationRunRecord)
            if run_ids:
                query = query.filter(EvaluationRunRecord.id.in_(run_ids))
            if from_date:
                query = query.filter(EvaluationRunRecord.started_at >= from_date)
            if to_date:
                query = query.filter(EvaluationRunRecord.started_at <= to_date)

            records = query.order_by(EvaluationRunRecord.started_at.desc()).limit(50).all()

            comparison_points: list[EvaluationComparisonPointView] = []
            total_cases = 0
            pass_rates: list[float] = []
            latencies: list[float] = []

            for record in records:
                metrics = dict(record.aggregate_metrics)
                pass_rate = metrics.get("pass_rate")
                avg_latency = metrics.get("average_latency_ms")
                model_slugs = record.summary.get("model_slugs", []) if record.summary else []

                comparison_points.append(
                    EvaluationComparisonPointView(
                        evaluation_run_id=record.id,
                        suite_id=record.suite_id,
                        suite_type=record.suite_type,
                        passed=record.passed,
                        pass_rate=float(pass_rate) if pass_rate is not None else None,
                        avg_latency_ms=float(avg_latency) if avg_latency is not None else None,
                        total_tokens=metrics.get("total_tokens", 0),
                        case_count=metrics.get("case_count", 0),
                        model_slugs=model_slugs,
                        started_at=record.started_at.isoformat(),
                    )
                )
                total_cases += metrics.get("case_count", 0)
                if pass_rate is not None:
                    pass_rates.append(float(pass_rate))
                if avg_latency is not None:
                    latencies.append(float(avg_latency))

            return EvaluationComparisonView(
                runs=comparison_points,
                run_count=len(comparison_points),
                total_cases=total_cases,
                avg_pass_rate=round(sum(pass_rates) / len(pass_rates), 4) if pass_rates else None,
                avg_latency_ms=round(sum(latencies) / len(latencies), 2) if latencies else None,
            )

    def get_benchmark_dashboard(
        self,
        *,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> BenchmarkDashboardView:
        with self._session_factory() as session:
            query = session.query(EvaluationRunRecord)
            if from_date:
                query = query.filter(EvaluationRunRecord.started_at >= from_date)
            if to_date:
                query = query.filter(EvaluationRunRecord.started_at <= to_date)

            records = query.all()
            total_runs = len(records)
            total_cases = 0

            model_performance: dict[str, ModelPerformanceView] = {}

            for record in records:
                metrics = dict(record.aggregate_metrics)
                model_slugs = record.summary.get("model_slugs", []) if record.summary else []
                total_cases += metrics.get("case_count", 0)

                for model_slug in model_slugs:
                    if model_slug not in model_performance:
                        model_performance[model_slug] = ModelPerformanceView(
                            model_slug=model_slug,
                            provider=None,
                            run_count=0,
                            passed_count=0,
                            failed_count=0,
                            pass_rate=None,
                            avg_latency_ms=None,
                            total_prompt_tokens=0,
                            total_completion_tokens=0,
                            total_tokens=0,
                            estimated_cost_usd=None,
                        )

                    perf = model_performance[model_slug]
                    perf.run_count += 1
                    if record.passed:
                        perf.passed_count += 1
                    else:
                        perf.failed_count += 1

                    perf.total_prompt_tokens += metrics.get("total_prompt_tokens", 0)
                    perf.total_completion_tokens += metrics.get("total_completion_tokens", 0)
                    perf.total_tokens += metrics.get("total_tokens", 0)

                    model_latency = metrics.get("average_latency_ms")
                    if model_latency is not None:
                        if perf.avg_latency_ms is None:
                            perf.avg_latency_ms = float(model_latency)
                        else:
                            perf.avg_latency_ms = (
                                perf.avg_latency_ms * (perf.run_count - 1) + float(model_latency)
                            ) / perf.run_count

            for _model_slug, perf in model_performance.items():
                if perf.run_count > 0:
                    perf.pass_rate = round(perf.passed_count / perf.run_count, 4)
                if perf.avg_latency_ms is not None:
                    perf.avg_latency_ms = round(perf.avg_latency_ms, 2)

            from_date_str = from_date.isoformat() if from_date else None
            to_date_str = to_date.isoformat() if to_date else None

            return BenchmarkDashboardView(
                models=list(model_performance.values()),
                total_runs=total_runs,
                total_cases=total_cases,
                from_date=from_date_str,
                to_date=to_date_str,
            )

    def get_case_detail(self, case_id: str) -> EvaluationCaseDetailView:
        with self._session_factory() as session:
            case_record = (
                session.query(EvaluationCaseResultRecord)
                .filter(EvaluationCaseResultRecord.case_id == case_id)
                .order_by(EvaluationCaseResultRecord.id.desc())
                .first()
            )
            if case_record is None:
                raise domain_error(
                    "Evaluation case was not found",
                    code="SS-DOMAIN-033",
                    status_code=404,
                    details={"case_id": case_id},
                )

            run_record = session.get(EvaluationRunRecord, case_record.evaluation_run_id)
            if run_record is None:
                raise domain_error(
                    "Evaluation run was not found",
                    code="SS-DOMAIN-022",
                    status_code=404,
                    details={"evaluation_run_id": case_record.evaluation_run_id},
                )

            return EvaluationCaseDetailView(
                case_id=case_record.case_id,
                case_label=case_record.case_label,
                status=case_record.status,
                error_code=case_record.error_code,
                suite_id=run_record.suite_id,
                suite_type=run_record.suite_type,
                suite_version=run_record.suite_version,
                evaluation_run_id=run_record.id,
                passed=run_record.passed,
                metrics=dict(case_record.metrics),
                detail_payload=dict(case_record.detail_payload),
                started_at=run_record.started_at.isoformat(),
                completed_at=None
                if run_record.completed_at is None
                else run_record.completed_at.isoformat(),
            )
