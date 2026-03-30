"""Rubric-loading interfaces for the marking runtime."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Protocol

from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.engines.marking import (
    RubricCriterion,
    RubricDefinition,
    RubricLevel,
    RubricScale,
)
from soft_skills_backend.platform.db.models import RubricRecord, RubricVersionRecord
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
    """SQLAlchemy rubric loader backed by the new rubric_versions table."""

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
            # Get the latest published version
            version = (
                session.query(RubricVersionRecord)
                .filter(
                    RubricVersionRecord.rubric_id == rubric_id,
                    RubricVersionRecord.status == "published",
                )
                .order_by(RubricVersionRecord.version.desc())
                .first()
            )
            if version is None:
                raise validation_error(
                    "Rubric version was not found",
                    code="SS-VALIDATION-074",
                    details={"rubric_id": rubric_id},
                )

        criteria_data = version.criteria
        criteria = [
            self._to_criterion(criterion_data)
            for criterion_data in criteria_data
            if _criterion_matches_required(criterion_data, required)
        ]
        if not criteria:
            raise validation_error(
                "Rubric criteria were not found",
                code="SS-VALIDATION-072",
                details={"rubric_id": rubric_id},
            )
        maximum_score = max(level.level for criterion in criteria for level in criterion.levels)
        return RubricDefinition(
            rubric_id=rubric.id,
            rubric_version=version.version,
            scale=RubricScale(minimum_score=1, maximum_score=maximum_score),
            criteria=criteria,
        )

    def get_skill_criterion(self, rubric_id: str, skill_slug: str) -> RubricCriterion:
        with self._session_factory() as session:
            version = (
                session.query(RubricVersionRecord)
                .filter(
                    RubricVersionRecord.rubric_id == rubric_id,
                    RubricVersionRecord.status == "published",
                )
                .order_by(RubricVersionRecord.version.desc())
                .first()
            )
            if version is None:
                raise validation_error(
                    "Rubric version was not found",
                    code="SS-VALIDATION-074",
                    details={"rubric_id": rubric_id},
                )

        for criterion_data in version.criteria:
            if criterion_data.get("criterion_ref") == skill_slug:
                return self._to_criterion(criterion_data)

        raise validation_error(
            "Rubric criterion was not found",
            code="SS-VALIDATION-073",
            details={"rubric_id": rubric_id, "skill_slug": skill_slug},
        )

    def _to_criterion(self, data: dict[str, Any]) -> RubricCriterion:
        levels: list[RubricLevel] = []
        for item in list(data.get("levels", [])):
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
            criterion_ref=data.get("criterion_ref", ""),
            title=data.get("title", ""),
            description=data.get("description", ""),
            weight=data.get("weight", 0.0),
            required=data.get("required", True),
            levels=levels,
        )


def _criterion_matches_required(criterion_data: dict[str, Any], required: set[str] | None) -> bool:
    if required is None:
        return True
    return criterion_data.get("criterion_ref") in required
