from __future__ import annotations

import pytest
from pydantic import BaseModel

from soft_skills_backend.config import Settings
from soft_skills_backend.shared.errors import AppError
from soft_skills_backend.smoke import build_default_registry
from soft_skills_backend.smoke.contracts import SmokeCase, SmokeContext
from soft_skills_backend.smoke.registry import SmokeRegistry
from soft_skills_backend.smoke.runner import SmokeRunner


class _DummyResult(BaseModel):
    status: str


class _DummySmoke(SmokeCase):
    name = "dummy"
    description = "Dummy smoke for runner tests."

    def run(self, context: SmokeContext) -> BaseModel:
        assert context.settings.environment == "test"
        return _DummyResult(status="ok")


def test_smoke_runner_runs_default_smoke() -> None:
    runner = SmokeRunner(
        SmokeRegistry([_DummySmoke()]),
        SmokeContext.create(Settings(_env_file=None, environment="test")),  # type: ignore[call-arg]
    )

    result = runner.run()

    assert result.smoke_name == "dummy"
    assert result.payload == {"status": "ok"}


def test_smoke_registry_rejects_unknown_smoke() -> None:
    registry = SmokeRegistry([_DummySmoke()])

    with pytest.raises(AppError) as exc_info:
        registry.get("missing")

    assert exc_info.value.code == "SS-VALIDATION-003"


def test_default_registry_includes_practice_run_lifecycle_smoke() -> None:
    registry = build_default_registry()

    assert registry.names() == [
        "provider-baseline",
        "assistant-read-runtime",
        "assistant-generation-runtime",
        "assistant-stream-runtime",
        "generation-structured",
        "generation-chat",
        "generation-prompt-items-structured",
        "generation-prompt-items-chat",
        "generation-latency-envelope",
        "generation-streaming",
        "auth-flows",
        "evaluation-benchmark",
        "eval-dashboard",
        "marking-quick-practice",
        "marking-interview",
        "marking-scenario",
        "marking-relational-persistence",
        "practice-session-flow",
        "practice-run-lifecycle",
        "organisation-management",
        "admin-user-management",
        "pipeline-visualization",
        "telemetry",
    ]
