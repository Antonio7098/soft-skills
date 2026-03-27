"""Fixture seeding for smoke suites."""

from __future__ import annotations

from .backend import JsonObject, SmokeBackendClient
from .models import PracticeFixtures


class PracticeFixtureSeeder:
    """Seeds smoke data required for practice flows."""

    def __init__(self, backend: SmokeBackendClient) -> None:
        self._backend = backend

    async def seed(self, user_id: str) -> PracticeFixtures:
        scenario = await self._seed_scenario(user_id)
        quick_prompt = await self._seed_quick_practice_prompt(user_id)
        interview_prompt = await self._seed_interview_prompt(user_id)
        return PracticeFixtures(
            quick_prompt_id=str(quick_prompt["id"]),
            interview_prompt_id=str(interview_prompt["id"]),
            scenario_id=str(scenario["id"]),
        )

    async def _seed_quick_practice_prompt(self, user_id: str) -> JsonObject:
        collection_id = await self._backend.create_collection(
            user_id=user_id,
            title="Smoke Quick Practice",
            content_format_mix=["quick_practice_prompt"],
            target_skill_slugs=["active-listening", "expectation-setting"],
            target_competency_slugs=["stakeholder-management"],
            rubric_ids=["quick_practice_reset_timeline@v1"],
        )
        return await self._backend.create_prompt_item(
            collection_id=collection_id,
            user_id=user_id,
            operation="create quick-practice prompt item",
            payload={
                "prompt_type": "quick_practice_prompt",
                "title": "Reset the timeline",
                "prompt_text": (
                    "A client asks for an impossible delivery date. Respond with empathy "
                    "and a realistic next step."
                ),
                "difficulty": "intermediate",
                "target_skill_slugs": ["active-listening", "expectation-setting"],
                "rubric_id": "quick_practice_reset_timeline@v1",
            },
        )

    async def _seed_interview_prompt(self, user_id: str) -> JsonObject:
        collection_id = await self._backend.create_collection(
            user_id=user_id,
            title="Smoke Interview Practice",
            content_format_mix=["interview_prompt"],
            target_skill_slugs=["active-listening", "decision-justification"],
            target_competency_slugs=["adaptability"],
            rubric_ids=["interview_text@v1"],
        )
        return await self._backend.create_prompt_item(
            collection_id=collection_id,
            user_id=user_id,
            operation="create interview prompt item",
            payload={
                "prompt_type": "interview_prompt",
                "title": "Lead through ambiguity",
                "prompt_text": (
                    "Tell me about a time you had to make a decision with incomplete information."
                ),
                "difficulty": "intermediate",
                "target_skill_slugs": ["active-listening", "decision-justification"],
                "rubric_id": "interview_text@v1",
            },
        )

    async def _seed_scenario(self, user_id: str) -> JsonObject:
        collection_id = await self._backend.create_collection(
            user_id=user_id,
            title="Smoke Scenario Practice",
            content_format_mix=["scenario_step"],
            target_skill_slugs=["expectation-setting", "prioritization-under-pressure"],
            target_competency_slugs=["managing-ambiguity"],
            rubric_ids=["scenario_text@v1"],
        )
        return await self._backend.create_scenario(
            collection_id=collection_id,
            user_id=user_id,
            payload={
                "title": "Escalating launch risk",
                "business_context": (
                    "An AI feature launch is at risk after legal review surfaced new concerns."
                ),
                "learner_objective": "Re-align the sponsor without hiding delivery risk.",
                "constraints": ["The launch date is on the board agenda tomorrow."],
                "stakeholder_tensions": ["Legal wants a delay and sales wants the current date."],
                "target_skill_slugs": [
                    "expectation-setting",
                    "prioritization-under-pressure",
                ],
                "rubric_id": "scenario_text@v1",
                "mock_company": {
                    "name": "Northstar AI",
                    "industry": "Enterprise SaaS",
                    "operating_context": "Scaling quickly under board scrutiny.",
                },
                "mock_people": [
                    {
                        "name": "Maya Chen",
                        "role": "VP Sales",
                        "goals": ["Keep the launch date"],
                        "communication_style": "Direct and urgent",
                        "relationship_to_scenario": "Commercial sponsor pushing for launch",
                    },
                    {
                        "name": "Jordan Singh",
                        "role": "Legal Counsel",
                        "goals": ["Reduce regulatory exposure"],
                        "communication_style": "Precise and cautious",
                        "relationship_to_scenario": "Risk owner blocking approval",
                    },
                ],
            },
        )
