"""Assistant edge case smoke suites - comprehensive testing of assistant runtime."""

from __future__ import annotations

import asyncio
from typing import cast

import httpx

from soft_skills_backend.config import Settings
from soft_skills_backend.shared.errors import provider_error, validation_error
from soft_skills_backend.smoke.contracts import SmokeCase, SmokeContext
from soft_skills_backend.smoke.support.actors import SmokeActorBootstrap
from soft_skills_backend.smoke.support.backend import JsonObject, SmokeBackendClient
from soft_skills_backend.smoke.support.environment import (
    ProviderSmokePreflight,
    SmokeApplicationSessionFactory,
)

from .contracts import (
    AssistantConcurrentSessionsSmokeResult,
    AssistantEmptyMessageSmokeResult,
    AssistantInvalidSessionSmokeResult,
    AssistantLongMessageSmokeResult,
    AssistantRapidTurnsSmokeResult,
    AssistantSpecialCharsSmokeResult,
    AssistantToolSequenceSmokeResult,
)

ASSISTANT_EDGE_CASE_TIMEOUT_SECONDS = 180.0


class AssistantLongMessageSmoke(SmokeCase):
    """Test assistant with extremely long messages."""

    name = "assistant-long-message"
    description = "Test assistant with very long messages (5000+ chars)."

    def __init__(
        self,
        *,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = ASSISTANT_EDGE_CASE_TIMEOUT_SECONDS,
    ) -> None:
        self._preflight = preflight or ProviderSmokePreflight()
        self._session_factory = session_factory or SmokeApplicationSessionFactory()
        self._flow_timeout_seconds = flow_timeout_seconds

    def run(self, context: SmokeContext) -> AssistantLongMessageSmokeResult:
        self._preflight.assert_ready(context.settings)
        try:
            return asyncio.run(
                asyncio.wait_for(self._run(context.settings), timeout=self._flow_timeout_seconds)
            )
        except TimeoutError as exc:
            raise provider_error(
                "Long message smoke exceeded runtime budget",
                code="SS-PROVIDER-012",
                details={"timeout_seconds": self._flow_timeout_seconds},
            ) from exc

    async def _run(self, settings: Settings) -> AssistantLongMessageSmokeResult:
        async with self._session_factory.open(settings) as backend:
            actors = await SmokeActorBootstrap(backend).prepare()
            session_payload = await backend.create_assistant_session(
                user_id=actors.learner_id,
                title="Long Message Smoke",
            )
            long_message = (
                "I need your help with a complex stakeholder communication challenge. " * 50
            )
            turn_payload = await backend.create_assistant_turn(
                user_id=actors.learner_id,
                session_id=str(session_payload["id"]),
                message=long_message,
            )
            turn = await backend.wait_for_assistant_turn(
                user_id=actors.learner_id,
                session_id=str(session_payload["id"]),
                turn_id=str(turn_payload["id"]),
            )
            if str(turn["status"]) != "completed":
                return AssistantLongMessageSmokeResult(
                    status="error",
                    test_name="long_message",
                    session_id=str(session_payload["id"]),
                    error_code=str(turn.get("last_error_code", "UNKNOWN")),
                    error_details={"turn_status": turn.get("status")},
                )
            messages = await backend.list_assistant_messages(
                user_id=actors.learner_id,
                session_id=str(session_payload["id"]),
            )
            tool_names = [
                str(tool["tool_name"])
                for tool in cast(list[JsonObject], turn.get("tool_calls", []))
            ]
            return AssistantLongMessageSmokeResult(
                status="ok",
                test_name="long_message",
                session_id=str(session_payload["id"]),
                turn_count=1,
                tool_names=tool_names,
            )


class AssistantSpecialCharsSmoke(SmokeCase):
    """Test assistant with special characters including injection attempts."""

    name = "assistant-special-chars"
    description = "Test assistant with special chars, unicode, emoji, and injection attempts."

    def __init__(
        self,
        *,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = ASSISTANT_EDGE_CASE_TIMEOUT_SECONDS,
    ) -> None:
        self._preflight = preflight or ProviderSmokePreflight()
        self._session_factory = session_factory or SmokeApplicationSessionFactory()
        self._flow_timeout_seconds = flow_timeout_seconds

    def run(self, context: SmokeContext) -> AssistantSpecialCharsSmokeResult:
        self._preflight.assert_ready(context.settings)
        try:
            return asyncio.run(
                asyncio.wait_for(self._run(context.settings), timeout=self._flow_timeout_seconds)
            )
        except TimeoutError as exc:
            raise provider_error(
                "Special chars smoke exceeded runtime budget",
                code="SS-PROVIDER-012",
                details={"timeout_seconds": self._flow_timeout_seconds},
            ) from exc

    async def _run(self, settings: Settings) -> AssistantSpecialCharsSmokeResult:
        async with self._session_factory.open(settings) as backend:
            actors = await SmokeActorBootstrap(backend).prepare()
            session_payload = await backend.create_assistant_session(
                user_id=actors.learner_id,
                title="Special Chars Smoke",
            )
            special_message = (
                "Test message with special chars: @#$%^&*() "
                "Unicode: \u4e2d\u6587\u65e5\u672c\u8a9e \u041f\u0440\u0438\u0432\u0435\u0442 "
                "Emoji: \U0001f600\U0001f4af\U0001f30d\U0001f30e "
                "SQL injection attempt: '; DROP TABLE users; -- "
                "XSS attempt: <script>alert('xss')</script> "
                'Newlines:\n\t\r\\" and more special chars: \u00e9\u00e8\u00ea'
            )
            turn_payload = await backend.create_assistant_turn(
                user_id=actors.learner_id,
                session_id=str(session_payload["id"]),
                message=special_message,
            )
            turn = await backend.wait_for_assistant_turn(
                user_id=actors.learner_id,
                session_id=str(session_payload["id"]),
                turn_id=str(turn_payload["id"]),
            )
            messages = await backend.list_assistant_messages(
                user_id=actors.learner_id,
                session_id=str(session_payload["id"]),
            )
            tool_names = [
                str(tool["tool_name"])
                for tool in cast(list[JsonObject], turn.get("tool_calls", []))
            ]
            return AssistantSpecialCharsSmokeResult(
                status="ok" if str(turn["status"]) == "completed" else "error",
                test_name="special_chars",
                session_id=str(session_payload["id"]),
                turn_count=1,
                tool_names=tool_names,
                error_code=str(turn.get("last_error_code"))
                if turn.get("status") != "completed"
                else None,
            )


class AssistantRapidTurnsSmoke(SmokeCase):
    """Test assistant with multiple rapid sequential turns."""

    name = "assistant-rapid-turns"
    description = "Test multiple rapid sequential turns to same session."

    def __init__(
        self,
        *,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = ASSISTANT_EDGE_CASE_TIMEOUT_SECONDS,
    ) -> None:
        self._preflight = preflight or ProviderSmokePreflight()
        self._session_factory = session_factory or SmokeApplicationSessionFactory()
        self._flow_timeout_seconds = flow_timeout_seconds

    def run(self, context: SmokeContext) -> AssistantRapidTurnsSmokeResult:
        self._preflight.assert_ready(context.settings)
        try:
            return asyncio.run(
                asyncio.wait_for(self._run(context.settings), timeout=self._flow_timeout_seconds)
            )
        except TimeoutError as exc:
            raise provider_error(
                "Rapid turns smoke exceeded runtime budget",
                code="SS-PROVIDER-012",
                details={"timeout_seconds": self._flow_timeout_seconds},
            ) from exc

    async def _run(self, settings: Settings) -> AssistantRapidTurnsSmokeResult:
        async with self._session_factory.open(settings) as backend:
            actors = await SmokeActorBootstrap(backend).prepare()
            session_payload = await backend.create_assistant_session(
                user_id=actors.learner_id,
                title="Rapid Turns Smoke",
            )
            messages_to_send = [
                "Hello, tell me about active listening.",
                "Can you elaborate on that?",
                "What about expectation setting?",
            ]
            turn_ids = []
            for msg in messages_to_send:
                turn_payload = await backend.create_assistant_turn(
                    user_id=actors.learner_id,
                    session_id=str(session_payload["id"]),
                    message=msg,
                )
                turn_ids.append(str(turn_payload["id"]))
            all_turns = []
            for turn_id in turn_ids:
                turn = await backend.wait_for_assistant_turn(
                    user_id=actors.learner_id,
                    session_id=str(session_payload["id"]),
                    turn_id=turn_id,
                )
                all_turns.append(turn)
            messages = await backend.list_assistant_messages(
                user_id=actors.learner_id,
                session_id=str(session_payload["id"]),
            )
            all_tool_names = []
            for turn in all_turns:
                for tool in cast(list[JsonObject], turn.get("tool_calls", [])):
                    all_tool_names.append(str(tool["tool_name"]))
            completed_count = sum(1 for t in all_turns if str(t["status"]) == "completed")
            return AssistantRapidTurnsSmokeResult(
                status="ok" if completed_count == len(messages_to_send) else "partial",
                test_name="rapid_turns",
                session_id=str(session_payload["id"]),
                turn_count=len(turn_ids),
                tool_names=all_tool_names,
            )


class AssistantConcurrentSessionsSmoke(SmokeCase):
    """Test assistant with concurrent sessions for same user."""

    name = "assistant-concurrent-sessions"
    description = "Test multiple concurrent sessions for same user."

    def __init__(
        self,
        *,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = ASSISTANT_EDGE_CASE_TIMEOUT_SECONDS,
    ) -> None:
        self._preflight = preflight or ProviderSmokePreflight()
        self._session_factory = session_factory or SmokeApplicationSessionFactory()
        self._flow_timeout_seconds = flow_timeout_seconds

    def run(self, context: SmokeContext) -> AssistantConcurrentSessionsSmokeResult:
        self._preflight.assert_ready(context.settings)
        try:
            return asyncio.run(
                asyncio.wait_for(self._run(context.settings), timeout=self._flow_timeout_seconds)
            )
        except TimeoutError as exc:
            raise provider_error(
                "Concurrent sessions smoke exceeded runtime budget",
                code="SS-PROVIDER-012",
                details={"timeout_seconds": self._flow_timeout_seconds},
            ) from exc

    async def _run(self, settings: Settings) -> AssistantConcurrentSessionsSmokeResult:
        async with self._session_factory.open(settings) as backend:
            actors = await SmokeActorBootstrap(backend).prepare()
            session_a = await backend.create_assistant_session(
                user_id=actors.learner_id,
                title="Session A",
            )
            session_b = await backend.create_assistant_session(
                user_id=actors.learner_id,
                title="Session B",
            )
            session_c = await backend.create_assistant_session(
                user_id=actors.learner_id,
                title="Session C",
            )
            turn_a = await backend.create_assistant_turn(
                user_id=actors.learner_id,
                session_id=str(session_a["id"]),
                message="Session A: Tell me about decision justification.",
            )
            turn_b = await backend.create_assistant_turn(
                user_id=actors.learner_id,
                session_id=str(session_b["id"]),
                message="Session B: What is prioritization under pressure?",
            )
            turn_c = await backend.create_assistant_turn(
                user_id=actors.learner_id,
                session_id=str(session_c["id"]),
                message="Session C: Explain stakeholder management.",
            )
            result_a = await backend.wait_for_assistant_turn(
                user_id=actors.learner_id,
                session_id=str(session_a["id"]),
                turn_id=str(turn_a["id"]),
            )
            result_b = await backend.wait_for_assistant_turn(
                user_id=actors.learner_id,
                session_id=str(session_b["id"]),
                turn_id=str(turn_b["id"]),
            )
            result_c = await backend.wait_for_assistant_turn(
                user_id=actors.learner_id,
                session_id=str(session_c["id"]),
                turn_id=str(turn_c["id"]),
            )
            sessions = await backend.list_assistant_sessions(user_id=actors.learner_id)
            completed = sum(1 for s in sessions if str(s.get("title", "")).startswith("Session"))
            return AssistantConcurrentSessionsSmokeResult(
                status="ok",
                test_name="concurrent_sessions",
                session_id=str(session_a["id"]),
                turn_count=3,
                tool_names=[
                    str(t.get("tool_name"))
                    for t in cast(list[JsonObject], result_a.get("tool_calls", []))
                ],
            )


class AssistantEmptyMessageSmoke(SmokeCase):
    """Test assistant with empty or minimal messages."""

    name = "assistant-empty-message"
    description = "Test assistant with empty and minimal messages."

    def __init__(
        self,
        *,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = ASSISTANT_EDGE_CASE_TIMEOUT_SECONDS,
    ) -> None:
        self._preflight = preflight or ProviderSmokePreflight()
        self._session_factory = session_factory or SmokeApplicationSessionFactory()
        self._flow_timeout_seconds = flow_timeout_seconds

    def run(self, context: SmokeContext) -> AssistantEmptyMessageSmokeResult:
        self._preflight.assert_ready(context.settings)
        try:
            return asyncio.run(
                asyncio.wait_for(self._run(context.settings), timeout=self._flow_timeout_seconds)
            )
        except TimeoutError as exc:
            raise provider_error(
                "Empty message smoke exceeded runtime budget",
                code="SS-PROVIDER-012",
                details={"timeout_seconds": self._flow_timeout_seconds},
            ) from exc

    async def _run(self, settings: Settings) -> AssistantEmptyMessageSmokeResult:
        async with self._session_factory.open(settings) as backend:
            actors = await SmokeActorBootstrap(backend).prepare()
            session_payload = await backend.create_assistant_session(
                user_id=actors.learner_id,
                title="Empty Message Smoke",
            )
            empty_message = ""
            response = await backend._client.post(
                f"/api/assistant/sessions/{session_payload['id']}/turns",
                headers={"X-User-ID": actors.learner_id},
                json={"message": empty_message},
            )
            status = response.status_code
            if status == 200:
                turn = response.json().get("data", {})
                turn_result = await backend.wait_for_assistant_turn(
                    user_id=actors.learner_id,
                    session_id=str(session_payload["id"]),
                    turn_id=str(turn.get("id", "")),
                )
                final_status = "ok"
                error_code = None
            else:
                final_status = "rejected"
                error_code = str(response.json().get("error", {}).get("code", "UNKNOWN"))
            return AssistantEmptyMessageSmokeResult(
                status=final_status,
                test_name="empty_message",
                session_id=str(session_payload["id"]),
                turn_count=1 if status == 200 else 0,
                error_code=error_code,
            )


class AssistantToolSequenceSmoke(SmokeCase):
    """Test assistant with sequence of different tools."""

    name = "assistant-tool-sequence"
    description = "Test assistant triggering multiple tools in sequence."

    def __init__(
        self,
        *,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = ASSISTANT_EDGE_CASE_TIMEOUT_SECONDS,
    ) -> None:
        self._preflight = preflight or ProviderSmokePreflight()
        self._session_factory = session_factory or SmokeApplicationSessionFactory()
        self._flow_timeout_seconds = flow_timeout_seconds

    def run(self, context: SmokeContext) -> AssistantToolSequenceSmokeResult:
        self._preflight.assert_ready(context.settings)
        try:
            return asyncio.run(
                asyncio.wait_for(self._run(context.settings), timeout=self._flow_timeout_seconds)
            )
        except TimeoutError as exc:
            raise provider_error(
                "Tool sequence smoke exceeded runtime budget",
                code="SS-PROVIDER-012",
                details={"timeout_seconds": self._flow_timeout_seconds},
            ) from exc

    async def _run(self, settings: Settings) -> AssistantToolSequenceSmokeResult:
        async with self._session_factory.open(settings) as backend:
            actors = await SmokeActorBootstrap(backend).prepare()
            session_payload = await backend.create_assistant_session(
                user_id=actors.learner_id,
                title="Tool Sequence Smoke",
            )
            turn_payload = await backend.create_assistant_turn(
                user_id=actors.learner_id,
                session_id=str(session_payload["id"]),
                message=(
                    "I need help with stakeholder communication. Can you first check my profile "
                    "and then generate a collection about expectation setting with active listening?"
                ),
            )
            turn = await backend.wait_for_assistant_turn(
                user_id=actors.learner_id,
                session_id=str(session_payload["id"]),
                turn_id=str(turn_payload["id"]),
            )
            messages = await backend.list_assistant_messages(
                user_id=actors.learner_id,
                session_id=str(session_payload["id"]),
            )
            tool_names = [
                str(tool["tool_name"])
                for tool in cast(list[JsonObject], turn.get("tool_calls", []))
            ]
            return AssistantToolSequenceSmokeResult(
                status="ok" if str(turn["status"]) == "completed" else "error",
                test_name="tool_sequence",
                session_id=str(session_payload["id"]),
                turn_count=1,
                tool_names=tool_names,
            )


class AssistantInvalidSessionSmoke(SmokeCase):
    """Test assistant handling of invalid session IDs."""

    name = "assistant-invalid-session"
    description = "Test assistant handling of invalid/non-existent session IDs."

    def __init__(
        self,
        *,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = ASSISTANT_EDGE_CASE_TIMEOUT_SECONDS,
    ) -> None:
        self._preflight = preflight or ProviderSmokePreflight()
        self._session_factory = session_factory or SmokeApplicationSessionFactory()
        self._flow_timeout_seconds = flow_timeout_seconds

    def run(self, context: SmokeContext) -> AssistantInvalidSessionSmokeResult:
        self._preflight.assert_ready(context.settings)
        try:
            return asyncio.run(
                asyncio.wait_for(self._run(context.settings), timeout=self._flow_timeout_seconds)
            )
        except TimeoutError as exc:
            raise provider_error(
                "Invalid session smoke exceeded runtime budget",
                code="SS-PROVIDER-012",
                details={"timeout_seconds": self._flow_timeout_seconds},
            ) from exc

    async def _run(self, settings: Settings) -> AssistantInvalidSessionSmokeResult:
        async with self._session_factory.open(settings) as backend:
            actors = await SmokeActorBootstrap(backend).prepare()
            response = await backend._client.post(
                "/api/assistant/sessions/nonexistent-session-12345/turns",
                headers={"X-User-ID": actors.learner_id},
                json={"message": "Hello"},
            )
            status = response.status_code
            error_payload = response.json().get("error", {})
            error_code = str(error_payload.get("code", "UNKNOWN"))
            return AssistantInvalidSessionSmokeResult(
                status="rejected" if status in {401, 403, 404} else "unexpected",
                test_name="invalid_session",
                error_code=error_code,
                error_details={"status": status},
            )
