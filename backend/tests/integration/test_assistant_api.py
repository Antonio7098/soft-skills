"""Assistant API integration tests."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient

from alembic import command as alembic_command
from soft_skills_backend.engines.config import load_marking_runtime_config
from soft_skills_backend.modules.practice.domain.practice import AssessmentDraft
from soft_skills_backend.modules.practice.workflows.assessment import (
    AssessmentTransformPayload,
    ResolvedAttemptPayload,
)
from soft_skills_backend.platform.db.models import (
    AssistantMessageRecord,
    AssistantSessionRecord,
    AssistantToolCallRecord,
    AssistantTurnRecord,
    AssessmentRecord,
    AttemptRecord,
    PipelineRunRecord,
    PracticeRunRecord,
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


async def _bootstrap_admin_and_learner(client: Any, *, learner_email: str) -> dict[str, object]:
    admin = await _register_user_async(
        client,
        email="assistant-admin@example.com",
        display_name="Assistant Admin",
    )
    bootstrap_response = await client.post(
        "/api/skills/bootstrap-canon",
        headers={"X-User-ID": admin["id"]},
    )
    assert bootstrap_response.status_code == 200
    return await _register_user_async(
        client,
        email=learner_email,
        display_name="Assistant Learner",
    )


async def _create_collection(
    client: Any,
    *,
    learner_id: str,
    title: str,
    content_format_mix: list[str],
    rubric_ids: list[str],
    target_skill_slugs: list[str],
    target_competency_slugs: list[str],
) -> dict[str, object]:
    response = await client.post(
        "/api/collections",
        headers={"X-User-ID": learner_id},
        json={
            "title": title,
            "summary": "Assistant facilitation coverage collection.",
            "target_audience": "Early-career consultants",
            "difficulty": "intermediate",
            "content_format_mix": content_format_mix,
            "target_skill_slugs": target_skill_slugs,
            "target_competency_slugs": target_competency_slugs,
            "rubric_ids": rubric_ids,
        },
    )
    assert response.status_code == 200
    return response.json()["data"]


async def _seed_quick_practice_collection(client: Any, learner_id: str) -> dict[str, object]:
    collection = await _create_collection(
        client,
        learner_id=learner_id,
        title="Assistant Practice Pack",
        content_format_mix=["quick_practice_prompt"],
        rubric_ids=["quick_practice_reset_timeline@v1"],
        target_skill_slugs=["active-listening", "expectation-setting"],
        target_competency_slugs=["stakeholder-management"],
    )
    prompt_payloads = [
        {
            "prompt_type": "quick_practice_prompt",
            "title": "Reset the timeline",
            "prompt_text": (
                "A client asks for an impossible delivery date. Respond with empathy and a realistic next step."
            ),
            "difficulty": "intermediate",
            "target_skill_slugs": ["active-listening", "expectation-setting"],
            "rubric_id": "quick_practice_reset_timeline@v1",
        },
        {
            "prompt_type": "quick_practice_prompt",
            "title": "Handle a scope push",
            "prompt_text": (
                "A stakeholder wants to add urgent scope without moving the deadline. Respond with a clear tradeoff."
            ),
            "difficulty": "intermediate",
            "target_skill_slugs": ["active-listening", "expectation-setting"],
            "rubric_id": "quick_practice_reset_timeline@v1",
        },
    ]
    for payload in prompt_payloads:
        response = await client.post(
            f"/api/collections/{collection['id']}/prompt-items",
            headers={"X-User-ID": learner_id},
            json=payload,
        )
        assert response.status_code == 200
    detail_response = await client.get(
        f"/api/collections/{collection['id']}",
        headers={"X-User-ID": learner_id},
    )
    assert detail_response.status_code == 200
    return detail_response.json()["data"]


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
                tool_errors = (
                    session.query(AssistantToolCallRecord)
                    .filter(AssistantToolCallRecord.turn_id == turn_id)
                    .order_by(AssistantToolCallRecord.started_at.asc())
                    .all()
                )
                raise AssertionError(
                    "Turn ended with unexpected status "
                    f"{turn_record.status} "
                    f"(last_error_code={turn_record.last_error_code}, "
                    f"reason={turn_record.cancel_reason}, "
                    f"tool_errors={[(tool.tool_name, tool.error_message) for tool in tool_errors]})"
                )
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


class _AssistantPracticeMarker:
    provider_name = "openai"
    model_slug = "gpt-4.1-mini"

    async def mark_attempt(
        self,
        *,
        prompt_payload: ResolvedAttemptPayload,
        learner_payload: Any,
        call_context: Any,
    ) -> AssessmentTransformPayload:
        del learner_payload, call_context
        config = load_marking_runtime_config()
        score = 2 if prompt_payload.prompt.practice_type.value == "quick_practice" else 4
        skill_slugs = list(prompt_payload.prompt.target_skill_slugs)
        if prompt_payload.prompt.practice_type.value == "quick_practice" and not skill_slugs:
            skill_slugs = ["active-listening", "expectation-setting"]
        return AssessmentTransformPayload(
            draft=AssessmentDraft.model_validate(
                {
                    "prompt_version": config.prompt_version,
                    "rubric_version": prompt_payload.prompt.rubric_version,
                    "provider": self.provider_name,
                    "model_slug": self.model_slug,
                    "overall_score": score,
                    "rationale": "The response handled the stakeholder pressure credibly.",
                    "skill_scores": [
                        {
                            "skill_slug": slug,
                            "score": score,
                            "rationale": f"The response demonstrated {slug}.",
                        }
                        for slug in skill_slugs
                    ],
                    "evidence": [
                        {
                            "skill_slug": slug,
                            "quote": prompt_payload.response_text,
                            "explanation": f"The response text showed evidence for {slug}.",
                        }
                        for slug in skill_slugs
                    ],
                    "strengths": ["Stayed grounded in the prompt and proposed a concrete next step."],
                    "weaknesses": ["Could have added one clearer check-in point."],
                    "next_actions": ["Practice closing with an owner and deadline."],
                }
            ),
            raw_payload={"ok": True, "practice_type": prompt_payload.prompt.practice_type.value},
            model_slug=self.model_slug,
            schema_version=config.output_schema_version,
        )


@pytest.mark.asyncio
async def test_assistant_turn_streams_tool_events_and_persists_messages(
    app: Any, client: Any, test_settings: Any
) -> None:
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
async def test_assistant_facilitates_multi_turn_practice_run(
    app: Any, client: Any, test_settings: Any
) -> None:
    _migrate(test_settings)
    container = app.state.container
    container.assistant_service._workflows._llm_provider = _SequencedAssistantProvider(  # type: ignore[attr-defined]
        payloads=[
            {
                "tool_calls": [
                    {
                        "call_id": "call-start",
                        "tool_name": "start_collection_practice",
                        "arguments": {"collection_id": "__COLLECTION_ID__", "item_limit": 2},
                    }
                ],
                "final_response": None,
            },
            {
                "tool_calls": [],
                "final_response": (
                    "Practice started. Here is question 1. Answer it as if you were replying to the stakeholder."
                ),
            },
            {
                "tool_calls": [
                    {
                        "call_id": "call-submit-1",
                        "tool_name": "submit_active_practice_response",
                        "arguments": {},
                    }
                ],
                "final_response": None,
            },
            {
                "tool_calls": [],
                "final_response": (
                    "Nice. Here is question 2. Respond with a clear tradeoff and next step."
                ),
            },
            {
                "tool_calls": [
                    {
                        "call_id": "call-submit-2",
                        "tool_name": "submit_active_practice_response",
                        "arguments": {},
                    }
                ],
                "final_response": None,
            },
            {
                "tool_calls": [],
                "final_response": (
                    "Practice complete. You handled the pressure well and kept the response grounded."
                ),
            },
        ]
    )
    container.practice_service._assessment_marker = _AssistantPracticeMarker()
    learner = await _bootstrap_admin_and_learner(
        client,
        learner_email="assistant-practice@example.com",
    )
    collection = await _seed_quick_practice_collection(client, str(learner["id"]))
    provider_payloads = container.assistant_service._workflows._llm_provider._payloads  # type: ignore[attr-defined]
    provider_payloads[0]["tool_calls"][0]["arguments"]["collection_id"] = collection["id"]  # type: ignore[index]

    session_response = await client.post(
        "/api/assistant/sessions",
        headers={"X-User-ID": learner["id"]},
        json={"title": "Practice Coach"},
    )
    assert session_response.status_code == 200
    session_id = session_response.json()["data"]["id"]

    first_turn_response = await client.post(
        f"/api/assistant/sessions/{session_id}/turns",
        headers={"X-User-ID": learner["id"]},
        json={"message": f"Start a two-question practice session from collection {collection['id']}."},
    )
    assert first_turn_response.status_code == 200
    first_turn = first_turn_response.json()["data"]
    await _wait_for_turn_status(container, turn_id=first_turn["id"], expected_status="completed")

    second_turn_response = await client.post(
        f"/api/assistant/sessions/{session_id}/turns",
        headers={"X-User-ID": learner["id"]},
        json={
            "message": (
                "I understand why the date matters. The earliest realistic option is next Friday, "
                "and I can confirm the scope tradeoff with the team tomorrow afternoon."
            )
        },
    )
    assert second_turn_response.status_code == 200
    second_turn = second_turn_response.json()["data"]
    await _wait_for_turn_status(container, turn_id=second_turn["id"], expected_status="completed")

    third_turn_response = await client.post(
        f"/api/assistant/sessions/{session_id}/turns",
        headers={"X-User-ID": learner["id"]},
        json={
            "message": (
                "I hear the urgency. If we add the scope now, we need to move the deadline by two days, "
                "or we keep the date and drop the new request until the next checkpoint."
            )
        },
    )
    assert third_turn_response.status_code == 200
    third_turn = third_turn_response.json()["data"]
    await _wait_for_turn_status(container, turn_id=third_turn["id"], expected_status="completed")

    session_view_response = await client.get(
        f"/api/assistant/sessions/{session_id}",
        headers={"X-User-ID": learner["id"]},
    )
    assert session_view_response.status_code == 200
    session_view = session_view_response.json()["data"]
    turn_tool_names = [
        [tool["tool_name"] for tool in turn["tool_calls"]]
        for turn in session_view["turns"]
    ]
    assert turn_tool_names == [
        ["start_collection_practice"],
        ["submit_active_practice_response"],
        ["submit_active_practice_response"],
    ]
    assert len(session_view["messages"]) == 6
    assert "Practice started." in session_view["messages"][1]["content"]
    assert "Here is question 2." in session_view["messages"][3]["content"]
    assert "Practice complete." in session_view["messages"][5]["content"]

    practice_run_id = session_view["turns"][0]["tool_calls"][0]["result"]["practice"]["practice_run_id"]

    with container.session_factory() as session:
        assistant_session = session.get(AssistantSessionRecord, session_id)
        run_record = session.get(PracticeRunRecord, practice_run_id)
        attempt_records = (
            session.query(AttemptRecord)
            .filter(AttemptRecord.workflow_id == practice_run_id)
            .order_by(AttemptRecord.created_at.asc())
            .all()
        )
        assessment_records = (
            session.query(AssessmentRecord)
            .filter(AssessmentRecord.workflow_id == practice_run_id)
            .order_by(AssessmentRecord.created_at.asc())
            .all()
        )
        workflow_event_types = {
            event.event_type for event in session.query(WorkflowEventRecord).all()
        }
    assert assistant_session is not None
    assert assistant_session.metadata_payload["practice_state"]["practice_run_id"] is None
    assert assistant_session.metadata_payload["practice_state"]["current_attempt_id"] is None
    assert run_record is not None
    assert run_record.status == "completed"
    assert run_record.completed_items == 2
    assert len(attempt_records) == 2
    assert all(record.status == "assessed" for record in attempt_records)
    assert len(assessment_records) == 2
    assert "practice.run_started.v1" in workflow_event_types
    assert "practice.attempt_submitted.v1" in workflow_event_types
    assert "assessment.validated.v1" in workflow_event_types


@pytest.mark.asyncio
@pytest.mark.skip(reason="Known integration harness hang while teardown is being stabilized")
async def test_assistant_practice_session_metadata_transitions_between_questions(
    app: Any, client: Any, test_settings: Any
) -> None:
    _migrate(test_settings)
    container = app.state.container
    container.assistant_service._workflows._llm_provider = _SequencedAssistantProvider(  # type: ignore[attr-defined]
        payloads=[
            {
                "tool_calls": [
                    {
                        "call_id": "call-start",
                        "tool_name": "start_collection_practice",
                        "arguments": {"collection_id": "__COLLECTION_ID__", "item_limit": 2},
                    }
                ],
                "final_response": None,
            },
            {
                "tool_calls": [],
                "final_response": "Here is question 1.",
            },
            {
                "tool_calls": [
                    {
                        "call_id": "call-submit-1",
                        "tool_name": "submit_active_practice_response",
                        "arguments": {},
                    }
                ],
                "final_response": None,
            },
            {
                "tool_calls": [],
                "final_response": "Here is question 2.",
            },
            {
                "tool_calls": [
                    {
                        "call_id": "call-submit-2",
                        "tool_name": "submit_active_practice_response",
                        "arguments": {},
                    }
                ],
                "final_response": None,
            },
            {
                "tool_calls": [],
                "final_response": "Practice complete.",
            },
        ]
    )
    container.practice_service._assessment_marker = _AssistantPracticeMarker()
    learner = await _bootstrap_admin_and_learner(
        client,
        learner_email="assistant-practice-metadata@example.com",
    )
    collection = await _seed_quick_practice_collection(client, str(learner["id"]))
    provider_payloads = container.assistant_service._workflows._llm_provider._payloads  # type: ignore[attr-defined]
    provider_payloads[0]["tool_calls"][0]["arguments"]["collection_id"] = collection["id"]  # type: ignore[index]

    session_response = await client.post(
        "/api/assistant/sessions",
        headers={"X-User-ID": learner["id"]},
        json={"title": "Practice Metadata"},
    )
    assert session_response.status_code == 200
    session_id = session_response.json()["data"]["id"]

    first_turn_response = await client.post(
        f"/api/assistant/sessions/{session_id}/turns",
        headers={"X-User-ID": learner["id"]},
        json={"message": f"Start a two-question practice session from collection {collection['id']}."},
    )
    assert first_turn_response.status_code == 200
    first_turn = first_turn_response.json()["data"]
    await _wait_for_turn_status(container, turn_id=first_turn["id"], expected_status="completed")

    with container.session_factory() as session:
        assistant_session = session.get(AssistantSessionRecord, session_id)
        assert assistant_session is not None
        state_after_start = dict(assistant_session.metadata_payload["practice_state"])

    assert state_after_start["practice_run_id"] is not None
    assert state_after_start["current_attempt_id"] is not None
    assert state_after_start["current_position"] == 1
    assert state_after_start["total_items"] == 2
    assert state_after_start["awaiting_user_answer"] is True

    second_turn_response = await client.post(
        f"/api/assistant/sessions/{session_id}/turns",
        headers={"X-User-ID": learner["id"]},
        json={
            "message": (
                "I understand why the date matters. The earliest realistic option is next Friday, "
                "and I can confirm the scope tradeoff with the team tomorrow afternoon."
            )
        },
    )
    assert second_turn_response.status_code == 200
    second_turn = second_turn_response.json()["data"]
    await _wait_for_turn_status(container, turn_id=second_turn["id"], expected_status="completed")

    with container.session_factory() as session:
        assistant_session = session.get(AssistantSessionRecord, session_id)
        assert assistant_session is not None
        state_after_first_answer = dict(assistant_session.metadata_payload["practice_state"])

    assert state_after_first_answer["practice_run_id"] == state_after_start["practice_run_id"]
    assert state_after_first_answer["current_attempt_id"] != state_after_start["current_attempt_id"]
    assert state_after_first_answer["current_position"] == 2
    assert state_after_first_answer["total_items"] == 2
    assert state_after_first_answer["awaiting_user_answer"] is True

    third_turn_response = await client.post(
        f"/api/assistant/sessions/{session_id}/turns",
        headers={"X-User-ID": learner["id"]},
        json={
            "message": (
                "I hear the urgency. If we add the scope now, we need to move the deadline by two days, "
                "or we keep the date and drop the new request until the next checkpoint."
            )
        },
    )
    assert third_turn_response.status_code == 200
    third_turn = third_turn_response.json()["data"]
    await _wait_for_turn_status(container, turn_id=third_turn["id"], expected_status="completed")

    with container.session_factory() as session:
        assistant_session = session.get(AssistantSessionRecord, session_id)
        assert assistant_session is not None
        final_state = dict(assistant_session.metadata_payload["practice_state"])

    assert final_state["practice_run_id"] is None
    assert final_state["current_attempt_id"] is None
    assert final_state["current_position"] is None
    assert final_state["total_items"] is None
    assert final_state["awaiting_user_answer"] is False


@pytest.mark.asyncio
async def test_assistant_turn_can_be_cancelled_over_websocket(
    app: Any, client: Any, test_settings: Any
) -> None:
    _migrate(test_settings)
    container = app.state.container
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
