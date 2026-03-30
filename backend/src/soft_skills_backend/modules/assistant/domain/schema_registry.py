"""Assistant-safe SQL schema registry."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AssistantJoinHint:
    left_view: str
    left_column: str
    right_view: str
    right_column: str
    description: str


@dataclass(frozen=True, slots=True)
class AssistantViewSchema:
    name: str
    description: str
    columns: tuple[str, ...]
    scope_columns: tuple[str, ...]
    examples: tuple[str, ...]


class AssistantSchemaRegistry:
    """Allowlisted learner-safe views for SQL reads."""

    def __init__(self) -> None:
        self._views = {
            view.name: view
            for view in (
                AssistantViewSchema(
                    name="assistant_safe_collections_v",
                    description=(
                        "Collections visible to the learner within the current organisation."
                    ),
                    columns=(
                        "organisation_id",
                        "collection_id",
                        "title",
                        "summary",
                        "target_audience",
                        "difficulty",
                        "content_format_mix",
                        "target_skill_slugs",
                        "target_competency_slugs",
                        "author_user_id",
                        "saved_count",
                        "rating_count",
                        "avg_rating",
                        "created_at",
                        "updated_at",
                    ),
                    scope_columns=("organisation_id",),
                    examples=(
                        "SELECT title, difficulty, rating_count "
                        "FROM assistant_safe_collections_v "
                        "ORDER BY updated_at DESC LIMIT 5",
                    ),
                ),
                AssistantViewSchema(
                    name="assistant_safe_attempt_summaries_v",
                    description=(
                        "Recent attempt summaries for the authenticated learner without raw "
                        "response text."
                    ),
                    columns=(
                        "organisation_id",
                        "user_id",
                        "attempt_id",
                        "session_id",
                        "practice_run_id",
                        "practice_type",
                        "content_item_id",
                        "content_item_type",
                        "status",
                        "assessment_id",
                        "overall_score",
                        "strength_summary",
                        "next_action_summary",
                        "created_at",
                        "submitted_at",
                        "assessed_at",
                    ),
                    scope_columns=("organisation_id", "user_id"),
                    examples=(
                        "SELECT attempt_id, practice_type, overall_score, assessed_at "
                        "FROM assistant_safe_attempt_summaries_v "
                        "ORDER BY created_at DESC LIMIT 5",
                    ),
                ),
                AssistantViewSchema(
                    name="assistant_safe_progress_snapshots_v",
                    description=(
                        "Latest persisted progress snapshots for the authenticated learner."
                    ),
                    columns=(
                        "organisation_id",
                        "user_id",
                        "snapshot_id",
                        "source_assessment_id",
                        "weak_skill_slugs",
                        "stagnating_skill_slugs",
                        "coverage_gap_skill_slugs",
                        "skill_state_count",
                        "competency_state_count",
                        "created_at",
                    ),
                    scope_columns=("organisation_id", "user_id"),
                    examples=(
                        "SELECT weak_skill_slugs, coverage_gap_skill_slugs, created_at "
                        "FROM assistant_safe_progress_snapshots_v "
                        "ORDER BY created_at DESC LIMIT 1",
                    ),
                ),
                AssistantViewSchema(
                    name="assistant_safe_recommendations_v",
                    description=(
                        "Persisted recommendation summaries for the authenticated learner."
                    ),
                    columns=(
                        "organisation_id",
                        "user_id",
                        "recommendation_id",
                        "progress_snapshot_id",
                        "context_snapshot_id",
                        "candidate_count",
                        "top_pick_ref",
                        "top_pick_reason",
                        "alternative_refs",
                        "created_at",
                    ),
                    scope_columns=("organisation_id", "user_id"),
                    examples=(
                        "SELECT top_pick_ref, top_pick_reason, alternative_refs "
                        "FROM assistant_safe_recommendations_v "
                        "ORDER BY created_at DESC LIMIT 1",
                    ),
                ),
            )
        }
        self._joins = (
            AssistantJoinHint(
                left_view="assistant_safe_attempt_summaries_v",
                left_column="content_item_id",
                right_view="assistant_safe_collections_v",
                right_column="collection_id",
                description="Link attempts to their source collection when the content item is a collection.",
            ),
            AssistantJoinHint(
                left_view="assistant_safe_recommendations_v",
                left_column="progress_snapshot_id",
                right_view="assistant_safe_progress_snapshots_v",
                right_column="snapshot_id",
                description="Link recommendations to the progression snapshot that produced them.",
            ),
        )

    @property
    def join_hints(self) -> tuple[AssistantJoinHint, ...]:
        return self._joins

    def allowed_views(self) -> tuple[str, ...]:
        return tuple(self._views)

    def get_view(self, name: str) -> AssistantViewSchema:
        return self._views[name]

    def has_view(self, name: str) -> bool:
        return name in self._views

    def render_prompt_context(self) -> str:
        sections: list[str] = ["Allowed learner-safe views:"]
        for view in self._views.values():
            sections.append(f"- {view.name}: {view.description}")
            sections.append(f"  columns: {', '.join(view.columns)}")
            sections.append(f"  scope columns: {', '.join(view.scope_columns)}")
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
