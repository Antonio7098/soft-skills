"""Worker fan-out helpers for catalog generation workflows."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, cast
from uuid import uuid4

from stageflow.api import Pipeline, StageKind, stage
from stageflow.core import StageContext

from soft_skills_backend.engines.config.models import CatalogGenerationRuntimeConfig
from soft_skills_backend.modules.admin.domain.prompt_registry import PromptRegistry
from soft_skills_backend.modules.admin.workflows.prompt_render_stage import (
    PromptRenderRequest,
    create_prompt_render_stage,
)
from soft_skills_backend.modules.catalog.domain.constants import ALLOWED_SCENARIO_ARTIFACT_TYPES
from soft_skills_backend.modules.catalog.domain.models import (
    GeneratedPromptItemDraft,
    GeneratedPromptItemPlan,
    GeneratedScenarioDraft,
    GeneratedScenarioPlan,
)
from soft_skills_backend.modules.practice.workflows.assessment import (
    TypedLLMOutput,
    TypedLLMResult,
)
from soft_skills_backend.platform.providers.llm.prompts import (
    CREATOR_PROMPT_ITEM_OUTPUT_FORMAT,
    CREATOR_SCENARIO_OUTPUT_FORMAT,
)
from soft_skills_backend.platform.workflows.stageflow import (
    StageflowPipelineSupport,
    StageflowStageResult,
    metadata_value,
    ok_output,
    payload_from_inputs,
    pipeline_run_id_from_context,
    request_id_from_context,
    run_logged_subpipeline,
    user_id_from_context,
)
from soft_skills_backend.shared.errors import validation_error
from soft_skills_backend.shared.ports.llm import LLMProvider
from soft_skills_backend.shared.ports.telemetry import ProviderCallContext


def _normalize_prompt_item_skills(prompt_type: str, target_skill_slugs: list[str]) -> list[str]:
    if prompt_type == "quick_practice_prompt":
        return []
    return list(target_skill_slugs)


@dataclass(slots=True)
class WorkerExecutionResult:
    typed_result: TypedLLMResult
    child_run_id: str
    correlation_id: str


async def run_prompt_item_workers(
    *,
    parent_ctx: Any,
    prompt_registry: PromptRegistry,
    config: CatalogGenerationRuntimeConfig,
    llm_provider: LLMProvider,
    prompt_item_worker_output: TypedLLMOutput,
    stageflow: StageflowPipelineSupport,
    collection_title: str,
    target_audience: str,
    collection_difficulty: str,
    workplace_context: str,
    prompt_item_plans: list[GeneratedPromptItemPlan],
    timeout_ms: int,
) -> list[WorkerExecutionResult]:
    semaphore = asyncio.Semaphore(max(1, config.max_parallel_prompt_item_children))

    async def run_worker(index: int, plan: GeneratedPromptItemPlan) -> WorkerExecutionResult:
        async with semaphore:
            return await _run_prompt_item_worker(
                parent_ctx=parent_ctx,
                prompt_registry=prompt_registry,
                config=config,
                llm_provider=llm_provider,
                prompt_item_worker_output=prompt_item_worker_output,
                stageflow=stageflow,
                collection_title=collection_title,
                target_audience=target_audience,
                collection_difficulty=collection_difficulty,
                workplace_context=workplace_context,
                plan=plan,
                worker_index=index,
                timeout_ms=timeout_ms,
            )

    results = await asyncio.gather(
        *(run_worker(index, plan) for index, plan in enumerate(prompt_item_plans, start=1))
    )
    return list(results)


async def run_scenario_workers(
    *,
    parent_ctx: Any,
    prompt_registry: PromptRegistry,
    config: CatalogGenerationRuntimeConfig,
    llm_provider: LLMProvider,
    scenario_worker_output: TypedLLMOutput,
    stageflow: StageflowPipelineSupport,
    collection_title: str,
    target_audience: str,
    collection_difficulty: str,
    workplace_context: str,
    scenario_plans: list[GeneratedScenarioPlan],
    timeout_ms: int,
) -> list[WorkerExecutionResult]:
    semaphore = asyncio.Semaphore(max(1, config.max_parallel_scenario_children))

    async def run_worker(index: int, plan: GeneratedScenarioPlan) -> WorkerExecutionResult:
        async with semaphore:
            return await _run_scenario_worker(
                parent_ctx=parent_ctx,
                prompt_registry=prompt_registry,
                config=config,
                llm_provider=llm_provider,
                scenario_worker_output=scenario_worker_output,
                stageflow=stageflow,
                collection_title=collection_title,
                target_audience=target_audience,
                collection_difficulty=collection_difficulty,
                workplace_context=workplace_context,
                plan=plan,
                worker_index=index,
                timeout_ms=timeout_ms,
            )

    results = await asyncio.gather(
        *(run_worker(index, plan) for index, plan in enumerate(scenario_plans, start=1))
    )
    return list(results)


async def _run_prompt_item_worker(
    *,
    parent_ctx: Any,
    prompt_registry: PromptRegistry,
    config: CatalogGenerationRuntimeConfig,
    llm_provider: LLMProvider,
    prompt_item_worker_output: TypedLLMOutput,
    stageflow: StageflowPipelineSupport,
    collection_title: str,
    target_audience: str,
    collection_difficulty: str,
    workplace_context: str,
    plan: GeneratedPromptItemPlan,
    worker_index: int,
    timeout_ms: int,
) -> WorkerExecutionResult:
    correlation_id = uuid4()

    async def input_guard(_ctx: StageContext) -> Any:
        return ok_output(
            StageflowStageResult(
                payload=plan,
                summary={"prompt_type": plan.prompt_type, "rubric_id": plan.rubric_id},
            )
        )

    async def prompt_request_transform(_ctx: StageContext) -> Any:
        prompt_request = PromptRenderRequest(
            name=config.prompt_item_worker_prompt_name,
            version=config.prompt_item_worker_prompt_version,
            variables={
                "collection_title": collection_title,
                "target_audience": target_audience,
                "collection_difficulty": collection_difficulty,
                "workplace_context": workplace_context,
                "prompt_type": plan.prompt_type,
                "difficulty": plan.difficulty,
                "target_skill_slugs": ", ".join(plan.target_skill_slugs),
                "rubric_id": plan.rubric_id,
                "title_hint": plan.title_hint,
                "generation_brief": plan.generation_brief,
                "output_format": CREATOR_PROMPT_ITEM_OUTPUT_FORMAT,
            },
        )
        return ok_output(
            StageflowStageResult(
                payload=prompt_request,
                summary={"prompt_name": prompt_request.name, "prompt_version": prompt_request.version},
            )
        )

    async def prompt_render_transform(ctx: StageContext) -> Any:
        renderer = create_prompt_render_stage(
            prompt_registry=prompt_registry,
            request_stage_name="prompt_request_transform",
        )
        return await renderer(ctx)

    async def llm_transform(ctx: StageContext) -> Any:
        rendered_prompt = payload_from_inputs(ctx, "prompt_render_transform")
        typed_result = await prompt_item_worker_output.generate(
            llm_provider,
            messages=[
                {
                    "role": "system",
                    "content": "Generate one realistic SoftSkills prompt item. Return JSON only.",
                },
                {"role": "user", "content": rendered_prompt.content},
            ],
            call_context=ProviderCallContext(
                operation="catalog_prompt_item_worker_generation",
                request_id=request_id_from_context(ctx),
                trace_id=metadata_value(ctx, "trace_id"),
                pipeline_run_id=pipeline_run_id_from_context(ctx),
                workflow_id=metadata_value(ctx, "workflow_id"),
                user_id=user_id_from_context(ctx),
            ),
        )
        return ok_output(
            StageflowStageResult(
                payload=typed_result, summary={"model_slug": typed_result.model_slug}
            )
        )

    async def output_guard(ctx: StageContext) -> Any:
        typed_result = cast(TypedLLMResult, payload_from_inputs(ctx, "llm_transform"))
        draft = cast(GeneratedPromptItemDraft, typed_result.parsed)
        draft.target_skill_slugs = _normalize_prompt_item_skills(
            draft.prompt_type, draft.target_skill_slugs
        )
        if draft.prompt_type != plan.prompt_type or draft.rubric_id != plan.rubric_id:
            raise validation_error(
                "Generated prompt item drifted from the worker plan metadata",
                code="SS-VALIDATION-067",
                details={
                    "expected_prompt_type": plan.prompt_type,
                    "expected_rubric_id": plan.rubric_id,
                },
            )
        if draft.prompt_type == "quick_practice_prompt":
            if draft.generated_rubric is None:
                raise validation_error(
                    "Generated quick-practice prompt item must include a question-specific rubric",
                    code="SS-VALIDATION-078",
                    details={"title": draft.title, "rubric_id": draft.rubric_id},
                )
        elif draft.generated_rubric is not None:
            raise validation_error(
                "Only quick-practice prompt items may include a generated rubric payload",
                code="SS-VALIDATION-079",
                details={"prompt_type": draft.prompt_type, "title": draft.title},
            )
        return ok_output(
            StageflowStageResult(
                payload=typed_result,
                summary={"prompt_type": draft.prompt_type, "title": draft.title},
            )
        )

    pipeline = Pipeline.from_stages(
        stage("input_guard", cast(Any, input_guard), StageKind.GUARD),
        stage(
            "prompt_request_transform",
            cast(Any, prompt_request_transform),
            StageKind.TRANSFORM,
            dependencies=("input_guard",),
        ),
        stage(
            "prompt_render_transform",
            cast(Any, prompt_render_transform),
            StageKind.TRANSFORM,
            dependencies=("prompt_request_transform",),
        ),
        stage(
            "llm_transform",
            cast(Any, llm_transform),
            StageKind.TRANSFORM,
            dependencies=("prompt_render_transform",),
        ),
        stage(
            "output_guard",
            cast(Any, output_guard),
            StageKind.GUARD,
            dependencies=("llm_transform",),
        ),
        name="catalog_prompt_item_worker",
    )
    result = await run_logged_subpipeline(
        stageflow,
        parent_ctx=parent_ctx,
        parent_stage_name=parent_ctx.stage_name,
        correlation_id=correlation_id,
        pipeline=pipeline,
        result_stage_name="output_guard",
        execution_mode="catalog_generation_worker",
        service="soft_skills_backend.catalog",
        idempotency_key=f"catalog_prompt_item_worker:{request_id_from_context(parent_ctx)}:{worker_index}",
        idempotency_params=plan.model_dump(mode="json"),
        timeout_ms=timeout_ms,
    )
    if not result.success or result.data is None:
        raise validation_error(
            "Prompt-item worker pipeline failed",
            code="SS-VALIDATION-068",
            details={"worker_index": worker_index, "reason": result.error},
        )
    typed_result = cast(TypedLLMResult, result.data["payload"])
    return WorkerExecutionResult(
        typed_result=typed_result,
        child_run_id=str(result.child_run_id),
        correlation_id=str(correlation_id),
    )


async def _run_scenario_worker(
    *,
    parent_ctx: Any,
    prompt_registry: PromptRegistry,
    config: CatalogGenerationRuntimeConfig,
    llm_provider: LLMProvider,
    scenario_worker_output: TypedLLMOutput,
    stageflow: StageflowPipelineSupport,
    collection_title: str,
    target_audience: str,
    collection_difficulty: str,
    workplace_context: str,
    plan: GeneratedScenarioPlan,
    worker_index: int,
    timeout_ms: int,
) -> WorkerExecutionResult:
    correlation_id = uuid4()

    async def input_guard(_ctx: StageContext) -> Any:
        return ok_output(StageflowStageResult(payload=plan, summary={"rubric_id": plan.rubric_id}))

    async def prompt_request_transform(_ctx: StageContext) -> Any:
        prompt_request = PromptRenderRequest(
            name=config.scenario_worker_prompt_name,
            version=config.scenario_worker_prompt_version,
            variables={
                "collection_title": collection_title,
                "target_audience": target_audience,
                "collection_difficulty": collection_difficulty,
                "workplace_context": workplace_context,
                "target_skill_slugs": ", ".join(plan.target_skill_slugs),
                "rubric_id": plan.rubric_id,
                "supporting_artifact_count": plan.supporting_artifact_count,
                "allowed_artifact_types": ", ".join(sorted(ALLOWED_SCENARIO_ARTIFACT_TYPES)),
                "title_hint": plan.title_hint,
                "generation_brief": plan.generation_brief,
                "output_format": CREATOR_SCENARIO_OUTPUT_FORMAT,
            },
        )
        return ok_output(
            StageflowStageResult(
                payload=prompt_request,
                summary={"prompt_name": prompt_request.name, "prompt_version": prompt_request.version},
            )
        )

    async def prompt_render_transform(ctx: StageContext) -> Any:
        renderer = create_prompt_render_stage(
            prompt_registry=prompt_registry,
            request_stage_name="prompt_request_transform",
        )
        return await renderer(ctx)

    async def llm_transform(ctx: StageContext) -> Any:
        rendered_prompt = payload_from_inputs(ctx, "prompt_render_transform")
        typed_result = await scenario_worker_output.generate(
            llm_provider,
            messages=[
                {
                    "role": "system",
                    "content": "Generate one realistic SoftSkills scenario draft. Return JSON only.",
                },
                {"role": "user", "content": rendered_prompt.content},
            ],
            call_context=ProviderCallContext(
                operation="catalog_scenario_worker_generation",
                request_id=request_id_from_context(ctx),
                trace_id=metadata_value(ctx, "trace_id"),
                pipeline_run_id=pipeline_run_id_from_context(ctx),
                workflow_id=metadata_value(ctx, "workflow_id"),
                user_id=user_id_from_context(ctx),
            ),
        )
        return ok_output(
            StageflowStageResult(
                payload=typed_result, summary={"model_slug": typed_result.model_slug}
            )
        )

    async def output_guard(ctx: StageContext) -> Any:
        typed_result = cast(TypedLLMResult, payload_from_inputs(ctx, "llm_transform"))
        draft = cast(GeneratedScenarioDraft, typed_result.parsed)
        if draft.rubric_id != plan.rubric_id or list(draft.target_skill_slugs) != list(
            plan.target_skill_slugs
        ):
            raise validation_error(
                "Generated scenario drifted from the worker plan metadata",
                code="SS-VALIDATION-069",
                details={"expected_rubric_id": plan.rubric_id},
            )
        if len(draft.supporting_artifacts) != plan.supporting_artifact_count:
            raise validation_error(
                "Generated scenario supporting artifact count did not match the worker plan",
                code="SS-VALIDATION-070",
                details={
                    "expected": plan.supporting_artifact_count,
                    "actual": len(draft.supporting_artifacts),
                },
            )
        return ok_output(StageflowStageResult(payload=typed_result, summary={"title": draft.title}))

    pipeline = Pipeline.from_stages(
        stage("input_guard", cast(Any, input_guard), StageKind.GUARD),
        stage(
            "prompt_request_transform",
            cast(Any, prompt_request_transform),
            StageKind.TRANSFORM,
            dependencies=("input_guard",),
        ),
        stage(
            "prompt_render_transform",
            cast(Any, prompt_render_transform),
            StageKind.TRANSFORM,
            dependencies=("prompt_request_transform",),
        ),
        stage(
            "llm_transform",
            cast(Any, llm_transform),
            StageKind.TRANSFORM,
            dependencies=("prompt_render_transform",),
        ),
        stage(
            "output_guard",
            cast(Any, output_guard),
            StageKind.GUARD,
            dependencies=("llm_transform",),
        ),
        name="catalog_scenario_worker",
    )
    result = await run_logged_subpipeline(
        stageflow,
        parent_ctx=parent_ctx,
        parent_stage_name=parent_ctx.stage_name,
        correlation_id=correlation_id,
        pipeline=pipeline,
        result_stage_name="output_guard",
        execution_mode="catalog_generation_worker",
        service="soft_skills_backend.catalog",
        idempotency_key=f"catalog_scenario_worker:{request_id_from_context(parent_ctx)}:{worker_index}",
        idempotency_params=plan.model_dump(mode="json"),
        timeout_ms=timeout_ms,
    )
    if not result.success or result.data is None:
        raise validation_error(
            "Scenario worker pipeline failed",
            code="SS-VALIDATION-071",
            details={"worker_index": worker_index, "reason": result.error},
        )
    typed_result = cast(TypedLLMResult, result.data["payload"])
    return WorkerExecutionResult(
        typed_result=typed_result,
        child_run_id=str(result.child_run_id),
        correlation_id=str(correlation_id),
    )
