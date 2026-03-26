"""HTTP client wrapper for smoke backend interactions."""

from __future__ import annotations

from typing import cast

import httpx

from soft_skills_backend.shared.errors import provider_error

JsonObject = dict[str, object]


class SmokeBackendClient:
    """Typed wrapper around smoke backend HTTP calls."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def register_user(
        self,
        *,
        email: str,
        display_name: str,
        role: str = "standard_user",
    ) -> JsonObject:
        response = await self._client.post(
            "/api/auth/register",
            json={
                "email": email,
                "display_name": display_name,
                "role": role,
                "target_role": "Consultant",
                "goals": ["Improve stakeholder handling"],
                "practice_preferences": {"session_length": "short"},
            },
        )
        self.require_ok(response, "register user")
        return self.data(response)

    async def bootstrap_canon(self, user_id: str) -> None:
        response = await self._client.post(
            "/api/skills/bootstrap-canon",
            headers={"X-User-ID": user_id},
        )
        self.require_ok(response, "bootstrap canon")

    async def create_collection(
        self,
        *,
        user_id: str,
        title: str,
        content_format_mix: list[str],
        target_skill_slugs: list[str],
        target_competency_slugs: list[str],
        rubric_ids: list[str],
    ) -> str:
        response = await self._client.post(
            "/api/collections",
            headers={"X-User-ID": user_id},
            json={
                "title": title,
                "summary": f"{title} smoke content.",
                "target_audience": "Early-career consultants",
                "difficulty": "intermediate",
                "content_format_mix": content_format_mix,
                "target_skill_slugs": target_skill_slugs,
                "target_competency_slugs": target_competency_slugs,
                "rubric_ids": rubric_ids,
            },
        )
        self.require_ok(response, f"create collection {title}")
        return str(self.data(response)["id"])

    async def create_prompt_item(
        self,
        *,
        collection_id: str,
        user_id: str,
        payload: JsonObject,
        operation: str,
    ) -> JsonObject:
        response = await self._client.post(
            f"/api/collections/{collection_id}/prompt-items",
            headers={"X-User-ID": user_id},
            json=payload,
        )
        self.require_ok(response, operation)
        return self.data(response)

    async def create_scenario(
        self,
        *,
        collection_id: str,
        user_id: str,
        payload: JsonObject,
    ) -> JsonObject:
        response = await self._client.post(
            f"/api/collections/{collection_id}/scenarios",
            headers={"X-User-ID": user_id},
            json=payload,
        )
        self.require_ok(response, "create scenario")
        return self.data(response)

    async def generate_structured_collection(self, *, user_id: str) -> JsonObject:
        response = await self._client.post(
            "/api/collections/generate/structured",
            headers={"X-User-ID": user_id},
            json={
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
        self.require_ok(response, "generate structured collection")
        payload = self.data(response)
        return cast(JsonObject, payload["collection"])

    async def generate_chat_collection(self, *, user_id: str) -> JsonObject:
        response = await self._client.post(
            "/api/collections/generate/chat",
            headers={"X-User-ID": user_id},
            json={
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
        self.require_ok(response, "generate chat collection")
        payload = self.data(response)
        return cast(JsonObject, payload["collection"])

    async def start_quick_practice_session(self, *, user_id: str, prompt_item_id: str) -> JsonObject:
        response = await self._client.post(
            "/api/attempts/quick-practice/sessions",
            headers={"X-User-ID": user_id},
            json={"prompt_item_id": prompt_item_id},
        )
        self.require_ok(response, "start quick-practice session")
        return self.data(response)

    async def start_interview_session(
        self,
        *,
        user_id: str,
        prompt_item_id: str,
        competency_context: str,
        interviewer_perspective: str,
    ) -> JsonObject:
        response = await self._client.post(
            "/api/attempts/interview/sessions",
            headers={"X-User-ID": user_id},
            json={
                "prompt_item_id": prompt_item_id,
                "competency_context": competency_context,
                "interviewer_perspective": interviewer_perspective,
            },
        )
        self.require_ok(response, "start interview session")
        return self.data(response)

    async def start_scenario_session(
        self,
        *,
        user_id: str,
        scenario_id: str,
        artifacts: list[JsonObject],
    ) -> JsonObject:
        response = await self._client.post(
            "/api/attempts/scenario/sessions",
            headers={"X-User-ID": user_id},
            json={"scenario_id": scenario_id, "artifacts": artifacts},
        )
        self.require_ok(response, "start scenario session")
        return self.data(response)

    async def get_attempt(self, *, user_id: str, attempt_id: str) -> JsonObject:
        response = await self._client.get(
            f"/api/attempts/{attempt_id}",
            headers={"X-User-ID": user_id},
        )
        self.require_ok(response, f"get attempt {attempt_id}")
        return self.data(response)

    async def start_practice_run(self, *, user_id: str, payload: JsonObject) -> JsonObject:
        response = await self._client.post(
            "/api/practice-runs",
            headers={"X-User-ID": user_id},
            json=payload,
        )
        self.require_ok(response, "start aggregate practice run")
        return self.data(response)

    async def submit_attempt_response(
        self,
        *,
        user_id: str,
        attempt_id: str,
        response_text: str,
    ) -> httpx.Response:
        return await self._client.post(
            f"/api/attempts/{attempt_id}/submit",
            headers={"X-User-ID": user_id},
            json={"response_text": response_text},
        )

    async def submit_attempt(self, *, user_id: str, attempt_id: str, response_text: str) -> None:
        response = await self.submit_attempt_response(
            user_id=user_id,
            attempt_id=attempt_id,
            response_text=response_text,
        )
        self.require_ok(response, f"submit aggregate attempt {attempt_id}")

    async def get_practice_run(self, *, user_id: str, run_id: str) -> JsonObject:
        response = await self._client.get(
            f"/api/practice-runs/{run_id}",
            headers={"X-User-ID": user_id},
        )
        self.require_ok(response, "fetch aggregate practice run")
        return self.data(response)

    async def list_practice_runs(self, *, user_id: str) -> list[JsonObject]:
        response = await self._client.get(
            "/api/practice-runs",
            headers={"X-User-ID": user_id},
        )
        self.require_ok(response, "list aggregate practice runs")
        return cast(list[JsonObject], response.json()["data"])

    @staticmethod
    def data(response: httpx.Response) -> JsonObject:
        return cast(JsonObject, response.json()["data"])

    @staticmethod
    def require_ok(response: httpx.Response, operation: str) -> None:
        if response.status_code == 200:
            return
        raise provider_error(
            "Smoke backend step failed",
            code="SS-PROVIDER-011",
            details={
                "operation": operation,
                "status_code": response.status_code,
                "body": response.text,
            },
        )
