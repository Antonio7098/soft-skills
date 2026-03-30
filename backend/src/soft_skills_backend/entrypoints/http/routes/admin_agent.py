"""Admin-agent HTTP endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request

from soft_skills_backend.entrypoints.http.dependencies import (
    get_admin_agent_service,
    require_admin_actor,
)
from soft_skills_backend.entrypoints.http.schemas import ApiEnvelope, ok_response
from soft_skills_backend.modules.admin_agent import (
    AdminAgentChatCommand,
    AdminAgentChatView,
    AdminAgentCorrelation,
)

router = APIRouter()


def _correlation_from_request(request: Request) -> AdminAgentCorrelation:
    return AdminAgentCorrelation(
        request_id=getattr(request.state, "request_id", ""),
        trace_id=getattr(request.state, "trace_id", ""),
        workflow_id=getattr(request.state, "workflow_id", None),
    )


@router.post("/chat", response_model=ApiEnvelope[AdminAgentChatView])
async def chat(
    request: Request,
    command: AdminAgentChatCommand,
) -> ApiEnvelope[AdminAgentChatView]:
    actor = await require_admin_actor(request)
    service = get_admin_agent_service(request)
    payload = await service.chat(actor, _correlation_from_request(request), command)
    return ok_response(request, payload)
