"""Assistant-side coordination for facilitated practice sessions."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from soft_skills_backend.modules.assistant.domain.models import AssistantMessageRole
from soft_skills_backend.modules.assistant.infra.repository import AssistantRepository
from soft_skills_backend.modules.catalog import (
    CatalogService,
    CollectionView,
    PromptItemView,
    ScenarioView,
)
from soft_skills_backend.modules.practice.domain.practice import PracticeType
from soft_skills_backend.modules.practice.models import (
    AttemptView,
    PracticeCorrelation,
    PracticeRunView,
    StartInterviewRunItemCommand,
    StartPracticeRunCommand,
    StartQuickPracticeRunItemCommand,
    StartScenarioRunItemCommand,
    SubmitAttemptCommand,
)
from soft_skills_backend.modules.practice.use_cases.practice_service import PracticeService
from soft_skills_backend.modules.practice.workflows.assessment.models import PracticePromptView
from soft_skills_backend.shared.auth import Actor
from soft_skills_backend.shared.errors import validation_error

PRACTICE_STATE_METADATA_KEY = "practice_state"
PRACTICE_STATE_SCHEMA_VERSION = "assistant_practice_state.v1"


class AssistantPracticeState(BaseModel):
    """Durable assistant-session state for an active practice run."""

    schema_version: Literal["assistant_practice_state.v1"] = PRACTICE_STATE_SCHEMA_VERSION
    practice_run_id: str | None = None
    current_attempt_id: str | None = None
    current_position: int | None = None
    total_items: int | None = None
    awaiting_user_answer: bool = False

    @classmethod
    def from_session_metadata(cls, metadata: dict[str, Any]) -> AssistantPracticeState:
        raw = metadata.get(PRACTICE_STATE_METADATA_KEY)
        if not isinstance(raw, dict):
            return cls()
        return cls.model_validate(raw)

    def is_active(self) -> bool:
        return bool(self.practice_run_id and self.current_attempt_id and self.awaiting_user_answer)

    def metadata_fragment(self) -> dict[str, Any]:
        return {PRACTICE_STATE_METADATA_KEY: self.model_dump(mode="json")}


class StartCollectionPracticeToolArgs(BaseModel):
    """Arguments for starting a practice run from one collection."""

    collection_id: str = Field(min_length=1)
    item_limit: int = Field(default=2, ge=1, le=5)
    include_prompt_items: bool = True
    include_scenarios: bool = True
    prompt_item_ids: list[str] = Field(default_factory=list, max_length=5)
    scenario_ids: list[str] = Field(default_factory=list, max_length=5)

    @model_validator(mode="after")
    def validate_selection(self) -> StartCollectionPracticeToolArgs:
        if self.prompt_item_ids or self.scenario_ids:
            return self
        if self.include_prompt_items or self.include_scenarios:
            return self
        raise ValueError("At least one collection content source must be enabled")


class AssistantPracticeQuestionView(BaseModel):
    """Question payload the assistant can present to the learner."""

    practice_run_id: str
    attempt_id: str
    session_id: str
    position: int
    total_items: int
    prompt: PracticePromptView


class AssistantPracticeStartResult(BaseModel):
    """Result after starting a collection-backed practice run."""

    practice_run_id: str
    current_question: AssistantPracticeQuestionView
    state: AssistantPracticeState


class AssistantPracticeAdvanceResult(BaseModel):
    """Result after submitting one active practice response."""

    practice_run_id: str
    submitted_attempt: AttemptView
    next_question: AssistantPracticeQuestionView | None = None
    run_completed: bool
    run_summary: dict[str, Any] | None = None
    state: AssistantPracticeState


class AssistantActivePracticeResult(BaseModel):
    """Result for reading the current active practice question."""

    state: AssistantPracticeState
    current_question: AssistantPracticeQuestionView | None = None


class AssistantEndPracticeResult(BaseModel):
    """Result after ending the active practice session."""

    ended: bool
    practice_run_id: str | None = None
    state: AssistantPracticeState


class AssistantPracticeCoordinator:
    """Bridge assistant tools to the existing practice runtime."""

    def __init__(
        self,
        *,
        repository: AssistantRepository,
        catalog_service: CatalogService,
        practice_service: PracticeService,
    ) -> None:
        self._repository = repository
        self._catalog = catalog_service
        self._practice = practice_service

    async def start_collection_practice(
        self,
        *,
        actor: Actor,
        session_id: str,
        request_id: str,
        trace_id: str,
        args: StartCollectionPracticeToolArgs,
    ) -> AssistantPracticeStartResult:
        collection = self._catalog.get_collection(actor, args.collection_id)
        command = StartPracticeRunCommand(
            items=self._build_run_items(collection=collection, args=args),
        )
        run = await self._practice.start_practice_run(
            actor,
            PracticeCorrelation(request_id=request_id, trace_id=trace_id),
            command,
        )
        question = _current_question_from_run(run)
        if question is None:
            raise validation_error(
                "Practice run did not produce an active question",
                code="SS-VALIDATION-207",
                details={"practice_run_id": run.run_id},
            )
        state = AssistantPracticeState(
            practice_run_id=run.run_id,
            current_attempt_id=question.attempt_id,
            current_position=question.position,
            total_items=question.total_items,
            awaiting_user_answer=True,
        )
        self._persist_state(actor=actor, session_id=session_id, state=state)
        return AssistantPracticeStartResult(
            practice_run_id=run.run_id,
            current_question=question,
            state=state,
        )

    def get_active_practice(
        self,
        *,
        actor: Actor,
        session_id: str,
    ) -> AssistantActivePracticeResult:
        state = self._load_state(actor=actor, session_id=session_id)
        if not state.is_active() or state.practice_run_id is None:
            return AssistantActivePracticeResult(state=state, current_question=None)
        run = self._practice.get_practice_run(actor, state.practice_run_id)
        question = _current_question_from_run(run)
        if question is None:
            idle_state = AssistantPracticeState()
            self._persist_state(actor=actor, session_id=session_id, state=idle_state)
            return AssistantActivePracticeResult(state=idle_state, current_question=None)
        refreshed_state = AssistantPracticeState(
            practice_run_id=run.run_id,
            current_attempt_id=question.attempt_id,
            current_position=question.position,
            total_items=question.total_items,
            awaiting_user_answer=True,
        )
        self._persist_state(actor=actor, session_id=session_id, state=refreshed_state)
        return AssistantActivePracticeResult(state=refreshed_state, current_question=question)

    async def submit_active_practice_response(
        self,
        *,
        actor: Actor,
        session_id: str,
        request_id: str,
        trace_id: str,
        response_text: str | None = None,
    ) -> AssistantPracticeAdvanceResult:
        state = self._load_state(actor=actor, session_id=session_id)
        if not state.is_active() or state.practice_run_id is None or state.current_attempt_id is None:
            raise validation_error(
                "There is no active practice question to submit",
                code="SS-VALIDATION-208",
                details={"session_id": session_id},
            )
        answer_text = (response_text or self._latest_user_message(actor, session_id)).strip()
        if not answer_text:
            raise validation_error(
                "Practice response text was empty",
                code="SS-VALIDATION-209",
                details={"session_id": session_id},
            )
        submitted_attempt = await self._practice.submit_attempt(
            actor,
            PracticeCorrelation(request_id=request_id, trace_id=trace_id),
            state.current_attempt_id,
            SubmitAttemptCommand(response_text=answer_text),
        )
        run = self._practice.get_practice_run(actor, state.practice_run_id)
        next_question = _current_question_from_run(run)
        if next_question is None:
            idle_state = AssistantPracticeState()
            self._persist_state(actor=actor, session_id=session_id, state=idle_state)
            return AssistantPracticeAdvanceResult(
                practice_run_id=run.run_id,
                submitted_attempt=submitted_attempt,
                next_question=None,
                run_completed=True,
                run_summary=run.summary.model_dump(mode="json"),
                state=idle_state,
            )
        refreshed_state = AssistantPracticeState(
            practice_run_id=run.run_id,
            current_attempt_id=next_question.attempt_id,
            current_position=next_question.position,
            total_items=next_question.total_items,
            awaiting_user_answer=True,
        )
        self._persist_state(actor=actor, session_id=session_id, state=refreshed_state)
        return AssistantPracticeAdvanceResult(
            practice_run_id=run.run_id,
            submitted_attempt=submitted_attempt,
            next_question=next_question,
            run_completed=False,
            run_summary=None,
            state=refreshed_state,
        )

    def end_active_practice(
        self,
        *,
        actor: Actor,
        session_id: str,
    ) -> AssistantEndPracticeResult:
        state = self._load_state(actor=actor, session_id=session_id)
        idle_state = AssistantPracticeState()
        self._persist_state(actor=actor, session_id=session_id, state=idle_state)
        return AssistantEndPracticeResult(
            ended=state.practice_run_id is not None,
            practice_run_id=state.practice_run_id,
            state=idle_state,
        )

    def _build_run_items(
        self,
        *,
        collection: CollectionView,
        args: StartCollectionPracticeToolArgs,
    ) -> list[
        StartQuickPracticeRunItemCommand | StartInterviewRunItemCommand | StartScenarioRunItemCommand
    ]:
        items: list[
            StartQuickPracticeRunItemCommand | StartInterviewRunItemCommand | StartScenarioRunItemCommand
        ] = []

        prompt_items = self._select_prompt_items(collection=collection, args=args)
        for prompt_item in prompt_items:
            items.append(_prompt_item_to_run_item(prompt_item))

        scenarios = self._select_scenarios(collection=collection, args=args)
        for scenario in scenarios:
            items.extend(_scenario_to_run_items(scenario))

        if not items:
            raise validation_error(
                "Collection did not contain any practice-ready items",
                code="SS-VALIDATION-210",
                details={"collection_id": collection.id},
            )
        return items[: args.item_limit]

    def _select_prompt_items(
        self,
        *,
        collection: CollectionView,
        args: StartCollectionPracticeToolArgs,
    ) -> list[PromptItemView]:
        if args.prompt_item_ids:
            return _ordered_prompt_items(collection, args.prompt_item_ids)
        if not args.include_prompt_items:
            return []
        return [
            prompt_item
            for prompt_item in collection.prompt_items
            if prompt_item.prompt_type in {"quick_practice_prompt", "interview_prompt"}
        ]

    def _select_scenarios(
        self,
        *,
        collection: CollectionView,
        args: StartCollectionPracticeToolArgs,
    ) -> list[ScenarioView]:
        if args.scenario_ids:
            return _ordered_scenarios(collection, args.scenario_ids)
        if not args.include_scenarios:
            return []
        return list(collection.scenarios)

    def _latest_user_message(self, actor: Actor, session_id: str) -> str:
        history = self._repository.load_history(actor=actor, session_id=session_id, limit=8)
        return next(
            (
                message.content
                for message in reversed(history)
                if message.role == AssistantMessageRole.USER
            ),
            "",
        )

    def _load_state(self, *, actor: Actor, session_id: str) -> AssistantPracticeState:
        metadata = self._repository.load_session_metadata(actor=actor, session_id=session_id)
        return AssistantPracticeState.from_session_metadata(metadata)

    def _persist_state(
        self,
        *,
        actor: Actor,
        session_id: str,
        state: AssistantPracticeState,
    ) -> None:
        metadata = self._repository.load_session_metadata(actor=actor, session_id=session_id)
        metadata.update(state.metadata_fragment())
        self._repository.update_session_metadata(
            actor=actor,
            session_id=session_id,
            metadata_payload=metadata,
        )


def _ordered_prompt_items(collection: CollectionView, prompt_item_ids: list[str]) -> list[PromptItemView]:
    prompt_items = {prompt_item.id: prompt_item for prompt_item in collection.prompt_items}
    ordered: list[PromptItemView] = []
    for prompt_item_id in prompt_item_ids:
        prompt_item = prompt_items.get(prompt_item_id)
        if prompt_item is None:
            raise validation_error(
                "Prompt item was not found in the collection",
                code="SS-VALIDATION-211",
                details={"collection_id": collection.id, "prompt_item_id": prompt_item_id},
            )
        ordered.append(prompt_item)
    return ordered


def _ordered_scenarios(collection: CollectionView, scenario_ids: list[str]) -> list[ScenarioView]:
    scenarios = {scenario.id: scenario for scenario in collection.scenarios}
    ordered: list[ScenarioView] = []
    for scenario_id in scenario_ids:
        scenario = scenarios.get(scenario_id)
        if scenario is None:
            raise validation_error(
                "Scenario was not found in the collection",
                code="SS-VALIDATION-212",
                details={"collection_id": collection.id, "scenario_id": scenario_id},
            )
        ordered.append(scenario)
    return ordered


def _prompt_item_to_run_item(
    prompt_item: PromptItemView,
) -> StartQuickPracticeRunItemCommand | StartInterviewRunItemCommand:
    if prompt_item.prompt_type == "quick_practice_prompt":
        return StartQuickPracticeRunItemCommand(
            practice_type=PracticeType.QUICK_PRACTICE.value,
            prompt_item_id=prompt_item.id,
        )
    if prompt_item.prompt_type == "interview_prompt":
        return StartInterviewRunItemCommand(
            practice_type=PracticeType.INTERVIEW.value,
            prompt_item_id=prompt_item.id,
        )
    raise validation_error(
        "Prompt item was not practice-compatible",
        code="SS-VALIDATION-213",
        details={"prompt_item_id": prompt_item.id, "prompt_type": prompt_item.prompt_type},
    )


def _scenario_to_run_item(scenario: ScenarioView) -> StartScenarioRunItemCommand:
    return StartScenarioRunItemCommand(
        practice_type=PracticeType.SCENARIO.value,
        scenario_id=scenario.id,
        artifacts=[
            {
                "artifact_type": artifact.artifact_type,
                "title": artifact.title,
                "body": artifact.body,
            }
            for artifact in scenario.supporting_artifacts
        ],
    )


def _scenario_to_run_items(scenario: ScenarioView) -> list[StartScenarioRunItemCommand]:
    if not scenario.questions:
        return [_scenario_to_run_item(scenario)]
    return [
        StartScenarioRunItemCommand(
            practice_type=PracticeType.SCENARIO.value,
            scenario_id=scenario.id,
            artifacts=[
                {
                    "artifact_type": artifact.artifact_type,
                    "title": artifact.title,
                    "body": artifact.body,
                }
                for artifact in scenario.supporting_artifacts
            ],
            question_text=question,
            question_index=index,
            question_count=len(scenario.questions),
        )
        for index, question in enumerate(scenario.questions, start=1)
    ]


def _current_question_from_run(run: PracticeRunView) -> AssistantPracticeQuestionView | None:
    if run.current_attempt_id is None:
        return None
    for item in run.items:
        if item.attempt.id != run.current_attempt_id:
            continue
        return AssistantPracticeQuestionView(
            practice_run_id=run.run_id,
            attempt_id=item.attempt.id,
            session_id=item.attempt.session_id,
            position=item.position,
            total_items=run.total_items,
            prompt=item.attempt.prompt,
        )
    raise validation_error(
        "Practice run current attempt was not present in the run items",
        code="SS-VALIDATION-214",
        details={"practice_run_id": run.run_id, "current_attempt_id": run.current_attempt_id},
    )
