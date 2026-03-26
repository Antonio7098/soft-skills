"""Core smoke test contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from pydantic import BaseModel

from soft_skills_backend.config import Settings, get_settings


@dataclass(frozen=True, slots=True)
class SmokeContext:
    """Runtime context shared by smoke suites."""

    settings: Settings

    @classmethod
    def create(cls, settings: Settings | None = None) -> SmokeContext:
        return cls(settings=settings or get_settings())


class SmokeDefinition(BaseModel):
    """Serializable smoke metadata."""

    name: str
    description: str


class SmokeExecutionResult(BaseModel):
    """Serialized smoke run output."""

    smoke_name: str
    description: str
    payload: dict[str, object]

    @classmethod
    def from_result(cls, smoke: SmokeCase, result: BaseModel) -> SmokeExecutionResult:
        return cls(
            smoke_name=smoke.name,
            description=smoke.description,
            payload=result.model_dump(mode="json"),
        )


class SmokeCase(ABC):
    """Base contract for concrete smoke suites."""

    name: str
    description: str

    @abstractmethod
    def run(self, context: SmokeContext) -> BaseModel:
        """Execute the smoke suite."""
