"""Content-generation smoke suites."""

from __future__ import annotations

import asyncio
import json
import socket
import tempfile
import threading
import time
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, cast

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
    ContentGenerationLatencyEnvelopeResult,
    ContentGenerationSmokeResult,
    ContentGenerationTimingSample,
)

SMOKE_FLOW_TIMEOUT_SECONDS = 420.0


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _as_optional_str(value: object) -> str | None:
    return str(value) if value is not None else None


@asynccontextmanager
async def _open_websocket_capable_backend(
    settings: Settings,
    *,
    provider_max_retries: int = 0,
    assessment_validation_retries: int = 0,
) -> AsyncIterator[SmokeBackendClient]:
    from alembic.config import Config

    from alembic import command as alembic_command

    base_path = Path(__file__).resolve().parents[5]

    with tempfile.TemporaryDirectory(prefix="soft-skills-content-gen-") as temp_dir:
        db_path = Path(temp_dir) / "smoke.db"
        db_url = f"sqlite+pysqlite:///{db_path}"
        port = _find_free_port()
        smoke_settings = settings.model_copy(
            update={
                "environment": "test",
                "database_url": db_url,
                "smoke_timeout_seconds": 60.0,
                "provider_max_retries": provider_max_retries,
                "assessment_validation_retries": assessment_validation_retries,
            }
        )

        alembic_cfg = Config(str(base_path / "alembic.ini"))
        alembic_cfg.set_main_option("script_location", str(base_path / "alembic"))
        alembic_cfg.set_main_option("sqlalchemy.url", db_url)
        alembic_command.upgrade(alembic_cfg, "heads")

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
            async with httpx.AsyncClient(
                base_url=base_url,
                timeout=httpx.Timeout(SMOKE_FLOW_TIMEOUT_SECONDS),
            ) as client:
                yield SmokeBackendClient(
                    client,
                    session_factory=test_app.state.container.session_factory,
                )
        finally:
            server.should_exit = True
            server_thread.join(timeout=5)


async def _generate_collection_via_websocket(
    *,
    backend: SmokeBackendClient,
    user_id: str,
    endpoint: str,
    payload: JsonObject,
    flow_timeout_seconds: float,
) -> JsonObject:
    response = await backend._client.post(
        endpoint,
        headers={"X-User-ID": user_id},
        json=payload,
    )
    backend.require_ok(response, "generate collection")
    data = response.json()
    envelope = data.get("data", {})
    if not isinstance(envelope, dict):
        raise provider_error(
            "Unexpected response envelope",
            code="SS-PROVIDER-013",
        )
    stream_token = envelope.get("stream_token")
    if not stream_token:
        raise provider_error(
            "Missing stream_token in response",
            code="SS-PROVIDER-013",
            details={"envelope": envelope},
        )

    collection_id: str | None = None
    generation_artifact_id: str | None = None
    ws_url = (
        str(backend._client.base_url).replace("http://", "ws://").replace("https://", "wss://")
        + f"/api/ws/generation/{stream_token}"
    )

    deadline = time.time() + flow_timeout_seconds
    async with websockets.connect(ws_url) as ws:
        while time.time() < deadline:
            remaining = deadline - time.time()
            try:
                message = await asyncio.wait_for(ws.recv(), timeout=max(1.0, remaining))
                event_data: dict[str, Any] = json.loads(message)
                event_type = str(event_data.get("type", ""))
                if event_type == "completed":
                    comp_payload = event_data.get("payload", {})
                    collection_id = comp_payload.get("collection_id")
                    generation_artifact_id = comp_payload.get("generation_artifact_id")
                    break
                if event_type == "failed":
                    failed_payload = event_data.get("payload", {})
                    error_msg = (
                        failed_payload.get("error", "unknown")
                        if isinstance(failed_payload, dict)
                        else str(failed_payload)
                    )
                    raise provider_error(
                        f"Generation failed: {error_msg}",
                        code="SS-PROVIDER-013",
                    )
            except TimeoutError:
                continue

    if collection_id is None:
        raise provider_error(
            "Generation did not complete within timeout",
            code="SS-PROVIDER-012",
            details={"timeout_seconds": flow_timeout_seconds},
        )

    collection_response = await backend._client.get(
        f"/api/collections/{collection_id}",
        headers={"X-User-ID": user_id},
    )
    backend.require_ok(collection_response, "fetch generated collection")
    collection_payload = collection_response.json().get("data")
    if not isinstance(collection_payload, dict):
        raise provider_error(
            "Unexpected collection response envelope",
            code="SS-PROVIDER-013",
        )
    artifact = cast(JsonObject | None, collection_payload.get("last_generation_artifact"))

    return {
        "collection": collection_payload,
        "generation_artifact_id": generation_artifact_id,
        "provider": _as_optional_str(artifact.get("provider")) if artifact else None,
        "model_slug": _as_optional_str(artifact.get("model_slug")) if artifact else None,
    }


class _ContentGenerationSmoke(SmokeCase, ABC):
    """Base suite for content generation flows."""

    def __init__(
        self,
        *,
        name: str,
        description: str,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = SMOKE_FLOW_TIMEOUT_SECONDS,
    ) -> None:
        self.name = name
        self.description = description
        self._preflight = preflight or ProviderSmokePreflight()
        self._session_factory = session_factory or SmokeApplicationSessionFactory(
            provider_max_retries=2
        )
        self._flow_timeout_seconds = flow_timeout_seconds

    def run(self, context: SmokeContext) -> ContentGenerationSmokeResult:
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

    async def _run(self, settings: Settings) -> ContentGenerationSmokeResult:
        async with self._open_backend(settings) as backend:
            actors = await SmokeActorBootstrap(backend).prepare()
            collection = await self._generate_collection(backend, actors.learner_id)
            collection_id = str(collection["id"])
            prompt_items = cast(list[object], collection.get("prompt_items", []))
            scenarios = cast(list[object], collection.get("scenarios", []))
            for scenario in scenarios:
                scenario_payload = cast(JsonObject, scenario)
                questions = cast(list[object], scenario_payload.get("questions", []))
                if not questions:
                    raise provider_error(
                        "Generated scenario was missing authored questions",
                        code="SS-PROVIDER-013",
                        details={"scenario_id": scenario_payload.get("id"), "collection_id": collection_id},
                    )
            prompt_items_count = len(prompt_items)
            scenarios_count = len(scenarios)
            artifact = cast(JsonObject | None, collection.get("last_generation_artifact"))
            return ContentGenerationSmokeResult(
                status="ok",
                generation_mode=self.generation_mode,
                collection_id=collection_id,
                provider=_as_optional_str(artifact.get("provider")) if artifact else None,
                model_slug=_as_optional_str(artifact.get("model_slug")) if artifact else None,
                generation_artifact_id=_as_optional_str(artifact.get("id")) if artifact else None,
                prompt_items_count=prompt_items_count,
                scenarios_count=scenarios_count,
            )

    @asynccontextmanager
    async def _open_backend(self, settings: Settings) -> AsyncIterator[SmokeBackendClient]:
        async with _open_websocket_capable_backend(settings, provider_max_retries=2) as backend:
            yield backend

    @property
    @abstractmethod
    def generation_mode(self) -> str:
        """Generation mode under test."""

    @abstractmethod
    async def _generate_collection(
        self,
        backend: SmokeBackendClient,
        user_id: str,
    ) -> JsonObject:
        """Generate the concrete collection."""

    async def _generate_via_websocket(
        self,
        backend: SmokeBackendClient,
        user_id: str,
        endpoint: str,
        payload: JsonObject,
    ) -> JsonObject:
        result = await _generate_collection_via_websocket(
            backend=backend,
            user_id=user_id,
            endpoint=endpoint,
            payload=payload,
            flow_timeout_seconds=self._flow_timeout_seconds,
        )
        collection = cast(JsonObject, result["collection"])
        return {
            "id": collection["id"],
            "prompt_items": collection.get("prompt_items", []),
            "scenarios": collection.get("scenarios", []),
            "last_generation_artifact": cast(
                JsonObject | None, collection.get("last_generation_artifact")
            ),
        }


class StructuredGenerationSmoke(_ContentGenerationSmoke):
    """Smoke suite for structured collection generation."""

    generation_mode = "structured"

    def __init__(
        self,
        *,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = SMOKE_FLOW_TIMEOUT_SECONDS,
    ) -> None:
        super().__init__(
            name="generation-structured",
            description="Run the structured content generation flow end to end.",
            preflight=preflight,
            session_factory=session_factory,
            flow_timeout_seconds=flow_timeout_seconds,
        )

    async def _generate_collection(
        self,
        backend: SmokeBackendClient,
        user_id: str,
    ) -> JsonObject:
        return await self._generate_via_websocket(
            backend,
            user_id,
            "/api/collections/generate/structured",
            {
                "title_hint": "Smoke Structured Draft",
                "target_audience": "Early-career consultants",
                "difficulty": "intermediate",
                "content_format_mix": ["quick_practice_prompt"],
                "target_skill_slugs": ["active-listening", "expectation-setting"],
                "target_competency_slugs": ["stakeholder-management"],
                "rubric_ids": ["quick_practice_text@v1"],
                "domain": "Enterprise SaaS",
                "workplace_context": "A launch is under time pressure after a legal escalation.",
                "scenario_theme": "Conflicting stakeholder expectations",
                "realism_notes": ["Keep the scenario specific and realistic."],
                "counts": {
                    "quick_practice_prompt_count": 1,
                    "interview_prompt_count": 0,
                    "scenario_count": 0,
                    "scenario_artifact_count": 0,
                },
            },
        )


class ChatGenerationSmoke(_ContentGenerationSmoke):
    """Smoke suite for chat-based collection generation."""

    generation_mode = "chat"

    def __init__(
        self,
        *,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = SMOKE_FLOW_TIMEOUT_SECONDS,
    ) -> None:
        super().__init__(
            name="generation-chat",
            description="Run the chat-based content generation flow end to end.",
            preflight=preflight,
            session_factory=session_factory,
            flow_timeout_seconds=flow_timeout_seconds,
        )

    async def _generate_collection(
        self,
        backend: SmokeBackendClient,
        user_id: str,
    ) -> JsonObject:
        return await self._generate_via_websocket(
            backend,
            user_id,
            "/api/collections/generate/chat",
            {
                "prompt": (
                    "Create a realistic interview draft about making a decision with incomplete "
                    "information while keeping a senior stakeholder aligned."
                ),
                "target_audience": "Early-career consultants",
                "difficulty": "intermediate",
                "content_format_mix": ["interview_prompt"],
                "target_skill_slugs": ["decision-justification"],
                "target_competency_slugs": ["problem-solving"],
                "rubric_ids": ["interview_text@v1"],
                "counts": {
                    "quick_practice_prompt_count": 0,
                    "interview_prompt_count": 1,
                    "scenario_count": 0,
                    "scenario_artifact_count": 0,
                },
            },
        )


class _PromptItemGenerationSmoke(SmokeCase, ABC):
    """Base suite for prompt-item generation against an existing collection."""

    def __init__(
        self,
        *,
        name: str,
        description: str,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = SMOKE_FLOW_TIMEOUT_SECONDS,
    ) -> None:
        self.name = name
        self.description = description
        self._preflight = preflight or ProviderSmokePreflight()
        self._session_factory = session_factory or SmokeApplicationSessionFactory(
            provider_max_retries=2
        )
        self._flow_timeout_seconds = flow_timeout_seconds

    def run(self, context: SmokeContext) -> ContentGenerationSmokeResult:
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

    async def _run(self, settings: Settings) -> ContentGenerationSmokeResult:
        async with self._session_factory.open(settings) as backend:
            actors = await SmokeActorBootstrap(backend).prepare()
            collection_id = await backend.create_collection(
                user_id=actors.learner_id,
                title="Smoke Prompt Expansion Collection",
                content_format_mix=["interview_prompt"],
                target_skill_slugs=["decision-justification"],
                target_competency_slugs=["problem-solving"],
                rubric_ids=["interview_text@v1"],
            )
            generation = await self._generate_prompt_items(
                backend=backend,
                user_id=actors.learner_id,
                collection_id=collection_id,
            )
            prompt_items = cast(list[object], generation.get("prompt_items", []))
            return ContentGenerationSmokeResult(
                status="ok",
                generation_mode=self.generation_mode,
                collection_id=str(cast(JsonObject, generation["collection"])["id"]),
                provider=cast(str | None, generation.get("provider")),
                model_slug=cast(str | None, generation.get("model_slug")),
                generation_artifact_id=cast(str | None, generation.get("generation_artifact_id")),
                prompt_items_count=len(prompt_items),
                scenarios_count=0,
            )

    @property
    @abstractmethod
    def generation_mode(self) -> str:
        """Generation mode under test."""

    @abstractmethod
    async def _generate_prompt_items(
        self,
        *,
        backend: SmokeBackendClient,
        user_id: str,
        collection_id: str,
    ) -> JsonObject:
        """Generate prompt items for an existing collection."""


class StructuredPromptItemGenerationSmoke(_PromptItemGenerationSmoke):
    """Smoke suite for structured prompt-item generation in an existing collection."""

    generation_mode = "prompt_items_structured"

    def __init__(
        self,
        *,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = SMOKE_FLOW_TIMEOUT_SECONDS,
    ) -> None:
        super().__init__(
            name="generation-prompt-items-structured",
            description="Run structured prompt-item generation for an existing collection.",
            preflight=preflight,
            session_factory=session_factory,
            flow_timeout_seconds=flow_timeout_seconds,
        )

    async def _generate_prompt_items(
        self,
        *,
        backend: SmokeBackendClient,
        user_id: str,
        collection_id: str,
    ) -> JsonObject:
        return await backend.generate_structured_prompt_items(
            user_id=user_id,
            collection_id=collection_id,
        )


class ChatPromptItemGenerationSmoke(_PromptItemGenerationSmoke):
    """Smoke suite for chat prompt-item generation in an existing collection."""

    generation_mode = "prompt_items_chat"

    def __init__(
        self,
        *,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = SMOKE_FLOW_TIMEOUT_SECONDS,
    ) -> None:
        super().__init__(
            name="generation-prompt-items-chat",
            description="Run chat prompt-item generation for an existing collection.",
            preflight=preflight,
            session_factory=session_factory,
            flow_timeout_seconds=flow_timeout_seconds,
        )

    async def _generate_prompt_items(
        self,
        *,
        backend: SmokeBackendClient,
        user_id: str,
        collection_id: str,
    ) -> JsonObject:
        return await backend.generate_chat_prompt_items(
            user_id=user_id,
            collection_id=collection_id,
        )


class GenerationLatencyEnvelopeSmoke(SmokeCase):
    """Provider-backed stress exercise for generation latency and fan-out."""

    name = "generation-latency-envelope"
    description = (
        "Run a larger multi-call generation workload and report timings, "
        "expected LLM calls, and expected subpipeline counts."
    )

    def __init__(
        self,
        *,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = SMOKE_FLOW_TIMEOUT_SECONDS,
    ) -> None:
        self._preflight = preflight or ProviderSmokePreflight()
        self._session_factory = session_factory or SmokeApplicationSessionFactory(
            provider_max_retries=2
        )
        self._flow_timeout_seconds = flow_timeout_seconds

    def run(self, context: SmokeContext) -> ContentGenerationLatencyEnvelopeResult:
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

    async def _run(self, settings: Settings) -> ContentGenerationLatencyEnvelopeResult:
        async with _open_websocket_capable_backend(settings, provider_max_retries=2) as backend:
            actors = await SmokeActorBootstrap(backend).prepare()
            provider = self._preflight.build_provider(settings)
            suite_started = time.perf_counter()
            samples = [
                await self._run_heavy_structured_collection(backend, actors.learner_id),
                await self._run_heavy_chat_collection(backend, actors.learner_id),
                await self._run_heavy_structured_prompt_expansion(backend, actors.learner_id),
                await self._run_heavy_chat_prompt_expansion(backend, actors.learner_id),
            ]
            total_elapsed_ms = int((time.perf_counter() - suite_started) * 1000)
            return ContentGenerationLatencyEnvelopeResult(
                status="ok",
                provider=provider.provider_name,
                model_slug=provider.model_slug,
                total_elapsed_ms=total_elapsed_ms,
                max_flow_elapsed_ms=max(sample.elapsed_ms for sample in samples),
                total_expected_llm_calls=sum(sample.expected_llm_calls for sample in samples),
                total_expected_subpipelines=sum(sample.expected_subpipelines for sample in samples),
                samples=samples,
            )

    async def _run_heavy_structured_collection(
        self,
        backend: SmokeBackendClient,
        user_id: str,
    ) -> ContentGenerationTimingSample:
        payload: JsonObject = {
            "title_hint": "Latency Envelope Structured Pack",
            "target_audience": "Senior consultants",
            "difficulty": "advanced",
            "content_format_mix": [
                "quick_practice_prompt",
                "interview_prompt",
            ],
            "target_skill_slugs": [
                "active-listening",
                "expectation-setting",
                "decision-justification",
            ],
            "target_competency_slugs": [
                "stakeholder-management",
                "problem-solving",
            ],
            "rubric_ids": [
                "quick_practice_text@v1",
                "interview_text@v1",
            ],
            "domain": "Enterprise AI transformation",
            "workplace_context": (
                "A regulated enterprise rollout is slipping after legal review, a skeptical "
                "executive sponsor, and conflicting launch commitments across sales and product."
            ),
            "scenario_theme": "Executive alignment under delivery risk",
            "realism_notes": [
                "Keep the stakeholders specific.",
                "Use concrete operating constraints.",
                "Avoid generic coaching language.",
            ],
            "counts": {
                "quick_practice_prompt_count": 3,
                "interview_prompt_count": 3,
                "scenario_count": 0,
                "scenario_artifact_count": 0,
            },
        }
        started = time.perf_counter()
        result = await _generate_collection_via_websocket(
            backend=backend,
            user_id=user_id,
            endpoint="/api/collections/generate/structured",
            payload=payload,
            flow_timeout_seconds=self._flow_timeout_seconds,
        )
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        collection = cast(JsonObject, result["collection"])
        return ContentGenerationTimingSample(
            flow_name="heavy_structured_collection",
            generation_mode="structured",
            elapsed_ms=elapsed_ms,
            collection_id=str(collection["id"]),
            generation_artifact_id=cast(str | None, result.get("generation_artifact_id")),
            provider=cast(str | None, result.get("provider")),
            model_slug=cast(str | None, result.get("model_slug")),
            prompt_items_count=len(cast(list[object], collection.get("prompt_items", []))),
            scenarios_count=len(cast(list[object], collection.get("scenarios", []))),
            expected_llm_calls=7,
            expected_subpipelines=6,
        )

    async def _run_heavy_chat_collection(
        self,
        backend: SmokeBackendClient,
        user_id: str,
    ) -> ContentGenerationTimingSample:
        payload: JsonObject = {
            "prompt": (
                "Create an advanced mixed-format collection about defending tradeoffs, "
                "resetting executive expectations, and navigating a delayed AI rollout "
                "with legal, sales, and product leaders pushing in different directions."
            ),
            "target_audience": "Senior consultants",
            "difficulty": "advanced",
            "content_format_mix": [
                "quick_practice_prompt",
                "interview_prompt",
            ],
            "target_skill_slugs": [
                "active-listening",
                "expectation-setting",
                "decision-justification",
            ],
            "target_competency_slugs": [
                "stakeholder-management",
                "problem-solving",
            ],
            "rubric_ids": [
                "quick_practice_text@v1",
                "interview_text@v1",
            ],
            "counts": {
                "quick_practice_prompt_count": 3,
                "interview_prompt_count": 2,
                "scenario_count": 0,
                "scenario_artifact_count": 0,
            },
        }
        started = time.perf_counter()
        result = await _generate_collection_via_websocket(
            backend=backend,
            user_id=user_id,
            endpoint="/api/collections/generate/chat",
            payload=payload,
            flow_timeout_seconds=self._flow_timeout_seconds,
        )
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        collection = cast(JsonObject, result["collection"])
        return ContentGenerationTimingSample(
            flow_name="heavy_chat_collection",
            generation_mode="chat",
            elapsed_ms=elapsed_ms,
            collection_id=str(collection["id"]),
            generation_artifact_id=cast(str | None, result.get("generation_artifact_id")),
            provider=cast(str | None, result.get("provider")),
            model_slug=cast(str | None, result.get("model_slug")),
            prompt_items_count=len(cast(list[object], collection.get("prompt_items", []))),
            scenarios_count=len(cast(list[object], collection.get("scenarios", []))),
            expected_llm_calls=6,
            expected_subpipelines=5,
        )

    async def _run_heavy_structured_prompt_expansion(
        self,
        backend: SmokeBackendClient,
        user_id: str,
    ) -> ContentGenerationTimingSample:
        collection_id = await backend.create_collection(
            user_id=user_id,
            title="Latency Envelope Prompt Expansion Structured",
            content_format_mix=["interview_prompt"],
            target_skill_slugs=["decision-justification"],
            target_competency_slugs=["problem-solving"],
            rubric_ids=["interview_text@v1"],
        )
        payload: JsonObject = {
            "title_hint": "Expansion under executive pressure",
            "workplace_context": (
                "A sponsor escalation, a hesitant legal lead, and a product deadline are "
                "forcing the learner to reset expectations and justify hard tradeoffs."
            ),
            "generation_focus": (
                "Generate a larger varied set of interview prompts for executive alignment under pressure."
            ),
            "realism_notes": [
                "Use concrete stakeholder motives.",
                "Keep the questions distinct.",
            ],
            "target_skill_slugs": ["decision-justification"],
            "counts": {
                "quick_practice_prompt_count": 0,
                "interview_prompt_count": 3,
            },
        }
        started = time.perf_counter()
        result = await backend.generate_structured_prompt_items_payload(
            user_id=user_id,
            collection_id=collection_id,
            payload=payload,
        )
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        collection = cast(JsonObject, result["collection"])
        return ContentGenerationTimingSample(
            flow_name="heavy_structured_prompt_expansion",
            generation_mode="prompt_items_structured",
            elapsed_ms=elapsed_ms,
            collection_id=str(collection["id"]),
            generation_artifact_id=cast(str | None, result.get("generation_artifact_id")),
            provider=cast(str | None, result.get("provider")),
            model_slug=cast(str | None, result.get("model_slug")),
            prompt_items_count=len(cast(list[object], result.get("prompt_items", []))),
            scenarios_count=0,
            expected_llm_calls=7,
            expected_subpipelines=4,
        )

    async def _run_heavy_chat_prompt_expansion(
        self,
        backend: SmokeBackendClient,
        user_id: str,
    ) -> ContentGenerationTimingSample:
        collection_id = await backend.create_collection(
            user_id=user_id,
            title="Latency Envelope Prompt Expansion Chat",
            content_format_mix=["interview_prompt"],
            target_skill_slugs=["decision-justification"],
            target_competency_slugs=["problem-solving"],
            rubric_ids=["interview_text@v1"],
        )
        payload: JsonObject = {
            "prompt": (
                "Add a larger, varied set of interview prompts about "
                "justifying tradeoffs and leading through "
                "ambiguity in a delayed enterprise AI rollout."
            ),
            "target_skill_slugs": ["decision-justification"],
            "counts": {
                "quick_practice_prompt_count": 0,
                "interview_prompt_count": 3,
            },
        }
        started = time.perf_counter()
        result = await backend.generate_chat_prompt_items_payload(
            user_id=user_id,
            collection_id=collection_id,
            payload=payload,
        )
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        collection = cast(JsonObject, result["collection"])
        return ContentGenerationTimingSample(
            flow_name="heavy_chat_prompt_expansion",
            generation_mode="prompt_items_chat",
            elapsed_ms=elapsed_ms,
            collection_id=str(collection["id"]),
            generation_artifact_id=cast(str | None, result.get("generation_artifact_id")),
            provider=cast(str | None, result.get("provider")),
            model_slug=cast(str | None, result.get("model_slug")),
            prompt_items_count=len(cast(list[object], result.get("prompt_items", []))),
            scenarios_count=0,
            expected_llm_calls=7,
            expected_subpipelines=4,
        )
