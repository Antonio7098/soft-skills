"""Centralized prompt templates for all application services."""

from __future__ import annotations

ASSESSMENT_PROMPT_NAME = "quick-practice-assessment"
CREATOR_STRUCTURED_GENERATION_PROMPT_NAME = "creator-structured-draft"
CREATOR_CHAT_GENERATION_PROMPT_NAME = "creator-chat-draft"

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

CREATOR_DRAFT_OUTPUT_FORMAT = """Return JSON with these required fields exactly:
- prompt_version: '{prompt_version}'
- provider: '{provider}'
- model_slug: '{model_slug}'
- title: string
- summary: string
- target_audience: string
- difficulty: one of introductory, intermediate, advanced
- content_format_mix: array of strings using only the allowed formats
- target_skill_slugs: array of strings using only the allowed skill slugs
- target_competency_slugs: array of strings using only the allowed competency slugs
- rubric_ids: array of strings using only the allowed rubric ids
- prompt_items: array of objects with prompt_type, title, prompt_text, difficulty, target_skill_slugs, rubric_id
- scenarios: array of objects with:
  - title
  - business_context
  - learner_objective
  - constraints
  - stakeholder_tensions
  - target_skill_slugs
  - rubric_id
  - mock_company: null or object with name, industry, operating_context
  - mock_people: array of objects with name, role, goals, communication_style, relationship_to_scenario
  - supporting_artifacts: array of objects with artifact_type, title, body
Rules:
- Preserve metadata exactly as requested.
- Use only the supplied taxonomy identifiers.
- Keep all generated content coherent, specific, and editable.
- Each scenario supporting artifact must reinforce the scenario rather than contradict it.
- If a nested object is present, every required nested field must be populated.
- Do not include markdown fences or prose outside the JSON object."""

CREATOR_STRUCTURED_GENERATION_PROMPT = """Generate an editable SoftSkills creator draft.
Collection metadata:
- title hint: {title_hint}
- target audience: {target_audience}
- difficulty: {difficulty}
- content formats: {content_format_mix}
- target skills: {target_skill_slugs}
- target competencies: {target_competency_slugs}
- rubric ids: {rubric_ids}
Generation brief:
- domain: {domain}
- workplace context: {workplace_context}
- scenario theme: {scenario_theme}
- realism notes: {realism_notes}
- prompt counts: {prompt_counts}
- scenario count: {scenario_count}
- max supporting artifacts per scenario: {scenario_artifact_count}
Allowed prompt types: {allowed_prompt_types}
Allowed artifact types: {allowed_artifact_types}
{output_format}"""

CREATOR_CHAT_GENERATION_PROMPT = """Generate an editable SoftSkills creator draft from the user's brief.
Collection metadata:
- target audience: {target_audience}
- difficulty: {difficulty}
- content formats: {content_format_mix}
- target skills: {target_skill_slugs}
- target competencies: {target_competency_slugs}
- rubric ids: {rubric_ids}
- requested counts: {requested_counts}
Allowed prompt types: {allowed_prompt_types}
Allowed artifact types: {allowed_artifact_types}
Hardened user brief:
{user_prompt}
{output_format}"""
