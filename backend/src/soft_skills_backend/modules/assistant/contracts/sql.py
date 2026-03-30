"""Assistant structured SQL contracts."""

from __future__ import annotations

from typing import TypeAlias

from pydantic import BaseModel, Field, field_validator

AssistantSqlScalar: TypeAlias = str | int | float | bool | None


class QueryUserContextCommand(BaseModel):
    sql: str = Field(min_length=1, max_length=4000)
    params: dict[str, AssistantSqlScalar] = Field(default_factory=dict)

    @field_validator("sql")
    @classmethod
    def _strip_sql(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("SQL must not be blank")
        return normalized
