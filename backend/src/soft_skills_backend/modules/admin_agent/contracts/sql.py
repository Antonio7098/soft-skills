"""Admin-agent structured SQL planning contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field

from soft_skills_backend.modules.admin_agent.contracts.commands import AdminAgentScalar


class AdminAgentPlan(BaseModel):
    intent_summary: str = Field(min_length=1, max_length=240)
    sql: str = Field(min_length=1, max_length=4000)
    params: dict[str, AdminAgentScalar] = Field(default_factory=dict)
