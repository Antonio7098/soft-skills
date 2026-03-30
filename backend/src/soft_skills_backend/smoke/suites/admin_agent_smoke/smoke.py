"""Admin-agent provider-backed smoke suite."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from soft_skills_backend.config import Settings
from soft_skills_backend.modules.assistant.domain.models import (
    AssistantSessionStatus,
    AssistantTurnStatus,
)
from soft_skills_backend.platform.db.models import (
    AssistantSessionRecord,
    AssistantTurnRecord,
    PipelineRunRecord,
    ProviderCallRecord,
    WorkflowEventRecord,
)
from soft_skills_backend.shared.errors import provider_error
from soft_skills_backend.smoke.contracts import SmokeCase, SmokeContext
from soft_skills_backend.smoke.support.actors import SmokeActorBootstrap
from soft_skills_backend.smoke.support.backend import SmokeBackendClient
from soft_skills_backend.smoke.support.environment import (
    ProviderSmokePreflight,
    SmokeApplicationSessionFactory,
)

from .contracts import AdminAgentSmokeResult

ADMIN_AGENT_SMOKE_TIMEOUT_SECONDS = 180.0


class AdminAgentSmoke(SmokeCase):
    """Verify the admin-agent endpoint can plan and run a safe SQL investigation."""

    name = "admin-agent"
    description = "Run a provider-backed admin-agent chat against admin-safe org-scoped views."

    def __init__(
        self,
        *,
        preflight: ProviderSmokePreflight | None = None,
        session_factory: SmokeApplicationSessionFactory | None = None,
        timeout_seconds: float = ADMIN_AGENT_SMOKE_TIMEOUT_SECONDS,
    ) -> None:
        self._preflight = preflight or ProviderSmokePreflight()
        self._session_factory = session_factory or SmokeApplicationSessionFactory(provider_max_retries=2)
        self._timeout_seconds = timeout_seconds

    def run(self, context: SmokeContext) -> AdminAgentSmokeResult:
        self._preflight.assert_ready(context.settings)
        try:
            return asyncio.run(
                asyncio.wait_for(self._run(context.settings), timeout=self._timeout_seconds)
            )
        except TimeoutError as exc:
            raise provider_error(
                "Admin-agent smoke exceeded the allowed runtime budget",
                code="SS-PROVIDER-013",
                details={"timeout_seconds": self._timeout_seconds},
            ) from exc

    async def _run(self, settings: Settings) -> AdminAgentSmokeResult:
        async with self._session_factory.open(settings) as backend:
            actors = await SmokeActorBootstrap(backend).prepare()
            org = await backend.create_organisation(
                user_id=actors.admin_id,
                name="Admin Agent Smoke Org",
                slug=f"admin-agent-smoke-{actors.admin_id[:8]}",
            )
            organisation_id = str(org["id"])
            await backend.add_member(
                user_id=actors.admin_id,
                organisation_id=organisation_id,
                new_member_id=actors.learner_id,
                role="member",
            )
            self._seed_investigation_rows(
                backend,
                organisation_id=organisation_id,
                learner_id=actors.learner_id,
            )

            result = await backend.admin_agent_chat(
                user_id=actors.admin_id,
                organisation_id=organisation_id,
                message=(
                    "Count assistant sessions by session_status for my organisation using only "
                    "admin_agent_assistant_sessions_v. Use one SELECT, no WHERE clause, and "
                    "group by session_status."
                ),
            )

            tool_results = result.get("tool_results", [])
            first_tool = tool_results[0] if isinstance(tool_results, list) and tool_results else {}
            source_views = first_tool.get("source_views", [])
            if not isinstance(source_views, list):
                source_views = []
            row_count = int(first_tool.get("row_count", 0) or 0)
            if "admin_agent_assistant_sessions_v" not in source_views:
                raise provider_error(
                    "Admin-agent smoke used an unexpected source view",
                    code="SS-PROVIDER-011",
                    details={"source_views": source_views},
                )
            if row_count <= 0:
                raise provider_error(
                    "Admin-agent smoke returned zero investigation rows despite seeded data",
                    code="SS-PROVIDER-011",
                    details={"tool_result": first_tool},
                )

            return AdminAgentSmokeResult(
                conversation_id=str(result["conversation_id"]),
                organisation_id=organisation_id,
                session_row_count=row_count,
                source_view_count=len(source_views),
                message_preview=str(result.get("message", ""))[:160],
            )

    def _seed_investigation_rows(
        self,
        backend: SmokeBackendClient,
        *,
        organisation_id: str,
        learner_id: str,
    ) -> None:
        if backend.session_factory is None:
            raise provider_error(
                "Admin-agent smoke requires DB-backed seeding support",
                code="SS-PROVIDER-011",
            )

        now = datetime.now(UTC)
        active_session_id = uuid4().hex
        archived_session_id = uuid4().hex
        pipeline_run_id = uuid4().hex
        trace_id = uuid4().hex
        request_id = uuid4().hex

        with backend.session_factory() as session:
            session.add_all(
                [
                    AssistantSessionRecord(
                        id=active_session_id,
                        user_id=learner_id,
                        title="Admin Agent Active Session",
                        status=AssistantSessionStatus.ACTIVE.value,
                        metadata_payload={"seeded_by": "admin_agent_smoke"},
                        created_at=now - timedelta(minutes=15),
                        updated_at=now - timedelta(minutes=5),
                    ),
                    AssistantSessionRecord(
                        id=archived_session_id,
                        user_id=learner_id,
                        title="Admin Agent Archived Session",
                        status=AssistantSessionStatus.ARCHIVED.value,
                        metadata_payload={"seeded_by": "admin_agent_smoke"},
                        created_at=now - timedelta(hours=2),
                        updated_at=now - timedelta(hours=1),
                    ),
                    AssistantTurnRecord(
                        id=uuid4().hex,
                        session_id=active_session_id,
                        user_id=learner_id,
                        request_id=uuid4().hex,
                        trace_id=uuid4().hex,
                        workflow_id=f"assistant_turn:{uuid4().hex}",
                        pipeline_run_id=None,
                        status=AssistantTurnStatus.COMPLETED.value,
                        stream_token=uuid4().hex + uuid4().hex,
                        user_message_id=None,
                        assistant_message_id=None,
                        last_error_code=None,
                        cancel_reason=None,
                        tool_call_count=0,
                        metadata_payload={"seeded_by": "admin_agent_smoke"},
                        created_at=now - timedelta(minutes=14),
                        started_at=now - timedelta(minutes=14),
                        completed_at=now - timedelta(minutes=13),
                        cancelled_at=None,
                    ),
                    AssistantTurnRecord(
                        id=uuid4().hex,
                        session_id=active_session_id,
                        user_id=learner_id,
                        request_id=uuid4().hex,
                        trace_id=uuid4().hex,
                        workflow_id=f"assistant_turn:{uuid4().hex}",
                        pipeline_run_id=None,
                        status=AssistantTurnStatus.COMPLETED.value,
                        stream_token=uuid4().hex + uuid4().hex,
                        user_message_id=None,
                        assistant_message_id=None,
                        last_error_code=None,
                        cancel_reason=None,
                        tool_call_count=0,
                        metadata_payload={"seeded_by": "admin_agent_smoke"},
                        created_at=now - timedelta(minutes=12),
                        started_at=now - timedelta(minutes=12),
                        completed_at=now - timedelta(minutes=11),
                        cancelled_at=None,
                    ),
                    AssistantTurnRecord(
                        id=uuid4().hex,
                        session_id=archived_session_id,
                        user_id=learner_id,
                        request_id=uuid4().hex,
                        trace_id=uuid4().hex,
                        workflow_id=f"assistant_turn:{uuid4().hex}",
                        pipeline_run_id=None,
                        status=AssistantTurnStatus.FAILED.value,
                        stream_token=uuid4().hex + uuid4().hex,
                        user_message_id=None,
                        assistant_message_id=None,
                        last_error_code="SS-SMOKE-001",
                        cancel_reason=None,
                        tool_call_count=0,
                        metadata_payload={"seeded_by": "admin_agent_smoke"},
                        created_at=now - timedelta(hours=2),
                        started_at=now - timedelta(hours=2),
                        completed_at=now - timedelta(hours=2) + timedelta(minutes=1),
                        cancelled_at=None,
                    ),
                    PipelineRunRecord(
                        pipeline_run_id=pipeline_run_id,
                        pipeline_name="admin_agent_smoke_seed",
                        topology="seeded_investigation",
                        execution_mode="smoke_seed",
                        status="completed",
                        request_id=request_id,
                        trace_id=trace_id,
                        user_id=learner_id,
                        error=None,
                        failed_stage=None,
                        stage_results={"seeded_rows": 2},
                        started_at=now - timedelta(minutes=10),
                        finished_at=now - timedelta(minutes=9),
                    ),
                    ProviderCallRecord(
                        call_id=uuid4().hex,
                        operation="admin_agent_smoke.seeded_provider_call",
                        provider="smoke-provider",
                        model_id="smoke-model",
                        success=True,
                        latency_ms=187,
                        error=None,
                        pipeline_run_id=pipeline_run_id,
                        request_id=request_id,
                        trace_id=trace_id,
                        metrics={"seeded_by": "admin_agent_smoke"},
                        created_at=now - timedelta(minutes=9),
                    ),
                    WorkflowEventRecord(
                        event_id=uuid4().hex,
                        event_type="admin.agent.seeded.v1",
                        request_id=request_id,
                        trace_id=trace_id,
                        workflow_id=f"admin_agent_smoke:{pipeline_run_id}",
                        error_code=None,
                        organisation_id=organisation_id,
                        payload={"seeded_by": "admin_agent_smoke", "assistant_session_count": 2},
                        occurred_at=now - timedelta(minutes=9),
                    ),
                ]
            )
            session.commit()
