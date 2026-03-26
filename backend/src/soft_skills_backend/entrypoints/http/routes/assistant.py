"""Assistant HTTP and websocket endpoints."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect

from soft_skills_backend.entrypoints.http.dependencies import get_assistant_service, require_actor
from soft_skills_backend.entrypoints.http.schemas import ApiEnvelope, ok_response
from soft_skills_backend.modules.assistant import (
    AssistantCorrelation,
    AssistantMessageView,
    AssistantService,
    AssistantSessionView,
    AssistantStreamControlMessage,
    AssistantTurnView,
    CancelAssistantTurnCommand,
    CreateAssistantSessionCommand,
    CreateAssistantTurnCommand,
)
from soft_skills_backend.shared.errors import AppError

router = APIRouter()


def _correlation_from_request(request: Request) -> AssistantCorrelation:
    return AssistantCorrelation(
        request_id=getattr(request.state, "request_id", ""),
        trace_id=getattr(request.state, "trace_id", ""),
        workflow_id=getattr(request.state, "workflow_id", None),
    )


@router.post("/sessions", response_model=ApiEnvelope[AssistantSessionView])
async def create_session(
    request: Request,
    command: CreateAssistantSessionCommand,
) -> ApiEnvelope[AssistantSessionView]:
    actor = require_actor(request)
    service = get_assistant_service(request)
    payload = service.create_session(actor, _correlation_from_request(request), command)
    return ok_response(request, payload)


@router.get("/sessions", response_model=ApiEnvelope[list[AssistantSessionView]])
async def list_sessions(request: Request) -> ApiEnvelope[list[AssistantSessionView]]:
    actor = require_actor(request)
    service = get_assistant_service(request)
    return ok_response(request, service.list_sessions(actor))


@router.get("/sessions/{session_id}", response_model=ApiEnvelope[AssistantSessionView])
async def get_session(request: Request, session_id: str) -> ApiEnvelope[AssistantSessionView]:
    actor = require_actor(request)
    service = get_assistant_service(request)
    return ok_response(request, service.get_session(actor, session_id))


@router.get("/sessions/{session_id}/messages", response_model=ApiEnvelope[list[AssistantMessageView]])
async def list_messages(
    request: Request,
    session_id: str,
) -> ApiEnvelope[list[AssistantMessageView]]:
    actor = require_actor(request)
    service = get_assistant_service(request)
    return ok_response(request, service.list_messages(actor, session_id))


@router.post("/sessions/{session_id}/turns", response_model=ApiEnvelope[AssistantTurnView])
async def create_turn(
    request: Request,
    session_id: str,
    command: CreateAssistantTurnCommand,
) -> ApiEnvelope[AssistantTurnView]:
    actor = require_actor(request)
    service = get_assistant_service(request)
    payload = service.create_turn(actor, _correlation_from_request(request), session_id, command)
    return ok_response(request, payload)


@router.post("/turns/{turn_id}/cancel", response_model=ApiEnvelope[AssistantTurnView])
async def cancel_turn(
    request: Request,
    turn_id: str,
    command: CancelAssistantTurnCommand,
) -> ApiEnvelope[AssistantTurnView]:
    actor = require_actor(request)
    service = get_assistant_service(request)
    payload = await service.cancel_turn(actor, turn_id, command)
    return ok_response(request, payload)


@router.get("/turns/{turn_id}", response_model=ApiEnvelope[AssistantTurnView])
async def get_turn(request: Request, turn_id: str) -> ApiEnvelope[AssistantTurnView]:
    actor = require_actor(request)
    service = get_assistant_service(request)
    return ok_response(request, service.get_turn(actor, turn_id))


@router.websocket("/streams/{stream_token}")
async def stream_turn(websocket: WebSocket, stream_token: str) -> None:
    container = websocket.app.state.container
    service: AssistantService = container.assistant_service
    broker = container.assistant_broker
    try:
        service.get_turn_by_stream_token(stream_token)
    except AppError:
        await websocket.close(code=4404)
        return

    await websocket.accept()
    queue = broker.subscribe(stream_token)
    last_sequence_raw = websocket.query_params.get("last_event_id")
    last_sequence = None if last_sequence_raw is None else int(last_sequence_raw)
    try:
        backlog = broker.backlog(stream_token, after_sequence=last_sequence)
        if backlog:
            for event in backlog:
                await websocket.send_json(event.model_dump(mode="json"))
        else:
            for event in service.list_stream_events(stream_token, after_sequence=last_sequence):
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

            message = AssistantStreamControlMessage.model_validate(receive_task.result())
            if message.type == "turn.cancel":
                await service.cancel_turn_by_stream_token(
                    stream_token,
                    CancelAssistantTurnCommand(reason=message.reason or "user_requested"),
                )
    except WebSocketDisconnect:
        return
    finally:
        broker.unsubscribe(stream_token, queue)
