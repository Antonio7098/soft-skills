"""Assistant runtime smoke suites."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from pathlib import Path
from tempfile import TemporaryDirectory
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

from .contracts import (
    AssistantPracticeRuntimeSmokeResult,
    AssistantApprovalSmokeResult,
    AssistantRuntimeSmokeResult,
    AssistantStreamSmokeResult,
)

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
        self._session_factory = session_factory or SmokeApplicationSessionFactory(
            provider_max_retries=2
        )
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
        if str(turn["status"]) != "completed":
            raise provider_error(
                "Assistant read smoke did not complete successfully",
                code="SS-PROVIDER-011",
                details={
                    "turn_status": turn.get("status"),
                    "last_error_code": turn.get("last_error_code"),
                },
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


class _ApprovalSequencedAssistantProvider:
    provider_name = "test-provider"
    model_slug = "test-model"

    def __init__(self, payloads: list[dict[str, object]]) -> None:
        self._payloads = payloads

    async def complete_json(self, *, messages: object, call_context: object):
        del messages, call_context
        payload = self._payloads.pop(0)
        from soft_skills_backend.shared.ports.models import ProviderCompletion

        return ProviderCompletion(
            content=payload,
            model_slug=self.model_slug,
            usage={"total_tokens": 10},
            raw_response={"provider": self.provider_name},
        )

    async def stream_text(self, *, messages: object, call_context: object):
        del call_context
        draft = str(cast(list[dict[str, object]], messages)[-1]["content"]).split(
            "guidance:\n",
            maxsplit=1,
        )[-1]
        from soft_skills_backend.shared.ports.models import ProviderTextChunk

        for token in draft.split():
            yield ProviderTextChunk(delta=f"{token} ", model_slug=self.model_slug, done=False)
        yield ProviderTextChunk(delta="", model_slug=self.model_slug, done=True)


class AssistantApprovalWorkflowSmoke(SmokeCase):
    """Local assistant approval flow smoke."""

    name = "assistant-approval-workflow"
    description = "Run an assistant turn that pauses for human approval before a mutating tool."

    def run(self, context: SmokeContext) -> AssistantApprovalSmokeResult:
        return asyncio.run(asyncio.wait_for(self._run(context.settings), timeout=60.0))

    async def _run(self, settings: Settings) -> AssistantApprovalSmokeResult:
        with TemporaryDirectory(prefix="soft-skills-approval-smoke-") as temp_dir:
            database_path = Path(temp_dir) / "approval-smoke.db"
            smoke_settings = settings.model_copy(
                update={
                    "environment": "test",
                    "database_url": f"sqlite+pysqlite:///{database_path}",
                    "provider_max_retries": 0,
                    "assessment_validation_retries": 0,
                }
            )
            app = create_app(smoke_settings)
            app.state.container.background_tasks.attach(asyncio.get_running_loop())
            SmokeApplicationSessionFactory()._migrate(smoke_settings)
            app.state.container.assistant_service._workflows._llm_provider = (  # type: ignore[attr-defined]
                _ApprovalSequencedAssistantProvider(
                    payloads=[
                        {
                            "tool_calls": [
                                {
                                    "call_id": "call-start",
                                    "tool_name": "start_collection_practice",
                                    "arguments": {
                                        "collection_id": "__COLLECTION_ID__",
                                        "item_limit": 1,
                                    },
                                }
                            ],
                            "final_response": None,
                        },
                        {
                            "tool_calls": [],
                            "final_response": "Practice started after approval.",
                        },
                    ]
                )
            )

            transport = httpx.ASGITransport(app=app)
            try:
                async with httpx.AsyncClient(
                    transport=transport,
                    base_url="http://testserver",
                ) as client:
                    backend = SmokeBackendClient(
                        client,
                        session_factory=app.state.container.session_factory,
                    )
                    actors = await SmokeActorBootstrap(backend).prepare()
                    collection_id = await backend.create_collection(
                        user_id=actors.learner_id,
                        title="Assistant Approval Smoke",
                        content_format_mix=["quick_practice_prompt"],
                        target_skill_slugs=["active-listening"],
                        target_competency_slugs=["stakeholder-management"],
                        rubric_ids=["quick_practice_reset_timeline@v1"],
                    )
                    await backend.create_prompt_item(
                        collection_id=collection_id,
                        user_id=actors.learner_id,
                        operation="create assistant approval smoke prompt",
                        payload={
                            "prompt_type": "quick_practice_prompt",
                            "title": "Reset the timeline",
                            "prompt_text": (
                                "A client asks for an impossible delivery date. Respond with empathy and a realistic next step."
                            ),
                            "difficulty": "intermediate",
                            "target_skill_slugs": ["active-listening"],
                            "rubric_id": "quick_practice_reset_timeline@v1",
                        },
                    )
                    payloads = app.state.container.assistant_service._workflows._llm_provider._payloads  # type: ignore[attr-defined]
                    payloads[0]["tool_calls"][0]["arguments"]["collection_id"] = collection_id  # type: ignore[index]

                    session_payload = await backend.create_assistant_session(
                        user_id=actors.learner_id,
                        title="Assistant Approval Smoke",
                    )
                    turn_payload = await backend.create_assistant_turn(
                        user_id=actors.learner_id,
                        session_id=str(session_payload["id"]),
                        message=f"Start one practice item from collection {collection_id}.",
                    )
                    approval_request = await self._wait_for_pending_approval(
                        backend,
                        user_id=actors.learner_id,
                    )
                    await backend.decide_assistant_approval(
                        user_id=actors.learner_id,
                        request_id=str(approval_request["id"]),
                        decision="approved",
                        reason="smoke_continue",
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
                    events = app.state.container.assistant_service.list_stream_events(  # type: ignore[attr-defined]
                        str(turn["stream_token"])
                    )
                    tool_names = [
                        str(tool["tool_name"])
                        for tool in cast(list[JsonObject], turn.get("tool_calls", []))
                    ]
                    event_types = [event.type for event in events]
                    if "approval.requested" not in event_types or "approval.decided" not in event_types:
                        raise provider_error(
                            "Assistant approval smoke did not emit approval lifecycle events",
                            code="SS-PROVIDER-011",
                            details={"event_types": event_types},
                        )
                    if "start_collection_practice" not in tool_names:
                        raise provider_error(
                            "Assistant approval smoke did not execute the expected tool",
                            code="SS-PROVIDER-011",
                            details={"tool_names": tool_names},
                        )
                    return AssistantApprovalSmokeResult(
                        status="ok",
                        session_id=str(session_payload["id"]),
                        turn_id=str(turn_payload["id"]),
                        approval_request_id=str(approval_request["id"]),
                        approval_status="approved",
                        event_types=event_types,
                        tool_names=tool_names,
                        assistant_message_preview=(
                            str(messages[-1]["content"])[:160] if messages else None
                        ),
                    )
            finally:
                await app.state.container.background_tasks.shutdown()
                await app.state.container.shutdown()
                app.state.container.dispose()

    async def _wait_for_pending_approval(
        self,
        backend: SmokeBackendClient,
        *,
        user_id: str,
    ) -> JsonObject:
        deadline = asyncio.get_running_loop().time() + 5.0
        while True:
            approvals = await backend.list_assistant_approvals(
                user_id=user_id,
                status="pending",
            )
            if approvals:
                return approvals[0]
            if asyncio.get_running_loop().time() >= deadline:
                raise provider_error(
                    "Smoke backend step failed",
                    code="SS-PROVIDER-011",
                    details={"operation": "wait for assistant approval"},
                )
            await asyncio.sleep(0.05)


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
                "Call the generate_collection tool now and do not answer directly. "
                "Create one interview-only collection for early-career consultants. "
                "Use prompt text intent about defending a decision with incomplete information. "
                "Use difficulty intermediate, content_format_mix [\"interview_prompt\"], "
                "target_skill_slugs [\"decision-justification\"], "
                "target_competency_slugs [\"problem-solving\"], "
                "rubric_ids [\"interview_text@v1\"], and counts with one interview prompt and zero of everything else."
            ),
        )
        turn = await backend.wait_for_assistant_turn(
            user_id=user_id,
            session_id=str(session_payload["id"]),
            turn_id=str(turn_payload["id"]),
            timeout_seconds=240.0,
        )
        if str(turn["status"]) != "completed":
            raise provider_error(
                "Assistant generation smoke did not complete successfully",
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


class AssistantPracticeRuntimeSmoke(_AssistantRuntimeSmoke):
    """Provider-backed multi-turn assistant practice facilitation flow."""

    def __init__(
        self,
        *,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = ASSISTANT_SMOKE_TIMEOUT_SECONDS,
    ) -> None:
        super().__init__(
            name="assistant-practice-runtime",
            description="Run a provider-backed assistant practice session across multiple turns.",
            preflight=preflight,
            session_factory=session_factory,
            flow_timeout_seconds=flow_timeout_seconds,
        )

    def run(self, context: SmokeContext) -> AssistantPracticeRuntimeSmokeResult:  # type: ignore[override]
        self._preflight.assert_ready(context.settings)
        try:
            return asyncio.run(
                asyncio.wait_for(
                    self._run_practice(context.settings),
                    timeout=self._flow_timeout_seconds,
                )
            )
        except TimeoutError as exc:
            raise provider_error(
                "Smoke flow exceeded the allowed runtime budget",
                code="SS-PROVIDER-012",
                details={"timeout_seconds": self._flow_timeout_seconds},
            ) from exc

    async def _run_practice(self, settings: Settings) -> AssistantPracticeRuntimeSmokeResult:
        async with self._session_factory.open(settings) as backend:
            actors = await SmokeActorBootstrap(backend).prepare()
            payload = await self._run_flow(backend, actors.learner_id)
            return AssistantPracticeRuntimeSmokeResult.model_validate(payload)

    async def _run_flow(self, backend: SmokeBackendClient, user_id: str) -> JsonObject:
        collection_id = await backend.create_collection(
            user_id=user_id,
            title="Assistant Practice Smoke",
            content_format_mix=["quick_practice_prompt"],
            target_skill_slugs=["active-listening", "expectation-setting"],
            target_competency_slugs=["stakeholder-management"],
            rubric_ids=["quick_practice_reset_timeline@v1"],
        )
        await backend.create_prompt_item(
            collection_id=collection_id,
            user_id=user_id,
            operation="create assistant practice smoke prompt 1",
            payload={
                "prompt_type": "quick_practice_prompt",
                "title": "Reset the timeline",
                "prompt_text": (
                    "A client asks for an impossible delivery date. Respond with empathy and a realistic next step."
                ),
                "difficulty": "intermediate",
                "target_skill_slugs": ["active-listening", "expectation-setting"],
                "rubric_id": "quick_practice_reset_timeline@v1",
            },
        )
        await backend.create_prompt_item(
            collection_id=collection_id,
            user_id=user_id,
            operation="create assistant practice smoke prompt 2",
            payload={
                "prompt_type": "quick_practice_prompt",
                "title": "Handle a scope push",
                "prompt_text": (
                    "A stakeholder wants extra scope without moving the deadline. Respond with a clear tradeoff."
                ),
                "difficulty": "intermediate",
                "target_skill_slugs": ["active-listening", "expectation-setting"],
                "rubric_id": "quick_practice_reset_timeline@v1",
            },
        )

        session_payload = await backend.create_assistant_session(
            user_id=user_id,
            title="Assistant Practice Smoke",
        )
        session_id = str(session_payload["id"])

        turn_ids: list[str] = []
        tool_names: list[str] = []

        start_turn = await backend.create_assistant_turn(
            user_id=user_id,
            session_id=session_id,
            message=(
                f"Start a two-question practice session from collection {collection_id}. "
                "Ask me the first question and wait for my answer."
            ),
        )
        turn_ids.append(str(start_turn["id"]))
        completed_start_turn = await backend.wait_for_assistant_turn(
            user_id=user_id,
            session_id=session_id,
            turn_id=str(start_turn["id"]),
            timeout_seconds=240.0,
        )
        tool_names.extend(
            str(tool["tool_name"])
            for tool in cast(list[JsonObject], completed_start_turn.get("tool_calls", []))
        )
        practice_run_id = str(
            cast(list[JsonObject], completed_start_turn["tool_calls"])[0]["result"]["practice"][
                "practice_run_id"
            ]
        )

        first_answer_turn = await backend.create_assistant_turn(
            user_id=user_id,
            session_id=session_id,
            message=(
                "I understand why the date matters. The earliest realistic option is next Friday, "
                "and I can confirm any scope tradeoff with the team tomorrow afternoon."
            ),
        )
        turn_ids.append(str(first_answer_turn["id"]))
        completed_first_answer_turn = await backend.wait_for_assistant_turn(
            user_id=user_id,
            session_id=session_id,
            turn_id=str(first_answer_turn["id"]),
            timeout_seconds=240.0,
        )
        tool_names.extend(
            str(tool["tool_name"])
            for tool in cast(list[JsonObject], completed_first_answer_turn.get("tool_calls", []))
        )

        second_answer_turn = await backend.create_assistant_turn(
            user_id=user_id,
            session_id=session_id,
            message=(
                "I hear the urgency. If we add the scope now, we need to move the date by two days, "
                "or we keep the date and defer the new request until the next checkpoint."
            ),
        )
        turn_ids.append(str(second_answer_turn["id"]))
        completed_second_answer_turn = await backend.wait_for_assistant_turn(
            user_id=user_id,
            session_id=session_id,
            turn_id=str(second_answer_turn["id"]),
            timeout_seconds=240.0,
        )
        tool_names.extend(
            str(tool["tool_name"])
            for tool in cast(list[JsonObject], completed_second_answer_turn.get("tool_calls", []))
        )

        messages = await backend.list_assistant_messages(
            user_id=user_id,
            session_id=session_id,
        )
        assistant_message = cast(JsonObject, messages[-1]) if messages else {}
        if "start_collection_practice" not in tool_names:
            raise provider_error(
                "Assistant practice smoke did not invoke the practice-start tool",
                code="SS-PROVIDER-011",
                details={"tool_names": tool_names},
            )
        submit_count = sum(tool_name == "submit_active_practice_response" for tool_name in tool_names)
        if submit_count < 2:
            raise provider_error(
                "Assistant practice smoke did not submit both active practice answers",
                code="SS-PROVIDER-011",
                details={"tool_names": tool_names, "submit_count": submit_count},
            )
        return {
            "status": "ok",
            "session_id": session_id,
            "practice_run_id": practice_run_id,
            "turn_ids": turn_ids,
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

    def run(self, context: SmokeContext) -> AssistantStreamSmokeResult:  # type: ignore[override]
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

    async def _run(self, settings: Settings) -> AssistantStreamSmokeResult:  # type: ignore[override]
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
