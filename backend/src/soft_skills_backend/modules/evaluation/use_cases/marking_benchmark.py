"""Provider-backed golden benchmark runner for marking models."""

from __future__ import annotations

from collections.abc import Callable
from time import perf_counter
from typing import Any, cast

from sqlalchemy.orm import Session, sessionmaker
from stageflow.core import StageContext

from soft_skills_backend.config import LLMTaskKind, Settings
from soft_skills_backend.engines.config import load_marking_runtime_config
from soft_skills_backend.engines.marking.domain.rubric_repository import SqlAlchemyRubricRepository
from soft_skills_backend.modules.evaluation.contracts.commands import EvaluationRunCommand
from soft_skills_backend.modules.evaluation.domain.evaluation import (
    BuiltinEvaluationSuite,
    EvaluationCaseOutcome,
    EvaluationComputation,
    GoldenDataset,
    GoldenMarkingCase,
    ScoreBand,
    build_marking_computation,
    estimate_cost_usd,
    load_suite_dataset,
    select_cases,
)
from soft_skills_backend.modules.practice.domain.practice import validate_assessment_draft
from soft_skills_backend.modules.practice.workflows.assessment.marking_provider import (
    DefaultAssessmentMarkingProvider,
    StructuredOutputRejectionError,
    build_aggregation_typed_output,
    build_per_skill_typed_output,
    build_prompt_library,
)
from soft_skills_backend.modules.practice.workflows.assessment.models import (
    AssessmentTransformPayload,
    LearnerContextPayload,
    PracticePromptView,
    ResolvedAttemptPayload,
)
from soft_skills_backend.modules.practice.workflows.assessment_service import (
    model_slug_matches_execution_source,
)
from soft_skills_backend.platform.db.models import RubricCriterionRecord, RubricRecord
from soft_skills_backend.platform.providers.llm.openai_compatible import (
    OpenAICompatibleLLMProvider,
)
from soft_skills_backend.platform.workflows.stageflow import (
    metadata_value,
    pipeline_run_id_from_context,
    request_id_from_context,
)
from soft_skills_backend.shared.auth import Actor
from soft_skills_backend.shared.errors import AppError, scoring_error
from soft_skills_backend.shared.ports.telemetry import ProviderCallContext

ProviderFactory = Callable[[Settings, Any], Any]


class MarkingBenchmarkRunner:
    """Execute provider-backed marking evals against the golden dataset."""

    def __init__(
        self,
        *,
        settings: Settings,
        session_factory: sessionmaker[Session],
        provider_call_logger: Any,
        provider_factory: ProviderFactory | None = None,
    ) -> None:
        self._settings = settings
        self._session_factory = session_factory
        self._provider_call_logger = provider_call_logger
        self._provider_factory = provider_factory or self._default_provider_factory
        self._rubric_repository = SqlAlchemyRubricRepository(session_factory)

    def set_provider_factory(self, provider_factory: ProviderFactory) -> None:
        self._provider_factory = provider_factory

    async def execute(
        self,
        *,
        ctx: StageContext,
        actor: Actor,
        suite: BuiltinEvaluationSuite,
        command: EvaluationRunCommand,
    ) -> EvaluationComputation:
        dataset = load_suite_dataset(suite)
        selected_cases = select_cases(dataset=dataset, case_ids=command.case_ids)
        self._materialize_rubrics(dataset=dataset, selected_cases=selected_cases)
        model_slugs = command.model_slugs or [self._default_model_slug()]
        case_results: list[EvaluationCaseOutcome] = []
        for model_slug in model_slugs:
            marker = self._build_marker(model_slug)
            for case in selected_cases:
                case_results.append(
                    await self._evaluate_case(
                        ctx=ctx,
                        actor=actor,
                        dataset=dataset,
                        case=case,
                        requested_model_slug=model_slug,
                        marker=marker,
                    )
                )
        return build_marking_computation(
            suite=suite,
            dataset=dataset,
            selected_cases=selected_cases,
            model_slugs=model_slugs,
            case_results=case_results,
        )

    def _materialize_rubrics(
        self,
        *,
        dataset: GoldenDataset,
        selected_cases: list[GoldenMarkingCase],
    ) -> None:
        required_rubric_ids = {case.prompt.rubric_id for case in selected_cases}
        rubric_map = {
            rubric.rubric_id: rubric
            for rubric in dataset.rubrics
            if rubric.rubric_id in required_rubric_ids
        }
        missing = sorted(required_rubric_ids.difference(rubric_map))
        if missing:
            raise scoring_error(
                "Golden dataset was missing required rubric definitions",
                code="SS-SCORING-026",
                details={"missing_rubric_ids": missing, "dataset_version": dataset.dataset_version},
            )
        with self._session_factory() as session:
            for rubric_id in sorted(required_rubric_ids):
                rubric = rubric_map[rubric_id]
                existing = session.get(RubricRecord, rubric_id)
                if existing is None:
                    existing = RubricRecord(rubric_id=rubric_id)
                    session.add(existing)
                existing.family = rubric.family
                existing.version = rubric.version
                existing.content_type = rubric.content_type
                existing.schema_version = rubric.schema_version
                existing.name = rubric.name
                existing.criteria = [criterion.skill_slug for criterion in rubric.criteria]
                session.query(RubricCriterionRecord).filter(
                    RubricCriterionRecord.rubric_id == rubric_id
                ).delete()
                for criterion in rubric.criteria:
                    session.add(
                        RubricCriterionRecord(
                            rubric_id=rubric.rubric_id,
                            rubric_version=rubric.version,
                            criterion_ref=criterion.criterion_ref,
                            skill_slug=criterion.skill_slug,
                            title=criterion.title,
                            description=criterion.description,
                            weight=criterion.weight,
                            required=criterion.required,
                            position=criterion.position,
                            levels_json=[
                                {
                                    f"level_{level.level}": {
                                        "description": level.description,
                                        "examples": list(level.examples),
                                    }
                                }
                                for level in criterion.levels
                            ],
                        )
                    )
            session.commit()

    def _build_marker(self, model_slug: str) -> DefaultAssessmentMarkingProvider:
        settings = self._settings.model_copy(
            update={
                "llm_marking_per_skill_model": model_slug,
                "llm_marking_aggregation_model": model_slug,
                "llm_default_backup_model": None,
            }
        )
        provider = self._provider_factory(settings, self._provider_call_logger)
        return DefaultAssessmentMarkingProvider(
            settings=settings,
            llm_provider=provider,
            prompt_library=build_prompt_library(settings),
            per_skill_typed_output=build_per_skill_typed_output(settings),
            aggregation_typed_output=build_aggregation_typed_output(settings),
            rubric_repository=SqlAlchemyRubricRepository(self._session_factory),
        )

    async def _evaluate_case(
        self,
        *,
        ctx: StageContext,
        actor: Actor,
        dataset: GoldenDataset,
        case: GoldenMarkingCase,
        requested_model_slug: str,
        marker: DefaultAssessmentMarkingProvider,
    ) -> EvaluationCaseOutcome:
        prompt_payload = self._build_prompt_payload(ctx=ctx, case=case)
        learner_payload = LearnerContextPayload.model_validate(case.learner_context.model_dump())
        latency_start = perf_counter()
        raw_payload: dict[str, Any] = {}
        usage: dict[str, int] = {}
        observed_model_slug = requested_model_slug
        try:
            transform_payload = await marker.mark_attempt(
                prompt_payload=prompt_payload,
                learner_payload=learner_payload,
                call_context=self._call_context(ctx=ctx, actor=actor, case_id=case.case_id),
            )
            latency_ms = int((perf_counter() - latency_start) * 1000)
            raw_payload = cast(dict[str, Any], transform_payload.raw_payload)
            usage = dict(transform_payload.usage)
            observed_model_slug = transform_payload.model_slug
            self._accept_output(
                marker=marker,
                prompt_payload=prompt_payload,
                case=case,
                transform_payload=transform_payload,
            )
            draft = transform_payload.draft
            actual_skill_scores = {
                skill_score.skill_slug: skill_score.score for skill_score in draft.skill_scores
            }
            skill_errors = [
                abs(actual_skill_scores[skill_slug] - expected.minimum)
                if expected.minimum == expected.maximum
                else _distance_to_band(
                    actual_skill_scores[skill_slug],
                    minimum=expected.minimum,
                    maximum=expected.maximum,
                )
                for skill_slug, expected in case.expected_skill_scores.items()
                if skill_slug in actual_skill_scores
            ]
            evidence_coverage_rate = _evidence_coverage_rate(
                expected_skill_slugs=list(case.expected_skill_scores.keys()),
                actual_evidence_skill_slugs=[item.skill_slug for item in draft.evidence],
            )
            overall_score_abs_error = _distance_to_band(
                draft.overall_score,
                minimum=case.expected_overall_score.minimum,
                maximum=case.expected_overall_score.maximum,
            )
            skill_band_pass_rate = _skill_band_pass_rate(
                expected_skill_scores=case.expected_skill_scores,
                actual_skill_scores=actual_skill_scores,
            )
            accepted_output = True
            passed = (
                overall_score_abs_error == 0
                and skill_band_pass_rate == 1.0
                and evidence_coverage_rate >= case.minimum_evidence_coverage
            )
            prompt_tokens = int(usage.get("prompt_tokens", 0))
            completion_tokens = int(usage.get("completion_tokens", 0))
            total_tokens = int(usage.get("total_tokens", prompt_tokens + completion_tokens))
            return EvaluationCaseOutcome(
                case_id=f"{observed_model_slug}:{case.case_id}",
                case_label=f"{case.label} [{observed_model_slug}]",
                status="passed" if passed else "failed",
                metrics={
                    "accepted_output": accepted_output,
                    "latency_ms": latency_ms,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "estimated_cost_usd": estimate_cost_usd(
                        model_slug=observed_model_slug,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                    ),
                    "overall_score_abs_error": float(overall_score_abs_error),
                    "skill_score_abs_error_mean": round(
                        sum(skill_errors) / max(1, len(skill_errors)), 4
                    ),
                    "skill_band_pass_rate": round(skill_band_pass_rate, 4),
                    "evidence_coverage_rate": round(evidence_coverage_rate, 4),
                },
                detail_payload={
                    "dataset_id": dataset.dataset_id,
                    "dataset_version": dataset.dataset_version,
                    "case_id": case.case_id,
                    "case_tags": list(case.tags),
                    "requested_model_slug": requested_model_slug,
                    "evaluated_model_slug": observed_model_slug,
                    "provider": marker.provider_name,
                    "prompt_type": case.prompt.prompt_type,
                    "practice_type": case.prompt.practice_type.value,
                    "expected_overall_score": case.expected_overall_score.model_dump(mode="json"),
                    "expected_skill_scores": {
                        skill_slug: band.model_dump(mode="json")
                        for skill_slug, band in case.expected_skill_scores.items()
                    },
                    "actual_assessment": draft.model_dump(mode="json"),
                    "raw_payload": raw_payload,
                },
            )
        except StructuredOutputRejectionError as exc:
            latency_ms = int((perf_counter() - latency_start) * 1000)
            return EvaluationCaseOutcome(
                case_id=f"{requested_model_slug}:{case.case_id}",
                case_label=f"{case.label} [{requested_model_slug}]",
                status="failed",
                error_code=exc.app_error.code,
                metrics={
                    "accepted_output": False,
                    "latency_ms": latency_ms,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                    "estimated_cost_usd": estimate_cost_usd(
                        model_slug=observed_model_slug,
                        prompt_tokens=0,
                        completion_tokens=0,
                    ),
                },
                detail_payload={
                    "dataset_id": dataset.dataset_id,
                    "dataset_version": dataset.dataset_version,
                    "case_id": case.case_id,
                    "case_tags": list(case.tags),
                    "requested_model_slug": requested_model_slug,
                    "evaluated_model_slug": observed_model_slug,
                    "provider": marker.provider_name,
                    "practice_type": case.prompt.practice_type.value,
                    "error_message": exc.app_error.message,
                    "raw_payload": exc.raw_payload,
                },
            )
        except AppError as exc:
            latency_ms = int((perf_counter() - latency_start) * 1000)
            prompt_tokens = int(usage.get("prompt_tokens", 0))
            completion_tokens = int(usage.get("completion_tokens", 0))
            total_tokens = int(usage.get("total_tokens", prompt_tokens + completion_tokens))
            return EvaluationCaseOutcome(
                case_id=f"{requested_model_slug}:{case.case_id}",
                case_label=f"{case.label} [{requested_model_slug}]",
                status="failed",
                error_code=exc.code,
                metrics={
                    "accepted_output": False,
                    "latency_ms": latency_ms,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "estimated_cost_usd": estimate_cost_usd(
                        model_slug=observed_model_slug,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                    ),
                },
                detail_payload={
                    "dataset_id": dataset.dataset_id,
                    "dataset_version": dataset.dataset_version,
                    "case_id": case.case_id,
                    "case_tags": list(case.tags),
                    "requested_model_slug": requested_model_slug,
                    "evaluated_model_slug": observed_model_slug,
                    "provider": marker.provider_name,
                    "practice_type": case.prompt.practice_type.value,
                    "error_message": exc.message,
                    "raw_payload": raw_payload,
                },
            )

    def _build_prompt_payload(
        self,
        *,
        ctx: StageContext,
        case: GoldenMarkingCase,
    ) -> ResolvedAttemptPayload:
        return ResolvedAttemptPayload(
            attempt_id=f"eval-attempt-{case.case_id}",
            session_id=f"eval-session-{case.case_id}",
            workflow_id=str(metadata_value(ctx, "workflow_id")),
            response_text=case.response_text,
            prompt=PracticePromptView(
                practice_type=case.prompt.practice_type,
                content_item_id=f"golden-content-{case.case_id}",
                content_item_type=case.prompt.prompt_type,
                prompt_type=case.prompt.prompt_type,
                title=case.prompt.title,
                prompt_text=case.prompt.prompt_text,
                difficulty=case.prompt.difficulty,
                delivery_version=load_marking_runtime_config().prompt_version,
                response_mode="text",
                target_skill_slugs=list(case.prompt.target_skill_slugs),
                rubric_id=case.prompt.rubric_id,
                rubric_version=case.prompt.rubric_version,
                scenario_context=case.prompt.scenario_context,
                interview_context=case.prompt.interview_context,
            ),
        )

    def _call_context(
        self,
        *,
        ctx: StageContext,
        actor: Actor,
        case_id: str,
    ) -> ProviderCallContext:
        return ProviderCallContext(
            operation=f"evaluation_marking_benchmark:{case_id}",
            request_id=request_id_from_context(ctx),
            trace_id=metadata_value(ctx, "trace_id"),
            pipeline_run_id=pipeline_run_id_from_context(ctx),
            workflow_id=metadata_value(ctx, "workflow_id"),
            user_id=actor.user_id,
        )

    def _accept_output(
        self,
        *,
        marker: DefaultAssessmentMarkingProvider,
        prompt_payload: ResolvedAttemptPayload,
        case: GoldenMarkingCase,
        transform_payload: AssessmentTransformPayload,
    ) -> None:
        config = load_marking_runtime_config()
        draft = transform_payload.draft
        if draft.prompt_version != config.prompt_version:
            raise scoring_error(
                "Assessment output prompt version did not match the active contract",
                code="SS-SCORING-007",
                details={
                    "expected_prompt_version": config.prompt_version,
                    "observed_prompt_version": draft.prompt_version,
                },
            )
        if draft.rubric_version != prompt_payload.prompt.rubric_version:
            raise scoring_error(
                "Assessment output rubric version did not match the active rubric",
                code="SS-SCORING-008",
                details={
                    "expected_rubric_version": prompt_payload.prompt.rubric_version,
                    "observed_rubric_version": draft.rubric_version,
                },
            )
        if draft.provider != marker.provider_name or not model_slug_matches_execution_source(
            executed_slug=transform_payload.model_slug,
            output_slug=draft.model_slug,
            configured_slug=marker.model_slug,
        ):
            raise scoring_error(
                "Assessment output provider metadata did not match the execution source",
                code="SS-SCORING-009",
                details={
                    "expected_provider": marker.provider_name,
                    "observed_provider": draft.provider,
                    "expected_model_slug": transform_payload.model_slug,
                    "observed_model_slug": draft.model_slug,
                },
            )
        validate_assessment_draft(
            response_text=case.response_text,
            required_skill_slugs=case.prompt.target_skill_slugs,
            draft=draft,
            rubric_definition=self._rubric_repository.get_rubric_definition(
                prompt_payload.prompt.rubric_id,
                required_skill_slugs=prompt_payload.prompt.target_skill_slugs,
            ),
        )

    def _default_model_slug(self) -> str:
        return self._settings.get_llm_model_for_task(LLMTaskKind.MARKING_PER_SKILL)

    def _default_provider_factory(self, settings: Settings, provider_call_logger: Any) -> Any:
        return OpenAICompatibleLLMProvider(
            settings=settings,
            provider_call_logger=provider_call_logger,
        )


def _distance_to_band(value: int, *, minimum: int, maximum: int) -> int:
    if minimum <= value <= maximum:
        return 0
    if value < minimum:
        return minimum - value
    return value - maximum


def _evidence_coverage_rate(
    *,
    expected_skill_slugs: list[str],
    actual_evidence_skill_slugs: list[str],
) -> float:
    if not expected_skill_slugs:
        return 1.0
    actual = set(actual_evidence_skill_slugs)
    covered = sum(1 for skill_slug in expected_skill_slugs if skill_slug in actual)
    return covered / len(expected_skill_slugs)


def _skill_band_pass_rate(
    *,
    expected_skill_scores: dict[str, ScoreBand],
    actual_skill_scores: dict[str, int],
) -> float:
    if not expected_skill_scores:
        return 1.0
    passed = 0
    for skill_slug, band in expected_skill_scores.items():
        value = actual_skill_scores.get(skill_slug)
        if value is not None and band.minimum <= value <= band.maximum:
            passed += 1
    return passed / len(expected_skill_scores)
