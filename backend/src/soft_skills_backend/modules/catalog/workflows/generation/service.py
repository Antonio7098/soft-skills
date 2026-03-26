"""Provider-backed creator generation workflows."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker
from stageflow.agent.security import PromptSecurityError, PromptSecurityPolicy
from stageflow.api import Pipeline, StageKind, stage

from soft_skills_backend.config import Settings
from soft_skills_backend.engines.config import (
    load_catalog_generation_runtime_config,
)
from soft_skills_backend.modules.catalog.contracts.collection_commands import (
    ChatCollectionGenerationCommand,
    CollectionCreateCommand,
    StructuredCollectionGenerationCommand,
)
from soft_skills_backend.modules.catalog.contracts.collection_views import (
    CollectionGenerationView,
)
from soft_skills_backend.modules.catalog.contracts.prompt_item_commands import (
    PromptItemCreateCommand,
)
from soft_skills_backend.modules.catalog.contracts.scenario_commands import ScenarioCreateCommand
from soft_skills_backend.modules.catalog.contracts.views import build_collection_view
from soft_skills_backend.modules.catalog.domain.constants import (
    ALLOWED_PROMPT_TYPES,
    ALLOWED_SCENARIO_ARTIFACT_TYPES,
)
from soft_skills_backend.modules.catalog.domain.models import (
    GeneratedCollectionDraft,
)
from soft_skills_backend.modules.catalog.domain.validators import (
    validate_collection_command,
    validate_generation_request,
    validate_prompt_command,
    validate_scenario_command,
)
from soft_skills_backend.modules.catalog.infra.events import CatalogEventRecorder
from soft_skills_backend.modules.practice.workflows.assessment import (
    PromptLibrary,
    PromptTemplate,
    StructuredOutputRejectionError,
    TypedLLMOutput,
)
from soft_skills_backend.platform.db.models import (
    CollectionRecord,
    ContentGenerationArtifactRecord,
    PromptItemRecord,
    ScenarioRecord,
)
from soft_skills_backend.platform.providers.llm.prompts import (
    CREATOR_CHAT_GENERATION_PROMPT,
    CREATOR_DRAFT_OUTPUT_FORMAT,
    CREATOR_STRUCTURED_GENERATION_PROMPT,
)
from soft_skills_backend.platform.workflows.stageflow import (
    StageflowPipelineSupport,
    StageflowStageResult,
    metadata_value,
    ok_output,
    payload_from_results,
    pipeline_run_id_from_context,
    request_id_from_context,
    run_logged_pipeline,
    user_id_from_context,
)
from soft_skills_backend.platform.workflows.stageflow_runtime import StageflowRuntime
from soft_skills_backend.shared.auth import Actor
from soft_skills_backend.shared.errors import validation_error
from soft_skills_backend.shared.ports.llm import LLMProvider
from soft_skills_backend.shared.ports.telemetry import ProviderCallContext


class CatalogGenerationService:
    """Generate draft collections through typed provider-backed pipelines."""

    def __init__(
        self,
        *,
        settings: Settings,
        session_factory: sessionmaker[Session],
        events: CatalogEventRecorder,
        llm_provider: LLMProvider,
        prompt_library: PromptLibrary,
        typed_output: TypedLLMOutput,
        prompt_security_policy: PromptSecurityPolicy,
        stageflow_runtime: StageflowRuntime,
    ) -> None:
        self._settings = settings
        self._session_factory = session_factory
        self._events = events
        self._llm_provider = llm_provider
        self._prompt_library = prompt_library
        self._typed_output = typed_output
        self._prompt_security_policy = prompt_security_policy
        self._stageflow = StageflowPipelineSupport.from_runtime(stageflow_runtime)

    async def generate_structured_draft(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        command: StructuredCollectionGenerationCommand,
    ) -> CollectionGenerationView:
        async def input_guard(_ctx) -> Any:
            with self._session_factory() as session:
                validate_generation_request(session, command)
            return ok_output(
                StageflowStageResult(
                    payload=command,
                    summary={"difficulty": command.difficulty, "mode": "structured"},
                )
            )

        async def generate_transform(ctx) -> Any:
            config = load_catalog_generation_runtime_config()
            hardened_brief = self._sanitize_generation_text(
                json.dumps(
                    {
                        "title_hint": command.title_hint,
                        "domain": command.domain,
                        "workplace_context": command.workplace_context,
                        "scenario_theme": command.scenario_theme,
                        "realism_notes": command.realism_notes,
                    },
                    sort_keys=True,
                )
            )
            rendered_prompt = self._prompt_library.render(
                config.structured_prompt_name,
                version=config.structured_prompt_version,
                variables={
                    "title_hint": command.title_hint or "none",
                    "target_audience": command.target_audience,
                    "difficulty": command.difficulty,
                    "content_format_mix": ", ".join(command.content_format_mix),
                    "target_skill_slugs": ", ".join(command.target_skill_slugs),
                    "target_competency_slugs": ", ".join(command.target_competency_slugs),
                    "rubric_ids": ", ".join(command.rubric_ids),
                    "domain": command.domain,
                    "workplace_context": command.workplace_context,
                    "scenario_theme": command.scenario_theme,
                    "realism_notes": hardened_brief,
                    "prompt_counts": json.dumps(
                        {
                            "quick_practice_prompt_count": command.counts.quick_practice_prompt_count,
                            "interview_prompt_count": command.counts.interview_prompt_count,
                        },
                        sort_keys=True,
                    ),
                    "scenario_count": command.counts.scenario_count,
                    "scenario_artifact_count": command.counts.scenario_artifact_count,
                    "allowed_prompt_types": ", ".join(sorted(ALLOWED_PROMPT_TYPES)),
                    "allowed_artifact_types": ", ".join(sorted(ALLOWED_SCENARIO_ARTIFACT_TYPES)),
                    "prompt_version": config.structured_prompt_version,
                    "provider": self._llm_provider.provider_name,
                    "model_slug": self._llm_provider.model_slug,
                    "output_format": CREATOR_DRAFT_OUTPUT_FORMAT.format(
                        prompt_version=config.structured_prompt_version,
                        provider=self._llm_provider.provider_name,
                        model_slug=self._llm_provider.model_slug,
                    ),
                },
            )
            try:
                typed_result = await self._typed_output.generate(
                    self._llm_provider,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You generate realistic SoftSkills creator drafts. Return JSON only."
                            ),
                        },
                        {"role": "user", "content": rendered_prompt.content},
                    ],
                    call_context=ProviderCallContext(
                        operation="catalog_structured_generation",
                        request_id=request_id_from_context(ctx),
                        trace_id=metadata_value(ctx, "trace_id"),
                        pipeline_run_id=pipeline_run_id_from_context(ctx),
                        workflow_id=metadata_value(ctx, "workflow_id"),
                        user_id=user_id_from_context(ctx),
                    ),
                )
            except StructuredOutputRejectionError as exc:
                raise validation_error(
                    exc.app_error.message,
                    code=exc.app_error.code,
                    details={
                        **(dict(exc.app_error.details or {})),
                        "raw_payload": exc.raw_payload,
                    },
                ) from exc
            return ok_output(
                StageflowStageResult(
                    payload=typed_result,
                    summary={"mode": "structured", "model_slug": typed_result.model_slug},
                )
            )

        async def output_guard(ctx) -> Any:
            typed_result = cast(Any, ctx.inputs.require_from("generate_transform", "payload"))
            draft = cast(GeneratedCollectionDraft, typed_result.parsed)
            with self._session_factory() as session:
                self._validate_generated_draft(
                    session,
                    collection_command=self._collection_command_from_draft(draft),
                    structured_command=command,
                    chat_command=None,
                    draft=draft,
                    resolved_model_slug=typed_result.model_slug,
                )
            return ok_output(
                StageflowStageResult(
                    payload=typed_result,
                    summary={"prompt_items": len(draft.prompt_items), "scenarios": len(draft.scenarios)},
                )
            )

        async def persistence_work(ctx) -> Any:
            typed_result = cast(Any, ctx.inputs.require_from("output_guard", "payload"))
            draft = cast(GeneratedCollectionDraft, typed_result.parsed)
            view = self._persist_generated_collection(
                actor=actor,
                request_id=request_id_from_context(ctx),
                trace_id=metadata_value(ctx, "trace_id"),
                workflow_id=metadata_value(ctx, "workflow_id"),
                generation_mode="structured",
                draft=draft,
                raw_payload=typed_result.raw_payload,
                input_payload=command.model_dump(mode="json"),
            )
            return ok_output(
                StageflowStageResult(
                    payload=view,
                    summary={"collection_id": view.collection.id, "generation_artifact_id": view.generation_artifact_id},
                )
            )

        pipeline = Pipeline.from_stages(
            stage("input_guard", cast(Any, input_guard), StageKind.GUARD),
            stage(
                "generate_transform",
                cast(Any, generate_transform),
                StageKind.TRANSFORM,
                dependencies=("input_guard",),
            ),
            stage(
                "output_guard",
                cast(Any, output_guard),
                StageKind.GUARD,
                dependencies=("generate_transform",),
            ),
            stage(
                "persistence_work",
                cast(Any, persistence_work),
                StageKind.WORK,
                dependencies=("output_guard",),
            ),
            name="catalog_structured_generation",
        )
        results = await run_logged_pipeline(
            self._stageflow,
            pipeline,
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id or f"catalog-structured-generation:{actor.user_id}:{request_id}",
            user_id=actor.user_id,
            execution_mode="catalog_generation",
            service="soft_skills_backend.catalog",
            idempotency_key=f"catalog_structured_generation:{actor.user_id}:{request_id}",
            idempotency_params=command.model_dump(mode="json"),
            timeout_ms=self._generation_timeout_ms,
        )
        return payload_from_results(results, "persistence_work", expected_type=CollectionGenerationView)

    async def generate_chat_draft(
        self,
        actor: Actor,
        *,
        request_id: str,
        trace_id: str,
        workflow_id: str | None,
        command: ChatCollectionGenerationCommand,
    ) -> CollectionGenerationView:
        async def input_guard(_ctx) -> Any:
            with self._session_factory() as session:
                validate_generation_request(session, command)
            return ok_output(
                StageflowStageResult(
                    payload=command,
                    summary={"difficulty": command.difficulty, "mode": "chat"},
                )
            )

        async def generate_transform(ctx) -> Any:
            config = load_catalog_generation_runtime_config()
            try:
                user_message, report = self._prompt_security_policy.build_user_message(command.prompt)
            except PromptSecurityError as exc:
                raise validation_error(
                    "Chat generation prompt was blocked by the prompt-security policy",
                    code="SS-VALIDATION-048",
                    details=exc.report.to_dict(),
                ) from exc

            rendered_prompt = self._prompt_library.render(
                config.chat_prompt_name,
                version=config.chat_prompt_version,
                variables={
                    "target_audience": command.target_audience,
                    "difficulty": command.difficulty,
                    "content_format_mix": ", ".join(command.content_format_mix),
                    "target_skill_slugs": ", ".join(command.target_skill_slugs),
                    "target_competency_slugs": ", ".join(command.target_competency_slugs),
                    "rubric_ids": ", ".join(command.rubric_ids),
                    "requested_counts": json.dumps(command.counts.model_dump(mode="json"), sort_keys=True),
                    "allowed_prompt_types": ", ".join(sorted(ALLOWED_PROMPT_TYPES)),
                    "allowed_artifact_types": ", ".join(sorted(ALLOWED_SCENARIO_ARTIFACT_TYPES)),
                    "user_prompt": user_message["content"],
                    "prompt_version": config.chat_prompt_version,
                    "provider": self._llm_provider.provider_name,
                    "model_slug": self._llm_provider.model_slug,
                    "output_format": CREATOR_DRAFT_OUTPUT_FORMAT.format(
                        prompt_version=config.chat_prompt_version,
                        provider=self._llm_provider.provider_name,
                        model_slug=self._llm_provider.model_slug,
                    ),
                },
            )
            try:
                typed_result = await self._typed_output.generate(
                    self._llm_provider,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You generate realistic SoftSkills creator drafts. Return JSON only."
                            ),
                        },
                        {"role": "user", "content": rendered_prompt.content},
                    ],
                    call_context=ProviderCallContext(
                        operation="catalog_chat_generation",
                        request_id=request_id_from_context(ctx),
                        trace_id=metadata_value(ctx, "trace_id"),
                        pipeline_run_id=pipeline_run_id_from_context(ctx),
                        workflow_id=metadata_value(ctx, "workflow_id"),
                        user_id=user_id_from_context(ctx),
                    ),
                )
            except StructuredOutputRejectionError as exc:
                raise validation_error(
                    exc.app_error.message,
                    code=exc.app_error.code,
                    details={
                        **(dict(exc.app_error.details or {})),
                        "raw_payload": exc.raw_payload,
                    },
                ) from exc
            summary = {
                "mode": "chat",
                "model_slug": typed_result.model_slug,
                "prompt_injection_detected": not report.allowed,
                "prompt_truncated": report.truncated,
            }
            return ok_output(StageflowStageResult(payload=typed_result, summary=summary))

        async def output_guard(ctx) -> Any:
            typed_result = cast(Any, ctx.inputs.require_from("generate_transform", "payload"))
            draft = cast(GeneratedCollectionDraft, typed_result.parsed)
            with self._session_factory() as session:
                self._validate_generated_draft(
                    session,
                    collection_command=self._collection_command_from_draft(draft),
                    structured_command=None,
                    chat_command=command,
                    draft=draft,
                    resolved_model_slug=typed_result.model_slug,
                )
            return ok_output(
                StageflowStageResult(
                    payload=typed_result,
                    summary={"prompt_items": len(draft.prompt_items), "scenarios": len(draft.scenarios)},
                )
            )

        async def persistence_work(ctx) -> Any:
            typed_result = cast(Any, ctx.inputs.require_from("output_guard", "payload"))
            draft = cast(GeneratedCollectionDraft, typed_result.parsed)
            view = self._persist_generated_collection(
                actor=actor,
                request_id=request_id_from_context(ctx),
                trace_id=metadata_value(ctx, "trace_id"),
                workflow_id=metadata_value(ctx, "workflow_id"),
                generation_mode="chat",
                draft=draft,
                raw_payload=typed_result.raw_payload,
                input_payload=command.model_dump(mode="json"),
            )
            return ok_output(
                StageflowStageResult(
                    payload=view,
                    summary={"collection_id": view.collection.id, "generation_artifact_id": view.generation_artifact_id},
                )
            )

        pipeline = Pipeline.from_stages(
            stage("input_guard", cast(Any, input_guard), StageKind.GUARD),
            stage(
                "generate_transform",
                cast(Any, generate_transform),
                StageKind.TRANSFORM,
                dependencies=("input_guard",),
            ),
            stage(
                "output_guard",
                cast(Any, output_guard),
                StageKind.GUARD,
                dependencies=("generate_transform",),
            ),
            stage(
                "persistence_work",
                cast(Any, persistence_work),
                StageKind.WORK,
                dependencies=("output_guard",),
            ),
            name="catalog_chat_generation",
        )
        results = await run_logged_pipeline(
            self._stageflow,
            pipeline,
            request_id=request_id,
            trace_id=trace_id,
            workflow_id=workflow_id or f"catalog-chat-generation:{actor.user_id}:{request_id}",
            user_id=actor.user_id,
            execution_mode="catalog_generation",
            service="soft_skills_backend.catalog",
            idempotency_key=f"catalog_chat_generation:{actor.user_id}:{request_id}",
            idempotency_params=command.model_dump(mode="json"),
            timeout_ms=self._generation_timeout_ms,
        )
        return payload_from_results(results, "persistence_work", expected_type=CollectionGenerationView)

    def _validate_generated_draft(
        self,
        session: Session,
        *,
        collection_command: CollectionCreateCommand,
        structured_command: StructuredCollectionGenerationCommand | None,
        chat_command: ChatCollectionGenerationCommand | None,
        draft: GeneratedCollectionDraft,
        resolved_model_slug: str,
    ) -> None:
        config = load_catalog_generation_runtime_config()
        validate_collection_command(session, collection_command)
        if structured_command is not None:
            self._validate_generation_metadata(
                draft=draft,
                prompt_version=config.structured_prompt_version,
                provider=self._llm_provider.provider_name,
                model_slug=resolved_model_slug,
                content_format_mix=structured_command.content_format_mix,
                skill_slugs=structured_command.target_skill_slugs,
                competency_slugs=structured_command.target_competency_slugs,
                rubric_ids=structured_command.rubric_ids,
                prompt_count=structured_command.counts.quick_practice_prompt_count
                + structured_command.counts.interview_prompt_count,
                scenario_count=structured_command.counts.scenario_count,
            )
        if chat_command is not None:
            self._validate_generation_metadata(
                draft=draft,
                prompt_version=config.chat_prompt_version,
                provider=self._llm_provider.provider_name,
                model_slug=resolved_model_slug,
                content_format_mix=chat_command.content_format_mix,
                skill_slugs=chat_command.target_skill_slugs,
                competency_slugs=chat_command.target_competency_slugs,
                rubric_ids=chat_command.rubric_ids,
                prompt_count=chat_command.counts.quick_practice_prompt_count
                + chat_command.counts.interview_prompt_count,
                scenario_count=chat_command.counts.scenario_count,
            )
        collection_record = CollectionRecord(
            id="draft",
            author_user_id="draft",
            title=draft.title,
            summary=draft.summary,
            target_audience=draft.target_audience,
            difficulty=draft.difficulty,
            lifecycle_state="draft",
            verification_state="unverified",
            source_type="manual",
            last_generation_artifact_id=None,
            content_format_mix=list(draft.content_format_mix),
            target_skill_slugs=list(draft.target_skill_slugs),
            target_competency_slugs=list(draft.target_competency_slugs),
            rubric_ids=list(draft.rubric_ids),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        for prompt_item in draft.prompt_items:
            validate_prompt_command(
                session,
                collection_record,
                PromptItemCreateCommand.model_validate(prompt_item.model_dump()),
            )
        for scenario in draft.scenarios:
            validate_scenario_command(
                session,
                collection_record,
                ScenarioCreateCommand.model_validate(scenario.model_dump()),
            )

    def _validate_generation_metadata(
        self,
        *,
        draft: GeneratedCollectionDraft,
        prompt_version: str,
        provider: str,
        model_slug: str,
        content_format_mix: list[str],
        skill_slugs: list[str],
        competency_slugs: list[str],
        rubric_ids: list[str],
        prompt_count: int,
        scenario_count: int,
    ) -> None:
        if draft.prompt_version != prompt_version:
            raise validation_error(
                "Generated draft prompt version did not match the requested contract",
                code="SS-VALIDATION-049",
                details={"expected": prompt_version, "actual": draft.prompt_version},
            )
        if draft.provider != provider:
            raise validation_error(
                "Generated draft provider did not match the executing provider",
                code="SS-VALIDATION-057",
                details={"expected": provider, "actual": draft.provider},
            )
        if draft.model_slug != model_slug:
            raise validation_error(
                "Generated draft model slug did not match the executing model",
                code="SS-VALIDATION-058",
                details={"expected": model_slug, "actual": draft.model_slug},
            )
        if list(draft.content_format_mix) != list(content_format_mix):
            raise validation_error(
                "Generated draft content formats drifted from the request",
                code="SS-VALIDATION-050",
            )
        if list(draft.target_skill_slugs) != list(skill_slugs):
            raise validation_error(
                "Generated draft target skills drifted from the request",
                code="SS-VALIDATION-051",
            )
        if list(draft.target_competency_slugs) != list(competency_slugs):
            raise validation_error(
                "Generated draft target competencies drifted from the request",
                code="SS-VALIDATION-052",
            )
        if list(draft.rubric_ids) != list(rubric_ids):
            raise validation_error(
                "Generated draft rubrics drifted from the request",
                code="SS-VALIDATION-053",
            )
        if len(draft.prompt_items) != prompt_count:
            raise validation_error(
                "Generated draft prompt count did not match the request",
                code="SS-VALIDATION-054",
                details={"expected": prompt_count, "actual": len(draft.prompt_items)},
            )
        if len(draft.scenarios) != scenario_count:
            raise validation_error(
                "Generated draft scenario count did not match the request",
                code="SS-VALIDATION-055",
                details={"expected": scenario_count, "actual": len(draft.scenarios)},
            )

    def _persist_generated_collection(
        self,
        *,
        actor: Actor,
        request_id: str,
        trace_id: str,
        workflow_id: str,
        generation_mode: str,
        draft: GeneratedCollectionDraft,
        raw_payload: dict[str, Any],
        input_payload: dict[str, Any],
    ) -> CollectionGenerationView:
        config = load_catalog_generation_runtime_config()
        source_type = "generated_structured" if generation_mode == "structured" else "generated_chat"
        now = datetime.now(UTC)
        with self._session_factory() as session:
            collection = CollectionRecord(
                id=uuid4().hex,
                author_user_id=actor.user_id,
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
                self._persist_scenario_children(
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
                output_payload=draft.model_dump(mode="json"),
                raw_payload=raw_payload,
                created_at=now,
            )
            session.add(artifact)
            session.flush()
            collection.last_generation_artifact_id = artifact.id
            session.commit()
            collection_view = build_collection_view(session, collection, actor=actor)
            artifact_id = artifact.id

        self._events.record(
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
        self._events.record(
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

    def _collection_command_from_draft(self, draft: GeneratedCollectionDraft) -> CollectionCreateCommand:
        return CollectionCreateCommand(
            title=draft.title,
            summary=draft.summary,
            target_audience=draft.target_audience,
            difficulty=draft.difficulty,
            content_format_mix=list(draft.content_format_mix),
            target_skill_slugs=list(draft.target_skill_slugs),
            target_competency_slugs=list(draft.target_competency_slugs),
            rubric_ids=list(draft.rubric_ids),
        )

    def _sanitize_generation_text(self, text: str) -> str:
        try:
            _, report = self._prompt_security_policy.build_user_message(text)
        except PromptSecurityError as exc:
            raise validation_error(
                "Structured generation input was blocked by the prompt-security policy",
                code="SS-VALIDATION-056",
                details=exc.report.to_dict(),
            ) from exc
        return report.sanitized_text

    @property
    def _generation_timeout_ms(self) -> int:
        return int(max(60_000, self._settings.smoke_timeout_seconds * 4_000))

    def _persist_scenario_children(
        self,
        session: Session,
        scenario_id: str,
        command: ScenarioCreateCommand,
    ) -> None:
        from soft_skills_backend.platform.db.models import (
            MockCompanyRecord,
            MockPersonRecord,
            ScenarioSupportingArtifactRecord,
        )

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


def build_catalog_generation_prompt_library(settings: Settings) -> PromptLibrary:
    """Build the versioned prompt library for creator generation."""

    del settings
    config = load_catalog_generation_runtime_config()
    library = PromptLibrary()
    library.register(
        PromptTemplate(
            name=config.structured_prompt_name,
            version=config.structured_prompt_version,
            template=CREATOR_STRUCTURED_GENERATION_PROMPT,
        ),
        make_default=True,
    )
    library.register(
        PromptTemplate(
            name=config.chat_prompt_name,
            version=config.chat_prompt_version,
            template=CREATOR_CHAT_GENERATION_PROMPT,
        ),
        make_default=True,
    )
    return library


def build_catalog_generation_typed_output(settings: Settings) -> TypedLLMOutput:
    """Build the typed output parser for creator generation."""

    config = load_catalog_generation_runtime_config()
    return TypedLLMOutput(
        GeneratedCollectionDraft,
        schema_version=config.output_schema_version,
        max_validation_retries=settings.creator_generation_validation_retries,
    )
