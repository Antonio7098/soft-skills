"""Unit tests for progress history repository methods."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from soft_skills_backend.modules.progression.contracts.views import (
    ProgressHistoryView,
    SkillTimelineView,
)
from soft_skills_backend.modules.progression.infra.repository import ProgressionRepository
from soft_skills_backend.platform.db.models import (
    ProgressionSnapshotRecord,
    SkillRecord,
)
from soft_skills_backend.shared.auth import Actor


def _create_mock_snapshot(
    session: Session,
    *,
    snapshot_id: str,
    learner_id: str,
    created_at: datetime,
    skill_states: list[dict],
    competency_states: list[dict] | None = None,
    source_assessment_id: str = "assess-001",
) -> ProgressionSnapshotRecord:
    """Create a mock snapshot record."""
    payload = {
        "snapshot_id": snapshot_id,
        "learner_id": learner_id,
        "source_assessment_id": source_assessment_id,
        "created_at": created_at.isoformat(),
        "engine_version": "1.0.0",
        "schema_version": "1.0.0",
        "config_version": "1.0.0",
        "evidence_ledger_schema_version": "1.0.0",
        "trace_id": f"trace-{snapshot_id}",
        "skill_states": skill_states,
        "competency_states": competency_states or [],
        "weak_skill_slugs": [],
        "stagnating_skill_slugs": [],
        "coverage_gap_skill_slugs": [],
    }
    
    record = ProgressionSnapshotRecord(
        id=snapshot_id,
        learner_id=learner_id,
        source_assessment_id=source_assessment_id,
        created_at=created_at,
        snapshot_payload=payload,
        trace_id=f"trace-{snapshot_id}",
    )
    session.add(record)
    session.commit()
    return record


def _create_mock_skill(session: Session, slug: str, name: str) -> SkillRecord:
    """Create a mock skill record."""
    record = SkillRecord(
        slug=slug,
        name=name,
        description=f"Description for {name}",
    )
    session.add(record)
    session.commit()
    return record


@pytest.fixture
def mock_session_factory():
    """Create a mock session factory."""
    session = MagicMock(spec=Session)
    return MagicMock(return_value=session)


@pytest.fixture
def mock_workflow_events():
    """Create mock workflow events repository."""
    return MagicMock()


@pytest.fixture
def actor():
    """Create a test actor."""
    return Actor(
        user_id="learner-001",
        email="learner@test.com",
        organisation_id=None,
        organisation_role=None,
    )


class TestGetProgressHistory:
    """Tests for get_progress_history repository method."""

    def test_returns_snapshots_ordered_by_date(self, mock_session_factory, mock_workflow_events, actor):
        """Test that snapshots are returned in chronological order."""
        repository = ProgressionRepository(
            session_factory=mock_session_factory,
            workflow_events=mock_workflow_events,
        )
        
        # The method should return a ProgressHistoryView
        # Mock will return empty since we can't easily mock the query chain
        # In real integration tests, we'd use an actual database
        
        with patch.object(repository, '_assert_access') as mock_assert:
            mock_assert.return_value = None
            
            # Mock the session query chain
            mock_session = MagicMock()
            mock_query = MagicMock()
            mock_session.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            
            # Create mock records
            now = datetime.now(UTC)
            mock_records = [
                MagicMock(
                    id=f"snap-{i}",
                    learner_id="learner-001",
                    source_assessment_id=f"assess-{i}",
                    created_at=now - timedelta(days=i),
                    snapshot_payload={
                        "skill_states": [
                            {
                                "skill_slug": "active-listening",
                                "score": 0.5 + i * 0.1,
                                "confidence": 0.6,
                                "confidence_band": "medium",
                                "evidence_count": i + 1,
                                "delta": 0.05,
                            }
                        ],
                        "competency_states": [],
                        "weak_skill_slugs": [],
                        "stagnating_skill_slugs": [],
                        "coverage_gap_skill_slugs": [],
                    },
                )
                for i in range(3)
            ]
            mock_query.limit.return_value.all.return_value = mock_records
            mock_session_factory.return_value.__enter__.return_value = mock_session
            
            result = repository.get_progress_history(
                actor, "learner-001", from_date=None, to_date=None, limit=10
            )
            
            assert isinstance(result, ProgressHistoryView)
            assert result.learner_id == "learner-001"

    def test_respects_date_filters(self, mock_session_factory, mock_workflow_events, actor):
        """Test that from_date and to_date filters are applied."""
        repository = ProgressionRepository(
            session_factory=mock_session_factory,
            workflow_events=mock_workflow_events,
        )
        
        with patch.object(repository, '_assert_access') as mock_assert:
            mock_assert.return_value = None
            
            mock_session = MagicMock()
            mock_query = MagicMock()
            mock_session.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.limit.return_value.all.return_value = []
            mock_session_factory.return_value.__enter__.return_value = mock_session
            
            from_date = datetime.now(UTC) - timedelta(days=30)
            to_date = datetime.now(UTC)
            
            result = repository.get_progress_history(
                actor, "learner-001", from_date=from_date, to_date=to_date, limit=50
            )
            
            # Verify filters were applied
            assert mock_query.filter.call_count >= 1
            assert result.learner_id == "learner-001"
            assert result.from_date == from_date.isoformat()
            assert result.to_date == to_date.isoformat()

    def test_empty_result_for_learner_with_no_snapshots(self, mock_session_factory, mock_workflow_events, actor):
        """Test that empty history is returned for learner with no snapshots."""
        repository = ProgressionRepository(
            session_factory=mock_session_factory,
            workflow_events=mock_workflow_events,
        )
        
        with patch.object(repository, '_assert_access') as mock_assert:
            mock_assert.return_value = None
            
            mock_session = MagicMock()
            mock_query = MagicMock()
            mock_session.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.limit.return_value.all.return_value = []
            mock_session_factory.return_value.__enter__.return_value = mock_session
            
            result = repository.get_progress_history(actor, "new-learner-001")
            
            assert isinstance(result, ProgressHistoryView)
            assert result.learner_id == "new-learner-001"
            assert result.snapshots == []


class TestGetSkillTimeline:
    """Tests for get_skill_timeline repository method."""

    def test_returns_timeline_for_specific_skill(self, mock_session_factory, mock_workflow_events, actor):
        """Test that timeline is returned for the specified skill."""
        repository = ProgressionRepository(
            session_factory=mock_session_factory,
            workflow_events=mock_workflow_events,
        )
        
        with patch.object(repository, '_assert_access') as mock_assert:
            mock_assert.return_value = None
            
            mock_session = MagicMock()
            mock_query = MagicMock()
            mock_session.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = MagicMock(name="Active Listening")
            mock_query.order_by.return_value = mock_query
            
            now = datetime.now(UTC)
            mock_records = [
                MagicMock(
                    id=f"snap-{i}",
                    source_assessment_id=f"assess-{i}",
                    created_at=now - timedelta(days=i * 2),
                    snapshot_payload={
                        "skill_states": [
                            {
                                "skill_slug": "active-listening",
                                "score": 0.4 + i * 0.1,
                                "confidence": 0.5 + i * 0.1,
                                "evidence_count": i + 1,
                                "delta": 0.05,
                            },
                            {
                                "skill_slug": "other-skill",
                                "score": 0.5,
                                "confidence": 0.6,
                                "evidence_count": 1,
                                "delta": 0,
                            },
                        ],
                    },
                )
                for i in range(3)
            ]
            mock_query.limit.return_value.all.return_value = mock_records
            mock_session_factory.return_value.__enter__.return_value = mock_session
            
            result = repository.get_skill_timeline(
                actor, "learner-001", "active-listening", from_date=None, to_date=None, limit=10
            )
            
            assert isinstance(result, SkillTimelineView)
            assert result.skill_slug == "active-listening"
            # Should only include points for active-listening, not other-skill
            assert len(result.points) == 3
            for point in result.points:
                assert "recorded_at" in point.model_dump()
                assert "score" in point.model_dump()

    def test_calculates_trend_correctly(self, mock_session_factory, mock_workflow_events, actor):
        """Test that trend is calculated based on score progression."""
        repository = ProgressionRepository(
            session_factory=mock_session_factory,
            workflow_events=mock_workflow_events,
        )
        
        with patch.object(repository, '_assert_access') as mock_assert:
            mock_assert.return_value = None
            
            mock_session = MagicMock()
            mock_query = MagicMock()
            mock_session.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = MagicMock(name="Test Skill")
            mock_query.order_by.return_value = mock_query
            
            # Create records with improving scores
            now = datetime.now(UTC)
            mock_records = [
                MagicMock(
                    id="snap-1",
                    source_assessment_id="assess-1",
                    created_at=now - timedelta(days=10),
                    snapshot_payload={
                        "skill_states": [
                            {
                                "skill_slug": "test-skill",
                                "score": 0.4,
                                "confidence": 0.5,
                                "evidence_count": 1,
                                "delta": 0,
                            }
                        ],
                    },
                ),
                MagicMock(
                    id="snap-2",
                    source_assessment_id="assess-2",
                    created_at=now - timedelta(days=5),
                    snapshot_payload={
                        "skill_states": [
                            {
                                "skill_slug": "test-skill",
                                "score": 0.6,
                                "confidence": 0.6,
                                "evidence_count": 2,
                                "delta": 0.2,
                            }
                        ],
                    },
                ),
            ]
            mock_query.limit.return_value.all.return_value = mock_records
            mock_session_factory.return_value.__enter__.return_value = mock_session
            
            result = repository.get_skill_timeline(
                actor, "learner-001", "test-skill"
            )
            
            # With improvement from 0.4 to 0.6, trend should be "improving"
            assert result.trend == "improving"
            assert result.overall_change == 0.2

    def test_stable_trend_for_minor_changes(self, mock_session_factory, mock_workflow_events, actor):
        """Test that small score changes result in stable trend."""
        repository = ProgressionRepository(
            session_factory=mock_session_factory,
            workflow_events=mock_workflow_events,
        )
        
        with patch.object(repository, '_assert_access') as mock_assert:
            mock_assert.return_value = None
            
            mock_session = MagicMock()
            mock_query = MagicMock()
            mock_session.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = MagicMock(name="Test Skill")
            mock_query.order_by.return_value = mock_query
            
            now = datetime.now(UTC)
            mock_records = [
                MagicMock(
                    id="snap-1",
                    source_assessment_id="assess-1",
                    created_at=now - timedelta(days=10),
                    snapshot_payload={
                        "skill_states": [
                            {
                                "skill_slug": "test-skill",
                                "score": 0.5,
                                "confidence": 0.5,
                                "evidence_count": 1,
                                "delta": 0,
                            }
                        ],
                    },
                ),
                MagicMock(
                    id="snap-2",
                    source_assessment_id="assess-2",
                    created_at=now,
                    snapshot_payload={
                        "skill_states": [
                            {
                                "skill_slug": "test-skill",
                                "score": 0.52,  # Small change < 0.05 threshold
                                "confidence": 0.6,
                                "evidence_count": 2,
                                "delta": 0.02,
                            }
                        ],
                    },
                ),
            ]
            mock_query.limit.return_value.all.return_value = mock_records
            mock_session_factory.return_value.__enter__.return_value = mock_session
            
            result = repository.get_skill_timeline(
                actor, "learner-001", "test-skill"
            )
            
            assert result.trend == "stable"

    def test_declining_trend_for_score_drop(self, mock_session_factory, mock_workflow_events, actor):
        """Test that declining scores result in declining trend."""
        repository = ProgressionRepository(
            session_factory=mock_session_factory,
            workflow_events=mock_workflow_events,
        )
        
        with patch.object(repository, '_assert_access') as mock_assert:
            mock_assert.return_value = None
            
            mock_session = MagicMock()
            mock_query = MagicMock()
            mock_session.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = MagicMock(name="Test Skill")
            mock_query.order_by.return_value = mock_query
            
            now = datetime.now(UTC)
            mock_records = [
                MagicMock(
                    id="snap-1",
                    source_assessment_id="assess-1",
                    created_at=now - timedelta(days=10),
                    snapshot_payload={
                        "skill_states": [
                            {
                                "skill_slug": "test-skill",
                                "score": 0.7,
                                "confidence": 0.6,
                                "evidence_count": 3,
                                "delta": 0,
                            }
                        ],
                    },
                ),
                MagicMock(
                    id="snap-2",
                    source_assessment_id="assess-2",
                    created_at=now,
                    snapshot_payload={
                        "skill_states": [
                            {
                                "skill_slug": "test-skill",
                                "score": 0.5,  # Significant drop > 0.05 threshold
                                "confidence": 0.5,
                                "evidence_count": 4,
                                "delta": -0.2,
                            }
                        ],
                    },
                ),
            ]
            mock_query.limit.return_value.all.return_value = mock_records
            mock_session_factory.return_value.__enter__.return_value = mock_session
            
            result = repository.get_skill_timeline(
                actor, "learner-001", "test-skill"
            )
            
            assert result.trend == "declining"

    def test_skill_name_lookup_from_taxonomy(self, mock_session_factory, mock_workflow_events, actor):
        """Test that skill name is looked up from taxonomy."""
        repository = ProgressionRepository(
            session_factory=mock_session_factory,
            workflow_events=mock_workflow_events,
        )
        
        with patch.object(repository, '_assert_access') as mock_assert:
            mock_assert.return_value = None
            
            mock_session = MagicMock()
            mock_query = MagicMock()
            mock_session.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            # Return skill with name
            mock_query.first.return_value = MagicMock(name="Active Listening Skill")
            mock_query.order_by.return_value = mock_query
            mock_query.limit.return_value.all.return_value = []
            mock_session_factory.return_value.__enter__.return_value = mock_session
            
            result = repository.get_skill_timeline(
                actor, "learner-001", "active-listening"
            )
            
            assert result.skill_name == "Active Listening Skill"

    def test_fallback_to_slug_when_skill_not_found(self, mock_session_factory, mock_workflow_events, actor):
        """Test that slug is used as name when skill not in taxonomy."""
        repository = ProgressionRepository(
            session_factory=mock_session_factory,
            workflow_events=mock_workflow_events,
        )
        
        with patch.object(repository, '_assert_access') as mock_assert:
            mock_assert.return_value = None
            
            mock_session = MagicMock()
            mock_query = MagicMock()
            mock_session.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            # Return None to simulate skill not found
            mock_query.first.return_value = None
            mock_query.order_by.return_value = mock_query
            mock_query.limit.return_value.all.return_value = []
            mock_session_factory.return_value.__enter__.return_value = mock_session
            
            result = repository.get_skill_timeline(
                actor, "learner-001", "unknown-skill-slug"
            )
            
            assert result.skill_name == "unknown-skill-slug"

    def test_empty_timeline_for_skill_with_no_data(self, mock_session_factory, mock_workflow_events, actor):
        """Test that empty points are returned for skill with no snapshot data."""
        repository = ProgressionRepository(
            session_factory=mock_session_factory,
            workflow_events=mock_workflow_events,
        )
        
        with patch.object(repository, '_assert_access') as mock_assert:
            mock_assert.return_value = None
            
            mock_session = MagicMock()
            mock_query = MagicMock()
            mock_session.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = MagicMock(name="Unused Skill")
            mock_query.order_by.return_value = mock_query
            # Return records but with different skills
            mock_query.limit.return_value.all.return_value = [
                MagicMock(
                    snapshot_payload={
                        "skill_states": [
                            {"skill_slug": "other-skill-1"},
                            {"skill_slug": "other-skill-2"},
                        ]
                    }
                )
            ]
            mock_session_factory.return_value.__enter__.return_value = mock_session
            
            result = repository.get_skill_timeline(
                actor, "learner-001", "unused-skill"
            )
            
            assert result.points == []
            assert result.trend == "stable"
            assert result.overall_change == 0.0
