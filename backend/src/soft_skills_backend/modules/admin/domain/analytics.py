"""Pure admin analytics aggregation helpers."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, TypedDict


class UsageTrendBucket(TypedDict):
    bucket_date: str
    sessions_started: int
    attempts_submitted: int
    assessments_validated: int
    assessments_rejected: int


def build_usage_trend_points(
    *,
    session_timestamps: list[datetime],
    submitted_attempt_timestamps: list[datetime],
    validated_assessment_timestamps: list[datetime],
    rejected_assessment_timestamps: list[datetime],
) -> list[UsageTrendBucket]:
    """Build ordered daily usage trend points."""

    buckets: dict[str, UsageTrendBucket] = {}

    def ensure_bucket(bucket_date: str) -> UsageTrendBucket:
        return buckets.setdefault(
            bucket_date,
            UsageTrendBucket(
                bucket_date=bucket_date,
                sessions_started=0,
                attempts_submitted=0,
                assessments_validated=0,
                assessments_rejected=0,
            ),
        )

    for timestamp in session_timestamps:
        ensure_bucket(timestamp.date().isoformat())["sessions_started"] += 1
    for timestamp in submitted_attempt_timestamps:
        ensure_bucket(timestamp.date().isoformat())["attempts_submitted"] += 1
    for timestamp in validated_assessment_timestamps:
        ensure_bucket(timestamp.date().isoformat())["assessments_validated"] += 1
    for timestamp in rejected_assessment_timestamps:
        ensure_bucket(timestamp.date().isoformat())["assessments_rejected"] += 1

    return [buckets[key] for key in sorted(buckets.keys())]


def build_provider_summary(provider_calls: list[Any]) -> list[dict[str, int | float | str | None]]:
    """Aggregate provider calls by provider and model slug."""

    grouped: dict[tuple[str, str | None], dict[str, Any]] = {}
    for call in provider_calls:
        key = (call.provider, call.model_id)
        summary = grouped.setdefault(
            key,
            {
                "provider": call.provider,
                "model_slug": call.model_id,
                "call_count": 0,
                "success_count": 0,
                "failure_count": 0,
                "latencies": [],
            },
        )
        summary["call_count"] += 1
        if call.success:
            summary["success_count"] += 1
        else:
            summary["failure_count"] += 1
        if call.latency_ms is not None:
            summary["latencies"].append(call.latency_ms)

    ordered: list[dict[str, int | float | str | None]] = []
    for key in sorted(grouped.keys()):
        summary = grouped[key]
        latencies = summary.pop("latencies")
        summary["avg_latency_ms"] = (
            None if not latencies else round(sum(latencies) / len(latencies), 2)
        )
        ordered.append(summary)
    return ordered


def build_skill_clusters(weak_skill_lists: list[list[str]]) -> list[dict[str, int | str]]:
    """Aggregate weak-skill counts across learners."""

    counts = Counter(skill for items in weak_skill_lists for skill in items)
    return [
        {"skill_slug": skill_slug, "learner_count": learner_count}
        for skill_slug, learner_count in sorted(
            counts.items(), key=lambda item: (-item[1], item[0])
        )
    ]


def build_average_skill_scores(
    snapshot_payloads: list[dict[str, Any]],
) -> list[dict[str, int | float | str]]:
    """Average latest snapshot skill scores across learners."""

    scores_by_skill: dict[str, list[float]] = defaultdict(list)
    for payload in snapshot_payloads:
        for state in payload.get("skill_states", []):
            scores_by_skill[str(state["skill_slug"])].append(float(state["score"]))
    return [
        {
            "skill_slug": skill_slug,
            "avg_score": round(sum(scores) / len(scores), 2),
            "learner_count": len(scores),
        }
        for skill_slug, scores in sorted(scores_by_skill.items())
    ]
