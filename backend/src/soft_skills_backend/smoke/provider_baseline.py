"""Real-provider smoke harness for all MVP text practice modes."""

from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import cast
from uuid import uuid4

import httpx
from alembic.config import Config
from pydantic import BaseModel

from alembic import command
from soft_skills_backend.app import create_app
from soft_skills_backend.config import Settings, get_settings
from soft_skills_backend.domain.errors import AppError, provider_error, validation_error
from soft_skills_backend.integrations.llm.openai_compatible import OpenAICompatibleLLMProvider

SMOKE_PROVIDER_TIMEOUT_SECONDS = 30.0
SMOKE_FLOW_TIMEOUT_SECONDS = 120.0


class PracticeModeSmokeResult(BaseModel):
    """Result for one practice mode in the smoke flow."""

    practice_type: str
    provider: str
    model_slug: str
    assessment_id: str
    attempt_id: str
    overall_score: int


class ProviderSmokeResult(BaseModel):
    """Result of the end-to-end provider smoke flow."""

    status: str
    results: list[PracticeModeSmokeResult]


def run_provider_smoke(settings: Settings | None = None) -> ProviderSmokeResult:
    """Exercise the full text-practice backend flow against the real provider."""

    resolved_settings = settings or get_settings()
    try:
        _build_smoke_provider(resolved_settings).assert_configured()
    except AppError as exc:
        raise validation_error(
            "Provider API key is required for smoke coverage",
            code="SS-VALIDATION-002",
        ) from exc

    try:
        return asyncio.run(
            asyncio.wait_for(
                _run_text_practice_smoke(resolved_settings), timeout=SMOKE_FLOW_TIMEOUT_SECONDS
            )
        )
    except TimeoutError as exc:
        raise provider_error(
            "Smoke flow exceeded the allowed runtime budget",
            code="SS-PROVIDER-012",
            details={"timeout_seconds": SMOKE_FLOW_TIMEOUT_SECONDS},
        ) from exc


async def _run_text_practice_smoke(settings: Settings) -> ProviderSmokeResult:
    with TemporaryDirectory(prefix="soft-skills-smoke-") as temp_dir:
        database_path = Path(temp_dir) / "smoke.db"
        smoke_settings = settings.model_copy(
            update={
                "environment": "test",
                "database_url": f"sqlite+pysqlite:///{database_path}",
                "smoke_timeout_seconds": SMOKE_PROVIDER_TIMEOUT_SECONDS,
                "provider_max_retries": 0,
                "assessment_validation_retries": 0,
            }
        )
        app = create_app(smoke_settings)
        _migrate(smoke_settings)

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            suffix = uuid4().hex[:8]
            admin = await _register_user(
                client,
                email=f"admin-smoke-{suffix}@example.com",
                display_name="Smoke Admin",
                role="admin",
            )
            bootstrap_response = await client.post(
                "/api/skills/bootstrap-canon",
                headers={"X-User-ID": str(admin["id"])},
            )
            _require_ok(bootstrap_response, "bootstrap canon")

            learner = await _register_user(
                client,
                email=f"learner-smoke-{suffix}@example.com",
                display_name="Smoke Learner",
            )
            learner_id = str(learner["id"])

            quick_prompt = await _seed_quick_practice_prompt(client, learner_id)
            interview_prompt = await _seed_interview_prompt(client, learner_id)
            scenario = await _seed_scenario(client, learner_id)

            results = [
                await _run_quick_practice_mode(client, learner_id, str(quick_prompt["id"])),
                await _run_interview_mode(client, learner_id, str(interview_prompt["id"])),
                await _run_scenario_mode(client, learner_id, str(scenario["id"])),
            ]
            return ProviderSmokeResult(status="ok", results=results)


async def _run_quick_practice_mode(
    client: httpx.AsyncClient, user_id: str, prompt_id: str
) -> PracticeModeSmokeResult:
    start_response = await client.post(
        "/api/attempts/quick-practice/sessions",
        headers={"X-User-ID": user_id},
        json={"prompt_item_id": prompt_id},
    )
    _require_ok(start_response, "start quick-practice session")
    attempt_id = start_response.json()["data"]["attempt_id"]

    submit_response = await client.post(
        f"/api/attempts/{attempt_id}/submit",
        headers={"X-User-ID": user_id},
        json={
            "response_text": (
                "I hear why the date matters to you. The earliest realistic date is next Friday, "
                "and I can confirm any scope tradeoffs with the team by tomorrow afternoon."
            )
        },
    )
    return _extract_assessment_result(
        submit_response, "submit quick-practice attempt", "quick_practice"
    )


async def _run_interview_mode(
    client: httpx.AsyncClient, user_id: str, prompt_id: str
) -> PracticeModeSmokeResult:
    start_response = await client.post(
        "/api/attempts/interview/sessions",
        headers={"X-User-ID": user_id},
        json={
            "prompt_item_id": prompt_id,
            "competency_context": "Assess structured communication, tradeoff handling, and ownership.",
            "interviewer_perspective": "You are responding to a consulting hiring manager.",
        },
    )
    _require_ok(start_response, "start interview session")
    attempt_id = start_response.json()["data"]["attempt_id"]

    submit_response = await client.post(
        f"/api/attempts/{attempt_id}/submit",
        headers={"X-User-ID": user_id},
        json={
            "response_text": (
                "I led the decision by surfacing the uncertainty clearly, aligning the team on the tradeoff, "
                "and setting a next-morning checkpoint with a named owner."
            )
        },
    )
    return _extract_assessment_result(submit_response, "submit interview attempt", "interview")


async def _run_scenario_mode(
    client: httpx.AsyncClient, user_id: str, scenario_id: str
) -> PracticeModeSmokeResult:
    start_response = await client.post(
        "/api/attempts/scenario/sessions",
        headers={"X-User-ID": user_id},
        json={
            "scenario_id": scenario_id,
            "artifacts": [
                {
                    "artifact_type": "email",
                    "title": "Board escalation note",
                    "body": "The board expects a recommendation before 9am tomorrow.",
                }
            ],
        },
    )
    _require_ok(start_response, "start scenario session")
    attempt_id = start_response.json()["data"]["attempt_id"]

    submit_response = await client.post(
        f"/api/attempts/{attempt_id}/submit",
        headers={"X-User-ID": user_id},
        json={
            "response_text": (
                "I would recommend a one-day delay, explain the legal risk directly, "
                "and propose a 7am checkpoint with sales and legal before the board meeting."
            )
        },
    )
    return _extract_assessment_result(submit_response, "submit scenario attempt", "scenario")


def _extract_assessment_result(
    response: httpx.Response, operation: str, practice_type: str
) -> PracticeModeSmokeResult:
    _require_ok(response, operation)
    attempt = response.json()["data"]
    assessment = attempt["assessment"]
    if assessment is None:
        raise provider_error(
            "Smoke assessment did not return a learner-facing artifact",
            code="SS-PROVIDER-010",
            details={"practice_type": practice_type, "attempt_id": attempt["id"]},
        )
    return PracticeModeSmokeResult(
        practice_type=practice_type,
        provider=str(assessment["provider"]),
        model_slug=str(assessment["model_slug"]),
        assessment_id=str(assessment["assessment_id"]),
        attempt_id=str(attempt["id"]),
        overall_score=int(assessment["overall_score"]),
    )


async def _register_user(
    client: httpx.AsyncClient,
    *,
    email: str,
    display_name: str,
    role: str = "standard_user",
) -> dict[str, object]:
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
    _require_ok(response, "register user")
    return cast(dict[str, object], response.json()["data"])


async def _create_collection(
    client: httpx.AsyncClient,
    *,
    user_id: str,
    title: str,
    content_format_mix: list[str],
    target_skill_slugs: list[str],
    target_competency_slugs: list[str],
    rubric_ids: list[str],
) -> str:
    collection_response = await client.post(
        "/api/collections",
        headers={"X-User-ID": user_id},
        json={
            "title": title,
            "summary": f"{title} smoke content.",
            "target_audience": "Early-career consultants",
            "difficulty": "intermediate",
            "content_format_mix": content_format_mix,
            "target_skill_slugs": target_skill_slugs,
            "target_competency_slugs": target_competency_slugs,
            "rubric_ids": rubric_ids,
        },
    )
    _require_ok(collection_response, f"create collection {title}")
    return str(collection_response.json()["data"]["id"])


async def _seed_quick_practice_prompt(client: httpx.AsyncClient, user_id: str) -> dict[str, object]:
    collection_id = await _create_collection(
        client,
        user_id=user_id,
        title="Smoke Quick Practice",
        content_format_mix=["quick_practice_prompt"],
        target_skill_slugs=["active-listening", "expectation-setting"],
        target_competency_slugs=["stakeholder-management"],
        rubric_ids=["quick_practice_text@v1"],
    )
    prompt_response = await client.post(
        f"/api/collections/{collection_id}/prompt-items",
        headers={"X-User-ID": user_id},
        json={
            "prompt_type": "quick_practice_prompt",
            "title": "Reset the timeline",
            "prompt_text": (
                "A client asks for an impossible delivery date. Respond with empathy and a realistic next step."
            ),
            "difficulty": "intermediate",
            "target_skill_slugs": ["active-listening", "expectation-setting"],
            "rubric_id": "quick_practice_text@v1",
        },
    )
    _require_ok(prompt_response, "create quick-practice prompt item")
    return cast(dict[str, object], prompt_response.json()["data"])


async def _seed_interview_prompt(client: httpx.AsyncClient, user_id: str) -> dict[str, object]:
    collection_id = await _create_collection(
        client,
        user_id=user_id,
        title="Smoke Interview Practice",
        content_format_mix=["interview_prompt"],
        target_skill_slugs=["active-listening", "decision-justification"],
        target_competency_slugs=["adaptability"],
        rubric_ids=["interview_text@v1"],
    )
    prompt_response = await client.post(
        f"/api/collections/{collection_id}/prompt-items",
        headers={"X-User-ID": user_id},
        json={
            "prompt_type": "interview_prompt",
            "title": "Lead through ambiguity",
            "prompt_text": "Tell me about a time you had to make a decision with incomplete information.",
            "difficulty": "intermediate",
            "target_skill_slugs": ["active-listening", "decision-justification"],
            "rubric_id": "interview_text@v1",
        },
    )
    _require_ok(prompt_response, "create interview prompt item")
    return cast(dict[str, object], prompt_response.json()["data"])


async def _seed_scenario(client: httpx.AsyncClient, user_id: str) -> dict[str, object]:
    collection_id = await _create_collection(
        client,
        user_id=user_id,
        title="Smoke Scenario Practice",
        content_format_mix=["scenario_step"],
        target_skill_slugs=["expectation-setting", "prioritization-under-pressure"],
        target_competency_slugs=["managing-ambiguity"],
        rubric_ids=["scenario_text@v1"],
    )
    scenario_response = await client.post(
        f"/api/collections/{collection_id}/scenarios",
        headers={"X-User-ID": user_id},
        json={
            "title": "Escalating launch risk",
            "business_context": "An AI feature launch is at risk after legal review surfaced new concerns.",
            "learner_objective": "Re-align the sponsor without hiding delivery risk.",
            "constraints": ["The launch date is on the board agenda tomorrow."],
            "stakeholder_tensions": ["Legal wants a delay and sales wants the current date."],
            "target_skill_slugs": ["expectation-setting", "prioritization-under-pressure"],
            "rubric_id": "scenario_text@v1",
            "mock_company": {
                "name": "Northstar AI",
                "industry": "Enterprise SaaS",
                "operating_context": "Scaling quickly under board scrutiny.",
            },
            "mock_people": [
                {
                    "name": "Maya Chen",
                    "role": "VP Sales",
                    "goals": ["Keep the launch date"],
                    "communication_style": "Direct and urgent",
                    "relationship_to_scenario": "Commercial sponsor pushing for launch",
                },
                {
                    "name": "Jordan Singh",
                    "role": "Legal Counsel",
                    "goals": ["Reduce regulatory exposure"],
                    "communication_style": "Precise and cautious",
                    "relationship_to_scenario": "Risk owner blocking approval",
                },
            ],
        },
    )
    _require_ok(scenario_response, "create scenario")
    return cast(dict[str, object], scenario_response.json()["data"])


def _migrate(settings: Settings) -> None:
    alembic_config = Config(str(Path(__file__).resolve().parents[3] / "alembic.ini"))
    alembic_config.set_main_option("sqlalchemy.url", settings.database_url)
    command.upgrade(alembic_config, "head")


def _require_ok(response: httpx.Response, operation: str) -> None:
    if response.status_code == 200:
        return
    raise provider_error(
        "Smoke backend step failed",
        code="SS-PROVIDER-011",
        details={
            "operation": operation,
            "status_code": response.status_code,
            "body": response.text,
        },
    )


def _build_smoke_provider(settings: Settings) -> OpenAICompatibleLLMProvider:
    return OpenAICompatibleLLMProvider(
        settings=settings,
        provider_call_logger=_NoOpProviderCallLogger(),
    )


class _NoOpProviderCallLogger:
    async def log_call_start(self, **_: object) -> str:
        return "smoke-preflight"

    async def log_call_end(self, _call_id: object, **_: object) -> None:
        return None


def main() -> None:
    """CLI entrypoint."""

    result = run_provider_smoke()
    print(result.model_dump_json())


if __name__ == "__main__":
    main()
