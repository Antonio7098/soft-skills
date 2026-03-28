"""Tests for analytics domain aggregation logic."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from soft_skills_backend.modules.admin.domain.analytics import (
    build_average_skill_scores,
    build_provider_summary,
    build_skill_clusters,
    build_usage_trend_points,
)
from soft_skills_backend.modules.admin.contracts.views import (
    AnalyticsOverviewView,
    CohortAnalyticsView,
    CohortComparisonView,
    LearnerAnalyticsView,
    ProviderUsageView,
    SkillAverageView,
    SkillClusterView,
    UsageSummaryView,
    UsageTrendPointView,
)


class FakeProviderCall:
    def __init__(
        self,
        provider: str,
        model_id: str | None,
        success: bool,
        latency_ms: float | None = None,
    ) -> None:
        self.provider = provider
        self.model_id = model_id
        self.success = success
        self.latency_ms = latency_ms


class TestBuildUsageTrendPoints:
    def test_empty_inputs_returns_empty_list(self) -> None:
        result = build_usage_trend_points(
            session_timestamps=[],
            submitted_attempt_timestamps=[],
            validated_assessment_timestamps=[],
            rejected_assessment_timestamps=[],
        )
        assert result == []

    def test_single_session_bucket(self) -> None:
        now = datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC)
        result = build_usage_trend_points(
            session_timestamps=[now],
            submitted_attempt_timestamps=[],
            validated_assessment_timestamps=[],
            rejected_assessment_timestamps=[],
        )
        assert len(result) == 1
        assert result[0]["bucket_date"] == "2024-01-15"
        assert result[0]["sessions_started"] == 1
        assert result[0]["attempts_submitted"] == 0

    def test_multiple_events_in_same_bucket(self) -> None:
        day = datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC)
        result = build_usage_trend_points(
            session_timestamps=[day, day],
            submitted_attempt_timestamps=[day],
            validated_assessment_timestamps=[day],
            rejected_assessment_timestamps=[],
        )
        assert len(result) == 1
        assert result[0]["sessions_started"] == 2
        assert result[0]["attempts_submitted"] == 1
        assert result[0]["assessments_validated"] == 1

    def test_multiple_buckets_sorted_chronologically(self) -> None:
        day1 = datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC)
        day2 = datetime(2024, 1, 17, 10, 0, 0, tzinfo=UTC)
        result = build_usage_trend_points(
            session_timestamps=[day2, day1],
            submitted_attempt_timestamps=[],
            validated_assessment_timestamps=[],
            rejected_assessment_timestamps=[],
        )
        assert len(result) == 2
        assert result[0]["bucket_date"] == "2024-01-15"
        assert result[1]["bucket_date"] == "2024-01-17"


class TestBuildProviderSummary:
    def test_empty_input(self) -> None:
        result = build_provider_summary([])
        assert result == []

    def test_single_provider_call(self) -> None:
        call = FakeProviderCall(provider="openai", model_id="gpt-4", success=True, latency_ms=100.0)
        result = build_provider_summary([call])
        assert len(result) == 1
        assert result[0]["provider"] == "openai"
        assert result[0]["model_slug"] == "gpt-4"
        assert result[0]["call_count"] == 1
        assert result[0]["success_count"] == 1
        assert result[0]["failure_count"] == 0
        assert result[0]["avg_latency_ms"] == 100.0

    def test_multiple_calls_same_provider_model(self) -> None:
        calls = [
            FakeProviderCall(provider="openai", model_id="gpt-4", success=True, latency_ms=100.0),
            FakeProviderCall(provider="openai", model_id="gpt-4", success=False, latency_ms=200.0),
            FakeProviderCall(provider="openai", model_id="gpt-4", success=True, latency_ms=150.0),
        ]
        result = build_provider_summary(calls)
        assert len(result) == 1
        assert result[0]["call_count"] == 3
        assert result[0]["success_count"] == 2
        assert result[0]["failure_count"] == 1
        assert result[0]["avg_latency_ms"] == 150.0

    def test_multiple_providers_separated(self) -> None:
        calls = [
            FakeProviderCall(provider="openai", model_id="gpt-4", success=True, latency_ms=100.0),
            FakeProviderCall(
                provider="anthropic", model_id="claude-3", success=True, latency_ms=200.0
            ),
        ]
        result = build_provider_summary(calls)
        assert len(result) == 2
        assert result[0]["provider"] == "anthropic"
        assert result[1]["provider"] == "openai"

    def test_null_latency_not_included_in_average(self) -> None:
        calls = [
            FakeProviderCall(provider="openai", model_id="gpt-4", success=True, latency_ms=100.0),
            FakeProviderCall(provider="openai", model_id="gpt-4", success=True, latency_ms=None),
        ]
        result = build_provider_summary(calls)
        assert result[0]["avg_latency_ms"] == 100.0


class TestBuildSkillClusters:
    def test_empty_input(self) -> None:
        result = build_skill_clusters([])
        assert result == []

    def test_single_learner_weak_skills(self) -> None:
        result = build_skill_clusters([["active-listening", "expectation-setting"]])
        assert len(result) == 2
        skill_slugs = {r["skill_slug"] for r in result}
        assert skill_slugs == {"active-listening", "expectation-setting"}
        for r in result:
            assert r["learner_count"] == 1

    def test_multiple_learners_same_weak_skills(self) -> None:
        result = build_skill_clusters(
            [
                ["active-listening", "expectation-setting"],
                ["active-listening", "stakeholder-management"],
                ["active-listening"],
            ]
        )
        assert len(result) == 3
        active_listening = next(r for r in result if r["skill_slug"] == "active-listening")
        assert active_listening["learner_count"] == 3
        expectation = next(r for r in result if r["skill_slug"] == "expectation-setting")
        assert expectation["learner_count"] == 1

    def test_sorted_by_learner_count_desc(self) -> None:
        result = build_skill_clusters(
            [
                ["skill-a"],
                ["skill-a"],
                ["skill-a"],
                ["skill-b"],
                ["skill-b"],
                ["skill-c"],
            ]
        )
        counts = [r["learner_count"] for r in result]
        assert counts == [3, 2, 1]


class TestBuildAverageSkillScores:
    def test_empty_input(self) -> None:
        result = build_average_skill_scores([])
        assert result == []

    def test_single_learner_snapshot(self) -> None:
        payload = {
            "skill_states": [
                {"skill_slug": "active-listening", "score": 4},
                {"skill_slug": "expectation-setting", "score": 3},
            ]
        }
        result = build_average_skill_scores([payload])
        assert len(result) == 2
        active = next(r for r in result if r["skill_slug"] == "active-listening")
        assert active["avg_score"] == 4.0
        assert active["learner_count"] == 1

    def test_multiple_learners_average(self) -> None:
        payloads = [
            {"skill_states": [{"skill_slug": "active-listening", "score": 4}]},
            {"skill_states": [{"skill_slug": "active-listening", "score": 2}]},
            {"skill_states": [{"skill_slug": "active-listening", "score": 6}]},
        ]
        result = build_average_skill_scores(payloads)
        assert len(result) == 1
        assert result[0]["avg_score"] == 4.0
        assert result[0]["learner_count"] == 3

    def test_multiple_skills(self) -> None:
        payloads = [
            {
                "skill_states": [
                    {"skill_slug": "active-listening", "score": 4},
                    {"skill_slug": "expectation-setting", "score": 3},
                ]
            },
            {"skill_states": [{"skill_slug": "active-listening", "score": 2}]},
        ]
        result = build_average_skill_scores(payloads)
        assert len(result) == 2
        active = next(r for r in result if r["skill_slug"] == "active-listening")
        assert active["avg_score"] == 3.0
        assert active["learner_count"] == 2


class TestAnalyticsViewConstruction:
    def test_usage_summary_view_defaults(self) -> None:
        view = UsageSummaryView()
        assert view.total_sessions == 0
        assert view.total_attempts == 0
        assert view.avg_validated_score is None

    def test_usage_trend_point_view_defaults(self) -> None:
        view = UsageTrendPointView(bucket_date="2024-01-15")
        assert view.sessions_started == 0
        assert view.attempts_submitted == 0

    def test_cohort_analytics_view(self) -> None:
        usage = UsageSummaryView(total_sessions=10, total_attempts=5)
        view = CohortAnalyticsView(
            cohort_key="Consultant",
            learner_count=3,
            usage=usage,
        )
        assert view.cohort_key == "Consultant"
        assert view.learner_count == 3
        assert view.usage.total_sessions == 10

    def test_learner_analytics_view(self) -> None:
        usage = UsageSummaryView(total_sessions=10)
        view = LearnerAnalyticsView(
            learner_id="learner-1",
            usage=usage,
        )
        assert view.learner_id == "learner-1"

    def test_skill_cluster_view(self) -> None:
        view = SkillClusterView(skill_slug="active-listening", learner_count=5)
        assert view.skill_slug == "active-listening"
        assert view.learner_count == 5

    def test_skill_average_view(self) -> None:
        view = SkillAverageView(skill_slug="active-listening", avg_score=3.5, learner_count=10)
        assert view.avg_score == 3.5

    def test_provider_usage_view(self) -> None:
        view = ProviderUsageView(provider="openai", model_slug="gpt-4", call_count=100)
        assert view.call_count == 100
        assert view.avg_latency_ms is None

    def test_analytics_overview_view_defaults(self) -> None:
        view = AnalyticsOverviewView()
        assert view.total_learners == 0
        assert view.active_learners_30d == 0
        assert view.top_weak_skills == []
        assert view.cohort_breakdown == []

    def test_cohort_comparison_view(self) -> None:
        usage = UsageSummaryView(total_sessions=5)
        cohort = CohortAnalyticsView(cohort_key="Consultant", learner_count=2, usage=usage)
        view = CohortComparisonView(cohorts=[cohort], comparison_timestamp="2024-01-15T10:00:00Z")
        assert len(view.cohorts) == 1
        assert view.comparison_timestamp == "2024-01-15T10:00:00Z"
