"""Real-provider quick-practice smoke harness."""

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
from soft_skills_backend.integrations.llm.openai_compatible import (
    OpenAICompatibleLLMProvider,
)

SMOKE_PROVIDER_TIMEOUT_SECONDS = 15.0
SMOKE_FLOW_TIMEOUT_SECONDS = 25.0


class ProviderSmokeResult(BaseModel):
    """Result of the end-to-end provider smoke flow."""

    provider: str
    status: str
    model_slug: str
    assessment_id: str
    attempt_id: str
    overall_score: int


def run_provider_smoke(settings: Settings | None = None) -> ProviderSmokeResult:
    """Exercise the full quick-practice backend flow against the real provider."""

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
                _run_quick_practice_smoke(resolved_settings),
                timeout=SMOKE_FLOW_TIMEOUT_SECONDS,
            )
        )
    except TimeoutError as exc:
        raise provider_error(
            "Smoke flow exceeded the allowed runtime budget",
            code="SS-PROVIDER-012",
            details={"timeout_seconds": SMOKE_FLOW_TIMEOUT_SECONDS},
        ) from exc


async def _run_quick_practice_smoke(settings: Settings) -> ProviderSmokeResult:
    with TemporaryDirectory(prefix="soft-skills-smoke-") as temp_dir:
        database_path = Path(temp_dir) / "smoke.db"
        smoke_settings = settings.model_copy(
            update={
                "environment": "test",
                "database_url": f"sqlite+pysqlite:///{database_path}",
                "stageflow_required": False,
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
            prompt = await _seed_prompt(client, str(learner["id"]))

            start_response = await client.post(
                "/api/attempts/quick-practice/sessions",
                headers={"X-User-ID": str(learner["id"])},
                json={"prompt_item_id": prompt["id"]},
            )
            _require_ok(start_response, "start quick-practice session")
            attempt_id = start_response.json()["data"]["attempt_id"]

            submit_response = await client.post(
                f"/api/attempts/{attempt_id}/submit",
                headers={"X-User-ID": str(learner["id"])},
                json={
                    "response_text": (
                        "I hear why the date matters to you. The earliest realistic date is next Friday, "
                        "and I can confirm any scope tradeoffs with the team by tomorrow afternoon."
                    )
                },
            )
            _require_ok(submit_response, "submit quick-practice attempt")
            assessment = submit_response.json()["data"]["assessment"]
            if assessment is None:
                raise provider_error(
                    "Smoke assessment did not return a learner-facing artifact",
                    code="SS-PROVIDER-010",
                    details={"attempt_id": attempt_id},
                )
            return ProviderSmokeResult(
                provider=str(assessment["provider"]),
                status="ok",
                model_slug=str(assessment["model_slug"]),
                assessment_id=str(assessment["assessment_id"]),
                attempt_id=attempt_id,
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


async def _seed_prompt(client: httpx.AsyncClient, user_id: str) -> dict[str, object]:
    collection_response = await client.post(
        "/api/collections",
        headers={"X-User-ID": user_id},
        json={
            "title": "Smoke Quick Practice",
            "summary": "Quick-practice smoke prompt.",
            "target_audience": "Early-career consultants",
            "difficulty": "intermediate",
            "content_format_mix": ["quick_practice_prompt"],
            "target_skill_slugs": ["active-listening", "expectation-setting"],
            "target_competency_slugs": ["stakeholder-management"],
            "rubric_ids": ["quick_practice_text@v1"],
        },
    )
    _require_ok(collection_response, "create collection")
    collection_id = str(collection_response.json()["data"]["id"])

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
    _require_ok(prompt_response, "create prompt item")
    return cast(dict[str, object], prompt_response.json()["data"])


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
