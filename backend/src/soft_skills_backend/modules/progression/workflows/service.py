"""Stageflow-backed progression orchestration."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

from stageflow.api import Pipeline, StageKind, stage

from soft_skills_backend.modules.progression.contracts.commands import ProgressRecalculationCommand
from soft_skills_backend.modules.progression.contracts.views import (
    ProgressDashboardView,
    ProgressRecalculationView,
)
from soft_skills_backend.modules.progression.domain.progression import (
    ComputedProgressSnapshot,
    ComputedRecommendation,
    build_prior_progress_state,
    compute_progress_snapshot,
    compute_recommendation,
)
from soft_skills_backend.modules.progression.infra.repository import (
    ProgressionPersistedArtifacts,
    ProgressionRefreshInput,
    ProgressionRepository,
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


def _now() -> datetime:
    return datetime.now(UTC)


class ProgressionWorkflowService:
    """Own Stageflow orchestration for progression refresh and replay."""

    def __init__(
        self,
        *,
        stageflow_runtime: StageflowRuntime,
        repository: ProgressionRepository,
    ) -> None:
        self._repository = repository
        self._stageflow = StageflowPipelineSupport.from_runtime(stageflow_runtime)

    async def refresh_from_assessment(
        self,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str,
        learner_id: str,
        assessment_id: str,
    ) -> ProgressDashboardView:
        async def input_guard(_ctx) -> Any:
            refresh_input = self._repository.load_refresh_input(assessment_id)
            return ok_output(
                StageflowStageResult(
                    payload=refresh_input,
                    summary={
                        "learner_id": refresh_input.learner.learner_id,
                        "assessment_count": len(refresh_input.assessments),
                    },
                )
            )

        async def snapshot_transform(ctx) -> Any:
            refresh_input = cast(ProgressionRefreshInput, payload_from_inputs(ctx, "input_guard"))
            previous_state = build_prior_progress_state(refresh_input.previous_state_payload)
            computed = compute_progress_snapshot(
                assessments=refresh_input.assessments,
                skill_slugs=refresh_input.skill_slugs,
                competency_definitions=refresh_input.competency_definitions,
                previous_state=previous_state,
                now=_now(),
            )
            return ok_output(
                StageflowStageResult(
                    payload=computed,
                    summary={
                        "weak_skill_count": len(computed.weak_skill_slugs),
                        "stagnating_skill_count": len(computed.stagnating_skill_slugs),
                    },
                )
            )

        async def snapshot_work(ctx) -> Any:
            refresh_input = cast(ProgressionRefreshInput, payload_from_inputs(ctx, "input_guard"))
            computed = cast(ComputedProgressSnapshot, payload_from_inputs(ctx, "snapshot_transform"))
            snapshot = self._repository.persist_snapshot(
                ctx=ctx,
                learner_id=refresh_input.learner.learner_id,
                source_assessment_id=refresh_input.source_assessment.assessment_id,
                computed=computed,
            )
            return ok_output(
                StageflowStageResult(
                    payload=snapshot,
                    summary={"snapshot_id": snapshot.snapshot_id},
                )
            )

        async def recommendation_enrich(ctx) -> Any:
            refresh_input = cast(ProgressionRefreshInput, payload_from_inputs(ctx, "input_guard"))
            candidates = self._repository.load_catalog_candidates(refresh_input.learner.learner_id)
            return ok_output(
                StageflowStageResult(
                    payload=candidates,
                    summary={"candidate_count": len(candidates)},
                )
            )

        async def recommendation_transform(ctx) -> Any:
            refresh_input = cast(ProgressionRefreshInput, payload_from_inputs(ctx, "input_guard"))
            computed_snapshot = cast(
                ComputedProgressSnapshot,
                payload_from_inputs(ctx, "snapshot_transform"),
            )
            candidates = payload_from_inputs(ctx, "recommendation_enrich")
            computed = compute_recommendation(
                learner=refresh_input.learner,
                snapshot=computed_snapshot,
                candidates=cast(list, candidates),
                now=_now(),
            )
            return ok_output(
                StageflowStageResult(
                    payload=computed,
                    summary={"selected_count": len(computed.items)},
                )
            )

        async def recommendation_work(ctx) -> Any:
            refresh_input = cast(ProgressionRefreshInput, payload_from_inputs(ctx, "input_guard"))
            snapshot = payload_from_inputs(ctx, "snapshot_work")
            recommendation = self._repository.persist_recommendation(
                ctx=ctx,
                learner_id=refresh_input.learner.learner_id,
                snapshot_id=snapshot.snapshot_id,
                computed=cast(
                    ComputedRecommendation,
                    payload_from_inputs(ctx, "recommendation_transform"),
                ),
            )
            return ok_output(
                StageflowStageResult(
                    payload=ProgressionPersistedArtifacts(
                        snapshot=snapshot,
                        recommendation=recommendation,
                    ),
                    summary={"recommendation_id": recommendation.recommendation_id},
                )
            )

        pipeline = Pipeline.from_stages(
            stage("input_guard", cast(Any, input_guard), StageKind.GUARD),
            stage(
                "snapshot_transform",
                cast(Any, snapshot_transform),
                StageKind.TRANSFORM,
                dependencies=("input_guard",),
            ),
            stage(
                "snapshot_work",
                cast(Any, snapshot_work),
                StageKind.WORK,
                dependencies=("input_guard", "snapshot_transform"),
            ),
            stage(
                "recommendation_enrich",
                cast(Any, recommendation_enrich),
                StageKind.ENRICH,
                dependencies=("input_guard",),
            ),
            stage(
                "recommendation_transform",
                cast(Any, recommendation_transform),
                StageKind.TRANSFORM,
                dependencies=("input_guard", "snapshot_transform", "recommendation_enrich"),
            ),
            stage(
                "recommendation_work",
                cast(Any, recommendation_work),
                StageKind.WORK,
                dependencies=("input_guard", "snapshot_work", "recommendation_transform"),
            ),
            name="progression_refresh",
        )
        result = await run_logged_pipeline(
            self._stageflow,
            pipeline,
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id,
            user_id=learner_id,
            session_id=learner_id,
            execution_mode="progression_runtime",
            service="soft_skills_backend.progression",
            idempotency_key=f"progression_refresh:{learner_id}:{assessment_id}",
            idempotency_params={"assessment_id": assessment_id},
        )
        persisted = payload_from_results(
            result,
            "recommendation_work",
            expected_type=ProgressionPersistedArtifacts,
        )
        return ProgressDashboardView(
            snapshot=persisted.snapshot,
            recommendation=persisted.recommendation,
        )

    async def recalculate(
        self,
        *,
        actor: Actor,
        request_id: str,
        trace_id: str,
        workflow_id: str,
        command: ProgressRecalculationCommand,
    ) -> ProgressRecalculationView:
        run_id = self._repository.create_recalculation_run(
            request_id=request_id,
            learner_id=command.learner_id,
            reason=command.reason,
            trace_id=trace_id,
            workflow_id=workflow_id,
        )
        dashboard = await self.refresh_from_assessment(
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id,
            learner_id=command.learner_id,
            assessment_id=self._latest_assessment_id(command.learner_id),
        )
        refresh_input = self._repository.load_refresh_input(dashboard.snapshot.source_assessment_id)
        del actor
        return self._repository.complete_recalculation_run(
            request_id=request_id,
            workflow_id=workflow_id,
            run_id=run_id,
            reason=command.reason,
            learner_id=command.learner_id,
            assessment_count=len(refresh_input.assessments),
            previous_state_payload=refresh_input.previous_state_payload,
            snapshot=dashboard.snapshot,
            recommendation=dashboard.recommendation,
        )

    def _latest_assessment_id(self, learner_id: str) -> str:
        return self._repository.latest_validated_assessment_id(learner_id)
