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
    command.upgrade(alembic_config, "heads")


async def _register_user(client, *, email: str, display_name: str):
    response = await client.post(
        "/api/auth/register",
        json={
            "email": email,
            "display_name": display_name,
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

    async def complete_json(
        self,
        *,
        messages,
        call_context,
        response_schema=None,
        timeout_seconds=None,
    ) -> ProviderCompletion:
        del response_schema, timeout_seconds
        content = "\n".join(str(message.get("content", "")) for message in messages)
        operation = call_context.operation
        if operation.endswith(":aggregation"):
            if "manual approval bottleneck" in content:
                payload: dict[str, object] = {
                    "summary": "The response aligned with the interviewer concern and justified the recommendation with clear tradeoffs.",
                    "next_actions": [
                        "Keep naming the key tradeoff before defending the recommendation."
                    ],
                }
            else:
                payload = {
                    "summary": "The response protected the launch date and set a realistic follow-through plan.",
                    "next_actions": [
                        "Keep stating what ships now and when deferred work will be revisited."
                    ],
                }
        else:
            skill_slug = operation.rsplit(":", 1)[-1]
            if "I hear why the date matters to you" in content:
                payload = {
                    "skill_slug": skill_slug,
                    "score": 2,
                    "rationale": "The response acknowledges the pressure and sets a realistic next step.",
                    "evidence": [
                        {
                            "quote": (
                                "I hear why the date matters to you."
                                if skill_slug == "active-listening"
                                else "The earliest realistic delivery date is next Friday,"
                            ),
                            "explanation": (
                                "The response directly acknowledges the stakeholder concern."
                                if skill_slug == "active-listening"
                                else "The response sets a concrete, realistic boundary."
                            ),
                        }
                    ],
                }
            elif "I know this is important and I will do my best to make it happen." in content:
                payload = {
                    "skill_slug": skill_slug,
                    "score": 1,
                    "rationale": "The response stays vague and does not create a usable boundary.",
                    "evidence": [
                        {
                            "quote": (
                                "I know this is important"
                                if skill_slug == "active-listening"
                                else "I will keep you posted."
                            ),
                            "explanation": (
                                "The response only gestures at urgency."
                                if skill_slug == "active-listening"
                                else "The response avoids a concrete next step."
                            ),
                        }
                    ],
                }
            elif "manual approval bottleneck" in content:
                payload = {
                    "skill_slug": skill_slug,
                    "score": 5 if skill_slug == "decision-justification" else 4,
                    "rationale": (
                        "The response explains the recommendation with explicit tradeoffs."
                        if skill_slug == "decision-justification"
                        else "The response reflects the interviewer concern before answering."
                    ),
                    "evidence": [
                        {
                            "quote": (
                                "the real concern is whether the extra spend buys us a meaningful reduction in delivery risk"
                                if skill_slug == "active-listening"
                                else "I would recommend the proposal because it removes the manual approval bottleneck"
                            ),
                            "explanation": (
                                "The answer identifies what the interviewer is actually asking about."
                                if skill_slug == "active-listening"
                                else "The answer defends the recommendation with concrete reasoning."
                            ),
                        }
                    ],
                }
            else:
                payload = {
                    "skill_slug": skill_slug,
                    "score": 5 if skill_slug == "expectation-setting" else 4,
                    "rationale": (
                        "The response sets a precise plan for what ships next and when the team will reconfirm."
                        if skill_slug == "expectation-setting"
                        else "The response makes a strong prioritization decision under deadline pressure."
                    ),
                    "evidence": [
                        {
                            "quote": (
                                "To protect the launch date, I would cut the custom export from this release"
                                if skill_slug == "prioritization-under-pressure"
                                else "set a checkpoint tomorrow afternoon to confirm the revised customer communication"
                            ),
                            "explanation": (
                                "The answer protects the deadline by cutting lower-value scope."
                                if skill_slug == "prioritization-under-pressure"
                                else "The answer sets a concrete follow-through checkpoint."
                            ),
                        }
                    ],
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
    model_slug = settings.llm_marking_per_skill_model or settings.llm_default_model
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
    )
    app.state.container.evaluation_service.set_provider_factory(_fake_provider_factory)

    suites_response = await client.get(
        "/api/admin/evaluations/suites",
        headers={"X-User-ID": admin["id"]},
    )
    assert suites_response.status_code == 200
    actual_suites = {item["suite_id"] for item in suites_response.json()["data"]}
    assert "marking_benchmark_v1" in actual_suites
    assert "quick_practice_benchmark_v1" in actual_suites

    run_response = await client.post(
        "/api/admin/evaluations/runs",
        headers={"X-User-ID": admin["id"]},
        json={
            "suite_id": "marking_benchmark_v1",
            "model_slugs": ["model-a", "model-b"],
            "case_ids": ["interview-pushback-01", "scenario-launch-tradeoff-02"],
        },
    )
    assert run_response.status_code == 200
    payload = run_response.json()["data"]
    assert payload["status"] == "completed"
    assert payload["passed"] is True
    assert payload["summary"]["dataset_version"] == "marking-golden-dataset.v2"
    assert payload["summary"]["model_slugs"] == ["model-a", "model-b"]
    assert payload["summary"]["selected_case_count"] == 2
    assert payload["aggregate_metrics"]["case_count"] == 4
    assert payload["aggregate_metrics"]["total_tokens"] == 2130
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


@pytest.mark.asyncio
async def test_admin_quick_practice_evaluation_suite_runs_with_binary_expectations(
    app, client, test_settings
) -> None:
    _migrate(test_settings)
    admin = await _register_user(
        client,
        email="admin-quick-evaluation@example.com",
        display_name="Admin Quick Evaluation",
    )
    app.state.container.evaluation_service.set_provider_factory(_fake_provider_factory)

    run_response = await client.post(
        "/api/admin/evaluations/runs",
        headers={"X-User-ID": admin["id"]},
        json={
            "suite_id": "quick_practice_benchmark_v1",
            "model_slugs": ["model-a"],
            "case_ids": ["quick-reset-deadline-01", "quick-vague-reassurance-02"],
        },
    )
    assert run_response.status_code == 200
    payload = run_response.json()["data"]
    assert payload["status"] == "completed"
    assert payload["passed"] is True
    assert payload["summary"]["dataset_version"] == "quick-practice-golden-dataset.v1"
    assert payload["summary"]["selected_case_count"] == 2
    assert payload["aggregate_metrics"]["case_count"] == 2
    assert payload["aggregate_metrics"]["total_tokens"] == 640


@pytest.mark.asyncio
async def test_admin_evaluation_dashboard_empty(app, client, test_settings) -> None:
    _migrate(test_settings)
    admin = await _register_user(
        client,
        email="admin-dashboard@example.com",
        display_name="Admin Dashboard",
    )

    response = await client.get(
        "/api/admin/evaluations/dashboard",
        headers={"X-User-ID": admin["id"]},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total_runs"] == 0
    assert data["total_cases"] == 0
    assert data["pass_fail"]["total_runs"] == 0


@pytest.mark.asyncio
async def test_admin_evaluation_dashboard_after_runs(app, client, test_settings) -> None:
    _migrate(test_settings)
    admin = await _register_user(
        client,
        email="admin-dashboard-runs@example.com",
        display_name="Admin Dashboard Runs",
    )
    app.state.container.evaluation_service.set_provider_factory(_fake_provider_factory)

    run_response = await client.post(
        "/api/admin/evaluations/runs",
        headers={"X-User-ID": admin["id"]},
        json={
            "suite_id": "marking_benchmark_v1",
            "model_slugs": ["model-a"],
            "case_ids": ["interview-pushback-01"],
        },
    )
    assert run_response.status_code == 200

    dashboard_response = await client.get(
        "/api/admin/evaluations/dashboard",
        headers={"X-User-ID": admin["id"]},
    )
    assert dashboard_response.status_code == 200
    data = dashboard_response.json()["data"]
    assert data["total_runs"] >= 1
    assert data["pass_fail"]["total_runs"] >= 1
    assert "marking_benchmark_v1" in data["suite_breakdown"]


@pytest.mark.asyncio
async def test_admin_evaluation_compare_runs(app, client, test_settings) -> None:
    _migrate(test_settings)
    admin = await _register_user(
        client,
        email="admin-compare@example.com",
        display_name="Admin Compare",
    )
    app.state.container.evaluation_service.set_provider_factory(_fake_provider_factory)

    run_response = await client.post(
        "/api/admin/evaluations/runs",
        headers={"X-User-ID": admin["id"]},
        json={
            "suite_id": "marking_benchmark_v1",
            "model_slugs": ["model-a"],
            "case_ids": ["interview-pushback-01"],
        },
    )
    assert run_response.status_code == 200
    run_id = run_response.json()["data"]["evaluation_run_id"]

    compare_response = await client.get(
        "/api/admin/evaluations/runs/compare",
        headers={"X-User-ID": admin["id"]},
    )
    assert compare_response.status_code == 200
    data = compare_response.json()["data"]
    assert data["run_count"] >= 1
    assert any(r["evaluation_run_id"] == run_id for r in data["runs"])


@pytest.mark.asyncio
async def test_admin_evaluation_benchmark(app, client, test_settings) -> None:
    _migrate(test_settings)
    admin = await _register_user(
        client,
        email="admin-benchmark@example.com",
        display_name="Admin Benchmark",
    )
    app.state.container.evaluation_service.set_provider_factory(_fake_provider_factory)

    await client.post(
        "/api/admin/evaluations/runs",
        headers={"X-User-ID": admin["id"]},
        json={
            "suite_id": "marking_benchmark_v1",
            "model_slugs": ["model-a", "model-b"],
            "case_ids": ["interview-pushback-01"],
        },
    )

    benchmark_response = await client.get(
        "/api/admin/evaluations/benchmark",
        headers={"X-User-ID": admin["id"]},
    )
    assert benchmark_response.status_code == 200
    data = benchmark_response.json()["data"]
    assert data["total_runs"] >= 1
    assert len(data["models"]) >= 1


@pytest.mark.asyncio
async def test_admin_evaluation_case_detail_not_found(app, client, test_settings) -> None:
    _migrate(test_settings)
    admin = await _register_user(
        client,
        email="admin-case-detail@example.com",
        display_name="Admin Case Detail",
    )

    response = await client.get(
        "/api/admin/evaluations/cases/nonexistent-case",
        headers={"X-User-ID": admin["id"]},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SS-DOMAIN-033"
