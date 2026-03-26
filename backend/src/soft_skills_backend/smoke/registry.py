"""Smoke registry for discoverable suites."""

from __future__ import annotations

from collections.abc import Iterable

from soft_skills_backend.shared.errors import validation_error

from .contracts import SmokeCase, SmokeDefinition


class SmokeRegistry:
    """Central registry of smoke suites."""

    def __init__(self, smokes: Iterable[SmokeCase] | None = None) -> None:
        self._smokes: dict[str, SmokeCase] = {}
        for smoke in smokes or ():
            self.register(smoke)

    def register(self, smoke: SmokeCase) -> None:
        if smoke.name in self._smokes:
            raise ValueError(f"Smoke '{smoke.name}' is already registered")
        self._smokes[smoke.name] = smoke

    def get(self, name: str) -> SmokeCase:
        smoke = self._smokes.get(name)
        if smoke is not None:
            return smoke
        raise validation_error(
            "Unknown smoke target",
            code="SS-VALIDATION-003",
            details={"smoke_name": name, "available_smokes": self.names()},
        )

    def default(self) -> SmokeCase:
        if not self._smokes:
            raise RuntimeError("Smoke registry is empty")
        return next(iter(self._smokes.values()))

    def definitions(self) -> list[SmokeDefinition]:
        return [
            SmokeDefinition(name=smoke.name, description=smoke.description)
            for smoke in self._smokes.values()
        ]

    def names(self) -> list[str]:
        return list(self._smokes)
