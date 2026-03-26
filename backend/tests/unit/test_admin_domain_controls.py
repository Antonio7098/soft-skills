from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from soft_skills_backend.modules.admin.domain.analytics import (
    build_provider_summary,
    build_usage_trend_points,
)
from soft_skills_backend.modules.admin.domain.relationships import (
    validate_admin_relationship_target,
    validate_admin_relationship_type,
)
from soft_skills_backend.modules.admin.domain.verification import (
    validate_admin_verification_transition,
)


def test_admin_verification_requires_public_collection_and_rejection_note() -> None:
    with pytest.raises(Exception) as private_exc:
        validate_admin_verification_transition(
            lifecycle_state="draft",
            current_state="unverified",
            next_state="verified",
            note=None,
            collection_id="collection-1",
        )
    assert "SS-DOMAIN-029" in str(private_exc.value)

    with pytest.raises(Exception) as note_exc:
        validate_admin_verification_transition(
            lifecycle_state="published_public",
            current_state="unverified",
            next_state="rejected",
            note=None,
            collection_id="collection-1",
        )
    assert "SS-VALIDATION-050" in str(note_exc.value)


def test_admin_analytics_helpers_aggregate_trends_and_provider_calls() -> None:
    now = datetime(2026, 3, 26, 10, 0, tzinfo=UTC)
    trend = build_usage_trend_points(
        session_timestamps=[now],
        submitted_attempt_timestamps=[now, now],
        validated_assessment_timestamps=[now],
        rejected_assessment_timestamps=[],
    )
    assert trend == [
        {
            "bucket_date": "2026-03-26",
            "sessions_started": 1,
            "attempts_submitted": 2,
            "assessments_validated": 1,
            "assessments_rejected": 0,
        }
    ]

    provider_summary = build_provider_summary(
        [
            SimpleNamespace(
                provider="openai",
                model_id="gpt-4.1-mini",
                success=True,
                latency_ms=120,
            ),
            SimpleNamespace(
                provider="openai",
                model_id="gpt-4.1-mini",
                success=False,
                latency_ms=180,
            ),
        ]
    )
    assert provider_summary == [
        {
            "provider": "openai",
            "model_slug": "gpt-4.1-mini",
            "call_count": 2,
            "success_count": 1,
            "failure_count": 1,
            "avg_latency_ms": 150.0,
        }
    ]


def test_admin_relationship_rules_are_explicit() -> None:
    validate_admin_relationship_type("manager")

    with pytest.raises(Exception) as type_exc:
        validate_admin_relationship_type("friend")
    assert "SS-VALIDATION-051" in str(type_exc.value)

    with pytest.raises(Exception) as target_exc:
        validate_admin_relationship_target(
            learner_user_id="same-user",
            admin_user_id="same-user",
        )
    assert "SS-DOMAIN-031" in str(target_exc.value)
