"""Generation edge case smoke suites - comprehensive testing of generation flows."""

from __future__ import annotations

import asyncio
import json
import socket
import time
from typing import Any, cast

import httpx
import websockets

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
    GenerationEdgeCaseSmokeResult,
    GenerationEmptyCountsSmokeResult,
    GenerationInvalidSkillSlugSmokeResult,
    GenerationLongPromptSmokeResult,
    GenerationMultipleCollectionsSmokeResult,
    GenerationSpecialCharsPromptSmokeResult,
)

GENERATION_EDGE_CASE_TIMEOUT_SECONDS = 300.0


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


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

    return {
        "collection": collection_payload,
        "generation_artifact_id": generation_artifact_id,
    }


class GenerationLongPromptSmoke(SmokeCase):
    """Test generation with very long prompt (5000+ chars)."""

    name = "generation-long-prompt"
    description = "Test generation with very long prompt text."

    def __init__(
        self,
        *,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = GENERATION_EDGE_CASE_TIMEOUT_SECONDS,
    ) -> None:
        self._preflight = preflight or ProviderSmokePreflight()
        self._session_factory = session_factory or SmokeApplicationSessionFactory()
        self._flow_timeout_seconds = flow_timeout_seconds

    def run(self, context: SmokeContext) -> GenerationLongPromptSmokeResult:
        self._preflight.assert_ready(context.settings)
        try:
            return asyncio.run(
                asyncio.wait_for(self._run(context.settings), timeout=self._flow_timeout_seconds)
            )
        except TimeoutError as exc:
            raise provider_error(
                "Long prompt generation smoke exceeded runtime budget",
                code="SS-PROVIDER-012",
                details={"timeout_seconds": self._flow_timeout_seconds},
            ) from exc

    async def _run(self, settings: Settings) -> GenerationLongPromptSmokeResult:
        async with self._session_factory.open(settings) as backend:
            actors = await SmokeActorBootstrap(backend).prepare()
            long_prompt = (
                "I need you to create a realistic interview draft about making decisions with incomplete "
                "information. " * 50
            )
            payload = await backend.generate_chat_collection_payload(
                user_id=actors.learner_id,
                payload={
                    "prompt": long_prompt,
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
            collection = cast(JsonObject, payload.get("collection", payload))
            collection_id = collection.get("id") if isinstance(collection, dict) else None
            prompt_items = collection.get("prompt_items") if isinstance(collection, dict) else None
            return GenerationLongPromptSmokeResult(
                status="ok",
                test_name="long_prompt",
                generation_mode="chat",
                collection_id=str(collection_id) if collection_id else None,
                prompt_items_count=len(prompt_items) if prompt_items else 0,
            )


class GenerationSpecialCharsPromptSmoke(SmokeCase):
    """Test generation with special characters in prompt."""

    name = "generation-special-chars-prompt"
    description = "Test generation with special characters, unicode, and emoji in prompt."

    def __init__(
        self,
        *,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = GENERATION_EDGE_CASE_TIMEOUT_SECONDS,
    ) -> None:
        self._preflight = preflight or ProviderSmokePreflight()
        self._session_factory = session_factory or SmokeApplicationSessionFactory()
        self._flow_timeout_seconds = flow_timeout_seconds

    def run(self, context: SmokeContext) -> GenerationSpecialCharsPromptSmokeResult:
        self._preflight.assert_ready(context.settings)
        try:
            return asyncio.run(
                asyncio.wait_for(self._run(context.settings), timeout=self._flow_timeout_seconds)
            )
        except TimeoutError as exc:
            raise provider_error(
                "Special chars prompt generation smoke exceeded runtime budget",
                code="SS-PROVIDER-012",
                details={"timeout_seconds": self._flow_timeout_seconds},
            ) from exc

    async def _run(self, settings: Settings) -> GenerationSpecialCharsPromptSmokeResult:
        async with self._session_factory.open(settings) as backend:
            actors = await SmokeActorBootstrap(backend).prepare()
            special_prompt = (
                "Create interview prompt about \u4e2d\u6587 and English mixing: "
                "\U0001f600\U0001f4af\u2705\u2728 "
                'Special chars: @#$%^&*() \n\t\r\\" '
                "And some SQL-like: SELECT * FROM prompts WHERE active=true;"
            )
            payload = await backend.generate_chat_collection_payload(
                user_id=actors.learner_id,
                payload={
                    "prompt": special_prompt,
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
            collection = cast(JsonObject, payload.get("collection", payload))
            collection_id = collection.get("id") if isinstance(collection, dict) else None
            prompt_items = collection.get("prompt_items") if isinstance(collection, dict) else None
            return GenerationSpecialCharsPromptSmokeResult(
                status="ok",
                test_name="special_chars_prompt",
                generation_mode="chat",
                collection_id=str(collection_id) if collection_id else None,
                prompt_items_count=len(prompt_items) if prompt_items else 0,
            )


class GenerationInvalidSkillSlugSmoke(SmokeCase):
    """Test generation with invalid skill slugs."""

    name = "generation-invalid-skill-slug"
    description = "Test generation with non-existent skill slugs."

    def __init__(
        self,
        *,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = GENERATION_EDGE_CASE_TIMEOUT_SECONDS,
    ) -> None:
        self._preflight = preflight or ProviderSmokePreflight()
        self._session_factory = session_factory or SmokeApplicationSessionFactory()
        self._flow_timeout_seconds = flow_timeout_seconds

    def run(self, context: SmokeContext) -> GenerationInvalidSkillSlugSmokeResult:
        self._preflight.assert_ready(context.settings)
        try:
            return asyncio.run(
                asyncio.wait_for(self._run(context.settings), timeout=self._flow_timeout_seconds)
            )
        except TimeoutError as exc:
            raise provider_error(
                "Invalid skill slug generation smoke exceeded runtime budget",
                code="SS-PROVIDER-012",
                details={"timeout_seconds": self._flow_timeout_seconds},
            ) from exc

    async def _run(self, settings: Settings) -> GenerationInvalidSkillSlugSmokeResult:
        async with self._session_factory.open(settings) as backend:
            actors = await SmokeActorBootstrap(backend).prepare()
            response = await backend._client.post(
                "/api/collections/generate/structured",
                headers={"X-User-ID": actors.learner_id},
                json={
                    "title_hint": "Invalid Skill Slug Test",
                    "target_audience": "Early-career consultants",
                    "difficulty": "intermediate",
                    "content_format_mix": ["quick_practice_prompt"],
                    "target_skill_slugs": ["nonexistent-skill-xyz", "invalid-skill-123"],
                    "target_competency_slugs": ["nonexistent-competency"],
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
            status = response.status_code
            if status == 200:
                data = response.json().get("data", {})
                collection = cast(JsonObject, data.get("collection", {}))
                return GenerationInvalidSkillSlugSmokeResult(
                    status="ok",
                    test_name="invalid_skill_slug",
                    generation_mode="structured",
                    collection_id=str(collection.get("id")) if collection.get("id") else None,
                    prompt_items_count=len(collection.get("prompt_items", []))
                    if collection.get("prompt_items")
                    else 0,
                )
            else:
                error = response.json().get("error", {})
                return GenerationInvalidSkillSlugSmokeResult(
                    status="rejected",
                    test_name="invalid_skill_slug",
                    error_code=str(error.get("code", "UNKNOWN")),
                    error_details={"status": status},
                )


class GenerationEmptyCountsSmoke(SmokeCase):
    """Test generation with all counts set to zero."""

    name = "generation-empty-counts"
    description = "Test generation with all item counts set to zero."

    def __init__(
        self,
        *,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = GENERATION_EDGE_CASE_TIMEOUT_SECONDS,
    ) -> None:
        self._preflight = preflight or ProviderSmokePreflight()
        self._session_factory = session_factory or SmokeApplicationSessionFactory()
        self._flow_timeout_seconds = flow_timeout_seconds

    def run(self, context: SmokeContext) -> GenerationEmptyCountsSmokeResult:
        self._preflight.assert_ready(context.settings)
        try:
            return asyncio.run(
                asyncio.wait_for(self._run(context.settings), timeout=self._flow_timeout_seconds)
            )
        except TimeoutError as exc:
            raise provider_error(
                "Empty counts generation smoke exceeded runtime budget",
                code="SS-PROVIDER-012",
                details={"timeout_seconds": self._flow_timeout_seconds},
            ) from exc

    async def _run(self, settings: Settings) -> GenerationEmptyCountsSmokeResult:
        async with self._session_factory.open(settings) as backend:
            actors = await SmokeActorBootstrap(backend).prepare()
            response = await backend._client.post(
                "/api/collections/generate/structured",
                headers={"X-User-ID": actors.learner_id},
                json={
                    "title_hint": "Empty Counts Test",
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
                        "quick_practice_prompt_count": 0,
                        "interview_prompt_count": 0,
                        "scenario_count": 0,
                        "scenario_artifact_count": 0,
                    },
                },
            )
            status = response.status_code
            if status == 200:
                data = response.json().get("data", {})
                collection = cast(JsonObject, data.get("collection", {}))
                return GenerationEmptyCountsSmokeResult(
                    status="ok",
                    test_name="empty_counts",
                    generation_mode="structured",
                    collection_id=str(collection.get("id")) if collection.get("id") else None,
                    prompt_items_count=len(collection.get("prompt_items", []))
                    if collection.get("prompt_items")
                    else 0,
                )
            else:
                error = response.json().get("error", {})
                return GenerationEmptyCountsSmokeResult(
                    status="rejected",
                    test_name="empty_counts",
                    error_code=str(error.get("code", "UNKNOWN")),
                    error_details={"status": status},
                )


class GenerationMultipleCollectionsSmoke(SmokeCase):
    """Test rapid generation of multiple collections."""

    name = "generation-multiple-collections"
    description = "Test rapid generation of multiple collections in sequence."

    def __init__(
        self,
        *,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = GENERATION_EDGE_CASE_TIMEOUT_SECONDS,
    ) -> None:
        self._preflight = preflight or ProviderSmokePreflight()
        self._session_factory = session_factory or SmokeApplicationSessionFactory()
        self._flow_timeout_seconds = flow_timeout_seconds

    def run(self, context: SmokeContext) -> GenerationMultipleCollectionsSmokeResult:
        self._preflight.assert_ready(context.settings)
        try:
            return asyncio.run(
                asyncio.wait_for(self._run(context.settings), timeout=self._flow_timeout_seconds)
            )
        except TimeoutError as exc:
            raise provider_error(
                "Multiple collections generation smoke exceeded runtime budget",
                code="SS-PROVIDER-012",
                details={"timeout_seconds": self._flow_timeout_seconds},
            ) from exc

    async def _run(self, settings: Settings) -> GenerationMultipleCollectionsSmokeResult:
        async with self._session_factory.open(settings) as backend:
            actors = await SmokeActorBootstrap(backend).prepare()
            initiated_count = 0
            errors = []
            for i in range(3):
                try:
                    response = await backend._client.post(
                        "/api/collections/generate/structured",
                        headers={"X-User-ID": actors.learner_id},
                        json={
                            "title_hint": f"Smoke Collection {i + 1}",
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
                    if response.status_code == 200:
                        initiated_count += 1
                    else:
                        errors.append(f"collection {i + 1}: status {response.status_code}")
                except Exception as exc:
                    errors.append(f"collection {i + 1}: {type(exc).__name__} - {exc}")
            return GenerationMultipleCollectionsSmokeResult(
                status="ok" if initiated_count == 3 else "partial",
                test_name="multiple_collections",
                generation_mode="structured",
                error_details={
                    "initiated_count": initiated_count,
                    "errors": errors,
                },
            )
