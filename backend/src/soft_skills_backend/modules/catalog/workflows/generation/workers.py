"""Worker fan-out helpers for catalog generation workflows."""

from __future__ import annotations

import asyncio
import json
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
from soft_skills_backend.modules.catalog.domain.constants import (
    ALLOWED_SCENARIO_ARTIFACT_TYPES,
    DETERMINISTIC_RUBRIC_BY_CONTENT_TYPE,
)
from soft_skills_backend.modules.catalog.domain.models import (
    GeneratedPromptItemDraft,
    GeneratedPromptItemPlan,
    GeneratedScenarioDraft,
    GeneratedScenarioQuestionDraft,
    GeneratedScenarioPlan,
    GeneratedScenarioShellDraft,
)
from soft_skills_backend.modules.catalog.domain.validators import (
    validate_mock_world,
    validate_scenario_questions,
)
from soft_skills_backend.modules.practice.workflows.assessment import (
    TypedLLMOutput,
    TypedLLMResult,
)
from soft_skills_backend.platform.providers.llm.prompts import (
    CREATOR_PROMPT_ITEM_OUTPUT_FORMAT,
    CREATOR_SCENARIO_QUESTION_OUTPUT_FORMAT,
    CREATOR_SCENARIO_SHELL_OUTPUT_FORMAT,
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
from soft_skills_backend.shared.errors import AppError, validation_error
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


def _semantic_retry_feedback(error: Exception) -> str:
    if hasattr(error, "message") and hasattr(error, "code"):
        details = getattr(error, "details", None)
        details_suffix = f" Details: {json.dumps(details, sort_keys=True)}" if details else ""
        return (
            f"{getattr(error, 'code')}: {getattr(error, 'message')}{details_suffix}. "
            "Return corrected JSON only."
        )
    return f"{error}. Return corrected JSON only."


def _validate_generated_scenario_draft(
    *,
    draft: GeneratedScenarioDraft,
    plan: GeneratedScenarioPlan,
) -> None:
    if list(draft.target_skill_slugs) != list(plan.target_skill_slugs):
        raise validation_error(
            "Generated scenario drifted from the worker plan metadata",
            code="SS-VALIDATION-069",
            details={"expected_rubric_id": plan.rubric_id},
        )
    if (
        draft.rubric_id is not None
        and plan.rubric_id is not None
        and draft.rubric_id != plan.rubric_id
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
    if len(draft.questions) != plan.question_count:
        raise validation_error(
            "Generated scenario question count did not match the worker plan",
            code="SS-VALIDATION-089",
            details={"expected": plan.question_count, "actual": len(draft.questions)},
        )
    validate_scenario_questions(draft.questions)
    validate_mock_world(cast(Any, draft))


def _validate_generated_prompt_item_draft(
    *,
    draft: GeneratedPromptItemDraft,
    plan: GeneratedPromptItemPlan,
) -> None:
    draft.target_skill_slugs = _normalize_prompt_item_skills(
        draft.prompt_type, draft.target_skill_slugs
    )
    if draft.prompt_type != plan.prompt_type:
        raise validation_error(
            "Generated prompt item drifted from the worker plan metadata",
            code="SS-VALIDATION-067",
            details={
                "expected_prompt_type": plan.prompt_type,
                "expected_rubric_id": plan.rubric_id,
            },
        )
    if (
        draft.rubric_id is not None
        and plan.rubric_id is not None
        and draft.rubric_id != plan.rubric_id
    ):
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
        for criterion in draft.generated_rubric.criteria:
            if len(criterion.levels) != 2:
                raise validation_error(
                    "Generated quick-practice rubric criteria must include exactly two levels",
                    code="SS-VALIDATION-086",
                    details={
                        "title": draft.title,
                        "criterion_ref": criterion.criterion_ref,
                        "levels_count": len(criterion.levels),
                    },
                )
    elif draft.generated_rubric is not None:
        raise validation_error(
            "Only quick-practice prompt items may include a generated rubric payload",
            code="SS-VALIDATION-079",
            details={"prompt_type": draft.prompt_type, "title": draft.title},
        )


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
    scenario_shell_worker_output: TypedLLMOutput,
    scenario_question_worker_output: TypedLLMOutput,
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
                scenario_shell_worker_output=scenario_shell_worker_output,
                scenario_question_worker_output=scenario_question_worker_output,
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
                summary={
                    "prompt_name": prompt_request.name,
                    "prompt_version": prompt_request.version,
                },
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
        base_messages: list[dict[str, object]] = [
            {
                "role": "system",
                "content": "Generate one realistic SoftSkills prompt item. Return JSON only.",
            },
            {"role": "user", "content": rendered_prompt.content},
        ]
        retry_messages = list(base_messages)
        last_error: AppError | None = None
        for _ in range(prompt_item_worker_output._max_validation_retries + 1):
            typed_result = await prompt_item_worker_output.generate(
                llm_provider,
                messages=retry_messages,
                call_context=ProviderCallContext(
                    operation="catalog_prompt_item_worker_generation",
                    request_id=request_id_from_context(ctx),
                    trace_id=metadata_value(ctx, "trace_id"),
                    pipeline_run_id=pipeline_run_id_from_context(ctx),
                    workflow_id=metadata_value(ctx, "workflow_id"),
                    user_id=user_id_from_context(ctx),
                ),
            )
            draft = cast(GeneratedPromptItemDraft, typed_result.parsed)
            try:
                _validate_generated_prompt_item_draft(draft=draft, plan=plan)
                return ok_output(
                    StageflowStageResult(
                        payload=typed_result, summary={"model_slug": typed_result.model_slug}
                    )
                )
            except AppError as exc:
                last_error = exc
                retry_messages = [
                    *base_messages,
                    {
                        "role": "assistant",
                        "content": json.dumps(typed_result.raw_payload, sort_keys=True),
                    },
                    {
                        "role": "user",
                        "content": (
                            "The previous prompt item draft was invalid. "
                            + _semantic_retry_feedback(exc)
                        ),
                    },
                ]
        assert last_error is not None
        raise last_error

    async def output_guard(ctx: StageContext) -> Any:
        typed_result = cast(TypedLLMResult, payload_from_inputs(ctx, "llm_transform"))
        draft = cast(GeneratedPromptItemDraft, typed_result.parsed)
        _validate_generated_prompt_item_draft(draft=draft, plan=plan)
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
            details={
                "worker_index": worker_index,
                "child_run_id": str(result.child_run_id),
                "reason": result.error,
            },
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
    scenario_shell_worker_output: TypedLLMOutput,
    scenario_question_worker_output: TypedLLMOutput,
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
            name=config.scenario_shell_worker_prompt_name,
            version=config.scenario_shell_worker_prompt_version,
            variables={
                "collection_title": collection_title,
                "target_audience": target_audience,
                "collection_difficulty": collection_difficulty,
                "workplace_context": workplace_context,
                "target_skill_slugs": ", ".join(plan.target_skill_slugs),
                "rubric_id": plan.rubric_id,
                "supporting_artifact_count": plan.supporting_artifact_count,
                "question_count": plan.question_count,
                "allowed_artifact_types": ", ".join(sorted(ALLOWED_SCENARIO_ARTIFACT_TYPES)),
                "title_hint": plan.title_hint,
                "generation_brief": plan.generation_brief,
                "output_format": CREATOR_SCENARIO_SHELL_OUTPUT_FORMAT,
            },
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

    async def prompt_render_transform(ctx: StageContext) -> Any:
        renderer = create_prompt_render_stage(
            prompt_registry=prompt_registry,
            request_stage_name="prompt_request_transform",
        )
        return await renderer(ctx)

    async def llm_transform(ctx: StageContext) -> Any:
        rendered_prompt = payload_from_inputs(ctx, "prompt_render_transform")
        base_messages: list[dict[str, object]] = [
            {
                "role": "system",
                "content": "Generate one realistic SoftSkills scenario shell. Return JSON only.",
            },
            {"role": "user", "content": rendered_prompt.content},
        ]
        retry_messages = list(base_messages)
        last_error: AppError | None = None
        for _ in range(scenario_shell_worker_output._max_validation_retries + 1):
            typed_result = await scenario_shell_worker_output.generate(
                llm_provider,
                messages=retry_messages,
                call_context=ProviderCallContext(
                    operation="catalog_scenario_shell_generation",
                    request_id=request_id_from_context(ctx),
                    trace_id=metadata_value(ctx, "trace_id"),
                    pipeline_run_id=pipeline_run_id_from_context(ctx),
                    workflow_id=metadata_value(ctx, "workflow_id"),
                    user_id=user_id_from_context(ctx),
                ),
            )
            draft = cast(GeneratedScenarioShellDraft, typed_result.parsed)
            try:
                if list(draft.target_skill_slugs) != list(plan.target_skill_slugs):
                    raise validation_error(
                        "Generated scenario shell drifted from the worker plan metadata",
                        code="SS-VALIDATION-069",
                        details={"expected_rubric_id": plan.rubric_id},
                    )
                if draft.rubric_id is not None and plan.rubric_id is not None and draft.rubric_id != plan.rubric_id:
                    raise validation_error(
                        "Generated scenario shell drifted from the worker plan metadata",
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
                if len(draft.question_plans) != plan.question_count:
                    raise validation_error(
                        "Generated scenario question plan count did not match the worker plan",
                        code="SS-VALIDATION-090",
                        details={"expected": plan.question_count, "actual": len(draft.question_plans)},
                    )
                expected_indexes = list(range(1, plan.question_count + 1))
                actual_indexes = [question_plan.index for question_plan in draft.question_plans]
                if actual_indexes != expected_indexes:
                    raise validation_error(
                        "Generated scenario question plan indexes were invalid",
                        code="SS-VALIDATION-091",
                        details={"expected": expected_indexes, "actual": actual_indexes},
                    )
                return ok_output(
                    StageflowStageResult(
                        payload=typed_result, summary={"model_slug": typed_result.model_slug}
                    )
                )
            except AppError as exc:
                last_error = exc
                retry_messages = [
                    *base_messages,
                    {
                        "role": "assistant",
                        "content": json.dumps(typed_result.raw_payload, sort_keys=True),
                    },
                    {
                        "role": "user",
                        "content": (
                            "The previous scenario shell draft was invalid. "
                            + _semantic_retry_feedback(exc)
                        ),
                    },
                ]
        assert last_error is not None
        raise last_error

    async def question_work(ctx: StageContext) -> Any:
        shell_result = cast(TypedLLMResult, payload_from_inputs(ctx, "llm_transform"))
        shell = cast(GeneratedScenarioShellDraft, shell_result.parsed)
        semaphore = asyncio.Semaphore(max(1, plan.question_count))

        async def run_question_worker(question_plan_index: int) -> TypedLLMResult:
            question_plan = shell.question_plans[question_plan_index - 1]
            async with semaphore:
                render_result = prompt_registry.render(
                    config.scenario_question_worker_prompt_name,
                    version=config.scenario_question_worker_prompt_version,
                    variables={
                        "collection_title": collection_title,
                        "target_audience": target_audience,
                        "collection_difficulty": collection_difficulty,
                        "scenario_title": shell.title,
                        "business_context": shell.business_context,
                        "learner_objective": shell.learner_objective,
                        "constraints": "; ".join(shell.constraints) or "none",
                        "stakeholder_tensions": "; ".join(shell.stakeholder_tensions) or "none",
                        "target_skill_slugs": ", ".join(shell.target_skill_slugs),
                        "question_index": str(question_plan.index),
                        "question_count": str(plan.question_count),
                        "question_generation_brief": question_plan.generation_brief,
                        "output_format": CREATOR_SCENARIO_QUESTION_OUTPUT_FORMAT,
                    },
                    trace_id=metadata_value(ctx, "trace_id"),
                    pipeline_run_id=pipeline_run_id_from_context(ctx),
                )
                base_messages: list[dict[str, object]] = [
                    {
                        "role": "system",
                        "content": "Generate one realistic SoftSkills scenario question. Return JSON only.",
                    },
                    {"role": "user", "content": render_result.rendered.content},
                ]
                retry_messages = list(base_messages)
                last_error: AppError | None = None
                for _ in range(scenario_question_worker_output._max_validation_retries + 1):
                    typed_result = await scenario_question_worker_output.generate(
                        llm_provider,
                        messages=retry_messages,
                        call_context=ProviderCallContext(
                            operation="catalog_scenario_question_generation",
                            request_id=request_id_from_context(ctx),
                            trace_id=metadata_value(ctx, "trace_id"),
                            pipeline_run_id=pipeline_run_id_from_context(ctx),
                            workflow_id=metadata_value(ctx, "workflow_id"),
                            user_id=user_id_from_context(ctx),
                        ),
                    )
                    question_draft = cast(GeneratedScenarioQuestionDraft, typed_result.parsed)
                    try:
                        if question_draft.index != question_plan.index:
                            raise validation_error(
                                "Generated scenario question index drifted from the worker plan metadata",
                                code="SS-VALIDATION-092",
                                details={"expected": question_plan.index, "actual": question_draft.index},
                            )
                        validate_scenario_questions([question_draft.question])
                        return typed_result
                    except AppError as exc:
                        last_error = exc
                        retry_messages = [
                            *base_messages,
                            {
                                "role": "assistant",
                                "content": json.dumps(typed_result.raw_payload, sort_keys=True),
                            },
                            {
                                "role": "user",
                                "content": (
                                    "The previous scenario question draft was invalid. "
                                    + _semantic_retry_feedback(exc)
                                ),
                            },
                        ]
                assert last_error is not None
                raise last_error

        question_results = await asyncio.gather(
            *(run_question_worker(index) for index in range(1, plan.question_count + 1))
        )
        return ok_output(
            StageflowStageResult(
                payload=question_results,
                summary={"generated_questions": len(question_results)},
            )
        )

    async def output_guard(ctx: StageContext) -> Any:
        shell_result = cast(TypedLLMResult, payload_from_inputs(ctx, "llm_transform"))
        shell = cast(GeneratedScenarioShellDraft, shell_result.parsed)
        question_results = cast(list[TypedLLMResult], payload_from_inputs(ctx, "question_work"))
        ordered_questions = [
            cast(GeneratedScenarioQuestionDraft, result.parsed)
            for result in sorted(
                question_results,
                key=lambda result: cast(GeneratedScenarioQuestionDraft, result.parsed).index,
            )
        ]
        draft = GeneratedScenarioDraft(
            title=shell.title,
            business_context=shell.business_context,
            learner_objective=shell.learner_objective,
            constraints=list(shell.constraints),
            stakeholder_tensions=list(shell.stakeholder_tensions),
            questions=[question.question for question in ordered_questions],
            target_skill_slugs=list(shell.target_skill_slugs),
            rubric_id=shell.rubric_id,
            mock_company=shell.mock_company,
            mock_people=list(shell.mock_people),
            supporting_artifacts=list(shell.supporting_artifacts),
        )
        _validate_generated_scenario_draft(draft=draft, plan=plan)
        return ok_output(
            StageflowStageResult(
                payload=TypedLLMResult(
                    raw_payload={
                        "shell": shell_result.raw_payload,
                        "questions": [result.raw_payload for result in question_results],
                    },
                    parsed=draft,
                    model_slug=shell_result.model_slug,
                    schema_version=shell_result.schema_version,
                    usage=shell_result.usage,
                ),
                summary={"title": draft.title},
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
            "question_work",
            cast(Any, question_work),
            StageKind.WORK,
            dependencies=("llm_transform",),
        ),
        stage(
            "output_guard",
            cast(Any, output_guard),
            StageKind.GUARD,
            dependencies=("llm_transform", "question_work"),
        ),
        name="catalog_scenario_generation",
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
        idempotency_key=f"catalog_scenario_generation:{request_id_from_context(parent_ctx)}:{worker_index}",
        idempotency_params=plan.model_dump(mode="json"),
        timeout_ms=timeout_ms,
    )
    if not result.success or result.data is None:
        raise validation_error(
            "Scenario generation pipeline failed",
            code="SS-VALIDATION-071",
            details={
                "worker_index": worker_index,
                "child_run_id": str(result.child_run_id),
                "reason": result.error,
            },
        )
    typed_result = cast(TypedLLMResult, result.data["payload"])
    return WorkerExecutionResult(
        typed_result=typed_result,
        child_run_id=str(result.child_run_id),
        correlation_id=str(correlation_id),
    )
