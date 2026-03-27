from __future__ import annotations

import pytest

from soft_skills_backend.modules.practice.domain.practice import (
    AssessmentDraft,
    AttemptStatus,
    ensure_attempt_transition,
    validate_assessment_draft,
)
from soft_skills_backend.modules.practice.workflows.assessment import TypedLLMOutput
from soft_skills_backend.shared.errors import AppError
from soft_skills_backend.shared.ports.llm import (
    ProviderCallContext,
    ProviderCompletion,
)


class FakeProvider:
    def __init__(self, responses: list[str | dict[str, object]]) -> None:
        self._responses = responses
        self.calls = 0

    async def complete_json(
        self,
        *,
        messages: list[dict[str, str]],
        call_context: ProviderCallContext,
    ) -> ProviderCompletion:
        del messages, call_context
        self.calls += 1
        response = self._responses.pop(0)
        return ProviderCompletion(
            content=response,
            model_slug="gpt-4.1-mini",
        )


def _draft(**overrides: object) -> AssessmentDraft:
    payload: dict[str, object] = {
        "prompt_version": "assessment.quick-practice.v1",
        "rubric_version": "v1",
        "provider": "openai",
        "model_slug": "gpt-4.1-mini",
        "overall_score": 4,
        "rationale": "The response was calm, direct, and set a realistic next step.",
        "skill_scores": [
            {
                "skill_slug": "active-listening",
                "score": 4,
                "rationale": "It acknowledged the client concern.",
            },
            {
                "skill_slug": "expectation-setting",
                "score": 4,
                "rationale": "It reset the timeline credibly.",
            },
        ],
        "evidence": [
            {
                "skill_slug": "active-listening",
                "quote": "I hear why the deadline matters to you",
                "explanation": "The learner acknowledged the stakeholder concern explicitly.",
            },
            {
                "skill_slug": "expectation-setting",
                "quote": "The earliest realistic date is next Friday",
                "explanation": "The learner set a specific, realistic boundary.",
            },
        ],
        "strengths": ["Acknowledged the client concern clearly."],
        "weaknesses": ["Could have offered one more contingency if timing moved again."],
        "next_actions": ["Practice pairing empathy with one backup option."],
    }
    payload.update(overrides)
    return AssessmentDraft.model_validate(payload)


def test_attempt_transition_rejects_invalid_resubmission() -> None:
    with pytest.raises(AppError) as exc_info:
        ensure_attempt_transition(AttemptStatus.ASSESSED.value, AttemptStatus.SUBMITTED)

    assert exc_info.value.code == "SS-DOMAIN-009"


def test_assessment_draft_requires_direct_evidence_quotes() -> None:
    with pytest.raises(AppError) as exc_info:
        validate_assessment_draft(
            response_text=(
                "I hear why the deadline matters to you, and the earliest realistic date is next Friday."
            ),
            required_skill_slugs=["active-listening", "expectation-setting"],
            draft=_draft(
                evidence=[
                    {
                        "skill_slug": "active-listening",
                        "quote": "You handled it well",
                        "explanation": "This was generic praise rather than direct evidence.",
                    }
                ]
            ),
        )

    assert exc_info.value.code == "SS-SCORING-004"


def test_assessment_draft_rejects_contradictory_feedback() -> None:
    with pytest.raises(AppError) as exc_info:
        validate_assessment_draft(
            response_text=(
                "I hear why the deadline matters to you, and the earliest realistic date is next Friday."
            ),
            required_skill_slugs=["active-listening", "expectation-setting"],
            draft=_draft(
                strengths=["Reset the timeline clearly."],
                weaknesses=["Reset the timeline clearly."],
            ),
        )

    assert exc_info.value.code == "SS-SCORING-005"


def test_assessment_draft_rejects_inconsistent_overall_score() -> None:
    with pytest.raises(AppError) as exc_info:
        validate_assessment_draft(
            response_text=(
                "I hear why the deadline matters to you, and the earliest realistic date is next Friday."
            ),
            required_skill_slugs=["active-listening", "expectation-setting"],
            draft=_draft(
                overall_score=1,
                skill_scores=[
                    {
                        "skill_slug": "active-listening",
                        "score": 5,
                        "rationale": "Strong empathy.",
                    },
                    {
                        "skill_slug": "expectation-setting",
                        "score": 5,
                        "rationale": "Strong boundary setting.",
                    },
                ],
            ),
        )

    assert exc_info.value.code == "SS-SCORING-006"


@pytest.mark.skip(
    reason="Function _model_slug_matches_execution_source was removed during refactoring"
)
def test_model_slug_match_accepts_provider_normalized_slug() -> None:
    pass


@pytest.mark.asyncio
async def test_typed_llm_output_retries_invalid_json_once() -> None:
    typed_output = TypedLLMOutput(
        AssessmentDraft,
        schema_version="quick-practice-assessment-output.v1",
        max_validation_retries=1,
    )
    provider = FakeProvider(
        responses=[
            '{"not": "valid"}',
            {
                "prompt_version": "assessment.quick-practice.v1",
                "rubric_version": "v1",
                "provider": "openai",
                "model_slug": "gpt-4.1-mini",
                "overall_score": 4,
                "rationale": "The response was solid.",
                "skill_scores": [
                    {
                        "skill_slug": "active-listening",
                        "score": 4,
                        "rationale": "Good empathy.",
                    }
                ],
                "evidence": [
                    {
                        "skill_slug": "active-listening",
                        "quote": "I hear why the deadline matters to you",
                        "explanation": "Direct acknowledgement.",
                    }
                ],
                "strengths": ["Acknowledged the concern."],
                "weaknesses": ["Could tighten the closing ask."],
                "next_actions": ["Practice ending with one concrete checkpoint."],
            },
        ]
    )

    result = await typed_output.generate(
        provider,  # type: ignore[arg-type]
        messages=[{"role": "user", "content": "Assess this"}],
        call_context=ProviderCallContext(
            operation="quick_practice_assessment",
            pipeline_run_id="run-1",
            request_id="req-1",
            trace_id="trace-1",
            workflow_id="workflow-1",
            user_id="user-1",
        ),
    )

    assert provider.calls == 2
    assert result.schema_version == "quick-practice-assessment-output.v1"
    assert result.parsed.model_dump()["prompt_version"] == "assessment.quick-practice.v1"
