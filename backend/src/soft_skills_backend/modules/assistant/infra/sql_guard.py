"""Guardrails for assistant SQL reads."""

from __future__ import annotations

import re
from dataclasses import dataclass

from soft_skills_backend.modules.assistant.contracts.sql import (
    AssistantSqlScalar,
    QueryUserContextCommand,
)
from soft_skills_backend.modules.assistant.domain.schema_registry import AssistantSchemaRegistry
from soft_skills_backend.shared.errors import validation_error

_RELATION_PATTERN = re.compile(
    r"\b(?P<keyword>from|join)\s+"
    r"(?P<view>assistant_safe_[a-zA-Z0-9_]+(?:_v)?)"
    r"(?:\s+(?:as\s+)?"
    r"(?P<alias>(?!where\b|group\b|order\b|limit\b|join\b|on\b|having\b)[a-zA-Z_][a-zA-Z0-9_]*))?",
    re.IGNORECASE,
)
_DENIED_TOKEN_PATTERN = re.compile(
    r"\b(insert|update|delete|alter|drop|truncate|attach|detach|pragma|create|replace|merge|call|copy|vacuum)\b",
    re.IGNORECASE,
)
_SET_OPERATION_PATTERN = re.compile(r"\b(union|intersect|except)\b", re.IGNORECASE)
_COUNT_STAR_PATTERN = re.compile(r"^\s*count\s*\(\s*\*\s*\)\s*(?:as\s+\w+)?\s*$", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class GuardedAssistantQuery:
    sql: str
    scoped_sql: str
    params: dict[str, AssistantSqlScalar]
    source_views: tuple[str, ...]
    row_cap_applied: bool


class AssistantSqlGuard:
    """Validate and scope learner-safe read-only SQL."""

    def __init__(
        self,
        *,
        schema_registry: AssistantSchemaRegistry,
        row_limit: int,
    ) -> None:
        self._schema_registry = schema_registry
        self._row_limit = row_limit

    def validate_and_scope(self, command: QueryUserContextCommand) -> GuardedAssistantQuery:
        sql = self._normalize_sql(command.sql)
        sql = self._canonicalize_view_names(sql)
        self._reject_disallowed_sql(sql)
        source_views, aliases = self._extract_source_views(sql)
        sql = self._canonicalize_projection_columns(sql, aliases)
        sql = self._expand_select_wildcards(sql, aliases)
        self._reject_select_wildcards(sql)
        scoped_sql = self._scope_sql(sql)
        return GuardedAssistantQuery(
            sql=sql,
            scoped_sql=(
                f"SELECT * FROM ({scoped_sql}) AS assistant_result LIMIT :_assistant_row_limit"
            ),
            params=dict(command.params),
            source_views=source_views,
            row_cap_applied=True,
        )

    def _normalize_sql(self, sql: str) -> str:
        normalized = sql.strip()
        if normalized.endswith(";"):
            normalized = normalized[:-1].rstrip()
        if not normalized:
            raise validation_error(
                "Assistant SQL must not be blank",
                code="SS-VALIDATION-312",
            )
        return normalized

    def _reject_disallowed_sql(self, sql: str) -> None:
        lowered = sql.lower()
        if not lowered.startswith("select "):
            raise validation_error(
                "Assistant accepts SELECT queries only",
                code="SS-VALIDATION-313",
            )
        if "--" in sql or "/*" in sql or "*/" in sql or ";" in sql:
            raise validation_error(
                "Assistant SQL comments and multi-statement syntax are not allowed",
                code="SS-VALIDATION-314",
            )
        if "(select" in lowered or _SET_OPERATION_PATTERN.search(sql):
            raise validation_error(
                "Assistant SQL must not use subqueries or set operations",
                code="SS-VALIDATION-315",
            )
        if _DENIED_TOKEN_PATTERN.search(sql):
            raise validation_error(
                "Assistant SQL contained a denied statement",
                code="SS-VALIDATION-316",
            )

    def _canonicalize_view_names(self, sql: str) -> str:
        def replace(match: re.Match[str]) -> str:
            keyword = match.group("keyword")
            raw_view_name = match.group("view")
            alias = match.group("alias")
            resolved_view = self._schema_registry.resolve_view_name(raw_view_name)
            view_name = resolved_view or raw_view_name
            alias_suffix = ""
            if alias:
                alias_suffix = f" AS {alias}"
            return f"{keyword} {view_name}{alias_suffix}"

        return _RELATION_PATTERN.sub(replace, sql)

    def _extract_source_views(self, sql: str) -> tuple[tuple[str, ...], dict[str, str]]:
        views: list[str] = []
        aliases: dict[str, str] = {}
        for match in _RELATION_PATTERN.finditer(sql):
            view_name = match.group("view")
            if not self._schema_registry.has_view(view_name):
                raise validation_error(
                    "Assistant SQL referenced a disallowed target",
                    code="SS-VALIDATION-317",
                    details={"target": view_name},
                )
            views.append(view_name)
            alias = match.group("alias")
            if alias:
                aliases[alias] = view_name
            aliases[view_name] = view_name
        if not views:
            raise validation_error(
                "Assistant SQL must query an allowlisted assistant view",
                code="SS-VALIDATION-318",
            )
        return tuple(dict.fromkeys(views)), aliases

    def _canonicalize_projection_columns(self, sql: str, aliases: dict[str, str]) -> str:
        select_clause = _extract_select_clause(sql)
        select_items = _split_top_level_csv(select_clause)
        rewritten_items: list[str] = []
        changed = False

        for item in select_items:
            rewritten_item = self._canonicalize_select_item(item, aliases)
            if rewritten_item != item:
                changed = True
            rewritten_items.append(rewritten_item)

        if not changed:
            return sql

        lowered = sql.lower()
        from_index = lowered.index(" from")
        return f"SELECT {', '.join(rewritten_items)}{sql[from_index:]}"

    def _expand_select_wildcards(self, sql: str, aliases: dict[str, str]) -> str:
        select_clause = _extract_select_clause(sql)
        select_items = _split_top_level_csv(select_clause)
        expanded_items: list[str] = []
        changed = False

        for item in select_items:
            stripped = item.strip()
            if stripped == "*":
                if len(set(aliases.values())) != 1:
                    expanded_items.append(item)
                    continue
                view_name = next(iter(aliases.values()))
                expanded_items.extend(self._schema_registry.get_view(view_name).columns)
                changed = True
                continue
            if stripped.endswith(".*"):
                qualifier = stripped[:-2]
                expanded_view_name: str | None = aliases.get(qualifier)
                if expanded_view_name is None:
                    expanded_items.append(item)
                    continue
                expanded_items.extend(
                    f"{qualifier}.{column}"
                    for column in self._schema_registry.get_view(expanded_view_name).columns
                )
                changed = True
                continue
            expanded_items.append(item)

        if not changed:
            return sql

        lowered = sql.lower()
        from_index = lowered.index(" from")
        rewritten_select = ", ".join(expanded_items)
        return f"SELECT {rewritten_select}{sql[from_index:]}"

    def _canonicalize_select_item(self, item: str, aliases: dict[str, str]) -> str:
        match = re.match(
            r"^\s*(?:(?P<qualifier>[A-Za-z_][A-Za-z0-9_]*)\.)?"
            r"(?P<column>[A-Za-z_][A-Za-z0-9_]*)"
            r"(?:\s+AS\s+(?P<alias>[A-Za-z_][A-Za-z0-9_]*))?\s*$",
            item,
            re.IGNORECASE,
        )
        if match is None:
            return item

        qualifier = match.group("qualifier")
        column = match.group("column")
        alias = match.group("alias")
        view_name: str
        if qualifier is None:
            unique_views = tuple(dict.fromkeys(aliases.values()))
            if len(unique_views) != 1:
                return item
            view_name = unique_views[0]
        else:
            resolved_view_name = aliases.get(qualifier)
            if resolved_view_name is None:
                return item
            view_name = resolved_view_name

        resolved_column = self._schema_registry.resolve_column_name(view_name, column)
        if resolved_column is None or resolved_column == column:
            return item

        column_ref = f"{qualifier}.{resolved_column}" if qualifier else resolved_column
        alias_ref = alias or column
        return f"{column_ref} AS {alias_ref}"

    def _reject_select_wildcards(self, sql: str) -> None:
        select_clause = _extract_select_clause(sql)
        for item in _split_top_level_csv(select_clause):
            if "*" not in item:
                continue
            if _COUNT_STAR_PATTERN.match(item):
                continue
            raise validation_error(
                "Assistant SQL must project explicit columns",
                code="SS-VALIDATION-319",
                details={"select_item": item.strip()},
            )

    def _scope_sql(self, sql: str) -> str:
        def replace(match: re.Match[str]) -> str:
            keyword = match.group("keyword").upper()
            view_name = match.group("view")
            alias = match.group("alias") or view_name
            view = self._schema_registry.get_view(view_name)
            predicates: list[str] = []
            if "organisation_id" in view.scope_columns:
                predicates.append(
                    "(organisation_id = :organisation_id OR "
                    "(:organisation_id IS NULL AND organisation_id IS NULL))"
                )
            if view_name == "assistant_safe_collections_v":
                predicates.append("author_user_id = :user_id")
            if "user_id" in view.scope_columns:
                predicates.append("user_id = :user_id")
            return (
                f"{keyword} (SELECT * FROM {view_name} WHERE {' AND '.join(predicates)}) AS {alias}"
            )

        return _RELATION_PATTERN.sub(replace, sql)


def _extract_select_clause(sql: str) -> str:
    lowered = sql.lower()
    depth = 0
    for index, char in enumerate(sql):
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)
        elif depth == 0 and lowered[index : index + 5] == " from":
            return sql[6:index]
    raise validation_error(
        "Assistant SQL must include a FROM clause",
        code="SS-VALIDATION-320",
    )


def _split_top_level_csv(value: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    for char in value:
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)
        if char == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    if current:
        parts.append("".join(current).strip())
    return [part for part in parts if part]
