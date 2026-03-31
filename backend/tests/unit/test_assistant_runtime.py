from __future__ import annotations

import pytest
from pydantic import ValidationError

from soft_skills_backend.modules.assistant.workflows.practice_facilitation import (
    AssistantPracticeState,
    StartCollectionPracticeToolArgs,
)
from soft_skills_backend.modules.assistant.workflows.runtime_models import AssistantDecision
from soft_skills_backend.modules.assistant.workflows.service import (
    _build_compact_learner_context,
    _chunk_text,
    _generation_clarification_for_invalid_tool_request,
    _generation_clarification_for_tool_error,
    _required_tool_name,
    _should_rewrite_final_response,
)
from soft_skills_backend.modules.assistant.workflows.tools import (
    _normalize_collection_generation_command,
)
from soft_skills_backend.modules.catalog.contracts.collection_commands import (
    ChatCollectionGenerationCommand,
)
from soft_skills_backend.modules.taxonomy.models import (
    CompetencyView,
    RubricView,
    SkillView,
    TaxonomySnapshot,
)
from soft_skills_backend.shared.errors import orchestration_error
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


def test_invalid_generation_tool_request_returns_clarification() -> None:
    tool_calls = [
        ProviderToolCall(
            call_id="call-1",
            tool_name="generate_collection",
            arguments={
                "prompt": "default prompt",
                "target_audience": "default audience",
                "difficulty": "introductory",
                "content_format_mix": ["text"],
                "target_skill_slugs": ["default-skill"],
                "target_competency_slugs": ["default-competency"],
                "rubric_ids": ["default-rubric"],
                "counts": {
                    "quick_practice_prompt_count": 1,
                    "interview_prompt_count": 0,
                    "scenario_count": 0,
                    "scenario_artifact_count": 0,
                },
            },
        )
    ]
    with pytest.raises(ValidationError) as exc_info:
        ChatCollectionGenerationCommand(
            prompt="default prompt",
            target_audience="default audience",
            difficulty="introductory",
            content_format_mix=["text"],
            target_skill_slugs=["default-skill"],
            target_competency_slugs=["default-competency"],
            rubric_ids=["default-rubric"],
            counts={
                "quick_practice_prompt_count": 1,
                "interview_prompt_count": 0,
                "scenario_count": 0,
                "scenario_artifact_count": 0,
            },
        )
    clarification = _generation_clarification_for_invalid_tool_request(
        raw_tool_calls=tool_calls,
        error=exc_info.value,
    )

    assert clarification is not None
    assert "quick_practice_prompt" in clarification


def test_generation_tool_orchestration_validation_error_returns_clarification() -> None:
    error = orchestration_error(
        "Assistant generation subpipeline failed",
        code="SS-ORCHESTRATION-204",
        details={"error": "SS-VALIDATION-036: Unsupported content format"},
    )

    clarification = _generation_clarification_for_tool_error(
        tool_requests=[type("Req", (), {"tool_name": "generate_collection"})()],
        error=error,
    )

    assert clarification is not None
    assert "pick from your weak skills" in clarification


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
