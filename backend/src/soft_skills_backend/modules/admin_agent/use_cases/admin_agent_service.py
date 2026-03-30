"""Admin-agent application facade."""

from __future__ import annotations

from uuid import uuid4

from soft_skills_backend.modules.admin_agent.contracts.commands import (
    AdminAgentChatCommand,
    AdminAgentCorrelation,
)
from soft_skills_backend.modules.admin_agent.contracts.views import AdminAgentChatView
from soft_skills_backend.modules.admin_agent.workflows.service import (
    AdminAgentExecutionInput,
    AdminAgentWorkflowService,
)
from soft_skills_backend.shared.auth import Actor


class AdminAgentService:
    """Execute admin investigations through the constrained admin agent pipeline."""

    def __init__(self, *, workflows: AdminAgentWorkflowService) -> None:
        self._workflows = workflows

    async def chat(
        self,
        actor: Actor,
        correlation: AdminAgentCorrelation,
        command: AdminAgentChatCommand,
    ) -> AdminAgentChatView:
        conversation_id = command.conversation_id or correlation.workflow_id or uuid4().hex
        return await self._workflows.run_chat(
            AdminAgentExecutionInput(
                actor=actor,
                request_id=correlation.request_id,
                trace_id=correlation.trace_id,
                workflow_id=conversation_id,
                conversation_id=conversation_id,
                message=command.message,
            )
        )
