"""Admin rubric repository for CRUD operations on marking scheme rubrics."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.modules.admin.contracts.commands import (
    CreateRubricCommand,
    CreateRubricCriterionCommand,
    RubricCriterionCommand,
    RubricCriterionLevelCommand,
    RubricCriterionUpdateCommand,
    UpdateRubricCommand,
)
from soft_skills_backend.modules.admin.contracts.views import (
    RubricCriterionLevelView,
    RubricCriterionView,
    RubricView,
)
from soft_skills_backend.platform.db.models import RubricRecord, RubricVersionRecord
from soft_skills_backend.shared.errors import domain_error


class RubricAdminRepository:
    """Repository for admin CRUD operations on rubrics."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def list_rubrics(self) -> list[RubricView]:
        with self._session_factory() as session:
            rubrics = session.query(RubricRecord).order_by(RubricRecord.rubric_id).all()
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
                rubric_id=command.rubric_id,
                family=command.family,
                version=command.version,
                content_type=command.content_type,
                schema_version=command.schema_version,
                name=command.name,
                criteria=[c.criterion_ref for c in command.criteria],
            )
            session.add(rubric_record)

            for criterion_cmd in command.criteria:
                self._add_criterion_record(
                    session, command.rubric_id, command.version, criterion_cmd
                )

            session.commit()

            rubric = session.get(RubricRecord, command.rubric_id)
            assert rubric is not None
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

            if command.family is not None:
                rubric.family = command.family
            if command.version is not None:
                rubric.version = command.version
            if command.name is not None:
                rubric.name = command.name

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

            session.query(RubricCriterionRecord).filter(
                RubricCriterionRecord.rubric_id == rubric_id
            ).delete()
            session.delete(rubric)
            session.commit()

    def create_criterion(self, rubric_id: str, command: CreateRubricCriterionCommand) -> RubricView:
        with self._session_factory() as session:
            rubric = session.get(RubricRecord, rubric_id)
            if rubric is None:
                raise domain_error(
                    "Rubric was not found",
                    code="SS-ADMIN-001",
                    status_code=404,
                    details={"rubric_id": rubric_id},
                )

            existing = (
                session.query(RubricCriterionRecord)
                .filter(
                    RubricCriterionRecord.rubric_id == rubric_id,
                    RubricCriterionRecord.criterion_ref == command.criterion_ref,
                )
                .one_or_none()
            )
            if existing is not None:
                raise domain_error(
                    "Criterion already exists in rubric",
                    code="SS-ADMIN-003",
                    details={
                        "rubric_id": rubric_id,
                        "criterion_ref": command.criterion_ref,
                    },
                )

            self._add_criterion_record(session, rubric_id, rubric.version, command)

            rubric.criteria = sorted(set(rubric.criteria) | {command.criterion_ref})
            session.commit()

            return self._build_rubric_view(session, rubric)

    def update_criterion(
        self, rubric_id: str, criterion_ref: str, command: RubricCriterionUpdateCommand
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

            criterion = (
                session.query(RubricCriterionRecord)
                .filter(
                    RubricCriterionRecord.rubric_id == rubric_id,
                    RubricCriterionRecord.criterion_ref == criterion_ref,
                )
                .one_or_none()
            )
            if criterion is None:
                raise domain_error(
                    "Criterion was not found",
                    code="SS-ADMIN-004",
                    status_code=404,
                    details={"rubric_id": rubric_id, "criterion_ref": criterion_ref},
                )

            if command.title is not None:
                criterion.title = command.title
            if command.description is not None:
                criterion.description = command.description
            if command.weight is not None:
                criterion.weight = command.weight
            if command.required is not None:
                criterion.required = command.required
            if command.position is not None:
                criterion.position = command.position
            if command.levels is not None:
                criterion.levels_json = self._build_levels_json(command.levels)

            session.commit()
            return self._build_rubric_view(session, rubric)

    def delete_criterion(self, rubric_id: str, criterion_ref: str) -> RubricView:
        with self._session_factory() as session:
            rubric = session.get(RubricRecord, rubric_id)
            if rubric is None:
                raise domain_error(
                    "Rubric was not found",
                    code="SS-ADMIN-001",
                    status_code=404,
                    details={"rubric_id": rubric_id},
                )

            deleted = (
                session.query(RubricCriterionRecord)
                .filter(
                    RubricCriterionRecord.rubric_id == rubric_id,
                    RubricCriterionRecord.criterion_ref == criterion_ref,
                )
                .delete()
            )
            if deleted == 0:
                raise domain_error(
                    "Criterion was not found",
                    code="SS-ADMIN-004",
                    status_code=404,
                    details={"rubric_id": rubric_id, "criterion_ref": criterion_ref},
                )

            rubric.criteria = [c for c in rubric.criteria if c != criterion_ref]
            session.commit()

            return self._build_rubric_view(session, rubric)

    def _add_criterion_record(
        self,
        session: Session,
        rubric_id: str,
        rubric_version: str,
        command: RubricCriterionCommand | CreateRubricCriterionCommand,
    ) -> None:
        record = RubricCriterionRecord(
            rubric_id=rubric_id,
            rubric_version=rubric_version,
            criterion_ref=command.criterion_ref,
            skill_slug=command.skill_slug,
            title=command.title,
            description=command.description,
            weight=command.weight,
            required=command.required,
            position=command.position,
            levels_json=self._build_levels_json(command.levels),
        )
        session.add(record)

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
        criteria_records = (
            session.query(RubricCriterionRecord)
            .filter(RubricCriterionRecord.rubric_id == rubric.rubric_id)
            .order_by(RubricCriterionRecord.position)
            .all()
        )
        return RubricView(
            rubric_id=rubric.rubric_id,
            family=rubric.family,
            version=rubric.version,
            content_type=rubric.content_type,
            schema_version=rubric.schema_version,
            name=rubric.name,
            criteria=[self._build_criterion_view(r) for r in criteria_records],
        )

    def _build_criterion_view(self, record: RubricCriterionRecord) -> RubricCriterionView:
        levels = []
        for item in list(record.levels_json):
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
            criterion_ref=record.criterion_ref,
            skill_slug=record.skill_slug,
            title=record.title,
            description=record.description,
            weight=record.weight,
            required=record.required,
            position=record.position,
            levels=levels,
        )
