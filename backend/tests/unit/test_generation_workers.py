from __future__ import annotations

import pytest

from soft_skills_backend.modules.catalog.domain.models import (
    GeneratedScenarioDraft,
    GeneratedScenarioPlan,
    MockCompanyInput,
    MockPersonInput,
)
from soft_skills_backend.modules.catalog.workflows.generation.workers import (
    _validate_generated_scenario_draft,
)


def _plan() -> GeneratedScenarioPlan:
    return GeneratedScenarioPlan(
        title_hint="Escalating launch risk",
        prompt_text_hint="Jordan says legal cannot approve launch. What do you say first?",
        generation_brief="A launch is at risk after legal review and conflicting stakeholder expectations.",
        target_skill_slugs=["expectation-setting"],
        rubric_id="scenario_text@v1",
        supporting_artifact_count=0,
    )


def _draft(*, prompt_text: str) -> GeneratedScenarioDraft:
    return GeneratedScenarioDraft(
        title="Escalating launch risk",
        prompt_text=prompt_text,
        business_context="A launch is at risk after legal review.",
        learner_objective="Reset expectations without damaging trust.",
        constraints=["Board review tomorrow"],
        stakeholder_tensions=["Sales wants speed", "Legal wants certainty"],
        target_skill_slugs=["expectation-setting"],
        rubric_id="scenario_text@v1",
        mock_company=MockCompanyInput(
            name="Northstar AI",
            industry="Enterprise SaaS",
            operating_context="Scaling under board scrutiny.",
        ),
        mock_people=[
            MockPersonInput(
                name="Jordan Singh",
                role="Legal Counsel",
                goals=["Reduce regulatory exposure"],
                communication_style="Precise and cautious",
                relationship_to_scenario="Risk owner",
            )
        ],
        supporting_artifacts=[],
    )


def test_generated_scenario_draft_requires_first_turn_prompt() -> None:
    with pytest.raises(Exception) as exc_info:
        _validate_generated_scenario_draft(draft=_draft(prompt_text="   "), plan=_plan())

    assert "SS-VALIDATION-087" in str(exc_info.value)


def test_generated_scenario_draft_accepts_concrete_prompt_text() -> None:
    _validate_generated_scenario_draft(
        draft=_draft(
            prompt_text="Jordan Singh says legal cannot sign off yet. How do you respond first?"
        ),
        plan=_plan(),
    )
