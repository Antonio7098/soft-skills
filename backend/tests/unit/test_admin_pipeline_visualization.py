"""Unit tests for admin service pipeline visualization methods."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from soft_skills_backend.modules.admin.use_cases.admin_service import AdminService
from soft_skills_backend.shared.auth import Actor


class TestAdminServicePipelineMethods:
    """Tests for AdminService pipeline visualization methods."""

    @pytest.fixture
    def mock_pipeline_definitions_repo(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def mock_stage_definitions_repo(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def mock_pipeline_execution_traces_repo(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def mock_pipeline_runs_repo(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def actor(self) -> Actor:
        return Actor(
            user_id="test-user-id",
            email="test@example.com",
            organisation_id="test-org-id",
            organisation_role="admin",
        )

    def test_list_pipelines_returns_empty_when_repo_none(
        self,
        mock_pipeline_definitions_repo: MagicMock,
        actor: Actor,
    ) -> None:
        """list_pipelines should return empty list when repo is None."""
        service = AdminService(
            session_factory=MagicMock(),
            workflow_events=MagicMock(),
            pipeline_definitions=None,
        )

        result = service.list_pipelines(actor)

        assert result == []

    def test_list_pipelines_returns_pipeline_views(
        self,
        mock_pipeline_definitions_repo: MagicMock,
        actor: Actor,
    ) -> None:
        """list_pipelines should return PipelineDefinitionView list."""
        now = datetime.now(UTC)
        mock_pipeline_definitions_repo.list_all.return_value = [
            SimpleNamespace(
                pipeline_name="test-pipeline",
                topology="test-topology",
                description="Test description",
                stage_definitions=["s1", "s2"],
                created_at=now,
                updated_at=now,
            )
        ]

        service = AdminService(
            session_factory=MagicMock(),
            workflow_events=MagicMock(),
            pipeline_definitions=mock_pipeline_definitions_repo,
        )

        result = service.list_pipelines(actor)

        assert len(result) == 1
        assert result[0].pipeline_name == "test-pipeline"
        assert result[0].topology == "test-topology"
        assert result[0].description == "Test description"
        assert result[0].stage_count == 2

    def test_get_pipeline_dag_returns_none_when_repos_none(
        self,
        actor: Actor,
    ) -> None:
        """get_pipeline_dag should return None when repos are None."""
        service = AdminService(
            session_factory=MagicMock(),
            workflow_events=MagicMock(),
            pipeline_definitions=None,
            stage_definitions=None,
        )

        result = service.get_pipeline_dag(actor, "test-pipeline")

        assert result is None

    def test_get_pipeline_dag_returns_none_when_not_found(
        self,
        mock_pipeline_definitions_repo: MagicMock,
        actor: Actor,
    ) -> None:
        """get_pipeline_dag should return None when pipeline not found."""
        mock_pipeline_definitions_repo.get_by_name.return_value = None

        service = AdminService(
            session_factory=MagicMock(),
            workflow_events=MagicMock(),
            pipeline_definitions=mock_pipeline_definitions_repo,
            stage_definitions=MagicMock(),
        )

        result = service.get_pipeline_dag(actor, "nonexistent")

        assert result is None

    def test_get_pipeline_dag_returns_dag_with_stages(
        self,
        mock_pipeline_definitions_repo: MagicMock,
        mock_stage_definitions_repo: MagicMock,
        actor: Actor,
    ) -> None:
        """get_pipeline_dag should return DAG with stage definitions."""
        mock_pipeline_definitions_repo.get_by_name.return_value = SimpleNamespace(
            pipeline_name="test-pipeline",
            topology="test-topology",
            description="Test pipeline",
        )
        mock_stage_definitions_repo.get_by_pipeline.return_value = [
            SimpleNamespace(
                stage_name="stage-1",
                stage_kind="WORK",
                dependencies=[],
                runner_class="TestRunner",
                description="First stage",
            ),
            SimpleNamespace(
                stage_name="stage-2",
                stage_kind="TRANSFORM",
                dependencies=["stage-1"],
                runner_class=None,
                description=None,
            ),
        ]

        service = AdminService(
            session_factory=MagicMock(),
            workflow_events=MagicMock(),
            pipeline_definitions=mock_pipeline_definitions_repo,
            stage_definitions=mock_stage_definitions_repo,
        )

        result = service.get_pipeline_dag(actor, "test-pipeline")

        assert result is not None
        assert result.pipeline_name == "test-pipeline"
        assert result.topology == "test-topology"
        assert len(result.stages) == 2
        assert result.stages[0].name == "stage-1"
        assert result.stages[0].kind == "WORK"
        assert result.stages[0].dependencies == []
        assert result.stages[1].name == "stage-2"
        assert result.stages[1].kind == "TRANSFORM"
        assert result.stages[1].dependencies == ["stage-1"]

    def test_list_pipeline_runs_returns_empty_when_repos_none(self, actor: Actor) -> None:
        """list_pipeline_runs should return empty list when repos are None."""
        service = AdminService(
            session_factory=MagicMock(),
            workflow_events=MagicMock(),
            pipeline_execution_traces=None,
            pipeline_runs=None,
        )

        result = service.list_pipeline_runs(actor, "test-pipeline")

        assert result == []

    def test_list_pipeline_runs_returns_run_summaries(
        self,
        mock_pipeline_execution_traces_repo: MagicMock,
        mock_pipeline_runs_repo: MagicMock,
        actor: Actor,
    ) -> None:
        """list_pipeline_runs should return pipeline run summaries."""
        now = datetime.now(UTC)
        mock_pipeline_execution_traces_repo.get_by_pipeline.return_value = [
            SimpleNamespace(
                pipeline_run_id="run-1",
                pipeline_name="test-pipeline",
                started_at=now,
                completed_at=now,
                total_duration_ms=100,
                execution_sequence=[],
            )
        ]
        mock_pipeline_runs_repo.list_by_pipeline.return_value = [
            SimpleNamespace(
                pipeline_run_id="run-1",
                pipeline_name="test-pipeline",
                status="completed",
                execution_mode="async",
                user_id="user-1",
                request_id="req-1",
                trace_id="trace-1",
                failed_stage=None,
            )
        ]

        service = AdminService(
            session_factory=MagicMock(),
            workflow_events=MagicMock(),
            pipeline_execution_traces=mock_pipeline_execution_traces_repo,
            pipeline_runs=mock_pipeline_runs_repo,
        )

        result = service.list_pipeline_runs(actor, "test-pipeline")

        assert len(result) == 1
        assert result[0].pipeline_run_id == "run-1"
        assert result[0].status == "completed"
        assert result[0].duration_ms == 100

    def test_get_pipeline_trace_returns_none_when_repo_none(self, actor: Actor) -> None:
        """get_pipeline_trace should return None when repo is None."""
        service = AdminService(
            session_factory=MagicMock(),
            workflow_events=MagicMock(),
            pipeline_execution_traces=None,
        )

        result = service.get_pipeline_trace(actor, "test-pipeline", "run-1")

        assert result is None

    def test_get_pipeline_trace_returns_trace(
        self,
        mock_pipeline_execution_traces_repo: MagicMock,
        actor: Actor,
    ) -> None:
        """get_pipeline_trace should return execution trace."""
        now = datetime.now(UTC)
        mock_pipeline_execution_traces_repo.get_by_run_id.return_value = SimpleNamespace(
            pipeline_run_id="run-1",
            pipeline_name="test-pipeline",
            started_at=now,
            completed_at=now,
            total_duration_ms=150,
            execution_sequence=[
                {
                    "stage_name": "stage-1",
                    "event_type": "stage_completed",
                    "timestamp": now.isoformat(),
                    "duration_ms": 50,
                    "status": "completed",
                    "error": None,
                },
                {
                    "stage_name": "stage-2",
                    "event_type": "stage_completed",
                    "timestamp": now.isoformat(),
                    "duration_ms": 100,
                    "status": "completed",
                    "error": None,
                },
            ],
        )

        service = AdminService(
            session_factory=MagicMock(),
            workflow_events=MagicMock(),
            pipeline_execution_traces=mock_pipeline_execution_traces_repo,
        )

        result = service.get_pipeline_trace(actor, "test-pipeline", "run-1")

        assert result is not None
        assert result.pipeline_run_id == "run-1"
        assert result.pipeline_name == "test-pipeline"
        assert result.total_duration_ms == 150
        assert len(result.execution_sequence) == 2
        assert result.execution_sequence[0].stage_name == "stage-1"
        assert result.execution_sequence[0].duration_ms == 50

    def test_get_pipeline_metrics_returns_empty_when_no_runs(
        self,
        mock_pipeline_execution_traces_repo: MagicMock,
        mock_pipeline_runs_repo: MagicMock,
        actor: Actor,
    ) -> None:
        """get_pipeline_metrics should return empty metrics when no runs."""
        mock_pipeline_runs_repo.list_by_pipeline.return_value = []

        service = AdminService(
            session_factory=MagicMock(),
            workflow_events=MagicMock(),
            pipeline_execution_traces=mock_pipeline_execution_traces_repo,
            pipeline_runs=mock_pipeline_runs_repo,
        )

        result = service.get_pipeline_metrics(actor, "test-pipeline")

        assert result is not None
        assert result.pipeline_name == "test-pipeline"
        assert result.total_runs == 0
        assert result.stage_metrics == []

    def test_get_pipeline_metrics_calculates_aggregates(
        self,
        mock_pipeline_execution_traces_repo: MagicMock,
        mock_pipeline_runs_repo: MagicMock,
        actor: Actor,
    ) -> None:
        """get_pipeline_metrics should calculate stage metrics correctly."""
        mock_pipeline_runs_repo.list_by_pipeline.return_value = [
            SimpleNamespace(pipeline_run_id="run-1", status="completed"),
            SimpleNamespace(pipeline_run_id="run-2", status="failed"),
        ]
        mock_pipeline_execution_traces_repo.get_by_pipeline.return_value = [
            SimpleNamespace(
                pipeline_run_id="run-1",
                execution_sequence=[
                    {"stage_name": "stage-1", "status": "completed", "duration_ms": 100},
                    {"stage_name": "stage-2", "status": "completed", "duration_ms": 200},
                ],
            ),
            SimpleNamespace(
                pipeline_run_id="run-2",
                execution_sequence=[
                    {"stage_name": "stage-1", "status": "failed", "duration_ms": 50},
                ],
            ),
        ]

        service = AdminService(
            session_factory=MagicMock(),
            workflow_events=MagicMock(),
            pipeline_execution_traces=mock_pipeline_execution_traces_repo,
            pipeline_runs=mock_pipeline_runs_repo,
        )

        result = service.get_pipeline_metrics(actor, "test-pipeline")

        assert result.pipeline_name == "test-pipeline"
        assert result.total_runs == 2
        assert result.success_count == 1
        assert result.failure_count == 1
        assert result.cancel_count == 0
        assert len(result.stage_metrics) == 2

        stage1_metrics = next(s for s in result.stage_metrics if s.stage_name == "stage-1")
        assert stage1_metrics.invocation_count == 2
        assert stage1_metrics.success_count == 1
        assert stage1_metrics.failure_count == 1

        stage2_metrics = next(s for s in result.stage_metrics if s.stage_name == "stage-2")
        assert stage2_metrics.invocation_count == 1
        assert stage2_metrics.success_count == 1
