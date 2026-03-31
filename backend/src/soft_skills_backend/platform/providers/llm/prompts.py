"""Centralized prompt templates for all application services."""

from __future__ import annotations

ASSESSMENT_PROMPT_NAME = "assessment-per-skill"
ASSESSMENT_AGGREGATION_PROMPT_NAME = "assessment-aggregation"
CREATOR_STRUCTURED_GENERATION_PROMPT_NAME = "creator-structured-draft"
CREATOR_CHAT_GENERATION_PROMPT_NAME = "creator-chat-draft"
CREATOR_PROMPT_ITEM_STRUCTURED_GENERATION_PROMPT_NAME = "creator-prompt-items-structured-plan"
CREATOR_PROMPT_ITEM_CHAT_GENERATION_PROMPT_NAME = "creator-prompt-items-chat-plan"
CREATOR_PROMPT_ITEM_WORKER_PROMPT_NAME = "creator-prompt-item-worker"
CREATOR_SCENARIO_SHELL_WORKER_PROMPT_NAME = "creator-scenario-shell-worker"
CREATOR_SCENARIO_QUESTION_WORKER_PROMPT_NAME = "creator-scenario-question-worker"

PER_SKILL_ASSESSMENT_PROMPT = """Assess this SoftSkills text practice response for exactly one skill.
Practice mode: {practice_type}
Prompt type: {prompt_type}
Prompt: {prompt_text}
Additional context:
{context_block}
Response: {response_text}
Target role: {target_role}
Learner goals: {goals}
Prior assessed attempts: {prior_assessed_attempts}
Requested skill: {skill_slug}
Rubric id: {rubric_id}
Rubric version: {rubric_version}
Criterion title: {criterion_title}
Criterion description: {criterion_description}
Criterion levels:
{criterion_levels}
CRITICAL CONSTRAINTS:
- You MUST assess only the requested skill: {skill_slug}
- You MUST copy EXACT words from the response text above. Do NOT paraphrase or invent quotes.
- If the response is too short to quote, use the full response as the quote.
- Return one or two evidence items only
- Keep the rationale aligned to the selected rubric level
Return JSON with these required fields exactly:
- skill_slug: '{skill_slug}'
- score: integer using one of the rubric levels listed above
- rationale: string
- evidence: array of objects with quote and explanation
Do not include markdown fences or extra fields."""

ASSESSMENT_AGGREGATION_PROMPT = """Synthesize the validated per-skill assessments for a SoftSkills practice response.
Learner response: {response_text}
Per-skill assessments:
{per_skill_json}
Return JSON with these required fields exactly:
- summary: string
- next_actions: array of strings
Rules:
- Do not invent new scores
- Do not restate per-skill evidence verbatim unless necessary
- Keep the summary grounded in the supplied per-skill assessments
- Do not include markdown fences or extra fields."""

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
  - questions
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
  - question_count
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
- generated_rubric: null or object with:
  - title
  - criteria: array of objects with:
    - criterion_ref
    - skill_slug
    - title
    - description
    - levels: array with exactly two objects:
      - level: 1 or 2
      - description
      - examples: array of strings
Rules:
- Preserve prompt_type, difficulty, target_skill_slugs, and rubric_id exactly as requested.
- If prompt_type is quick_practice_prompt, target_skill_slugs must be an empty array.
- If prompt_type is quick_practice_prompt, generated_rubric is required and must define a question-specific pass/fail rubric for this exact prompt.
- If prompt_type is quick_practice_prompt, every generated_rubric criterion must include exactly two levels, in this order: level 1 then level 2.
- Never omit either binary rubric level. Never return a criterion with only one level.
- Quick-practice rubric criteria are not skill-based. Use criterion_ref as a short rubric check id, and set skill_slug to the same value or null.
- If prompt_type is not quick_practice_prompt, generated_rubric must be null exactly.
- Produce editable, realistic workplace practice content.
- Avoid repeating the title hint verbatim if a better specific title exists.
- Do not include markdown fences or prose outside the JSON object."""

CREATOR_SCENARIO_SHELL_OUTPUT_FORMAT = """Return JSON with these required fields exactly:
- title: string
- business_context: string
- learner_objective: string
- constraints: array of strings
- stakeholder_tensions: array of strings
- questions: array of strings
- target_skill_slugs: array of strings
- rubric_id: string
- mock_company: null or object with name, industry, operating_context
- mock_people: array of objects with name, role, goals, communication_style, relationship_to_scenario
- supporting_artifacts: array of objects with artifact_type, title, body
- question_plans: array of objects with index and generation_brief
Rules:
- Preserve target_skill_slugs and rubric_id exactly as requested.
- Keep the mock world internally consistent.
- Generate exactly the requested number of supporting artifacts.
- Generate exactly the requested number of question_plans.
- question_plans indexes must start at 1 and increase by 1 with no gaps.
- Each question_plans generation_brief must be concise, distinct, and progressively more challenging.
- Every required field must be present.
- Use [] for empty arrays and null for absent mock_company.
- supporting_artifacts must be an array, even when the count is 0.
- Do not include markdown fences or prose outside the JSON object."""

CREATOR_SCENARIO_QUESTION_OUTPUT_FORMAT = """Return JSON with these required fields exactly:
- index: integer
- question: string
Rules:
- Preserve index exactly as requested.
- Return one concise scenario question only.
- The question must be grounded in the supplied scenario context.
- The question must not restate the entire scenario.
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
Available taxonomy:
{taxonomy_context}
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
Available taxonomy:
{taxonomy_context}
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
Rules:
- If prompt_type is quick_practice_prompt, return target_skill_slugs as [].
- Quick-practice criteria are rubric checks, not platform skills.
- If prompt_type is quick_practice_prompt, generated_rubric is mandatory.
- For every quick-practice criterion, the levels array must contain exactly two objects only:
  1. {{ "level": 1, "description": "...", "examples": ["..."] }}
  2. {{ "level": 2, "description": "...", "examples": ["..."] }}
- Do not return a criterion with one level.
- If prompt_type is not quick_practice_prompt, return generated_rubric as null.
{output_format}"""

CREATOR_SCENARIO_SHELL_WORKER_PROMPT = """Generate one editable SoftSkills scenario shell.
Collection context:
- collection title: {collection_title}
- target audience: {target_audience}
- collection difficulty: {collection_difficulty}
- workplace context: {workplace_context}
Fixed worker metadata:
- target skills: {target_skill_slugs}
- rubric id: {rubric_id}
- supporting artifact count: {supporting_artifact_count}
- question count: {question_count}
- allowed artifact types: {allowed_artifact_types}
Creative brief:
- title hint: {title_hint}
- generation brief: {generation_brief}
Rules:
- Return every required field explicitly.
- If there is no mock company, set mock_company to null.
- If mock_people contains one or more people, mock_company must be a non-null object with name, industry, and operating_context.
- Do not return mock_people unless they clearly belong to the same mock_company context.
- If there are no mock people, constraints, stakeholder tensions, or supporting artifacts, return [] for those arrays.
- supporting_artifacts must contain exactly {supporting_artifact_count} items.
- question_plans must contain exactly {question_count} items.
- question_plans must progress from foundational to more complex.
{output_format}"""

CREATOR_SCENARIO_QUESTION_WORKER_PROMPT = """Generate one scenario question for a pre-planned SoftSkills scenario.
Collection context:
- collection title: {collection_title}
- target audience: {target_audience}
- collection difficulty: {collection_difficulty}
Scenario context:
- title: {scenario_title}
- business context: {business_context}
- learner objective: {learner_objective}
- constraints: {constraints}
- stakeholder tensions: {stakeholder_tensions}
- target skills: {target_skill_slugs}
- question index: {question_index}
- question count: {question_count}
Question brief:
- generation brief: {question_generation_brief}
Rules:
- Return exactly one question.
- Keep it concise and directly answerable by the learner.
- Make it distinct from other likely questions by following the supplied brief.
- Preserve index exactly as requested.
{output_format}"""
