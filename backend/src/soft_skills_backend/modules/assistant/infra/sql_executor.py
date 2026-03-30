"""Scoped SQL executor for the learner assistant."""

from __future__ import annotations

from time import perf_counter
from typing import Any, Mapping, cast

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.modules.assistant.contracts.views import QueryUserContextResultView
from soft_skills_backend.modules.assistant.domain.redactor import AssistantResultRedactor
from soft_skills_backend.modules.assistant.infra.sql_guard import GuardedAssistantQuery
from soft_skills_backend.shared.auth import Actor
from soft_skills_backend.shared.errors import orchestration_error, validation_error


class AssistantSqlExecutor:
    """Execute guarded learner SQL with defensive redaction."""

    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        redactor: AssistantResultRedactor,
        row_limit: int,
        timeout_seconds: float,
    ) -> None:
        self._session_factory = session_factory
        self._redactor = redactor
        self._row_limit = row_limit
        self._timeout_seconds = timeout_seconds

    async def execute(
        self,
        *,
        actor: Actor,
        query: GuardedAssistantQuery,
    ) -> QueryUserContextResultView:
        rows, duration_ms = self._execute_sync(actor.user_id, actor.organisation_id, query)
        if duration_ms > int(self._timeout_seconds * 1000):
            raise orchestration_error(
                "Assistant query timed out",
                code="SS-ORCHESTRATION-205",
                status_code=504,
                details={"timeout_seconds": self._timeout_seconds},
            )

        return QueryUserContextResultView(
            sql=query.sql,
            params=query.params,
            source_views=list(query.source_views),
            row_count=len(rows),
            row_cap_applied=query.row_cap_applied,
            duration_ms=duration_ms,
            rows=rows,
        )

    def _execute_sync(
        self,
        user_id: str,
        organisation_id: str | None,
        query: GuardedAssistantQuery,
    ) -> tuple[list[dict[str, Any]], int]:
        started = perf_counter()
        try:
            with self._session_factory() as session:
                result = session.execute(
                    text(query.scoped_sql),
                    {
                        "user_id": user_id,
                        "organisation_id": organisation_id,
                        "_assistant_row_limit": self._row_limit,
                        **query.params,
                    },
                )
                rows = [dict(mapping) for mapping in result.mappings().all()]
        except SQLAlchemyError as exc:
            raise validation_error(
                "Assistant SQL failed execution",
                code="SS-VALIDATION-321",
                details={"reason": str(exc)},
            ) from exc
        duration_ms = int((perf_counter() - started) * 1000)
        return self._redactor.redact_rows(cast(list[Mapping[str, Any]], rows)), duration_ms
