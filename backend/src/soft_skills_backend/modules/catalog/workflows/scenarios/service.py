"""Scenario catalog service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker
from stageflow.api import Pipeline, StageKind, stage

from soft_skills_backend.modules.catalog.contracts.scenario_commands import ScenarioCreateCommand
from soft_skills_backend.modules.catalog.contracts.scenario_views import ScenarioView
from soft_skills_backend.modules.catalog.domain.validators import (
    require_collection_owner_or_admin,
    validate_scenario_command,
)
from soft_skills_backend.modules.catalog.infra.events import CatalogEventRecorder
from soft_skills_backend.modules.catalog.workflows.collections.service import CollectionService
from soft_skills_backend.platform.db.models import (
    CollectionRecord,
    MockCompanyRecord,
    MockPersonRecord,
    ScenarioRecord,
)
from soft_skills_backend.platform.workflows.stageflow import (
    StageflowPipelineSupport,
    StageflowStageResult,
    ok_output,
    payload_from_results,
    run_logged_pipeline,
)
from soft_skills_backend.platform.workflows.stageflow_runtime import StageflowRuntime
from soft_skills_backend.shared.auth import Actor
from soft_skills_backend.shared.errors import domain_error


class ScenarioService:
    """Own scenario authoring operations."""

    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        events: CatalogEventRecorder,
        collections: CollectionService,
        stageflow_runtime: StageflowRuntime,
    ) -> None:
        self._session_factory = session_factory
        self._events = events
        self._collections = collections
        self._stageflow = StageflowPipelineSupport.from_runtime(stageflow_runtime)

    async def add_scenario(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        collection_id: str,
        command: ScenarioCreateCommand,
    ) -> ScenarioView:
        async def input_guard(_ctx) -> Any:
            with self._session_factory() as session:
                collection = session.get(CollectionRecord, collection_id)
                if collection is None:
                    raise domain_error(
                        "Collection was not found",
                        code="SS-DOMAIN-005",
                        status_code=404,
                        details={"collection_id": collection_id},
                    )
                require_collection_owner_or_admin(actor, collection)
                validate_scenario_command(session, collection, command)
            return ok_output(
                StageflowStageResult(
                    payload=command,
                    summary={"collection_id": collection_id, "rubric_id": command.rubric_id},
                )
            )

        async def persistence_work(_ctx) -> Any:
            with self._session_factory() as session:
                collection = session.get(CollectionRecord, collection_id)
                assert collection is not None
                scenario = ScenarioRecord(
                    id=uuid4().hex,
                    collection_id=collection_id,
                    author_user_id=actor.user_id,
                    title=command.title,
                    business_context=command.business_context,
                    learner_objective=command.learner_objective,
                    constraints=command.constraints,
                    stakeholder_tensions=command.stakeholder_tensions,
                    lifecycle_state="draft",
                    target_skill_slugs=command.target_skill_slugs,
                    rubric_id=command.rubric_id,
                )
                session.add(scenario)
                session.flush()
                if command.mock_company is not None:
                    company = MockCompanyRecord(
                        id=uuid4().hex,
                        scenario_id=scenario.id,
                        name=command.mock_company.name,
                        industry=command.mock_company.industry,
                        operating_context=command.mock_company.operating_context,
                    )
                    session.add(company)
                    session.flush()
                    company_id = company.id
                else:
                    company_id = None
                for person in command.mock_people:
                    session.add(
                        MockPersonRecord(
                            id=uuid4().hex,
                            scenario_id=scenario.id,
                            mock_company_id=company_id,
                            name=person.name,
                            role=person.role,
                            goals=person.goals,
                            communication_style=person.communication_style,
                            relationship_to_scenario=person.relationship_to_scenario,
                        )
                    )
                collection.updated_at = datetime.now(UTC)
                session.commit()
                scenario_id = scenario.id

            self._events.record(
                "catalog.scenario.created.v1",
                actor.user_id,
                {"collection_id": collection_id, "scenario_id": scenario_id},
            )
            scenario_view = self._collections.get_collection(actor, collection_id).scenarios[-1]
            return ok_output(
                StageflowStageResult(
                    payload=scenario_view,
                    summary={"collection_id": collection_id, "scenario_id": scenario_id},
                )
            )

        pipeline = Pipeline.from_stages(
            stage("input_guard", cast(Any, input_guard), StageKind.GUARD),
            stage(
                "persistence_work",
                cast(Any, persistence_work),
                StageKind.WORK,
                dependencies=("input_guard",),
            ),
            name="catalog_scenario_create",
        )
        results = await run_logged_pipeline(
            self._stageflow,
            pipeline,
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id or collection_id,
            user_id=actor.user_id,
            execution_mode="catalog_authoring",
            service="soft_skills_backend.catalog",
            idempotency_key=f"catalog_scenario_create:{actor.user_id}:{request_id}:{collection_id}",
            idempotency_params=command.model_dump(mode="json"),
        )
        return payload_from_results(results, "persistence_work", expected_type=ScenarioView)
