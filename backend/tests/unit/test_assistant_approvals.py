from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from soft_skills_backend.modules.assistant.domain.models import (
    AssistantApprovalStatus,
    AssistantSessionStatus,
    AssistantToolCallStatus,
    AssistantTurnStatus,
)
from soft_skills_backend.modules.assistant.infra.repository import AssistantRepository
from soft_skills_backend.modules.assistant.workflows.approval_service import (
    AssistantApprovalService,
)
from soft_skills_backend.platform.db.base import Base
from soft_skills_backend.platform.db.models import (
    AssistantSessionRecord,
    AssistantToolCallRecord,
    AssistantTurnRecord,
    UserAccountRecord,
)
from soft_skills_backend.platform.db.repositories import SqlAlchemyWorkflowEventRepository
from soft_skills_backend.shared.auth import Actor


@pytest.fixture()
def approval_harness(tmp_path):
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'assistant-approvals.db'}")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    workflow_events = SqlAlchemyWorkflowEventRepository(session_factory)
    repository = AssistantRepository(
        session_factory=session_factory,
        workflow_events=workflow_events,
    )
    actor = Actor(
        user_id="11111111111111111111111111111111",
        email="approvals@example.com",
    )
    now = datetime.now(UTC)
    with session_factory() as session:
        session.add(
            UserAccountRecord(
                id=actor.user_id,
                email=actor.email,
                display_name="Approvals User",
                auth_provider="header",
                auth_subject=actor.user_id,
                is_active=True,
                created_at=now,
            )
        )
        session.add(
            AssistantSessionRecord(
                id="22222222222222222222222222222222",
                user_id=actor.user_id,
                title="Approval Session",
                status=AssistantSessionStatus.ACTIVE.value,
                metadata_payload={},
                created_at=now,
                updated_at=now,
            )
        )
        session.add(
            AssistantTurnRecord(
                id="33333333333333333333333333333333",
                session_id="22222222222222222222222222222222",
                user_id=actor.user_id,
                request_id="req-1",
                trace_id="trace-1",
                workflow_id="workflow-1",
                pipeline_run_id=None,
                status=AssistantTurnStatus.RUNNING.value,
                stream_token="stream-token",
                user_message_id=None,
                assistant_message_id=None,
                last_error_code=None,
                cancel_reason=None,
                tool_call_count=1,
                metadata_payload={},
                created_at=now,
                started_at=now,
                completed_at=None,
                cancelled_at=None,
            )
        )
        session.add(
            AssistantToolCallRecord(
                id="44444444444444444444444444444444",
                session_id="22222222222222222222222222222222",
                turn_id="33333333333333333333333333333333",
                user_id=actor.user_id,
                tool_name="generate_collection",
                status=AssistantToolCallStatus.PENDING_APPROVAL.value,
                args_payload={"title": "Approval Draft"},
                result_payload=None,
                error_code=None,
                error_message=None,
                child_run_id=None,
                started_at=now,
                completed_at=None,
            )
        )
        session.commit()
    return actor, repository, AssistantApprovalService(repository=repository)


@pytest.mark.asyncio
async def test_approval_service_resolves_waiting_request(approval_harness) -> None:
    actor, repository, approvals = approval_harness
    request = await approvals.request_tool_approval(
        tool_call_id="44444444444444444444444444444444",
        approval_message="Approve generate_collection?",
        payload_summary={"title": "Approval Draft"},
        timeout_seconds=1.0,
    )

    waiter = asyncio.create_task(
        approvals.await_decision(request_id=request.id, timeout_seconds=1.0)
    )
    await asyncio.sleep(0)
    resolved = await approvals.record_decision(
        actor=actor,
        request_id=request.id,
        granted=True,
        reason="looks good",
    )
    decision = await waiter

    assert decision.granted is True
    assert resolved.status is AssistantApprovalStatus.APPROVED
    persisted = repository.get_approval(actor, request.id)
    assert persisted.status is AssistantApprovalStatus.APPROVED
    assert persisted.decision_reason == "looks good"


@pytest.mark.asyncio
async def test_approval_service_expires_when_no_decision_arrives(approval_harness) -> None:
    actor, repository, approvals = approval_harness
    request = await approvals.request_tool_approval(
        tool_call_id="44444444444444444444444444444444",
        approval_message="Approve generate_collection?",
        payload_summary={"title": "Approval Draft"},
        timeout_seconds=0.01,
    )

    decision = await approvals.await_decision(
        request_id=request.id,
        timeout_seconds=0.01,
    )

    assert decision.granted is False
    persisted = repository.get_approval(actor, request.id)
    assert persisted.status is AssistantApprovalStatus.EXPIRED
    assert persisted.decision_reason == "approval_timeout"
