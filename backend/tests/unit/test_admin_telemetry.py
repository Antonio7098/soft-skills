"""Unit tests for admin service telemetry methods."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from soft_skills_backend.modules.admin.use_cases.admin_service import AdminService
from soft_skills_backend.shared.auth import Actor


class TestAdminServiceTelemetryMethods:
    """Tests for AdminService telemetry methods."""

    @pytest.fixture
    def actor(self) -> Actor:
        return Actor(
            user_id="test-user-id",
            email="test@example.com",
            organisation_id="test-org-id",
            organisation_role="admin",
        )

    def test_get_telemetry_overview_requires_organisation_id(
        self,
        actor: Actor,
    ) -> None:
        """get_telemetry_overview should raise error when no organisation_id and actor has none."""
        actor_no_org = Actor(
            user_id="test-user-id",
            email="test@example.com",
            organisation_id=None,
            organisation_role="admin",
        )
        service = AdminService(
            session_factory=MagicMock(),
            workflow_events=MagicMock(),
        )

        from soft_skills_backend.shared.errors import AppError

        with pytest.raises(AppError) as exc_info:
            service.get_telemetry_overview(actor_no_org)

        assert exc_info.value.code == "SS-ADMIN-050"

    def test_list_telemetry_traces_requires_organisation_id(
        self,
        actor: Actor,
    ) -> None:
        """list_telemetry_traces should raise error when no organisation_id and actor has none."""
        actor_no_org = Actor(
            user_id="test-user-id",
            email="test@example.com",
            organisation_id=None,
            organisation_role="admin",
        )
        service = AdminService(
            session_factory=MagicMock(),
            workflow_events=MagicMock(),
        )

        from soft_skills_backend.shared.errors import AppError

        with pytest.raises(AppError) as exc_info:
            service.list_telemetry_traces(actor_no_org)

        assert exc_info.value.code == "SS-ADMIN-051"

    def test_get_telemetry_trace_requires_organisation_id(
        self,
        actor: Actor,
    ) -> None:
        """get_telemetry_trace should raise error when no organisation_id and actor has none."""
        actor_no_org = Actor(
            user_id="test-user-id",
            email="test@example.com",
            organisation_id=None,
            organisation_role="admin",
        )
        service = AdminService(
            session_factory=MagicMock(),
            workflow_events=MagicMock(),
        )

        from soft_skills_backend.shared.errors import AppError

        with pytest.raises(AppError) as exc_info:
            service.get_telemetry_trace(actor_no_org, "trace-123")

        assert exc_info.value.code == "SS-ADMIN-052"


def _make_mock_provider_call(
    call_id: str,
    provider: str,
    model_id: str,
    operation: str,
    success: bool,
    latency_ms: float,
    trace_id: str,
    created_at: datetime,
) -> MagicMock:
    mock = MagicMock()
    mock.call_id = call_id
    mock.provider = provider
    mock.model_id = model_id
    mock.operation = operation
    mock.success = success
    mock.latency_ms = latency_ms
    mock.trace_id = trace_id
    mock.created_at = created_at
    mock.metrics = {}
    return mock


def _make_mock_workflow_event(
    event_id: str,
    event_type: str,
    trace_id: str,
    error_code: str | None,
    organisation_id: str,
    occurred_at: datetime,
) -> MagicMock:
    mock = MagicMock()
    mock.event_id = event_id
    mock.event_type = event_type
    mock.trace_id = trace_id
    mock.workflow_id = None
    mock.error_code = error_code
    mock.organisation_id = organisation_id
    mock.payload = {}
    mock.occurred_at = occurred_at
    return mock


def _make_mock_pipeline_run(
    pipeline_run_id: str,
    pipeline_name: str,
    status: str,
    trace_id: str,
    started_at: datetime,
    finished_at: datetime,
) -> MagicMock:
    mock = MagicMock()
    mock.pipeline_run_id = pipeline_run_id
    mock.pipeline_name = pipeline_name
    mock.topology = "test"
    mock.status = status
    mock.request_id = "req-1"
    mock.trace_id = trace_id
    mock.user_id = "user-1"
    mock.error = None
    mock.failed_stage = None
    mock.stage_results = {}
    mock.started_at = started_at
    mock.finished_at = finished_at
    return mock


class TestTelemetryAnalyticsRepository:
    """Tests for AdminAnalyticsRepository telemetry methods."""

    @pytest.fixture
    def mock_session_factory(self) -> MagicMock:
        factory = MagicMock()
        session = MagicMock()
        factory.return_value.__enter__ = MagicMock(return_value=session)
        factory.return_value.__exit__ = MagicMock(return_value=False)
        return factory

    def test_get_telemetry_overview_returns_overview_with_metrics(
        self,
        mock_session_factory: MagicMock,
    ) -> None:
        """get_telemetry_overview should return telemetry overview with provider and pipeline metrics."""
        from soft_skills_backend.modules.admin.infra.analytics_repository import (
            AdminAnalyticsRepository,
        )

        session = mock_session_factory.return_value.__enter__()

        session.query.return_value.filter.return_value.all.return_value = []
        session.query.return_value.count.return_value = 0

        repo = AdminAnalyticsRepository(session_factory=mock_session_factory)
        result = repo.get_telemetry_overview(organisation_id=None)

        assert result.total_provider_calls == 0
        assert result.total_pipeline_runs == 0
        assert result.total_workflow_events == 0
        assert result.provider_metrics == []
        assert result.pipeline_health == []

    def test_get_telemetry_overview_filters_by_date_range(
        self,
        mock_session_factory: MagicMock,
    ) -> None:
        """get_telemetry_overview should filter by date range."""
        from soft_skills_backend.modules.admin.infra.analytics_repository import (
            AdminAnalyticsRepository,
        )

        session = mock_session_factory.return_value.__enter__()

        session.query.return_value.filter.return_value.all.return_value = []
        session.query.return_value.count.return_value = 0

        repo = AdminAnalyticsRepository(session_factory=mock_session_factory)
        from_date = datetime(2024, 1, 1, tzinfo=UTC)
        to_date = datetime(2024, 12, 31, tzinfo=UTC)

        result = repo.get_telemetry_overview(
            organisation_id="org-1",
            from_date=from_date,
            to_date=to_date,
        )

        assert result.total_provider_calls == 0
        assert result.total_pipeline_runs == 0
        assert result.total_workflow_events == 0

    def test_list_telemetry_traces_returns_paginated_list(
        self,
        mock_session_factory: MagicMock,
    ) -> None:
        """list_telemetry_traces should return paginated trace list."""
        from soft_skills_backend.modules.admin.infra.analytics_repository import (
            AdminAnalyticsRepository,
        )

        session = mock_session_factory.return_value.__enter__()
        now = datetime.now(UTC)

        workflow_event = _make_mock_workflow_event(
            event_id="evt-1",
            event_type="pipeline.started",
            trace_id="trace-1",
            error_code=None,
            organisation_id="org-1",
            occurred_at=now,
        )

        session.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            workflow_event
        ]
        session.query.return_value.filter.return_value.count.return_value = 1

        repo = AdminAnalyticsRepository(session_factory=mock_session_factory)
        result = repo.list_telemetry_traces(
            organisation_id="org-1",
            offset=0,
            limit=50,
        )

        assert result.offset == 0
        assert result.limit == 50

    def test_get_telemetry_trace_returns_none_when_not_found(
        self,
        mock_session_factory: MagicMock,
    ) -> None:
        """get_telemetry_trace should return None when trace does not exist."""
        from soft_skills_backend.modules.admin.infra.analytics_repository import (
            AdminAnalyticsRepository,
        )

        session = mock_session_factory.return_value.__enter__()
        session.query.return_value.filter.return_value.all.return_value = []

        repo = AdminAnalyticsRepository(session_factory=mock_session_factory)
        result = repo.get_telemetry_trace("nonexistent-trace")

        assert result is None

    def test_get_telemetry_trace_returns_trace_with_spans(
        self,
        mock_session_factory: MagicMock,
    ) -> None:
        """get_telemetry_trace should return trace with pipeline and provider spans."""
        from soft_skills_backend.modules.admin.infra.analytics_repository import (
            AdminAnalyticsRepository,
        )

        session = mock_session_factory.return_value.__enter__()
        now = datetime.now(UTC)

        pipeline_run = _make_mock_pipeline_run(
            pipeline_run_id="run-1",
            pipeline_name="test-pipeline",
            status="completed",
            trace_id="trace-1",
            started_at=now,
            finished_at=now,
        )

        session.query.return_value.filter.return_value.all.side_effect = [
            [pipeline_run],
            [],
            [],
        ]

        repo = AdminAnalyticsRepository(session_factory=mock_session_factory)
        result = repo.get_telemetry_trace("trace-1")

        assert result is not None
        assert result.trace_id == "trace-1"
        assert len(result.spans) == 1
        assert result.spans[0].operation_name == "pipeline.test-pipeline"

    def test_build_provider_metrics_calculates_percentiles(
        self,
        mock_session_factory: MagicMock,
    ) -> None:
        """_build_provider_metrics should calculate p50, p95, p99 latency."""
        from soft_skills_backend.modules.admin.infra.analytics_repository import (
            AdminAnalyticsRepository,
        )

        session = mock_session_factory.return_value.__enter__()

        session.query.return_value.filter.return_value.all.return_value = []
        session.query.return_value.count.return_value = 0

        repo = AdminAnalyticsRepository(session_factory=mock_session_factory)
        result = repo.get_telemetry_overview(organisation_id=None)

        assert result.total_provider_calls == 0
        assert result.provider_metrics == []
        assert result.pipeline_health == []

    def test_build_error_breakdown_groups_by_error_code(
        self,
        mock_session_factory: MagicMock,
    ) -> None:
        """_build_error_breakdown should group errors by error code."""
        from soft_skills_backend.modules.admin.infra.analytics_repository import (
            AdminAnalyticsRepository,
        )

        session = mock_session_factory.return_value.__enter__()
        now = datetime.now(UTC)

        workflow_events = []
        for i in range(10):
            evt = _make_mock_workflow_event(
                event_id=f"evt-{i}",
                event_type="pipeline.error",
                trace_id=f"trace-{i}",
                error_code="SS-PROVIDER-001" if i < 7 else "SS-ORCHESTRATION-001",
                organisation_id="org-1",
                occurred_at=now,
            )
            workflow_events.append(evt)

        session.query.return_value.filter.return_value.all.return_value = workflow_events
        session.query.return_value.count.return_value = 10

        repo = AdminAnalyticsRepository(session_factory=mock_session_factory)
        overview = repo.get_telemetry_overview(organisation_id="org-1")

        assert overview.total_errors == 10
        assert len(overview.error_breakdown) == 2
        sorted_breakdown = sorted(overview.error_breakdown, key=lambda x: x.count, reverse=True)
        assert sorted_breakdown[0].error_code == "SS-PROVIDER-001"
        assert sorted_breakdown[0].count == 7
        assert sorted_breakdown[0].percentage == 70.0

    def test_build_latency_distribution_creates_buckets(
        self,
        mock_session_factory: MagicMock,
    ) -> None:
        """_build_latency_distribution should create latency histogram buckets."""
        from soft_skills_backend.modules.admin.infra.analytics_repository import (
            AdminAnalyticsRepository,
        )

        session = mock_session_factory.return_value.__enter__()

        session.query.return_value.filter.return_value.all.return_value = []
        session.query.return_value.count.return_value = 0

        repo = AdminAnalyticsRepository(session_factory=mock_session_factory)
        result = repo.get_telemetry_overview(organisation_id=None)

        assert result.latency_distribution == []
