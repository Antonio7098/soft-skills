"""Full user journey smoke suite."""

from __future__ import annotations

import asyncio
import json
import socket
import tempfile
import threading
import time
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
from soft_skills_backend.smoke.support.environment import ProviderSmokePreflight

from .contracts import FullUserJourneySmokeResult

SMOKE_TIMEOUT_SECONDS = 480.0


def _inject_fake_assessment_marker(app: Any) -> None:
    from soft_skills_backend.engines.config import load_marking_runtime_config
    from soft_skills_backend.modules.practice.domain.practice import AssessmentDraft
    from soft_skills_backend.modules.practice.workflows.assessment import (
        AssessmentTransformPayload,
    )

    config = load_marking_runtime_config()

    class _FakeAssessmentMarker:
        provider_name = "openai"
        model_slug = "gpt-4.1-mini"

        async def mark_attempt(
            self, *, prompt_payload: Any, learner_payload: Any, call_context: Any
        ) -> AssessmentTransformPayload:
            skill_slugs = list(prompt_payload.prompt.target_skill_slugs)
            if not skill_slugs:
                skill_slugs = ["active-listening", "expectation-setting"]
            score = 4
            return AssessmentTransformPayload(
                draft=AssessmentDraft.model_validate(
                    {
                        "prompt_version": config.prompt_version,
                        "rubric_version": prompt_payload.prompt.rubric_version,
                        "provider": self.provider_name,
                        "model_slug": self.model_slug,
                        "overall_score": score,
                        "rationale": "Credible stakeholder handling.",
                        "skill_scores": [
                            {
                                "skill_slug": slug,
                                "score": score,
                                "rationale": f"Demonstrated {slug}.",
                            }
                            for slug in skill_slugs
                        ],
                        "evidence": [
                            {
                                "skill_slug": slug,
                                "quote": prompt_payload.response_text,
                                "explanation": f"Response showed evidence for {slug}.",
                            }
                            for slug in skill_slugs
                        ],
                        "strengths": ["Stayed grounded and proposed a concrete next step."],
                        "weaknesses": ["Could have added a clearer check-in point."],
                        "next_actions": ["Practice closing with an owner and deadline."],
                    }
                ),
                raw_payload={"ok": True},
                model_slug=self.model_slug,
                schema_version=config.output_schema_version,
            )

    app.state.container.practice_service._assessment_marker = _FakeAssessmentMarker()


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@asynccontextmanager
async def _open_websocket_capable_backend(
    settings: Settings,
    *,
    provider_max_retries: int = 2,
) -> AsyncIterator[SmokeBackendClient]:
    from alembic.config import Config

    from alembic import command as alembic_command

    base_path = Path(__file__).resolve().parents[5]

    with tempfile.TemporaryDirectory(prefix="soft-skills-journey-") as temp_dir:
        db_path = Path(temp_dir) / "smoke.db"
        db_url = f"sqlite+pysqlite:///{db_path}"
        port = _find_free_port()
        smoke_settings = settings.model_copy(
            update={
                "environment": "test",
                "database_url": db_url,
                "smoke_timeout_seconds": 60.0,
                "provider_max_retries": provider_max_retries,
                "assessment_validation_retries": 0,
            }
        )

        alembic_cfg = Config(str(base_path / "alembic.ini"))
        alembic_cfg.set_main_option("script_location", str(base_path / "alembic"))
        alembic_cfg.set_main_option("sqlalchemy.url", db_url)
        alembic_command.upgrade(alembic_cfg, "head")

        test_app = create_app(smoke_settings)
        _inject_fake_assessment_marker(test_app)

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
                timeout=httpx.Timeout(SMOKE_TIMEOUT_SECONDS),
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

    return {
        "collection": collection_payload,
        "generation_artifact_id": generation_artifact_id,
    }


class FullUserJourneySmoke(SmokeCase):
    """Full user journey smoke test exercising the complete user flow end to end."""

    name = "full-user-journey"
    description = (
        "Run the complete user journey: register, generate collection, assistant interactions, "
        "practice sessions, progression tracking, and collection saving."
    )

    def __init__(
        self,
        *,
        preflight: ProviderSmokePreflight | None = None,
        flow_timeout_seconds: float = SMOKE_TIMEOUT_SECONDS,
    ) -> None:
        self._preflight = preflight or ProviderSmokePreflight()
        self._flow_timeout_seconds = flow_timeout_seconds

    def run(self, context: SmokeContext) -> FullUserJourneySmokeResult:
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

    async def _run(self, settings: Settings) -> FullUserJourneySmokeResult:
        async with _open_websocket_capable_backend(settings) as backend:
            actors = await SmokeActorBootstrap(backend).prepare()
            user_id = actors.learner_id

            first_collection_result = await self._generate_first_collection(backend, user_id)
            first_collection = cast(JsonObject, first_collection_result["collection"])
            first_collection_id = str(first_collection["id"])
            first_prompt_items = cast(list[object], first_collection.get("prompt_items", []))

            assistant_session = await backend.create_assistant_session(
                user_id=user_id,
                title="Full Journey Assistant",
            )
            assistant_session_id = str(assistant_session["id"])

            view_turn = await backend.create_assistant_turn(
                user_id=user_id,
                session_id=assistant_session_id,
                message=f"Summarize collection {first_collection_id} and tell me what skills it covers.",
            )
            completed_view_turn = await backend.wait_for_assistant_turn(
                user_id=user_id,
                session_id=assistant_session_id,
                turn_id=str(view_turn["id"]),
                timeout_seconds=120.0,
            )
            view_tool_names = [
                str(tool["tool_name"])
                for tool in cast(list[JsonObject], completed_view_turn.get("tool_calls", []))
            ]

            second_collection_result = await self._generate_second_collection_via_assistant(
                backend=backend,
                user_id=user_id,
                session_id=assistant_session_id,
            )
            second_collection = cast(JsonObject, second_collection_result["collection"])
            second_collection_id = str(second_collection["id"])
            second_prompt_items = cast(list[object], second_collection.get("prompt_items", []))

            await self._add_prompt_item_to_first_collection(backend, user_id, first_collection_id)

            practice_run_payload = await backend.start_practice_run(
                user_id=user_id,
                payload={
                    "items": [
                        {
                            "practice_type": "quick_practice",
                            "prompt_item_id": str(first_prompt_items[0]["id"]),
                        },
                        {
                            "practice_type": "quick_practice",
                            "prompt_item_id": str(second_prompt_items[0]["id"]),
                        },
                    ],
                },
            )
            practice_run_id = str(practice_run_payload["run_id"])
            items = cast(list[JsonObject], practice_run_payload["items"])
            attempt_ids = [str(cast(JsonObject, item["attempt"])["id"]) for item in items]

            for attempt_id in attempt_ids:
                response = await backend.submit_attempt_response(
                    user_id=user_id,
                    attempt_id=attempt_id,
                    response_text=(
                        "I understand the pressure. The earliest realistic option is next Friday, "
                        "and I can confirm any scope tradeoffs with the team tomorrow afternoon."
                    ),
                )
                if response.status_code not in {200, 422, 503}:
                    backend.require_ok(response, f"submit attempt {attempt_id}")

            await backend.get_practice_run(user_id=user_id, run_id=practice_run_id)

            progress_response = await backend._client.get(
                "/api/progress/me",
                headers={"X-User-ID": user_id},
            )
            progress_snapshot_id = None
            if progress_response.status_code == 200:
                progress_data = progress_response.json().get("data")
                snapshot = cast(
                    JsonObject | None, progress_data.get("snapshot") if progress_data else None
                )
                if snapshot:
                    progress_snapshot_id = str(snapshot["snapshot_id"])

            query_attempts_turn = await backend.create_assistant_turn(
                user_id=user_id,
                session_id=assistant_session_id,
                message="What were my recent practice attempts?",
            )
            completed_query_turn = await backend.wait_for_assistant_turn(
                user_id=user_id,
                session_id=assistant_session_id,
                turn_id=str(query_attempts_turn["id"]),
                timeout_seconds=120.0,
            )
            query_tool_names = [
                str(tool["tool_name"])
                for tool in cast(list[JsonObject], completed_query_turn.get("tool_calls", []))
            ]

            all_tool_names = (
                view_tool_names + second_collection_result.get("tool_names", []) + query_tool_names
            )

            start_practice_turn = await backend.create_assistant_turn(
                user_id=user_id,
                session_id=assistant_session_id,
                message=(
                    f"Start a practice session from collection {first_collection_id}. "
                    "Ask me the first question and wait for my answer."
                ),
            )
            completed_practice_turn = await backend.wait_for_assistant_turn(
                user_id=user_id,
                session_id=assistant_session_id,
                turn_id=str(start_practice_turn["id"]),
                timeout_seconds=240.0,
            )
            practice_tool_names = [
                str(tool["tool_name"])
                for tool in cast(list[JsonObject], completed_practice_turn.get("tool_calls", []))
            ]
            all_tool_names.extend(practice_tool_names)

            answer_turn = await backend.create_assistant_turn(
                user_id=user_id,
                session_id=assistant_session_id,
                message=(
                    "I hear why the date matters. The earliest realistic option is next Friday, "
                    "and I can confirm the scope tradeoff with the team tomorrow afternoon."
                ),
            )
            await backend.wait_for_assistant_turn(
                user_id=user_id,
                session_id=assistant_session_id,
                turn_id=str(answer_turn["id"]),
                timeout_seconds=240.0,
            )

            await backend.list_assistant_messages(
                user_id=user_id,
                session_id=assistant_session_id,
            )

            org = await backend.create_organisation(
                user_id=user_id,
                name="Full Journey Org",
                slug=f"full-journey-org-{user_id[:8]}",
            )
            organisation_id = str(org["id"])

            await backend._client.post(
                f"/api/collections/{first_collection_id}/save",
                headers={"X-User-ID": user_id},
            )
            await backend._client.post(
                f"/api/collections/{second_collection_id}/save",
                headers={"X-User-ID": user_id},
            )

            global_response = await backend._client.get(
                "/api/collections",
                params={"include_private": "false", "discovery_tier": "global_public"},
                headers={"X-User-ID": user_id},
            )
            backend.require_ok(global_response, "fetch global hub collections")
            global_collections = cast(list[JsonObject], global_response.json().get("data", []))
            global_hub_ids = [str(c["id"]) for c in global_collections]

            skill_slugs = list(
                set(
                    str(skill)
                    for prompt_item in first_prompt_items + second_prompt_items
                    for skill in cast(list[str], prompt_item.get("target_skill_slugs", []))
                )
            )

            return FullUserJourneySmokeResult(
                status="ok",
                user_id=user_id,
                first_collection_id=first_collection_id,
                first_collection_prompt_items_count=len(first_prompt_items),
                second_collection_id=second_collection_id,
                second_collection_prompt_items_count=len(second_prompt_items),
                assistant_session_id=assistant_session_id,
                assistant_turn_ids=[str(view_turn["id"]), str(second_collection_result["turn_id"])],
                assistant_tool_names=all_tool_names,
                practice_run_id=practice_run_id,
                attempt_ids=attempt_ids,
                skill_slugs=skill_slugs,
                progress_snapshot_id=progress_snapshot_id,
                organisation_id=organisation_id,
                saved_collection_ids=[first_collection_id, second_collection_id],
                global_hub_collection_ids=global_hub_ids,
            )

    async def _generate_first_collection(
        self, backend: SmokeBackendClient, user_id: str
    ) -> JsonObject:
        return await _generate_collection_via_websocket(
            backend=backend,
            user_id=user_id,
            endpoint="/api/collections/generate/structured",
            payload={
                "title_hint": "First Journey Collection",
                "target_audience": "Early-career consultants",
                "difficulty": "intermediate",
                "content_format_mix": ["quick_practice_prompt"],
                "target_skill_slugs": ["active-listening", "expectation-setting"],
                "target_competency_slugs": ["stakeholder-management"],
                "rubric_ids": ["quick_practice_reset_timeline@v1"],
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
            flow_timeout_seconds=self._flow_timeout_seconds,
        )

    async def _generate_second_collection_via_assistant(
        self, backend: SmokeBackendClient, user_id: str, session_id: str
    ) -> JsonObject:
        turn_payload = await backend.create_assistant_turn(
            user_id=user_id,
            session_id=session_id,
            message=(
                "Call the generate_collection tool now. Create one quick practice collection "
                "about handling scope creep under deadline pressure. "
                'Use content_format_mix ["quick_practice_prompt"], '
                'target_skill_slugs ["expectation-setting", "prioritization-under-pressure"], '
                'target_competency_slugs ["managing-ambiguity"], '
                'rubric_ids ["quick_practice_reset_timeline@v1"], and counts with one quick practice prompt.'
            ),
        )
        turn_id = str(turn_payload["id"])
        completed_turn = await backend.wait_for_assistant_turn(
            user_id=user_id,
            session_id=session_id,
            turn_id=turn_id,
            timeout_seconds=240.0,
        )
        tool_calls = cast(list[JsonObject], completed_turn.get("tool_calls", []))
        tool_names = [str(tool["tool_name"]) for tool in tool_calls]
        if "generate_collection" not in tool_names:
            raise provider_error(
                "Assistant did not invoke generate_collection tool",
                code="SS-PROVIDER-011",
                details={"tool_names": tool_names},
            )

        collections_response = await backend._client.get(
            "/api/collections",
            headers={"X-User-ID": user_id},
        )
        backend.require_ok(collections_response, "list collections after assistant generation")
        all_collections = cast(list[JsonObject], collections_response.json().get("data", []))
        if not all_collections:
            raise provider_error(
                "No collections found after assistant generation",
                code="SS-PROVIDER-014",
            )
        second_collection = all_collections[0]
        second_collection_id = str(second_collection["id"])
        return {
            "collection": second_collection,
            "turn_id": turn_id,
            "tool_names": tool_names,
        }

    async def _add_prompt_item_to_first_collection(
        self, backend: SmokeBackendClient, user_id: str, collection_id: str
    ) -> JsonObject:
        response = await backend._client.post(
            f"/api/collections/{collection_id}/prompt-items",
            headers={"X-User-ID": user_id},
            json={
                "prompt_type": "quick_practice_prompt",
                "title": "Assistant added question",
                "prompt_text": (
                    "A stakeholder adds urgent scope one day before delivery. "
                    "Respond with a clear tradeoff analysis."
                ),
                "difficulty": "intermediate",
                "target_skill_slugs": ["expectation-setting", "prioritization-under-pressure"],
                "rubric_id": "quick_practice_reset_timeline@v1",
            },
        )
        backend.require_ok(response, "add prompt item to collection")
        return response.json().get("data", {})
