"""Tests for generation streaming components."""

from __future__ import annotations

import asyncio
from datetime import datetime

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
