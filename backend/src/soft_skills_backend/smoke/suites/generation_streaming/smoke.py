"""Generation streaming smoke suites."""

from __future__ import annotations

import asyncio
import json
import socket
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

import httpx
import websockets

from soft_skills_backend.app import create_app
from soft_skills_backend.config import Settings
from soft_skills_backend.shared.errors import provider_error
from soft_skills_backend.smoke.contracts import SmokeCase, SmokeContext
from soft_skills_backend.smoke.support.actors import SmokeActorBootstrap
from soft_skills_backend.smoke.support.backend import SmokeBackendClient
from soft_skills_backend.smoke.support.environment import (
    ProviderSmokePreflight,
    SmokeApplicationSessionFactory,
)

from .contracts import BlueprintPayload, GenerationStreamingSmokeResult, PromptItemPayload

GENERATION_SMOKE_TIMEOUT_SECONDS = 420.0


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class GenerationStreamingSmoke(SmokeCase):
    """Provider-backed generation streaming smoke."""

    name = "generation-streaming"
    description = "Run generation with WebSocket streaming of progress events."

    def __init__(
        self,
        *,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = GENERATION_SMOKE_TIMEOUT_SECONDS,
    ) -> None:
        self._preflight = preflight or ProviderSmokePreflight()
        self._session_factory = session_factory or SmokeApplicationSessionFactory()
        self._flow_timeout_seconds = flow_timeout_seconds

    def run(self, context: SmokeContext) -> GenerationStreamingSmokeResult:
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

    async def _run(self, settings: Settings) -> GenerationStreamingSmokeResult:
        from alembic.config import Config

        from alembic import command as alembic_command

        base_path = Path(__file__).resolve().parents[5]

        with tempfile.TemporaryDirectory(prefix="soft-skills-gen-stream-") as temp_dir:
            db_path = Path(temp_dir) / "smoke.db"
            db_url = f"sqlite+pysqlite:///{db_path}"
            port = _find_free_port()

            smoke_settings = settings.model_copy(
                update={
                    "environment": "test",
                    "database_url": db_url,
                    "smoke_timeout_seconds": 60.0,
                    "provider_max_retries": 0,
                    "assessment_validation_retries": 0,
                }
            )

            alembic_cfg = Config(str(base_path / "alembic.ini"))
            alembic_cfg.set_main_option("script_location", str(base_path / "alembic"))
            alembic_cfg.set_main_option("sqlalchemy.url", db_url)
            alembic_command.upgrade(alembic_cfg, "head")

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

            time.sleep(1)

            try:
                base_url = f"http://127.0.0.1:{port}"

                generation_id: str | None = None
                stream_token: str | None = None

                transport = httpx.ASGITransport(app=test_app)
                async with httpx.AsyncClient(transport=transport, base_url=base_url) as client:
                    backend = SmokeBackendClient(client)
                    actors = await SmokeActorBootstrap(backend).prepare()
                    user_id = actors.learner_id

                    response = await backend._client.post(
                        "/api/collections/generate/structured",
                        headers={"X-User-ID": user_id},
                        json={
                            "title_hint": "Smoke Streaming Test",
                            "target_audience": "Early-career consultants",
                            "difficulty": "intermediate",
                            "content_format_mix": ["quick_practice_prompt"],
                            "target_skill_slugs": ["active-listening"],
                            "target_competency_slugs": ["stakeholder-management"],
                            "rubric_ids": ["quick_practice_text@v1"],
                            "domain": "Enterprise SaaS",
                            "workplace_context": "A launch is under time pressure.",
                            "scenario_theme": "Conflicting stakeholder expectations",
                            "realism_notes": ["Keep the scenario specific."],
                            "counts": {
                                "quick_practice_prompt_count": 1,
                                "interview_prompt_count": 0,
                                "scenario_count": 0,
                                "scenario_artifact_count": 0,
                            },
                        },
                    )

                    if response.status_code != 200:
                        return GenerationStreamingSmokeResult(
                            status="error",
                            generation_mode="structured",
                            error=f"HTTP {response.status_code}: {response.text[:500]}",
                        )

                    data = response.json()
                    envelope = data.get("data", {})
                    if isinstance(envelope, dict):
                        generation_id = envelope.get("generation_id")
                        stream_token = envelope.get("stream_token")

                    if not generation_id or not stream_token:
                        return GenerationStreamingSmokeResult(
                            status="error",
                            generation_mode="structured",
                            error=f"Missing generation_id or stream_token. Response: {data}",
                        )

                    ws_url = f"ws://127.0.0.1:{port}/api/ws/generation/{stream_token}"

                stages_received: list[str] = []
                final_status: str | None = None
                collection_id: str | None = None
                generation_artifact_id: str | None = None
                blueprint: BlueprintPayload | None = None
                prompt_items: list[PromptItemPayload] = []
                error_message: str | None = None

                async with websockets.connect(ws_url) as ws:
                    deadline = time.time() + self._flow_timeout_seconds
                    while time.time() < deadline:
                        try:
                            remaining = deadline - time.time()
                            message = await asyncio.wait_for(ws.recv(), timeout=max(1.0, remaining))
                            event_data: dict[str, Any] = json.loads(message)
                            event_type = str(event_data.get("type", ""))
                            stage = str(event_data.get("stage", ""))
                            if stage:
                                stages_received.append(stage)
                            if event_type == "completed":
                                final_status = "completed"
                                payload = event_data.get("payload", {})
                                collection_id = payload.get("collection_id")
                                generation_artifact_id = payload.get("generation_artifact_id")
                                break
                            elif event_type == "failed":
                                final_status = "failed"
                                payload = event_data.get("payload", {})
                                error_message = (
                                    str(payload.get("error", "no error message"))
                                    if isinstance(payload, dict)
                                    else str(payload)
                                )
                                break
                            elif stage == "blueprint_llm_transform" and not blueprint:
                                payload = event_data.get("payload", {})
                                blueprint = BlueprintPayload(
                                    title=payload.get("title"),
                                    summary=payload.get("summary"),
                                    prompt_items_count=payload.get("prompt_items_count"),
                                    scenarios_count=payload.get("scenarios_count"),
                                    model_slug=payload.get("model_slug"),
                                )
                            elif stage == "prompt_items_work":
                                payload = event_data.get("payload", {})
                                items = payload.get("prompt_items", [])
                                for item_data in items:
                                    item = PromptItemPayload(
                                        title=item_data.get("title"),
                                        prompt_type=item_data.get("prompt_type"),
                                        difficulty=item_data.get("difficulty"),
                                    )
                                    prompt_items.append(item)
                        except TimeoutError:
                            continue

                    if final_status is None:
                        final_status = "timeout"

                if final_status == "failed":
                    return GenerationStreamingSmokeResult(
                        status="error",
                        generation_mode="structured",
                        generation_id=generation_id,
                        stream_token=stream_token,
                        stages_received=stages_received,
                        blueprint=blueprint,
                        prompt_items=prompt_items,
                        final_status=final_status,
                        error=error_message,
                    )

                if not stages_received:
                    return GenerationStreamingSmokeResult(
                        status="error",
                        generation_mode="structured",
                        generation_id=generation_id,
                        stream_token=stream_token,
                        error="No streaming events received",
                    )

                if not blueprint:
                    return GenerationStreamingSmokeResult(
                        status="error",
                        generation_mode="structured",
                        generation_id=generation_id,
                        stream_token=stream_token,
                        stages_received=stages_received,
                        error="Blueprint not received in streaming events",
                    )

                if not blueprint.title:
                    return GenerationStreamingSmokeResult(
                        status="error",
                        generation_mode="structured",
                        generation_id=generation_id,
                        stream_token=stream_token,
                        stages_received=stages_received,
                        error="Blueprint title is empty",
                    )

                return GenerationStreamingSmokeResult(
                    status="ok",
                    generation_mode="structured",
                    generation_id=generation_id,
                    stream_token=stream_token,
                    collection_id=collection_id,
                    generation_artifact_id=generation_artifact_id,
                    stages_received=stages_received,
                    blueprint=blueprint,
                    prompt_items=prompt_items,
                    final_status=final_status,
                )
            finally:
                server.should_exit = True
                server_thread.join(timeout=5)
