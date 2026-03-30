"""Admin rubric repository for CRUD operations on marking scheme rubrics."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.modules.admin.contracts.commands import (
    CreateRubricCommand,
    CreateRubricCriterionCommand,
    CreateRubricVersionCommand,
    RubricCriterionCommand,
    RubricCriterionLevelCommand,
    RubricCriterionUpdateCommand,
    UpdateRubricCommand,
)
from soft_skills_backend.modules.admin.contracts.views import (
    RubricCriterionLevelView,
    RubricCriterionView,
    RubricVersionView,
    RubricView,
)
from soft_skills_backend.platform.db.models import RubricRecord, RubricVersionRecord
from soft_skills_backend.shared.errors import domain_error


class RubricAdminRepository:
    """Repository for admin CRUD operations on rubrics using parent-child model."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def list_rubrics(self) -> list[RubricView]:
        with self._session_factory() as session:
            rubrics = session.query(RubricRecord).order_by(RubricRecord.name).all()
            return [self._build_rubric_view(session, r) for r in rubrics]

    def get_rubric(self, rubric_id: str) -> RubricView:
        with self._session_factory() as session:
            rubric = session.get(RubricRecord, rubric_id)
            if rubric is None:
                raise domain_error(
                    "Rubric was not found",
                    code="SS-ADMIN-001",
                    status_code=404,
                    details={"rubric_id": rubric_id},
                )
            return self._build_rubric_view(session, rubric)

    def create_rubric(self, command: CreateRubricCommand) -> RubricView:
        with self._session_factory() as session:
            existing = session.get(RubricRecord, command.rubric_id)
            if existing is not None:
                raise domain_error(
                    "Rubric already exists",
                    code="SS-ADMIN-002",
                    details={"rubric_id": command.rubric_id},
                )

            rubric_record = RubricRecord(
                id=command.rubric_id,
                skill_slug=command.skill_slug,
                organisation_id=command.organisation_id,
                name=command.name,
                description=command.description,
                content_type=command.content_type,
                schema_version=command.schema_version,
            )
            session.add(rubric_record)

            criteria_data = self._build_criteria_json(command.criteria)
            version_record = RubricVersionRecord(
                rubric_id=command.rubric_id,
                version=command.version,
                criteria=criteria_data,
                status="draft",
            )
            session.add(version_record)

            session.commit()

            rubric = session.get(RubricRecord, command.rubric_id)
            assert rubric is not None
            return self._build_rubric_view(session, rubric)

    def create_version(self, rubric_id: str, command: CreateRubricVersionCommand) -> RubricView:
        with self._session_factory() as session:
            rubric = session.get(RubricRecord, rubric_id)
            if rubric is None:
                raise domain_error(
                    "Rubric was not found",
                    code="SS-ADMIN-001",
                    status_code=404,
                    details={"rubric_id": rubric_id},
                )

            existing_version = (
                session.query(RubricVersionRecord)
                .filter(
                    RubricVersionRecord.rubric_id == rubric_id,
                    RubricVersionRecord.version == command.version,
                )
                .first()
            )
            if existing_version is not None:
                raise domain_error(
                    "Rubric version already exists",
                    code="SS-ADMIN-010",
                    details={"rubric_id": rubric_id, "version": command.version},
                )

            criteria_data = self._build_criteria_json(command.criteria)
            version_record = RubricVersionRecord(
                rubric_id=rubric_id,
                version=command.version,
                criteria=criteria_data,
                status="draft",
            )
            session.add(version_record)
            session.commit()

            return self._build_rubric_view(session, rubric)

    def update_rubric(self, rubric_id: str, command: UpdateRubricCommand) -> RubricView:
        with self._session_factory() as session:
            rubric = session.get(RubricRecord, rubric_id)
            if rubric is None:
                raise domain_error(
                    "Rubric was not found",
                    code="SS-ADMIN-001",
                    status_code=404,
                    details={"rubric_id": rubric_id},
                )

            if command.name is not None:
                rubric.name = command.name
            if command.description is not None:
                rubric.description = command.description

            session.commit()
            return self._build_rubric_view(session, rubric)

    def update_criterion(
        self,
        rubric_id: str,
        version: str,
        criterion_ref: str,
        command: RubricCriterionUpdateCommand,
    ) -> RubricView:
        with self._session_factory() as session:
            rubric = session.get(RubricRecord, rubric_id)
            if rubric is None:
                raise domain_error(
                    "Rubric was not found",
                    code="SS-ADMIN-001",
                    status_code=404,
                    details={"rubric_id": rubric_id},
                )

            version_record = (
                session.query(RubricVersionRecord)
                .filter(
                    RubricVersionRecord.rubric_id == rubric_id,
                    RubricVersionRecord.version == version,
                )
                .first()
            )
            if version_record is None:
                raise domain_error(
                    "Rubric version was not found",
                    code="SS-ADMIN-011",
                    status_code=404,
                    details={"rubric_id": rubric_id, "version": version},
                )

            if version_record.status != "draft":
                raise domain_error(
                    "Only draft rubric versions can be updated",
                    code="SS-ADMIN-012",
                    status_code=400,
                    details={"rubric_id": rubric_id, "version": version},
                )

            criteria = version_record.criteria
            criterion_idx = None
            for idx, c in enumerate(criteria):
                if c.get("criterion_ref") == criterion_ref:
                    criterion_idx = idx
                    break

            if criterion_idx is None:
                raise domain_error(
                    "Criterion was not found",
                    code="SS-ADMIN-004",
                    status_code=404,
                    details={"rubric_id": rubric_id, "criterion_ref": criterion_ref},
                )

            criterion = dict(criteria[criterion_idx])
            if command.title is not None:
                criterion["title"] = command.title
            if command.description is not None:
                criterion["description"] = command.description
            if command.weight is not None:
                criterion["weight"] = command.weight
            if command.required is not None:
                criterion["required"] = command.required
            if command.position is not None:
                criterion["position"] = command.position
            if command.levels is not None:
                criterion["levels"] = self._build_levels_json(command.levels)

            new_criteria = list(criteria)
            new_criteria[criterion_idx] = criterion
            version_record.criteria = new_criteria
            version_record.updated_at = datetime.now(UTC)
            session.commit()
            session.refresh(version_record)

            return self._build_rubric_view(session, rubric)

    def add_criterion(
        self,
        rubric_id: str,
        version: str,
        command: CreateRubricCriterionCommand,
    ) -> RubricView:
        with self._session_factory() as session:
            rubric = session.get(RubricRecord, rubric_id)
            if rubric is None:
                raise domain_error(
                    "Rubric was not found",
                    code="SS-ADMIN-001",
                    status_code=404,
                    details={"rubric_id": rubric_id},
                )

            version_record = (
                session.query(RubricVersionRecord)
                .filter(
                    RubricVersionRecord.rubric_id == rubric_id,
                    RubricVersionRecord.version == version,
                )
                .first()
            )
            if version_record is None:
                raise domain_error(
                    "Rubric version was not found",
                    code="SS-ADMIN-011",
                    status_code=404,
                    details={"rubric_id": rubric_id, "version": version},
                )

            if version_record.status != "draft":
                raise domain_error(
                    "Only draft rubric versions can be updated",
                    code="SS-ADMIN-012",
                    status_code=400,
                    details={"rubric_id": rubric_id, "version": version},
                )

            for c in version_record.criteria:
                if c.get("criterion_ref") == command.criterion_ref:
                    raise domain_error(
                        "Criterion already exists in rubric version",
                        code="SS-ADMIN-003",
                        details={
                            "rubric_id": rubric_id,
                            "version": version,
                            "criterion_ref": command.criterion_ref,
                        },
                    )

            new_criterion = self._build_criterion_dict(command)
            version_record.criteria = version_record.criteria + [new_criterion]
            version_record.updated_at = datetime.now(UTC)
            session.commit()

            return self._build_rubric_view(session, rubric)

    def delete_criterion(self, rubric_id: str, version: str, criterion_ref: str) -> RubricView:
        with self._session_factory() as session:
            rubric = session.get(RubricRecord, rubric_id)
            if rubric is None:
                raise domain_error(
                    "Rubric was not found",
                    code="SS-ADMIN-001",
                    status_code=404,
                    details={"rubric_id": rubric_id},
                )

            version_record = (
                session.query(RubricVersionRecord)
                .filter(
                    RubricVersionRecord.rubric_id == rubric_id,
                    RubricVersionRecord.version == version,
                )
                .first()
            )
            if version_record is None:
                raise domain_error(
                    "Rubric version was not found",
                    code="SS-ADMIN-011",
                    status_code=404,
                    details={"rubric_id": rubric_id, "version": version},
                )

            if version_record.status != "draft":
                raise domain_error(
                    "Only draft rubric versions can be updated",
                    code="SS-ADMIN-012",
                    status_code=400,
                    details={"rubric_id": rubric_id, "version": version},
                )

            original_len = len(version_record.criteria)
            version_record.criteria = [
                c for c in version_record.criteria if c.get("criterion_ref") != criterion_ref
            ]

            if len(version_record.criteria) == original_len:
                raise domain_error(
                    "Criterion was not found",
                    code="SS-ADMIN-004",
                    status_code=404,
                    details={"rubric_id": rubric_id, "criterion_ref": criterion_ref},
                )

            version_record.updated_at = datetime.now(UTC)
            session.commit()

            return self._build_rubric_view(session, rubric)

    def delete_rubric(self, rubric_id: str) -> None:
        with self._session_factory() as session:
            rubric = session.get(RubricRecord, rubric_id)
            if rubric is None:
                raise domain_error(
                    "Rubric was not found",
                    code="SS-ADMIN-001",
                    status_code=404,
                    details={"rubric_id": rubric_id},
                )

            session.query(RubricVersionRecord).filter(
                RubricVersionRecord.rubric_id == rubric_id
            ).delete()
            session.delete(rubric)
            session.commit()

    def publish_version(self, rubric_id: str, version: str) -> RubricView:
        with self._session_factory() as session:
            rubric = session.get(RubricRecord, rubric_id)
            if rubric is None:
                raise domain_error(
                    "Rubric was not found",
                    code="SS-ADMIN-001",
                    status_code=404,
                    details={"rubric_id": rubric_id},
                )

            version_record = (
                session.query(RubricVersionRecord)
                .filter(
                    RubricVersionRecord.rubric_id == rubric_id,
                    RubricVersionRecord.version == version,
                )
                .first()
            )
            if version_record is None:
                raise domain_error(
                    "Rubric version was not found",
                    code="SS-ADMIN-011",
                    status_code=404,
                    details={"rubric_id": rubric_id, "version": version},
                )

            if version_record.status != "draft":
                raise domain_error(
                    "Only draft rubric versions can be published",
                    code="SS-ADMIN-013",
                    status_code=400,
                    details={"rubric_id": rubric_id, "version": version},
                )

            version_record.status = "published"
            version_record.updated_at = datetime.now(UTC)
            session.commit()

            return self._build_rubric_view(session, rubric)

    def archive_version(self, rubric_id: str, version: str) -> RubricView:
        with self._session_factory() as session:
            rubric = session.get(RubricRecord, rubric_id)
            if rubric is None:
                raise domain_error(
                    "Rubric was not found",
                    code="SS-ADMIN-001",
                    status_code=404,
                    details={"rubric_id": rubric_id},
                )

            version_record = (
                session.query(RubricVersionRecord)
                .filter(
                    RubricVersionRecord.rubric_id == rubric_id,
                    RubricVersionRecord.version == version,
                )
                .first()
            )
            if version_record is None:
                raise domain_error(
                    "Rubric version was not found",
                    code="SS-ADMIN-011",
                    status_code=404,
                    details={"rubric_id": rubric_id, "version": version},
                )

            if version_record.status != "published":
                raise domain_error(
                    "Only published rubric versions can be archived",
                    code="SS-ADMIN-014",
                    status_code=400,
                    details={"rubric_id": rubric_id, "version": version},
                )

            version_record.status = "archived"
            version_record.updated_at = datetime.now(UTC)
            session.commit()

            return self._build_rubric_view(session, rubric)

    def _build_criteria_json(
        self, criteria_commands: list[RubricCriterionCommand]
    ) -> list[dict[str, Any]]:
        return [self._build_criterion_dict(cmd) for cmd in criteria_commands]

    def _build_criterion_dict(self, command: RubricCriterionCommand) -> dict[str, Any]:
        return {
            "criterion_ref": command.criterion_ref,
            "skill_slug": command.skill_slug,
            "title": command.title,
            "description": command.description,
            "weight": command.weight,
            "required": command.required,
            "position": command.position,
            "levels": self._build_levels_json(command.levels),
        }

    def _build_levels_json(self, levels: list[RubricCriterionLevelCommand]) -> list[dict[str, Any]]:
        return [
            {
                f"level_{level_cmd.level}": {
                    "description": level_cmd.description,
                    "examples": list(level_cmd.examples),
                }
            }
            for level_cmd in sorted(levels, key=lambda lv: lv.level)
        ]

    def _build_rubric_view(self, session: Session, rubric: RubricRecord) -> RubricView:
        version_records = (
            session.query(RubricVersionRecord)
            .filter(RubricVersionRecord.rubric_id == rubric.id)
            .order_by(RubricVersionRecord.version.desc())
            .all()
        )

        versions = [self._build_version_view(v) for v in version_records]

        return RubricView(
            rubric_id=rubric.id,
            skill_slug=rubric.skill_slug,
            organisation_id=rubric.organisation_id,
            name=rubric.name,
            description=rubric.description,
            content_type=rubric.content_type,
            schema_version=rubric.schema_version,
            versions=versions,
        )

    def _build_version_view(self, version: RubricVersionRecord) -> RubricVersionView:
        criteria = [self._build_criterion_view(c) for c in version.criteria]

        return RubricVersionView(
            id=version.id,
            rubric_id=version.rubric_id,
            version=version.version,
            criteria=criteria,
            status=version.status,
            created_at=version.created_at.isoformat() if version.created_at else "",
            updated_at=version.updated_at.isoformat() if version.updated_at else None,
        )

    def _build_criterion_view(self, criterion_data: dict[str, Any]) -> RubricCriterionView:
        levels = []
        for item in list(criterion_data.get("levels", [])):
            if not item:
                continue
            label, payload = next(iter(item.items()))
            level_value = int(str(label).split("_")[-1])
            levels.append(
                RubricCriterionLevelView(
                    level=level_value,
                    description=str(payload["description"]),
                    examples=[str(ex) for ex in payload.get("examples", [])],
                )
            )
        levels.sort(key=lambda lv: lv.level)

        return RubricCriterionView(
            criterion_ref=criterion_data.get("criterion_ref", ""),
            skill_slug=criterion_data.get("skill_slug", ""),
            title=criterion_data.get("title", ""),
            description=criterion_data.get("description", ""),
            weight=criterion_data.get("weight", 1.0),
            required=criterion_data.get("required", True),
            position=criterion_data.get("position", 0),
            levels=levels,
        )
