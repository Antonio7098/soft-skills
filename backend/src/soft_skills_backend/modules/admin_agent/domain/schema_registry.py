"""Admin-agent safe schema registry."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AdminAgentJoinHint:
    left_view: str
    left_column: str
    right_view: str
    right_column: str
    description: str


@dataclass(frozen=True, slots=True)
class AdminAgentViewSchema:
    name: str
    description: str
    columns: tuple[str, ...]
    examples: tuple[str, ...]


class AdminAgentSchemaRegistry:
    """Allowlisted admin-safe view metadata for planning and validation."""

    def __init__(self) -> None:
        self._views = {
            view.name: view
            for view in (
                AdminAgentViewSchema(
                    name="admin_agent_workflow_events_v",
                    description=(
                        "Organisation-scoped workflow events with safe identifiers, event types, "
                        "error codes, and timestamps."
                    ),
                    columns=(
                        "organisation_id",
                        "event_id",
                        "event_type",
                        "request_id",
                        "trace_id",
                        "workflow_id",
                        "error_code",
                        "occurred_at",
                    ),
                    examples=(
                        "SELECT event_type, COUNT(*) AS event_count "
                        "FROM admin_agent_workflow_events_v "
                        "GROUP BY event_type ORDER BY event_count DESC LIMIT 10",
                    ),
                ),
                AdminAgentViewSchema(
                    name="admin_agent_pipeline_runs_v",
                    description=(
                        "Organisation-scoped Stageflow pipeline run telemetry with status, "
                        "failure stage, actor alias, and timing."
                    ),
                    columns=(
                        "organisation_id",
                        "pipeline_run_id",
                        "pipeline_name",
                        "topology",
                        "execution_mode",
                        "run_status",
                        "request_id",
                        "trace_id",
                        "actor_alias",
                        "failed_stage",
                        "error_summary",
                        "started_at",
                        "finished_at",
                    ),
                    examples=(
                        "SELECT pipeline_name, run_status, COUNT(*) AS run_count "
                        "FROM admin_agent_pipeline_runs_v "
                        "GROUP BY pipeline_name, run_status "
                        "ORDER BY run_count DESC LIMIT 20",
                    ),
                ),
                AdminAgentViewSchema(
                    name="admin_agent_provider_calls_v",
                    description=(
                        "Organisation-scoped provider call telemetry without prompts or "
                        "completions. Safe for operational latency and failure investigation."
                    ),
                    columns=(
                        "organisation_id",
                        "call_id",
                        "operation",
                        "provider",
                        "model_id",
                        "success",
                        "latency_ms",
                        "pipeline_run_id",
                        "request_id",
                        "trace_id",
                        "created_at",
                    ),
                    examples=(
                        "SELECT provider, operation, AVG(latency_ms) AS avg_latency_ms "
                        "FROM admin_agent_provider_calls_v "
                        "WHERE success = 1 "
                        "GROUP BY provider, operation "
                        "ORDER BY avg_latency_ms DESC LIMIT 20",
                    ),
                ),
                AdminAgentViewSchema(
                    name="admin_agent_assistant_sessions_v",
                    description=(
                        "Organisation-scoped assistant session metadata with pseudonymous users "
                        "and turn counts. No conversation text is exposed."
                    ),
                    columns=(
                        "organisation_id",
                        "session_id",
                        "user_alias",
                        "session_title",
                        "session_status",
                        "turn_count",
                        "created_at",
                        "updated_at",
                    ),
                    examples=(
                        "SELECT session_status, COUNT(*) AS session_count "
                        "FROM admin_agent_assistant_sessions_v "
                        "GROUP BY session_status ORDER BY session_count DESC LIMIT 10",
                    ),
                ),
                AdminAgentViewSchema(
                    name="admin_agent_evaluation_runs_v",
                    description=(
                        "Organisation-scoped evaluation execution records with pseudonymous "
                        "actors, suite metadata, pass/fail status, and pipeline lineage."
                    ),
                    columns=(
                        "organisation_id",
                        "evaluation_run_id",
                        "suite_id",
                        "suite_type",
                        "suite_version",
                        "run_status",
                        "triggered_by_alias",
                        "learner_alias",
                        "passed",
                        "subject_type",
                        "subject_ref",
                        "request_id",
                        "trace_id",
                        "workflow_id",
                        "pipeline_run_id",
                        "started_at",
                        "completed_at",
                    ),
                    examples=(
                        "SELECT suite_type, run_status, COUNT(*) AS run_count "
                        "FROM admin_agent_evaluation_runs_v "
                        "GROUP BY suite_type, run_status ORDER BY run_count DESC LIMIT 20",
                    ),
                ),
            )
        }
        self._joins = (
            AdminAgentJoinHint(
                left_view="admin_agent_workflow_events_v",
                left_column="trace_id",
                right_view="admin_agent_pipeline_runs_v",
                right_column="trace_id",
                description="Link workflow events to the owning pipeline run trace.",
            ),
            AdminAgentJoinHint(
                left_view="admin_agent_provider_calls_v",
                left_column="pipeline_run_id",
                right_view="admin_agent_pipeline_runs_v",
                right_column="pipeline_run_id",
                description="Link provider calls to their pipeline runs.",
            ),
            AdminAgentJoinHint(
                left_view="admin_agent_evaluation_runs_v",
                left_column="pipeline_run_id",
                right_view="admin_agent_pipeline_runs_v",
                right_column="pipeline_run_id",
                description="Link evaluation runs to pipeline runs when present.",
            ),
        )

    @property
    def join_hints(self) -> tuple[AdminAgentJoinHint, ...]:
        return self._joins

    def allowed_views(self) -> tuple[str, ...]:
        return tuple(self._views)

    def get_view(self, name: str) -> AdminAgentViewSchema:
        return self._views[name]

    def has_view(self, name: str) -> bool:
        return name in self._views

    def render_prompt_context(self) -> str:
        sections: list[str] = ["Allowed admin-safe views:"]
        for view in self._views.values():
            sections.append(f"- {view.name}: {view.description}")
            sections.append(f"  columns: {', '.join(view.columns)}")
            for example in view.examples:
                sections.append(f"  example: {example}")
        sections.append("Join hints:")
        for join in self._joins:
            sections.append(
                "- "
                f"{join.left_view}.{join.left_column} = "
                f"{join.right_view}.{join.right_column}: {join.description}"
            )
        sections.append("Rules:")
        sections.append("- SELECT only")
        sections.append("- no comments")
        sections.append("- no subqueries or unions")
        sections.append("- no SELECT * except COUNT(*)")
        sections.append("- query only the listed views")
        return "\n".join(sections)
