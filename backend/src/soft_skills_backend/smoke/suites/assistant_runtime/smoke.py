"""Assistant runtime smoke suites."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import cast

from soft_skills_backend.config import Settings
from soft_skills_backend.shared.errors import provider_error
from soft_skills_backend.smoke.contracts import SmokeCase, SmokeContext
from soft_skills_backend.smoke.support.actors import SmokeActorBootstrap
from soft_skills_backend.smoke.support.backend import JsonObject, SmokeBackendClient
from soft_skills_backend.smoke.support.environment import (
    ProviderSmokePreflight,
    SmokeApplicationSessionFactory,
)

from .contracts import AssistantRuntimeSmokeResult

ASSISTANT_SMOKE_TIMEOUT_SECONDS = 420.0


class _AssistantRuntimeSmoke(SmokeCase, ABC):
    def __init__(
        self,
        *,
        name: str,
        description: str,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = ASSISTANT_SMOKE_TIMEOUT_SECONDS,
    ) -> None:
        self.name = name
        self.description = description
        self._preflight = preflight or ProviderSmokePreflight()
        self._session_factory = session_factory or SmokeApplicationSessionFactory()
        self._flow_timeout_seconds = flow_timeout_seconds

    def run(self, context: SmokeContext) -> AssistantRuntimeSmokeResult:
        self._preflight.assert_ready(context.settings)
        try:
            return asyncio.run(
                asyncio.wait_for(self._run(context.settings), timeout=self._flow_timeout_seconds)
            )
        except TimeoutError as exc:
            raise provider_error(
                "Smoke flow exceeded the allowed runtime budget",
                code="SS-PROVIDER-012",
                details={"timeout_seconds": self._flow_timeout_seconds},
            ) from exc

    async def _run(self, settings: Settings) -> AssistantRuntimeSmokeResult:
        async with self._session_factory.open(settings) as backend:
            actors = await SmokeActorBootstrap(backend).prepare()
            payload = await self._run_flow(backend, actors.learner_id)
            return AssistantRuntimeSmokeResult.model_validate(payload)

    @abstractmethod
    async def _run_flow(self, backend: SmokeBackendClient, user_id: str) -> JsonObject:
        """Execute the concrete assistant flow."""


class AssistantReadRuntimeSmoke(_AssistantRuntimeSmoke):
    """Provider-backed assistant read flow."""

    def __init__(
        self,
        *,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = ASSISTANT_SMOKE_TIMEOUT_SECONDS,
    ) -> None:
        super().__init__(
            name="assistant-read-runtime",
            description="Run a provider-backed assistant read turn end to end.",
            preflight=preflight,
            session_factory=session_factory,
            flow_timeout_seconds=flow_timeout_seconds,
        )

    async def _run_flow(self, backend: SmokeBackendClient, user_id: str) -> JsonObject:
        session_payload = await backend.create_assistant_session(
            user_id=user_id,
            title="Assistant Read Smoke",
        )
        turn_payload = await backend.create_assistant_turn(
            user_id=user_id,
            session_id=str(session_payload["id"]),
            message="Summarize my current profile and tell me one practical next step.",
        )
        turn = await backend.wait_for_assistant_turn(
            user_id=user_id,
            session_id=str(session_payload["id"]),
            turn_id=str(turn_payload["id"]),
        )
        messages = await backend.list_assistant_messages(
            user_id=user_id,
            session_id=str(session_payload["id"]),
        )
        assistant_message = cast(JsonObject, messages[-1]) if messages else {}
        return {
            "status": "ok",
            "session_id": str(session_payload["id"]),
            "turn_id": str(turn_payload["id"]),
            "turn_status": str(turn["status"]),
            "tool_names": [str(tool["tool_name"]) for tool in cast(list[JsonObject], turn.get("tool_calls", []))],
            "message_count": len(messages),
            "assistant_message_preview": str(assistant_message.get("content", ""))[:160],
        }


class AssistantGenerationRuntimeSmoke(_AssistantRuntimeSmoke):
    """Provider-backed assistant generation flow."""

    def __init__(
        self,
        *,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = ASSISTANT_SMOKE_TIMEOUT_SECONDS,
    ) -> None:
        super().__init__(
            name="assistant-generation-runtime",
            description="Run a provider-backed assistant generation turn end to end.",
            preflight=preflight,
            session_factory=session_factory,
            flow_timeout_seconds=flow_timeout_seconds,
        )

    async def _run_flow(self, backend: SmokeBackendClient, user_id: str) -> JsonObject:
        session_payload = await backend.create_assistant_session(
            user_id=user_id,
            title="Assistant Generation Smoke",
        )
        turn_payload = await backend.create_assistant_turn(
            user_id=user_id,
            session_id=str(session_payload["id"]),
            message=(
                "Use the generate_collection tool now. "
                "Generate one quick practice collection for early-career consultants. "
                "Use the exact skill slug active-listening, the exact competency slug "
                "stakeholder-management, difficulty intermediate, rubric "
                "quick_practice_text@v1, one quick practice prompt, and no scenarios."
            ),
        )
        turn = await backend.wait_for_assistant_turn(
            user_id=user_id,
            session_id=str(session_payload["id"]),
            turn_id=str(turn_payload["id"]),
            timeout_seconds=240.0,
        )
        tool_names = [
            str(tool["tool_name"]) for tool in cast(list[JsonObject], turn.get("tool_calls", []))
        ]
        if "generate_collection" not in tool_names:
            raise provider_error(
                "Assistant generation smoke did not invoke the expected generation tool",
                code="SS-PROVIDER-011",
                details={"tool_names": tool_names},
            )
        messages = await backend.list_assistant_messages(
            user_id=user_id,
            session_id=str(session_payload["id"]),
        )
        assistant_message = cast(JsonObject, messages[-1]) if messages else {}
        return {
            "status": "ok",
            "session_id": str(session_payload["id"]),
            "turn_id": str(turn_payload["id"]),
            "turn_status": str(turn["status"]),
            "tool_names": tool_names,
            "message_count": len(messages),
            "assistant_message_preview": str(assistant_message.get("content", ""))[:160],
        }
