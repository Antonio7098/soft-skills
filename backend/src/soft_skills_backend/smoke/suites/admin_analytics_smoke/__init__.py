"""Admin analytics smoke suite."""

from __future__ import annotations

from .contracts import AdminAnalyticsSmokeResult
from .smoke import AdminAnalyticsSmoke

__all__ = ["AdminAnalyticsSmoke", "AdminAnalyticsSmokeResult"]
