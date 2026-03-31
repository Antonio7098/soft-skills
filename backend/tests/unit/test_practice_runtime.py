from __future__ import annotations

import pytest
from pydantic import ValidationError

from soft_skills_backend.modules.practice.models import (
    StartInterviewSessionCommand,
    StartScenarioRunItemCommand,
    StartScenarioSessionCommand,
)
from soft_skills_backend.modules.practice.infra.queries import _build_scenario_prompt_text
from soft_skills_backend.modules.practice.workflows.assessment.models import ScenarioContextView


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


def test_start_scenario_run_item_normalizes_optional_question_text() -> None:
    command = StartScenarioRunItemCommand(
        practice_type="scenario",
        scenario_id="scenario-123",
        question_text="  What do you say to the CFO first?  ",
        question_index=2,
        question_count=4,
    )

    assert command.question_text == "What do you say to the CFO first?"
    assert command.question_index == 2
    assert command.question_count == 4


def test_build_scenario_prompt_text_includes_active_question_progress() -> None:
    prompt_text = _build_scenario_prompt_text(
        ScenarioContextView(
            business_context="A launch date is under pressure.",
            learner_objective="Reset expectations with the sponsor.",
            constraints=["Board review tomorrow"],
            stakeholder_tensions=["Legal wants delay"],
            questions=["Question one", "Question two"],
            active_question_text="What do you say to the sponsor first?",
            active_question_index=2,
            question_count=4,
        )
    )

    assert "Question 2 of 4: What do you say to the sponsor first?" in prompt_text
    assert "Business context: A launch date is under pressure." in prompt_text
