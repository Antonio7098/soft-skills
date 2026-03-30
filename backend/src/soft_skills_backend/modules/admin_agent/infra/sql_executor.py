"""Scoped SQL executor for the admin agent."""

from __future__ import annotations

from time import perf_counter
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.modules.admin_agent.contracts.views import QueryAdminDataResultView
from soft_skills_backend.modules.admin_agent.domain.redactor import AdminAgentResultRedactor
from soft_skills_backend.modules.admin_agent.infra.sql_guard import GuardedAdminQuery
from soft_skills_backend.shared.auth import Actor
from soft_skills_backend.shared.errors import orchestration_error, validation_error


class AdminAgentSqlExecutor:
    """Execute guarded admin-agent SQL with org scoping and defensive redaction."""

    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        redactor: AdminAgentResultRedactor,
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
        query: GuardedAdminQuery,
    ) -> QueryAdminDataResultView:
        if actor.organisation_id is None:
            raise validation_error(
                "Admin agent queries require an organisation context",
                code="SS-VALIDATION-310",
            )
        rows, duration_ms = self._execute_sync(actor.organisation_id, query)
        if duration_ms > int(self._timeout_seconds * 1000):
            raise orchestration_error(
                "Admin agent query timed out",
                code="SS-ORCHESTRATION-301",
                status_code=504,
                details={"timeout_seconds": self._timeout_seconds},
            )

        return QueryAdminDataResultView(
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
        organisation_id: str,
        query: GuardedAdminQuery,
    ) -> tuple[list[dict[str, Any]], int]:
        started = perf_counter()
        try:
            with self._session_factory() as session:
                result = session.execute(
                    text(query.scoped_sql),
                    {
                        "organisation_id": organisation_id,
                        "_admin_agent_row_limit": self._row_limit,
                        **query.params,
                    },
                )
                rows = [dict(mapping) for mapping in result.mappings().all()]
        except SQLAlchemyError as exc:
            raise validation_error(
                "Admin agent SQL failed execution",
                code="SS-VALIDATION-311",
                details={"reason": str(exc)},
            ) from exc
        duration_ms = int((perf_counter() - started) * 1000)
        return self._redactor.redact_rows(rows), duration_ms
