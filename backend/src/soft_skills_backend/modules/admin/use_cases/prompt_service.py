"""Prompt registry application service."""

from __future__ import annotations

from typing import Any

from soft_skills_backend.modules.admin.contracts.commands import (
    ArchivePromptCommand,
    ComparePromptsCommand,
    CreatePromptCommand,
    PublishPromptCommand,
    UpdatePromptCommand,
)
from soft_skills_backend.modules.admin.contracts.views import (
    PromptAnalyticsView,
    PromptCompareView,
    PromptSummaryView,
    PromptVersionView,
)
from soft_skills_backend.config import Settings
from soft_skills_backend.modules.admin.domain.prompt_validation import (
    PromptValidationError,
    validate_prompt_definition,
)
from soft_skills_backend.modules.admin.infra.prompt_repository import PromptRepository
from soft_skills_backend.shared.auth import Actor
from soft_skills_backend.shared.errors import validation_error


class PromptService:
    """Application service for prompt registry management."""

    def __init__(self, *, settings: Settings, prompts: PromptRepository) -> None:
        self._settings = settings
        self._prompts = prompts

    def list_prompts(self, actor: Actor) -> list[PromptSummaryView]:
        """List all prompt names with latest published version."""
        del actor
        self._ensure_seeded()
        name_records = self._prompts.list_all_names()
        return [
            PromptSummaryView(
                name=name,
                prompt_type=record.prompt_type,
                latest_version=record.version,
                status=record.status,
                created_at=record.created_at.isoformat(),
            )
            for name, record in name_records
        ]

    def list_versions(self, actor: Actor, name: str) -> list[PromptVersionView]:
        """List all versions of a prompt."""
        del actor
        self._ensure_seeded()
        records = self._prompts.list_by_name(name)
        return [
            PromptVersionView(
                id=r.id,
                name=r.name,
                version=r.version,
                prompt_type=r.prompt_type,
                template=r.template,
                variables_schema=r.variables_schema,
                output_schema=r.output_schema,
                status=r.status,
                parent_version_id=r.parent_version_id,
                created_at=r.created_at.isoformat(),
                updated_at=r.updated_at.isoformat(),
            )
            for r in records
        ]

    def get_version(self, actor: Actor, name: str, version: str) -> PromptVersionView | None:
        """Get a specific prompt version."""
        del actor
        self._ensure_seeded()
        record = self._prompts.get_by_name_version(name, version)
        if record is None:
            return None
        return PromptVersionView(
            id=record.id,
            name=record.name,
            version=record.version,
            prompt_type=record.prompt_type,
            template=record.template,
            variables_schema=record.variables_schema,
            output_schema=record.output_schema,
            status=record.status,
            parent_version_id=record.parent_version_id,
            created_at=record.created_at.isoformat(),
            updated_at=record.updated_at.isoformat(),
        )

    def create_prompt(self, actor: Actor, command: CreatePromptCommand) -> PromptVersionView:
        """Create a new prompt version (draft status)."""
        del actor
        self._validate_definition(command.template, command.variables_schema)
        record = self._prompts.create(
            name=command.name,
            version=command.version,
            prompt_type=command.prompt_type,
            template=command.template,
            variables_schema=command.variables_schema,
            output_schema=command.output_schema,
            status="draft",
            parent_version_id=command.parent_version_id,
        )
        return PromptVersionView(
            id=record.id,
            name=record.name,
            version=record.version,
            prompt_type=record.prompt_type,
            template=record.template,
            variables_schema=record.variables_schema,
            output_schema=record.output_schema,
            status=record.status,
            parent_version_id=record.parent_version_id,
            created_at=record.created_at.isoformat(),
            updated_at=record.updated_at.isoformat(),
        )

    def update_prompt(
        self,
        actor: Actor,
        name: str,
        version: str,
        command: UpdatePromptCommand,
    ) -> PromptVersionView | None:
        """Update a draft prompt version."""
        del actor
        self._ensure_seeded()
        record = self._prompts.get_by_name_version(name, version)
        if record is None:
            return None
        if record.status != "draft":
            from soft_skills_backend.shared.errors import domain_error

            raise domain_error(
                "Only draft prompts can be updated",
                code="SS-DOMAIN-006",
                status_code=400,
                details={"name": name, "version": version, "status": record.status},
            )
        template = command.template if command.template is not None else record.template
        variables_schema = (
            command.variables_schema
            if command.variables_schema is not None
            else record.variables_schema
        )
        self._validate_definition(template, variables_schema)
        updated = self._prompts.update(
            record.id,
            template=command.template,
            variables_schema=command.variables_schema,
            output_schema=command.output_schema,
        )
        if updated is None:
            return None
        return PromptVersionView(
            id=updated.id,
            name=updated.name,
            version=updated.version,
            prompt_type=updated.prompt_type,
            template=updated.template,
            variables_schema=updated.variables_schema,
            output_schema=updated.output_schema,
            status=updated.status,
            parent_version_id=updated.parent_version_id,
            created_at=updated.created_at.isoformat(),
            updated_at=updated.updated_at.isoformat(),
        )

    def publish_prompt(
        self, actor: Actor, name: str, version: str, command: PublishPromptCommand
    ) -> PromptVersionView | None:
        """Publish a draft prompt to production."""
        del actor
        del command
        self._ensure_seeded()
        record = self._prompts.get_by_name_version(name, version)
        if record is None:
            return None
        if record.status != "draft":
            from soft_skills_backend.shared.errors import domain_error

            raise domain_error(
                "Only draft prompts can be published",
                code="SS-DOMAIN-007",
                status_code=400,
                details={"name": name, "version": version, "status": record.status},
            )
        updated = self._prompts.update(record.id, status="published")
        if updated is None:
            return None
        return PromptVersionView(
            id=updated.id,
            name=updated.name,
            version=updated.version,
            prompt_type=updated.prompt_type,
            template=updated.template,
            variables_schema=updated.variables_schema,
            output_schema=updated.output_schema,
            status=updated.status,
            parent_version_id=updated.parent_version_id,
            created_at=updated.created_at.isoformat(),
            updated_at=updated.updated_at.isoformat(),
        )

    def archive_prompt(
        self, actor: Actor, name: str, version: str, command: ArchivePromptCommand
    ) -> PromptVersionView | None:
        """Archive a published prompt."""
        del actor
        del command
        self._ensure_seeded()
        record = self._prompts.get_by_name_version(name, version)
        if record is None:
            return None
        if record.status != "published":
            from soft_skills_backend.shared.errors import domain_error

            raise domain_error(
                "Only published prompts can be archived",
                code="SS-DOMAIN-008",
                status_code=400,
                details={"name": name, "version": version, "status": record.status},
            )
        updated = self._prompts.update(record.id, status="archived")
        if updated is None:
            return None
        return PromptVersionView(
            id=updated.id,
            name=updated.name,
            version=updated.version,
            prompt_type=updated.prompt_type,
            template=updated.template,
            variables_schema=updated.variables_schema,
            output_schema=updated.output_schema,
            status=updated.status,
            parent_version_id=updated.parent_version_id,
            created_at=updated.created_at.isoformat(),
            updated_at=updated.updated_at.isoformat(),
        )

    def get_analytics(self, actor: Actor, name: str, version: str) -> PromptAnalyticsView | None:
        """Get performance metrics for a prompt version."""
        del actor
        self._ensure_seeded()
        record = self._prompts.get_by_name_version(name, version)
        if record is None:
            return None
        metrics = self._prompts.get_render_metrics(record.id)
        if metrics is None:
            return PromptAnalyticsView(
                prompt_version_id=record.id,
                name=record.name,
                version=record.version,
                render_count=0,
                success_count=0,
                failure_count=0,
                avg_latency_ms=None,
                total_tokens=0,
                last_rendered_at=None,
            )
        return PromptAnalyticsView(
            prompt_version_id=metrics.prompt_version_id,
            name=record.name,
            version=record.version,
            render_count=metrics.render_count,
            success_count=metrics.success_count,
            failure_count=metrics.failure_count,
            avg_latency_ms=metrics.avg_latency_ms,
            total_tokens=metrics.total_tokens,
            last_rendered_at=metrics.last_rendered_at.isoformat()
            if metrics.last_rendered_at
            else None,
        )

    def compare_prompts(
        self, actor: Actor, command: ComparePromptsCommand
    ) -> PromptCompareView | None:
        """Compare two prompt versions for A/B testing."""
        del actor
        self._ensure_seeded()
        record_a = self._prompts.get_by_name_version(command.name, command.version_a)
        record_b = self._prompts.get_by_name_version(command.name, command.version_b)
        if record_a is None or record_b is None:
            return None
        metrics_a = self._prompts.get_render_metrics(record_a.id)
        metrics_b = self._prompts.get_render_metrics(record_b.id)

        def _to_view(m: Any, *, version: str) -> PromptAnalyticsView | None:
            if m is None:
                return None
            return PromptAnalyticsView(
                prompt_version_id=m.prompt_version_id,
                name=record_a.name,
                version=version,
                render_count=m.render_count,
                success_count=m.success_count,
                failure_count=m.failure_count,
                avg_latency_ms=m.avg_latency_ms,
                total_tokens=m.total_tokens,
                last_rendered_at=m.last_rendered_at.isoformat() if m.last_rendered_at else None,
            )

        return PromptCompareView(
            name=command.name,
            version_a=command.version_a,
            version_b=command.version_b,
            template_a=record_a.template,
            template_b=record_b.template,
            variables_schema_a=record_a.variables_schema,
            variables_schema_b=record_b.variables_schema,
            metrics_a=_to_view(metrics_a, version=record_a.version),
            metrics_b=_to_view(metrics_b, version=record_b.version),
        )

    def _ensure_seeded(self) -> None:
        from soft_skills_backend.modules.admin.domain.builtin_prompts import (
            built_in_prompt_definitions,
        )

        self._prompts.ensure_seeded(built_in_prompt_definitions(self._settings))

    def _validate_definition(
        self,
        template: str,
        variables_schema: dict[str, object],
    ) -> None:
        try:
            validate_prompt_definition(
                template=template,
                variables_schema=variables_schema,
            )
        except PromptValidationError as exc:
            raise validation_error(
                "Prompt definition failed validation",
                code=f"SS-VALIDATION-PROMPT-{exc.stage.upper()}",
                details=exc.details,
            ) from exc
