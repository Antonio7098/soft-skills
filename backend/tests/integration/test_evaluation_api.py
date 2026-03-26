from __future__ import annotations

from pathlib import Path

import pytest
from alembic.config import Config

from alembic import command
from soft_skills_backend.platform.db.models import (
    EvaluationCaseResultRecord,
    EvaluationRunRecord,
    WorkflowEventRecord,
)
from soft_skills_backend.shared.ports.models import ProviderCompletion


def _migrate(test_settings) -> None:
    alembic_config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    alembic_config.set_main_option("sqlalchemy.url", test_settings.database_url)
    command.upgrade(alembic_config, "head")


async def _register_user(client, *, email: str, display_name: str, role: str = "standard_user"):
    response = await client.post(
        "/api/auth/register",
        json={
            "email": email,
            "display_name": display_name,
            "role": role,
            "target_role": "Consultant",
            "goals": ["Improve stakeholder handling"],
            "practice_preferences": {"session_length": "short"},
        },
    )
    assert response.status_code == 200
    return response.json()["data"]


class FakeEvaluationProvider:
    def __init__(self, model_slug: str) -> None:
        self._model_slug = model_slug

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_slug(self) -> str:
        return self._model_slug

    async def complete_json(self, *, messages, call_context) -> ProviderCompletion:
        del call_context
        content = "\n".join(str(message.get("content", "")) for message in messages)
        if "I hear why the date matters to you" in content:
            payload = {
                "prompt_version": "assessment.quick-practice.v1",
                "rubric_version": "v1",
                "provider": "openai",
                "model_slug": self._model_slug,
                "overall_score": 4,
                "rationale": "The response paired empathy with a realistic boundary.",
                "skill_scores": [
                    {
                        "skill_slug": "active-listening",
                        "score": 4,
                        "rationale": "It acknowledged the concern directly.",
                    },
                    {
                        "skill_slug": "expectation-setting",
                        "score": 3,
                        "rationale": "It set a realistic next step.",
                    },
                ],
                "evidence": [
                    {
                        "skill_slug": "active-listening",
                        "quote": "I hear why the date matters to you.",
                        "explanation": "The response starts by acknowledging the pressure.",
                    },
                    {
                        "skill_slug": "expectation-setting",
                        "quote": "The earliest realistic delivery date is next Friday,",
                        "explanation": "It sets a concrete boundary and timing.",
                    },
                ],
                "strengths": ["Empathetic acknowledgement before the boundary."],
                "weaknesses": ["Could name ownership slightly more clearly."],
                "next_actions": ["Keep practicing direct boundary setting."],
            }
        elif "I understand why you want the full scope this week" in content:
            payload = {
                "prompt_version": "assessment.quick-practice.v1",
                "rubric_version": "v1",
                "provider": "openai",
                "model_slug": self._model_slug,
                "overall_score": 4,
                "rationale": "The response preserves trust while proposing a concrete tradeoff.",
                "skill_scores": [
                    {
                        "skill_slug": "active-listening",
                        "score": 4,
                        "rationale": "It recognizes the sponsor priority.",
                    },
                    {
                        "skill_slug": "expectation-setting",
                        "score": 4,
                        "rationale": "It proposes a realistic scope boundary with a checkpoint.",
                    },
                ],
                "evidence": [
                    {
                        "skill_slug": "active-listening",
                        "quote": "I understand why you want the full scope this week.",
                        "explanation": "The response names the stakeholder goal first.",
                    },
                    {
                        "skill_slug": "expectation-setting",
                        "quote": "we should ship the core reporting flow first",
                        "explanation": "The response narrows scope to preserve the date.",
                    },
                ],
                "strengths": ["Balanced trust and realism."],
                "weaknesses": ["Could mention the downside of the tradeoff more explicitly."],
                "next_actions": ["Keep naming checkpoint owners in tradeoff conversations."],
            }
        else:
            payload = {
                "prompt_version": "assessment.quick-practice.v1",
                "rubric_version": "v1",
                "provider": "openai",
                "model_slug": self._model_slug,
                "overall_score": 2,
                "rationale": "The response is empathetic but vague about delivery.",
                "skill_scores": [
                    {
                        "skill_slug": "active-listening",
                        "score": 2,
                        "rationale": "It recognizes urgency in general terms.",
                    },
                    {
                        "skill_slug": "expectation-setting",
                        "score": 1,
                        "rationale": "It avoids giving a concrete boundary.",
                    },
                ],
                "evidence": [
                    {
                        "skill_slug": "active-listening",
                        "quote": "I know this is important",
                        "explanation": "The response acknowledges urgency.",
                    },
                    {
                        "skill_slug": "expectation-setting",
                        "quote": "I will keep you posted.",
                        "explanation": "The response stays vague instead of setting a boundary.",
                    },
                ],
                "strengths": ["Shows some empathy."],
                "weaknesses": ["Does not provide a concrete commitment or boundary."],
                "next_actions": ["Practice naming realistic dates and tradeoffs."],
            }
        usage = {
            "prompt_tokens": 120 if self._model_slug == "model-a" else 140,
            "completion_tokens": 40 if self._model_slug == "model-a" else 55,
            "total_tokens": 160 if self._model_slug == "model-a" else 195,
        }
        return ProviderCompletion(
            content=payload,
            model_slug=self._model_slug,
            usage=usage,
            raw_response={"provider": "openai", "model": self._model_slug},
        )


def _fake_provider_factory(settings, provider_call_logger):
    del provider_call_logger
    model_slug = settings.llm_marking_model or settings.provider_model_slug
    return FakeEvaluationProvider(model_slug)


@pytest.mark.asyncio
async def test_admin_evaluation_run_persists_provider_backed_golden_results(
    app, client, test_settings
) -> None:
    _migrate(test_settings)
    admin = await _register_user(
        client,
        email="admin-evaluation@example.com",
        display_name="Admin Evaluation",
        role="admin",
    )
    app.state.container.evaluation_service.set_provider_factory(_fake_provider_factory)

    suites_response = await client.get(
        "/api/admin/evaluations/suites",
        headers={"X-User-ID": admin["id"]},
    )
    assert suites_response.status_code == 200
    assert {item["suite_id"] for item in suites_response.json()["data"]} == {
        "marking_benchmark_v1"
    }

    run_response = await client.post(
        "/api/admin/evaluations/runs",
        headers={"X-User-ID": admin["id"]},
        json={
            "suite_id": "marking_benchmark_v1",
            "model_slugs": ["model-a", "model-b"],
            "case_ids": ["stakeholder-reset-01", "scope-tradeoff-02"],
        },
    )
    assert run_response.status_code == 200
    payload = run_response.json()["data"]
    assert payload["status"] == "completed"
    assert payload["passed"] is True
    assert payload["summary"]["dataset_version"] == "marking-golden-dataset.v1"
    assert payload["summary"]["model_slugs"] == ["model-a", "model-b"]
    assert payload["summary"]["selected_case_count"] == 2
    assert payload["aggregate_metrics"]["case_count"] == 4
    assert payload["aggregate_metrics"]["total_tokens"] == 710
    assert payload["release_decision"] is None
    run_id = payload["evaluation_run_id"]

    get_response = await client.get(
        f"/api/admin/evaluations/runs/{run_id}",
        headers={"X-User-ID": admin["id"]},
    )
    assert get_response.status_code == 200
    assert get_response.json()["data"]["evaluation_run_id"] == run_id

    with app.state.container.session_factory() as session:
        run_record = session.get(EvaluationRunRecord, run_id)
        case_result_count = (
            session.query(EvaluationCaseResultRecord)
            .filter(EvaluationCaseResultRecord.evaluation_run_id == run_id)
            .count()
        )
        event_types = {record.event_type for record in session.query(WorkflowEventRecord).all()}

    assert run_record is not None
    assert case_result_count == 4
    assert "evaluation.run.completed.v1" in event_types
