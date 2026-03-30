"""Tests for RubricAdminRepository with parent-child rubric versioning model."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.modules.admin.contracts.commands import (
    CreateRubricCommand,
    CreateRubricVersionCommand,
    RubricCriterionCommand,
    RubricCriterionLevelCommand,
    RubricCriterionUpdateCommand,
    UpdateRubricCommand,
)
from soft_skills_backend.modules.admin.infra.rubric_admin_repository import RubricAdminRepository
from soft_skills_backend.platform.db.models import Base, RubricRecord, RubricVersionRecord


@pytest.fixture
def session_factory():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal


@pytest.fixture
def repo(session_factory):
    return RubricAdminRepository(session_factory)


@pytest.fixture
def session(session_factory):
    return session_factory()


def _make_criterion_command(
    criterion_ref: str = "active-listening",
    skill_slug: str = "active-listening",
    title: str = "Active Listening",
    description: str = "Demonstrates active listening",
    weight: float = 1.0,
    required: bool = True,
    position: int = 0,
    levels: list[RubricCriterionLevelCommand] | None = None,
) -> RubricCriterionCommand:
    if levels is None:
        levels = [
            RubricCriterionLevelCommand(level=1, description="Poor", examples=["Example 1"]),
            RubricCriterionLevelCommand(level=2, description="Fair", examples=["Example 2"]),
            RubricCriterionLevelCommand(level=3, description="Good", examples=["Example 3"]),
            RubricCriterionLevelCommand(level=4, description="Excellent", examples=["Example 4"]),
        ]
    return RubricCriterionCommand(
        criterion_ref=criterion_ref,
        skill_slug=skill_slug,
        title=title,
        description=description,
        weight=weight,
        required=required,
        position=position,
        levels=levels,
    )


def _make_rubric_command(
    rubric_id: str = "test-rubric@v1",
    skill_slug: str = "active-listening",
    name: str = "Test Rubric",
    content_type: str = "quick_practice_prompt",
    criteria: list[RubricCriterionCommand] | None = None,
    organisation_id: str | None = None,
) -> CreateRubricCommand:
    if criteria is None:
        criteria = [_make_criterion_command()]
    return CreateRubricCommand(
        rubric_id=rubric_id,
        skill_slug=skill_slug,
        name=name,
        content_type=content_type,
        schema_version="v1",
        version="v1",
        criteria=criteria,
        organisation_id=organisation_id,
    )


class TestRubricAdminRepositoryCreate:
    def test_create_rubric_creates_parent_and_version(
        self, repo: RubricAdminRepository, session: Session
    ) -> None:
        command = _make_rubric_command()
        view = repo.create_rubric(command)

        assert view.rubric_id == "test-rubric@v1"
        assert view.skill_slug == "active-listening"
        assert view.name == "Test Rubric"
        assert len(view.versions) == 1
        assert view.versions[0].version == "v1"
        assert view.versions[0].status == "draft"
        assert len(view.versions[0].criteria) == 1

        rubric = session.get(RubricRecord, "test-rubric@v1")
        assert rubric is not None
        assert rubric.name == "Test Rubric"

        version = (
            session.query(RubricVersionRecord)
            .filter(RubricVersionRecord.rubric_id == "test-rubric@v1")
            .first()
        )
        assert version is not None
        assert version.version == "v1"
        assert version.status == "draft"
        assert len(version.criteria) == 1

    def test_create_rubric_with_multiple_criteria(self, repo: RubricAdminRepository) -> None:
        criteria = [
            _make_criterion_command("active-listening", "active-listening", "Active Listening"),
            _make_criterion_command("empathy", "empathy", "Empathy"),
        ]
        command = _make_rubric_command(criteria=criteria)
        view = repo.create_rubric(command)

        assert len(view.versions[0].criteria) == 2
        criterion_refs = {c.criterion_ref for c in view.versions[0].criteria}
        assert "active-listening" in criterion_refs
        assert "empathy" in criterion_refs

    def test_create_rubric_duplicate_id_raises(self, repo: RubricAdminRepository) -> None:
        command = _make_rubric_command()
        repo.create_rubric(command)

        with pytest.raises(Exception) as exc_info:
            repo.create_rubric(command)
        assert "SS-ADMIN-002" in str(exc_info.value)


class TestRubricAdminRepositoryGet:
    def test_get_rubric_returns_with_versions(self, repo: RubricAdminRepository) -> None:
        command = _make_rubric_command()
        repo.create_rubric(command)

        view = repo.get_rubric("test-rubric@v1")

        assert view.rubric_id == "test-rubric@v1"
        assert len(view.versions) == 1

    def test_get_rubric_not_found_raises(self, repo: RubricAdminRepository) -> None:
        with pytest.raises(Exception) as exc_info:
            repo.get_rubric("non-existent")
        assert "SS-ADMIN-001" in str(exc_info.value)


class TestRubricAdminRepositoryList:
    def test_list_rubrics_returns_all(self, repo: RubricAdminRepository) -> None:
        repo.create_rubric(_make_rubric_command("rubric-1@v1", name="Rubric 1"))
        repo.create_rubric(_make_rubric_command("rubric-2@v1", name="Rubric 2"))

        views = repo.list_rubrics()

        assert len(views) == 2
        names = {v.name for v in views}
        assert "Rubric 1" in names
        assert "Rubric 2" in names


class TestRubricAdminRepositoryUpdate:
    def test_update_rubric_metadata(self, repo: RubricAdminRepository) -> None:
        repo.create_rubric(_make_rubric_command())
        command = UpdateRubricCommand(name="Updated Name", description="New description")

        view = repo.update_rubric("test-rubric@v1", command)

        assert view.name == "Updated Name"
        assert view.description == "New description"


class TestRubricAdminRepositoryVersion:
    def test_create_version_creates_new_version(self, repo: RubricAdminRepository) -> None:
        repo.create_rubric(_make_rubric_command())
        command = CreateRubricVersionCommand(
            version="v2",
            criteria=[_make_criterion_command("empathy", "empathy", "Empathy v2")],
        )

        view = repo.create_version("test-rubric@v1", command)

        assert len(view.versions) == 2
        versions = {v.version for v in view.versions}
        assert "v1" in versions
        assert "v2" in versions

    def test_create_version_duplicate_raises(self, repo: RubricAdminRepository) -> None:
        repo.create_rubric(_make_rubric_command())
        command = CreateRubricVersionCommand(version="v1", criteria=[_make_criterion_command()])

        with pytest.raises(Exception) as exc_info:
            repo.create_version("test-rubric@v1", command)
        assert "SS-ADMIN-010" in str(exc_info.value)


class TestRubricAdminRepositoryCriterion:
    def test_add_criterion_to_version(self, repo: RubricAdminRepository) -> None:
        repo.create_rubric(_make_rubric_command())
        command = _make_criterion_command("empathy", "empathy", "Empathy")

        view = repo.add_criterion("test-rubric@v1", "v1", command)

        assert len(view.versions[0].criteria) == 2
        criterion_refs = {c.criterion_ref for c in view.versions[0].criteria}
        assert "empathy" in criterion_refs

    def test_add_criterion_duplicate_ref_raises(self, repo: RubricAdminRepository) -> None:
        repo.create_rubric(_make_rubric_command())
        command = _make_criterion_command(
            "active-listening", "active-listening", "Active Listening"
        )

        with pytest.raises(Exception) as exc_info:
            repo.add_criterion("test-rubric@v1", "v1", command)
        assert "SS-ADMIN-003" in str(exc_info.value)

    def test_update_criterion(self, repo: RubricAdminRepository) -> None:
        repo.create_rubric(_make_rubric_command())
        command = RubricCriterionUpdateCommand(
            criterion_ref="active-listening",
            title="Updated Title",
        )

        view = repo.update_criterion("test-rubric@v1", "v1", "active-listening", command)

        criterion = next(
            c for c in view.versions[0].criteria if c.criterion_ref == "active-listening"
        )
        assert criterion.title == "Updated Title"

    def test_delete_criterion(self, repo: RubricAdminRepository) -> None:
        criteria = [
            _make_criterion_command("active-listening", "active-listening", "Active Listening"),
            _make_criterion_command("empathy", "empathy", "Empathy"),
        ]
        repo.create_rubric(_make_rubric_command(criteria=criteria))

        view = repo.delete_criterion("test-rubric@v1", "v1", "active-listening")

        assert len(view.versions[0].criteria) == 1
        criterion_refs = {c.criterion_ref for c in view.versions[0].criteria}
        assert "active-listening" not in criterion_refs

    def test_delete_criterion_not_found_raises(self, repo: RubricAdminRepository) -> None:
        repo.create_rubric(_make_rubric_command())

        with pytest.raises(Exception) as exc_info:
            repo.delete_criterion("test-rubric@v1", "v1", "non-existent")
        assert "SS-ADMIN-004" in str(exc_info.value)

    def test_criterion_only_on_draft_version(self, repo: RubricAdminRepository) -> None:
        repo.create_rubric(_make_rubric_command())
        repo.publish_version("test-rubric@v1", "v1")
        command = _make_criterion_command("empathy", "empathy", "Empathy")

        with pytest.raises(Exception) as exc_info:
            repo.add_criterion("test-rubric@v1", "v1", command)
        assert "SS-ADMIN-012" in str(exc_info.value)


class TestRubricAdminRepositoryPublishArchive:
    def test_publish_version(self, repo: RubricAdminRepository) -> None:
        repo.create_rubric(_make_rubric_command())

        view = repo.publish_version("test-rubric@v1", "v1")

        assert view.versions[0].status == "published"

    def test_publish_already_published_raises(self, repo: RubricAdminRepository) -> None:
        repo.create_rubric(_make_rubric_command())
        repo.publish_version("test-rubric@v1", "v1")

        with pytest.raises(Exception) as exc_info:
            repo.publish_version("test-rubric@v1", "v1")
        assert "SS-ADMIN-013" in str(exc_info.value)

    def test_archive_version(self, repo: RubricAdminRepository) -> None:
        repo.create_rubric(_make_rubric_command())
        repo.publish_version("test-rubric@v1", "v1")

        view = repo.archive_version("test-rubric@v1", "v1")

        assert view.versions[0].status == "archived"

    def test_archive_draft_raises(self, repo: RubricAdminRepository) -> None:
        repo.create_rubric(_make_rubric_command())

        with pytest.raises(Exception) as exc_info:
            repo.archive_version("test-rubric@v1", "v1")
        assert "SS-ADMIN-014" in str(exc_info.value)


class TestRubricAdminRepositoryDelete:
    def test_delete_rubric_cascades_to_versions(
        self, repo: RubricAdminRepository, session: Session
    ) -> None:
        repo.create_rubric(_make_rubric_command())

        repo.delete_rubric("test-rubric@v1")

        rubric = session.get(RubricRecord, "test-rubric@v1")
        assert rubric is None
        versions = (
            session.query(RubricVersionRecord)
            .filter(RubricVersionRecord.rubric_id == "test-rubric@v1")
            .all()
        )
        assert len(versions) == 0

    def test_delete_rubric_not_found_raises(self, repo: RubricAdminRepository) -> None:
        with pytest.raises(Exception) as exc_info:
            repo.delete_rubric("non-existent")
        assert "SS-ADMIN-001" in str(exc_info.value)


class TestRubricAdminRepositoryEmbeddedCriteria:
    def test_criteria_embedded_in_version_json(
        self, repo: RubricAdminRepository, session: Session
    ) -> None:
        criteria = [
            _make_criterion_command("active-listening", "active-listening", "Active Listening"),
            _make_criterion_command("empathy", "empathy", "Empathy"),
        ]
        repo.create_rubric(_make_rubric_command(criteria=criteria))

        version = (
            session.query(RubricVersionRecord)
            .filter(RubricVersionRecord.rubric_id == "test-rubric@v1")
            .first()
        )

        assert isinstance(version.criteria, list)
        assert len(version.criteria) == 2
        assert version.criteria[0]["criterion_ref"] == "active-listening"
        assert "levels" in version.criteria[0]

    def test_levels_serialized_correctly(self, repo: RubricAdminRepository) -> None:
        levels = [
            RubricCriterionLevelCommand(level=1, description="Poor", examples=["Bad example"]),
            RubricCriterionLevelCommand(level=2, description="Good", examples=["Good example"]),
        ]
        criteria = [_make_criterion_command(levels=levels)]
        repo.create_rubric(_make_rubric_command(criteria=criteria))

        view = repo.get_rubric("test-rubric@v1")
        criterion = view.versions[0].criteria[0]

        assert len(criterion.levels) == 2
        assert criterion.levels[0].level == 1
        assert criterion.levels[0].description == "Poor"
        assert criterion.levels[0].examples == ["Bad example"]


class TestRubricAdminRepositoryOrgScoping:
    def test_create_org_scoped_rubric(self, repo: RubricAdminRepository) -> None:
        command = CreateRubricCommand(
            rubric_id="org-rubric@v1",
            skill_slug="active-listening",
            organisation_id="org-123",
            name="Org Rubric",
            content_type="quick_practice_prompt",
            schema_version="v1",
            version="v1",
            criteria=[_make_criterion_command()],
        )
        view = repo.create_rubric(command)

        assert view.rubric_id == "org-rubric@v1"
        assert view.organisation_id == "org-123"

    def test_list_rubrics_includes_org_scoped(self, repo: RubricAdminRepository) -> None:
        repo.create_rubric(_make_rubric_command("global-rubric@v1", organisation_id=None))
        org_command = CreateRubricCommand(
            rubric_id="org-rubric@v1",
            skill_slug="active-listening",
            organisation_id="org-123",
            name="Org Rubric",
            content_type="quick_practice_prompt",
            schema_version="v1",
            version="v1",
            criteria=[_make_criterion_command()],
        )
        repo.create_rubric(org_command)

        views = repo.list_rubrics()

        assert len(views) == 2
