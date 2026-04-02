"""Assistant HTTP and websocket endpoints."""

from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from soft_skills_backend.entrypoints.http.dependencies import get_assistant_service, require_actor
from soft_skills_backend.entrypoints.http.schemas import ApiEnvelope, ok_response
from soft_skills_backend.modules.assistant import (
    AssistantApprovalView,
    AssistantCorrelation,
    AssistantMessageView,
    AssistantService,
    AssistantSessionView,
    AssistantStreamControlMessage,
    AssistantTurnView,
    CancelAssistantTurnCommand,
    DecideAssistantApprovalCommand,
    CreateAssistantSessionCommand,
    CreateAssistantTurnCommand,
)
from soft_skills_backend.modules.assistant.domain.models import AssistantApprovalStatus
from soft_skills_backend.shared.errors import AppError

router = APIRouter()


def _format_sse_event(event: dict[str, object], *, event_id: str | None = None) -> str:
    lines: list[str] = []
    if event_id is not None:
        lines.append(f"id: {event_id}")
    lines.append(f"data: {json.dumps(event)}")
    return "\n".join(lines) + "\n\n"


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
    actor = await require_actor(request)
    service = get_assistant_service(request)
    payload = service.create_session(actor, _correlation_from_request(request), command)
    return ok_response(request, payload)


@router.get("/sessions", response_model=ApiEnvelope[list[AssistantSessionView]])
async def list_sessions(request: Request) -> ApiEnvelope[list[AssistantSessionView]]:
    actor = await require_actor(request)
    service = get_assistant_service(request)
    return ok_response(request, service.list_sessions(actor))


@router.get("/sessions/{session_id}", response_model=ApiEnvelope[AssistantSessionView])
async def get_session(request: Request, session_id: str) -> ApiEnvelope[AssistantSessionView]:
    actor = await require_actor(request)
    service = get_assistant_service(request)
    return ok_response(request, service.get_session(actor, session_id))


@router.get(
    "/sessions/{session_id}/messages", response_model=ApiEnvelope[list[AssistantMessageView]]
)
async def list_messages(
    request: Request,
    session_id: str,
) -> ApiEnvelope[list[AssistantMessageView]]:
    actor = await require_actor(request)
    service = get_assistant_service(request)
    return ok_response(request, service.list_messages(actor, session_id))


@router.post("/sessions/{session_id}/turns", response_model=ApiEnvelope[AssistantTurnView])
async def create_turn(
    request: Request,
    session_id: str,
    command: CreateAssistantTurnCommand,
) -> ApiEnvelope[AssistantTurnView]:
    actor = await require_actor(request)
    service = get_assistant_service(request)
    payload = service.create_turn(actor, _correlation_from_request(request), session_id, command)
    return ok_response(request, payload)


@router.post("/turns/{turn_id}/cancel", response_model=ApiEnvelope[AssistantTurnView])
async def cancel_turn(
    request: Request,
    turn_id: str,
    command: CancelAssistantTurnCommand,
) -> ApiEnvelope[AssistantTurnView]:
    actor = await require_actor(request)
    service = get_assistant_service(request)
    payload = await service.cancel_turn(actor, turn_id, command)
    return ok_response(request, payload)


@router.get("/turns/{turn_id}", response_model=ApiEnvelope[AssistantTurnView])
async def get_turn(request: Request, turn_id: str) -> ApiEnvelope[AssistantTurnView]:
    actor = await require_actor(request)
    service = get_assistant_service(request)
    return ok_response(request, service.get_turn(actor, turn_id))


@router.get("/approvals", response_model=ApiEnvelope[list[AssistantApprovalView]])
async def list_approvals(
    request: Request,
    status: AssistantApprovalStatus | None = None,
    session_id: str | None = None,
    turn_id: str | None = None,
) -> ApiEnvelope[list[AssistantApprovalView]]:
    actor = await require_actor(request)
    service = get_assistant_service(request)
    return ok_response(
        request,
        service.list_approvals(
            actor,
            status=status,
            session_id=session_id,
            turn_id=turn_id,
        ),
    )


@router.post("/approvals/{request_id}", response_model=ApiEnvelope[AssistantApprovalView])
async def decide_approval(
    request: Request,
    request_id: str,
    command: DecideAssistantApprovalCommand,
) -> ApiEnvelope[AssistantApprovalView]:
    actor = await require_actor(request)
    service = get_assistant_service(request)
    payload = await service.decide_approval(actor, request_id, command)
    return ok_response(request, payload)


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


@router.get("/streams/{stream_token}/events")
async def stream_turn_events(request: Request, stream_token: str) -> StreamingResponse:
    actor = await require_actor(request)
    service = get_assistant_service(request)
    turn = service.get_turn_by_stream_token(stream_token)
    service.get_turn(actor, turn.id)

    last_event_id_raw = request.headers.get("last-event-id") or request.query_params.get("last_event_id")
    last_sequence = None if last_event_id_raw is None else int(last_event_id_raw)

    async def event_stream() -> AsyncIterator[str]:
        current_sequence = last_sequence
        heartbeat_interval = 15.0
        poll_interval = 0.25
        elapsed_since_heartbeat = 0.0

        while True:
            if await request.is_disconnected():
                return

            events = service.list_stream_events(stream_token, after_sequence=current_sequence)
            if events:
                for event in events:
                    current_sequence = event.sequence_number
                    yield _format_sse_event(
                        event.model_dump(mode="json"),
                        event_id=str(event.sequence_number),
                    )
                    if event.type in {"turn.completed", "turn.failed", "turn.cancelled"}:
                        return
                elapsed_since_heartbeat = 0.0
                continue

            latest_turn = service.get_turn(actor, turn.id)
            if latest_turn.status in {"completed", "failed", "cancelled"}:
                return

            if elapsed_since_heartbeat >= heartbeat_interval:
                yield ": keep-alive\n\n"
                elapsed_since_heartbeat = 0.0

            await asyncio.sleep(poll_interval)
            elapsed_since_heartbeat += poll_interval

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers=headers,
    )
