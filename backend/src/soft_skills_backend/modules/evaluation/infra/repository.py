"""Evaluation repository facade."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from stageflow.core import StageContext

from soft_skills_backend.modules.evaluation.contracts.views import (
    EvaluationCaseResultView,
    EvaluationRunView,
    EvaluationSuiteView,
)
from soft_skills_backend.modules.evaluation.domain.evaluation import (
    BuiltinEvaluationSuite,
    EvaluationComputation,
    builtin_suites,
)
from soft_skills_backend.modules.evaluation.infra.events import EvaluationEventRecorder
from soft_skills_backend.platform.db.models import (
    EvaluationCaseResultRecord,
    EvaluationRunRecord,
    EvaluationSuiteRecord,
)
from soft_skills_backend.platform.db.repositories import SqlAlchemyWorkflowEventRepository
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
        self._events = EvaluationEventRecorder(workflow_events)

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
