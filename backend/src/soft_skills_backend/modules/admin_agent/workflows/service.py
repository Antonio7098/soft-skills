"""Stageflow-backed admin-agent workflow."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast

from stageflow.api import Pipeline, StageKind, stage
from stageflow.core import StageContext

from soft_skills_backend.config import LLMTaskKind, Settings
from soft_skills_backend.engines.marking.use_cases.structured_output import (
    StructuredOutputRejectionError,
    StructuredOutputRepairMode,
    TypedLLMOutput,
)
from soft_skills_backend.modules.admin_agent.contracts.commands import QueryAdminDataCommand
from soft_skills_backend.modules.admin_agent.contracts.sql import AdminAgentPlan
from soft_skills_backend.modules.admin_agent.contracts.views import (
    AdminAgentChatView,
    AdminAgentResponseMetadataView,
    QueryAdminDataResultView,
)
from soft_skills_backend.modules.admin_agent.domain.schema_registry import (
    AdminAgentSchemaRegistry,
)
from soft_skills_backend.modules.admin_agent.infra.repository import AdminAgentRepository
from soft_skills_backend.modules.admin_agent.infra.sql_executor import AdminAgentSqlExecutor
from soft_skills_backend.modules.admin_agent.infra.sql_guard import AdminAgentSqlGuard
from soft_skills_backend.platform.workflows.stageflow import (
    StageflowPipelineSupport,
    StageflowStageResult,
    ok_output,
    payload_from_inputs,
    payload_from_results,
    run_logged_pipeline,
)
from soft_skills_backend.platform.workflows.stageflow_runtime import StageflowRuntime
from soft_skills_backend.shared.auth import Actor
from soft_skills_backend.shared.errors import AppError, orchestration_error
from soft_skills_backend.shared.ports.llm import LLMProvider
from soft_skills_backend.shared.ports.telemetry import ProviderCallContext

ADMIN_AGENT_QUERY_TOOL = "query_admin_data"


@dataclass(frozen=True, slots=True)
class AdminAgentExecutionInput:
    actor: Actor
    request_id: str
    trace_id: str
    workflow_id: str
    conversation_id: str
    message: str


@dataclass(frozen=True, slots=True)
class _ContextPayload:
    schema_context: str
    conversation_history: list[dict[str, Any]]


@dataclass(frozen=True, slots=True)
class _PlanPayload:
    plan: AdminAgentPlan
    prompt_version: str
    provider: str
    model_slug: str


class AdminAgentWorkflowService:
    """Plan and execute org-scoped admin investigations through one SQL tool."""

    def __init__(
        self,
        *,
        settings: Settings,
        llm_provider: LLMProvider,
        repository: AdminAgentRepository,
        schema_registry: AdminAgentSchemaRegistry,
        sql_guard: AdminAgentSqlGuard,
        sql_executor: AdminAgentSqlExecutor,
        stageflow_runtime: StageflowRuntime,
    ) -> None:
        self._settings = settings
        self._llm_provider = llm_provider
        self._repository = repository
        self._schema_registry = schema_registry
        self._sql_guard = sql_guard
        self._sql_executor = sql_executor
        self._stageflow = StageflowPipelineSupport.from_runtime(stageflow_runtime)
        self._typed_output = TypedLLMOutput(
            AdminAgentPlan,
            schema_version="admin_agent_plan.v1",
            max_validation_retries=0,
            repair_mode=StructuredOutputRepairMode.FAIL_FAST,
            timeout_seconds=settings.llm_admin_agent_timeout_seconds,
            transport_schema_name="admin_agent_plan",
        )

    async def run_chat(self, execution: AdminAgentExecutionInput) -> AdminAgentChatView:
        self._assert_query_tool_auto_allowed()
        pipeline = self._build_pipeline(execution)
        results = await run_logged_pipeline(
            self._stageflow,
            pipeline,
            request_id=execution.request_id,
            trace_id=execution.trace_id,
            workflow_id=execution.workflow_id,
            user_id=execution.actor.user_id,
            execution_mode="admin_agent_chat",
            service="soft_skills_backend.admin_agent",
            idempotency_key=(
                f"admin_agent_chat:{execution.workflow_id}:{execution.request_id}:{execution.message}"
            ),
            idempotency_params={"conversation_id": execution.conversation_id},
            timeout_ms=max(120_000, int(self._settings.smoke_timeout_seconds * 1000 * 2)),
        )
        return payload_from_results(
            results,
            "response_formulation",
            expected_type=AdminAgentChatView,
        )

    def _assert_query_tool_auto_allowed(self) -> None:
        if ADMIN_AGENT_QUERY_TOOL not in self._settings.tool_approval_auto_allow:
            raise orchestration_error(
                "Admin agent SQL tool must be auto-allowed for the MVP read-only workflow",
                code="SS-ORCHESTRATION-302",
                details={"tool_name": ADMIN_AGENT_QUERY_TOOL},
            )

    def _build_pipeline(self, execution: AdminAgentExecutionInput) -> Pipeline:
        async def input_guard(_ctx: StageContext) -> Any:
            if execution.actor.organisation_id is None or not execution.actor.is_org_admin:
                raise orchestration_error(
                    "Admin agent requires an organisation admin actor",
                    code="SS-ORCHESTRATION-303",
                )
            self._record_event(
                execution,
                event_type="admin.agent.request.received.v1",
                payload={"question": execution.message},
            )
            return ok_output(
                StageflowStageResult(
                    payload={"conversation_id": execution.conversation_id},
                    summary={"conversation_id": execution.conversation_id},
                )
            )

        async def context_enrich(_ctx: StageContext) -> Any:
            history = self._repository.list_conversation_history(
                conversation_id=execution.conversation_id,
                organisation_id=cast(str, execution.actor.organisation_id),
                limit=self._settings.admin_agent_conversation_history_limit,
            )
            payload = _ContextPayload(
                schema_context=self._schema_registry.render_prompt_context(),
                conversation_history=history,
            )
            self._record_event(
                execution,
                event_type="admin.agent.context.loaded.v1",
                payload={"history_turn_count": len(history)},
            )
            return ok_output(
                StageflowStageResult(
                    payload=payload,
                    summary={"history_turn_count": len(history)},
                )
            )

        async def query_planning(ctx: StageContext) -> Any:
            context_payload = cast(_ContextPayload, payload_from_inputs(ctx, "context_enrich"))
            prompt_version = self._settings.get_llm_prompt_version_for_task(LLMTaskKind.ADMIN_AGENT)
            model_slug = self._settings.get_llm_model_for_task(LLMTaskKind.ADMIN_AGENT)
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are an admin SQL planner. Return JSON with keys "
                        "`intent_summary`, `sql`, and `params`. "
                        "Plan one SELECT query only. "
                        "Do not use comments, subqueries, unions, or non-admin views. "
                        "Do not use SELECT * except COUNT(*). "
                        "Prefer simple aggregates and explicit aliases."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Prompt version: {prompt_version}\n"
                        f"Conversation history: {context_payload.conversation_history}\n"
                        f"Schema:\n{context_payload.schema_context}\n\n"
                        f"Question: {execution.message}"
                    ),
                },
            ]
            try:
                typed = await self._typed_output.generate(
                    self._llm_provider,
                    messages=messages,
                    call_context=ProviderCallContext(
                        operation="admin_agent.query_planning",
                        request_id=execution.request_id,
                        trace_id=execution.trace_id,
                        workflow_id=execution.workflow_id,
                        user_id=execution.actor.user_id,
                    ),
                )
            except StructuredOutputRejectionError as exc:
                self._record_event(
                    execution,
                    event_type="admin.agent.plan.rejected.v1",
                    payload={"question": execution.message},
                    error_code=exc.app_error.code,
                )
                raise exc.app_error

            plan_payload = _PlanPayload(
                plan=cast(AdminAgentPlan, typed.parsed),
                prompt_version=prompt_version,
                provider=self._llm_provider.provider_name,
                model_slug=typed.model_slug or model_slug,
            )
            self._record_event(
                execution,
                event_type="admin.agent.plan.generated.v1",
                payload={
                    "question": execution.message,
                    "intent_summary": plan_payload.plan.intent_summary,
                    "sql": plan_payload.plan.sql,
                    "prompt_version": plan_payload.prompt_version,
                    "provider": plan_payload.provider,
                    "model_slug": plan_payload.model_slug,
                    "config_version": self._settings.admin_agent_runtime_config_version,
                },
            )
            return ok_output(
                StageflowStageResult(
                    payload=plan_payload,
                    summary={
                        "prompt_version": prompt_version,
                        "provider": plan_payload.provider,
                        "model_slug": plan_payload.model_slug,
                    },
                )
            )

        async def query_execution(ctx: StageContext) -> Any:
            plan_payload = cast(_PlanPayload, payload_from_inputs(ctx, "query_planning"))
            try:
                guarded = self._sql_guard.validate_and_scope(
                    QueryAdminDataCommand(
                        sql=plan_payload.plan.sql,
                        params=plan_payload.plan.params,
                    )
                )
                result = await self._sql_executor.execute(
                    actor=execution.actor,
                    query=guarded,
                )
            except AppError as exc:
                self._record_event(
                    execution,
                    event_type="admin.agent.query.denied.v1",
                    payload={
                        "question": execution.message,
                        "sql": plan_payload.plan.sql,
                        "tool_name": ADMIN_AGENT_QUERY_TOOL,
                        "approval_state": "auto_allowed",
                    },
                    error_code=exc.code,
                )
                raise

            self._record_event(
                execution,
                event_type="admin.agent.query.executed.v1",
                payload={
                    "question": execution.message,
                    "intent_summary": plan_payload.plan.intent_summary,
                    "sql": result.sql,
                    "row_count": result.row_count,
                    "duration_ms": result.duration_ms,
                    "source_views": result.source_views,
                    "tool_name": ADMIN_AGENT_QUERY_TOOL,
                    "approval_state": result.approval_state,
                    "prompt_version": plan_payload.prompt_version,
                    "provider": plan_payload.provider,
                    "model_slug": plan_payload.model_slug,
                    "config_version": self._settings.admin_agent_runtime_config_version,
                },
            )
            return ok_output(
                StageflowStageResult(
                    payload=result,
                    summary={
                        "row_count": result.row_count,
                        "duration_ms": result.duration_ms,
                    },
                )
            )

        async def response_formulation(ctx: StageContext) -> Any:
            plan_payload = cast(_PlanPayload, payload_from_inputs(ctx, "query_planning"))
            query_result = cast(
                QueryAdminDataResultView, payload_from_inputs(ctx, "query_execution")
            )
            message = _format_response_message(
                question=execution.message,
                intent_summary=plan_payload.plan.intent_summary,
                result=query_result,
            )
            response = AdminAgentChatView(
                message=message,
                conversation_id=execution.conversation_id,
                tool_results=[query_result],
                metadata=AdminAgentResponseMetadataView(
                    conversation_id=execution.conversation_id,
                    request_id=execution.request_id,
                    trace_id=execution.trace_id,
                    workflow_id=execution.workflow_id,
                    provider=plan_payload.provider,
                    model_slug=plan_payload.model_slug,
                    prompt_version=plan_payload.prompt_version,
                    config_version=self._settings.admin_agent_runtime_config_version,
                    generated_at=datetime.now(UTC),
                ),
            )
            self._record_event(
                execution,
                event_type="admin.agent.response.completed.v1",
                payload={
                    "question": execution.message,
                    "intent_summary": plan_payload.plan.intent_summary,
                    "sql": query_result.sql,
                    "row_count": query_result.row_count,
                    "response_preview": response.message[:240],
                    "prompt_version": plan_payload.prompt_version,
                    "provider": plan_payload.provider,
                    "model_slug": plan_payload.model_slug,
                    "config_version": self._settings.admin_agent_runtime_config_version,
                },
            )
            return ok_output(
                StageflowStageResult(
                    payload=response,
                    summary={"row_count": query_result.row_count},
                )
            )

        return Pipeline.from_stages(
            stage("input_guard", input_guard, StageKind.GUARD),
            stage(
                "context_enrich",
                context_enrich,
                StageKind.ENRICH,
                dependencies=("input_guard",),
            ),
            stage(
                "query_planning",
                query_planning,
                StageKind.AGENT,
                dependencies=("context_enrich",),
            ),
            stage(
                "query_execution",
                query_execution,
                StageKind.WORK,
                dependencies=("query_planning",),
            ),
            stage(
                "response_formulation",
                response_formulation,
                StageKind.TRANSFORM,
                dependencies=("query_planning", "query_execution"),
            ),
            name="admin_agent_chat_runtime",
        )

    def _record_event(
        self,
        execution: AdminAgentExecutionInput,
        *,
        event_type: str,
        payload: dict[str, Any],
        error_code: str | None = None,
    ) -> None:
        self._repository.record_event(
            event_type=event_type,
            request_id=execution.request_id,
            trace_id=execution.trace_id,
            workflow_id=execution.workflow_id,
            organisation_id=cast(str, execution.actor.organisation_id),
            payload=payload,
            error_code=error_code,
        )


def _format_response_message(
    *,
    question: str,
    intent_summary: str,
    result: QueryAdminDataResultView,
) -> str:
    if result.row_count == 0:
        return (
            f"{intent_summary}. No matching records were found for: {question!r}. "
            "The query ran successfully against the admin-safe views."
        )
    preview = [_row_preview(row) for row in result.rows[:5]]
    joined_preview = "\n".join(f"- {item}" for item in preview)
    suffix = ""
    if result.row_count > len(preview):
        suffix = f"\n- ... {result.row_count - len(preview)} more row(s) omitted"
    return (
        f"{intent_summary}. Returned {result.row_count} row(s) from the admin-safe SQL tool.\n"
        f"{joined_preview}{suffix}"
    )


def _row_preview(row: dict[str, Any]) -> str:
    return ", ".join(f"{key}={value}" for key, value in row.items())
