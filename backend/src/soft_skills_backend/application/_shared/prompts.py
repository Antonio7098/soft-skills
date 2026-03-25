"""Centralized prompt templates for all application services."""

from __future__ import annotations

ASSESSMENT_PROMPT_NAME = "quick-practice-assessment"

QUICK_PRACTICE_ASSESSMENT_PROMPT = """Assess this SoftSkills text practice response.
Practice mode: {practice_type}
Prompt type: {prompt_type}
Prompt: {prompt_text}
Additional context:
{context_block}
Learner response: {response_text}
Target role: {target_role}
Learner goals: {goals}
Prior assessed attempts: {prior_assessed_attempts}
Target skills: {skill_slugs}
Rubric version: {rubric_version}
Return JSON with these required fields exactly:
- prompt_version: '{prompt_version}'
- rubric_version: '{rubric_version}'
- provider: '{provider}'
- model_slug: '{model_slug}'
- overall_score: integer 1-5
- rationale: string
- skill_scores: array of objects with skill_slug, score, rationale
- evidence: array of objects with skill_slug, quote, explanation
- strengths: array of strings
- weaknesses: array of strings
- next_actions: array of strings
Each evidence quote must be copied directly from the learner response."""
