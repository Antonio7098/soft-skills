"""HTTP client wrapper for smoke backend interactions."""

from __future__ import annotations

import asyncio
from typing import cast

import httpx
from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.shared.errors import provider_error

JsonObject = dict[str, object]


class SmokeBackendClient:
    """Typed wrapper around smoke backend HTTP calls."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        session_factory: sessionmaker[Session] | None = None,
    ) -> None:
        self._client = client
        self.session_factory = session_factory

    async def register_user(
        self,
        *,
        email: str,
        display_name: str,
    ) -> JsonObject:
        response = await self._client.post(
            "/api/auth/register",
            json={
                "email": email,
                "display_name": display_name,
                "target_role": "Consultant",
                "goals": ["Improve stakeholder handling"],
                "practice_preferences": {"session_length": "short"},
            },
        )
        self.require_ok(response, "register user")
        return self.data(response)

    async def get_user_me(self, *, user_id: str) -> JsonObject:
        response = await self._client.get(
            "/api/users/me",
            headers={"X-User-ID": user_id},
        )
        self.require_ok(response, "get current user")
        return self.data(response)

    async def update_profile(
        self,
        *,
        user_id: str,
        target_role: str | None = None,
        goals: list[str] | None = None,
        practice_preferences: dict[str, object] | None = None,
    ) -> JsonObject:
        payload: dict[str, object] = {}
        if target_role is not None:
            payload["target_role"] = target_role
        if goals is not None:
            payload["goals"] = goals
        if practice_preferences is not None:
            payload["practice_preferences"] = practice_preferences
        response = await self._client.patch(
            "/api/users/me/profile",
            headers={"X-User-ID": user_id},
            json=payload,
        )
        self.require_ok(response, "update user profile")
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
        payload = await self.generate_structured_collection_payload(
            user_id=user_id,
            payload={
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
        return cast(JsonObject, payload["collection"])

    async def generate_structured_collection_payload(
        self,
        *,
        user_id: str,
        payload: JsonObject,
    ) -> JsonObject:
        response = await self._client.post(
            "/api/collections/generate/structured",
            headers={"X-User-ID": user_id},
            json=payload,
        )
        self.require_ok(response, "generate structured collection")
        return self.data(response)

    async def generate_chat_collection(self, *, user_id: str) -> JsonObject:
        payload = await self.generate_chat_collection_payload(
            user_id=user_id,
            payload={
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
        return cast(JsonObject, payload["collection"])

    async def generate_chat_collection_payload(
        self,
        *,
        user_id: str,
        payload: JsonObject,
    ) -> JsonObject:
        response = await self._client.post(
            "/api/collections/generate/chat",
            headers={"X-User-ID": user_id},
            json=payload,
        )
        self.require_ok(response, "generate chat collection")
        return self.data(response)

    async def generate_structured_prompt_items(
        self,
        *,
        user_id: str,
        collection_id: str,
    ) -> JsonObject:
        return await self.generate_structured_prompt_items_payload(
            user_id=user_id,
            collection_id=collection_id,
            payload={
                "title_hint": "Smoke Prompt Expansion",
                "workplace_context": "A senior stakeholder is escalating delivery risk after new legal feedback.",
                "generation_focus": "Generate one realistic interview prompt about resetting expectations under pressure.",
                "realism_notes": ["Keep the conflict concrete and business-relevant."],
                "target_skill_slugs": ["decision-justification"],
                "counts": {
                    "quick_practice_prompt_count": 0,
                    "interview_prompt_count": 1,
                },
            },
        )

    async def generate_structured_prompt_items_payload(
        self,
        *,
        user_id: str,
        collection_id: str,
        payload: JsonObject,
    ) -> JsonObject:
        response = await self._client.post(
            f"/api/collections/{collection_id}/generate/prompt-items/structured",
            headers={"X-User-ID": user_id},
            json=payload,
        )
        self.require_ok(response, "generate structured prompt items")
        return self.data(response)

    async def generate_chat_prompt_items(
        self,
        *,
        user_id: str,
        collection_id: str,
    ) -> JsonObject:
        return await self.generate_chat_prompt_items_payload(
            user_id=user_id,
            collection_id=collection_id,
            payload={
                "prompt": (
                    "Add an interview prompt about defending a decision made with incomplete "
                    "information while keeping a senior stakeholder aligned."
                ),
                "target_skill_slugs": ["decision-justification"],
                "counts": {
                    "quick_practice_prompt_count": 0,
                    "interview_prompt_count": 1,
                },
            },
        )

    async def generate_chat_prompt_items_payload(
        self,
        *,
        user_id: str,
        collection_id: str,
        payload: JsonObject,
    ) -> JsonObject:
        response = await self._client.post(
            f"/api/collections/{collection_id}/generate/prompt-items/chat",
            headers={"X-User-ID": user_id},
            json=payload,
        )
        self.require_ok(response, "generate chat prompt items")
        return self.data(response)

    async def start_quick_practice_session(
        self, *, user_id: str, prompt_item_id: str
    ) -> JsonObject:
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

    async def create_assistant_session(
        self,
        *,
        user_id: str,
        title: str | None = None,
    ) -> JsonObject:
        response = await self._client.post(
            "/api/assistant/sessions",
            headers={"X-User-ID": user_id},
            json={} if title is None else {"title": title},
        )
        self.require_ok(response, "create assistant session")
        return self.data(response)

    async def create_assistant_turn(
        self,
        *,
        user_id: str,
        session_id: str,
        message: str,
        organisation_id: str | None = None,
    ) -> JsonObject:
        response = await self._client.post(
            f"/api/assistant/sessions/{session_id}/turns",
            headers={
                "X-User-ID": user_id,
                **(
                    {}
                    if organisation_id is None
                    else {"X-Organisation-ID": organisation_id}
                ),
            },
            json={"message": message},
        )
        self.require_ok(response, "create assistant turn")
        return self.data(response)

    async def admin_agent_chat(
        self,
        *,
        user_id: str,
        organisation_id: str,
        message: str,
        conversation_id: str | None = None,
    ) -> JsonObject:
        payload: JsonObject = {"message": message}
        if conversation_id is not None:
            payload["conversation_id"] = conversation_id
        response = await self._client.post(
            "/api/admin-agent/chat",
            headers={
                "X-User-ID": user_id,
                "X-Organisation-ID": organisation_id,
            },
            json=payload,
        )
        self.require_ok(response, "run admin agent chat")
        return self.data(response)

    async def get_assistant_session(self, *, user_id: str, session_id: str) -> JsonObject:
        response = await self._client.get(
            f"/api/assistant/sessions/{session_id}",
            headers={"X-User-ID": user_id},
        )
        self.require_ok(response, "get assistant session")
        return self.data(response)

    async def list_assistant_sessions(self, *, user_id: str) -> list[JsonObject]:
        response = await self._client.get(
            "/api/assistant/sessions",
            headers={"X-User-ID": user_id},
        )
        self.require_ok(response, "list assistant sessions")
        return cast(list[JsonObject], response.json()["data"])

    async def list_assistant_messages(self, *, user_id: str, session_id: str) -> list[JsonObject]:
        response = await self._client.get(
            f"/api/assistant/sessions/{session_id}/messages",
            headers={"X-User-ID": user_id},
        )
        self.require_ok(response, "list assistant messages")
        return cast(list[JsonObject], response.json()["data"])

    async def list_assistant_approvals(
        self,
        *,
        user_id: str,
        status: str | None = None,
    ) -> list[JsonObject]:
        params = {} if status is None else {"status": status}
        response = await self._client.get(
            "/api/assistant/approvals",
            headers={"X-User-ID": user_id},
            params=params,
        )
        self.require_ok(response, "list assistant approvals")
        return cast(list[JsonObject], response.json()["data"])

    async def decide_assistant_approval(
        self,
        *,
        user_id: str,
        request_id: str,
        decision: str,
        reason: str | None = None,
    ) -> JsonObject:
        payload: JsonObject = {"decision": decision}
        if reason is not None:
            payload["reason"] = reason
        response = await self._client.post(
            f"/api/assistant/approvals/{request_id}",
            headers={"X-User-ID": user_id},
            json=payload,
        )
        self.require_ok(response, "decide assistant approval")
        return self.data(response)

    async def wait_for_assistant_turn(
        self,
        *,
        user_id: str,
        session_id: str,
        turn_id: str,
        timeout_seconds: float = 120.0,
        poll_interval_seconds: float = 0.5,
    ) -> JsonObject:
        deadline = asyncio.get_running_loop().time() + timeout_seconds
        while True:
            session_payload = await self.get_assistant_session(
                user_id=user_id, session_id=session_id
            )
            for turn in cast(list[JsonObject], session_payload.get("turns", [])):
                if str(turn.get("id")) != turn_id:
                    continue
                status = str(turn.get("status"))
                if status in {"completed", "failed", "cancelled"}:
                    return turn
            if asyncio.get_running_loop().time() >= deadline:
                raise provider_error(
                    "Smoke backend step failed",
                    code="SS-PROVIDER-011",
                    details={"operation": "wait for assistant turn", "turn_id": turn_id},
                )
            await asyncio.sleep(poll_interval_seconds)

    async def create_organisation(
        self,
        *,
        user_id: str,
        name: str,
        slug: str,
    ) -> JsonObject:
        response = await self._client.post(
            "/api/organisations",
            headers={"X-User-ID": user_id},
            json={"name": name, "slug": slug},
        )
        self.require_ok(response, f"create organisation {slug}")
        return self.data(response)

    async def get_organisation(
        self,
        *,
        user_id: str,
        organisation_id: str,
    ) -> JsonObject:
        response = await self._client.get(
            f"/api/organisations/{organisation_id}",
            headers={"X-User-ID": user_id, "X-Organisation-ID": organisation_id},
        )
        self.require_ok(response, f"get organisation {organisation_id}")
        return self.data(response)

    async def update_organisation(
        self,
        *,
        user_id: str,
        organisation_id: str,
        payload: JsonObject,
    ) -> JsonObject:
        response = await self._client.patch(
            f"/api/organisations/{organisation_id}",
            headers={"X-User-ID": user_id, "X-Organisation-ID": organisation_id},
            json=payload,
        )
        self.require_ok(response, f"update organisation {organisation_id}")
        return self.data(response)

    async def list_members(
        self,
        *,
        user_id: str,
        organisation_id: str,
    ) -> list[JsonObject]:
        response = await self._client.get(
            f"/api/organisations/{organisation_id}/members",
            headers={"X-User-ID": user_id, "X-Organisation-ID": organisation_id},
        )
        self.require_ok(response, f"list organisation members {organisation_id}")
        return cast(list[JsonObject], response.json()["data"])

    async def add_member(
        self,
        *,
        user_id: str,
        organisation_id: str,
        new_member_id: str,
        role: str = "member",
    ) -> JsonObject:
        response = await self._client.post(
            f"/api/organisations/{organisation_id}/members",
            headers={"X-User-ID": user_id, "X-Organisation-ID": organisation_id},
            json={"user_id": new_member_id, "role": role},
        )
        self.require_ok(response, f"add member to organisation {organisation_id}")
        return self.data(response)

    async def update_member(
        self,
        *,
        user_id: str,
        organisation_id: str,
        member_id: str,
        role: str,
    ) -> JsonObject:
        response = await self._client.patch(
            f"/api/organisations/{organisation_id}/members/{member_id}",
            headers={"X-User-ID": user_id, "X-Organisation-ID": organisation_id},
            json={"role": role},
        )
        self.require_ok(response, f"update member role in organisation {organisation_id}")
        return self.data(response)

    async def remove_member(
        self,
        *,
        user_id: str,
        organisation_id: str,
        member_id: str,
    ) -> None:
        response = await self._client.delete(
            f"/api/organisations/{organisation_id}/members/{member_id}",
            headers={"X-User-ID": user_id, "X-Organisation-ID": organisation_id},
        )
        self.require_ok(response, f"remove member from organisation {organisation_id}")

    async def list_evaluation_suites(self, *, user_id: str) -> list[JsonObject]:
        response = await self._client.get(
            "/api/admin/evaluations/suites",
            headers={"X-User-ID": user_id},
        )
        self.require_ok(response, "list evaluation suites")
        return cast(list[JsonObject], response.json()["data"])

    async def run_evaluation(
        self,
        *,
        user_id: str,
        suite_id: str,
        model_slugs: list[str] | None = None,
        case_ids: list[str] | None = None,
    ) -> JsonObject:
        response = await self._client.post(
            "/api/admin/evaluations/runs",
            headers={"X-User-ID": user_id},
            json={
                "suite_id": suite_id,
                "model_slugs": list(model_slugs or []),
                "case_ids": list(case_ids or []),
            },
        )
        self.require_ok(response, f"run evaluation suite {suite_id}")
        return self.data(response)

    async def get_evaluation_run(self, *, user_id: str, evaluation_run_id: str) -> JsonObject:
        response = await self._client.get(
            f"/api/admin/evaluations/runs/{evaluation_run_id}",
            headers={"X-User-ID": user_id},
        )
        self.require_ok(response, f"get evaluation run {evaluation_run_id}")
        return self.data(response)

    async def get_evaluation_dashboard(self, *, user_id: str) -> JsonObject:
        response = await self._client.get(
            "/api/admin/evaluations/dashboard",
            headers={"X-User-ID": user_id},
        )
        self.require_ok(response, "get evaluation dashboard")
        return self.data(response)

    async def get_evaluation_benchmark(self, *, user_id: str) -> JsonObject:
        response = await self._client.get(
            "/api/admin/evaluations/benchmark",
            headers={"X-User-ID": user_id},
        )
        self.require_ok(response, "get evaluation benchmark")
        return self.data(response)

    async def compare_evaluation_runs(
        self, *, user_id: str, run_ids: list[str] | None = None
    ) -> JsonObject:
        params = {}
        if run_ids:
            params["run_ids"] = ",".join(run_ids)
        response = await self._client.get(
            "/api/admin/evaluations/runs/compare",
            headers={"X-User-ID": user_id},
            params=params,
        )
        self.require_ok(response, "compare evaluation runs")
        return self.data(response)

    async def get_evaluation_case_detail(self, *, user_id: str, case_id: str) -> JsonObject:
        response = await self._client.get(
            f"/api/admin/evaluations/cases/{case_id}",
            headers={"X-User-ID": user_id},
        )
        self.require_ok(response, f"get evaluation case detail {case_id}")
        return self.data(response)

    async def admin_list_users(
        self,
        *,
        user_id: str,
        organisation_id: str,
        offset: int = 0,
        limit: int = 50,
        search: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
    ) -> JsonObject:
        params: dict[str, str | int | bool] = {"offset": offset, "limit": limit}
        if search:
            params["search"] = search
        if role:
            params["role"] = role
        if is_active is not None:
            params["is_active"] = str(is_active).lower()
        response = await self._client.get(
            "/api/admin/users",
            headers={"X-User-ID": user_id, "X-Organisation-ID": organisation_id},
            params=params,
        )
        self.require_ok(response, "admin list users")
        return self.data(response)

    async def admin_get_user(
        self,
        *,
        user_id: str,
        organisation_id: str,
        target_user_id: str,
    ) -> JsonObject:
        response = await self._client.get(
            f"/api/admin/users/{target_user_id}",
            headers={"X-User-ID": user_id, "X-Organisation-ID": organisation_id},
        )
        self.require_ok(response, f"admin get user {target_user_id}")
        return self.data(response)

    async def admin_update_user_role(
        self,
        *,
        user_id: str,
        organisation_id: str,
        target_user_id: str,
        role: str,
    ) -> JsonObject:
        response = await self._client.put(
            f"/api/admin/users/{target_user_id}/role",
            headers={"X-User-ID": user_id, "X-Organisation-ID": organisation_id},
            json={"role": role},
        )
        self.require_ok(response, f"admin update user role for {target_user_id}")
        return self.data(response)

    async def admin_update_user_status(
        self,
        *,
        user_id: str,
        organisation_id: str,
        target_user_id: str,
        is_active: bool,
    ) -> JsonObject:
        response = await self._client.patch(
            f"/api/admin/users/{target_user_id}/status",
            headers={"X-User-ID": user_id, "X-Organisation-ID": organisation_id},
            json={"is_active": is_active},
        )
        self.require_ok(response, f"admin update user status for {target_user_id}")
        return self.data(response)

    async def admin_add_user(
        self,
        *,
        user_id: str,
        organisation_id: str,
        email: str,
        role: str = "member",
    ) -> JsonObject:
        response = await self._client.post(
            "/api/admin/users",
            headers={"X-User-ID": user_id, "X-Organisation-ID": organisation_id},
            json={"email": email, "role": role},
        )
        self.require_ok(response, f"admin add user {email}")
        return self.data(response)

    async def admin_bulk_user_operation(
        self,
        *,
        user_id: str,
        organisation_id: str,
        user_ids: list[str],
        operation: str,
        payload: dict[str, object] | None = None,
    ) -> JsonObject:
        json_body: dict[str, object] = {
            "user_ids": user_ids,
            "operation": operation,
        }
        if payload:
            json_body["payload"] = payload
        response = await self._client.post(
            "/api/admin/users/bulk",
            headers={"X-User-ID": user_id, "X-Organisation-ID": organisation_id},
            json=json_body,
        )
        self.require_ok(response, f"admin bulk user operation {operation}")
        return self.data(response)

    async def admin_get_user_activity(
        self,
        *,
        user_id: str,
        organisation_id: str,
        target_user_id: str,
    ) -> JsonObject:
        response = await self._client.get(
            f"/api/admin/users/{target_user_id}/activity",
            headers={"X-User-ID": user_id, "X-Organisation-ID": organisation_id},
        )
        self.require_ok(response, f"admin get user activity for {target_user_id}")
        return self.data(response)

    async def admin_get_learner_analytics(
        self,
        *,
        user_id: str,
        organisation_id: str,
        learner_id: str,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> JsonObject:
        params: dict[str, str] = {}
        if from_date:
            params["from_date"] = from_date
        if to_date:
            params["to_date"] = to_date
        response = await self._client.get(
            f"/api/admin/learners/{learner_id}/analytics",
            headers={"X-User-ID": user_id, "X-Organisation-ID": organisation_id},
            params=params,
        )
        self.require_ok(response, f"admin get learner analytics for {learner_id}")
        return self.data(response)

    async def admin_get_cohort_analytics(
        self,
        *,
        user_id: str,
        organisation_id: str,
        target_role: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> JsonObject:
        params: dict[str, str] = {}
        if target_role:
            params["target_role"] = target_role
        if from_date:
            params["from_date"] = from_date
        if to_date:
            params["to_date"] = to_date
        response = await self._client.get(
            "/api/admin/cohorts/analytics",
            headers={"X-User-ID": user_id, "X-Organisation-ID": organisation_id},
            params=params,
        )
        self.require_ok(response, "admin get cohort analytics")
        return self.data(response)

    async def admin_get_analytics_overview(
        self,
        *,
        user_id: str,
        organisation_id: str,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> JsonObject:
        params: dict[str, str] = {}
        if from_date:
            params["from_date"] = from_date
        if to_date:
            params["to_date"] = to_date
        response = await self._client.get(
            "/api/admin/analytics/overview",
            headers={"X-User-ID": user_id, "X-Organisation-ID": organisation_id},
            params=params,
        )
        self.require_ok(response, "admin get analytics overview")
        return self.data(response)

    async def admin_get_cohort_comparison(
        self,
        *,
        user_id: str,
        organisation_id: str,
        cohort_keys: str,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> JsonObject:
        params: dict[str, str] = {"cohort_keys": cohort_keys}
        if from_date:
            params["from_date"] = from_date
        if to_date:
            params["to_date"] = to_date
        response = await self._client.get(
            "/api/admin/cohorts/comparison",
            headers={"X-User-ID": user_id, "X-Organisation-ID": organisation_id},
            params=params,
        )
        self.require_ok(response, "admin get cohort comparison")
        return self.data(response)

    async def admin_export_analytics(
        self,
        *,
        user_id: str,
        organisation_id: str,
        format: str = "json",
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> JsonObject:
        params: dict[str, str] = {"format": format}
        if from_date:
            params["from_date"] = from_date
        if to_date:
            params["to_date"] = to_date
        response = await self._client.get(
            "/api/admin/analytics/export",
            headers={"X-User-ID": user_id, "X-Organisation-ID": organisation_id},
            params=params,
        )
        self.require_ok(response, "admin export analytics")
        return {"status": "exported", "format": format}

    async def admin_get_telemetry_overview(
        self,
        *,
        user_id: str,
        organisation_id: str,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> JsonObject:
        params: dict[str, str] = {}
        if from_date:
            params["from_date"] = from_date
        if to_date:
            params["to_date"] = to_date
        response = await self._client.get(
            "/api/admin/telemetry/overview",
            headers={"X-User-ID": user_id, "X-Organisation-ID": organisation_id},
            params=params,
        )
        self.require_ok(response, "admin get telemetry overview")
        return self.data(response)

    async def admin_list_telemetry_traces(
        self,
        *,
        user_id: str,
        organisation_id: str,
        offset: int = 0,
        limit: int = 50,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> JsonObject:
        params: dict[str, str | int] = {"offset": offset, "limit": limit}
        if from_date:
            params["from_date"] = from_date
        if to_date:
            params["to_date"] = to_date
        response = await self._client.get(
            "/api/admin/telemetry/traces",
            headers={"X-User-ID": user_id, "X-Organisation-ID": organisation_id},
            params=params,
        )
        self.require_ok(response, "admin list telemetry traces")
        return self.data(response)

    async def admin_get_telemetry_trace(
        self,
        *,
        user_id: str,
        organisation_id: str,
        trace_id: str,
    ) -> JsonObject:
        response = await self._client.get(
            f"/api/admin/telemetry/traces/{trace_id}",
            headers={"X-User-ID": user_id, "X-Organisation-ID": organisation_id},
        )
        self.require_ok(response, f"admin get telemetry trace {trace_id}")
        return self.data(response)

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
