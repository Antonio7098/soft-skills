"""Generation HTTP and websocket endpoints."""

from __future__ import annotations

import asyncio
from contextlib import suppress
from dataclasses import dataclass
from typing import Any

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect

from soft_skills_backend.entrypoints.http.dependencies import (
    require_actor,
)
from soft_skills_backend.entrypoints.http.schemas import ApiEnvelope, ok_response
from soft_skills_backend.modules.catalog import (
    ChatCollectionGenerationCommand,
    StructuredCollectionGenerationCommand,
)
from soft_skills_backend.modules.catalog.contracts.stream import GenerationControlMessage
from soft_skills_backend.modules.catalog.domain.validators import validate_generation_request
from soft_skills_backend.modules.catalog.infra.realtime import GenerationRealtimeBroker
from soft_skills_backend.modules.catalog.workflows.generation.service import (
    CatalogGenerationService,
)
from soft_skills_backend.platform.background_tasks import BackgroundTaskRunner

router = APIRouter()


@dataclass(frozen=True, slots=True)
class GenerationCorrelation:
    request_id: str
    trace_id: str
    workflow_id: str | None


def _correlation_from_request(request: Request) -> GenerationCorrelation:
    return GenerationCorrelation(
        request_id=getattr(request.state, "request_id", ""),
        trace_id=getattr(request.state, "trace_id", ""),
        workflow_id=getattr(request.state, "workflow_id", None),
    )


@router.post(
    "/collections/generate/structured",
    response_model=ApiEnvelope[dict[str, Any]],
)
async def start_structured_generation(
    request: Request,
    command: StructuredCollectionGenerationCommand,
) -> ApiEnvelope[dict[str, Any]]:
    actor = await require_actor(request)
    container = request.app.state.container
    catalog_service: CatalogGenerationService = container.catalog_service._generation
    broker: GenerationRealtimeBroker = container.generation_broker
    background_tasks: BackgroundTaskRunner = container.background_tasks
    session_factory = container.session_factory
    correlation = _correlation_from_request(request)

    # Validate input synchronously before returning 200
    with session_factory() as session:
        validate_generation_request(session, command)

    started_view, cmd = catalog_service.prepare_structured_draft_stream(
        actor,
        request_id=correlation.request_id,
        trace_id=correlation.trace_id,
        workflow_id=correlation.workflow_id,
        command=command,
    )

    async def run_in_background() -> None:
        execution = broker.get_execution_by_token(started_view.stream_token)
        if execution is None:
            return
        with suppress(Exception):
            await catalog_service.run_structured_draft_stream(
                actor=actor,
                execution=execution,
                request_id=correlation.request_id,
                trace_id=correlation.trace_id,
                workflow_id=correlation.workflow_id,
                command=cmd,
            )

    background_tasks.start(run_in_background())

    return ok_response(
        request,
        {
            "generation_id": started_view.generation_id,
            "stream_token": started_view.stream_token,
            "mode": started_view.mode,
        },
    )


@router.post(
    "/collections/generate/chat",
    response_model=ApiEnvelope[dict[str, Any]],
)
async def start_chat_generation(
    request: Request,
    command: ChatCollectionGenerationCommand,
) -> ApiEnvelope[dict[str, Any]]:
    actor = await require_actor(request)
    container = request.app.state.container
    catalog_service: CatalogGenerationService = container.catalog_service._generation
    broker: GenerationRealtimeBroker = container.generation_broker
    background_tasks: BackgroundTaskRunner = container.background_tasks
    session_factory = container.session_factory
    correlation = _correlation_from_request(request)

    # Validate input synchronously before returning 200
    with session_factory() as session:
        validate_generation_request(session, command)

    started_view, cmd = catalog_service.prepare_chat_draft_stream(
        actor,
        request_id=correlation.request_id,
        trace_id=correlation.trace_id,
        workflow_id=correlation.workflow_id,
        command=command,
    )

    async def run_in_background() -> None:
        execution = broker.get_execution_by_token(started_view.stream_token)
        if execution is None:
            return
        with suppress(Exception):
            await catalog_service.run_chat_draft_stream(
                actor=actor,
                execution=execution,
                request_id=correlation.request_id,
                trace_id=correlation.trace_id,
                workflow_id=correlation.workflow_id,
                command=cmd,
            )

    background_tasks.start(run_in_background())

    return ok_response(
        request,
        {
            "generation_id": started_view.generation_id,
            "stream_token": started_view.stream_token,
            "mode": started_view.mode,
        },
    )


@router.websocket("/ws/generation/{stream_token}")
async def stream_generation(websocket: WebSocket, stream_token: str) -> None:
    container = websocket.app.state.container
    broker: GenerationRealtimeBroker = container.generation_broker

    await websocket.accept()

    execution = broker.get_execution_by_token(stream_token)
    if execution is None:
        await websocket.send_json(
            {
                "type": "error",
                "code": "NOT_FOUND",
                "message": "Generation not found or already completed",
            }
        )
        await websocket.close(code=4404)
        return
    queue = broker.subscribe(stream_token)
    last_sequence_raw = websocket.query_params.get("last_event_id")
    last_sequence = None if last_sequence_raw is None else int(last_sequence_raw)

    try:
        backlog = broker.backlog(stream_token, after_sequence=last_sequence)
        if backlog:
            for event in backlog:
                await websocket.send_json(event.model_dump(mode="json"))
        else:
            for event in broker.backlog(stream_token, after_sequence=last_sequence):
                await websocket.send_json(event.model_dump(mode="json"))

        while True:
            receive_task = asyncio.create_task(websocket.receive_json())
            event_task = asyncio.create_task(queue.get())
            done, pending = await asyncio.wait(
                {receive_task, event_task},
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()

            if event_task in done:
                event = event_task.result()
                await websocket.send_json(event.model_dump(mode="json"))
                continue

            message = GenerationControlMessage.model_validate(receive_task.result())
            if message.action == "cancel":
                execution.request_cancel(message.reason or "user_requested")
                if execution.task is not None:
                    execution.task.cancel()
            elif message.action == "ping":
                await websocket.send_json(
                    {
                        "type": "pong",
                        "generation_id": execution.generation_id,
                    }
                )
    except WebSocketDisconnect:
        return
    finally:
        broker.unsubscribe(stream_token, queue)
