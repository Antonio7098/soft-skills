"""Tests for agent observability features."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

from soft_skills_backend.platform.observability.circuit_breaker import (
    CIRCUIT_BREAKER_THRESHOLD,
    CircuitBreakerRecord,
    CircuitBreakerStatus,
    DatabaseCircuitBreaker,
)
from soft_skills_backend.platform.observability.stageflow_logging import (
    PipelineErrorSummary,
    summarize_pipeline_error,
)
from soft_skills_backend.platform.workflows.stageflow import AgentWideEventEmitter
from soft_skills_backend.shared.errors import (
    orchestration_error,
    provider_error,
    validation_error,
)


class TestSummarizePipelineError:
    def test_summarize_app_error_with_code(self) -> None:
        error = orchestration_error(
            "Pipeline execution failed",
            code="SS-ORCHESTRATION-003",
            details={"stage": "input_guard"},
        )
        summary = summarize_pipeline_error(
            error,
            stage_name="input_guard",
            pipeline_name="assistant_turn_runtime",
        )
        assert isinstance(summary, PipelineErrorSummary)
        assert summary.error_code == "SS-ORCHESTRATION-003"
        assert summary.category == "orchestration"
        assert summary.stage_name == "input_guard"
        assert summary.pipeline_name == "assistant_turn_runtime"
        assert summary.root_cause == "Pipeline execution failed"
        assert summary.is_retryable is False

    def test_summarize_provider_error_is_retryable(self) -> None:
        error = provider_error(
            "Provider timeout",
            code="SS-PROVIDER-001",
        )
        summary = summarize_pipeline_error(error, stage_name="assistant_runtime")
        assert summary.category == "provider"
        assert summary.is_retryable is True

    def test_summarize_validation_error(self) -> None:
        error = validation_error(
            "Invalid input",
            code="SS-VALIDATION-001",
        )
        summary = summarize_pipeline_error(error)
        assert summary.category == "validation"
        assert summary.is_retryable is False

    def test_summarize_string_error(self) -> None:
        error_str = "Something went wrong"
        summary = summarize_pipeline_error(
            error_str,
            stage_name="history_enrich",
            pipeline_name="assistant_turn_runtime",
        )
        assert summary.error_type == "UnknownError"
        assert summary.root_cause == error_str
        assert summary.stage_name == "history_enrich"

    def test_summarize_exception_with_timeout_in_message(self) -> None:
        error = Exception("Request timeout after 30s")
        summary = summarize_pipeline_error(error)
        assert summary.error_type == "Exception"
        assert summary.is_retryable is True

    def test_summarize_generic_exception(self) -> None:
        error = ValueError("invalid value")
        summary = summarize_pipeline_error(error)
        assert summary.error_type == "ValueError"
        assert summary.root_cause == "invalid value"
        assert summary.is_retryable is False


class TestDatabaseCircuitBreaker:
    def test_get_state_when_no_record(self) -> None:
        session = MagicMock()
        session.get.return_value = None

        breaker = DatabaseCircuitBreaker(session)
        state = breaker.get_state("test_stage")

        assert state.status == CircuitBreakerStatus.CLOSED
        assert state.failure_count == 0
        assert state.last_failure_at is None

    def test_get_state_when_record_exists(self) -> None:
        session = MagicMock()
        now = datetime.now(UTC)
        mock_record = CircuitBreakerRecord(
            name="test_stage",
            status=CircuitBreakerStatus.OPEN.value,
            failure_count=5,
            last_failure_at=now,
            last_failure_reason="Provider timeout",
            opened_at=now,
            closed_at=None,
        )
        session.get.return_value = mock_record

        breaker = DatabaseCircuitBreaker(session)
        state = breaker.get_state("test_stage")

        assert state.status == CircuitBreakerStatus.OPEN
        assert state.failure_count == 5
        assert state.last_failure_reason == "Provider timeout"

    def test_is_callable_when_closed(self) -> None:
        session = MagicMock()
        session.get.return_value = None

        breaker = DatabaseCircuitBreaker(session)
        assert breaker.is_callable("test_stage") is True

    def test_is_callable_when_open_and_within_timeout(self) -> None:
        session = MagicMock()
        now = datetime.now(UTC)
        mock_record = CircuitBreakerRecord(
            name="test_stage",
            status=CircuitBreakerStatus.OPEN.value,
            failure_count=5,
            last_failure_at=now,
        )
        session.get.return_value = mock_record

        breaker = DatabaseCircuitBreaker(session)
        assert breaker.is_callable("test_stage") is False

    def test_record_success_clears_state(self) -> None:
        session = MagicMock()
        now = datetime.now(UTC)
        mock_record = CircuitBreakerRecord(
            name="test_stage",
            status=CircuitBreakerStatus.HALF_OPEN.value,
            failure_count=2,
            last_failure_at=now,
        )
        session.get.return_value = mock_record

        breaker = DatabaseCircuitBreaker(session)
        breaker.record_success("test_stage")

        assert mock_record.status == CircuitBreakerStatus.CLOSED.value
        assert mock_record.failure_count == 0

    def test_record_failure_increments_count(self) -> None:
        session = MagicMock()
        session.get.return_value = None

        breaker = DatabaseCircuitBreaker(session)
        breaker.record_failure("test_stage", "timeout")

        session.add.assert_called_once()
        added_record = session.add.call_args[0][0]
        assert added_record.failure_count == 1
        assert added_record.last_failure_reason == "timeout"

    def test_record_failure_opens_circuit_at_threshold(self) -> None:
        session = MagicMock()
        now = datetime.now(UTC)
        mock_record = CircuitBreakerRecord(
            name="test_stage",
            status=CircuitBreakerStatus.HALF_OPEN.value,
            failure_count=CIRCUIT_BREAKER_THRESHOLD - 1,
            last_failure_at=now,
        )
        session.get.return_value = mock_record

        breaker = DatabaseCircuitBreaker(session)
        breaker.record_failure("test_stage", "timeout")

        assert mock_record.status == CircuitBreakerStatus.OPEN.value
        assert mock_record.failure_count == CIRCUIT_BREAKER_THRESHOLD
        assert mock_record.opened_at is not None


class TestAgentWideEventEmitter:
    def test_emit_stage_event_uses_namespaced_type(self) -> None:
        mock_ctx = MagicMock()
        mock_event_sink = MagicMock()
        mock_ctx.event_sink = mock_event_sink

        mock_result = MagicMock()
        mock_result.name = "input_guard"
        mock_result.status = MagicMock()
        mock_result.status.value = "completed"
        mock_result.started_at = datetime.now(UTC)
        mock_result.ended_at = datetime.now(UTC)
        mock_result.data = {}

        emitter = AgentWideEventEmitter()
        emitter.emit_stage_event(ctx=mock_ctx, result=mock_result)

        mock_event_sink.try_emit.assert_called_once()
        call_kwargs = mock_event_sink.try_emit.call_args[1]
        assert call_kwargs["type"] == "stage.wide.input_guard"

    def test_emit_pipeline_event_uses_namespaced_type(self) -> None:
        mock_ctx = MagicMock()
        mock_ctx.topology = "assistant_turn_runtime"
        mock_event_sink = MagicMock()
        mock_ctx.event_sink = mock_event_sink

        mock_result = MagicMock()
        mock_result.name = "input_guard"
        mock_result.status = MagicMock()
        mock_result.status.value = "completed"
        mock_result.started_at = datetime.now(UTC)
        mock_result.ended_at = datetime.now(UTC)
        mock_result.data = {}

        emitter = AgentWideEventEmitter()
        emitter.emit_pipeline_event(
            ctx=mock_ctx,
            stage_results={"input_guard": mock_result},
            pipeline_name="assistant_turn_runtime",
            status="completed",
        )

        mock_event_sink.try_emit.assert_called_once()
        call_kwargs = mock_event_sink.try_emit.call_args[1]
        assert call_kwargs["type"] == "pipeline.wide.assistant_turn_runtime"

    def test_stage_event_type_prefix(self) -> None:
        emitter = AgentWideEventEmitter()
        assert emitter.stage_event_type == "stage.wide"
        assert emitter.pipeline_event_type == "pipeline.wide"


class TestToolInvokedEvent:
    def test_tool_invoked_event_emitted_before_dispatch(self) -> None:
        mock_ctx = MagicMock()
        mock_event_sink = MagicMock()
        mock_ctx.event_sink = mock_event_sink
        mock_ctx.try_emit_event = MagicMock()

        from soft_skills_backend.modules.assistant.workflows.runtime_models import (
            QueryUserContextToolRequest,
        )

        tool_requests = [
            QueryUserContextToolRequest(
                call_id="call-1",
                tool_name="query_user_context",
                arguments={"sql": "SELECT attempt_id FROM assistant_safe_attempt_summaries_v"},
            )
        ]

        mock_ctx.try_emit_event.assert_not_called()

        for tool_request in tool_requests:
            mock_ctx.try_emit_event(
                "tool.invoked",
                {
                    "tool_name": tool_request.tool_name,
                    "call_id": tool_request.call_id,
                    "arguments": tool_request.arguments,
                    "pipeline_run_id": "test-run-id",
                    "request_id": "test-request-id",
                    "trace_id": "test-trace-id",
                    "workflow_id": "test-workflow-id",
                },
            )

        assert mock_ctx.try_emit_event.call_count == 1
        call_kwargs = mock_ctx.try_emit_event.call_args[0]
        assert call_kwargs[0] == "tool.invoked"
        assert call_kwargs[1]["tool_name"] == "query_user_context"
        assert call_kwargs[1]["call_id"] == "call-1"
