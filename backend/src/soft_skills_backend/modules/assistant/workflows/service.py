"""Stageflow-backed assistant turn orchestration."""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from time import perf_counter
from typing import Any, cast
from uuid import uuid4

from stageflow.agent.security import PromptSecurityError, PromptSecurityPolicy
from stageflow.api import Pipeline, StageKind, stage
from stageflow.core import StageContext, StageOutput

from soft_skills_backend.config import Settings
from soft_skills_backend.engines.marking.contracts.models import RenderedPrompt
from soft_skills_backend.modules.admin.domain.prompt_registry import PromptRegistry
from soft_skills_backend.modules.admin.workflows.prompt_render_stage import (
    PromptRenderRequest,
    create_prompt_render_stage,
)
from soft_skills_backend.modules.assistant.contracts.stream import AssistantStreamEvent
from soft_skills_backend.modules.assistant.contracts.views import AssistantTurnView
from soft_skills_backend.modules.assistant.contracts.sql import QueryUserContextCommand
from soft_skills_backend.modules.assistant.domain.schema_registry import AssistantSchemaRegistry
from soft_skills_backend.modules.assistant.domain.models import AssistantTurnStatus
from soft_skills_backend.modules.assistant.infra.realtime import (
    ActiveTurnExecution,
    AssistantRealtimeBroker,
)
from soft_skills_backend.modules.assistant.infra.repository import AssistantRepository
from soft_skills_backend.modules.assistant.infra.sql_executor import AssistantSqlExecutor
from soft_skills_backend.modules.assistant.infra.sql_guard import AssistantSqlGuard
from soft_skills_backend.modules.assistant.workflows.practice_facilitation import (
    AssistantPracticeState,
)
from soft_skills_backend.modules.assistant.workflows.approval_service import (
    AssistantApprovalService,
)
from soft_skills_backend.modules.assistant.workflows.prompting import (
    ASSISTANT_FINAL_RESPONSE_PROMPT_NAME,
    ASSISTANT_FINAL_RESPONSE_PROMPT_VERSION,
    ASSISTANT_PROMPT_NAME,
    ASSISTANT_PROMPT_VERSION,
    build_assistant_tool_definitions,
)
from soft_skills_backend.modules.assistant.workflows.runtime_models import (
    parse_assistant_tool_requests,
)
from soft_skills_backend.modules.assistant.workflows.tools import (
    ASSISTANT_RUNTIME_STAGE,
    AssistantToolExecutor,
    ToolExecutionContext,
)
from soft_skills_backend.modules.catalog import CatalogService
from soft_skills_backend.modules.practice import PracticeService
from soft_skills_backend.modules.progression import ProgressionService
from soft_skills_backend.modules.taxonomy import TaxonomyService
from soft_skills_backend.platform.workflows.stageflow import (
    StageflowPipelineSupport,
    StageflowStageResult,
    ok_output,
    payload_from_inputs,
    run_logged_pipeline,
)
from soft_skills_backend.platform.workflows.stageflow_runtime import StageflowRuntime
from soft_skills_backend.shared.auth import Actor
from soft_skills_backend.shared.errors import orchestration_error, validation_error
from soft_skills_backend.shared.ports.llm import LLMProvider
from soft_skills_backend.shared.ports.telemetry import ProviderCallContext

MAX_TOOL_ITERATIONS = 6


@dataclass(slots=True)
class AssistantTurnExecutionInput:
    actor: Actor
    request_id: str
    trace_id: str
    workflow_id: str
    session_id: str
    turn_id: str
    stream_token: str


class AssistantWorkflowService:
    """Run assistant turns with parallel enrichment, tools, streaming, and cancellation."""

    def __init__(
        self,
        *,
        llm_provider: LLMProvider,
        repository: AssistantRepository,
        approvals: AssistantApprovalService,
        broker: AssistantRealtimeBroker,
        schema_registry: AssistantSchemaRegistry,
        sql_guard: AssistantSqlGuard,
        sql_executor: AssistantSqlExecutor,
        catalog_service: CatalogService,
        practice_service: PracticeService,
        progression_service: ProgressionService,
        taxonomy_service: TaxonomyService,
        stageflow_runtime: StageflowRuntime,
        prompt_registry: PromptRegistry,
        settings: Settings,
    ) -> None:
        self._settings = settings
        self._llm_provider = llm_provider
        self._repository = repository
        self._broker = broker
        self._schema_registry = schema_registry
        self._sql_guard = sql_guard
        self._sql_executor = sql_executor
        self._progression = progression_service
        self._taxonomy = taxonomy_service
        self._prompt_registry = prompt_registry
        self._stageflow = StageflowPipelineSupport.from_runtime(stageflow_runtime)
        self._prompt_security = PromptSecurityPolicy(
            max_user_chars=12000,
            max_tool_chars=12000,
        )
        self._tools = AssistantToolExecutor(
            repository=repository,
            approvals=approvals,
            broker=broker,
            sql_guard=sql_guard,
            sql_executor=sql_executor,
            catalog_service=catalog_service,
            practice_service=practice_service,
            stageflow_support=self._stageflow,
            settings=settings,
        )

    async def run_turn(self, execution: AssistantTurnExecutionInput) -> None:
        active = ActiveTurnExecution(turn_id=execution.turn_id, stream_token=execution.stream_token)
        self._broker.register_execution(active)

        def on_context_ready(pipeline_ctx: Any) -> None:
            active.pipeline_context = pipeline_ctx
            started_view = self._repository.mark_turn_running(
                turn_id=execution.turn_id,
                pipeline_run_id=str(pipeline_ctx.pipeline_run_id),
            )
            asyncio.get_running_loop().create_task(
                self._publish_event(
                    turn_id=execution.turn_id,
                    stream_token=execution.stream_token,
                    event_type="turn.started",
                    payload={
                        "session_id": execution.session_id,
                        "pipeline_run_id": started_view.pipeline_run_id,
                        "workflow_id": execution.workflow_id,
                    },
                    emitted_at=started_view.started_at or started_view.created_at,
                )
            )

        active.task = asyncio.current_task()
        try:
            pipeline = self._build_pipeline(execution, active)
            await run_logged_pipeline(
                self._stageflow,
                pipeline,
                request_id=execution.request_id,
                trace_id=execution.trace_id,
                workflow_id=execution.workflow_id,
                user_id=execution.actor.user_id,
                session_id=execution.session_id,
                execution_mode="assistant_runtime",
                service="soft_skills_backend.assistant",
                idempotency_key=f"assistant_turn:{execution.turn_id}",
                idempotency_params={"turn_id": execution.turn_id},
                timeout_ms=max(120_000, int(self._settings.smoke_timeout_seconds * 1000 * 2)),
                on_context_ready=on_context_ready,
            )
        except asyncio.CancelledError:
            cancelled = self._repository.mark_turn_cancelled(
                turn_id=execution.turn_id,
                reason=active.cancel_reason or "task_cancelled",
            )
            await self._emit_turn_cancelled(cancelled)
            raise
        except AppError as exc:
            failed = self._repository.mark_turn_failed(
                turn_id=execution.turn_id,
                error_code=exc.code,
                reason=exc.message,
            )
            await self._broker.publish(
                execution.stream_token,
                self._repository.create_stream_event(
                    turn_id=execution.turn_id,
                    event_type="turn.failed",
                    payload={"error_code": exc.code, "message": exc.message},
                    emitted_at=failed.completed_at or _utcnow(),
                ),
            )
        except Exception as exc:
            failed = self._repository.mark_turn_failed(
                turn_id=execution.turn_id,
                error_code="SS-ORCHESTRATION-206",
                reason="Assistant turn failed unexpectedly",
            )
            await self._broker.publish(
                execution.stream_token,
                self._repository.create_stream_event(
                    turn_id=execution.turn_id,
                    event_type="turn.failed",
                    payload={
                        "error_code": "SS-ORCHESTRATION-206",
                        "message": "Assistant turn failed unexpectedly",
                        "reason": str(exc),
                    },
                    emitted_at=failed.completed_at or _utcnow(),
                ),
            )
            raise
        finally:
            self._broker.remove_execution(execution.turn_id)

    async def request_cancel(self, *, turn: AssistantTurnView, reason: str) -> AssistantTurnView:
        cancelling = self._repository.request_cancel(actor=None, turn_id=turn.id, reason=reason)
        await self._broker.publish(
            turn.stream_token,
            self._repository.create_stream_event(
                turn_id=turn.id,
                event_type="turn.cancelling",
                payload={"reason": reason},
                emitted_at=_utcnow(),
            ),
        )
        active = self._broker.get_execution(turn.id)
        if active is not None:
            active.request_cancel(reason)
            if active.task is not None:
                asyncio.get_running_loop().create_task(self._escalate_cancel(active))
        else:
            cancelled = self._repository.mark_turn_cancelled(turn_id=turn.id, reason=reason)
            await self._emit_turn_cancelled(cancelled)
            return cancelled
        return cancelling

    async def _escalate_cancel(self, execution: ActiveTurnExecution) -> None:
        await asyncio.sleep(1.0)
        if execution.task is not None and not execution.task.done():
            execution.task.cancel()

    def _build_pipeline(
        self,
        execution: AssistantTurnExecutionInput,
        active: ActiveTurnExecution,
    ) -> Pipeline:
        async def input_guard(_ctx: StageContext) -> Any:
            turn = self._repository.get_turn(execution.actor, execution.turn_id)
            if turn.status == AssistantTurnStatus.CANCELLING:
                cancelled = self._repository.mark_turn_cancelled(
                    turn_id=execution.turn_id,
                    reason=turn.cancel_reason or "user_requested",
                )
                await self._emit_turn_cancelled(cancelled)
                return StageOutput.cancel(
                    reason=cancelled.cancel_reason or "user_requested",
                    data={
                        "payload": {"status": cancelled.status.value},
                        "summary": {"status": "cancelled"},
                    },
                )
            return ok_output(
                StageflowStageResult(
                    payload={"turn_id": execution.turn_id},
                    summary={"turn_id": execution.turn_id},
                )
            )

        async def history_enrich(_ctx: StageContext) -> Any:
            messages = self._repository.load_history(
                actor=execution.actor,
                session_id=execution.session_id,
                limit=self._settings.llm_assistant_conversation_history_limit,
            )
            return ok_output(
                StageflowStageResult(
                    payload=messages,
                    summary={"message_count": len(messages)},
                )
            )

        async def profile_enrich(_ctx: StageContext) -> Any:
            payload = self._repository.load_profile(execution.actor.user_id)
            return ok_output(
                StageflowStageResult(payload=payload, summary={"user_id": execution.actor.user_id})
            )

        async def progress_enrich(_ctx: StageContext) -> Any:
            try:
                dashboard = self._progression.get_dashboard(
                    execution.actor, execution.actor.user_id
                )
                payload: dict[str, Any] = {
                    "available": True,
                    "dashboard": dashboard.model_dump(mode="json"),
                }
            except AppError as exc:
                if exc.status_code == 404:
                    payload = {"available": False}
                else:
                    raise
            return ok_output(
                StageflowStageResult(payload=payload, summary={"available": payload["available"]})
            )

        async def attempts_enrich(_ctx: StageContext) -> Any:
            guarded = self._sql_guard.validate_and_scope(
                QueryUserContextCommand(
                    sql=(
                        "SELECT attempt_id, practice_type, status, overall_score, "
                        "strength_summary, next_action_summary, created_at, assessed_at "
                        "FROM assistant_safe_attempt_summaries_v "
                        f"ORDER BY created_at DESC LIMIT {self._settings.llm_assistant_recent_attempt_limit}"
                    )
                )
            )
            result = await self._sql_executor.execute(
                actor=execution.actor,
                query=guarded,
            )
            return ok_output(
                StageflowStageResult(
                    payload=result.rows,
                    summary={"attempt_count": len(result.rows)},
                )
            )

        async def session_state_enrich(_ctx: StageContext) -> Any:
            state = AssistantPracticeState.from_session_metadata(
                self._repository.load_session_metadata(
                    actor=execution.actor,
                    session_id=execution.session_id,
                )
            )
            return ok_output(
                StageflowStageResult(
                    payload=state,
                    summary={"practice_active": state.is_active()},
                )
            )

        async def planning_prompt_request(ctx: StageContext) -> Any:
            history = cast(list[Any], payload_from_inputs(ctx, "history_enrich"))
            latest_user_message = _latest_user_message(history)
            prompt_request = PromptRenderRequest(
                name=ASSISTANT_PROMPT_NAME,
                version=ASSISTANT_PROMPT_VERSION,
                variables={
                    "learner_context": json.dumps(
                        _build_compact_learner_context(
                            latest_user_message=latest_user_message,
                            profile=cast(
                                dict[str, Any], payload_from_inputs(ctx, "profile_enrich")
                            ),
                            progress=cast(
                                dict[str, Any], payload_from_inputs(ctx, "progress_enrich")
                            ),
                            attempts=cast(
                                list[dict[str, Any]], payload_from_inputs(ctx, "attempts_enrich")
                            ),
                        ),
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                    "read_schema_context": self._schema_registry.render_prompt_context(),
                    "taxonomy_context": self._taxonomy.render_prompt_context(
                        execution.actor.organisation_id
                    ),
                    "practice_state": cast(
                        AssistantPracticeState,
                        payload_from_inputs(ctx, "session_state_enrich"),
                    ).model_dump_json(),
                    "conversation_history": "Conversation history is attached as lower-priority messages.",
                },
            )
            return ok_output(
                StageflowStageResult(
                    payload=prompt_request,
                    summary={
                        "prompt_name": prompt_request.name,
                        "prompt_version": prompt_request.version,
                    },
                )
            )

        async def planning_prompt_render(ctx: StageContext) -> Any:
            renderer = create_prompt_render_stage(
                prompt_registry=self._prompt_registry,
                request_stage_name="planning_prompt_request",
            )
            return await renderer(ctx)

        async def assistant_runtime(ctx: StageContext) -> Any:
            result = await self._run_agent_loop(
                ctx=ctx,
                execution=execution,
                active=active,
                rendered_prompt=cast(
                    RenderedPrompt, payload_from_inputs(ctx, "planning_prompt_render")
                ),
                history=cast(list[Any], payload_from_inputs(ctx, "history_enrich")),
                practice_state=cast(
                    AssistantPracticeState,
                    payload_from_inputs(ctx, "session_state_enrich"),
                ),
            )
            if result.cancelled:
                reason = result.reason or "cancelled"
                cancelled = self._repository.mark_turn_cancelled(
                    turn_id=execution.turn_id,
                    reason=reason,
                )
                await self._emit_turn_cancelled(cancelled)
                return StageOutput.cancel(
                    reason=reason,
                    data={"payload": {"status": "cancelled"}, "summary": {"status": "cancelled"}},
                )
            return ok_output(
                StageflowStageResult(
                    payload=result,
                    summary={"status": "planned", "prompt_version": result.prompt_version},
                )
            )

        async def final_response_prompt_request(ctx: StageContext) -> Any:
            result = cast(_AssistantLoopResult, payload_from_inputs(ctx, ASSISTANT_RUNTIME_STAGE))
            prompt_request = PromptRenderRequest(
                name=ASSISTANT_FINAL_RESPONSE_PROMPT_NAME,
                version=ASSISTANT_FINAL_RESPONSE_PROMPT_VERSION,
                variables={"draft_response": result.final_response},
            )
            return ok_output(
                StageflowStageResult(
                    payload=prompt_request,
                    summary={
                        "prompt_name": prompt_request.name,
                        "prompt_version": prompt_request.version,
                    },
                )
            )

        async def final_response_prompt_render(ctx: StageContext) -> Any:
            renderer = create_prompt_render_stage(
                prompt_registry=self._prompt_registry,
                request_stage_name="final_response_prompt_request",
            )
            return await renderer(ctx)

        async def final_response_work(ctx: StageContext) -> Any:
            result = cast(_AssistantLoopResult, payload_from_inputs(ctx, ASSISTANT_RUNTIME_STAGE))
            (
                final_response,
                streamed_model_slug,
                response_metrics,
            ) = await self._generate_final_response(
                execution=execution,
                ctx=ctx,
                active=active,
                rendered_prompt=cast(
                    RenderedPrompt, payload_from_inputs(ctx, "final_response_prompt_render")
                ),
                planning_messages=result.planning_messages or [],
                draft_response=result.final_response,
            )
            if active.cancel_reason is not None:
                cancelled = self._repository.mark_turn_cancelled(
                    turn_id=execution.turn_id,
                    reason=active.cancel_reason,
                )
                await self._emit_turn_cancelled(cancelled)
                return StageOutput.cancel(
                    reason=active.cancel_reason,
                    data={"payload": {"status": "cancelled"}, "summary": {"status": "cancelled"}},
                )
            completed = self._repository.mark_turn_completed(
                turn_id=execution.turn_id,
                assistant_message=final_response,
                metadata={
                    "prompt_version": result.prompt_version,
                    "provider": self._llm_provider.provider_name,
                    "model_slug": streamed_model_slug or result.model_slug,
                },
            )
            await self._publish_final_response_completed(
                turn=completed,
                response_text=final_response,
                metrics=response_metrics,
            )
            await self._broker.publish(
                execution.stream_token,
                self._repository.create_stream_event(
                    turn_id=execution.turn_id,
                    event_type="turn.completed",
                    payload={
                        "assistant_message_id": completed.assistant_message_id,
                        "status": completed.status.value,
                    },
                    emitted_at=completed.completed_at or _utcnow(),
                ),
            )
            return ok_output(
                StageflowStageResult(
                    payload={"assistant_message_id": completed.assistant_message_id},
                    summary={"status": "completed"},
                )
            )

        return Pipeline.from_stages(
            stage("input_guard", input_guard, StageKind.GUARD),
            stage(
                "history_enrich",
                history_enrich,
                StageKind.ENRICH,
                dependencies=("input_guard",),
            ),
            stage(
                "profile_enrich",
                profile_enrich,
                StageKind.ENRICH,
                dependencies=("input_guard",),
            ),
            stage(
                "progress_enrich",
                progress_enrich,
                StageKind.ENRICH,
                dependencies=("input_guard",),
            ),
            stage(
                "attempts_enrich",
                attempts_enrich,
                StageKind.ENRICH,
                dependencies=("input_guard",),
            ),
            stage(
                "session_state_enrich",
                session_state_enrich,
                StageKind.ENRICH,
                dependencies=("input_guard",),
            ),
            stage(
                "planning_prompt_request",
                planning_prompt_request,
                StageKind.TRANSFORM,
                dependencies=(
                    "history_enrich",
                    "profile_enrich",
                    "progress_enrich",
                    "attempts_enrich",
                    "session_state_enrich",
                ),
            ),
            stage(
                "planning_prompt_render",
                planning_prompt_render,
                StageKind.TRANSFORM,
                dependencies=("planning_prompt_request",),
            ),
            stage(
                ASSISTANT_RUNTIME_STAGE,
                assistant_runtime,
                StageKind.AGENT,
                dependencies=(
                    "history_enrich",
                    "planning_prompt_render",
                    "session_state_enrich",
                ),
            ),
            stage(
                "final_response_prompt_request",
                final_response_prompt_request,
                StageKind.TRANSFORM,
                dependencies=(ASSISTANT_RUNTIME_STAGE,),
            ),
            stage(
                "final_response_prompt_render",
                final_response_prompt_render,
                StageKind.TRANSFORM,
                dependencies=("final_response_prompt_request",),
            ),
            stage(
                "final_response_work",
                final_response_work,
                StageKind.WORK,
                dependencies=(ASSISTANT_RUNTIME_STAGE, "final_response_prompt_render"),
            ),
            name="assistant_turn_runtime",
        )

    async def _run_agent_loop(
        self,
        *,
        ctx: StageContext,
        execution: AssistantTurnExecutionInput,
        active: ActiveTurnExecution,
        rendered_prompt: RenderedPrompt,
        history: list[Any],
        practice_state: AssistantPracticeState,
    ) -> _AssistantLoopResult:
        messages: list[dict[str, Any]] = [{"role": "system", "content": rendered_prompt.content}]
        tool_definitions = build_assistant_tool_definitions()
        has_executed_tool = False
        for message in history:
            if message.role.value == "assistant":
                messages.append({"role": "assistant", "content": message.content})
            else:
                try:
                    hardened, _ = self._prompt_security.build_user_message(message.content)
                except PromptSecurityError as exc:
                    raise validation_error(
                        "Assistant blocked unsafe user content",
                        code="SS-VALIDATION-204",
                        details={"guardrail": exc.report.guardrail},
                    ) from exc
                messages.append(hardened)

        for _ in range(MAX_TOOL_ITERATIONS):
            if active.cancel_reason is not None:
                return _AssistantLoopResult(cancelled=True, reason=active.cancel_reason)
            ctx.try_emit_event(
                "assistant.provider_tool_request",
                {
                    "tool_count": len(tool_definitions),
                    "tool_names": [tool.name for tool in tool_definitions],
                    "tool_schema_bytes": {
                        tool.name: len(
                            json.dumps(tool.parameters, separators=(",", ":"), sort_keys=True)
                        )
                        for tool in tool_definitions
                    },
                    "message_count": len(messages),
                    "pipeline_run_id": str(ctx.pipeline_run_id) if ctx.pipeline_run_id else None,
                    "request_id": execution.request_id,
                    "trace_id": execution.trace_id,
                    "workflow_id": execution.workflow_id,
                },
            )
            completion = await self._llm_provider.complete_with_tools(
                messages=messages,
                tools=tool_definitions,
                call_context=ProviderCallContext(
                    operation="assistant_orchestrator_decision",
                    request_id=execution.request_id,
                    trace_id=execution.trace_id,
                    pipeline_run_id=str(ctx.pipeline_run_id) if ctx.pipeline_run_id else None,
                    workflow_id=execution.workflow_id,
                    user_id=execution.actor.user_id,
                ),
                timeout_seconds=self._settings.llm_assistant_timeout_seconds,
            )
            if not completion.tool_calls:
                final_response = (completion.content or "").strip()
                if not final_response:
                    raise orchestration_error(
                        "Assistant returned neither tool calls nor a final response",
                        code="SS-ORCHESTRATION-205",
                    )
                return _AssistantLoopResult(
                    cancelled=False,
                    reason=None,
                    final_response=final_response,
                    prompt_version=rendered_prompt.version,
                    model_slug=completion.model_slug,
                    planning_messages=list(messages),
                    used_tools=has_executed_tool,
                )
            tool_requests = parse_assistant_tool_requests(completion.tool_calls)
            messages.append(
                _provider_tool_call_message(
                    content=completion.content,
                    tool_requests=tool_requests,
                )
            )
            for tool_request in tool_requests:
                ctx.try_emit_event(
                    "tool.invoked",
                    {
                        "tool_name": tool_request.tool_name,
                        "call_id": tool_request.call_id,
                        "arguments": tool_request.arguments_payload(),
                        "pipeline_run_id": str(ctx.pipeline_run_id)
                        if ctx.pipeline_run_id
                        else None,
                        "request_id": execution.request_id,
                        "trace_id": execution.trace_id,
                        "workflow_id": execution.workflow_id,
                    },
                )
            tool_results = await self._tools.execute_many(
                stage_ctx=ctx,
                execution=ToolExecutionContext(
                    actor=execution.actor,
                    request_id=execution.request_id,
                    trace_id=execution.trace_id,
                    workflow_id=execution.workflow_id,
                    session_id=execution.session_id,
                    turn_id=execution.turn_id,
                    stream_token=execution.stream_token,
                ),
                tool_requests=tool_requests,
            )
            has_executed_tool = has_executed_tool or bool(tool_results)
            if active.cancel_reason is not None:
                return _AssistantLoopResult(cancelled=True, reason=active.cancel_reason)
            for tool_result in tool_results:
                try:
                    hardened_tool, _ = self._prompt_security.build_tool_message(
                        tool_name=tool_result.tool_name,
                        call_id=tool_result.call_id,
                        payload=tool_result.payload,
                    )
                except PromptSecurityError as exc:
                    raise validation_error(
                        "Assistant blocked unsafe tool output",
                        code="SS-VALIDATION-205",
                        details={
                            "guardrail": exc.report.guardrail,
                            "tool_name": tool_result.tool_name,
                        },
                    ) from exc
                messages.append(hardened_tool)
        raise orchestration_error(
            "Assistant exceeded the tool iteration budget",
            code="SS-ORCHESTRATION-203",
            details={"max_iterations": MAX_TOOL_ITERATIONS},
        )

    async def _generate_final_response(
        self,
        *,
        execution: AssistantTurnExecutionInput,
        ctx: StageContext,
        active: ActiveTurnExecution,
        rendered_prompt: RenderedPrompt,
        draft_response: str,
        planning_messages: list[dict[str, Any]],
    ) -> tuple[str, str | None, dict[str, Any]]:
        stream_messages = [
            *planning_messages,
            {
                "role": "user",
                "content": rendered_prompt.content,
            },
        ]
        chunks: list[str] = []
        model_slug: str | None = None
        index = 0
        chunk_count = 0
        prompt_tokens: int | None = None
        completion_tokens: int | None = None
        total_tokens: int | None = None
        start_time = perf_counter()
        if not _should_rewrite_final_response(
            draft_response=draft_response, planning_messages=planning_messages
        ):
            metrics = {
                "latency_ms": 0,
                "chunk_count": 0,
                "output_chars": len(draft_response),
                "mode": "draft_passthrough",
                "token_count_prompt": None,
                "token_count_completion": None,
                "token_count_total": None,
            }
            return draft_response, None, metrics
        try:
            async for chunk in self._llm_provider.stream_text(
                messages=stream_messages,
                call_context=ProviderCallContext(
                    operation="assistant_final_response",
                    request_id=execution.request_id,
                    trace_id=execution.trace_id,
                    pipeline_run_id=str(ctx.pipeline_run_id) if ctx.pipeline_run_id else None,
                    workflow_id=execution.workflow_id,
                    user_id=execution.actor.user_id,
                ),
            ):
                if active.cancel_reason is not None:
                    final_response = "".join(chunks).strip() or draft_response
                    return (
                        final_response,
                        model_slug,
                        self._build_response_metrics(
                            chunks=chunks,
                            model_slug=model_slug,
                            prompt_tokens=prompt_tokens,
                            completion_tokens=completion_tokens,
                            total_tokens=total_tokens,
                            start_time=start_time,
                            chunk_count=chunk_count,
                        ),
                    )
                if chunk.done:
                    model_slug = chunk.model_slug or model_slug
                    if chunk.usage:
                        prompt_tokens = chunk.usage.get("prompt_tokens", prompt_tokens)
                        completion_tokens = chunk.usage.get("completion_tokens", completion_tokens)
                        total_tokens = chunk.usage.get("total_tokens", total_tokens)
                    continue
                if not chunk.delta:
                    continue
                index += 1
                chunk_count += 1
                model_slug = chunk.model_slug or model_slug
                chunks.append(chunk.delta)
                if chunk.usage:
                    prompt_tokens = chunk.usage.get("prompt_tokens", prompt_tokens)
                    completion_tokens = chunk.usage.get("completion_tokens", completion_tokens)
                    total_tokens = chunk.usage.get("total_tokens", total_tokens)
                await self._broker.publish(
                    execution.stream_token,
                    AssistantStreamEvent(
                        event_id=uuid4().hex,
                        session_id=execution.session_id,
                        type="response.delta",
                        turn_id=execution.turn_id,
                        trace_id=execution.trace_id,
                        workflow_id=execution.workflow_id,
                        sequence_number=index,
                        emitted_at=_utcnow(),
                        payload={"index": index, "delta": chunk.delta},
                    ),
                )
        except (AttributeError, NotImplementedError):
            for index, chunk_text in enumerate(_chunk_text(draft_response), start=1):
                chunks.append(chunk_text)
                chunk_count += 1
                await self._broker.publish(
                    execution.stream_token,
                    AssistantStreamEvent(
                        event_id=uuid4().hex,
                        session_id=execution.session_id,
                        type="response.delta",
                        turn_id=execution.turn_id,
                        trace_id=execution.trace_id,
                        workflow_id=execution.workflow_id,
                        sequence_number=index,
                        emitted_at=_utcnow(),
                        payload={"index": index, "delta": chunk_text},
                    ),
                )
        final_response = "".join(chunks).strip()
        if not final_response:
            final_response = draft_response
        return (
            final_response,
            model_slug,
            self._build_response_metrics(
                chunks=chunks,
                model_slug=model_slug,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                start_time=start_time,
                chunk_count=chunk_count,
            ),
        )

    def _build_response_metrics(
        self,
        *,
        chunks: list[str],
        model_slug: str | None,
        prompt_tokens: int | None,
        completion_tokens: int | None,
        total_tokens: int | None,
        start_time: float,
        chunk_count: int,
    ) -> dict[str, Any]:
        content = "".join(chunks)
        max_content_length = 65536
        truncated_content = (
            content[:max_content_length] if len(content) > max_content_length else content
        )
        latency_ms = int((perf_counter() - start_time) * 1000)
        return {
            "content": truncated_content,
            "model_slug": model_slug,
            "token_count_prompt": prompt_tokens,
            "token_count_completion": completion_tokens,
            "token_count_total": total_tokens,
            "latency_ms": latency_ms,
            "chunk_count": chunk_count,
        }

    async def _publish_final_response_completed(
        self,
        *,
        turn: AssistantTurnView,
        response_text: str,
        metrics: dict[str, Any],
    ) -> None:
        event = self._repository.create_stream_event(
            turn_id=turn.id,
            event_type="response.completed",
            payload={
                "assistant_message_id": turn.assistant_message_id,
                "content": response_text,
                **metrics,
            },
            emitted_at=_utcnow(),
        )
        await self._broker.publish(turn.stream_token, event)

    async def _stream_final_response(self, *, turn: AssistantTurnView, response_text: str) -> None:
        for index, chunk in enumerate(_chunk_text(response_text), start=1):
            await self._broker.publish(
                turn.stream_token,
                AssistantStreamEvent(
                    event_id=uuid4().hex,
                    session_id=turn.session_id,
                    type="response.delta",
                    turn_id=turn.id,
                    trace_id=turn.trace_id,
                    workflow_id=turn.workflow_id,
                    sequence_number=index,
                    emitted_at=_utcnow(),
                    payload={"index": index, "delta": chunk},
                ),
            )
            await asyncio.sleep(0)
        await self._broker.publish(
            turn.stream_token,
            AssistantStreamEvent(
                event_id=uuid4().hex,
                session_id=turn.session_id,
                type="response.completed",
                turn_id=turn.id,
                trace_id=turn.trace_id,
                workflow_id=turn.workflow_id,
                sequence_number=len(_chunk_text(response_text)) + 1,
                emitted_at=_utcnow(),
                payload={
                    "assistant_message_id": turn.assistant_message_id,
                    "content": response_text,
                },
            ),
        )

    async def _emit_turn_cancelled(self, turn: AssistantTurnView) -> None:
        await self._broker.publish(
            turn.stream_token,
            self._repository.create_stream_event(
                turn_id=turn.id,
                event_type="turn.cancelled",
                payload={"reason": turn.cancel_reason},
                emitted_at=turn.cancelled_at or _utcnow(),
            ),
        )

    async def _publish_event(
        self,
        *,
        turn_id: str,
        stream_token: str,
        event_type: str,
        payload: dict[str, Any],
        emitted_at: datetime,
    ) -> None:
        event = self._repository.create_stream_event(
            turn_id=turn_id,
            event_type=event_type,
            payload=payload,
            emitted_at=emitted_at,
        )
        await self._broker.publish(stream_token, event)


@dataclass(slots=True)
class _AssistantLoopResult:
    cancelled: bool
    reason: str | None
    final_response: str = ""
    prompt_version: str | None = None
    model_slug: str | None = None
    planning_messages: list[dict[str, Any]] | None = None
    used_tools: bool = False


def _provider_tool_call_message(
    *,
    content: str | None,
    tool_requests: list[Any],
) -> dict[str, Any]:
    return {
        "role": "assistant",
        "content": content or "",
        "tool_calls": [
            {
                "id": tool_request.call_id,
                "type": "function",
                "function": {
                    "name": tool_request.tool_name,
                    "arguments": json.dumps(
                        tool_request.arguments_payload(),
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                },
            }
            for tool_request in tool_requests
        ],
    }


def _chunk_text(text: str, *, chunk_size: int = 80) -> list[str]:
    if not text:
        return [""]
    words = text.split()
    chunks: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if len(candidate) <= chunk_size:
            current = candidate
            continue
        chunks.append(current)
        current = word
    if current:
        chunks.append(current)
    return chunks


def _build_compact_learner_context(
    *,
    latest_user_message: str,
    profile: dict[str, Any],
    progress: dict[str, Any],
    attempts: list[dict[str, Any]],
) -> dict[str, Any]:
    compact_profile = {
        key: profile.get(key)
        for key in ("display_name", "email", "organisation_id")
        if profile.get(key) is not None
    }
    context: dict[str, Any] = {"profile": compact_profile}
    context["progress"] = _compact_progress_context(progress)
    context["recent_attempts"] = [
        {
            key: attempt.get(key)
            for key in (
                "practice_type",
                "status",
                "overall_score",
                "strength_summary",
                "next_action_summary",
            )
            if attempt.get(key) is not None
        }
        for attempt in attempts
    ]
    return context


def _compact_progress_context(progress: dict[str, Any]) -> dict[str, Any]:
    if not progress.get("available"):
        return {"available": False}
    dashboard = progress.get("dashboard")
    if not isinstance(dashboard, dict):
        return {"available": True}
    compact: dict[str, Any] = {"available": True}
    recommendation = dashboard.get("recommendation")
    if isinstance(recommendation, dict):
        compact["recommendation"] = {
            key: recommendation.get(key)
            for key in ("type", "title", "summary")
            if recommendation.get(key) is not None
        }
    competencies = dashboard.get("competencies")
    if isinstance(competencies, list):
        compact["competencies"] = [
            {
                key: item.get(key)
                for key in ("slug", "label", "score", "status")
                if isinstance(item, dict) and item.get(key) is not None
            }
            for item in competencies[:3]
            if isinstance(item, dict)
        ]
    return compact


def _required_tool_name(history: list[Any], practice_state: AssistantPracticeState) -> str | None:
    return None
def _should_rewrite_final_response(
    *, draft_response: str, planning_messages: list[dict[str, Any]]
) -> bool:
    if not draft_response.strip():
        return False
    return any(message.get("role") == "tool" for message in planning_messages)


def _latest_user_message(history: list[Any]) -> str:
    for entry in reversed(history):
        content = getattr(entry, "content", None)
        if isinstance(content, str) and content.strip():
            return content.strip()
    return ""


def _utcnow() -> datetime:
    return datetime.now(UTC)
