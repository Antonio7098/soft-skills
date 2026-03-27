from __future__ import annotations

import pytest
from pydantic import ValidationError

from soft_skills_backend.modules.practice.models import (
    StartInterviewSessionCommand,
    StartScenarioSessionCommand,
)


def test_start_interview_command_normalizes_optional_context() -> None:
    command = StartInterviewSessionCommand(
        prompt_item_id="prompt-123",
        competency_context="  Leadership examples  ",
        interviewer_perspective="   ",
    )

    assert command.prompt_item_id == "prompt-123"
    assert command.competency_context == "Leadership examples"
    assert command.interviewer_perspective is None


def test_start_scenario_command_rejects_blank_artifact_fields() -> None:
    with pytest.raises(ValidationError):
        StartScenarioSessionCommand(
            scenario_id="scenario-123",
            artifacts=[
                {  # type: ignore[list-item]
                    "artifact_type": "email",
                    "title": "Stakeholder note",
                    "body": "   ",
                }
            ],
        )
