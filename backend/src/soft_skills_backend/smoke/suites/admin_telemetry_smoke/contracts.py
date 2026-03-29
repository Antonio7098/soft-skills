"""Admin telemetry smoke result contracts."""

from __future__ import annotations

from pydantic import BaseModel


class AdminTelemetrySmokeResult(BaseModel):
    """Result of the admin telemetry smoke suite."""

    organisation_id: str
    admin_user_id: str
    member_user_id: str
    overview_status: str
    traces_count: int
    trace_detail_status: str
