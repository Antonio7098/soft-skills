"""Parent pipeline for generating prompt items inside an existing collection."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker
from stageflow.agent.security import PromptSecurityPolicy
from stageflow.api import Pipeline, StageKind, stage
from stageflow.core import StageContext

from soft_skills_backend.engines.config.models import CatalogGenerationRuntimeConfig
from soft_skills_backend.modules.admin.domain.prompt_registry import PromptRegistry
from soft_skills_backend.modules.admin.workflows.prompt_render_stage import (
    create_prompt_render_stage,
)
from soft_skills_backend.modules.catalog.contracts.prompt_item_commands import (
    ChatPromptItemGenerationCommand,
    PromptItemCreateCommand,
    StructuredPromptItemGenerationCommand,
)
from soft_skills_backend.modules.catalog.contracts.prompt_item_views import PromptItemGenerationView
from soft_skills_backend.modules.catalog.domain.models import (
    GeneratedPromptItemDraft,
    GeneratedPromptItemPlanBatch,
    GenerationManifest,
)
from soft_skills_backend.modules.catalog.domain.validators import (
    require_collection_owner_or_admin,
    validate_generated_prompt_item_uniqueness,
    validate_prompt_command,
    validate_prompt_item_generation_request,
)
from soft_skills_backend.modules.catalog.workflows.generation.persistence import (
    build_planner_artifact,
    build_worker_artifact,
    collection_or_error,
    persist_generated_prompt_items,
)
from soft_skills_backend.modules.catalog.workflows.generation.prompting import (
    build_prompt_item_plan_prompt_request,
    generate_prompt_item_plan_batch_from_prompt,
)
from soft_skills_backend.modules.catalog.workflows.generation.validation import (
    validate_prompt_item_plan_batch,
)
from soft_skills_backend.modules.catalog.workflows.generation.workers import (
    WorkerExecutionResult,
    run_prompt_item_workers,
)
from soft_skills_backend.modules.practice.workflows.assessment import (
    TypedLLMOutput,
    TypedLLMResult,
)
from soft_skills_backend.platform.db.models import PromptItemRecord
from soft_skills_backend.platform.observability.events import WorkflowEventRecorder
from soft_skills_backend.platform.workflows.stageflow import (
    StageflowPipelineSupport,
    StageflowStageResult,
    metadata_value,
    ok_output,
    payload_from_inputs,
    payload_from_results,
    pipeline_run_id_from_context,
    request_id_from_context,
    run_logged_pipeline,
)
from soft_skills_backend.shared.auth import Actor
from soft_skills_backend.shared.ports.llm import LLMProvider


async def generate_prompt_items_for_collection(
    *,
    actor: Actor,
    request_id: str,
    trace_id: str,
    workflow_id: str | None,
    collection_id: str,
    mode: str,
    structured_command: StructuredPromptItemGenerationCommand | None,
    chat_command: ChatPromptItemGenerationCommand | None,
    session_factory: sessionmaker[Session],
    events: WorkflowEventRecorder,
    llm_provider: LLMProvider,
    prompt_security_policy: PromptSecurityPolicy,
    stageflow: StageflowPipelineSupport,
    prompt_registry: PromptRegistry,
    config: CatalogGenerationRuntimeConfig,
    prompt_item_plan_output: TypedLLMOutput,
    prompt_item_worker_output: TypedLLMOutput,
    timeout_ms: int,
    sanitize_text: Callable[[str], str],
    compatible_prompt_item_rubric_ids: Callable[[list[str]], list[str]],
) -> PromptItemGenerationView:
    command = structured_command or cast(ChatPromptItemGenerationCommand, chat_command)

    async def input_guard(_ctx: StageContext) -> Any:
        with session_factory() as session:
            collection = collection_or_error(session, collection_id)
            require_collection_owner_or_admin(actor, collection)
            requested_skill_slugs = validate_prompt_item_generation_request(
                session, collection, command
            )
        return ok_output(
            StageflowStageResult(
                payload={
                    "collection_id": collection_id,
                    "requested_skill_slugs": requested_skill_slugs,
                },
                summary={"collection_id": collection_id, "mode": mode},
            )
        )

    async def plan_transform(ctx: StageContext) -> Any:
        with session_factory() as session:
            collection = collection_or_error(session, collection_id)
            existing_prompt_items = (
                session.query(PromptItemRecord)
                .filter(PromptItemRecord.collection_id == collection_id)
                .order_by(PromptItemRecord.created_at)
                .all()
            )
            prompt_request = build_prompt_item_plan_prompt_request(
                config=config,
                llm_provider=llm_provider,
                prompt_security_policy=prompt_security_policy,
                collection=collection,
                existing_prompt_items=existing_prompt_items,
                structured_command=structured_command,
                chat_command=chat_command,
                requested_skill_slugs=cast(dict[str, Any], payload_from_inputs(ctx, "input_guard"))[
                    "requested_skill_slugs"
                ],
                compatible_rubric_ids=compatible_prompt_item_rubric_ids(collection.rubric_ids),
                sanitize_text=sanitize_text,
            )
        return ok_output(
            StageflowStageResult(
                payload=prompt_request,
                summary={
                    "prompt_name": prompt_request.name,
                    "prompt_version": prompt_request.version,
                },
            )
        )

    async def plan_render(ctx: StageContext) -> Any:
        renderer = create_prompt_render_stage(
            prompt_registry=prompt_registry,
            request_stage_name="plan_transform",
        )
        return await renderer(ctx)

    async def plan_llm_transform(ctx: StageContext) -> Any:
        typed_result = await generate_prompt_item_plan_batch_from_prompt(
            ctx=ctx,
            structured_command=structured_command,
            config=config,
            llm_provider=llm_provider,
            prompt_item_plan_output=prompt_item_plan_output,
            rendered_prompt=payload_from_inputs(ctx, "plan_render"),
        )
        return ok_output(
            StageflowStageResult(
                payload=typed_result,
                summary={
                    "planned_prompt_items": len(
                        cast(GeneratedPromptItemPlanBatch, typed_result.parsed).prompt_items
                    )
                },
            )
        )

    async def plan_guard(ctx: StageContext) -> Any:
        typed_result = cast(TypedLLMResult, payload_from_inputs(ctx, "plan_llm_transform"))
        batch = cast(GeneratedPromptItemPlanBatch, typed_result.parsed)
        validate_prompt_item_plan_batch(
            config=config,
            llm_provider=llm_provider,
            batch=batch,
            mode=mode,
            resolved_model_slug=typed_result.model_slug,
            counts=command.counts.model_dump(mode="json"),
        )
        return ok_output(
            StageflowStageResult(
                payload=typed_result,
                summary={"planned_prompt_items": len(batch.prompt_items)},
            )
        )

    async def prompt_items_work(ctx: StageContext) -> Any:
        typed_result = cast(TypedLLMResult, payload_from_inputs(ctx, "plan_guard"))
        batch = cast(GeneratedPromptItemPlanBatch, typed_result.parsed)
        with session_factory() as session:
            collection = collection_or_error(session, collection_id)
        prompt_item_results = await run_prompt_item_workers(
            parent_ctx=ctx,
            prompt_registry=prompt_registry,
            config=config,
            llm_provider=llm_provider,
            prompt_item_worker_output=prompt_item_worker_output,
            stageflow=stageflow,
            collection_title=collection.title,
            target_audience=collection.target_audience,
            collection_difficulty=collection.difficulty,
            workplace_context=structured_command.workplace_context
            if structured_command is not None
            else collection.summary,
            prompt_item_plans=batch.prompt_items,
            timeout_ms=timeout_ms,
        )
        return ok_output(
            StageflowStageResult(
                payload=prompt_item_results,
                summary={"generated_prompt_items": len(prompt_item_results)},
            )
        )

    async def output_guard(ctx: StageContext) -> Any:
        prompt_item_results = cast(
            list[WorkerExecutionResult], payload_from_inputs(ctx, "prompt_items_work")
        )
        drafts = [
            cast(GeneratedPromptItemDraft, result.typed_result.parsed)
            for result in prompt_item_results
        ]
        commands = [PromptItemCreateCommand.model_validate(draft.model_dump()) for draft in drafts]
        with session_factory() as session:
            collection = collection_or_error(session, collection_id)
            existing_prompt_items = (
                session.query(PromptItemRecord)
                .filter(PromptItemRecord.collection_id == collection_id)
                .order_by(PromptItemRecord.created_at)
                .all()
            )
            for prompt_command in commands:
                validate_prompt_command(session, collection, prompt_command)
            validate_generated_prompt_item_uniqueness(
                existing_prompt_items=existing_prompt_items,
                generated_commands=commands,
            )
        return ok_output(
            StageflowStageResult(
                payload=drafts,
                summary={"validated_prompt_items": len(commands)},
            )
        )

    async def persistence_work(ctx: StageContext) -> Any:
        drafts = cast(list[GeneratedPromptItemDraft], payload_from_inputs(ctx, "output_guard"))
        plan_result = cast(TypedLLMResult, payload_from_inputs(ctx, "plan_guard"))
        plan_batch = cast(GeneratedPromptItemPlanBatch, plan_result.parsed)
        prompt_item_results = cast(
            list[WorkerExecutionResult], payload_from_inputs(ctx, "prompt_items_work")
        )
        manifest = GenerationManifest(
            planner=build_planner_artifact(
                provider_name=llm_provider.provider_name,
                pipeline_name=f"catalog_{mode}_planner",
                prompt_version=plan_batch.prompt_version,
                correlation_id=str(uuid4()),
                typed_result=plan_result,
                child_run_id=pipeline_run_id_from_context(ctx),
            ),
            prompt_items=[
                build_worker_artifact(
                    provider_name=llm_provider.provider_name,
                    pipeline_name="catalog_prompt_item_worker",
                    prompt_version=config.prompt_item_worker_prompt_version,
                    worker_result=result,
                )
                for result in prompt_item_results
            ],
        )
        view = persist_generated_prompt_items(
            session_factory=session_factory,
            events=events,
            config=config,
            actor=actor,
            request_id=request_id_from_context(ctx),
            trace_id=metadata_value(ctx, "trace_id"),
            workflow_id=metadata_value(ctx, "workflow_id"),
            collection_id=collection_id,
            generation_mode=mode,
            commands=drafts,
            planner_prompt_version=plan_batch.prompt_version,
            planner_provider=plan_batch.provider,
            planner_model_slug=plan_result.model_slug,
            input_payload=command.model_dump(mode="json"),
            manifest=manifest,
        )
        return ok_output(
            StageflowStageResult(
                payload=view,
                summary={
                    "collection_id": collection_id,
                    "generation_artifact_id": view.generation_artifact_id,
                },
            )
        )

    pipeline = Pipeline.from_stages(
        stage("input_guard", cast(Any, input_guard), StageKind.GUARD),
        stage(
            "plan_transform",
            cast(Any, plan_transform),
            StageKind.TRANSFORM,
            dependencies=("input_guard",),
        ),
        stage(
            "plan_render",
            cast(Any, plan_render),
            StageKind.TRANSFORM,
            dependencies=("plan_transform",),
        ),
        stage(
            "plan_llm_transform",
            cast(Any, plan_llm_transform),
            StageKind.TRANSFORM,
            dependencies=("plan_render",),
        ),
        stage(
            "plan_guard",
            cast(Any, plan_guard),
            StageKind.GUARD,
            dependencies=("plan_llm_transform",),
        ),
        stage(
            "prompt_items_work",
            cast(Any, prompt_items_work),
            StageKind.WORK,
            dependencies=("plan_guard",),
        ),
        stage(
            "output_guard",
            cast(Any, output_guard),
            StageKind.GUARD,
            dependencies=("prompt_items_work",),
        ),
        stage(
            "persistence_work",
            cast(Any, persistence_work),
            StageKind.WORK,
            dependencies=("output_guard", "plan_guard", "prompt_items_work"),
        ),
        name=f"catalog_{mode}_generation",
    )
    results = await run_logged_pipeline(
        stageflow,
        pipeline,
        request_id=request_id,
        trace_id=trace_id,
        workflow_id=workflow_id or f"{mode}:{actor.user_id}:{collection_id}:{request_id}",
        user_id=actor.user_id,
        execution_mode="catalog_generation",
        service="soft_skills_backend.catalog",
        idempotency_key=f"{mode}:{actor.user_id}:{collection_id}:{request_id}",
        idempotency_params=command.model_dump(mode="json"),
        timeout_ms=timeout_ms,
    )
    return payload_from_results(results, "persistence_work", expected_type=PromptItemGenerationView)
