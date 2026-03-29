"""Persistent assistant approval workflow service."""

from __future__ import annotations

import asyncio

from stageflow.tools.approval import ApprovalDecision

from soft_skills_backend.modules.assistant.contracts.views import AssistantApprovalView
from soft_skills_backend.modules.assistant.domain.models import AssistantApprovalStatus
from soft_skills_backend.modules.assistant.infra.repository import AssistantRepository
from soft_skills_backend.shared.auth import Actor


class AssistantApprovalService:
    """Coordinate persisted approval requests with in-process async waiters."""

    def __init__(self, *, repository: AssistantRepository) -> None:
        self._repository = repository
        self._events: dict[str, asyncio.Event] = {}
        self._lock = asyncio.Lock()

    async def request_tool_approval(
        self,
        *,
        tool_call_id: str,
        approval_message: str,
        payload_summary: dict[str, object],
        timeout_seconds: float,
    ) -> AssistantApprovalView:
        return self._repository.create_approval_request(
            tool_call_id=tool_call_id,
            approval_message=approval_message,
            payload_summary=dict(payload_summary),
            timeout_seconds=timeout_seconds,
        )

    async def await_decision(
        self,
        *,
        request_id: str,
        timeout_seconds: float,
    ) -> ApprovalDecision:
        async with self._lock:
            event = self._events.get(request_id)
            if event is None:
                event = asyncio.Event()
                self._events[request_id] = event

        approval = self._repository.get_approval_for_system(request_id)
        if approval.status is not AssistantApprovalStatus.PENDING:
            return ApprovalDecision(
                request_id=_as_uuid(request_id),
                granted=approval.status is AssistantApprovalStatus.APPROVED,
                reason=approval.decision_reason,
            )

        try:
            await asyncio.wait_for(event.wait(), timeout=timeout_seconds)
        except TimeoutError:
            approval = self._repository.resolve_approval_request(
                actor=None,
                request_id=request_id,
                status=AssistantApprovalStatus.EXPIRED,
                reason="approval_timeout",
            )
        else:
            approval = self._repository.get_approval_for_system(request_id)
        finally:
            async with self._lock:
                self._events.pop(request_id, None)

        return ApprovalDecision(
            request_id=_as_uuid(request_id),
            granted=approval.status is AssistantApprovalStatus.APPROVED,
            reason=approval.decision_reason,
        )

    async def record_decision(
        self,
        *,
        actor: Actor,
        request_id: str,
        granted: bool,
        reason: str | None,
    ) -> AssistantApprovalView:
        approval = self._repository.resolve_approval_request(
            actor=actor,
            request_id=request_id,
            status=(
                AssistantApprovalStatus.APPROVED
                if granted
                else AssistantApprovalStatus.DENIED
            ),
            reason=reason,
        )
        async with self._lock:
            event = self._events.get(request_id)
            if event is not None:
                event.set()
        return approval


def _as_uuid(value: str):
    from uuid import UUID

    return UUID(hex=value)
