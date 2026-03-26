"""Stageflow-backed evaluation orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from stageflow.api import Pipeline, StageKind, stage

from soft_skills_backend.modules.evaluation.contracts.commands import EvaluationRunCommand
from soft_skills_backend.modules.evaluation.contracts.views import EvaluationRunView
from soft_skills_backend.modules.evaluation.domain.evaluation import (
    BuiltinEvaluationSuite,
    suite_definition,
)
from soft_skills_backend.modules.evaluation.infra.repository import EvaluationRepository
from soft_skills_backend.modules.evaluation.use_cases.marking_benchmark import (
    MarkingBenchmarkRunner,
)
from soft_skills_backend.platform.workflows.stageflow import (
    StageflowPipelineSupport,
    StageflowStageResult,
    ok_output,
    payload_from_inputs,
    payload_from_results,
    run_logged_pipeline,
)
from soft_skills_backend.platform.workflows.stageflow_runtime import StageflowRuntime
from soft_skills_backend.shared.auth import Actor
from soft_skills_backend.shared.errors import AppError


@dataclass(frozen=True, slots=True)
class PreparedEvaluationRequest:
    """Validated evaluation request."""

    actor: Actor
    command: EvaluationRunCommand
    suite: BuiltinEvaluationSuite


class EvaluationWorkflowService:
    """Own Stageflow orchestration for evaluation runs."""

    _MARKING_EVAL_TIMEOUT_MS = 240_000

    def __init__(
        self,
        *,
        stageflow_runtime: StageflowRuntime,
        repository: EvaluationRepository,
        marking_benchmark: MarkingBenchmarkRunner,
    ) -> None:
        self._repository = repository
        self._stageflow = StageflowPipelineSupport.from_runtime(stageflow_runtime)
        self._marking_benchmark = marking_benchmark

    async def execute(
        self,
        *,
        actor: Actor,
        request_id: str,
        trace_id: str,
        workflow_id: str,
        command: EvaluationRunCommand,
    ) -> EvaluationRunView:
        self._repository.sync_builtin_suites()
        suite = suite_definition(command.suite_id)
        self._repository.record_started(
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id,
            suite_id=suite.suite_id,
            model_slugs=command.model_slugs,
            case_ids=command.case_ids,
        )

        async def input_guard(_ctx) -> Any:
            return ok_output(
                StageflowStageResult(
                    payload=PreparedEvaluationRequest(actor=actor, command=command, suite=suite),
                    summary={"suite_id": suite.suite_id},
                )
            )

        async def transform(ctx) -> Any:
            prepared = cast(PreparedEvaluationRequest, payload_from_inputs(ctx, "input_guard"))
            computation = await self._marking_benchmark.execute(
                ctx=ctx,
                actor=prepared.actor,
                suite=prepared.suite,
                command=prepared.command,
            )
            return ok_output(
                StageflowStageResult(
                    payload=computation,
                    summary={
                        "suite_id": prepared.suite.suite_id,
                        "passed": computation.passed,
                        "case_count": len(computation.case_results),
                    },
                )
            )

        async def work(ctx) -> Any:
            prepared = cast(PreparedEvaluationRequest, payload_from_inputs(ctx, "input_guard"))
            computation = payload_from_inputs(ctx, "transform")
            persisted = self._repository.persist_run(
                ctx=ctx,
                actor=prepared.actor,
                suite=prepared.suite,
                computation=computation,
            )
            return ok_output(
                StageflowStageResult(
                    payload=persisted,
                    summary={"evaluation_run_id": persisted.evaluation_run_id},
                )
            )

        pipeline = Pipeline.from_stages(
            stage("input_guard", cast(Any, input_guard), StageKind.GUARD),
            stage(
                "transform",
                cast(Any, transform),
                StageKind.TRANSFORM,
                dependencies=("input_guard",),
            ),
            stage(
                "work",
                cast(Any, work),
                StageKind.WORK,
                dependencies=("input_guard", "transform"),
            ),
            name="evaluation_run",
        )
        try:
            result = await run_logged_pipeline(
                self._stageflow,
                pipeline,
                request_id=request_id,
                trace_id=trace_id,
                workflow_id=workflow_id,
                user_id=actor.user_id,
                session_id=actor.user_id,
                execution_mode="evaluation_runtime",
                service="soft_skills_backend.evaluation",
                idempotency_key=(
                    f"evaluation:{suite.suite_id}:{','.join(command.model_slugs) or 'default'}:"
                    f"{','.join(command.case_ids) or 'all'}:{request_id}"
                ),
                timeout_ms=self._MARKING_EVAL_TIMEOUT_MS,
            )
        except AppError as exc:
            self._repository.record_failed(
                request_id=request_id,
                trace_id=trace_id,
                workflow_id=workflow_id,
                suite_id=suite.suite_id,
                model_slugs=command.model_slugs,
                error_code=exc.code,
                reason=exc.message,
            )
            raise
        return payload_from_results(result, "work", expected_type=EvaluationRunView)
