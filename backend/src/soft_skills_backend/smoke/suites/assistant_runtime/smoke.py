"""Assistant runtime smoke suites."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from pathlib import Path
from typing import cast

import httpx
import websockets

from soft_skills_backend.app import create_app
from soft_skills_backend.config import Settings
from soft_skills_backend.shared.errors import provider_error
from soft_skills_backend.smoke.contracts import SmokeCase, SmokeContext
from soft_skills_backend.smoke.support.actors import SmokeActorBootstrap
from soft_skills_backend.smoke.support.backend import JsonObject, SmokeBackendClient
from soft_skills_backend.smoke.support.environment import (
    ProviderSmokePreflight,
    SmokeApplicationSessionFactory,
)

from .contracts import AssistantRuntimeSmokeResult, AssistantStreamSmokeResult

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
            "tool_names": [
                str(tool["tool_name"])
                for tool in cast(list[JsonObject], turn.get("tool_calls", []))
            ],
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


class AssistantStreamRuntimeSmoke(_AssistantRuntimeSmoke):
    """Provider-backed assistant websocket streaming flow."""

    def __init__(
        self,
        *,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = ASSISTANT_SMOKE_TIMEOUT_SECONDS,
    ) -> None:
        super().__init__(
            name="assistant-stream-runtime",
            description="Run a provider-backed assistant turn and verify websocket streaming.",
            preflight=preflight,
            session_factory=session_factory,
            flow_timeout_seconds=flow_timeout_seconds,
        )

    def run(self, context: SmokeContext) -> AssistantStreamSmokeResult:
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

    async def _run(self, settings: Settings) -> AssistantStreamSmokeResult:
        import json
        import socket
        import tempfile
        import threading

        from alembic.config import Config

        from alembic import command as alembic_command

        def find_free_port() -> int:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", 0))
                return s.getsockname()[1]

        def run_migration(db_url: str) -> None:
            alembic_cfg = Config(str(Path(__file__).resolve().parents[5] / "alembic.ini"))
            alembic_cfg.set_main_option(
                "script_location", str(Path(__file__).resolve().parents[5] / "alembic")
            )
            alembic_cfg.set_main_option("sqlalchemy.url", db_url)
            alembic_command.upgrade(alembic_cfg, "head")

        with tempfile.TemporaryDirectory(prefix="soft-skills-stream-smoke-") as temp_dir:
            db_path = Path(temp_dir) / "smoke.db"
            db_url = f"sqlite+pysqlite:///{db_path}"
            port = find_free_port()

            smoke_settings = settings.model_copy(
                update={
                    "environment": "test",
                    "database_url": db_url,
                    "smoke_timeout_seconds": 60.0,
                    "provider_max_retries": 0,
                    "assessment_validation_retries": 0,
                }
            )

            run_migration(db_url)

            test_app = create_app(smoke_settings)

            import uvicorn

            server_config = uvicorn.Config(
                test_app,
                host="127.0.0.1",
                port=port,
                log_level="error",
            )
            server = uvicorn.Server(server_config)

            server_thread = threading.Thread(target=server.run, daemon=True)
            server_thread.start()

            import time

            time.sleep(1)

            try:
                base_url = f"http://127.0.0.1:{port}"

                transport = httpx.ASGITransport(app=test_app)
                async with httpx.AsyncClient(transport=transport, base_url=base_url) as client:
                    backend = SmokeBackendClient(client)
                    actors = await SmokeActorBootstrap(backend).prepare()
                    session_payload = await backend.create_assistant_session(
                        user_id=actors.learner_id,
                        title="Assistant Stream Smoke",
                    )
                    turn_payload = await backend.create_assistant_turn(
                        user_id=actors.learner_id,
                        session_id=str(session_payload["id"]),
                        message="Say hello in one short sentence.",
                    )
                    stream_token = str(turn_payload["stream_token"])
                    turn_id = str(turn_payload["id"])
                    session_id = str(session_payload["id"])
                    ws_url = f"ws://127.0.0.1:{port}/api/assistant/streams/{stream_token}"

                event_types: list[str] = []
                delta_count = 0
                final_content: str | None = None

                async with websockets.connect(ws_url) as ws:
                    while True:
                        message = await ws.recv()
                        data = json.loads(message)
                        event_type = str(data.get("type", ""))
                        event_types.append(event_type)
                        if event_type == "response.delta":
                            delta_count += 1
                        if event_type == "response.completed":
                            final_content = str(data.get("payload", {}).get("content", ""))
                        if event_type in ("response.completed", "turn.completed", "turn.failed"):
                            break

                async with httpx.AsyncClient(transport=transport, base_url=base_url) as client:
                    backend = SmokeBackendClient(client)
                    await backend.wait_for_assistant_turn(
                        user_id=actors.learner_id,
                        session_id=session_id,
                        turn_id=turn_id,
                    )

                if "response.delta" not in event_types:
                    raise provider_error(
                        "Websocket streaming smoke did not receive response.delta events",
                        code="SS-PROVIDER-011",
                        details={"event_types": event_types},
                    )
                if "response.completed" not in event_types:
                    raise provider_error(
                        "Websocket streaming smoke did not receive response.completed event",
                        code="SS-PROVIDER-011",
                        details={"event_types": event_types},
                    )

                return AssistantStreamSmokeResult(
                    status="ok",
                    session_id=session_id,
                    turn_id=turn_id,
                    stream_token=stream_token,
                    event_types=event_types,
                    delta_count=delta_count,
                    final_content=final_content,
                )
            finally:
                server.should_exit = True
                server_thread.join(timeout=5)

    async def _run_flow(self, backend: SmokeBackendClient, user_id: str) -> JsonObject:
        return {}
