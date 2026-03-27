"""Assistant API integration tests."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient

from alembic import command as alembic_command
from soft_skills_backend.platform.db.models import (
    AssistantMessageRecord,
    AssistantToolCallRecord,
    AssistantTurnRecord,
    PipelineRunRecord,
    WorkflowEventRecord,
)
from soft_skills_backend.shared.ports.models import ProviderCompletion, ProviderTextChunk


def _migrate(test_settings: Any) -> None:
    alembic_config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    alembic_config.set_main_option(
        "script_location",
        str(Path(__file__).resolve().parents[2] / "alembic"),
    )
    alembic_config.set_main_option("sqlalchemy.url", test_settings.database_url)
    alembic_command.upgrade(alembic_config, "head")


def _register_user(client: TestClient, *, email: str, display_name: str) -> dict[str, object]:
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "display_name": display_name,
            "target_role": "Consultant",
            "goals": ["Improve stakeholder handling"],
            "practice_preferences": {"session_length": "short"},
        },
    )
    assert response.status_code == 200
    return response.json()["data"]


async def _register_user_async(
    client: Any,
    *,
    email: str,
    display_name: str,
) -> dict[str, object]:
    response = await client.post(
        "/api/auth/register",
        json={
            "email": email,
            "display_name": display_name,
            "target_role": "Consultant",
            "goals": ["Improve stakeholder handling"],
            "practice_preferences": {"session_length": "short"},
        },
    )
    assert response.status_code == 200
    return response.json()["data"]


async def _wait_for_turn_status(
    container: Any,
    *,
    turn_id: str,
    expected_status: str,
    timeout_seconds: float = 5.0,
) -> AssistantTurnRecord:
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout_seconds
    while True:
        with container.session_factory() as session:
            turn_record = session.get(AssistantTurnRecord, turn_id)
            assert turn_record is not None
            if turn_record.status == expected_status:
                return turn_record
            if (
                turn_record.status in {"failed", "cancelled"}
                and turn_record.status != expected_status
            ):
                raise AssertionError(f"Turn ended with unexpected status {turn_record.status}")
        errors = container.background_tasks.pop_errors()
        if errors:
            raise AssertionError(
                f"Background task failed while waiting for turn {turn_id}: {errors[-1]!r}"
            ) from errors[-1]
        if loop.time() >= deadline:
            raise AssertionError(f"Timed out waiting for turn {turn_id} to reach {expected_status}")
        await asyncio.sleep(0.05)


class _SequencedAssistantProvider:
    provider_name = "test-provider"
    model_slug = "test-model"

    def __init__(self, payloads: list[dict[str, object]], *, delay_seconds: float = 0.0) -> None:
        self._payloads = payloads
        self._delay_seconds = delay_seconds

    async def complete_json(self, *, messages: Any, call_context: Any) -> ProviderCompletion:
        assert call_context.operation == "assistant_orchestrator_decision"
        if self._delay_seconds > 0:
            await asyncio.sleep(self._delay_seconds)
        payload = self._payloads.pop(0)
        return ProviderCompletion(
            content=payload,
            model_slug=self.model_slug,
            usage={"total_tokens": 10},
            raw_response={"provider": self.provider_name},
        )

    async def stream_text(self, *, messages: Any, call_context: Any) -> Any:
        assert call_context.operation == "assistant_final_response"
        draft = str(messages[-1]["content"]).split("guidance:\n", maxsplit=1)[-1]
        for token in draft.split():
            yield ProviderTextChunk(delta=f"{token} ", model_slug=self.model_slug, done=False)
        yield ProviderTextChunk(delta="", model_slug=self.model_slug, done=True)


@pytest.mark.asyncio
async def test_assistant_turn_streams_tool_events_and_persists_messages(
    app: Any, client: Any, test_settings: Any
) -> None:
    _migrate(test_settings)
    container = app.state.container
    container.background_tasks.attach(asyncio.get_running_loop())
    container.assistant_service._workflows._llm_provider = _SequencedAssistantProvider(  # type: ignore[attr-defined]
        payloads=[
            {
                "tool_calls": [
                    {
                        "call_id": "call-1",
                        "tool_name": "list_recent_attempts",
                        "arguments": {"limit": 2},
                    }
                ],
                "final_response": None,
            },
            {
                "tool_calls": [],
                "final_response": "You have no recent attempts yet. Start with a quick practice.",
            },
        ]
    )
    learner = await _register_user_async(
        client, email="assistant@example.com", display_name="Assistant User"
    )
    session_response = await client.post(
        "/api/assistant/sessions",
        headers={"X-User-ID": learner["id"]},
        json={"title": "Coaching"},
    )
    assert session_response.status_code == 200
    session_id = session_response.json()["data"]["id"]

    turn_response = await client.post(
        f"/api/assistant/sessions/{session_id}/turns",
        headers={"X-User-ID": learner["id"]},
        json={"message": "What should I work on next?"},
    )
    assert turn_response.status_code == 200
    turn = turn_response.json()["data"]

    await _wait_for_turn_status(container, turn_id=turn["id"], expected_status="completed")

    events = container.assistant_service.list_stream_events(turn["stream_token"])
    event_types = [event.type for event in events]
    sequence_numbers = [int(event.sequence_number) for event in events]
    final_response_events = [event for event in events if event.type == "response.completed"]

    assert "turn.started" in event_types
    assert "tool.started" in event_types
    assert "tool.completed" in event_types
    assert "response.completed" in event_types
    assert "turn.completed" in event_types
    assert sequence_numbers == sorted(sequence_numbers)
    assert final_response_events
    final_event = final_response_events[-1]
    assert "You have no recent attempts yet." in str(final_event.payload["content"])
    assert "token_count_prompt" in final_event.payload
    assert "token_count_completion" in final_event.payload
    assert "token_count_total" in final_event.payload
    assert "latency_ms" in final_event.payload
    assert "chunk_count" in final_event.payload
    for event in events:
        assert event.event_id
        assert event.session_id == session_id
        assert event.turn_id == turn["id"]

    with container.session_factory() as session:
        turn_record = session.get(AssistantTurnRecord, turn["id"])
        assert turn_record is not None
        assert turn_record.status == "completed"
        assert session.query(AssistantMessageRecord).filter_by(turn_id=turn["id"]).count() == 2
        assert session.query(AssistantToolCallRecord).filter_by(turn_id=turn["id"]).count() == 1
        pipeline_names = {record.pipeline_name for record in session.query(PipelineRunRecord).all()}
        workflow_events = session.query(WorkflowEventRecord).all()
        workflow_event_types = {event.event_type for event in workflow_events}
    assert "assistant_turn_runtime" in pipeline_names
    stage_wide_events = [et for et in workflow_event_types if et.startswith("stage.wide.")]
    pipeline_wide_events = [et for et in workflow_event_types if et.startswith("pipeline.wide.")]
    assert len(stage_wide_events) > 0, f"Expected stage.wide.* events, got: {workflow_event_types}"
    assert "tool.invoked" in workflow_event_types, (
        f"Expected tool.invoked in workflow events, got: {workflow_event_types}"
    )
    messages_response = await client.get(
        f"/api/assistant/sessions/{session_id}/messages",
        headers={"X-User-ID": learner["id"]},
    )
    assert messages_response.status_code == 200
    assert len(messages_response.json()["data"]) == 2


@pytest.mark.asyncio
async def test_assistant_turn_can_be_cancelled_over_websocket(
    app: Any, client: Any, test_settings: Any
) -> None:
    _migrate(test_settings)
    container = app.state.container
    container.background_tasks.attach(asyncio.get_running_loop())
    container.assistant_service._workflows._llm_provider = _SequencedAssistantProvider(  # type: ignore[attr-defined]
        payloads=[{"tool_calls": [], "final_response": "This should not complete."}],
        delay_seconds=10.0,
    )
    learner = await _register_user_async(
        client, email="cancel@example.com", display_name="Cancel User"
    )
    session_response = await client.post(
        "/api/assistant/sessions",
        headers={"X-User-ID": learner["id"]},
        json={"title": "Cancel"},
    )
    session_id = session_response.json()["data"]["id"]

    turn_response = await client.post(
        f"/api/assistant/sessions/{session_id}/turns",
        headers={"X-User-ID": learner["id"]},
        json={"message": "This will be cancelled."},
    )
    turn = turn_response.json()["data"]

    await asyncio.sleep(0.5)
    cancel_response = await client.post(
        f"/api/assistant/turns/{turn['id']}/cancel",
        headers={"X-User-ID": learner["id"]},
        json={},
    )
    assert cancel_response.status_code == 200

    await _wait_for_turn_status(container, turn_id=turn["id"], expected_status="cancelled")
    event_types = [
        event.type for event in container.assistant_service.list_stream_events(turn["stream_token"])
    ]
    assert "turn.cancelling" in event_types
    assert "turn.cancelled" in event_types

    with container.session_factory() as session:
        turn_record = session.get(AssistantTurnRecord, turn["id"])
        assert turn_record is not None
        assert turn_record.status == "cancelled"


@pytest.mark.asyncio
async def test_assistant_stream_replays_backlog_after_reconnect(
    app: Any, client: Any, test_settings: Any
) -> None:
    _migrate(test_settings)
    container = app.state.container
    container.background_tasks.attach(asyncio.get_running_loop())
    container.assistant_service._workflows._llm_provider = _SequencedAssistantProvider(  # type: ignore[attr-defined]
        payloads=[
            {
                "tool_calls": [],
                "final_response": "Review your recent work and start with one quick practice prompt.",
            }
        ]
    )
    learner = await _register_user_async(
        client, email="assistant-replay@example.com", display_name="Replay User"
    )
    session_response = await client.post(
        "/api/assistant/sessions",
        headers={"X-User-ID": learner["id"]},
        json={"title": "Replay"},
    )
    session_id = session_response.json()["data"]["id"]
    turn_response = await client.post(
        f"/api/assistant/sessions/{session_id}/turns",
        headers={"X-User-ID": learner["id"]},
        json={"message": "How should I start?"},
    )
    turn = turn_response.json()["data"]

    await _wait_for_turn_status(container, turn_id=turn["id"], expected_status="completed")

    replayed_events = container.assistant_service.list_stream_events(turn["stream_token"])
    replay_types = [event.type for event in replayed_events]
    replay_sequences = [int(event.sequence_number) for event in replayed_events]

    assert "response.completed" in replay_types
    assert "turn.completed" in replay_types
    assert replay_sequences == sorted(replay_sequences)

    tail_events = container.assistant_service.list_stream_events(
        turn["stream_token"],
        after_sequence=replay_sequences[-2],
    )
    assert len(tail_events) == 1
    assert tail_events[0].sequence_number == replay_sequences[-1]
    assert tail_events[0].type == "turn.completed"

    sessions_response = await client.get(
        "/api/assistant/sessions",
        headers={"X-User-ID": learner["id"]},
    )
    assert sessions_response.status_code == 200
    assert sessions_response.json()["data"][0]["id"] == session_id
