"""Prompt library smoke suite for verifying prompt rendering and management with real provider."""

from __future__ import annotations

import asyncio
import time

from soft_skills_backend.config import Settings
from soft_skills_backend.shared.errors import provider_error
from soft_skills_backend.smoke.contracts import SmokeCase, SmokeContext
from soft_skills_backend.smoke.support.actors import SmokeActorBootstrap
from soft_skills_backend.smoke.support.backend import JsonObject, SmokeBackendClient
from soft_skills_backend.smoke.support.environment import (
    ProviderSmokePreflight,
    SmokeApplicationSessionFactory,
)

from .contracts import PromptLibrarySmokeResult

SMOKE_FLOW_TIMEOUT_SECONDS = 180.0


class PromptLibrarySmoke(SmokeCase):
    """Verify prompt library management and rendering with real provider."""

    name = "prompt-library"
    description = "Run the prompt library CRUD and render flow end to end with real provider."

    def __init__(
        self,
        *,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        flow_timeout_seconds: float = SMOKE_FLOW_TIMEOUT_SECONDS,
    ) -> None:
        self._preflight = preflight or ProviderSmokePreflight()
        self._session_factory = session_factory or SmokeApplicationSessionFactory()
        self._flow_timeout_seconds = flow_timeout_seconds

    def run(self, context: SmokeContext) -> PromptLibrarySmokeResult:
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

    async def _run(self, settings: Settings) -> PromptLibrarySmokeResult:
        async with self._session_factory.open(settings) as backend:
            actors = await SmokeActorBootstrap(backend).prepare()
            admin_user_id = actors.admin_id

            prompt_name = f"smoke-test-prompt-{int(time.time())}"
            prompt_version = "v1"
            prompt_type = "generation"
            template = (
                "Generate content about {topic} for {audience}. "
                "Return JSON with fields: title, content, difficulty."
            )
            variables_schema = {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "The topic to generate content about",
                    },
                    "audience": {"type": "string", "description": "The target audience"},
                },
                "required": ["topic", "audience"],
            }
            output_schema = {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "difficulty": {"type": "string"},
                },
                "required": ["title", "content", "difficulty"],
            }

            created = await self._create_prompt(
                backend=backend,
                admin_user_id=admin_user_id,
                prompt_name=prompt_name,
                version=prompt_version,
                prompt_type=prompt_type,
                template=template,
                variables_schema=variables_schema,
                output_schema=output_schema,
            )

            assert created.get("name") == prompt_name, (
                f"Expected name {prompt_name}, got {created.get('name')}"
            )
            assert created.get("version") == prompt_version, (
                f"Expected version {prompt_version}, got {created.get('version')}"
            )
            assert created.get("status") == "draft", (
                f"Expected status draft, got {created.get('status')}"
            )

            published = await self._publish_prompt(
                backend=backend,
                admin_user_id=admin_user_id,
                prompt_name=prompt_name,
                version=prompt_version,
            )

            assert published.get("status") == "published", (
                f"Expected status published, got {published.get('status')}"
            )

            listed = await self._list_prompts(
                backend=backend,
                admin_user_id=admin_user_id,
            )

            prompt_names = [p.get("name") for p in listed]
            assert prompt_name in prompt_names, f"Expected {prompt_name} in {prompt_names}"

            versions = await self._list_prompt_versions(
                backend=backend,
                admin_user_id=admin_user_id,
                prompt_name=prompt_name,
            )

            assert len(versions) >= 1, f"Expected at least 1 version, got {len(versions)}"
            latest_version = versions[0]
            assert latest_version.get("name") == prompt_name

            analytics = await self._get_prompt_analytics(
                backend=backend,
                admin_user_id=admin_user_id,
                prompt_name=prompt_name,
                version=prompt_version,
            )

            assert analytics.get("name") == prompt_name
            assert analytics.get("version") == prompt_version
            assert analytics.get("render_count") == 0

            lineage_prompt_version_id = created.get("id")
            parent_version_id = created.get("parent_version_id")

            return PromptLibrarySmokeResult(
                status="ok",
                prompt_name=prompt_name,
                prompt_version=prompt_version,
                prompt_type=prompt_type,
                template_length=len(template),
                variables_schema_fields=len(variables_schema.get("properties", {})),
                lineage_prompt_version_id=lineage_prompt_version_id,
                parent_version_id=parent_version_id,
            )

    async def _create_prompt(
        self,
        *,
        backend: SmokeBackendClient,
        admin_user_id: str,
        prompt_name: str,
        version: str,
        prompt_type: str,
        template: str,
        variables_schema: JsonObject,
        output_schema: JsonObject | None,
    ) -> JsonObject:
        payload: JsonObject = {
            "name": prompt_name,
            "version": version,
            "prompt_type": prompt_type,
            "template": template,
            "variables_schema": variables_schema,
        }
        if output_schema is not None:
            payload["output_schema"] = output_schema
        response = await backend._client.post(
            "/api/admin/prompts",
            headers={"X-User-ID": admin_user_id},
            json=payload,
        )
        backend.require_ok(response, f"create prompt {prompt_name}")
        return backend.data(response)

    async def _publish_prompt(
        self,
        *,
        backend: SmokeBackendClient,
        admin_user_id: str,
        prompt_name: str,
        version: str,
    ) -> JsonObject:
        response = await backend._client.post(
            f"/api/admin/prompts/{prompt_name}/versions/{version}/publish",
            headers={"X-User-ID": admin_user_id},
            json={},
        )
        backend.require_ok(response, f"publish prompt {prompt_name}@{version}")
        return backend.data(response)

    async def _list_prompts(
        self,
        *,
        backend: SmokeBackendClient,
        admin_user_id: str,
    ) -> list[JsonObject]:
        response = await backend._client.get(
            "/api/admin/prompts",
            headers={"X-User-ID": admin_user_id},
        )
        backend.require_ok(response, "list prompts")
        return response.json()["data"]

    async def _list_prompt_versions(
        self,
        *,
        backend: SmokeBackendClient,
        admin_user_id: str,
        prompt_name: str,
    ) -> list[JsonObject]:
        response = await backend._client.get(
            f"/api/admin/prompts/{prompt_name}/versions",
            headers={"X-User-ID": admin_user_id},
        )
        backend.require_ok(response, f"list versions for {prompt_name}")
        return response.json()["data"]

    async def _get_prompt_analytics(
        self,
        *,
        backend: SmokeBackendClient,
        admin_user_id: str,
        prompt_name: str,
        version: str,
    ) -> JsonObject:
        response = await backend._client.get(
            f"/api/admin/prompts/{prompt_name}/versions/{version}/analytics",
            headers={"X-User-ID": admin_user_id},
        )
        backend.require_ok(response, f"get analytics for {prompt_name}@{version}")
        return backend.data(response)
