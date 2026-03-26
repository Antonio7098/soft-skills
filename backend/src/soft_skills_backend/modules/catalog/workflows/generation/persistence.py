"""Persistence helpers for catalog generation workflows."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.engines.config.models import CatalogGenerationRuntimeConfig
from soft_skills_backend.modules.catalog.contracts.collection_views import CollectionGenerationView
from soft_skills_backend.modules.catalog.contracts.prompt_item_commands import (
    PromptItemCreateCommand,
)
from soft_skills_backend.modules.catalog.contracts.prompt_item_views import PromptItemGenerationView
from soft_skills_backend.modules.catalog.contracts.scenario_commands import ScenarioCreateCommand
from soft_skills_backend.modules.catalog.contracts.views import build_collection_view
from soft_skills_backend.modules.catalog.domain.models import (
    GeneratedCollectionDraft,
    GenerationManifest,
    GenerationWorkerArtifact,
)
from soft_skills_backend.modules.catalog.infra.events import CatalogEventRecorder
from soft_skills_backend.modules.catalog.workflows.generation.workers import WorkerExecutionResult
from soft_skills_backend.modules.practice.workflows.assessment import TypedLLMResult
from soft_skills_backend.platform.db.models import (
    CollectionRecord,
    ContentGenerationArtifactRecord,
    MockCompanyRecord,
    MockPersonRecord,
    PromptItemRecord,
    ScenarioRecord,
    ScenarioSupportingArtifactRecord,
)
from soft_skills_backend.shared.auth import Actor
from soft_skills_backend.shared.errors import domain_error


def persist_generated_collection(
    *,
    session_factory: sessionmaker[Session],
    events: CatalogEventRecorder,
    config: CatalogGenerationRuntimeConfig,
    actor: Actor,
    request_id: str,
    trace_id: str,
    workflow_id: str,
    generation_mode: str,
    draft: GeneratedCollectionDraft,
    input_payload: dict[str, Any],
    manifest: GenerationManifest,
    organisation_id: str | None = None,
) -> CollectionGenerationView:
    source_type = "generated_structured" if generation_mode == "structured" else "generated_chat"
    now = datetime.now(UTC)
    with session_factory() as session:
        collection = CollectionRecord(
            id=uuid4().hex,
            author_user_id=actor.user_id,
            organisation_id=organisation_id,
            title=draft.title,
            summary=draft.summary,
            target_audience=draft.target_audience,
            difficulty=draft.difficulty,
            lifecycle_state="draft",
            verification_state="unverified",
            source_type=source_type,
            last_generation_artifact_id=None,
            content_format_mix=list(draft.content_format_mix),
            target_skill_slugs=list(draft.target_skill_slugs),
            target_competency_slugs=list(draft.target_competency_slugs),
            rubric_ids=list(draft.rubric_ids),
            created_at=now,
            updated_at=now,
        )
        session.add(collection)
        session.flush()
        for prompt_item in draft.prompt_items:
            session.add(
                PromptItemRecord(
                    id=uuid4().hex,
                    collection_id=collection.id,
                    author_user_id=actor.user_id,
                    prompt_type=prompt_item.prompt_type,
                    title=prompt_item.title,
                    prompt_text=prompt_item.prompt_text,
                    difficulty=prompt_item.difficulty,
                    lifecycle_state="draft",
                    target_skill_slugs=list(prompt_item.target_skill_slugs),
                    rubric_id=prompt_item.rubric_id,
                    created_at=now,
                    updated_at=now,
                )
            )
        for scenario in draft.scenarios:
            scenario_record = ScenarioRecord(
                id=uuid4().hex,
                collection_id=collection.id,
                author_user_id=actor.user_id,
                title=scenario.title,
                business_context=scenario.business_context,
                learner_objective=scenario.learner_objective,
                constraints=list(scenario.constraints),
                stakeholder_tensions=list(scenario.stakeholder_tensions),
                lifecycle_state="draft",
                target_skill_slugs=list(scenario.target_skill_slugs),
                rubric_id=scenario.rubric_id,
                created_at=now,
                updated_at=now,
            )
            session.add(scenario_record)
            session.flush()
            persist_scenario_children(
                session,
                scenario_record.id,
                ScenarioCreateCommand.model_validate(scenario.model_dump()),
            )
        artifact = ContentGenerationArtifactRecord(
            id=uuid4().hex,
            collection_id=collection.id,
            author_user_id=actor.user_id,
            generation_mode=generation_mode,
            prompt_version=draft.prompt_version,
            schema_version=config.output_schema_version,
            config_version=config.config_version,
            provider=draft.provider,
            model_slug=draft.model_slug,
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id,
            input_payload=input_payload,
            output_payload={
                "draft": draft.model_dump(mode="json"),
                "manifest": manifest.model_dump(mode="json"),
            },
            raw_payload=manifest.model_dump(mode="json"),
            created_at=now,
        )
        session.add(artifact)
        session.flush()
        collection.last_generation_artifact_id = artifact.id
        session.commit()
        collection_view = build_collection_view(session, collection, actor=actor)
        artifact_id = artifact.id
    events.record(
        "catalog.collection.created.v1",
        request_id=request_id,
        trace_id=trace_id,
        workflow_id=workflow_id,
        payload={
            "collection_id": collection_view.id,
            "author_user_id": actor.user_id,
            "source_type": source_type,
            "generation_artifact_id": artifact_id,
        },
    )
    events.record(
        "content.draft.generated.v1",
        request_id=request_id,
        trace_id=trace_id,
        workflow_id=workflow_id,
        payload={
            "collection_id": collection_view.id,
            "generation_artifact_id": artifact_id,
            "generation_mode": generation_mode,
            "prompt_version": draft.prompt_version,
            "provider": draft.provider,
            "model_slug": draft.model_slug,
        },
    )
    return CollectionGenerationView(
        collection=collection_view,
        generation_artifact_id=artifact_id,
        generation_mode=generation_mode,
        prompt_version=draft.prompt_version,
        provider=draft.provider,
        model_slug=draft.model_slug,
    )


def persist_generated_prompt_items(
    *,
    session_factory: sessionmaker[Session],
    events: CatalogEventRecorder,
    config: CatalogGenerationRuntimeConfig,
    actor: Actor,
    request_id: str,
    trace_id: str,
    workflow_id: str,
    collection_id: str,
    generation_mode: str,
    commands: list[PromptItemCreateCommand],
    planner_prompt_version: str,
    planner_provider: str,
    planner_model_slug: str,
    input_payload: dict[str, Any],
    manifest: GenerationManifest,
) -> PromptItemGenerationView:
    now = datetime.now(UTC)
    created_prompt_ids: list[str] = []
    with session_factory() as session:
        collection = collection_or_error(session, collection_id)
        for command in commands:
            record = PromptItemRecord(
                id=uuid4().hex,
                collection_id=collection_id,
                author_user_id=actor.user_id,
                prompt_type=command.prompt_type,
                title=command.title,
                prompt_text=command.prompt_text,
                difficulty=command.difficulty,
                lifecycle_state="draft",
                target_skill_slugs=list(command.target_skill_slugs),
                rubric_id=command.rubric_id,
                created_at=now,
                updated_at=now,
            )
            session.add(record)
            created_prompt_ids.append(record.id)
        artifact = ContentGenerationArtifactRecord(
            id=uuid4().hex,
            collection_id=collection_id,
            author_user_id=actor.user_id,
            generation_mode=generation_mode,
            prompt_version=planner_prompt_version,
            schema_version=config.output_schema_version,
            config_version=config.config_version,
            provider=planner_provider,
            model_slug=planner_model_slug,
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id,
            input_payload=input_payload,
            output_payload={
                "prompt_items": [command.model_dump(mode="json") for command in commands],
                "manifest": manifest.model_dump(mode="json"),
            },
            raw_payload=manifest.model_dump(mode="json"),
            created_at=now,
        )
        session.add(artifact)
        session.flush()
        collection.last_generation_artifact_id = artifact.id
        collection.updated_at = now
        session.commit()
        collection_view = build_collection_view(session, collection, actor=actor)
        generated_prompt_items = [
            prompt_item
            for prompt_item in collection_view.prompt_items
            if prompt_item.id in set(created_prompt_ids)
        ]
        artifact_id = artifact.id
    for prompt_item_id in created_prompt_ids:
        events.record(
            "catalog.prompt_item.created.v1",
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id,
            payload={"collection_id": collection_id, "prompt_item_id": prompt_item_id},
        )
    events.record(
        "content.draft.generated.v1",
        request_id=request_id,
        trace_id=trace_id,
        workflow_id=workflow_id,
        payload={
            "collection_id": collection_id,
            "generation_artifact_id": artifact_id,
            "generation_mode": generation_mode,
            "prompt_version": planner_prompt_version,
            "provider": planner_provider,
            "model_slug": planner_model_slug,
        },
    )
    return PromptItemGenerationView(
        collection=collection_view,
        prompt_items=generated_prompt_items,
        generation_artifact_id=artifact_id,
        generation_mode=generation_mode,
        prompt_version=planner_prompt_version,
        provider=planner_provider,
        model_slug=planner_model_slug,
    )


def collection_or_error(session: Session, collection_id: str) -> CollectionRecord:
    collection = session.get(CollectionRecord, collection_id)
    if collection is None:
        raise domain_error(
            "Collection was not found",
            code="SS-DOMAIN-028",
            details={"collection_id": collection_id},
        )
    return collection


def build_planner_artifact(
    *,
    provider_name: str,
    pipeline_name: str,
    prompt_version: str,
    correlation_id: str,
    typed_result: TypedLLMResult,
    child_run_id: str,
) -> GenerationWorkerArtifact:
    return GenerationWorkerArtifact(
        pipeline_name=pipeline_name,
        child_run_id=child_run_id,
        correlation_id=correlation_id,
        prompt_version=prompt_version,
        provider=provider_name,
        model_slug=typed_result.model_slug,
        usage=dict(typed_result.usage),
        output_payload=typed_result.parsed.model_dump(mode="json"),
        raw_payload=typed_result.raw_payload,
    )


def build_worker_artifact(
    *,
    provider_name: str,
    pipeline_name: str,
    prompt_version: str,
    worker_result: WorkerExecutionResult,
) -> GenerationWorkerArtifact:
    return GenerationWorkerArtifact(
        pipeline_name=pipeline_name,
        child_run_id=worker_result.child_run_id,
        correlation_id=worker_result.correlation_id,
        prompt_version=prompt_version,
        provider=provider_name,
        model_slug=worker_result.typed_result.model_slug,
        usage=dict(worker_result.typed_result.usage),
        output_payload=worker_result.typed_result.parsed.model_dump(mode="json"),
        raw_payload=worker_result.typed_result.raw_payload,
    )


def persist_scenario_children(
    session: Session,
    scenario_id: str,
    command: ScenarioCreateCommand,
) -> None:
    if command.mock_company is not None:
        company = MockCompanyRecord(
            id=uuid4().hex,
            scenario_id=scenario_id,
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
                scenario_id=scenario_id,
                mock_company_id=company_id,
                name=person.name,
                role=person.role,
                goals=list(person.goals),
                communication_style=person.communication_style,
                relationship_to_scenario=person.relationship_to_scenario,
            )
        )
    for artifact in command.supporting_artifacts:
        session.add(
            ScenarioSupportingArtifactRecord(
                id=uuid4().hex,
                scenario_id=scenario_id,
                artifact_type=artifact.artifact_type,
                title=artifact.title,
                body=artifact.body,
                created_at=datetime.now(UTC),
            )
        )
