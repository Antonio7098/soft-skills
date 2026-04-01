"""Assistant API integration tests."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient

from alembic import command as alembic_command
from soft_skills_backend.engines.config import load_marking_runtime_config
from soft_skills_backend.modules.catalog.contracts.stream import (
    GenerationStage,
    GenerationStreamEvent,
)
from soft_skills_backend.modules.catalog.domain.models import (
    CollectionView,
    PromptItemView,
)
from soft_skills_backend.modules.catalog.infra.realtime import GenerationExecution
from soft_skills_backend.modules.catalog.workflows.generation.service import GenerationStartedView
from soft_skills_backend.modules.practice.domain.practice import AssessmentDraft
from soft_skills_backend.modules.practice.workflows.assessment import (
    AssessmentTransformPayload,
    ResolvedAttemptPayload,
)
from soft_skills_backend.platform.db.models import (
    AssistantMessageRecord,
    AssistantSessionRecord,
    AssistantApprovalRequestRecord,
    AssistantToolCallRecord,
    AssistantTurnRecord,
    AssessmentRecord,
    AttemptRecord,
    PipelineRunRecord,
    PracticeRunRecord,
    WorkflowEventRecord,
)
from soft_skills_backend.shared.ports.models import (
    ProviderCompletion,
    ProviderTextChunk,
    ProviderToolCall,
    ProviderToolCompletion,
)


def _migrate(test_settings: Any) -> None:
    alembic_config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    alembic_config.set_main_option(
        "script_location",
        str(Path(__file__).resolve().parents[2] / "alembic"),
    )
    alembic_config.set_main_option("sqlalchemy.url", test_settings.database_url)
    alembic_command.upgrade(alembic_config, "heads")


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


async def _bootstrap_org_admin_and_learner(
    client: Any,
    *,
    admin_email: str,
    learner_email: str,
    org_slug: str,
) -> tuple[dict[str, object], dict[str, object], str]:
    admin = await _register_user_async(
        client,
        email=admin_email,
        display_name="Assistant Org Admin",
    )
    bootstrap_response = await client.post(
        "/api/skills/bootstrap-canon",
        headers={"X-User-ID": admin["id"]},
    )
    assert bootstrap_response.status_code == 200
    learner = await _register_user_async(
        client,
        email=learner_email,
        display_name="Assistant Learner",
    )
    org_response = await client.post(
        "/api/organisations",
        headers={"X-User-ID": str(admin["id"])},
        json={"name": f"Org {org_slug}", "slug": org_slug},
    )
    assert org_response.status_code == 200
    org_id = str(org_response.json()["data"]["id"])
    add_member_response = await client.post(
        f"/api/organisations/{org_id}/members",
        headers={"X-User-ID": str(admin["id"]), "X-Organisation-ID": org_id},
        json={"user_id": str(learner["id"]), "role": "member"},
    )
    assert add_member_response.status_code == 200
    return admin, learner, org_id


def _seed_attempt_summary(
    container: Any,
    *,
    user_id: str,
    practice_type: str,
    overall_score: int,
) -> str:
    now = datetime.now(UTC)
    attempt_id = uuid4().hex
    assessment_id = uuid4().hex
    with container.session_factory() as session:
        attempt = AttemptRecord(
            id=attempt_id,
            session_id=uuid4().hex,
            user_id=user_id,
            workflow_id=uuid4().hex,
            practice_type=practice_type,
            content_item_id=uuid4().hex,
            content_item_type="prompt_item",
            status="assessed",
            response_mode="text",
            response_text="Learner response",
            delivery_version="v1",
            rubric_id="quick_practice_reset_timeline@v1",
            rubric_version="v1",
            assessment_id=assessment_id,
            last_error_code=None,
            trace_id=uuid4().hex[:32],
            created_at=now,
            submitted_at=now,
            assessed_at=now,
        )
        assessment = AssessmentRecord(
            id=assessment_id,
            attempt_id=attempt_id,
            session_id=attempt.session_id,
            user_id=user_id,
            workflow_id=attempt.workflow_id,
            practice_type=practice_type,
            validation_status="validated",
            prompt_version="test.prompt.v1",
            rubric_id=attempt.rubric_id,
            rubric_version=attempt.rubric_version,
            schema_version="test.schema.v1",
            config_version="test.config.v1",
            provider="test-provider",
            model_slug="test-model",
            overall_score=overall_score,
            skill_scores=[],
            evidence=[],
            rationale="sound rationale",
            strengths=["Clear framing"],
            weaknesses=["Could be more specific"],
            next_actions=["Add a sharper tradeoff"],
            raw_payload={},
            rejection_code=None,
            trace_id=attempt.trace_id or uuid4().hex[:32],
            pipeline_run_id=uuid4().hex,
            created_at=now,
        )
        session.add(attempt)
        session.add(assessment)
        session.commit()
    return attempt_id


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


async def _wait_for_pending_approval(
    client: Any,
    *,
    user_id: str,
    timeout_seconds: float = 5.0,
) -> dict[str, object]:
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout_seconds
    while True:
        response = await client.get(
            "/api/assistant/approvals",
            headers={"X-User-ID": user_id},
            params={"status": "pending"},
        )
        assert response.status_code == 200
        approvals = response.json()["data"]
        if approvals:
            return approvals[0]
        if loop.time() >= deadline:
            raise AssertionError("Timed out waiting for a pending assistant approval")
        await asyncio.sleep(0.05)


class _SequencedAssistantProvider:
    provider_name = "test-provider"
    model_slug = "test-model"

    def __init__(self, payloads: list[dict[str, object]], *, delay_seconds: float = 0.0) -> None:
        self._payloads = payloads
        self._delay_seconds = delay_seconds

    async def complete_json(
        self,
        *,
        messages: Any,
        call_context: Any,
        response_schema: Any = None,
        timeout_seconds: Any = None,
    ) -> ProviderCompletion:
        assert call_context.operation == "assistant_orchestrator_decision"
        assert response_schema is not None
        assert timeout_seconds is not None
        if self._delay_seconds > 0:
            await asyncio.sleep(self._delay_seconds)
        payload = self._payloads.pop(0)
        return ProviderCompletion(
            content=payload,
            model_slug=self.model_slug,
            usage={"total_tokens": 10},
            raw_response={"provider": self.provider_name},
        )

    async def complete_with_tools(
        self,
        *,
        messages: Any,
        tools: Any,
        call_context: Any,
        timeout_seconds: Any = None,
        tool_choice: str | None = None,
    ) -> ProviderToolCompletion:
        del messages, tools, tool_choice
        assert call_context.operation == "assistant_orchestrator_decision"
        assert timeout_seconds is not None
        if self._delay_seconds > 0:
            await asyncio.sleep(self._delay_seconds)
        payload = self._payloads.pop(0)
        action = str(payload.get("action"))
        if action == "tool_calls":
            tool_calls = [
                ProviderToolCall(
                    call_id=str(tool_call["call_id"]),
                    tool_name=str(tool_call["tool_name"]),
                    arguments=dict(tool_call["arguments"]),  # type: ignore[arg-type]
                )
                for tool_call in payload["tool_calls"]  # type: ignore[index]
            ]
            return ProviderToolCompletion(
                content=None,
                tool_calls=tool_calls,
                model_slug=self.model_slug,
                usage={"total_tokens": 10},
                raw_response={"provider": self.provider_name},
            )
        return ProviderToolCompletion(
            content=str(payload.get("final_response") or ""),
            tool_calls=[],
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
                "action": "tool_calls",
                "tool_calls": [
                    {
                        "call_id": "call-1",
                        "tool_name": "query_user_context",
                        "arguments": {
                            "sql": (
                                "SELECT attempt_id, practice_type, overall_score "
                                "FROM assistant_safe_attempt_summaries_v "
                                "ORDER BY created_at DESC LIMIT 2"
                            )
                        },
                    }
                ],
                "final_response": None,
            },
            {
                "action": "final_response",
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


@pytest.mark.asyncio
async def test_assistant_generation_tool_streams_progress_updates(
    app: Any, client: Any, test_settings: Any
) -> None:
    _migrate(test_settings)
    container = app.state.container
    container.assistant_service._workflows._llm_provider = _SequencedAssistantProvider(  # type: ignore[attr-defined]
        payloads=[
            {
                "action": "tool_calls",
                "tool_calls": [
                    {
                        "call_id": "call-gen-1",
                        "tool_name": "generate_collection",
                        "arguments": {
                            "prompt": "Build a conflict resolution collection.",
                            "target_audience": "team leads",
                            "difficulty": "intermediate",
                            "content_format_mix": ["quick_practice_prompt"],
                            "target_skill_slugs": ["active-listening"],
                            "target_competency_slugs": ["stakeholder-management"],
                            "rubric_ids": ["quick_practice_reset_timeline@v1"],
                            "counts": {
                                "quick_practice_prompt_count": 1,
                                "interview_prompt_count": 0,
                                "scenario_count": 0,
                                "scenario_artifact_count": 0,
                            },
                        },
                    }
                ],
                "final_response": None,
            },
            {
                "action": "final_response",
                "tool_calls": [],
                "final_response": "Your collection is ready.",
            },
        ]
    )

    learner = await _register_user_async(
        client,
        email="assistant-generation@example.com",
        display_name="Assistant Generation User",
    )

    generation_service = container.catalog_service._generation
    broker = container.generation_broker

    def fake_prepare_chat_draft_stream(
        actor: Any,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        command: Any,
    ) -> tuple[GenerationStartedView, Any]:
        del actor, request_id, trace_id, workflow_id
        started_view = GenerationStartedView(
            generation_id="gen-123",
            stream_token="gen_stream_token",
            mode="chat",
        )
        broker.register_execution(
            GenerationExecution(
                generation_id=started_view.generation_id,
                mode=started_view.mode,
                stream_token=started_view.stream_token,
            )
        )
        return started_view, command

    async def fake_run_chat_draft_stream(
        *,
        actor: Any,
        execution: Any,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        command: Any,
    ) -> None:
        del actor, request_id, trace_id, workflow_id, command
        events = [
            GenerationStreamEvent(
                event_id=uuid4().hex,
                generation_id=execution.generation_id,
                type="started",
                stage=GenerationStage.PENDING,
                sequence_number=0,
                emitted_at=datetime.now(UTC),
                progress_percent=0.0,
                payload={"mode": "chat"},
            ),
            GenerationStreamEvent(
                event_id=uuid4().hex,
                generation_id=execution.generation_id,
                type="progress",
                stage=GenerationStage.BLUEPRINT_LLM_TRANSFORM,
                sequence_number=1,
                emitted_at=datetime.now(UTC),
                progress_percent=15.0,
                payload={
                    "title": "Conflict reset",
                    "summary": "Practice resetting tense stakeholder conversations.",
                    "prompt_items_count": 1,
                    "scenarios_count": 0,
                },
            ),
            GenerationStreamEvent(
                event_id=uuid4().hex,
                generation_id=execution.generation_id,
                type="progress",
                stage=GenerationStage.PROMPT_ITEMS_WORK,
                sequence_number=2,
                emitted_at=datetime.now(UTC),
                progress_percent=50.0,
                payload={
                    "generated_prompt_items": 1,
                    "prompt_items": [
                        {
                            "title": "Reset the room",
                            "prompt_type": "quick_practice_prompt",
                            "difficulty": "intermediate",
                        }
                    ],
                },
            ),
            GenerationStreamEvent(
                event_id=uuid4().hex,
                generation_id=execution.generation_id,
                type="completed",
                stage=GenerationStage.COMPLETED,
                sequence_number=3,
                emitted_at=datetime.now(UTC),
                progress_percent=100.0,
                payload={
                    "collection_id": "col-generated-1",
                    "generation_artifact_id": "artifact-generated-1",
                },
            ),
        ]
        for event in events:
            await broker.publish(execution.stream_token, event)
            await asyncio.sleep(0)

    def fake_get_collection(actor: Any, collection_id: str) -> CollectionView:
        del actor
        assert collection_id == "col-generated-1"
        return CollectionView(
            id=collection_id,
            author_user_id=str(learner["id"]),
            organisation_id=None,
            title="Conflict reset",
            summary="Practice resetting tense stakeholder conversations.",
            target_audience="team leads",
            difficulty="intermediate",
            lifecycle_state="draft",
            verification_state="unverified",
            discovery_tier="private",
            source_type="generated",
            content_format_mix=["quick_practice_prompt"],
            target_skill_slugs=["active-listening"],
            target_competency_slugs=["stakeholder-management"],
            rubric_ids=["quick_practice_reset_timeline@v1"],
            last_generation_artifact_id="artifact-generated-1",
            prompt_items=[
                PromptItemView(
                    id="pi-generated-1",
                    prompt_type="quick_practice_prompt",
                    title="Reset the room",
                    prompt_text="A stakeholder conversation has become tense. Reset it.",
                    difficulty="intermediate",
                    lifecycle_state="draft",
                    target_skill_slugs=["active-listening"],
                    rubric_id="quick_practice_reset_timeline@v1",
                    organisation_id=None,
                )
            ],
            scenarios=[],
        )

    generation_service.prepare_chat_draft_stream = fake_prepare_chat_draft_stream  # type: ignore[method-assign]
    generation_service.run_chat_draft_stream = fake_run_chat_draft_stream  # type: ignore[method-assign]
    container.catalog_service.get_collection = fake_get_collection  # type: ignore[method-assign]

    session_response = await client.post(
        "/api/assistant/sessions",
        headers={"X-User-ID": learner["id"]},
        json={"title": "Generation progress"},
    )
    assert session_response.status_code == 200
    session_id = session_response.json()["data"]["id"]

    turn_response = await client.post(
        f"/api/assistant/sessions/{session_id}/turns",
        headers={"X-User-ID": learner["id"]},
        json={"message": "Generate a conflict resolution collection and decide the rest."},
    )
    assert turn_response.status_code == 200
    turn = turn_response.json()["data"]

    await _wait_for_turn_status(container, turn_id=turn["id"], expected_status="completed")

    events = container.assistant_service.list_stream_events(turn["stream_token"])
    event_types = [event.type for event in events]
    progress_events = [event for event in events if event.type == "tool.updated"]
    completed_event = next(event for event in events if event.type == "tool.completed")

    assert "tool.started" in event_types
    assert "tool.updated" in event_types
    assert event_types.index("tool.updated") < event_types.index("tool.completed")
    assert progress_events
    assert progress_events[0].payload["status"] == "running"
    assert progress_events[0].payload["result"]["generation"]["generation_id"]  # type: ignore[index]
    assert progress_events[-1].payload["result"]["generation"]["current_stage"] == "completed"  # type: ignore[index]
    assert completed_event.payload["status"] == "completed"
    assert completed_event.payload["result"]["generation"]["title"] == "Conflict reset"  # type: ignore[index]
    assert completed_event.payload["result"]["generation"]["progress_percent"] == 100.0  # type: ignore[index]


@pytest.mark.asyncio
async def test_assistant_query_user_context_scopes_rows_to_authenticated_learner(
    app: Any, client: Any, test_settings: Any
) -> None:
    _migrate(test_settings)
    container = app.state.container
    container.assistant_service._workflows._llm_provider = _SequencedAssistantProvider(  # type: ignore[attr-defined]
        payloads=[
            {
                "action": "tool_calls",
                "tool_calls": [
                    {
                        "call_id": "call-1",
                        "tool_name": "query_user_context",
                        "arguments": {
                            "sql": (
                                "SELECT COUNT(*) AS attempt_count "
                                "FROM assistant_safe_attempt_summaries_v"
                            )
                        },
                    }
                ],
                "final_response": None,
            },
            {
                "action": "final_response",
                "tool_calls": [],
                "final_response": "You have one recent assessed attempt.",
            },
        ]
    )
    admin, learner_a, org_id = await _bootstrap_org_admin_and_learner(
        client,
        admin_email="assistant-sql-admin@example.com",
        learner_email="assistant-sql-learner-a@example.com",
        org_slug="assistant-sql-org",
    )
    learner_b = await _register_user_async(
        client,
        email="assistant-sql-learner-b@example.com",
        display_name="Assistant Learner B",
    )
    add_member_response = await client.post(
        f"/api/organisations/{org_id}/members",
        headers={"X-User-ID": str(admin['id']), "X-Organisation-ID": org_id},
        json={"user_id": str(learner_b["id"]), "role": "member"},
    )
    assert add_member_response.status_code == 200

    _seed_attempt_summary(
        container,
        user_id=str(learner_a["id"]),
        practice_type="quick_practice",
        overall_score=4,
    )
    _seed_attempt_summary(
        container,
        user_id=str(learner_b["id"]),
        practice_type="quick_practice",
        overall_score=2,
    )

    session_response = await client.post(
        "/api/assistant/sessions",
        headers={"X-User-ID": learner_a["id"]},
        json={"title": "Scoped SQL"},
    )
    assert session_response.status_code == 200
    session_id = session_response.json()["data"]["id"]

    turn_response = await client.post(
        f"/api/assistant/sessions/{session_id}/turns",
        headers={"X-User-ID": learner_a["id"], "X-Organisation-ID": org_id},
        json={"message": "How many recent attempts do I have?"},
    )
    assert turn_response.status_code == 200
    turn = turn_response.json()["data"]
    await _wait_for_turn_status(container, turn_id=turn["id"], expected_status="completed")

    session_view_response = await client.get(
        f"/api/assistant/sessions/{session_id}",
        headers={"X-User-ID": learner_a["id"]},
    )
    assert session_view_response.status_code == 200
    tool_call = session_view_response.json()["data"]["turns"][0]["tool_calls"][0]
    assert tool_call["tool_name"] == "query_user_context"
    assert tool_call["result"]["rows"] == [{"attempt_count": 1}]


@pytest.mark.asyncio
async def test_assistant_query_user_context_canonicalizes_safe_view_name_and_wildcard(
    app: Any, client: Any, test_settings: Any
) -> None:
    _migrate(test_settings)
    container = app.state.container
    container.assistant_service._workflows._llm_provider = _SequencedAssistantProvider(  # type: ignore[attr-defined]
        payloads=[
            {
                "action": "tool_calls",
                "tool_calls": [
                    {
                        "call_id": "call-1",
                        "tool_name": "query_user_context",
                        "arguments": {
                            "sql": (
                                "SELECT collection_id, collection_name "
                                "FROM assistant_safe_collections_v1 "
                                "ORDER BY updated_at DESC LIMIT 5"
                            )
                        },
                    }
                ],
                "final_response": None,
            },
            {
                "action": "final_response",
                "tool_calls": [],
                "final_response": "Here are your collections.",
            },
        ]
    )
    learner = await _bootstrap_admin_and_learner(
        client,
        learner_email="assistant-sql-collections@example.com",
    )
    await _create_collection(
        client,
        learner_id=str(learner["id"]),
        title="Existing Collection",
        content_format_mix=["quick_practice_prompt"],
        rubric_ids=["quick_practice_reset_timeline@v1"],
        target_skill_slugs=["active-listening"],
        target_competency_slugs=["stakeholder-management"],
    )

    session_response = await client.post(
        "/api/assistant/sessions",
        headers={"X-User-ID": learner["id"]},
        json={"title": "Collections SQL"},
    )
    assert session_response.status_code == 200
    session_id = session_response.json()["data"]["id"]

    turn_response = await client.post(
        f"/api/assistant/sessions/{session_id}/turns",
        headers={"X-User-ID": learner["id"]},
        json={"message": "Can you check my existing collections please"},
    )
    assert turn_response.status_code == 200
    turn = turn_response.json()["data"]
    await _wait_for_turn_status(container, turn_id=turn["id"], expected_status="completed")

    session_view_response = await client.get(
        f"/api/assistant/sessions/{session_id}",
        headers={"X-User-ID": learner["id"]},
    )
    assert session_view_response.status_code == 200
    tool_call = session_view_response.json()["data"]["turns"][0]["tool_calls"][0]
    assert tool_call["tool_name"] == "query_user_context"
    assert tool_call["status"] == "completed"
    assert tool_call["result"]["rows"][0]["collection_name"] == "Existing Collection"


@pytest.mark.asyncio
async def test_assistant_query_user_context_denies_non_allowlisted_sql(
    app: Any, client: Any, test_settings: Any
) -> None:
    _migrate(test_settings)
    container = app.state.container
    container.assistant_service._workflows._llm_provider = _SequencedAssistantProvider(  # type: ignore[attr-defined]
        payloads=[
            {
                "action": "tool_calls",
                "tool_calls": [
                    {
                        "call_id": "call-1",
                        "tool_name": "query_user_context",
                        "arguments": {"sql": "SELECT COUNT(*) AS user_count FROM user_accounts"},
                    }
                ],
                "final_response": None,
            }
        ]
    )
    learner = await _bootstrap_admin_and_learner(
        client,
        learner_email="assistant-sql-denied@example.com",
    )

    session_response = await client.post(
        "/api/assistant/sessions",
        headers={"X-User-ID": learner["id"]},
        json={"title": "Denied SQL"},
    )
    assert session_response.status_code == 200
    session_id = session_response.json()["data"]["id"]

    turn_response = await client.post(
        f"/api/assistant/sessions/{session_id}/turns",
        headers={"X-User-ID": learner["id"]},
        json={"message": "How many users exist globally?"},
    )
    assert turn_response.status_code == 200
    turn = turn_response.json()["data"]
    await _wait_for_turn_status(container, turn_id=turn["id"], expected_status="failed")

    session_view_response = await client.get(
        f"/api/assistant/sessions/{session_id}",
        headers={"X-User-ID": learner["id"]},
    )
    assert session_view_response.status_code == 200
    tool_call = session_view_response.json()["data"]["turns"][0]["tool_calls"][0]
    assert tool_call["tool_name"] == "query_user_context"
    assert tool_call["status"] == "failed"
    assert tool_call["error_code"] == "SS-VALIDATION-318"


@pytest.mark.asyncio
async def test_assistant_facilitates_multi_turn_practice_run(
    app: Any, client: Any, test_settings: Any
) -> None:
    _migrate(test_settings)
    container = app.state.container
    container.assistant_service._workflows._llm_provider = _SequencedAssistantProvider(  # type: ignore[attr-defined]
        payloads=[
            {
                "action": "tool_calls",
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
                "action": "final_response",
                "tool_calls": [],
                "final_response": (
                    "Practice started. Here is question 1. Answer it as if you were replying to the stakeholder."
                ),
            },
            {
                "action": "tool_calls",
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
                "action": "final_response",
                "tool_calls": [],
                "final_response": (
                    "Nice. Here is question 2. Respond with a clear tradeoff and next step."
                ),
            },
            {
                "action": "tool_calls",
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
                "action": "final_response",
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
async def test_assistant_turn_waits_for_human_approval_before_mutating_tool_executes(
    app: Any, client: Any, test_settings: Any
) -> None:
    _migrate(test_settings)
    container = app.state.container
    container.assistant_service._workflows._llm_provider = _SequencedAssistantProvider(  # type: ignore[attr-defined]
        payloads=[
            {
                "action": "tool_calls",
                "tool_calls": [
                    {
                        "call_id": "call-start",
                        "tool_name": "start_collection_practice",
                        "arguments": {"collection_id": "__COLLECTION_ID__", "item_limit": 1},
                    }
                ],
                "final_response": None,
            },
            {
                "action": "final_response",
                "tool_calls": [],
                "final_response": "Practice started after approval.",
            },
        ]
    )
    container.assistant_service._workflows._tools._auto_allow_tools = frozenset(  # type: ignore[attr-defined]
        tool_name
        for tool_name in container.assistant_service._workflows._tools._auto_allow_tools  # type: ignore[attr-defined]
        if tool_name != "start_collection_practice"
    )
    container.practice_service._assessment_marker = _AssistantPracticeMarker()
    learner = await _bootstrap_admin_and_learner(
        client,
        learner_email="assistant-approval@example.com",
    )
    collection = await _seed_quick_practice_collection(client, str(learner["id"]))
    provider_payloads = container.assistant_service._workflows._llm_provider._payloads  # type: ignore[attr-defined]
    provider_payloads[0]["tool_calls"][0]["arguments"]["collection_id"] = collection["id"]  # type: ignore[index]

    session_response = await client.post(
        "/api/assistant/sessions",
        headers={"X-User-ID": learner["id"]},
        json={"title": "Approval Coach"},
    )
    assert session_response.status_code == 200
    session_id = session_response.json()["data"]["id"]

    turn_response = await client.post(
        f"/api/assistant/sessions/{session_id}/turns",
        headers={"X-User-ID": learner["id"]},
        json={"message": f"Start one approved practice item from collection {collection['id']}."},
    )
    assert turn_response.status_code == 200
    turn = turn_response.json()["data"]

    approval = await _wait_for_pending_approval(client, user_id=str(learner["id"]))
    assert approval["tool_name"] == "start_collection_practice"

    before_decision_events = container.assistant_service.list_stream_events(turn["stream_token"])
    before_event_types = [event.type for event in before_decision_events]
    assert "approval.requested" in before_event_types
    assert "tool.started" not in before_event_types

    approve_response = await client.post(
        f"/api/assistant/approvals/{approval['id']}",
        headers={"X-User-ID": learner["id"]},
        json={"decision": "approved", "reason": "continue"},
    )
    assert approve_response.status_code == 200
    assert approve_response.json()["data"]["status"] == "approved"

    completed_turn = await _wait_for_turn_status(
        container,
        turn_id=turn["id"],
        expected_status="completed",
    )
    assert completed_turn.status == "completed"

    after_events = container.assistant_service.list_stream_events(turn["stream_token"])
    after_event_types = [event.type for event in after_events]
    assert after_event_types.index("approval.requested") < after_event_types.index("approval.decided")
    assert after_event_types.index("approval.decided") < after_event_types.index("tool.started")
    assert "tool.completed" in after_event_types
    assert "turn.completed" in after_event_types

    session_view_response = await client.get(
        f"/api/assistant/sessions/{session_id}",
        headers={"X-User-ID": learner["id"]},
    )
    assert session_view_response.status_code == 200
    tool_call = session_view_response.json()["data"]["turns"][0]["tool_calls"][0]
    assert tool_call["status"] == "completed"
    assert tool_call["current_approval"]["status"] == "approved"

    with container.session_factory() as session:
        approval_record = session.query(AssistantApprovalRequestRecord).one()
        tool_call_record = session.query(AssistantToolCallRecord).one()
        assert approval_record.status == "approved"
        assert tool_call_record.status == "completed"


@pytest.mark.asyncio
async def test_assistant_turn_fails_when_human_denies_required_tool_approval(
    app: Any, client: Any, test_settings: Any
) -> None:
    _migrate(test_settings)
    container = app.state.container
    container.assistant_service._workflows._llm_provider = _SequencedAssistantProvider(  # type: ignore[attr-defined]
        payloads=[
            {
                "action": "tool_calls",
                "tool_calls": [
                    {
                        "call_id": "call-start",
                        "tool_name": "start_collection_practice",
                        "arguments": {"collection_id": "__COLLECTION_ID__", "item_limit": 1},
                    }
                ],
                "final_response": None,
            }
        ]
    )
    container.assistant_service._workflows._tools._auto_allow_tools = frozenset(  # type: ignore[attr-defined]
        tool_name
        for tool_name in container.assistant_service._workflows._tools._auto_allow_tools  # type: ignore[attr-defined]
        if tool_name != "start_collection_practice"
    )
    learner = await _bootstrap_admin_and_learner(
        client,
        learner_email="assistant-approval-denied@example.com",
    )
    collection = await _seed_quick_practice_collection(client, str(learner["id"]))
    provider_payloads = container.assistant_service._workflows._llm_provider._payloads  # type: ignore[attr-defined]
    provider_payloads[0]["tool_calls"][0]["arguments"]["collection_id"] = collection["id"]  # type: ignore[index]

    session_response = await client.post(
        "/api/assistant/sessions",
        headers={"X-User-ID": learner["id"]},
        json={"title": "Approval Denial"},
    )
    assert session_response.status_code == 200
    session_id = session_response.json()["data"]["id"]

    turn_response = await client.post(
        f"/api/assistant/sessions/{session_id}/turns",
        headers={"X-User-ID": learner["id"]},
        json={"message": f"Start one practice item from collection {collection['id']}."},
    )
    assert turn_response.status_code == 200
    turn = turn_response.json()["data"]

    approval = await _wait_for_pending_approval(client, user_id=str(learner["id"]))
    deny_response = await client.post(
        f"/api/assistant/approvals/{approval['id']}",
        headers={"X-User-ID": learner["id"]},
        json={"decision": "denied", "reason": "not now"},
    )
    assert deny_response.status_code == 200

    failed_turn = await _wait_for_turn_status(
        container,
        turn_id=turn["id"],
        expected_status="failed",
    )
    assert failed_turn.last_error_code == "SS-ORCHESTRATION-203"

    events = container.assistant_service.list_stream_events(turn["stream_token"])
    event_types = [event.type for event in events]
    assert "approval.requested" in event_types
    assert "approval.decided" in event_types
    assert "tool.failed" in event_types
    assert "tool.started" not in event_types

    with container.session_factory() as session:
        approval_record = session.query(AssistantApprovalRequestRecord).one()
        tool_call_record = session.query(AssistantToolCallRecord).one()
        turn_record = session.get(AssistantTurnRecord, turn["id"])
        assert approval_record.status == "denied"
        assert tool_call_record.status == "failed"
        assert tool_call_record.error_code == "SS-ORCHESTRATION-203"
        assert turn_record is not None
        assert turn_record.status == "failed"

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
                "action": "tool_calls",
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
                "action": "final_response",
                "tool_calls": [],
                "final_response": "Here is question 1.",
            },
            {
                "action": "tool_calls",
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
                "action": "final_response",
                "tool_calls": [],
                "final_response": "Here is question 2.",
            },
            {
                "action": "tool_calls",
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
                "action": "final_response",
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
        payloads=[
            {
                "action": "final_response",
                "tool_calls": [],
                "final_response": "This should not complete.",
            }
        ],
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
                "action": "final_response",
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
