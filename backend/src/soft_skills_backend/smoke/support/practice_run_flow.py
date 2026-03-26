"""Shared aggregate practice-run smoke flow helpers."""

from __future__ import annotations

from typing import SupportsFloat, SupportsInt, cast

from soft_skills_backend.shared.errors import provider_error

from ..suites.practice_run_lifecycle.contracts import (
    PracticeRunHistoryEntrySmokeResult,
    PracticeRunLifecycleCheckpointResult,
    PracticeRunLifecycleSmokeResult,
)
from .backend import JsonObject, SmokeBackendClient
from .models import PracticeFixtures


class PracticeRunSmokeFlow:
    """Executes aggregate practice-run smoke paths."""

    def __init__(self, backend: SmokeBackendClient) -> None:
        self._backend = backend

    async def run_lifecycle_smoke(
        self,
        user_id: str,
        fixtures: PracticeFixtures,
    ) -> PracticeRunLifecycleSmokeResult:
        run_payload = await self._backend.start_practice_run(
            user_id=user_id,
            payload=self._practice_run_request(fixtures),
        )
        run_id = str(run_payload["run_id"])
        items = cast(list[JsonObject], run_payload["items"])
        answers_by_attempt = self._build_answers_by_attempt(run_payload)
        first_attempt_id = str(cast(JsonObject, items[0]["attempt"])["id"])
        second_attempt_id = str(cast(JsonObject, items[1]["attempt"])["id"])

        self._assert_run_state(
            run_payload,
            expected_status="active",
            expected_total_items=3,
            expected_completed_items=0,
            expected_current_attempt_id=first_attempt_id,
        )

        first_submit = await self._backend.submit_attempt_response(
            user_id=user_id,
            attempt_id=first_attempt_id,
            response_text=answers_by_attempt[first_attempt_id],
        )
        self._assert_terminal_submit_response(first_submit, first_attempt_id)

        mid_run = await self._backend.get_practice_run(user_id=user_id, run_id=run_id)
        self._assert_run_state(
            mid_run,
            expected_status="active",
            expected_total_items=3,
            expected_completed_items=1,
            expected_current_attempt_id=second_attempt_id,
        )

        for attempt_id, response_text in answers_by_attempt.items():
            if attempt_id == first_attempt_id:
                continue
            response = await self._backend.submit_attempt_response(
                user_id=user_id,
                attempt_id=attempt_id,
                response_text=response_text,
            )
            self._assert_terminal_submit_response(response, attempt_id)

        complete_run = await self._backend.get_practice_run(user_id=user_id, run_id=run_id)
        self._assert_run_state(
            complete_run,
            expected_status="completed",
            expected_total_items=3,
            expected_completed_items=3,
            expected_current_attempt_id=None,
        )
        complete_summary = cast(JsonObject, complete_run["summary"])
        score_distribution = cast(dict[str, int], complete_summary["score_distribution"])
        validated_attempt_count = _as_int(complete_summary["validated_attempt_count"])
        self._require_equal(sorted(score_distribution), ["1", "2", "3", "4", "5"], "score keys")
        self._require_equal(sum(score_distribution.values()), validated_attempt_count, "score total")
        self._require_subset(
            self._practice_types_from_breakdown(complete_summary),
            ["interview", "quick_practice", "scenario"],
            "practice-type breakdown",
        )
        self._require_subset(
            self._skill_slugs_from_breakdown(complete_summary),
            [
                "active-listening",
                "decision-justification",
                "expectation-setting",
                "prioritization-under-pressure",
            ],
            "skill breakdown",
        )

        history = await self._backend.list_practice_runs(user_id=user_id)
        if len(history) != 1:
            raise provider_error(
                "Smoke practice-run history length was unexpected",
                code="SS-PROVIDER-016",
                details={"run_id": run_id, "history_count": len(history)},
            )
        history_entry = history[0]
        self._require_equal(str(history_entry["run_id"]), run_id, "history run id")
        self._require_equal(str(history_entry["status"]), "completed", "history status")
        self._require_equal(
            [str(item) for item in cast(list[object], history_entry["practice_types"])],
            ["quick_practice", "interview", "scenario"],
            "history practice types",
        )

        return PracticeRunLifecycleSmokeResult(
            status="ok",
            run_id=run_id,
            total_items=3,
            started=_checkpoint_result(run_payload),
            in_progress=_checkpoint_result(mid_run),
            completed=_checkpoint_result(complete_run),
            score_distribution=score_distribution,
            skill_slugs=self._skill_slugs_from_breakdown(complete_summary),
            practice_types=self._practice_types_from_breakdown(complete_summary),
            history_entry=_history_entry_result(history_entry),
        )

    def _practice_run_request(self, fixtures: PracticeFixtures) -> JsonObject:
        return {
            "items": [
                {"practice_type": "quick_practice", "prompt_item_id": fixtures.quick_prompt_id},
                {
                    "practice_type": "interview",
                    "prompt_item_id": fixtures.interview_prompt_id,
                    "competency_context": (
                        "Assess structured communication, tradeoff handling, and ownership."
                    ),
                    "interviewer_perspective": (
                        "You are responding to a consulting hiring manager."
                    ),
                },
                {
                    "practice_type": "scenario",
                    "scenario_id": fixtures.scenario_id,
                    "artifacts": [
                        {
                            "artifact_type": "email",
                            "title": "Board escalation note",
                            "body": "The board expects a recommendation before 9am tomorrow.",
                        }
                    ],
                },
            ],
        }

    def _build_answers_by_attempt(self, run_payload: JsonObject) -> dict[str, str]:
        items = cast(list[JsonObject], run_payload["items"])
        return {
            str(cast(JsonObject, items[0]["attempt"])["id"]): (
                "I hear why the date matters to you. The earliest realistic date is next "
                "Friday, and I can confirm any scope tradeoffs with the team by tomorrow afternoon."
            ),
            str(cast(JsonObject, items[1]["attempt"])["id"]): (
                "I led the decision by surfacing the uncertainty clearly, aligning the team on "
                "the tradeoff, and setting a next-morning checkpoint with a named owner."
            ),
            str(cast(JsonObject, items[2]["attempt"])["id"]): (
                "I would recommend a one-day delay, explain the legal risk directly, and "
                "propose a 7am checkpoint with sales and legal before the board meeting."
            ),
        }

    def _assert_run_state(
        self,
        payload: JsonObject,
        *,
        expected_status: str,
        expected_total_items: int,
        expected_completed_items: int,
        expected_current_attempt_id: str | None,
    ) -> None:
        summary = cast(JsonObject, payload["summary"])
        validated_items = _as_int(payload["validated_items"])
        failed_items = _as_int(payload["failed_items"])
        validated_attempt_count = _as_int(summary["validated_attempt_count"])
        failed_attempt_count = _as_int(summary["failed_attempt_count"])
        overall_score_average = _as_optional_float(summary["overall_score_average"])
        score_distribution = cast(dict[str, int], summary["score_distribution"])
        self._require_equal(str(payload["status"]), expected_status, "run status")
        self._require_equal(_as_int(payload["total_items"]), expected_total_items, "run total items")
        self._require_equal(_as_int(payload["completed_items"]), expected_completed_items, "run completed items")
        self._require_equal(validated_items + failed_items, expected_completed_items, "terminal item count")
        self._require_equal(validated_items, validated_attempt_count, "validated item count")
        self._require_equal(failed_items, failed_attempt_count, "failed item count")
        self._require_equal(
            None if payload["current_attempt_id"] is None else str(payload["current_attempt_id"]),
            expected_current_attempt_id,
            "current attempt id",
        )
        self._require_equal(sorted(score_distribution), ["1", "2", "3", "4", "5"], "score keys")
        self._require_equal(sum(score_distribution.values()), validated_attempt_count, "score total")
        if validated_attempt_count > 0:
            self._require_score_range(overall_score_average, "overall average")
        else:
            self._require_equal(overall_score_average, None, "overall average")

    def _practice_types_from_breakdown(self, summary: JsonObject) -> list[str]:
        return [str(item["practice_type"]) for item in cast(list[JsonObject], summary["practice_type_breakdown"])]

    def _skill_slugs_from_breakdown(self, summary: JsonObject) -> list[str]:
        return [str(item["skill_slug"]) for item in cast(list[JsonObject], summary["skill_breakdown"])]

    def _require_equal(self, actual: object, expected: object, label: str) -> None:
        if actual != expected:
            raise provider_error(
                "Smoke assertion failed",
                code="SS-PROVIDER-017",
                details={"label": label, "expected": expected, "actual": actual},
            )

    def _require_subset(self, actual: list[str], expected_superset: list[str], label: str) -> None:
        if not set(actual).issubset(set(expected_superset)):
            raise provider_error(
                "Smoke assertion failed",
                code="SS-PROVIDER-017",
                details={"label": label, "expected": expected_superset, "actual": actual},
            )

    def _require_score_range(self, value: float | None, label: str) -> None:
        if value is None or not 1.0 <= value <= 5.0:
            raise provider_error(
                "Smoke assertion failed",
                code="SS-PROVIDER-017",
                details={"label": label, "expected": "score between 1.0 and 5.0", "actual": value},
            )

    def _assert_terminal_submit_response(self, response: object, attempt_id: str) -> None:
        from httpx import Response

        if not isinstance(response, Response):
            raise provider_error(
                "Smoke submit response had an unexpected type",
                code="SS-PROVIDER-018",
                details={"attempt_id": attempt_id, "response_type": type(response).__name__},
            )
        if response.status_code not in {200, 422, 503}:
            raise provider_error(
                "Smoke backend step failed",
                code="SS-PROVIDER-011",
                details={
                    "operation": f"submit aggregate attempt {attempt_id}",
                    "status_code": response.status_code,
                    "body": response.text,
                },
            )


def _as_int(value: object) -> int:
    return int(cast(str | SupportsInt, value))


def _as_float(value: object) -> float:
    return float(cast(str | SupportsFloat, value))


def _as_optional_float(value: object) -> float | None:
    if value is None:
        return None
    return _as_float(value)


def _checkpoint_result(payload: JsonObject) -> PracticeRunLifecycleCheckpointResult:
    summary = cast(JsonObject, payload["summary"])
    return PracticeRunLifecycleCheckpointResult(
        status=str(payload["status"]),
        completed_items=_as_int(payload["completed_items"]),
        validated_items=_as_int(payload["validated_items"]),
        failed_items=_as_int(payload["failed_items"]),
        current_attempt_id=None if payload["current_attempt_id"] is None else str(payload["current_attempt_id"]),
        validated_attempt_count=_as_int(summary["validated_attempt_count"]),
        failed_attempt_count=_as_int(summary["failed_attempt_count"]),
        overall_score_average=_as_optional_float(summary["overall_score_average"]),
    )


def _history_entry_result(payload: JsonObject) -> PracticeRunHistoryEntrySmokeResult:
    return PracticeRunHistoryEntrySmokeResult(
        run_id=str(payload["run_id"]),
        status=str(payload["status"]),
        overall_score_average=_as_optional_float(payload["overall_score_average"]),
        practice_types=[str(item) for item in cast(list[object], payload["practice_types"])],
    )
