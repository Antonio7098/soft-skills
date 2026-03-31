"""Parent pipeline for modular collection generation."""

from __future__ import annotations

import asyncio
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
from soft_skills_backend.modules.catalog.contracts.collection_commands import (
    ChatCollectionGenerationCommand,
    StructuredCollectionGenerationCommand,
)
from soft_skills_backend.modules.catalog.contracts.collection_views import CollectionGenerationView
from soft_skills_backend.modules.catalog.domain.models import (
    GeneratedCollectionBlueprint,
    GeneratedCollectionDraft,
    GeneratedPromptItemDraft,
    GeneratedScenarioDraft,
    GenerationManifest,
)
from soft_skills_backend.modules.catalog.domain.validators import validate_generation_request
from soft_skills_backend.modules.catalog.infra.realtime import GenerationExecution
from soft_skills_backend.modules.catalog.workflows.generation.persistence import (
    build_planner_artifact,
    build_worker_artifact,
    persist_generated_collection,
)
from soft_skills_backend.modules.catalog.workflows.generation.prompting import (
    build_collection_blueprint_prompt_request,
    generate_collection_blueprint_from_prompt,
)
from soft_skills_backend.modules.catalog.workflows.generation.validation import (
    validate_collection_blueprint,
    validate_generated_collection_draft,
)
from soft_skills_backend.modules.catalog.workflows.generation.workers import (
    WorkerExecutionResult,
    run_prompt_item_workers,
    run_scenario_workers,
)
from soft_skills_backend.modules.practice.workflows.assessment import (
    TypedLLMOutput,
    TypedLLMResult,
)
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


async def generate_collection(
    *,
    actor: Actor,
    request_id: str,
    trace_id: str,
    workflow_id: str | None,
    mode: str,
    structured_command: StructuredCollectionGenerationCommand | None,
    chat_command: ChatCollectionGenerationCommand | None,
    session_factory: sessionmaker[Session],
    events: WorkflowEventRecorder,
    llm_provider: LLMProvider,
    prompt_security_policy: PromptSecurityPolicy,
    stageflow: StageflowPipelineSupport,
    prompt_registry: PromptRegistry,
    config: CatalogGenerationRuntimeConfig,
    blueprint_output: TypedLLMOutput,
    prompt_item_worker_output: TypedLLMOutput,
    scenario_shell_worker_output: TypedLLMOutput,
    scenario_question_worker_output: TypedLLMOutput,
    timeout_ms: int,
    sanitize_text: Callable[[str], str],
    workplace_context_for_commands: Callable[
        [StructuredCollectionGenerationCommand | None, ChatCollectionGenerationCommand | None], str
    ],
    taxonomy_context_for_commands: Callable[
        [Actor, StructuredCollectionGenerationCommand | None, ChatCollectionGenerationCommand | None], str
    ],
    progress_callback: Callable[[str, float, dict[str, object]], None] | None = None,
    execution: GenerationExecution | None = None,
) -> CollectionGenerationView:
    assert structured_command is not None or chat_command is not None
    command = structured_command or cast(ChatCollectionGenerationCommand, chat_command)

    def _cancel_output() -> Any:
        from stageflow.core import StageOutput

        return StageOutput.cancel(
            reason=(execution.cancel_reason if execution is not None else None) or "user_requested",
            data={
                "payload": {"status": "cancelled"},
                "summary": {"status": "cancelled"},
            },
        )

    async def _yield_for_cancel() -> Any | None:
        if execution is None:
            return None
        if execution.is_cancelled:
            return _cancel_output()
        # Give the websocket control path a brief chance to deliver a real user cancel
        # before starting the next expensive LLM fan-out stage.
        await asyncio.sleep(0.15)
        if execution.is_cancelled:
            return _cancel_output()
        return None

    async def input_guard(_ctx: StageContext) -> Any:
        if execution is not None and execution.is_cancelled:
            return _cancel_output()
        if progress_callback:
            progress_callback("input_guard", 5.0, {"difficulty": command.difficulty, "mode": mode})
        with session_factory() as session:
            validate_generation_request(session, command)
        return ok_output(
            StageflowStageResult(
                payload=command,
                summary={"difficulty": command.difficulty, "mode": mode},
            )
        )

    async def blueprint_transform(ctx: StageContext) -> Any:
        prompt_request = build_collection_blueprint_prompt_request(
            config=config,
            llm_provider=llm_provider,
            prompt_security_policy=prompt_security_policy,
            structured_command=structured_command,
            chat_command=chat_command,
            taxonomy_context=taxonomy_context_for_commands(actor, structured_command, chat_command),
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

    async def blueprint_render(ctx: StageContext) -> Any:
        renderer = create_prompt_render_stage(
            prompt_registry=prompt_registry,
            request_stage_name="blueprint_transform",
        )
        return await renderer(ctx)

    async def blueprint_llm_transform(ctx: StageContext) -> Any:
        typed_result = await generate_collection_blueprint_from_prompt(
            ctx=ctx,
            config=config,
            llm_provider=llm_provider,
            blueprint_output=blueprint_output,
            rendered_prompt=payload_from_inputs(ctx, "blueprint_render"),
            structured_command=structured_command,
        )
        if progress_callback:
            blueprint = cast(GeneratedCollectionBlueprint, typed_result.parsed)
            progress_callback(
                "blueprint_llm_transform",
                15.0,
                {
                    "mode": mode,
                    "title": blueprint.title,
                    "summary": blueprint.summary,
                    "prompt_items_count": len(blueprint.prompt_items),
                    "scenarios_count": len(blueprint.scenarios),
                    "model_slug": typed_result.model_slug,
                },
            )
        return ok_output(
            StageflowStageResult(
                payload=typed_result,
                summary={"mode": mode, "model_slug": typed_result.model_slug},
            )
        )

    async def blueprint_guard(ctx: StageContext) -> Any:
        if progress_callback:
            progress_callback("blueprint_guard", 20.0, {})
        typed_result = cast(TypedLLMResult, payload_from_inputs(ctx, "blueprint_llm_transform"))
        blueprint = cast(GeneratedCollectionBlueprint, typed_result.parsed)
        validate_collection_blueprint(
            config=config,
            llm_provider=llm_provider,
            blueprint=blueprint,
            resolved_model_slug=typed_result.model_slug,
            structured_command=structured_command,
            chat_command=chat_command,
        )
        return ok_output(
            StageflowStageResult(
                payload=typed_result,
                summary={
                    "prompt_items": len(blueprint.prompt_items),
                    "scenarios": len(blueprint.scenarios),
                },
            )
        )

    async def prompt_items_work(ctx: StageContext) -> Any:
        if progress_callback:
            progress_callback("prompt_items_work", 35.0, {})
        cancel_output = await _yield_for_cancel()
        if cancel_output is not None:
            return cancel_output
        typed_result = cast(TypedLLMResult, payload_from_inputs(ctx, "blueprint_guard"))
        blueprint = cast(GeneratedCollectionBlueprint, typed_result.parsed)
        prompt_item_results = await run_prompt_item_workers(
            parent_ctx=ctx,
            prompt_registry=prompt_registry,
            config=config,
            llm_provider=llm_provider,
            prompt_item_worker_output=prompt_item_worker_output,
            stageflow=stageflow,
            collection_title=blueprint.title,
            target_audience=command.target_audience,
            collection_difficulty=command.difficulty,
            workplace_context=workplace_context_for_commands(structured_command, chat_command),
            prompt_item_plans=blueprint.prompt_items,
            timeout_ms=timeout_ms,
        )
        if progress_callback:
            prompt_items = [
                {
                    "title": cast(GeneratedPromptItemDraft, result.typed_result.parsed).title,
                    "prompt_type": cast(
                        GeneratedPromptItemDraft, result.typed_result.parsed
                    ).prompt_type,
                    "difficulty": cast(
                        GeneratedPromptItemDraft, result.typed_result.parsed
                    ).difficulty,
                }
                for result in prompt_item_results
            ]
            progress_callback(
                "prompt_items_work",
                50.0,
                {
                    "generated_prompt_items": len(prompt_item_results),
                    "prompt_items": prompt_items,
                },
            )
        return ok_output(
            StageflowStageResult(
                payload=prompt_item_results,
                summary={"generated_prompt_items": len(prompt_item_results)},
            )
        )

    async def scenarios_work(ctx: StageContext) -> Any:
        if progress_callback:
            progress_callback("scenarios_work", 55.0, {})
        cancel_output = await _yield_for_cancel()
        if cancel_output is not None:
            return cancel_output
        typed_result = cast(TypedLLMResult, payload_from_inputs(ctx, "blueprint_guard"))
        blueprint = cast(GeneratedCollectionBlueprint, typed_result.parsed)
        scenario_results = await run_scenario_workers(
            parent_ctx=ctx,
            prompt_registry=prompt_registry,
            config=config,
            llm_provider=llm_provider,
            scenario_shell_worker_output=scenario_shell_worker_output,
            scenario_question_worker_output=scenario_question_worker_output,
            stageflow=stageflow,
            collection_title=blueprint.title,
            target_audience=command.target_audience,
            collection_difficulty=command.difficulty,
            workplace_context=workplace_context_for_commands(structured_command, chat_command),
            scenario_plans=blueprint.scenarios,
            timeout_ms=timeout_ms,
        )
        if progress_callback:
            progress_callback(
                "scenarios_work", 65.0, {"generated_scenarios": len(scenario_results)}
            )
        return ok_output(
            StageflowStageResult(
                payload=scenario_results,
                summary={"generated_scenarios": len(scenario_results)},
            )
        )

    async def assemble_transform(ctx: StageContext) -> Any:
        if progress_callback:
            progress_callback("assemble_transform", 75.0, {})
        typed_result = cast(TypedLLMResult, payload_from_inputs(ctx, "blueprint_guard"))
        blueprint = cast(GeneratedCollectionBlueprint, typed_result.parsed)
        prompt_item_results = cast(
            list[WorkerExecutionResult], payload_from_inputs(ctx, "prompt_items_work")
        )
        scenario_results = cast(
            list[WorkerExecutionResult], payload_from_inputs(ctx, "scenarios_work")
        )
        draft = GeneratedCollectionDraft(
            prompt_version=blueprint.prompt_version,
            provider=blueprint.provider,
            model_slug=typed_result.model_slug,
            title=blueprint.title,
            summary=blueprint.summary,
            target_audience=command.target_audience,
            difficulty=command.difficulty,
            content_format_mix=list(command.content_format_mix),
            target_skill_slugs=list(command.target_skill_slugs),
            target_competency_slugs=list(command.target_competency_slugs),
            rubric_ids=list(command.rubric_ids),
            prompt_items=[
                cast(GeneratedPromptItemDraft, result.typed_result.parsed)
                for result in prompt_item_results
            ],
            scenarios=[
                cast(GeneratedScenarioDraft, result.typed_result.parsed)
                for result in scenario_results
            ],
        )
        return ok_output(
            StageflowStageResult(
                payload=draft,
                summary={
                    "prompt_items": len(draft.prompt_items),
                    "scenarios": len(draft.scenarios),
                },
            )
        )

    async def output_guard(ctx: StageContext) -> Any:
        if progress_callback:
            progress_callback("output_guard", 85.0, {})
        draft = cast(GeneratedCollectionDraft, payload_from_inputs(ctx, "assemble_transform"))
        with session_factory() as session:
            validate_generated_collection_draft(
                session,
                config=config,
                draft=draft,
                structured_command=structured_command,
                chat_command=chat_command,
            )
        return ok_output(
            StageflowStageResult(
                payload=draft,
                summary={"title": draft.title},
            )
        )

    async def persistence_work(ctx: StageContext) -> Any:
        if progress_callback:
            progress_callback("persistence_work", 90.0, {})
        draft = cast(GeneratedCollectionDraft, payload_from_inputs(ctx, "output_guard"))
        blueprint_result = cast(TypedLLMResult, payload_from_inputs(ctx, "blueprint_guard"))
        prompt_item_results = cast(
            list[WorkerExecutionResult], payload_from_inputs(ctx, "prompt_items_work")
        )
        scenario_results = cast(
            list[WorkerExecutionResult], payload_from_inputs(ctx, "scenarios_work")
        )
        manifest = GenerationManifest(
            planner=build_planner_artifact(
                provider_name=llm_provider.provider_name,
                pipeline_name=f"catalog_{mode}_blueprint",
                prompt_version=draft.prompt_version,
                correlation_id=str(uuid4()),
                typed_result=blueprint_result,
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
            scenarios=[
                build_worker_artifact(
                    provider_name=llm_provider.provider_name,
                    pipeline_name="catalog_scenario_generation",
                    prompt_version=config.scenario_shell_worker_prompt_version,
                    worker_result=result,
                )
                for result in scenario_results
            ],
        )
        view = persist_generated_collection(
            session_factory=session_factory,
            events=events,
            config=config,
            actor=actor,
            request_id=request_id_from_context(ctx),
            trace_id=metadata_value(ctx, "trace_id"),
            workflow_id=metadata_value(ctx, "workflow_id"),
            generation_mode=mode,
            draft=draft,
            input_payload=command.model_dump(mode="json"),
            manifest=manifest,
            organisation_id=getattr(command, "organisation_id", None) or actor.organisation_id,
        )
        if progress_callback:
            progress_callback(
                "persistence_work",
                100.0,
                {
                    "collection_id": str(view.collection.id),
                    "generation_artifact_id": view.generation_artifact_id,
                },
            )
        return ok_output(
            StageflowStageResult(
                payload=view,
                summary={
                    "collection_id": view.collection.id,
                    "generation_artifact_id": view.generation_artifact_id,
                },
            )
        )

    pipeline = Pipeline.from_stages(
        stage("input_guard", cast(Any, input_guard), StageKind.GUARD),
        stage(
            "blueprint_transform",
            cast(Any, blueprint_transform),
            StageKind.TRANSFORM,
            dependencies=("input_guard",),
        ),
        stage(
            "blueprint_render",
            cast(Any, blueprint_render),
            StageKind.TRANSFORM,
            dependencies=("blueprint_transform",),
        ),
        stage(
            "blueprint_llm_transform",
            cast(Any, blueprint_llm_transform),
            StageKind.TRANSFORM,
            dependencies=("blueprint_render",),
        ),
        stage(
            "blueprint_guard",
            cast(Any, blueprint_guard),
            StageKind.GUARD,
            dependencies=("blueprint_llm_transform",),
        ),
        stage(
            "prompt_items_work",
            cast(Any, prompt_items_work),
            StageKind.WORK,
            dependencies=("blueprint_guard",),
        ),
        stage(
            "scenarios_work",
            cast(Any, scenarios_work),
            StageKind.WORK,
            dependencies=("blueprint_guard",),
        ),
        stage(
            "assemble_transform",
            cast(Any, assemble_transform),
            StageKind.TRANSFORM,
            dependencies=("blueprint_guard", "prompt_items_work", "scenarios_work"),
        ),
        stage(
            "output_guard",
            cast(Any, output_guard),
            StageKind.GUARD,
            dependencies=("assemble_transform",),
        ),
        stage(
            "persistence_work",
            cast(Any, persistence_work),
            StageKind.WORK,
            dependencies=("output_guard", "blueprint_guard", "prompt_items_work", "scenarios_work"),
        ),
        name=f"catalog_{mode}_generation",
    )
    resolved_workflow_id = workflow_id or f"catalog-{mode}-generation:{actor.user_id}:{request_id}"
    events.record(
        "catalog.generation.started.v1",
        request_id=request_id,
        trace_id=trace_id,
        workflow_id=resolved_workflow_id,
        payload={
            "mode": mode,
            "actor_user_id": actor.user_id,
            "command": command.model_dump(mode="json"),
        },
    )
    try:
        def on_context_ready(pipeline_ctx: Any) -> None:
            if execution is None:
                return
            execution.pipeline_context = pipeline_ctx
            if execution.is_cancelled:
                pipeline_ctx.mark_canceled()

        results = await run_logged_pipeline(
            stageflow,
            pipeline,
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=resolved_workflow_id,
            user_id=actor.user_id,
            execution_mode="catalog_generation",
            service="soft_skills_backend.catalog",
            idempotency_key=f"catalog_{mode}_generation:{actor.user_id}:{request_id}",
            idempotency_params=command.model_dump(mode="json"),
            timeout_ms=timeout_ms,
            on_context_ready=on_context_ready,
        )
        events.record(
            "catalog.generation.completed.v1",
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=resolved_workflow_id,
            payload={"mode": mode},
        )
        return payload_from_results(
            results, "persistence_work", expected_type=CollectionGenerationView
        )
    except Exception as exc:
        events.record(
            "catalog.generation.failed.v1",
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=resolved_workflow_id,
            payload={"mode": mode, "error": str(exc)},
        )
        raise
    finally:
        if execution is not None:
            execution.pipeline_context = None
