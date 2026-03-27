"""Rubric-loading interfaces for the marking runtime."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.engines.marking import RubricCriterion, RubricDefinition, RubricLevel, RubricScale
from soft_skills_backend.platform.db.models import RubricCriterionRecord, RubricRecord
from soft_skills_backend.shared.errors import validation_error


class RubricRepository(Protocol):
    """Load rubric definitions and criterion text for marking."""

    def get_rubric_definition(
        self,
        rubric_id: str,
        *,
        required_skill_slugs: Iterable[str] | None = None,
    ) -> RubricDefinition: ...

    def get_skill_criterion(self, rubric_id: str, skill_slug: str) -> RubricCriterion: ...


class SqlAlchemyRubricRepository:
    """SQLAlchemy rubric loader backed by the rubric criteria table."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def get_rubric_definition(
        self,
        rubric_id: str,
        *,
        required_skill_slugs: Iterable[str] | None = None,
    ) -> RubricDefinition:
        required = None if required_skill_slugs is None else set(required_skill_slugs)
        with self._session_factory() as session:
            rubric = session.get(RubricRecord, rubric_id)
            if rubric is None:
                raise validation_error(
                    "Rubric was not found",
                    code="SS-VALIDATION-071",
                    details={"rubric_id": rubric_id},
                )
            query = session.query(RubricCriterionRecord).filter(
                RubricCriterionRecord.rubric_id == rubric_id
            )
            if required is not None:
                query = query.filter(RubricCriterionRecord.skill_slug.in_(sorted(required)))
            records = query.order_by(RubricCriterionRecord.position).all()
        if not records:
            raise validation_error(
                "Rubric criteria were not found",
                code="SS-VALIDATION-072",
                details={"rubric_id": rubric_id},
            )
        criteria = [self._to_criterion(record) for record in records]
        maximum_score = max(level.level for criterion in criteria for level in criterion.levels)
        return RubricDefinition(
            rubric_id=rubric.rubric_id,
            rubric_version=rubric.version,
            scale=RubricScale(minimum_score=1, maximum_score=maximum_score),
            criteria=criteria,
        )

    def get_skill_criterion(self, rubric_id: str, skill_slug: str) -> RubricCriterion:
        with self._session_factory() as session:
            record = (
                session.query(RubricCriterionRecord)
                .filter(
                    RubricCriterionRecord.rubric_id == rubric_id,
                    RubricCriterionRecord.skill_slug == skill_slug,
                )
                .one_or_none()
            )
        if record is None:
            raise validation_error(
                "Rubric criterion was not found",
                code="SS-VALIDATION-073",
                details={"rubric_id": rubric_id, "skill_slug": skill_slug},
            )
        return self._to_criterion(record)

    def _to_criterion(self, record: RubricCriterionRecord) -> RubricCriterion:
        levels: list[RubricLevel] = []
        for item in list(record.levels_json):
            if not item:
                continue
            label, payload = next(iter(item.items()))
            level_value = int(str(label).split("_")[-1])
            levels.append(
                RubricLevel(
                    level=level_value,
                    description=str(payload["description"]),
                    examples=[str(example) for example in payload.get("examples", [])],
                )
            )
        levels.sort(key=lambda item: item.level)
        return RubricCriterion(
            criterion_ref=record.criterion_ref,
            title=record.title,
            description=record.description,
            weight=record.weight,
            required=record.required,
            levels=levels,
        )
