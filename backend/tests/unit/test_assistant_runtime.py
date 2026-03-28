from __future__ import annotations

import pytest
from pydantic import ValidationError

from soft_skills_backend.modules.assistant.workflows.practice_facilitation import (
    AssistantPracticeState,
    StartCollectionPracticeToolArgs,
)
from soft_skills_backend.modules.assistant.workflows.runtime_models import AssistantDecision
from soft_skills_backend.modules.assistant.workflows.service import _chunk_text, _required_tool_name


def test_assistant_decision_requires_exactly_one_action() -> None:
    with pytest.raises(ValidationError):
        AssistantDecision(tool_calls=[], final_response=None)

    with pytest.raises(ValidationError):
        AssistantDecision(
            tool_calls=[
                {  # type: ignore[list-item]
                    "call_id": "call-1",
                    "tool_name": "list_recent_attempts",
                    "arguments": {},
                }
            ],
            final_response="Both set",
        )


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


def test_required_tool_name_requires_generation_tool_for_generation_request() -> None:
    tool_name = _required_tool_name(
        [_Message("user", "Generate a collection for me.")],
        AssistantPracticeState(),
    )

    assert tool_name == "generate_collection"


def test_required_tool_name_requires_practice_submission_when_active() -> None:
    tool_name = _required_tool_name(
        [_Message("user", "Here is my answer to the question.")],
        AssistantPracticeState(
            practice_run_id="run-1",
            current_attempt_id="attempt-1",
            current_position=1,
            total_items=2,
            awaiting_user_answer=True,
        ),
    )

    assert tool_name == "submit_active_practice_response"


def test_required_tool_name_prefers_active_practice_recall_tool() -> None:
    tool_name = _required_tool_name(
        [_Message("user", "Can you repeat the question again?")],
        AssistantPracticeState(
            practice_run_id="run-1",
            current_attempt_id="attempt-1",
            current_position=1,
            total_items=2,
            awaiting_user_answer=True,
        ),
    )

    assert tool_name == "get_active_practice"


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
