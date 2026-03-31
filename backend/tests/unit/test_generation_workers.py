from __future__ import annotations

import pytest

from soft_skills_backend.modules.catalog.domain.models import (
    GeneratedScenarioDraft,
    GeneratedScenarioPlan,
)
from soft_skills_backend.modules.catalog.workflows.generation.workers import (
    _validate_generated_scenario_draft,
)


def test_validate_generated_scenario_draft_rejects_duplicate_questions() -> None:
    draft = GeneratedScenarioDraft(
        title="Executive reset",
        business_context="A launch is under pressure.",
        learner_objective="Reset expectations without losing trust.",
        constraints=["Board update tomorrow"],
        stakeholder_tensions=["Sales wants the date unchanged"],
        questions=["What do you say first?", "what do you say first?"],
        target_skill_slugs=["expectation-setting"],
        rubric_id="scenario_text@v1",
    )
    plan = GeneratedScenarioPlan(
        title_hint="Executive reset",
        generation_brief="Keep it realistic.",
        target_skill_slugs=["expectation-setting"],
        rubric_id="scenario_text@v1",
        supporting_artifact_count=0,
        question_count=2,
    )

    with pytest.raises(Exception) as exc_info:
        _validate_generated_scenario_draft(draft=draft, plan=plan)

    assert "SS-VALIDATION-088" in str(exc_info.value)


def test_validate_generated_scenario_draft_rejects_question_count_mismatch() -> None:
    draft = GeneratedScenarioDraft(
        title="Executive reset",
        business_context="A launch is under pressure.",
        learner_objective="Reset expectations without losing trust.",
        constraints=[],
        stakeholder_tensions=[],
        questions=["What do you say first?"],
        target_skill_slugs=["expectation-setting"],
        rubric_id="scenario_text@v1",
    )
    plan = GeneratedScenarioPlan(
        title_hint="Executive reset",
        generation_brief="Keep it realistic.",
        target_skill_slugs=["expectation-setting"],
        rubric_id="scenario_text@v1",
        supporting_artifact_count=0,
        question_count=2,
    )

    with pytest.raises(Exception) as exc_info:
        _validate_generated_scenario_draft(draft=draft, plan=plan)

    assert "SS-VALIDATION-089" in str(exc_info.value)
