"""Assistant application facade."""

from __future__ import annotations

import asyncio
from uuid import uuid4

from soft_skills_backend.modules.assistant.contracts.commands import (
    AssistantCorrelation,
    CancelAssistantTurnCommand,
    CreateAssistantSessionCommand,
    CreateAssistantTurnCommand,
)
from soft_skills_backend.modules.assistant.contracts.stream import AssistantStreamEvent
from soft_skills_backend.modules.assistant.contracts.views import (
    AssistantMessageView,
    AssistantSessionView,
    AssistantTurnView,
)
from soft_skills_backend.modules.assistant.infra.repository import AssistantRepository
from soft_skills_backend.modules.assistant.workflows.service import (
    AssistantTurnExecutionInput,
    AssistantWorkflowService,
)
from soft_skills_backend.shared.auth import Actor


class AssistantService:
    """Own assistant session and turn lifecycle entrypoints."""

    def __init__(
        self,
        *,
        repository: AssistantRepository,
        workflows: AssistantWorkflowService,
    ) -> None:
        self._repository = repository
        self._workflows = workflows

    def create_session(
        self,
        actor: Actor,
        correlation: AssistantCorrelation,
        command: CreateAssistantSessionCommand,
    ) -> AssistantSessionView:
        return self._repository.create_session(
            actor=actor,
            title=command.title,
            request_id=correlation.request_id,
            trace_id=correlation.trace_id,
        )

    def get_session(self, actor: Actor, session_id: str) -> AssistantSessionView:
        return self._repository.get_session(actor, session_id)

    def list_sessions(self, actor: Actor) -> list[AssistantSessionView]:
        return self._repository.list_sessions(actor)

    def list_messages(self, actor: Actor, session_id: str) -> list[AssistantMessageView]:
        return self._repository.list_messages(actor=actor, session_id=session_id)

    def get_turn(self, actor: Actor, turn_id: str) -> AssistantTurnView:
        return self._repository.get_turn(actor, turn_id)

    def get_turn_by_stream_token(self, stream_token: str) -> AssistantTurnView:
        return self._repository.get_turn_by_stream_token(stream_token)

    def list_stream_events(
        self,
        stream_token: str,
        *,
        after_sequence: int | None = None,
    ) -> list[AssistantStreamEvent]:
        return self._repository.list_stream_events(
            stream_token=stream_token,
            after_sequence=after_sequence,
        )

    def create_turn(
        self,
        actor: Actor,
        correlation: AssistantCorrelation,
        session_id: str,
        command: CreateAssistantTurnCommand,
    ) -> AssistantTurnView:
        workflow_id = correlation.workflow_id or uuid4().hex
        turn = self._repository.create_turn(
            actor=actor,
            session_id=session_id,
            request_id=correlation.request_id,
            trace_id=correlation.trace_id,
            workflow_id=workflow_id,
            message_text=command.message,
        )
        asyncio.get_running_loop().create_task(
            self._workflows.run_turn(
                AssistantTurnExecutionInput(
                    actor=actor,
                    request_id=correlation.request_id,
                    trace_id=correlation.trace_id,
                    workflow_id=workflow_id,
                    session_id=session_id,
                    turn_id=turn.id,
                    stream_token=turn.stream_token,
                )
            )
        )
        return turn

    async def cancel_turn(
        self,
        actor: Actor,
        turn_id: str,
        command: CancelAssistantTurnCommand,
    ) -> AssistantTurnView:
        turn = self._repository.get_turn(actor, turn_id)
        return await self._workflows.request_cancel(turn=turn, reason=command.reason)

    async def cancel_turn_by_stream_token(
        self,
        stream_token: str,
        command: CancelAssistantTurnCommand,
    ) -> AssistantTurnView:
        turn = self._repository.get_turn_by_stream_token(stream_token)
        return await self._workflows.request_cancel(turn=turn, reason=command.reason)
