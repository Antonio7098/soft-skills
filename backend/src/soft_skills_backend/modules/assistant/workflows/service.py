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
from soft_skills_backend.engines.marking.use_cases.structured_output import (
    StructuredOutputRejectionError,
    TypedLLMOutput,
)
from soft_skills_backend.modules.admin.domain.prompt_registry import PromptRegistry
from soft_skills_backend.modules.admin.workflows.prompt_render_stage import (
    PromptRenderRequest,
    create_prompt_render_stage,
)
from soft_skills_backend.modules.assistant.contracts.stream import AssistantStreamEvent
from soft_skills_backend.modules.assistant.contracts.views import AssistantTurnView
from soft_skills_backend.modules.assistant.domain.models import AssistantTurnStatus
from soft_skills_backend.modules.assistant.infra.realtime import (
    ActiveTurnExecution,
    AssistantRealtimeBroker,
)
from soft_skills_backend.modules.assistant.infra.repository import AssistantRepository
from soft_skills_backend.modules.assistant.workflows.prompting import (
    ASSISTANT_FINAL_RESPONSE_PROMPT_NAME,
    ASSISTANT_FINAL_RESPONSE_PROMPT_VERSION,
    ASSISTANT_PROMPT_NAME,
    ASSISTANT_PROMPT_VERSION,
    render_tool_definitions,
)
from soft_skills_backend.modules.assistant.workflows.practice_facilitation import (
    AssistantPracticeState,
)
from soft_skills_backend.modules.assistant.workflows.runtime_models import AssistantDecision
from soft_skills_backend.modules.assistant.workflows.tools import (
    ASSISTANT_RUNTIME_STAGE,
    AssistantToolExecutor,
    ToolExecutionContext,
)
from soft_skills_backend.modules.catalog import CatalogService
from soft_skills_backend.modules.practice import PracticeService
from soft_skills_backend.modules.progression import ProgressionService
from soft_skills_backend.platform.workflows.stageflow import (
    StageflowPipelineSupport,
    StageflowStageResult,
    ok_output,
    payload_from_inputs,
    run_logged_pipeline,
)
from soft_skills_backend.platform.workflows.stageflow_runtime import StageflowRuntime
from soft_skills_backend.shared.auth import Actor
from soft_skills_backend.shared.errors import AppError, orchestration_error, validation_error
from soft_skills_backend.shared.ports.llm import LLMProvider
from soft_skills_backend.shared.ports.telemetry import ProviderCallContext

MAX_TOOL_ITERATIONS = 6
_GENERATION_REQUEST_PATTERN = re.compile(
    r"\b(generate|create|draft|make|add|build)\b",
    re.IGNORECASE,
)
_PRACTICE_STOP_PATTERN = re.compile(
    r"\b(stop|end|cancel|quit|leave|exit)\b",
    re.IGNORECASE,
)
_PRACTICE_RECALL_PATTERN = re.compile(
    r"\b(repeat|restate|remind)\b|"
    r"\bwhat (?:is|was)\b.*\b(question|prompt)\b|"
    r"\bshow\b.*\b(question|prompt)\b",
    re.IGNORECASE,
)


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
        broker: AssistantRealtimeBroker,
        catalog_service: CatalogService,
        practice_service: PracticeService,
        progression_service: ProgressionService,
        stageflow_runtime: StageflowRuntime,
        prompt_registry: PromptRegistry,
        settings: Settings,
    ) -> None:
        self._settings = settings
        self._llm_provider = llm_provider
        self._repository = repository
        self._broker = broker
        self._progression = progression_service
        self._prompt_registry = prompt_registry
        self._stageflow = StageflowPipelineSupport.from_runtime(stageflow_runtime)
        self._typed_output = TypedLLMOutput(
            AssistantDecision,
            schema_version="assistant_decision.v1",
            max_validation_retries=1,
        )
        self._prompt_security = PromptSecurityPolicy(
            max_user_chars=12000,
            max_tool_chars=12000,
        )
        self._tools = AssistantToolExecutor(
            repository=repository,
            broker=broker,
            catalog_service=catalog_service,
            practice_service=practice_service,
            stageflow_support=self._stageflow,
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
                limit=24,
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
            attempts = self._repository.load_recent_attempts(actor=execution.actor, limit=5)
            return ok_output(
                StageflowStageResult(
                    payload=attempts,
                    summary={"attempt_count": len(attempts)},
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
            prompt_request = PromptRenderRequest(
                name=ASSISTANT_PROMPT_NAME,
                version=ASSISTANT_PROMPT_VERSION,
                variables={
                    "learner_context": json.dumps(
                        {
                            "profile": cast(dict[str, Any], payload_from_inputs(ctx, "profile_enrich")),
                            "progress": cast(
                                dict[str, Any], payload_from_inputs(ctx, "progress_enrich")
                            ),
                            "recent_attempts": cast(
                                list[dict[str, Any]], payload_from_inputs(ctx, "attempts_enrich")
                            ),
                        },
                        sort_keys=True,
                    ),
                    "practice_state": cast(
                        AssistantPracticeState,
                        payload_from_inputs(ctx, "session_state_enrich"),
                    ).model_dump_json(),
                    "tool_definitions": render_tool_definitions(),
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
                rendered_prompt=cast(RenderedPrompt, payload_from_inputs(ctx, "planning_prompt_render")),
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
            stage("input_guard", input_guard, StageKind.GUARD),  # type: ignore[arg-type]
            stage(
                "history_enrich",
                history_enrich,  # type: ignore[arg-type]
                StageKind.ENRICH,
                dependencies=("input_guard",),
            ),
            stage(
                "profile_enrich",
                profile_enrich,  # type: ignore[arg-type]
                StageKind.ENRICH,
                dependencies=("input_guard",),
            ),
            stage(
                "progress_enrich",
                progress_enrich,  # type: ignore[arg-type]
                StageKind.ENRICH,
                dependencies=("input_guard",),
            ),
            stage(
                "attempts_enrich",
                attempts_enrich,  # type: ignore[arg-type]
                StageKind.ENRICH,
                dependencies=("input_guard",),
            ),
            stage(
                "session_state_enrich",
                session_state_enrich,  # type: ignore[arg-type]
                StageKind.ENRICH,
                dependencies=("input_guard",),
            ),
            stage(
                "planning_prompt_request",
                planning_prompt_request,  # type: ignore[arg-type]
                StageKind.TRANSFORM,
                dependencies=(
                    "profile_enrich",
                    "progress_enrich",
                    "attempts_enrich",
                    "session_state_enrich",
                ),
            ),
            stage(
                "planning_prompt_render",
                planning_prompt_render,  # type: ignore[arg-type]
                StageKind.TRANSFORM,
                dependencies=("planning_prompt_request",),
            ),
            stage(
                ASSISTANT_RUNTIME_STAGE,
                assistant_runtime,  # type: ignore[arg-type]
                StageKind.AGENT,
                dependencies=(
                    "history_enrich",
                    "planning_prompt_render",
                    "session_state_enrich",
                ),
            ),
            stage(
                "final_response_prompt_request",
                final_response_prompt_request,  # type: ignore[arg-type]
                StageKind.TRANSFORM,
                dependencies=(ASSISTANT_RUNTIME_STAGE,),
            ),
            stage(
                "final_response_prompt_render",
                final_response_prompt_render,  # type: ignore[arg-type]
                StageKind.TRANSFORM,
                dependencies=("final_response_prompt_request",),
            ),
            stage(
                "final_response_work",
                final_response_work,  # type: ignore[arg-type]
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
        messages = [{"role": "system", "content": rendered_prompt.content}]
        required_tool_name = _required_tool_name(history, practice_state)
        corrective_prompt_sent = False
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
            try:
                typed = await self._typed_output.generate(
                    self._llm_provider,
                    messages=messages,
                    call_context=ProviderCallContext(
                        operation="assistant_orchestrator_decision",
                        request_id=execution.request_id,
                        trace_id=execution.trace_id,
                        pipeline_run_id=str(ctx.pipeline_run_id) if ctx.pipeline_run_id else None,
                        workflow_id=execution.workflow_id,
                        user_id=execution.actor.user_id,
                    ),
                )
            except StructuredOutputRejectionError as exc:
                raise exc.app_error from exc
            decision = cast(AssistantDecision, typed.parsed)
            if decision.final_response is not None:
                if required_tool_name is not None and not has_executed_tool:
                    if corrective_prompt_sent:
                        raise validation_error(
                            "Assistant ignored a required generation tool request",
                            code="SS-VALIDATION-206",
                            details={"required_tool_name": required_tool_name},
                        )
                    messages.append(
                        {
                            "role": "system",
                            "content": (
                                "The latest user request requires a specific tool action. "
                                f"You must call the `{required_tool_name}` tool next and must not "
                                "return final_response until the tool result is available."
                            ),
                        }
                    )
                    corrective_prompt_sent = True
                    continue
                return _AssistantLoopResult(
                    cancelled=False,
                    reason=None,
                    final_response=decision.final_response.strip(),
                    prompt_version=rendered_prompt.version,
                    model_slug=typed.model_slug,
                    planning_messages=list(messages),
                )
            for tool_request in decision.tool_calls:
                ctx.try_emit_event(
                    "tool.invoked",
                    {
                        "tool_name": tool_request.tool_name,
                        "call_id": tool_request.call_id,
                        "arguments": tool_request.arguments,
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
                tool_requests=decision.tool_calls,
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
        planning_messages: list[dict[str, str]],
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
    planning_messages: list[dict[str, str]] | None = None


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

def _required_tool_name(history: list[Any], practice_state: AssistantPracticeState) -> str | None:
    latest_user_message = _latest_user_message(history)
    if practice_state.is_active() and _is_practice_recall_message(latest_user_message):
        return "get_active_practice"
    if practice_state.is_active() and not _is_practice_control_message(latest_user_message):
        return "submit_active_practice_response"
    return _required_generation_tool_name(latest_user_message)


def _required_generation_tool_name(latest_user_message: str) -> str | None:
    if not latest_user_message or _GENERATION_REQUEST_PATTERN.search(latest_user_message) is None:
        return None
    lowered = latest_user_message.lower()
    if "generate_prompt_items" in lowered:
        return "generate_prompt_items"
    if "generate_collection" in lowered:
        return "generate_collection"
    if "prompt item" in lowered or "prompt-item" in lowered:
        return "generate_prompt_items"
    return "generate_collection"


def _latest_user_message(history: list[Any]) -> str:
    return next(
        (
            str(message.content)
            for message in reversed(history)
            if getattr(getattr(message, "role", None), "value", None) == "user"
        ),
        "",
    )


def _is_practice_control_message(message: str) -> bool:
    return bool(message and _PRACTICE_STOP_PATTERN.search(message))


def _is_practice_recall_message(message: str) -> bool:
    return bool(message and _PRACTICE_RECALL_PATTERN.search(message))


def _utcnow() -> datetime:
    return datetime.now(UTC)
