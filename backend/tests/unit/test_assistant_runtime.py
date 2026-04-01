from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError
from stageflow.core import StageContext

from soft_skills_backend.modules.assistant.workflows.approval_service import (
    AssistantApprovalService,
)
from soft_skills_backend.modules.assistant.workflows.practice_facilitation import (
    AssistantPracticeState,
    StartCollectionPracticeToolArgs,
)
from soft_skills_backend.modules.assistant.workflows.runtime_models import (
    AssistantDecision,
    parse_assistant_tool_requests,
)
from soft_skills_backend.modules.assistant.workflows.service import (
    _build_compact_learner_context,
    _chunk_text,
    _required_tool_name,
    _should_rewrite_final_response,
)
from soft_skills_backend.modules.assistant.workflows.tools import (
    AssistantToolExecutor,
    ToolExecutionContext,
    _initial_generation_progress_state,
    _merge_generation_stream_event,
    _normalize_collection_generation_command,
    _summarize_streamed_generation_payload,
)
from soft_skills_backend.modules.catalog.contracts.collection_commands import (
    ChatCollectionGenerationCommand,
)
from soft_skills_backend.modules.catalog.contracts.stream import (
    GenerationStage,
    GenerationStreamEvent,
)
from soft_skills_backend.modules.catalog.workflows.generation.service import GenerationStartedView
from soft_skills_backend.modules.taxonomy.models import (
    CompetencyView,
    RubricView,
    SkillView,
    TaxonomySnapshot,
)
from soft_skills_backend.shared.auth import Actor
from soft_skills_backend.shared.errors import validation_error
from soft_skills_backend.shared.ports.models import ProviderToolCall


def test_assistant_decision_requires_exactly_one_action() -> None:
    with pytest.raises(ValidationError):
        AssistantDecision(action="tool_calls", tool_calls=[], final_response=None)

    with pytest.raises(ValidationError):
        AssistantDecision(
            action="tool_calls",
            tool_calls=[
                {  # type: ignore[list-item]
                    "call_id": "call-1",
                    "tool_name": "query_user_context",
                    "arguments": {
                        "sql": "SELECT attempt_id FROM assistant_safe_attempt_summaries_v"
                    },
                }
            ],
            final_response="Both set",
        )

    decision = AssistantDecision(
        action="final_response",
        tool_calls=[],
        final_response="Use one quick practice.",
    )
    assert decision.action == "final_response"


def test_chunk_text_preserves_readable_segments() -> None:
    chunks = _chunk_text("one two three four five six", chunk_size=9)
    assert chunks == ["one two", "three", "four five", "six"]


class _Role:
    def __init__(self, value: str) -> None:
        self.value = value


class _Message:
    def __init__(self, role: str, content: str) -> None:
        self.role = _Role(role)
        self.content = content


def test_required_tool_name_always_returns_none() -> None:
    """required_tool_name should always return None to let the LLM decide."""
    tool_name = _required_tool_name(
        [_Message("user", "generate a collection for me")],
        AssistantPracticeState(),
    )
    assert tool_name is None


def test_required_tool_name_does_not_force_submission_for_stop_message() -> None:
    tool_name = _required_tool_name(
        [_Message("user", "Stop this practice session.")],
        AssistantPracticeState(
            practice_run_id="run-1",
            current_attempt_id="attempt-1",
            current_position=1,
            total_items=2,
            awaiting_user_answer=True,
        ),
    )

    assert tool_name is None


def test_start_collection_practice_args_require_a_selection_source() -> None:
    with pytest.raises(ValidationError):
        StartCollectionPracticeToolArgs(
            collection_id="col-1",
            include_prompt_items=False,
            include_scenarios=False,
        )


def test_chat_collection_generation_command_content_formats_are_strict() -> None:
    with pytest.raises(ValidationError):
        ChatCollectionGenerationCommand(
            prompt="Build a practice set",
            target_audience="junior consultants",
            difficulty="introductory",
            content_format_mix=["text"],
            target_skill_slugs=["active-listening"],
            target_competency_slugs=["communication"],
            rubric_ids=["rubric-1"],
            counts={
                "quick_practice_prompt_count": 1,
                "interview_prompt_count": 0,
                "scenario_count": 0,
                "scenario_artifact_count": 0,
            },
        )


def test_normalize_collection_generation_command_adds_default_rubrics_and_repairs_counts() -> None:
    command = ChatCollectionGenerationCommand(
        prompt="Generate a collection on negotiating in remote teams for junior consultants.",
        target_audience="junior consultants",
        difficulty="intermediate",
        content_format_mix=["quick_practice_prompt", "interview_prompt", "scenario_step"],
        target_skill_slugs=["negotiation", "empathy", "expectation-setting"],
        target_competency_slugs=["stakeholder-management"],
        rubric_ids=[],
        counts={
            "quick_practice_prompt_count": 1,
            "interview_prompt_count": 1,
            "scenario_count": 0,
            "scenario_artifact_count": 1,
        },
    )
    snapshot = TaxonomySnapshot(
        skills=[
            SkillView(slug="negotiation", name="Negotiation", description=""),
            SkillView(slug="empathy", name="Empathy", description=""),
            SkillView(slug="expectation-setting", name="Expectation Setting", description=""),
        ],
        competencies=[
            CompetencyView(
                slug="stakeholder-management",
                name="Stakeholder Management",
                description="",
                skill_slugs=["negotiation", "empathy", "expectation-setting"],
            )
        ],
        rubrics=[
            RubricView(
                rubric_id="quick_practice_text@v1",
                skill_slug="general",
                content_type="quick_practice_prompt",
                schema_version="v1",
                name="Quick Practice",
            ),
            RubricView(
                rubric_id="interview_text@v1",
                skill_slug="general",
                content_type="interview_prompt",
                schema_version="v1",
                name="Interview",
            ),
            RubricView(
                rubric_id="scenario_text@v1",
                skill_slug="general",
                content_type="scenario_step",
                schema_version="v1",
                name="Scenario",
            ),
        ],
    )

    normalized = _normalize_collection_generation_command(command, snapshot)

    assert normalized.rubric_ids == [
        "quick_practice_text@v1",
        "interview_text@v1",
        "scenario_text@v1",
    ]
    assert normalized.counts.scenario_artifact_count == 0


def test_normalize_collection_generation_command_can_infer_taxonomy_targets_from_prompt() -> None:
    command = ChatCollectionGenerationCommand(
        prompt="Generate a negotiation collection for junior consultants in remote teams.",
        target_audience="junior consultants",
        difficulty="intermediate",
        content_format_mix=["interview_prompt"],
        target_skill_slugs=[],
        target_competency_slugs=[],
        rubric_ids=[],
        counts={
            "quick_practice_prompt_count": 0,
            "interview_prompt_count": 1,
            "scenario_count": 0,
            "scenario_artifact_count": 0,
        },
    )
    snapshot = TaxonomySnapshot(
        skills=[
            SkillView(slug="negotiation", name="Negotiation", description=""),
            SkillView(slug="active-listening", name="Active Listening", description=""),
        ],
        competencies=[
            CompetencyView(
                slug="stakeholder-management",
                name="Stakeholder Management",
                description="",
                skill_slugs=["negotiation", "active-listening"],
            )
        ],
        rubrics=[
            RubricView(
                rubric_id="interview_text@v1",
                skill_slug="general",
                content_type="interview_prompt",
                schema_version="v1",
                name="Interview",
            )
        ],
    )

    normalized = _normalize_collection_generation_command(command, snapshot)

    assert normalized.target_skill_slugs == ["negotiation"]
    assert normalized.target_competency_slugs == ["stakeholder-management"]
    assert normalized.rubric_ids == ["interview_text@v1"]


def test_should_rewrite_final_response_only_after_tool_usage() -> None:
    assert (
        _should_rewrite_final_response(
            draft_response="Here is a quick answer.",
            planning_messages=[{"role": "assistant", "content": "draft"}],
        )
        is False
    )
    assert (
        _should_rewrite_final_response(
            draft_response="Here is a grounded answer.",
            planning_messages=[{"role": "tool", "content": '{"rows": []}'}],
        )
        is True
    )


def test_generation_progress_state_merges_stream_updates() -> None:
    started_view = GenerationStartedView(
        generation_id="gen-123",
        stream_token="gen_token",
        mode="chat",
    )
    state = _initial_generation_progress_state(started_view)

    blueprint_event = GenerationStreamEvent(
        event_id="evt-1",
        generation_id="gen-123",
        type="progress",
        stage=GenerationStage.BLUEPRINT_LLM_TRANSFORM,
        sequence_number=1,
        emitted_at=datetime.now(UTC),
        progress_percent=15.0,
        payload={
            "title": "Conflict reset",
            "summary": "Practice handling a tense stakeholder exchange.",
            "prompt_items_count": 2,
            "scenarios_count": 1,
        },
    )
    prompt_items_event = GenerationStreamEvent(
        event_id="evt-2",
        generation_id="gen-123",
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
    )

    state = _merge_generation_stream_event(state, started_view=started_view, event=blueprint_event)
    state = _merge_generation_stream_event(
        state, started_view=started_view, event=prompt_items_event
    )

    generation = state["generation"]
    assert generation["generation_id"] == "gen-123"
    assert generation["stream_token"] == "gen_token"
    assert generation["current_stage"] == "prompt_items_work"
    assert generation["progress_percent"] == 50.0
    assert generation["blueprint"]["title"] == "Conflict reset"
    assert generation["prompt_items"][0]["title"] == "Reset the room"


def test_summarize_streamed_generation_payload_preserves_progress_metadata() -> None:
    payload = _summarize_streamed_generation_payload(
        progress_state={
            "generation": {
                "generation_id": "gen-123",
                "stream_token": "gen_token",
                "generation_mode": "chat",
                "current_stage": "prompt_items_work",
                "progress_percent": 50.0,
                "blueprint": {
                    "title": "Conflict reset",
                    "summary": "Practice handling a tense stakeholder exchange.",
                    "prompt_items_count": 2,
                    "scenarios_count": 1,
                },
            }
        },
        collection={
            "id": "col-123",
            "title": "Conflict reset",
            "difficulty": "intermediate",
            "content_format_mix": ["quick_practice_prompt"],
            "prompt_items": [{"id": "pi-1"}, {"id": "pi-2"}],
            "scenarios": [{"id": "sc-1"}],
        },
        generation_artifact_id="artifact-123",
        provider="groq",
    )

    assert payload["collection_id"] == "col-123"
    assert payload["generation_artifact_id"] == "artifact-123"
    assert payload["provider"] == "groq"
    assert payload["current_stage"] == "completed"
    assert payload["progress_percent"] == 100.0
    assert payload["prompt_item_count"] == 2
    assert payload["scenario_count"] == 1


def test_build_compact_learner_context_extracts_nested_user_fields() -> None:
    """Test that _build_compact_learner_context correctly extracts display_name and email from nested user dict."""
    profile = {
        "user": {
            "display_name": "Test User",
            "email": "test@example.com",
        },
        "profile": {
            "target_role": "developer",
            "goals": ["learn python"],
        },
    }
    progress = {}
    attempts = []

    result = _build_compact_learner_context(
        latest_user_message="Hello",
        profile=profile,
        progress=progress,
        attempts=attempts,
    )

    assert result["profile"] == {
        "display_name": "Test User",
        "email": "test@example.com",
    }


@pytest.mark.asyncio
async def test_started_tool_failure_is_returned_to_model_as_failed_tool_payload() -> None:
    class _ToolCallView:
        def __init__(
            self,
            *,
            tool_call_id: str,
            status: str,
            error_code: str | None = None,
            error_message: str | None = None,
        ) -> None:
            self.id = tool_call_id
            self.status = status
            self.error_code = error_code
            self.error_message = error_message
            self.started_at = datetime.now(UTC)
            self.completed_at = datetime.now(UTC) if status == "failed" else None

        def model_dump(self, *, mode: str = "json") -> dict[str, object]:
            assert mode == "json"
            return {
                "id": self.id,
                "status": self.status,
                "error_code": self.error_code,
                "error_message": self.error_message,
            }

    class _RepositoryStub:
        def __init__(self) -> None:
            self.failed_tool_call: _ToolCallView | None = None

        def create_tool_call(
            self,
            *,
            turn_id: str,
            tool_name: str,
            args_payload: dict[str, object],
            waiting_for_approval: bool,
        ) -> _ToolCallView:
            assert turn_id == "turn-1"
            assert tool_name == "query_user_context"
            assert args_payload["sql"] == "SELECT * FROM forbidden_table"
            assert waiting_for_approval is False
            return _ToolCallView(tool_call_id="tool-1", status="running")

        def fail_tool_call(
            self,
            *,
            tool_call_id: str,
            error_code: str,
            error_message: str,
        ) -> _ToolCallView:
            assert tool_call_id == "tool-1"
            self.failed_tool_call = _ToolCallView(
                tool_call_id=tool_call_id,
                status="failed",
                error_code=error_code,
                error_message=error_message,
            )
            return self.failed_tool_call

        def create_stream_event(
            self,
            *,
            turn_id: str,
            event_type: str,
            payload: dict[str, object],
            emitted_at: datetime,
        ) -> dict[str, object]:
            return {
                "turn_id": turn_id,
                "event_type": event_type,
                "payload": payload,
                "emitted_at": emitted_at.isoformat(),
            }

    repository = _RepositoryStub()
    broker = SimpleNamespace(publish=AsyncMock())
    sql_guard = SimpleNamespace(
        validate_and_scope=MagicMock(
            side_effect=validation_error(
                "Requested SQL is outside the assistant-safe SQL surface",
                code="SS-VALIDATION-318",
            )
        )
    )
    executor = AssistantToolExecutor(
        repository=repository,  # type: ignore[arg-type]
        approvals=MagicMock(spec=AssistantApprovalService),
        broker=broker,  # type: ignore[arg-type]
        sql_guard=sql_guard,  # type: ignore[arg-type]
        sql_executor=MagicMock(),
        catalog_service=MagicMock(),
        practice_service=MagicMock(),
        stageflow_support=MagicMock(),
        settings=SimpleNamespace(
            tool_approval_timeout_seconds=60,
            tool_approval_auto_allow=["query_user_context"],
            smoke_timeout_seconds=60,
        ),
    )
    tool_request = parse_assistant_tool_requests(
        [
            ProviderToolCall(
                call_id="call-1",
                tool_name="query_user_context",
                arguments={"sql": "SELECT * FROM forbidden_table"},
            )
        ]
    )[0]

    result = await executor._execute_one(
        stage_ctx=MagicMock(spec=StageContext),
        execution=ToolExecutionContext(
            actor=Actor(user_id="user-1", email="learner@example.com", organisation_id="org-1"),
            request_id="req-1",
            trace_id="trace-1",
            workflow_id="wf-1",
            session_id="session-1",
            turn_id="turn-1",
            stream_token="stream-1",
        ),
        tool_request=tool_request,
    )

    assert result.tool_name == "query_user_context"
    assert result.call_id == "call-1"
    assert result.payload["status"] == "failed"
    assert result.payload["error"]["code"] == "SS-VALIDATION-318"
    assert "assistant-safe SQL surface" in result.payload["error"]["message"]
    assert repository.failed_tool_call is not None
    published_events = [call.args[1]["event_type"] for call in broker.publish.await_args_list]
    assert published_events == ["tool.started", "tool.failed"]
