"""Content-generation smoke suites."""

from __future__ import annotations

import asyncio
import time
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

from .contracts import ContentGenerationSmokeResult
from .contracts import (
    ContentGenerationLatencyEnvelopeResult,
    ContentGenerationTimingSample,
)

SMOKE_FLOW_TIMEOUT_SECONDS = 420.0


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
        self._session_factory = session_factory or SmokeApplicationSessionFactory()
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
            collection = await self._generate_collection(backend, actors.learner_id)
            collection_id = str(collection["id"])
            prompt_items = cast(list[object], collection.get("prompt_items", []))
            scenarios = cast(list[object], collection.get("scenarios", []))
            prompt_items_count = len(prompt_items)
            scenarios_count = len(scenarios)
            artifact = cast(JsonObject | None, collection.get("last_generation_artifact"))
            return ContentGenerationSmokeResult(
                status="ok",
                generation_mode=self.generation_mode,
                collection_id=collection_id,
                provider=str(artifact["provider"]) if artifact else None,
                model_slug=str(artifact["model_slug"]) if artifact else None,
                generation_artifact_id=str(artifact["id"]) if artifact else None,
                prompt_items_count=prompt_items_count,
                scenarios_count=scenarios_count,
            )

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
        return await backend.generate_structured_collection(user_id=user_id)


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
        return await backend.generate_chat_collection(user_id=user_id)


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
        self._session_factory = session_factory or SmokeApplicationSessionFactory()
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
                content_format_mix=["quick_practice_prompt", "interview_prompt"],
                target_skill_slugs=["active-listening", "decision-justification"],
                target_competency_slugs=["stakeholder-management", "problem-solving"],
                rubric_ids=["quick_practice_text@v1", "interview_text@v1"],
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
        async with self._session_factory.open(settings) as backend:
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
                "scenario_step",
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
                "scenario_text@v1",
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
                "scenario_count": 1,
                "scenario_artifact_count": 1,
            },
        }
        started = time.perf_counter()
        result = await backend.generate_structured_collection_payload(user_id=user_id, payload=payload)
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
            expected_llm_calls=8,
            expected_subpipelines=7,
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
                "scenario_step",
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
                "scenario_text@v1",
            ],
            "counts": {
                "quick_practice_prompt_count": 3,
                "interview_prompt_count": 2,
                "scenario_count": 1,
                "scenario_artifact_count": 1,
            },
        }
        started = time.perf_counter()
        result = await backend.generate_chat_collection_payload(user_id=user_id, payload=payload)
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
            expected_llm_calls=7,
            expected_subpipelines=6,
        )

    async def _run_heavy_structured_prompt_expansion(
        self,
        backend: SmokeBackendClient,
        user_id: str,
    ) -> ContentGenerationTimingSample:
        collection_id = await backend.create_collection(
            user_id=user_id,
            title="Latency Envelope Prompt Expansion Structured",
            content_format_mix=["quick_practice_prompt", "interview_prompt"],
            target_skill_slugs=["active-listening", "decision-justification"],
            target_competency_slugs=["stakeholder-management", "problem-solving"],
            rubric_ids=["quick_practice_text@v1", "interview_text@v1"],
        )
        payload: JsonObject = {
            "title_hint": "Expansion under executive pressure",
            "workplace_context": (
                "A sponsor escalation, a hesitant legal lead, and a product deadline are "
                "forcing the learner to reset expectations and justify hard tradeoffs."
            ),
            "generation_focus": (
                "Generate a larger balanced set of quick practice and interview prompts "
                "for executive alignment under pressure."
            ),
            "realism_notes": [
                "Use concrete stakeholder motives.",
                "Keep the questions distinct.",
            ],
            "target_skill_slugs": ["active-listening", "decision-justification"],
            "counts": {
                "quick_practice_prompt_count": 3,
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
            expected_subpipelines=6,
        )

    async def _run_heavy_chat_prompt_expansion(
        self,
        backend: SmokeBackendClient,
        user_id: str,
    ) -> ContentGenerationTimingSample:
        collection_id = await backend.create_collection(
            user_id=user_id,
            title="Latency Envelope Prompt Expansion Chat",
            content_format_mix=["quick_practice_prompt", "interview_prompt"],
            target_skill_slugs=["active-listening", "decision-justification"],
            target_competency_slugs=["stakeholder-management", "problem-solving"],
            rubric_ids=["quick_practice_text@v1", "interview_text@v1"],
        )
        payload: JsonObject = {
            "prompt": (
                "Add a larger, varied set of quick practice and interview prompts about "
                "resetting sponsor expectations, justifying tradeoffs, and leading through "
                "ambiguity in a delayed enterprise AI rollout."
            ),
            "target_skill_slugs": ["active-listening", "decision-justification"],
            "counts": {
                "quick_practice_prompt_count": 3,
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
            expected_subpipelines=6,
        )
