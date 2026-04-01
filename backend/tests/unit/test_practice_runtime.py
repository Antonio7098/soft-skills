from __future__ import annotations

import pytest
from pydantic import ValidationError

from soft_skills_backend.modules.practice.domain.practice import PracticeType
from soft_skills_backend.modules.practice.models import (
    StartInterviewSessionCommand,
    StartScenarioSessionCommand,
)
from soft_skills_backend.modules.practice.workflows.assessment.models import (
    PracticePromptView,
    ResolvedAttemptPayload,
)
from soft_skills_backend.modules.practice.workflows.assessment_service import (
    _required_rubric_skills,
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


def test_quick_practice_assessment_does_not_filter_rubric_by_target_skill_slugs() -> None:
    payload = ResolvedAttemptPayload(
        attempt_id="attempt-123",
        session_id="session-123",
        workflow_id="workflow-123",
        response_text="I clarified the expectation and the next step.",
        prompt=PracticePromptView(
            practice_type=PracticeType.QUICK_PRACTICE,
            content_item_id="prompt-123",
            content_item_type="quick_practice_prompt",
            prompt_type="quick_practice_prompt",
            title="Clarify expectations",
            prompt_text="Respond to the stakeholder.",
            difficulty="intermediate",
            delivery_version="v1",
            response_mode="text",
            target_skill_slugs=["expectation-setting"],
            rubric_id="quick_practice_generated_test",
            rubric_version="v1",
        ),
    )

    assert _required_rubric_skills(payload) is None
