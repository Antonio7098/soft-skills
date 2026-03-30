"""Smoke test helpers."""

from __future__ import annotations

from soft_skills_backend.config import Settings

from .contracts import SmokeContext, SmokeDefinition, SmokeExecutionResult
from .registry import SmokeRegistry
from .runner import SmokeRunner
from .suites.admin_agent_smoke import AdminAgentSmoke
from .suites.admin_analytics_smoke import AdminAnalyticsSmoke
from .suites.admin_telemetry_smoke import AdminTelemetrySmoke
from .suites.admin_user_management_smoke import AdminUserManagementSmoke
from .suites.assessment_marking import (
    InterviewMarkingSmoke,
    MarkingRelationalPersistenceSmoke,
    QuickPracticeMarkingSmoke,
    ScenarioMarkingSmoke,
)
from .suites.assistant_runtime import (
    AssistantApprovalWorkflowSmoke,
    AssistantGenerationRuntimeSmoke,
    AssistantPracticeRuntimeSmoke,
    AssistantReadSqlDeniedSmoke,
    AssistantReadRuntimeSmoke,
    AssistantReadSqlWorkflowSmoke,
    AssistantStreamRuntimeSmoke,
)
from .suites.auth_flows import AuthFlowsSmoke
from .suites.content_generation import (
    ChatGenerationSmoke,
    ChatPromptItemGenerationSmoke,
    GenerationLatencyEnvelopeSmoke,
    StructuredGenerationSmoke,
    StructuredPromptItemGenerationSmoke,
)
from .suites.eval_dashboard_smoke import EvalDashboardSmoke
from .suites.evaluation_smoke import EvaluationSmoke
from .suites.full_user_journey import FullUserJourneySmoke
from .suites.generation_streaming import GenerationCancellationSmoke, GenerationStreamingSmoke
from .suites.organisation_smoke import OrganisationSmoke
from .suites.pipeline_visualization import PipelineVisualizationSmoke
from .suites.practice_run_lifecycle import PracticeRunLifecycleSmoke
from .suites.practice_session_flow import PracticeSessionFlowSmoke
from .suites.provider_baseline import ProviderBaselineSmoke
from .suites.telemetry_smoke import TelemetrySmoke


def build_default_registry() -> SmokeRegistry:
    """Build the default smoke registry."""

    return SmokeRegistry(
        [
            ProviderBaselineSmoke(),
            AdminAgentSmoke(),
            AssistantApprovalWorkflowSmoke(),
            AssistantReadSqlDeniedSmoke(),
            AssistantReadSqlWorkflowSmoke(),
            AssistantReadRuntimeSmoke(),
            AssistantGenerationRuntimeSmoke(),
            AssistantPracticeRuntimeSmoke(),
            AssistantStreamRuntimeSmoke(),
            StructuredGenerationSmoke(),
            ChatGenerationSmoke(),
            StructuredPromptItemGenerationSmoke(),
            ChatPromptItemGenerationSmoke(),
            GenerationLatencyEnvelopeSmoke(),
            GenerationStreamingSmoke(),
            GenerationCancellationSmoke(),
            AuthFlowsSmoke(),
            EvaluationSmoke(),
            EvalDashboardSmoke(),
            QuickPracticeMarkingSmoke(),
            InterviewMarkingSmoke(),
            ScenarioMarkingSmoke(),
            MarkingRelationalPersistenceSmoke(),
            PracticeSessionFlowSmoke(),
            PracticeRunLifecycleSmoke(),
            OrganisationSmoke(),
            AdminUserManagementSmoke(),
            AdminAnalyticsSmoke(),
            AdminTelemetrySmoke(),
            PipelineVisualizationSmoke(),
            TelemetrySmoke(),
            FullUserJourneySmoke(),
        ]
    )


def build_default_runner(settings: Settings | None = None) -> SmokeRunner:
    """Build the default centralized smoke runner."""

    return SmokeRunner(build_default_registry(), SmokeContext.create(settings))


__all__ = [
    "SmokeContext",
    "SmokeDefinition",
    "SmokeExecutionResult",
    "SmokeRegistry",
    "SmokeRunner",
    "build_default_registry",
    "build_default_runner",
]
