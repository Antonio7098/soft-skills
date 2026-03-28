"""Tests for WorkflowEventRecorder."""

from __future__ import annotations

from unittest.mock import MagicMock

from soft_skills_backend.platform.observability.events import (
    WorkflowEvent,
    WorkflowEventRecorder,
)
from soft_skills_backend.shared.ports import WorkflowEventRepository


class TestWorkflowEventRecorder:
    def test_record_calls_repository_with_correct_event(self) -> None:
        mock_repository = MagicMock(spec=WorkflowEventRepository)
        recorder = WorkflowEventRecorder(mock_repository)

        recorder.record(
            event_type="test.event",
            request_id="req-123",
            trace_id="trace-456",
            workflow_id="wf-789",
            payload={"key": "value"},
            error_code="SS-TEST-001",
        )

        mock_repository.record.assert_called_once()
        call_arg = mock_repository.record.call_args[0][0]
        assert isinstance(call_arg, WorkflowEvent)
        assert call_arg.event_type == "test.event"
        assert call_arg.request_id == "req-123"
        assert call_arg.trace_id == "trace-456"
        assert call_arg.workflow_id == "wf-789"
        assert call_arg.payload == {"key": "value"}
        assert call_arg.error_code == "SS-TEST-001"

    def test_record_with_optional_params(self) -> None:
        mock_repository = MagicMock(spec=WorkflowEventRepository)
        recorder = WorkflowEventRecorder(mock_repository)

        recorder.record(
            event_type="test.event",
            payload={"data": 123},
        )

        mock_repository.record.assert_called_once()
        call_arg = mock_repository.record.call_args[0][0]
        assert call_arg.request_id is None
        assert call_arg.trace_id is None
        assert call_arg.workflow_id is None
        assert call_arg.error_code is None

    def test_record_with_workflow_id_fallback_from_collection_id(self) -> None:
        mock_repository = MagicMock(spec=WorkflowEventRepository)
        recorder = WorkflowEventRecorder(mock_repository)

        recorder.record(
            event_type="test.event",
            payload={"collection_id": "col-abc"},
        )

        mock_repository.record.assert_called_once()
        call_arg = mock_repository.record.call_args[0][0]
        assert call_arg.workflow_id == "col-abc"

    def test_record_with_workflow_id_fallback_from_scenario_id(self) -> None:
        mock_repository = MagicMock(spec=WorkflowEventRepository)
        recorder = WorkflowEventRecorder(mock_repository)

        recorder.record(
            event_type="test.event",
            payload={"scenario_id": "scn-xyz"},
        )

        mock_repository.record.assert_called_once()
        call_arg = mock_repository.record.call_args[0][0]
        assert call_arg.workflow_id == "scn-xyz"

    def test_record_with_workflow_id_fallback_from_generation_artifact_id(self) -> None:
        mock_repository = MagicMock(spec=WorkflowEventRepository)
        recorder = WorkflowEventRecorder(mock_repository)

        recorder.record(
            event_type="test.event",
            payload={"generation_artifact_id": "art-123"},
        )

        mock_repository.record.assert_called_once()
        call_arg = mock_repository.record.call_args[0][0]
        assert call_arg.workflow_id == "art-123"

    def test_record_workflow_id_takes_precedence_over_fallback(self) -> None:
        mock_repository = MagicMock(spec=WorkflowEventRepository)
        recorder = WorkflowEventRecorder(mock_repository)

        recorder.record(
            event_type="test.event",
            workflow_id="wf-explicit",
            payload={"collection_id": "col-abc", "scenario_id": "scn-xyz"},
        )

        mock_repository.record.assert_called_once()
        call_arg = mock_repository.record.call_args[0][0]
        assert call_arg.workflow_id == "wf-explicit"

    def test_record_with_logger_logs_event(self) -> None:
        mock_repository = MagicMock(spec=WorkflowEventRepository)
        recorder = WorkflowEventRecorder(mock_repository, logger_name="test.logger")

        recorder.record(
            event_type="test.event",
            request_id="req-123",
            trace_id="trace-456",
            workflow_id="wf-789",
            payload={"key": "value"},
        )

        mock_repository.record.assert_called_once()

    def test_record_without_logger_does_not_fail(self) -> None:
        mock_repository = MagicMock(spec=WorkflowEventRepository)
        recorder = WorkflowEventRecorder(mock_repository)

        recorder.record(
            event_type="test.event",
            payload={"key": "value"},
        )

        mock_repository.record.assert_called_once()

    def test_record_prioritizes_workflow_id_over_collection_id(self) -> None:
        mock_repository = MagicMock(spec=WorkflowEventRepository)
        recorder = WorkflowEventRecorder(mock_repository)

        recorder.record(
            event_type="test.event",
            workflow_id="wf-priority",
            payload={"collection_id": "col-fallback"},
        )

        call_arg = mock_repository.record.call_args[0][0]
        assert call_arg.workflow_id == "wf-priority"

    def test_record_prioritizes_collection_id_over_scenario_id(self) -> None:
        mock_repository = MagicMock(spec=WorkflowEventRepository)
        recorder = WorkflowEventRecorder(mock_repository)

        recorder.record(
            event_type="test.event",
            payload={"collection_id": "col-first", "scenario_id": "scn-second"},
        )

        call_arg = mock_repository.record.call_args[0][0]
        assert call_arg.workflow_id == "col-first"

    def test_record_prioritizes_scenario_id_over_generation_artifact_id(self) -> None:
        mock_repository = MagicMock(spec=WorkflowEventRepository)
        recorder = WorkflowEventRecorder(mock_repository)

        recorder.record(
            event_type="test.event",
            payload={"scenario_id": "scn-first", "generation_artifact_id": "art-second"},
        )

        call_arg = mock_repository.record.call_args[0][0]
        assert call_arg.workflow_id == "scn-first"
