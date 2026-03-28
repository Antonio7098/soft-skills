"""Assistant tool execution runtime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from pydantic import ValidationError
from stageflow.api import Pipeline, StageKind, stage
from stageflow.core import StageContext

from soft_skills_backend.modules.assistant.infra.realtime import AssistantRealtimeBroker
from soft_skills_backend.modules.assistant.infra.repository import AssistantRepository
from soft_skills_backend.modules.assistant.workflows.practice_facilitation import (
    AssistantPracticeCoordinator,
    StartCollectionPracticeToolArgs,
)
from soft_skills_backend.modules.assistant.workflows.runtime_models import AssistantToolRequest
from soft_skills_backend.modules.catalog import CatalogService
from soft_skills_backend.modules.catalog.contracts.collection_commands import (
    ChatCollectionGenerationCommand,
    CollectionListFilters,
)
from soft_skills_backend.modules.catalog.contracts.prompt_item_commands import (
    ChatPromptItemGenerationCommand,
)
from soft_skills_backend.modules.practice import PracticeService
from soft_skills_backend.platform.workflows.stageflow import (
    StageflowPipelineSupport,
    StageflowStageResult,
    ok_output,
    run_logged_subpipeline,
)
from soft_skills_backend.shared.auth import Actor
from soft_skills_backend.shared.errors import AppError, orchestration_error, validation_error

ASSISTANT_RUNTIME_STAGE = "assistant_runtime"


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
        broker: AssistantRealtimeBroker,
        catalog_service: CatalogService,
        practice_service: PracticeService,
        stageflow_support: StageflowPipelineSupport,
    ) -> None:
        self._repository = repository
        self._broker = broker
        self._catalog = catalog_service
        self._practice = practice_service
        self._stageflow = stageflow_support
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
        tool_call = self._repository.create_tool_call(
            turn_id=execution.turn_id,
            tool_name=tool_request.tool_name,
            args_payload=tool_request.arguments,
        )
        await self._broker.publish(
            execution.stream_token,
            self._repository.create_stream_event(
                turn_id=execution.turn_id,
                event_type="tool.started",
                payload={
                    "tool_call_id": tool_call.id,
                    "call_id": tool_request.call_id,
                    "tool_name": tool_request.tool_name,
                    "arguments": tool_request.arguments,
                },
                emitted_at=tool_call.started_at,
            ),
        )
        try:
            result_payload, child_run_id = await self._dispatch_tool(
                stage_ctx=stage_ctx,
                execution=execution,
                tool_request=tool_request,
            )
            completed = self._repository.complete_tool_call(
                tool_call_id=tool_call.id,
                result_payload=result_payload,
                child_run_id=child_run_id,
            )
            await self._broker.publish(
                execution.stream_token,
                self._repository.create_stream_event(
                    turn_id=execution.turn_id,
                    event_type="tool.completed",
                    payload={
                        "tool_call_id": completed.id,
                        "call_id": tool_request.call_id,
                        "tool_name": completed.tool_name,
                        "result": result_payload,
                        "child_run_id": child_run_id,
                    },
                    emitted_at=completed.completed_at or completed.started_at,
                ),
            )
            return ToolPromptResult(
                tool_name=tool_request.tool_name,
                call_id=tool_request.call_id,
                payload=result_payload,
            )
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
            await self._publish_tool_failure(
                execution=execution,
                tool_request=tool_request,
                tool_call_id=failed.id,
                error=app_error,
            )
            raise app_error from exc
        except AppError as exc:
            failed = self._repository.fail_tool_call(
                tool_call_id=tool_call.id,
                error_code=exc.code,
                error_message=exc.message,
            )
            await self._publish_tool_failure(
                execution=execution,
                tool_request=tool_request,
                tool_call_id=failed.id,
                error=exc,
            )
            raise exc
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
            await self._publish_tool_failure(
                execution=execution,
                tool_request=tool_request,
                tool_call_id=failed.id,
                error=app_error,
            )
            raise app_error from exc

    async def _dispatch_tool(
        self,
        *,
        stage_ctx: StageContext,
        execution: ToolExecutionContext,
        tool_request: AssistantToolRequest,
    ) -> tuple[dict[str, Any], str | None]:
        arguments = tool_request.arguments
        if tool_request.tool_name == "list_collections":
            filters = CollectionListFilters.model_validate(arguments)
            result = self._catalog.list_collections(execution.actor, filters)
            return {"collections": [item.model_dump(mode="json") for item in result]}, None
        if tool_request.tool_name == "get_collection":
            collection_id = _require_string(arguments, "collection_id")
            collection = self._catalog.get_collection(execution.actor, collection_id)
            return {"collection": collection.model_dump(mode="json")}, None
        if tool_request.tool_name == "list_recent_attempts":
            limit = int(arguments.get("limit", 5))
            limit = max(1, min(limit, 10))
            return {
                "attempts": self._repository.load_recent_attempts(
                    actor=execution.actor, limit=limit
                )
            }, None
        if tool_request.tool_name == "get_attempt":
            attempt_id = _require_string(arguments, "attempt_id")
            attempt = self._practice.get_attempt(execution.actor, attempt_id)
            return {"attempt": attempt.model_dump(mode="json")}, None
        if tool_request.tool_name == "start_collection_practice":
            result = await self._practice_tools.start_collection_practice(
                actor=execution.actor,
                session_id=execution.session_id,
                request_id=execution.request_id,
                trace_id=execution.trace_id,
                args=StartCollectionPracticeToolArgs.model_validate(arguments),
            )
            return {"practice": result.model_dump(mode="json")}, None
        if tool_request.tool_name == "get_active_practice":
            result = self._practice_tools.get_active_practice(
                actor=execution.actor,
                session_id=execution.session_id,
            )
            return {"practice": result.model_dump(mode="json")}, None
        if tool_request.tool_name == "submit_active_practice_response":
            result = await self._practice_tools.submit_active_practice_response(
                actor=execution.actor,
                session_id=execution.session_id,
                request_id=execution.request_id,
                trace_id=execution.trace_id,
                response_text=_optional_string(arguments, "response_text"),
            )
            return {"practice": result.model_dump(mode="json")}, None
        if tool_request.tool_name == "end_active_practice":
            result = self._practice_tools.end_active_practice(
                actor=execution.actor,
                session_id=execution.session_id,
            )
            return {"practice": result.model_dump(mode="json")}, None
        if tool_request.tool_name == "generate_collection":
            return await self._run_generate_collection(
                parent_ctx=stage_ctx,
                execution=execution,
                command=ChatCollectionGenerationCommand.model_validate(arguments),
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
    ) -> tuple[dict[str, Any], str | None]:
        async def generation_stage(_ctx: StageContext) -> Any:
            result = await self._catalog.generate_chat_draft(
                execution.actor,
                request_id=execution.request_id,
                trace_id=execution.trace_id,
                workflow_id=execution.workflow_id,
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
            stage("generation", generation_stage, StageKind.WORK),  # type: ignore[arg-type]
            name="assistant_generate_collection",
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
        )
        if not result.success or result.data is None:
            raise orchestration_error(
                "Assistant generation subpipeline failed",
                code="SS-ORCHESTRATION-202",
                details={"child_run_id": str(result.child_run_id), "error": result.error},
            )
        return {"generation": result.data["payload"]}, str(result.child_run_id)

    async def _run_generate_prompt_items(
        self,
        *,
        parent_ctx: StageContext,
        execution: ToolExecutionContext,
        collection_id: str,
        command: ChatPromptItemGenerationCommand,
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
            stage("generation", generation_stage, StageKind.WORK),  # type: ignore[arg-type]
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
        )
        if not result.success or result.data is None:
            raise orchestration_error(
                "Assistant generation subpipeline failed",
                code="SS-ORCHESTRATION-202",
                details={"child_run_id": str(result.child_run_id), "error": result.error},
            )
        return {"generation": result.data["payload"]}, str(result.child_run_id)

    async def _publish_tool_failure(
        self,
        *,
        execution: ToolExecutionContext,
        tool_request: AssistantToolRequest,
        tool_call_id: str,
        error: AppError,
    ) -> None:
        await self._broker.publish(
            execution.stream_token,
            self._repository.create_stream_event(
                turn_id=execution.turn_id,
                event_type="tool.failed",
                payload={
                    "tool_call_id": tool_call_id,
                    "call_id": tool_request.call_id,
                    "tool_name": tool_request.tool_name,
                    "error_code": error.code,
                    "message": error.message,
                },
                emitted_at=stage_now(),
            ),
        )


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


def stage_now():
    from datetime import UTC, datetime

    return datetime.now(UTC)
