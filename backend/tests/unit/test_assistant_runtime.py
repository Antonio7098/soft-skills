from __future__ import annotations

import pytest
from pydantic import ValidationError

from soft_skills_backend.modules.assistant.workflows.runtime_models import AssistantDecision
from soft_skills_backend.modules.assistant.workflows.service import _chunk_text


def test_assistant_decision_requires_exactly_one_action() -> None:
    with pytest.raises(ValidationError):
        AssistantDecision(tool_calls=[], final_response=None)

    with pytest.raises(ValidationError):
        AssistantDecision(
            tool_calls=[
                {
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
