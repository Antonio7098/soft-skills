"""Assistant proactivity under ambiguity smoke suites."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import cast

from soft_skills_backend.shared.errors import provider_error
from soft_skills_backend.smoke.contracts import SmokeCase, SmokeContext
from soft_skills_backend.smoke.support.backend import JsonObject, SmokeBackendClient
from soft_skills_backend.smoke.support.actors import SmokeActorBootstrap
from soft_skills_backend.smoke.support.environment import (
    ProviderSmokePreflight,
    SmokeApplicationSessionFactory,
)

from .contracts import AssistantProactivitySmokeResult

ASSISTANT_PROACTIVITY_SMOKE_TIMEOUT_SECONDS = 420.0


class _AssistantProactivitySmoke(SmokeCase, ABC):
    def __init__(
        self,
        *,
        name: str,
        description: str,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = ASSISTANT_PROACTIVITY_SMOKE_TIMEOUT_SECONDS,
    ) -> None:
        self.name = name
        self.description = description
        self._preflight = preflight or ProviderSmokePreflight()
        self._session_factory = session_factory or SmokeApplicationSessionFactory(
            provider_max_retries=2
        )
        self._flow_timeout_seconds = flow_timeout_seconds

    def run(self, context: SmokeContext) -> AssistantProactivitySmokeResult:
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

    async def _run(self, settings: object) -> AssistantProactivitySmokeResult:
        async with self._session_factory.open(settings) as backend:
            actors = await SmokeActorBootstrap(backend).prepare()
            payload = await self._run_flow(backend, actors.learner_id)
            return AssistantProactivitySmokeResult.model_validate(payload)

    @abstractmethod
    async def _run_flow(self, backend: SmokeBackendClient, user_id: str) -> JsonObject:
        """Execute the concrete proactivity flow."""


class AssistantProactivityAmbiguitySmoke(_AssistantProactivitySmoke):
    """Provider-backed smoke that verifies the assistant acts proactively under ambiguity.

    Sends an ambiguous message ("check my collections") and asserts the assistant
    queries data itself rather than asking the user for IDs or details.
    """

    def __init__(
        self,
        *,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = ASSISTANT_PROACTIVITY_SMOKE_TIMEOUT_SECONDS,
    ) -> None:
        super().__init__(
            name="assistant-proactivity-ambiguity",
            description=(
                "Run a provider-backed assistant turn with an ambiguous request and verify "
                "it proactively queries data instead of asking the user for missing details."
            ),
            preflight=preflight,
            session_factory=session_factory,
            flow_timeout_seconds=flow_timeout_seconds,
        )

    async def _run_flow(self, backend: SmokeBackendClient, user_id: str) -> JsonObject:
        session_payload = await backend.create_assistant_session(
            user_id=user_id,
            title="Assistant Proactivity Smoke",
        )
        turn_payload = await backend.create_assistant_turn(
            user_id=user_id,
            session_id=str(session_payload["id"]),
            message="check my collections",
        )
        turn = await backend.wait_for_assistant_turn(
            user_id=user_id,
            session_id=str(session_payload["id"]),
            turn_id=str(turn_payload["id"]),
            timeout_seconds=240.0,
        )
        if str(turn["status"]) != "completed":
            raise provider_error(
                "Proactivity smoke did not complete successfully",
                code="SS-PROVIDER-011",
                details={
                    "turn_status": turn.get("status"),
                    "last_error_code": turn.get("last_error_code"),
                    "tool_calls": turn.get("tool_calls", []),
                },
            )
        tool_names = [
            str(tool["tool_name"]) for tool in cast(list[JsonObject], turn.get("tool_calls", []))
        ]
        if "query_user_context" not in tool_names:
            raise provider_error(
                "Assistant did not proactively query data for ambiguous request",
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
            "ambiguous_message": "check my collections",
        }
