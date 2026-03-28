"""Admin analytics smoke result contracts."""

from __future__ import annotations

from pydantic import BaseModel


class AdminAnalyticsSmokeResult(BaseModel):
    """Result of the admin analytics smoke suite."""

    organisation_id: str
    admin_user_id: str
    member_user_id: str
    overview_total_learners: int
    comparison_cohorts_count: int
    export_json_status: str
    export_csv_status: str
