"""Tests for generation streaming components."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from soft_skills_backend.modules.catalog.contracts.stream import (
    GenerationControlMessage,
    GenerationStage,
    GenerationStreamEvent,
)
from soft_skills_backend.modules.catalog.infra.realtime import (
    GenerationExecution,
    GenerationRealtimeBroker,
)
from soft_skills_backend.modules.catalog.workflows.generation import collection_pipeline
from soft_skills_backend.modules.catalog.workflows.generation.collection_pipeline import (
    generate_collection,
)
from soft_skills_backend.shared.auth import Actor


class TestGenerationStage:
    def test_stage_values(self) -> None:
        assert GenerationStage.PENDING == "pending"
        assert GenerationStage.INPUT_GUARD == "input_guard"
        assert GenerationStage.BLUEPRINT_TRANSFORM == "blueprint_transform"
        assert GenerationStage.BLUEPRINT_LLM_TRANSFORM == "blueprint_llm_transform"
        assert GenerationStage.BLUEPRINT_GUARD == "blueprint_guard"
        assert GenerationStage.PROMPT_ITEMS_WORK == "prompt_items_work"
        assert GenerationStage.SCENARIOS_WORK == "scenarios_work"
        assert GenerationStage.ASSEMBLE_TRANSFORM == "assemble_transform"
        assert GenerationStage.OUTPUT_GUARD == "output_guard"
        assert GenerationStage.PERSISTENCE_WORK == "persistence_work"
        assert GenerationStage.COMPLETED == "completed"
        assert GenerationStage.FAILED == "failed"
        assert GenerationStage.CANCELLED == "cancelled"


class TestGenerationStreamEvent:
    def test_event_creation(self) -> None:
        event = GenerationStreamEvent(
            event_id="evt-123",
            generation_id="gen-456",
            type="progress",
            stage=GenerationStage.BLUEPRINT_TRANSFORM,
            sequence_number=1,
            emitted_at=datetime.now(),
            progress_percent=25.0,
            payload={"model_slug": "gpt-4"},
        )
        assert event.event_id == "evt-123"
        assert event.generation_id == "gen-456"
        assert event.type == "progress"
        assert event.stage == GenerationStage.BLUEPRINT_TRANSFORM
        assert event.sequence_number == 1
        assert event.progress_percent == 25.0
        assert event.payload == {"model_slug": "gpt-4"}


class TestGenerationControlMessage:
    def test_cancel_message(self) -> None:
        msg = GenerationControlMessage(action="cancel", reason="user_requested")
        assert msg.action == "cancel"
        assert msg.reason == "user_requested"

    def test_ping_message(self) -> None:
        msg = GenerationControlMessage(action="ping")
        assert msg.action == "ping"
        assert msg.reason is None


class TestGenerationExecution:
    def test_initial_state(self) -> None:
        execution = GenerationExecution(
            generation_id="gen-123",
            mode="structured",
            stream_token="gen_gen-123",
        )
        assert execution.generation_id == "gen-123"
        assert execution.mode == "structured"
        assert execution.stream_token == "gen_gen-123"
        assert execution.is_cancelled is False
        assert execution.cancel_reason is None

    def test_request_cancel(self) -> None:
        execution = GenerationExecution(
            generation_id="gen-123",
            mode="structured",
            stream_token="gen_gen-123",
        )
        execution.request_cancel("test_reason")
        assert execution.is_cancelled is True
        assert execution.cancel_reason == "test_reason"


class TestGenerationRealtimeBroker:
    @pytest.mark.asyncio()
    async def test_subscribe_and_publish(self) -> None:
        broker = GenerationRealtimeBroker()
        stream_token = "test_token"

        queue = broker.subscribe(stream_token)
        event = GenerationStreamEvent(
            event_id="evt-1",
            generation_id="gen-1",
            type="progress",
            stage=GenerationStage.PENDING,
            sequence_number=0,
            emitted_at=datetime.now(),
            progress_percent=0.0,
            payload={},
        )
        await broker.publish(stream_token, event)

        received = await asyncio.wait_for(queue.get(), timeout=1.0)
        assert received.event_id == "evt-1"

    @pytest.mark.asyncio()
    async def test_backlog(self) -> None:
        broker = GenerationRealtimeBroker()
        stream_token = "test_token"

        for i in range(5):
            event = GenerationStreamEvent(
                event_id=f"evt-{i}",
                generation_id="gen-1",
                type="progress",
                stage=GenerationStage.PENDING,
                sequence_number=i,
                emitted_at=datetime.now(),
                progress_percent=0.0,
                payload={},
            )
            await broker.publish(stream_token, event)

        backlog = broker.backlog(stream_token)
        assert len(backlog) == 5

        backlog_after = broker.backlog(stream_token, after_sequence=2)
        assert len(backlog_after) == 2

    @pytest.mark.asyncio()
    async def test_unsubscribe(self) -> None:
        broker = GenerationRealtimeBroker()
        stream_token = "test_token"

        queue = broker.subscribe(stream_token)
        broker.unsubscribe(stream_token, queue)

        assert stream_token not in broker._subscribers

    def test_register_and_get_execution(self) -> None:
        broker = GenerationRealtimeBroker()
        execution = GenerationExecution(
            generation_id="gen-123",
            mode="structured",
            stream_token="gen_gen-123",
        )
        broker.register_execution(execution)

        retrieved = broker.get_execution("gen-123")
        assert retrieved is not None
        assert retrieved.generation_id == "gen-123"

    def test_get_execution_by_token(self) -> None:
        broker = GenerationRealtimeBroker()
        execution = GenerationExecution(
            generation_id="gen-123",
            mode="structured",
            stream_token="gen_gen-123",
        )
        broker.register_execution(execution)

        retrieved = broker.get_execution_by_token("gen_gen-123")
        assert retrieved is not None
        assert retrieved.generation_id == "gen-123"

    def test_remove_execution(self) -> None:
        broker = GenerationRealtimeBroker()
        execution = GenerationExecution(
            generation_id="gen-123",
            mode="structured",
            stream_token="gen_gen-123",
        )
        broker.register_execution(execution)
        broker.remove_execution("gen-123")

        assert broker.get_execution("gen-123") is None


class TestGenerationCancellationFlow:
    @pytest.mark.asyncio()
    async def test_cancelled_event_published_on_cancel(self) -> None:
        broker = GenerationRealtimeBroker()
        execution = GenerationExecution(
            generation_id="gen-123",
            mode="structured",
            stream_token="gen_gen-123",
        )
        broker.register_execution(execution)
        queue = broker.subscribe(execution.stream_token)

        execution.request_cancel("user_requested")
        assert execution.is_cancelled is True

        cancelled_event = GenerationStreamEvent(
            event_id="evt-cancel-1",
            generation_id=execution.generation_id,
            type="cancelled",
            stage=GenerationStage.CANCELLED,
            sequence_number=999,
            emitted_at=datetime.now(UTC),
            progress_percent=0.0,
            payload={"reason": "user_requested"},
        )
        await broker.publish(execution.stream_token, cancelled_event)

        received = await asyncio.wait_for(queue.get(), timeout=1.0)
        assert received.type == "cancelled"
        assert received.stage == GenerationStage.CANCELLED
        assert received.payload == {"reason": "user_requested"}

    def test_execution_cancellation_sets_is_cancelled_flag(self) -> None:
        execution = GenerationExecution(
            generation_id="gen-456",
            mode="chat",
            stream_token="gen_gen-456",
        )
        assert execution.is_cancelled is False
        assert execution.cancel_reason is None

        execution.request_cancel("timeout")
        assert execution.is_cancelled is True
        assert execution.cancel_reason == "timeout"

    def test_execution_cancellation_multiple_calls(self) -> None:
        execution = GenerationExecution(
            generation_id="gen-789",
            mode="structured",
            stream_token="gen_gen-789",
        )
        execution.request_cancel("first")
        assert execution.is_cancelled is True
        assert execution.cancel_reason == "first"

        execution.request_cancel("second")
        assert execution.is_cancelled is True
        assert execution.cancel_reason == "second"

    @pytest.mark.asyncio()
    async def test_run_structured_stream_stores_task_and_emits_cancelled_event(
        self, app, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        service = app.state.container.catalog_service._generation
        broker = app.state.container.generation_broker
        actor = Actor(user_id="user-123", email="user@example.com")
        execution = GenerationExecution(
            generation_id="gen-123",
            mode="structured",
            stream_token="gen_gen-123",
        )
        broker.register_execution(execution)
        queue = broker.subscribe(execution.stream_token)
        started = asyncio.Event()

        async def fake_generate_collection(**kwargs):
            assert kwargs["execution"] is execution
            assert execution.task is asyncio.current_task()
            execution.pipeline_context = SimpleNamespace(mark_canceled=lambda: None)
            started.set()
            await asyncio.sleep(10.0)
            raise AssertionError("generation task should have been cancelled")

        monkeypatch.setattr(
            "soft_skills_backend.modules.catalog.workflows.generation.service.generate_collection",
            fake_generate_collection,
        )

        task = asyncio.create_task(
            service.run_structured_draft_stream(
                actor=actor,
                execution=execution,
                request_id="req-123",
                trace_id="trace-123",
                workflow_id="wf-123",
                command=SimpleNamespace(),
            )
        )
        try:
            await asyncio.wait_for(started.wait(), timeout=1.0)
            execution.request_cancel("unit_test_cancel")
            assert execution.task is not None
            execution.task.cancel()
            await asyncio.wait_for(task, timeout=1.0)
        finally:
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)

        received = [await asyncio.wait_for(queue.get(), timeout=1.0) for _ in range(2)]
        assert [event.type for event in received] == ["started", "cancelled"]
        assert received[1].payload == {"reason": "unit_test_cancel"}
        assert execution.task is None

    @pytest.mark.asyncio()
    async def test_generate_collection_links_pipeline_context_for_cancellation(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        actor = Actor(user_id="user-123", email="user@example.com")
        execution = GenerationExecution(
            generation_id="gen-ctx",
            mode="structured",
            stream_token="gen_ctx",
            is_cancelled=True,
            cancel_reason="unit_test_cancel",
        )
        captured: dict[str, object] = {}
        expected_view = object()

        class _DummyContext:
            def __init__(self) -> None:
                self.mark_canceled_calls = 0

            def mark_canceled(self) -> None:
                self.mark_canceled_calls += 1

        async def fake_run_logged_pipeline(*args, **kwargs):
            on_context_ready = kwargs["on_context_ready"]
            ctx = _DummyContext()
            captured["ctx"] = ctx
            on_context_ready(ctx)
            assert execution.pipeline_context is ctx
            return object()

        monkeypatch.setattr(collection_pipeline, "run_logged_pipeline", fake_run_logged_pipeline)
        monkeypatch.setattr(
            collection_pipeline, "payload_from_results", lambda *args, **kwargs: expected_view
        )

        result = await generate_collection(
            actor=actor,
            request_id="req-ctx",
            trace_id="trace-ctx",
            workflow_id="wf-ctx",
            mode="structured",
            structured_command=SimpleNamespace(
                model_dump=lambda mode="json": {},
                difficulty="intermediate",
                target_audience="Audience",
            ),
            chat_command=None,
            session_factory=SimpleNamespace(),
            events=SimpleNamespace(record=lambda *args, **kwargs: None),
            llm_provider=SimpleNamespace(provider_name="test-provider"),
            prompt_security_policy=SimpleNamespace(),
            stageflow=SimpleNamespace(),
            prompt_registry=SimpleNamespace(),
            config=SimpleNamespace(),
            blueprint_output=SimpleNamespace(),
            prompt_item_worker_output=SimpleNamespace(),
            scenario_worker_output=SimpleNamespace(),
            timeout_ms=1000,
            sanitize_text=lambda text: text,
            workplace_context_for_commands=lambda *_args: "context",
            taxonomy_context_for_commands=lambda *_args: "taxonomy",
            execution=execution,
        )

        assert result is expected_view
        assert execution.pipeline_context is None
        assert isinstance(captured["ctx"], _DummyContext)
        assert captured["ctx"].mark_canceled_calls == 1

    @pytest.mark.asyncio()
    async def test_generate_collection_appends_stream_generation_id_to_idempotency_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        actor = Actor(user_id="user-123", email="user@example.com")
        execution = GenerationExecution(
            generation_id="gen-stream-123",
            mode="chat",
            stream_token="gen_stream_123",
        )
        captured: dict[str, object] = {}

        async def fake_run_logged_pipeline(*args, **kwargs):
            captured["idempotency_key"] = kwargs["idempotency_key"]
            captured["idempotency_params"] = kwargs["idempotency_params"]
            return object()

        monkeypatch.setattr(collection_pipeline, "run_logged_pipeline", fake_run_logged_pipeline)
        monkeypatch.setattr(
            collection_pipeline, "payload_from_results", lambda *args, **kwargs: object()
        )

        await generate_collection(
            actor=actor,
            request_id="req-ctx",
            trace_id="trace-ctx",
            workflow_id="wf-ctx",
            mode="chat",
            structured_command=None,
            chat_command=SimpleNamespace(
                model_dump=lambda mode="json": {"prompt": "stakeholder management"},
                difficulty="intermediate",
                target_audience="Audience",
            ),
            session_factory=SimpleNamespace(),
            events=SimpleNamespace(record=lambda *args, **kwargs: None),
            llm_provider=SimpleNamespace(provider_name="test-provider"),
            prompt_security_policy=SimpleNamespace(),
            stageflow=SimpleNamespace(),
            prompt_registry=SimpleNamespace(),
            config=SimpleNamespace(),
            blueprint_output=SimpleNamespace(),
            prompt_item_worker_output=SimpleNamespace(),
            scenario_worker_output=SimpleNamespace(),
            timeout_ms=1000,
            sanitize_text=lambda text: text,
            workplace_context_for_commands=lambda *_args: "context",
            taxonomy_context_for_commands=lambda *_args: "taxonomy",
            execution=execution,
            idempotency_key_suffix=execution.generation_id,
        )

        assert captured["idempotency_key"] == (
            "catalog_chat_generation:user-123:req-ctx:gen-stream-123"
        )
        assert captured["idempotency_params"] == {"prompt": "stakeholder management"}
