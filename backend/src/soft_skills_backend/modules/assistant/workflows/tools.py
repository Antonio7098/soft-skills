"""Assistant tool execution runtime."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
import re
from typing import Any
from uuid import uuid4

from pydantic import ValidationError
from stageflow.api import Pipeline, StageKind, stage
from stageflow.core import StageContext

from soft_skills_backend.config import Settings
from soft_skills_backend.modules.assistant.contracts.sql import QueryUserContextCommand
from soft_skills_backend.modules.assistant.domain.models import AssistantApprovalStatus
from soft_skills_backend.modules.assistant.infra.realtime import AssistantRealtimeBroker
from soft_skills_backend.modules.assistant.infra.repository import AssistantRepository
from soft_skills_backend.modules.assistant.infra.sql_executor import AssistantSqlExecutor
from soft_skills_backend.modules.assistant.contracts.views import QueryUserContextResultView
from soft_skills_backend.modules.assistant.infra.sql_guard import AssistantSqlGuard
from soft_skills_backend.modules.assistant.workflows.approval_service import (
    AssistantApprovalService,
)
from soft_skills_backend.modules.assistant.workflows.practice_facilitation import (
    AssistantPracticeCoordinator,
    StartCollectionPracticeToolArgs,
)
from soft_skills_backend.modules.assistant.workflows.runtime_models import AssistantToolRequest
from soft_skills_backend.modules.catalog import CatalogService
from soft_skills_backend.modules.catalog.contracts.collection_commands import (
    ChatCollectionGenerationCommand,
)
from soft_skills_backend.modules.catalog.contracts.stream import GenerationStreamEvent
from soft_skills_backend.modules.catalog.domain.models import CollectionGenerationCounts
from soft_skills_backend.modules.catalog.workflows.generation.service import (
    CatalogGenerationService,
    GenerationStartedView,
)
from soft_skills_backend.modules.catalog.contracts.prompt_item_commands import (
    ChatPromptItemGenerationCommand,
)
from soft_skills_backend.modules.practice import PracticeService
from soft_skills_backend.modules.taxonomy.models import TaxonomySnapshot
from soft_skills_backend.platform.workflows.stageflow import (
    StageflowPipelineSupport,
    StageflowStageResult,
    ok_output,
    run_logged_subpipeline,
)
from soft_skills_backend.shared.auth import Actor
from soft_skills_backend.shared.errors import AppError, orchestration_error, validation_error

ASSISTANT_RUNTIME_STAGE = "assistant_runtime"
_WORD_PATTERN = re.compile(r"[a-z0-9]+")
_DEFAULT_SKILL_PRIORITY = (
    "active-listening",
    "structured-communication",
    "expectation-setting",
    "decision-justification",
)


@dataclass(slots=True)
class ToolPromptResult:
    tool_name: str
    call_id: str
    payload: dict[str, Any]


@dataclass(slots=True)
class ToolExecutionContext:
    actor: Actor
    request_id: str
    trace_id: str
    workflow_id: str
    session_id: str
    turn_id: str
    stream_token: str


class AssistantToolExecutor:
    """Execute assistant tool calls with persistence and streaming hooks."""

    def __init__(
        self,
        *,
        repository: AssistantRepository,
        approvals: AssistantApprovalService,
        broker: AssistantRealtimeBroker,
        sql_guard: AssistantSqlGuard,
        sql_executor: AssistantSqlExecutor,
        catalog_service: CatalogService,
        practice_service: PracticeService,
        stageflow_support: StageflowPipelineSupport,
        settings: Settings,
    ) -> None:
        self._repository = repository
        self._approvals = approvals
        self._broker = broker
        self._sql_guard = sql_guard
        self._sql_executor = sql_executor
        self._catalog = catalog_service
        self._practice = practice_service
        self._stageflow = stageflow_support
        self._approval_timeout_seconds = settings.tool_approval_timeout_seconds
        self._auto_allow_tools = frozenset(settings.tool_approval_auto_allow)
        self._generation_timeout_ms = int(max(60_000, settings.smoke_timeout_seconds * 4_000))
        self._practice_tools = AssistantPracticeCoordinator(
            repository=repository,
            catalog_service=catalog_service,
            practice_service=practice_service,
        )

    async def execute_many(
        self,
        *,
        stage_ctx: StageContext,
        execution: ToolExecutionContext,
        tool_requests: list[AssistantToolRequest],
    ) -> list[ToolPromptResult]:
        tasks = [
            self._execute_one(
                stage_ctx=stage_ctx,
                execution=execution,
                tool_request=tool_request,
            )
            for tool_request in tool_requests
        ]
        return await _gather_strict(tasks)

    async def _execute_one(
        self,
        *,
        stage_ctx: StageContext,
        execution: ToolExecutionContext,
        tool_request: AssistantToolRequest,
    ) -> ToolPromptResult:
        requires_approval = self._requires_approval(tool_request.tool_name)
        arguments_payload = tool_request.arguments_payload()
        tool_call = self._repository.create_tool_call(
            turn_id=execution.turn_id,
            tool_name=tool_request.tool_name,
            args_payload=arguments_payload,
            waiting_for_approval=requires_approval,
        )
        try:
            if requires_approval:
                await self._await_human_approval(
                    execution=execution,
                    tool_request=tool_request,
                    tool_call_id=tool_call.id,
                    arguments_payload=arguments_payload,
                )
                tool_call = self._repository.mark_tool_call_running(tool_call_id=tool_call.id)
        except ValidationError as exc:
            app_error = validation_error(
                "Assistant tool arguments were invalid",
                code="SS-VALIDATION-201",
                details={"tool_name": tool_request.tool_name, "reason": str(exc)},
            )
            failed = self._repository.fail_tool_call(
                tool_call_id=tool_call.id,
                error_code=app_error.code,
                error_message=app_error.message,
            )
            await self._publish_tool_event(
                execution=execution,
                tool_request=tool_request,
                tool_call=failed,
                event_type="tool.failed",
            )
            raise app_error from exc
        except AppError as exc:
            failed = self._repository.fail_tool_call(
                tool_call_id=tool_call.id,
                error_code=exc.code,
                error_message=exc.message,
            )
            await self._publish_tool_event(
                execution=execution,
                tool_request=tool_request,
                tool_call=failed,
                event_type="tool.failed",
            )
            raise

        await self._publish_tool_started(
            execution=execution,
            tool_request=tool_request,
            tool_call=tool_call,
        )
        try:
            result_payload, child_run_id = await self._dispatch_tool(
                stage_ctx=stage_ctx,
                execution=execution,
                tool_request=tool_request,
                tool_call_id=tool_call.id,
            )
            completed = self._repository.complete_tool_call(
                tool_call_id=tool_call.id,
                result_payload=result_payload,
                child_run_id=child_run_id,
            )
            await self._publish_tool_event(
                execution=execution,
                tool_request=tool_request,
                tool_call=completed,
                event_type="tool.completed",
            )
            return ToolPromptResult(
                tool_name=tool_request.tool_name,
                call_id=tool_request.call_id,
                payload=result_payload,
            )
        except (ValidationError, AppError) as exc:
            _, app_error = await self._fail_started_tool_call(
                execution=execution,
                tool_request=tool_request,
                tool_call_id=tool_call.id,
                error=exc,
            )
            return ToolPromptResult(
                tool_name=tool_request.tool_name,
                call_id=tool_request.call_id,
                payload=_tool_failure_payload(tool_name=tool_request.tool_name, error=app_error),
            )
        except Exception as exc:  # pragma: no cover - defensive wrapper
            app_error = orchestration_error(
                "Assistant tool execution failed unexpectedly",
                code="SS-ORCHESTRATION-201",
                details={"tool_name": tool_request.tool_name, "reason": str(exc)},
            )
            failed = self._repository.fail_tool_call(
                tool_call_id=tool_call.id,
                error_code=app_error.code,
                error_message=app_error.message,
            )
            await self._publish_tool_event(
                execution=execution,
                tool_request=tool_request,
                tool_call=failed,
                event_type="tool.failed",
            )
            return ToolPromptResult(
                tool_name=tool_request.tool_name,
                call_id=tool_request.call_id,
                payload=_tool_failure_payload(tool_name=tool_request.tool_name, error=app_error),
            )

    def _requires_approval(self, tool_name: str) -> bool:
        return tool_name not in self._auto_allow_tools

    async def _await_human_approval(
        self,
        *,
        execution: ToolExecutionContext,
        tool_request: AssistantToolRequest,
        tool_call_id: str,
        arguments_payload: dict[str, Any],
    ) -> None:
        approval = await self._approvals.request_tool_approval(
            tool_call_id=tool_call_id,
            approval_message=_approval_message(tool_request),
            payload_summary={
                "arguments": arguments_payload,
                "call_id": tool_request.call_id,
            },
            timeout_seconds=self._approval_timeout_seconds,
        )
        await self._broker.publish(
            execution.stream_token,
            self._repository.create_stream_event(
                turn_id=execution.turn_id,
                event_type="approval.requested",
                payload={
                    "approval_request_id": approval.id,
                    "tool_call_id": tool_call_id,
                    "call_id": tool_request.call_id,
                    "tool_name": tool_request.tool_name,
                    "approval_message": approval.approval_message,
                    "payload_summary": approval.payload_summary,
                    "status": approval.status.value,
                    "expires_at": (
                        None if approval.expires_at is None else approval.expires_at.isoformat()
                    ),
                },
                emitted_at=approval.requested_at,
            ),
        )
        decision = await self._approvals.await_decision(
            request_id=approval.id,
            timeout_seconds=self._approval_timeout_seconds,
        )
        decided = self._repository.get_approval_for_system(approval.id)
        await self._broker.publish(
            execution.stream_token,
            self._repository.create_stream_event(
                turn_id=execution.turn_id,
                event_type="approval.decided",
                payload={
                    "approval_request_id": decided.id,
                    "tool_call_id": tool_call_id,
                    "call_id": tool_request.call_id,
                    "tool_name": tool_request.tool_name,
                    "decision": decided.status.value,
                    "reason": decided.decision_reason,
                    "decided_by_user_id": decided.decided_by_user_id,
                },
                emitted_at=decided.decided_at or stage_now(),
            ),
        )
        if decision.granted:
            return
        if decided.status is AssistantApprovalStatus.EXPIRED:
            raise orchestration_error(
                "Assistant tool approval timed out",
                code="SS-ORCHESTRATION-202",
                status_code=408,
                details={
                    "tool_name": tool_request.tool_name,
                    "approval_request_id": decided.id,
                },
            )
        raise orchestration_error(
            "Assistant tool approval was denied",
            code="SS-ORCHESTRATION-203",
            status_code=409,
            details={
                "tool_name": tool_request.tool_name,
                "approval_request_id": decided.id,
            },
        )

    async def _dispatch_tool(
        self,
        *,
        stage_ctx: StageContext,
        execution: ToolExecutionContext,
        tool_request: AssistantToolRequest,
        tool_call_id: str,
    ) -> tuple[dict[str, Any], str | None]:
        arguments = tool_request.arguments_payload()
        if tool_request.tool_name == "query_user_context":
            guarded = self._sql_guard.validate_and_scope(
                QueryUserContextCommand.model_validate(arguments)
            )
            result = await self._sql_executor.execute(
                actor=execution.actor,
                query=guarded,
            )
            return result.model_dump(mode="json"), None
        if tool_request.tool_name == "start_collection_practice":
            practice_result = await self._practice_tools.start_collection_practice(
                actor=execution.actor,
                session_id=execution.session_id,
                request_id=execution.request_id,
                trace_id=execution.trace_id,
                args=StartCollectionPracticeToolArgs.model_validate(arguments),
            )
            return {"practice": practice_result.model_dump(mode="json")}, None
        if tool_request.tool_name == "get_active_practice":
            practice_result = self._practice_tools.get_active_practice(
                actor=execution.actor,
                session_id=execution.session_id,
            )
            return {"practice": practice_result.model_dump(mode="json")}, None
        if tool_request.tool_name == "submit_active_practice_response":
            practice_result = await self._practice_tools.submit_active_practice_response(
                actor=execution.actor,
                session_id=execution.session_id,
                request_id=execution.request_id,
                trace_id=execution.trace_id,
                response_text=_optional_string(arguments, "response_text"),
            )
            return {"practice": practice_result.model_dump(mode="json")}, None
        if tool_request.tool_name == "end_active_practice":
            practice_result = self._practice_tools.end_active_practice(
                actor=execution.actor,
                session_id=execution.session_id,
            )
            return {"practice": practice_result.model_dump(mode="json")}, None
        if tool_request.tool_name == "generate_collection":
            command = ChatCollectionGenerationCommand.model_validate(arguments)
            taxonomy_service = getattr(getattr(self._catalog, "_generation", None), "_taxonomy_service", None)
            if taxonomy_service is not None:
                command = _normalize_collection_generation_command(
                    command,
                    taxonomy_service.snapshot(execution.actor.organisation_id),
                )
            return await self._run_generate_collection(
                parent_ctx=stage_ctx,
                execution=execution,
                command=command,
                tool_request=tool_request,
                tool_call_id=tool_call_id,
            )
        if tool_request.tool_name == "generate_prompt_items":
            collection_id = _require_string(arguments, "collection_id")
            command_payload = dict(arguments)
            command_payload.pop("collection_id", None)
            return await self._run_generate_prompt_items(
                parent_ctx=stage_ctx,
                execution=execution,
                collection_id=collection_id,
                command=ChatPromptItemGenerationCommand.model_validate(command_payload),
                tool_request=tool_request,
            )
        raise validation_error(
            "Assistant requested an unknown tool",
            code="SS-VALIDATION-202",
            details={"tool_name": tool_request.tool_name},
        )

    async def _run_generate_collection(
        self,
        *,
        parent_ctx: StageContext,
        execution: ToolExecutionContext,
        command: ChatCollectionGenerationCommand,
        tool_request: AssistantToolRequest,
        tool_call_id: str,
    ) -> tuple[dict[str, Any], str | None]:
        del parent_ctx
        generation_service = self._catalog_generation_service()
        started_view, normalized_command = generation_service.prepare_chat_draft_stream(
            execution.actor,
            request_id=execution.request_id,
            trace_id=execution.trace_id,
            workflow_id=execution.workflow_id,
            command=command,
        )
        broker = getattr(generation_service, "_broker", None)
        if broker is None:
            raise orchestration_error(
                "Assistant generation streaming is unavailable",
                code="SS-ORCHESTRATION-204",
            )
        generation_execution = broker.get_execution_by_token(started_view.stream_token)
        if generation_execution is None:
            raise orchestration_error(
                "Assistant generation stream could not be initialized",
                code="SS-ORCHESTRATION-204",
                details={"stream_token": started_view.stream_token},
            )

        progress_state = _initial_generation_progress_state(started_view)
        await self._publish_generation_tool_update(
            execution=execution,
            tool_request=tool_request,
            tool_call_id=tool_call_id,
            result_payload=progress_state,
        )

        queue = broker.subscribe(started_view.stream_token)
        runner_task = asyncio.create_task(
            generation_service.run_chat_draft_stream(
                actor=execution.actor,
                execution=generation_execution,
                request_id=execution.request_id,
                trace_id=execution.trace_id,
                workflow_id=execution.workflow_id,
                command=normalized_command,
            )
        )
        terminal_event: GenerationStreamEvent | None = None

        try:
            while True:
                event = await queue.get()
                progress_state = _merge_generation_stream_event(
                    progress_state,
                    started_view=started_view,
                    event=event,
                )
                await self._publish_generation_tool_update(
                    execution=execution,
                    tool_request=tool_request,
                    tool_call_id=tool_call_id,
                    result_payload=progress_state,
                )
                if event.type in {"completed", "failed", "cancelled"}:
                    terminal_event = event
                    break
            await runner_task
        except asyncio.CancelledError:
            generation_execution.request_cancel("assistant_cancelled")
            runner_task.cancel()
            raise
        finally:
            broker.unsubscribe(started_view.stream_token, queue)
            if not runner_task.done():
                runner_task.cancel()
                await asyncio.gather(runner_task, return_exceptions=True)

        if terminal_event is None:
            raise orchestration_error(
                "Assistant generation stream ended without a terminal event",
                code="SS-ORCHESTRATION-204",
                details={"generation_id": started_view.generation_id},
            )
        if terminal_event.type == "failed":
            raise orchestration_error(
                "Assistant generation subpipeline failed",
                code="SS-ORCHESTRATION-204",
                details={
                    "generation_id": started_view.generation_id,
                    "stream_token": started_view.stream_token,
                    "error": terminal_event.payload.get("error"),
                },
            )
        if terminal_event.type == "cancelled":
            raise orchestration_error(
                "Assistant generation was cancelled",
                code="SS-ORCHESTRATION-204",
                details={
                    "generation_id": started_view.generation_id,
                    "stream_token": started_view.stream_token,
                    "reason": terminal_event.payload.get("reason"),
                },
            )

        collection_id = str(terminal_event.payload.get("collection_id") or "")
        if not collection_id:
            raise orchestration_error(
                "Assistant generation completed without a collection identifier",
                code="SS-ORCHESTRATION-204",
                details={"generation_id": started_view.generation_id},
            )
        collection = self._catalog.get_collection(execution.actor, collection_id)
        generation_summary = _summarize_streamed_generation_payload(
            progress_state=progress_state,
            collection=collection.model_dump(mode="json"),
            generation_artifact_id=str(terminal_event.payload.get("generation_artifact_id") or ""),
            provider=getattr(generation_service._llm_provider, "provider_name", None),
        )
        return ({"generation": generation_summary}, None)

    async def _run_generate_prompt_items(
        self,
        *,
        parent_ctx: StageContext,
        execution: ToolExecutionContext,
        collection_id: str,
        command: ChatPromptItemGenerationCommand,
        tool_request: AssistantToolRequest,
    ) -> tuple[dict[str, Any], str | None]:
        async def generation_stage(_ctx: StageContext) -> Any:
            result = await self._catalog.generate_prompt_items_chat(
                execution.actor,
                request_id=execution.request_id,
                trace_id=execution.trace_id,
                workflow_id=execution.workflow_id,
                collection_id=collection_id,
                command=command,
            )
            return ok_output(
                StageflowStageResult(
                    payload=result.model_dump(mode="json"),
                    summary={
                        "collection_id": result.collection.id,
                        "generation_artifact_id": result.generation_artifact_id,
                    },
                )
            )

        pipeline = Pipeline.from_stages(
            stage("generation", generation_stage, StageKind.WORK),
            name="assistant_generate_prompt_items",
        )
        result = await run_logged_subpipeline(
            self._stageflow,
            parent_ctx=parent_ctx,
            parent_stage_name=ASSISTANT_RUNTIME_STAGE,
            correlation_id=uuid4(),
            pipeline=pipeline,
            result_stage_name="generation",
            execution_mode="assistant_generation",
            service="soft_skills_backend.assistant",
            timeout_ms=self._generation_timeout_ms,
        )
        if not result.success or result.data is None:
            raise orchestration_error(
                "Assistant generation subpipeline failed",
                code="SS-ORCHESTRATION-204",
                details={"child_run_id": str(result.child_run_id), "error": result.error},
            )
        return (
            {"generation": _summarize_generation_payload(result.data["payload"])},
            str(result.child_run_id),
        )

    async def _publish_tool_started(
        self,
        *,
        execution: ToolExecutionContext,
        tool_request: AssistantToolRequest,
        tool_call: Any,
    ) -> None:
        await self._publish_tool_event(
            execution=execution,
            tool_request=tool_request,
            tool_call=tool_call,
            event_type="tool.started",
            emitted_at=tool_call.started_at,
        )

    async def _publish_tool_event(
        self,
        *,
        execution: ToolExecutionContext,
        tool_request: AssistantToolRequest,
        tool_call: Any,
        event_type: str,
        emitted_at: Any | None = None,
    ) -> None:
        await self._broker.publish(
            execution.stream_token,
            self._repository.create_stream_event(
                turn_id=execution.turn_id,
                event_type=event_type,
                payload=_stream_tool_call_payload(tool_call, call_id=tool_request.call_id),
                emitted_at=emitted_at or tool_call.completed_at or tool_call.started_at or stage_now(),
            ),
        )

    async def _publish_generation_tool_update(
        self,
        *,
        execution: ToolExecutionContext,
        tool_request: AssistantToolRequest,
        tool_call_id: str,
        result_payload: dict[str, Any],
    ) -> None:
        updated_tool_call = self._repository.update_tool_call_result(
            tool_call_id=tool_call_id,
            result_payload=result_payload,
        )
        await self._publish_tool_event(
            execution=execution,
            tool_request=tool_request,
            tool_call=updated_tool_call,
            event_type="tool.updated",
        )

    def _catalog_generation_service(self) -> CatalogGenerationService:
        generation_service = getattr(self._catalog, "_generation", None)
        if isinstance(generation_service, CatalogGenerationService):
            return generation_service
        raise orchestration_error(
            "Assistant generation service is unavailable",
            code="SS-ORCHESTRATION-204",
        )

    async def _fail_started_tool_call(
        self,
        *,
        execution: ToolExecutionContext,
        tool_request: AssistantToolRequest,
        tool_call_id: str,
        error: ValidationError | AppError,
    ) -> tuple[Any, AppError]:
        if isinstance(error, ValidationError):
            app_error = validation_error(
                "Assistant tool arguments were invalid",
                code="SS-VALIDATION-201",
                details={"tool_name": tool_request.tool_name, "reason": str(error)},
            )
        else:
            app_error = error
        failed = self._repository.fail_tool_call(
            tool_call_id=tool_call_id,
            error_code=app_error.code,
            error_message=app_error.message,
        )
        await self._publish_tool_event(
            execution=execution,
            tool_request=tool_request,
            tool_call=failed,
            event_type="tool.failed",
        )
        return failed, app_error


async def _gather_strict(tasks: list[Any]) -> list[Any]:
    results = await __import__("asyncio").gather(*tasks)
    return list(results)


def _require_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if isinstance(value, str) and value.strip():
        return value.strip()
    raise validation_error(
        "Assistant tool argument was missing",
        code="SS-VALIDATION-203",
        details={"argument": key},
    )


def _optional_string(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    raise validation_error(
        "Assistant tool argument had the wrong type",
        code="SS-VALIDATION-215",
        details={"argument": key, "expected_type": "string"},
    )


def _summarize_generation_payload(payload: dict[str, Any]) -> dict[str, Any]:
    collection = payload.get("collection", {})
    prompt_items = collection.get("prompt_items", [])
    scenarios = collection.get("scenarios", [])
    return {
        "collection_id": collection.get("id"),
        "title": collection.get("title"),
        "difficulty": collection.get("difficulty"),
        "content_format_mix": collection.get("content_format_mix", []),
        "prompt_item_count": len(prompt_items) if isinstance(prompt_items, list) else 0,
        "scenario_count": len(scenarios) if isinstance(scenarios, list) else 0,
        "generation_artifact_id": payload.get("generation_artifact_id"),
        "generation_mode": payload.get("generation_mode"),
        "provider": payload.get("provider"),
        "model_slug": payload.get("model_slug"),
    }


def _initial_generation_progress_state(started_view: GenerationStartedView) -> dict[str, Any]:
    return {
        "generation": {
            "generation_id": started_view.generation_id,
            "stream_token": started_view.stream_token,
            "generation_mode": started_view.mode,
            "current_stage": "pending",
            "progress_percent": 0.0,
            "blueprint": None,
            "prompt_items": [],
        }
    }


def _merge_generation_stream_event(
    state: dict[str, Any],
    *,
    started_view: GenerationStartedView,
    event: GenerationStreamEvent,
) -> dict[str, Any]:
    generation = dict(state.get("generation", {}))
    generation.update(
        {
            "generation_id": started_view.generation_id,
            "stream_token": started_view.stream_token,
            "generation_mode": started_view.mode,
            "current_stage": event.stage.value,
            "progress_percent": event.progress_percent,
        }
    )
    payload = dict(event.payload)
    if event.stage.value == "blueprint_llm_transform":
        generation["blueprint"] = {
            "title": payload.get("title"),
            "summary": payload.get("summary"),
            "prompt_items_count": payload.get("prompt_items_count", 0),
            "scenarios_count": payload.get("scenarios_count", 0),
        }
    if event.stage.value == "prompt_items_work" and isinstance(payload.get("prompt_items"), list):
        generation["prompt_items"] = list(payload["prompt_items"])
    if payload:
        generation["latest_event_payload"] = payload
    return {"generation": generation}


def _summarize_streamed_generation_payload(
    *,
    progress_state: dict[str, Any],
    collection: dict[str, Any],
    generation_artifact_id: str,
    provider: str | None,
) -> dict[str, Any]:
    generation = dict(progress_state.get("generation", {}))
    prompt_items = collection.get("prompt_items", [])
    scenarios = collection.get("scenarios", [])
    generation.update(
        {
            "collection_id": collection.get("id"),
            "title": collection.get("title"),
            "difficulty": collection.get("difficulty"),
            "content_format_mix": collection.get("content_format_mix", []),
            "prompt_item_count": len(prompt_items) if isinstance(prompt_items, list) else 0,
            "scenario_count": len(scenarios) if isinstance(scenarios, list) else 0,
            "generation_artifact_id": generation_artifact_id,
            "provider": provider,
            "model_slug": (
                generation.get("latest_event_payload", {}).get("model_slug")
                if isinstance(generation.get("latest_event_payload"), dict)
                else None
            ),
            "current_stage": "completed",
            "progress_percent": 100.0,
        }
    )
    return generation


def _stream_tool_call_payload(tool_call: Any, *, call_id: str) -> dict[str, Any]:
    payload = tool_call.model_dump(mode="json")
    payload["call_id"] = call_id
    return payload


def _tool_failure_payload(*, tool_name: str, error: AppError) -> dict[str, Any]:
    return {
        "status": "failed",
        "tool_name": tool_name,
        "error": {
            "code": error.code,
            "message": error.message,
            "details": dict(error.details or {}),
        },
    }


def _normalize_collection_generation_command(
    command: ChatCollectionGenerationCommand,
    snapshot: TaxonomySnapshot,
) -> ChatCollectionGenerationCommand:
    skill_slugs = list(command.target_skill_slugs)
    competency_slugs = list(command.target_competency_slugs)
    skill_index = {skill.slug: skill for skill in snapshot.skills}
    competency_index = {competency.slug: competency for competency in snapshot.competencies}

    if not skill_slugs:
        skill_slugs = _infer_skill_slugs(
            text=" ".join(
                part for part in (command.prompt, command.target_audience) if part.strip()
            ),
            snapshot=snapshot,
        )
    if not skill_slugs:
        skill_slugs = _default_skill_slugs(snapshot)

    if skill_slugs and not competency_slugs:
        competency_slugs = _infer_competency_slugs(skill_slugs=skill_slugs, snapshot=snapshot)

    if competency_slugs and skill_slugs:
        aligned = [
            skill_slug
            for skill_slug in skill_slugs
            if any(
                skill_slug in competency_index[competency_slug].skill_slugs
                for competency_slug in competency_slugs
                if competency_slug in competency_index
            )
        ]
        if aligned:
            skill_slugs = aligned

    content_format_mix = list(dict.fromkeys(command.content_format_mix))
    if command.counts.quick_practice_prompt_count > 0 and "quick_practice_prompt" not in content_format_mix:
        content_format_mix.append("quick_practice_prompt")
    if command.counts.interview_prompt_count > 0 and "interview_prompt" not in content_format_mix:
        content_format_mix.append("interview_prompt")
    if command.counts.scenario_count > 0 and "scenario_step" not in content_format_mix:
        content_format_mix.append("scenario_step")

    rubric_ids = list(dict.fromkeys(command.rubric_ids))
    if not rubric_ids:
        rubric_ids = _default_rubric_ids_for_formats(
            content_format_mix=content_format_mix,
            snapshot=snapshot,
        )

    counts = command.counts
    if counts.scenario_count == 0 and counts.scenario_artifact_count > 0:
        counts = CollectionGenerationCounts.model_validate(
            {
                **counts.model_dump(mode="json"),
                "scenario_artifact_count": 0,
            }
        )

    return command.model_copy(
        update={
            "target_skill_slugs": [slug for slug in skill_slugs if slug in skill_index],
            "target_competency_slugs": [
                slug for slug in competency_slugs if slug in competency_index
            ],
            "content_format_mix": content_format_mix,
            "rubric_ids": rubric_ids,
            "counts": counts,
        }
    )


def _infer_skill_slugs(*, text: str, snapshot: TaxonomySnapshot) -> list[str]:
    terms = set(_WORD_PATTERN.findall(text.lower()))
    scored: list[tuple[int, str]] = []
    for skill in snapshot.skills:
        skill_terms = set(_WORD_PATTERN.findall(skill.slug.replace("-", " "))) | set(
            _WORD_PATTERN.findall(skill.name.lower())
        )
        score = len(terms & skill_terms)
        if score > 0:
            scored.append((score, skill.slug))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [slug for _, slug in scored[:4]]


def _infer_competency_slugs(
    *,
    skill_slugs: list[str],
    snapshot: TaxonomySnapshot,
) -> list[str]:
    requested = set(skill_slugs)
    scored: list[tuple[int, str]] = []
    for competency in snapshot.competencies:
        overlap = len(requested & set(competency.skill_slugs))
        if overlap > 0:
            scored.append((overlap, competency.slug))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [slug for _, slug in scored[:2]]


def _default_rubric_ids_for_formats(
    *,
    content_format_mix: list[str],
    snapshot: TaxonomySnapshot,
) -> list[str]:
    selected: list[str] = []
    for content_type in content_format_mix:
        matching = [rubric for rubric in snapshot.rubrics if rubric.content_type == content_type]
        if not matching:
            continue
        general = [rubric for rubric in matching if rubric.skill_slug == "general"]
        chosen = sorted(general or matching, key=lambda rubric: rubric.rubric_id)[0]
        selected.append(chosen.rubric_id)
    return list(dict.fromkeys(selected))


def _default_skill_slugs(snapshot: TaxonomySnapshot) -> list[str]:
    available = {skill.slug for skill in snapshot.skills}
    prioritized = [slug for slug in _DEFAULT_SKILL_PRIORITY if slug in available]
    if prioritized:
        return prioritized[:4]
    return sorted(available)[:4]


def stage_now() -> datetime:
    from datetime import UTC

    return datetime.now(UTC)


def _approval_message(tool_request: AssistantToolRequest) -> str:
    arguments = tool_request.arguments_payload()
    if tool_request.tool_name == "generate_collection":
        title = arguments.get("title")
        return (
            f"Approve generate_collection for '{title}'?"
            if isinstance(title, str)
            else "Approve generate_collection?"
        )
    if tool_request.tool_name == "generate_prompt_items":
        collection_id = arguments.get("collection_id")
        return (
            f"Approve generate_prompt_items for collection {collection_id}?"
            if isinstance(collection_id, str)
            else "Approve generate_prompt_items?"
        )
    if tool_request.tool_name == "start_collection_practice":
        collection_id = arguments.get("collection_id")
        return (
            f"Approve start_collection_practice for collection {collection_id}?"
            if isinstance(collection_id, str)
            else "Approve start_collection_practice?"
        )
    return f"Approve {tool_request.tool_name}?"
