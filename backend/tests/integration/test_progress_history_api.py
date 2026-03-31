"""Integration tests for progress history API endpoints."""

from __future__ import annotations

from pathlib import Path

import pytest
from alembic.config import Config
from alembic import command

from soft_skills_backend.platform.db.models import ProgressionSnapshotRecord


def _migrate(test_settings) -> None:
    alembic_config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    alembic_config.set_main_option("sqlalchemy.url", test_settings.database_url)
    command.upgrade(alembic_config, "heads")


async def _register_user(client, *, email: str, display_name: str):
    response = await client.post(
        "/api/auth/register",
        json={
            "email": email,
            "display_name": display_name,
            "target_role": "Consultant",
            "goals": ["Improve stakeholder handling"],
            "practice_preferences": {"session_length": "short"},
        },
    )
    assert response.status_code == 200
    return response.json()["data"]


async def _seed_multiple_assessments(client, app, learner_id: str, prompt_id: str, count: int = 5):
    """Create multiple assessed attempts to generate history."""
    from tests.integration.test_progression_api import FakeSuccessMarker
    
    app.state.container.practice_service._assessment_marker = FakeSuccessMarker()
    
    for i in range(count):
        start_response = await client.post(
            "/api/attempts/interview/sessions",
            headers={"X-User-ID": learner_id},
            json={
                "prompt_item_id": prompt_id,
                "competency_context": f"Assessment {i+1} for history testing.",
                "interviewer_perspective": "Hiring manager.",
            },
        )
        assert start_response.status_code == 200
        attempt_id = start_response.json()["data"]["attempt_id"]
        
        submit_response = await client.post(
            f"/api/attempts/{attempt_id}/submit",
            headers={"X-User-ID": learner_id},
            json={
                "response_text": (
                    f"Response {i+1}: I aligned the team, made a decision with incomplete info, "
                    f"and justified it with clear reasoning based on risk assessment."
                )
            },
        )
        assert submit_response.status_code == 200


@pytest.mark.asyncio
async def test_progress_history_returns_snapshots_ordered_by_date(
    app, client, test_settings
) -> None:
    """Test that progress history returns snapshots in chronological order."""
    _migrate(test_settings)
    
    from tests.integration.test_progression_api import _seed_prompt
    
    admin, learner, prompt = await _seed_prompt(client)
    
    # Create multiple assessments to generate history
    await _seed_multiple_assessments(client, app, str(learner["id"]), str(prompt["id"]), count=3)
    
    # Get progress history
    history_response = await client.get(
        "/api/progress/me/history",
        headers={"X-User-ID": str(learner["id"])},
    )
    assert history_response.status_code == 200
    
    payload = history_response.json()["data"]
    assert payload["learner_id"] == learner["id"]
    assert "snapshots" in payload
    assert len(payload["snapshots"]) >= 3
    
    # Verify snapshots are ordered by date (ascending)
    snapshots = payload["snapshots"]
    for i in range(1, len(snapshots)):
        prev_date = snapshots[i - 1]["recorded_at"]
        curr_date = snapshots[i]["recorded_at"]
        assert prev_date <= curr_date, "Snapshots should be ordered by recorded_at"
    
    # Verify each snapshot has required fields
    for snapshot in snapshots:
        assert "snapshot_id" in snapshot
        assert "recorded_at" in snapshot
        assert "source_assessment_id" in snapshot
        assert "skill_states" in snapshot
        assert "competency_states" in snapshot
        assert "weak_skill_slugs" in snapshot
        assert "stagnating_skill_slugs" in snapshot
        assert "coverage_gap_skill_slugs" in snapshot


@pytest.mark.asyncio
async def test_progress_history_with_date_filtering(app, client, test_settings) -> None:
    """Test date range filtering for progress history."""
    _migrate(test_settings)
    
    from tests.integration.test_progression_api import _seed_prompt
    from datetime import datetime, timedelta
    
    admin, learner, prompt = await _seed_prompt(client)
    
    # Create assessments
    await _seed_multiple_assessments(client, app, str(learner["id"]), str(prompt["id"]), count=3)
    
    # Calculate date range
    now = datetime.now()
    from_date = (now - timedelta(days=30)).isoformat()
    to_date = (now + timedelta(days=1)).isoformat()
    
    # Get filtered history
    history_response = await client.get(
        f"/api/progress/me/history?from_date={from_date}&to_date={to_date}&limit=10",
        headers={"X-User-ID": str(learner["id"])},
    )
    assert history_response.status_code == 200
    
    payload = history_response.json()["data"]
    assert payload["from_date"] == from_date
    assert payload["to_date"] == to_date
    assert len(payload["snapshots"]) <= 10


@pytest.mark.asyncio
async def test_skill_timeline_returns_time_series_data(app, client, test_settings) -> None:
    """Test skill timeline endpoint returns proper time-series data."""
    _migrate(test_settings)
    
    from tests.integration.test_progression_api import _seed_prompt
    
    admin, learner, prompt = await _seed_prompt(client)
    
    # Create multiple assessments
    await _seed_multiple_assessments(client, app, str(learner["id"]), str(prompt["id"]), count=5)
    
    # Get skill timeline for a specific skill
    skill_slug = "active-listening"
    timeline_response = await client.get(
        f"/api/progress/me/timeline/{skill_slug}",
        headers={"X-User-ID": str(learner["id"])},
    )
    assert timeline_response.status_code == 200
    
    payload = timeline_response.json()["data"]
    assert payload["skill_slug"] == skill_slug
    assert "skill_name" in payload
    assert "points" in payload
    assert len(payload["points"]) > 0
    
    # Verify trend calculation
    assert "trend" in payload
    assert payload["trend"] in ["improving", "declining", "stable"]
    assert "overall_change" in payload
    assert isinstance(payload["overall_change"], (int, float))
    
    # Verify each point has required fields
    for point in payload["points"]:
        assert "recorded_at" in point
        assert "score" in point
        assert "confidence" in point
        assert "evidence_count" in point
        assert "delta" in point
        assert "source_assessment_id" in point


@pytest.mark.asyncio
async def test_skill_timeline_with_date_range(app, client, test_settings) -> None:
    """Test skill timeline with date range filtering."""
    _migrate(test_settings)
    
    from tests.integration.test_progression_api import _seed_prompt
    from datetime import datetime, timedelta
    
    admin, learner, prompt = await _seed_prompt(client)
    
    await _seed_multiple_assessments(client, app, str(learner["id"]), str(prompt["id"]), count=3)
    
    now = datetime.now()
    from_date = (now - timedelta(days=30)).isoformat()
    to_date = (now + timedelta(days=1)).isoformat()
    
    skill_slug = "decision-justification"
    timeline_response = await client.get(
        f"/api/progress/me/timeline/{skill_slug}?from_date={from_date}&to_date={to_date}&limit=20",
        headers={"X-User-ID": str(learner["id"])},
    )
    assert timeline_response.status_code == 200
    
    payload = timeline_response.json()["data"]
    assert payload["from_date"] == from_date
    assert payload["to_date"] == to_date
    assert len(payload["points"]) <= 20


@pytest.mark.asyncio
async def test_skill_timeline_for_unknown_skill_returns_empty(app, client, test_settings) -> None:
    """Test that timeline for unknown skill returns empty points but valid structure."""
    _migrate(test_settings)
    
    from tests.integration.test_progression_api import _seed_prompt
    
    admin, learner, prompt = await _seed_prompt(client)
    
    # Get timeline for non-existent skill
    skill_slug = "non-existent-skill-xyz"
    timeline_response = await client.get(
        f"/api/progress/me/timeline/{skill_slug}",
        headers={"X-User-ID": str(learner["id"])},
    )
    assert timeline_response.status_code == 200
    
    payload = timeline_response.json()["data"]
    assert payload["skill_slug"] == skill_slug
    assert payload["skill_name"] == skill_slug  # Falls back to slug when not found
    assert payload["points"] == []
    assert payload["trend"] == "stable"
    assert payload["overall_change"] == 0.0


@pytest.mark.asyncio
async def test_progress_history_empty_for_new_learner(app, client, test_settings) -> None:
    """Test that new learner with no assessments gets empty history."""
    _migrate(test_settings)
    
    learner = await _register_user(
        client,
        email="new-learner-history@example.com",
        display_name="New Learner History",
    )
    
    history_response = await client.get(
        "/api/progress/me/history",
        headers={"X-User-ID": str(learner["id"])},
    )
    assert history_response.status_code == 200
    
    payload = history_response.json()["data"]
    assert payload["learner_id"] == learner["id"]
    assert payload["snapshots"] == []


@pytest.mark.asyncio
async def test_skill_states_in_history_have_required_fields(app, client, test_settings) -> None:
    """Verify skill states in history snapshots have all required fields."""
    _migrate(test_settings)
    
    from tests.integration.test_progression_api import _seed_prompt
    
    admin, learner, prompt = await _seed_prompt(client)
    await _seed_multiple_assessments(client, app, str(learner["id"]), str(prompt["id"]), count=2)
    
    history_response = await client.get(
        "/api/progress/me/history",
        headers={"X-User-ID": str(learner["id"])},
    )
    assert history_response.status_code == 200
    
    payload = history_response.json()["data"]
    
    for snapshot in payload["snapshots"]:
        for skill_state in snapshot["skill_states"]:
            assert "skill_slug" in skill_state
            assert "score" in skill_state
            assert "confidence" in skill_state
            assert "confidence_band" in skill_state
            assert skill_state["confidence_band"] in ["low", "medium", "high"]
            assert "evidence_count" in skill_state
            assert "delta" in skill_state
            assert "recorded_at" in skill_state


@pytest.mark.asyncio
async def test_competency_states_in_history_have_required_fields(app, client, test_settings) -> None:
    """Verify competency states in history snapshots have all required fields."""
    _migrate(test_settings)
    
    from tests.integration.test_progression_api import _seed_prompt
    
    admin, learner, prompt = await _seed_prompt(client)
    await _seed_multiple_assessments(client, app, str(learner["id"]), str(prompt["id"]), count=2)
    
    history_response = await client.get(
        "/api/progress/me/history",
        headers={"X-User-ID": str(learner["id"])},
    )
    assert history_response.status_code == 200
    
    payload = history_response.json()["data"]
    
    for snapshot in payload["snapshots"]:
        for competency_state in snapshot["competency_states"]:
            assert "competency_slug" in competency_state
            assert "score" in competency_state
            assert "confidence" in competency_state
            assert "confidence_band" in competency_state
            assert competency_state["confidence_band"] in ["low", "medium", "high"]
            assert "delta" in competency_state
            assert "recorded_at" in competency_state
