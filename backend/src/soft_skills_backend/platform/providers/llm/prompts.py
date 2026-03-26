"""Centralized prompt templates for all application services."""

from __future__ import annotations

ASSESSMENT_PROMPT_NAME = "quick-practice-assessment"
CREATOR_STRUCTURED_GENERATION_PROMPT_NAME = "creator-structured-draft"
CREATOR_CHAT_GENERATION_PROMPT_NAME = "creator-chat-draft"
CREATOR_PROMPT_ITEM_STRUCTURED_GENERATION_PROMPT_NAME = "creator-prompt-items-structured-plan"
CREATOR_PROMPT_ITEM_CHAT_GENERATION_PROMPT_NAME = "creator-prompt-items-chat-plan"
CREATOR_PROMPT_ITEM_WORKER_PROMPT_NAME = "creator-prompt-item-worker"
CREATOR_SCENARIO_WORKER_PROMPT_NAME = "creator-scenario-worker"

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

CREATOR_COLLECTION_BLUEPRINT_OUTPUT_FORMAT = """Return JSON with these required fields exactly:
- prompt_version: '{prompt_version}'
- provider: '{provider}'
- model_slug: '{model_slug}'
- title: string
- summary: string
- prompt_items: array of objects with:
  - prompt_type
  - title_hint
  - generation_brief
  - difficulty
  - target_skill_slugs
  - rubric_id
- scenarios: array of objects with:
  - title_hint
  - generation_brief
  - target_skill_slugs
  - rubric_id
  - supporting_artifact_count
Rules:
- Preserve requested counts exactly.
- Do not echo deterministic request metadata that is already fixed by the system.
- Use only the supplied taxonomy identifiers.
- Each generation_brief must be specific enough that a worker can produce realistic editable content.
- Do not include markdown fences or prose outside the JSON object."""

CREATOR_PROMPT_ITEM_PLAN_OUTPUT_FORMAT = """Return JSON with these required fields exactly:
- prompt_version: '{prompt_version}'
- provider: '{provider}'
- model_slug: '{model_slug}'
- prompt_items: array of objects with:
  - prompt_type
  - title_hint
  - generation_brief
  - difficulty
  - target_skill_slugs
  - rubric_id
Rules:
- Preserve requested counts exactly.
- Use only collection-enabled prompt types.
- Use only supplied skill slugs and rubric ids.
- Make each item materially distinct from the others and from the supplied existing prompts.
- Do not include markdown fences or prose outside the JSON object."""

CREATOR_PROMPT_ITEM_OUTPUT_FORMAT = """Return JSON with these required fields exactly:
- prompt_type: string
- title: string
- prompt_text: string
- difficulty: one of introductory, intermediate, advanced
- target_skill_slugs: array of strings
- rubric_id: string
Rules:
- Preserve prompt_type, difficulty, target_skill_slugs, and rubric_id exactly as requested.
- Produce editable, realistic workplace practice content.
- Avoid repeating the title hint verbatim if a better specific title exists.
- Do not include markdown fences or prose outside the JSON object."""

CREATOR_SCENARIO_OUTPUT_FORMAT = """Return JSON with these required fields exactly:
- title: string
- business_context: string
- learner_objective: string
- constraints: array of strings
- stakeholder_tensions: array of strings
- target_skill_slugs: array of strings
- rubric_id: string
- mock_company: null or object with name, industry, operating_context
- mock_people: array of objects with name, role, goals, communication_style, relationship_to_scenario
- supporting_artifacts: array of objects with artifact_type, title, body
Rules:
- Preserve target_skill_slugs and rubric_id exactly as requested.
- Keep the mock world internally consistent.
- Generate exactly the requested number of supporting artifacts.
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

CREATOR_STRUCTURED_COLLECTION_BLUEPRINT_PROMPT = """Plan a SoftSkills collection draft using the fixed metadata supplied by the system.
Deterministic collection metadata:
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

CREATOR_CHAT_COLLECTION_BLUEPRINT_PROMPT = """Plan a SoftSkills collection draft from the user's brief using the fixed metadata supplied by the system.
Deterministic collection metadata:
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

CREATOR_STRUCTURED_PROMPT_ITEM_PLAN_PROMPT = """Plan new SoftSkills prompt items for an existing collection.
Collection metadata:
- collection title: {collection_title}
- collection summary: {collection_summary}
- target audience: {target_audience}
- collection difficulty: {difficulty}
- enabled prompt types: {allowed_prompt_types}
- collection skills: {collection_skill_slugs}
- compatible rubrics: {compatible_rubric_ids}
- existing prompt fingerprints: {existing_prompt_fingerprints}
Generation brief:
- title hint: {title_hint}
- workplace context: {workplace_context}
- generation focus: {generation_focus}
- realism notes: {realism_notes}
- requested counts: {requested_counts}
- allowed target skills: {requested_skill_slugs}
{output_format}"""

CREATOR_CHAT_PROMPT_ITEM_PLAN_PROMPT = """Plan new SoftSkills prompt items for an existing collection from the user's brief.
Collection metadata:
- collection title: {collection_title}
- collection summary: {collection_summary}
- target audience: {target_audience}
- collection difficulty: {difficulty}
- enabled prompt types: {allowed_prompt_types}
- collection skills: {collection_skill_slugs}
- compatible rubrics: {compatible_rubric_ids}
- existing prompt fingerprints: {existing_prompt_fingerprints}
- requested counts: {requested_counts}
- allowed target skills: {requested_skill_slugs}
Hardened user brief:
{user_prompt}
{output_format}"""

CREATOR_PROMPT_ITEM_WORKER_PROMPT = """Generate one editable SoftSkills prompt item.
Collection context:
- collection title: {collection_title}
- target audience: {target_audience}
- collection difficulty: {collection_difficulty}
- workplace context: {workplace_context}
Fixed worker metadata:
- prompt_type: {prompt_type}
- difficulty: {difficulty}
- target skills: {target_skill_slugs}
- rubric id: {rubric_id}
Creative brief:
- title hint: {title_hint}
- generation brief: {generation_brief}
{output_format}"""

CREATOR_SCENARIO_WORKER_PROMPT = """Generate one editable SoftSkills scenario draft.
Collection context:
- collection title: {collection_title}
- target audience: {target_audience}
- collection difficulty: {collection_difficulty}
- workplace context: {workplace_context}
Fixed worker metadata:
- target skills: {target_skill_slugs}
- rubric id: {rubric_id}
- supporting artifact count: {supporting_artifact_count}
- allowed artifact types: {allowed_artifact_types}
Creative brief:
- title hint: {title_hint}
- generation brief: {generation_brief}
{output_format}"""
