from __future__ import annotations

import asyncio
from pathlib import Path

from alembic.config import Config
from fastapi.testclient import TestClient

from alembic import command
from soft_skills_backend.platform.db.models import (
    AssistantMessageRecord,
    AssistantToolCallRecord,
    AssistantTurnRecord,
    PipelineRunRecord,
)
from soft_skills_backend.shared.ports.models import ProviderCompletion, ProviderTextChunk


def _migrate(test_settings) -> None:
    alembic_config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    alembic_config.set_main_option(
        "script_location",
        str(Path(__file__).resolve().parents[2] / "alembic"),
    )
    alembic_config.set_main_option("sqlalchemy.url", test_settings.database_url)
    command.upgrade(alembic_config, "head")


def _register_user(client: TestClient, *, email: str, display_name: str) -> dict[str, object]:
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "display_name": display_name,
            "role": "standard_user",
            "target_role": "Consultant",
            "goals": ["Improve stakeholder handling"],
            "practice_preferences": {"session_length": "short"},
        },
    )
    assert response.status_code == 200
    return response.json()["data"]


class _SequencedAssistantProvider:
    provider_name = "test-provider"
    model_slug = "test-model"

    def __init__(self, payloads: list[dict[str, object]], *, delay_seconds: float = 0.0) -> None:
        self._payloads = payloads
        self._delay_seconds = delay_seconds

    async def complete_json(self, *, messages, call_context) -> ProviderCompletion:
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

    async def stream_text(self, *, messages, call_context):
        assert call_context.operation == "assistant_final_response"
        draft = str(messages[-1]["content"]).split("guidance:\n", maxsplit=1)[-1]
        for token in draft.split():
            yield ProviderTextChunk(delta=f"{token} ", model_slug=self.model_slug, done=False)
        yield ProviderTextChunk(delta="", model_slug=self.model_slug, done=True)


def test_assistant_turn_streams_tool_events_and_persists_messages(app, test_settings) -> None:
    _migrate(test_settings)
    container = app.state.container
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
    with TestClient(app) as client:
        learner = _register_user(client, email="assistant@example.com", display_name="Assistant User")
        session_response = client.post(
            "/api/assistant/sessions",
            headers={"X-User-ID": learner["id"]},
            json={"title": "Coaching"},
        )
        assert session_response.status_code == 200
        session_id = session_response.json()["data"]["id"]

        turn_response = client.post(
            f"/api/assistant/sessions/{session_id}/turns",
            headers={"X-User-ID": learner["id"]},
            json={"message": "What should I work on next?"},
        )
        assert turn_response.status_code == 200
        turn = turn_response.json()["data"]

        event_types: list[str] = []
        sequence_numbers: list[int] = []
        final_response_payload: dict[str, object] | None = None
        with client.websocket_connect(f"/api/assistant/streams/{turn['stream_token']}") as websocket:
            while True:
                event = websocket.receive_json()
                event_types.append(event["type"])
                sequence_numbers.append(int(event["sequence_number"]))
                assert event["event_id"]
                assert event["session_id"] == session_id
                assert event["turn_id"] == turn["id"]
                if event["type"] == "response.completed":
                    final_response_payload = event["payload"]
                if event["type"] in {"turn.completed", "turn.cancelled", "turn.failed"}:
                    break

        assert "turn.started" in event_types
        assert "tool.started" in event_types
        assert "tool.completed" in event_types
        assert "response.delta" in event_types
        assert "response.completed" in event_types
        assert "turn.completed" in event_types
        assert sequence_numbers == sorted(sequence_numbers)
        assert final_response_payload is not None
        assert "You have no recent attempts yet." in str(final_response_payload["content"])

        with container.session_factory() as session:
            turn_record = session.get(AssistantTurnRecord, turn["id"])
            assert turn_record is not None
            assert turn_record.status == "completed"
            assert session.query(AssistantMessageRecord).filter_by(turn_id=turn["id"]).count() == 2
            assert session.query(AssistantToolCallRecord).filter_by(turn_id=turn["id"]).count() == 1
            pipeline_names = {record.pipeline_name for record in session.query(PipelineRunRecord).all()}
        assert "assistant_turn_runtime" in pipeline_names
        messages_response = client.get(
            f"/api/assistant/sessions/{session_id}/messages",
            headers={"X-User-ID": learner["id"]},
        )
        assert messages_response.status_code == 200
        assert len(messages_response.json()["data"]) == 2


def test_assistant_turn_can_be_cancelled_over_websocket(app, test_settings) -> None:
    _migrate(test_settings)
    container = app.state.container
    container.assistant_service._workflows._llm_provider = _SequencedAssistantProvider(  # type: ignore[attr-defined]
        payloads=[{"tool_calls": [], "final_response": "This should not complete."}],
        delay_seconds=10.0,
    )
    with TestClient(app) as client:
        learner = _register_user(client, email="assistant-cancel@example.com", display_name="Cancel User")
        session_response = client.post(
            "/api/assistant/sessions",
            headers={"X-User-ID": learner["id"]},
            json={},
        )
        session_id = session_response.json()["data"]["id"]
        turn_response = client.post(
            f"/api/assistant/sessions/{session_id}/turns",
            headers={"X-User-ID": learner["id"]},
            json={"message": "Help me plan practice."},
        )
        assert turn_response.status_code == 200
        turn = turn_response.json()["data"]

        event_types: list[str] = []
        with client.websocket_connect(f"/api/assistant/streams/{turn['stream_token']}") as websocket:
            websocket.send_json({"type": "turn.cancel", "reason": "user_requested"})
            while True:
                event = websocket.receive_json()
                event_types.append(event["type"])
                if event["type"] in {"turn.cancelled", "turn.failed"}:
                    break

        assert "turn.cancelling" in event_types
        assert "turn.cancelled" in event_types

        with container.session_factory() as session:
            turn_record = session.get(AssistantTurnRecord, turn["id"])
            assert turn_record is not None
            assert turn_record.status == "cancelled"


def test_assistant_stream_replays_backlog_after_reconnect(app, test_settings) -> None:
    _migrate(test_settings)
    container = app.state.container
    container.assistant_service._workflows._llm_provider = _SequencedAssistantProvider(  # type: ignore[attr-defined]
        payloads=[
            {
                "tool_calls": [],
                "final_response": "Review your recent work and start with one quick practice prompt.",
            }
        ]
    )
    with TestClient(app) as client:
        learner = _register_user(client, email="assistant-replay@example.com", display_name="Replay User")
        session_response = client.post(
            "/api/assistant/sessions",
            headers={"X-User-ID": learner["id"]},
            json={"title": "Replay"},
        )
        session_id = session_response.json()["data"]["id"]
        turn_response = client.post(
            f"/api/assistant/sessions/{session_id}/turns",
            headers={"X-User-ID": learner["id"]},
            json={"message": "How should I start?"},
        )
        turn = turn_response.json()["data"]

        with client.websocket_connect(f"/api/assistant/streams/{turn['stream_token']}") as websocket:
            while True:
                event = websocket.receive_json()
                if event["type"] == "turn.completed":
                    break

        replay_types: list[str] = []
        replay_sequences: list[int] = []
        with client.websocket_connect(f"/api/assistant/streams/{turn['stream_token']}") as websocket:
            while True:
                event = websocket.receive_json()
                replay_types.append(event["type"])
                replay_sequences.append(int(event["sequence_number"]))
                if event["type"] == "turn.completed":
                    break

        assert "response.completed" in replay_types
        assert "turn.completed" in replay_types
        assert replay_sequences == sorted(replay_sequences)

        with client.websocket_connect(
            f"/api/assistant/streams/{turn['stream_token']}?last_event_id={replay_sequences[-2]}"
        ) as websocket:
            tail_one = websocket.receive_json()
            assert tail_one["sequence_number"] == replay_sequences[-1]
            assert tail_one["type"] == "turn.completed"
        sessions_response = client.get(
            "/api/assistant/sessions",
            headers={"X-User-ID": learner["id"]},
        )
        assert sessions_response.status_code == 200
        assert sessions_response.json()["data"][0]["id"] == session_id
