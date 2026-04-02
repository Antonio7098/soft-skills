# LLM-Based Pipelines — Canonical Reference

This document is the authoritative guide to every LLM-powered Stageflow pipeline in the Soft Skills backend. Each section covers the pipeline's purpose, stage DAG, prompt templates, LLM call sites, configuration knobs, and failure semantics.

---

## Table of Contents

1. [Shared Infrastructure](#1-shared-infrastructure)
2. [Catalog: Collection Generation](#2-catalog-collection-generation)
3. [Catalog: Prompt Item Generation](#3-catalog-prompt-item-generation)
4. [Catalog: Worker Subpipelines](#4-catalog-worker-subpipelines)
5. [Practice: Assessment Marking](#5-practice-assessment-marking)
6. [Evaluation: Benchmark Run](#6-evaluation-benchmark-run)
7. [Assistant: Turn Runtime](#7-assistant-turn-runtime)
8. [Admin Agent: Chat Runtime](#8-admin-agent-chat-runtime)
9. [Progression: Refresh](#9-progression-refresh)
10. [Prompt Template Reference](#10-prompt-template-reference)
11. [Cross-Pipeline Patterns](#11-cross-pipeline-patterns)

---

## 1. Shared Infrastructure

### 1.1 TypedLLMOutput

**File**: `engines/marking/use_cases/structured_output.py:90`

`TypedLLMOutput` is the core abstraction for every LLM call that returns structured JSON. It wraps `LLMProvider.complete_json()` with:

- **Schema enforcement**: Converts a Pydantic model into a `JsonSchemaResponseFormat` and passes it as the `response_schema` to the provider.
- **Bounded retries**: On `JSONDecodeError` or `ValidationError`, it appends the malformed output as an assistant message plus a corrective user message and retries (up to `max_validation_retries`).
- **Repair modes**: `FAIL_FAST` (no retries, used by admin agent) or `SELF_CORRECT` (append error feedback, used everywhere else).
- **Timeout**: Per-call timeout in seconds.

```python
TypedLLMOutput(
    PerSkillAssessment,
    schema_version="per_skill_assessment.v1",
    max_validation_retries=2,
    repair_mode=StructuredOutputRepairMode.SELF_CORRECT,
    timeout_seconds=60.0,
)
```

**Return type**: `TypedLLMResult` — contains `parsed` (the validated Pydantic model), `raw_payload` (the original JSON dict), `schema_version`, `usage` (token counts), and `model_slug`.

### 1.2 PromptLibrary

**File**: `engines/marking/use_cases/structured_output.py:50`

A small in-memory versioned prompt registry used by the marking engine and assistant. Templates are registered by `(name, version)` pairs with optional default resolution. Renders templates via Python `str.format()`.

### 1.3 Prompt Registry (Database-Backed)

**File**: `modules/admin/domain/prompt_registry.py`

The database-backed prompt registry manages versioned prompt templates synced at startup via `sync_builtins()`. Pipelines resolve prompts through `PromptRenderRequest` → `create_prompt_render_stage()` → `RenderedPrompt`. This is the standard path for catalog and assistant prompts.

### 1.4 LLM Provider Protocol

**File**: `shared/ports/llm.py`

Every LLM provider implements:

| Method | Used By |
|--------|---------|
| `complete_json(messages, response_schema, timeout)` | TypedLLMOutput (all structured calls) |
| `complete_with_tools(messages, tools, tool_choice, timeout)` | Assistant agent loop |
| `stream_text(messages)` | Assistant final response streaming |

Providers are instantiated per task kind: `DEFAULT`, `ASSISTANT`, `ADMIN_AGENT`.

### 1.5 ProviderCallContext

Every LLM call carries a `ProviderCallContext` with:

- `operation` — semantic name (e.g., `"assistant_orchestrator_decision"`)
- `request_id`, `trace_id`, `pipeline_run_id`, `workflow_id`, `user_id`

This is persisted by `DatabaseProviderCallLogger` for full observability.

---

## 2. Catalog: Collection Generation

**File**: `modules/catalog/workflows/generation/collection_pipeline.py`
**Pipeline name**: `catalog_{mode}_generation` where `mode` is `structured` or `chat`
**Execution mode**: `catalog_generation`
**Service namespace**: `soft_skills_backend.catalog`

### 2.1 Stage DAG

```
input_guard                          (GUARD)
    │
    ▼
blueprint_transform                  (TRANSFORM)
    │
    ▼
blueprint_render                     (TRANSFORM)
    │
    ▼
blueprint_llm_transform              (TRANSFORM)  ← LLM CALL
    │
    ▼
blueprint_guard                      (GUARD)
    │
    ├─── prompt_items_work ──── scenarios_work     (WORK, parallel)
    │         │                      │
    └─────────┴──────────────────────┘
              │
              ▼
    assemble_transform               (TRANSFORM)
              │
              ▼
    output_guard                     (GUARD)
              │
              ▼
    persistence_work                 (WORK)
```

### 2.2 Stage Details

| Stage | Kind | Dependencies | Description |
|-------|------|-------------|-------------|
| `input_guard` | GUARD | — | Validates generation request; checks cancellation |
| `blueprint_transform` | TRANSFORM | `input_guard` | Builds `PromptRenderRequest` from command + config |
| `blueprint_render` | TRANSFORM | `blueprint_transform` | Resolves and renders prompt from database registry |
| `blueprint_llm_transform` | TRANSFORM | `blueprint_render` | **LLM call** → `GeneratedCollectionBlueprint` |
| `blueprint_guard` | GUARD | `blueprint_llm_transform` | Validates blueprint, enforces command skill slugs |
| `prompt_items_work` | WORK | `blueprint_guard` | Fans out to prompt item worker subpipelines |
| `scenarios_work` | WORK | `blueprint_guard` | Fans out to scenario worker subpipelines |
| `assemble_transform` | TRANSFORM | `blueprint_guard`, `prompt_items_work`, `scenarios_work` | Combines blueprint + workers → `GeneratedCollectionDraft` |
| `output_guard` | GUARD | `assemble_transform` | Validates assembled draft |
| `persistence_work` | WORK | `output_guard`, `blueprint_guard`, `prompt_items_work`, `scenarios_work` | Persists to DB, records `GenerationManifest` |

### 2.3 LLM Calls

**Call 1 — Blueprint generation** (`blueprint_llm_transform`):
- **Method**: `TypedLLMOutput.generate()` → `complete_json()`
- **System prompt**: `"Plan a realistic SoftSkills collection blueprint. Return JSON only."`
- **User prompt**: Registry-rendered template (see §10)
- **Output schema**: `GeneratedCollectionBlueprint`
- **TypedLLMOutput config**: `blueprint_output` parameter (from `modules/assistant/workflows/assessment.py:build_typed_output`)

### 2.4 Prompt Templates

| Mode | Template Name | Template Variable Source |
|------|--------------|------------------------|
| `structured` | `creator-structured-collection-blueprint` (registry) | `config.structured_prompt_name/@version` |
| `chat` | `creator-chat-collection-blueprint` (registry) | `config.chat_prompt_name/@version` |

**Output format template**: `CREATOR_COLLECTION_BLUEPRINT_OUTPUT_FORMAT` (embedded in prompt via `output_format` variable)

### 2.5 Idempotency

Key: `catalog_{mode}_generation:{user_id}:{request_id}`
Params: Full command dump as JSON.

### 2.6 Configuration

From `CatalogGenerationRuntimeConfig` (`engines/config/artifacts/soft_skills_catalog_generation_runtime.v1.json`):

| Setting | Purpose |
|---------|---------|
| `structured_prompt_name/version` | Blueprint prompt for structured mode |
| `chat_prompt_name/version` | Blueprint prompt for chat mode |
| `prompt_item_structured_prompt_name/version` | Prompt item planning prompt |
| `prompt_item_chat_prompt_name/version` | Prompt item planning (chat) |
| `prompt_item_worker_prompt_name/version` | Worker prompt for prompt items |
| `scenario_worker_prompt_name/version` | Worker prompt for scenarios |
| `max_parallel_prompt_item_children` | Semaphore limit for prompt item workers |
| `max_parallel_scenario_children` | Semaphore limit for scenario workers |
| `max_validation_retries` | Semantic retry count for worker validation |

### 2.7 Cancellation

The pipeline checks for cancellation via `_yield_for_cancel()` between expensive stages:
1. Checks `execution.is_cancelled`
2. Yields with `asyncio.sleep(0.15)` to allow WebSocket cancel signal delivery
3. Re-checks cancellation flag
4. Returns `StageOutput.cancel` if cancelled

Cancellation checkpoints exist before `prompt_items_work` and `scenarios_work`.

### 2.8 Progress Tracking

A `progress_callback` reports percentage completion at each stage boundary (5% → 100%). Events stream via `GenerationRealtimeBroker` over WebSocket.

---

## 3. Catalog: Prompt Item Generation

**File**: `modules/catalog/workflows/generation/prompt_item_pipeline.py`
**Pipeline name**: `catalog_{mode}_generation` (same naming, different entry point)
**Execution mode**: `catalog_generation`

### 3.1 Stage DAG

```
input_guard                          (GUARD)
    │
    ▼
plan_transform                       (TRANSFORM)
    │
    ▼
plan_render                          (TRANSFORM)
    │
    ▼
plan_llm_transform                   (TRANSFORM)  ← LLM CALL
    │
    ▼
plan_guard                           (GUARD)
    │
    ▼
prompt_items_work                    (WORK)  ← fans out to worker subpipelines
    │
    ▼
output_guard                         (GUARD)
    │
    ▼
persistence_work                     (WORK)
```

### 3.2 LLM Calls

**Call 1 — Plan batch generation** (`plan_llm_transform`):
- **Method**: `TypedLLMOutput.generate()` → `complete_json()`
- **System prompt**: `"Plan realistic SoftSkills prompt items for an existing collection. Return JSON only."`
- **User prompt**: Registry-rendered template from `config.prompt_item_structured_prompt_name` or `config.prompt_item_chat_prompt_name`
- **Output schema**: `GeneratedPromptItemPlanBatch`

### 3.3 Key Differences from Collection Generation

- Operates on an existing collection (requires `collection_id`)
- Validates collection ownership (`require_collection_owner_or_admin`)
- Enforces uniqueness against existing prompt items (`validate_generated_prompt_item_uniqueness`)
- No scenario workers — only prompt item workers
- Uses existing collection metadata for context

### 3.4 Idempotency

Key: `{mode}:{user_id}:{collection_id}:{request_id}`

---

## 4. Catalog: Worker Subpipelines

**File**: `modules/catalog/workflows/generation/workers.py`

Worker subpipelines are spawned by both the collection and prompt item generation pipelines. They run as child pipelines via `run_logged_subpipeline()`.

### 4.1 Prompt Item Worker

**Pipeline name**: `catalog_prompt_item_worker`
**Execution mode**: `catalog_generation_worker`

```
input_guard                          (GUARD)
    │
    ▼
prompt_request_transform             (TRANSFORM)
    │
    ▼
prompt_render_transform              (TRANSFORM)
    │
    ▼
llm_transform                        (TRANSFORM)  ← LLM CALL (with semantic retry)
    │
    ▼
output_guard                         (GUARD)
```

**LLM Call** (`llm_transform`):
- **Method**: `TypedLLMOutput.generate()` → `complete_json()`
- **System prompt**: `"Generate one realistic SoftSkills prompt item. Return JSON only."`
- **User prompt**: Registry-rendered from `config.prompt_item_worker_prompt_name` with variables: `collection_title`, `target_audience`, `collection_difficulty`, `workplace_context`, `prompt_type`, `difficulty`, `target_skill_slugs`, `rubric_id`, `title_hint`, `generation_brief`, `output_format`
- **Output schema**: `GeneratedPromptItemDraft`
- **Semantic retry**: On `AppError` validation failure, appends error feedback as `{code}: {message} Details: {details}. Return corrected JSON only.` and retries up to `max_validation_retries`

**Idempotency**: `catalog_prompt_item_worker:{request_id}:{worker_index}`

### 4.2 Scenario Worker

**Pipeline name**: `catalog_scenario_worker`
**Execution mode**: `catalog_generation_worker`

```
input_guard                          (GUARD)
    │
    ▼
prompt_request_transform             (TRANSFORM)
    │
    ▼
prompt_render_transform              (TRANSFORM)
    │
    ▼
llm_transform                        (TRANSFORM)  ← LLM CALL (with semantic retry)
    │
    ▼
output_guard                         (GUARD)
```

**LLM Call** (`llm_transform`):
- **Method**: `TypedLLMOutput.generate()` → `complete_json()`
- **System prompt**: `"Generate one realistic SoftSkills scenario draft. Return JSON only."`
- **User prompt**: Registry-rendered from `config.scenario_worker_prompt_name` with variables including `supporting_artifact_count`, `allowed_artifact_types`, `prompt_text_hint`
- **Output schema**: `GeneratedScenarioDraft`

**Idempotency**: `catalog_scenario_worker:{request_id}:{worker_index}`

### 4.3 Validation Rules

**Prompt item worker** validates:
- `prompt_type` matches plan
- `rubric_id` matches plan (when both non-null)
- Quick-practice prompts must include `generated_rubric` with exactly 2 levels per criterion
- Non-quick-practice prompts must NOT include `generated_rubric`

**Scenario worker** validates:
- `target_skill_slugs` match plan
- `rubric_id` matches plan (when both non-null)
- `supporting_artifacts` count matches plan
- `prompt_text` is non-empty
- Mock world consistency

### 4.4 Concurrency

Workers run via `asyncio.gather()` with semaphore bounds:
- Prompt items: `config.max_parallel_prompt_item_children`
- Scenarios: `config.max_parallel_scenario_children`

---

## 5. Practice: Assessment Marking

**File**: `modules/practice/workflows/assessment/marking_provider.py`
**Not a Stageflow pipeline** — invoked as a service by the practice submit-attempt pipeline

### 5.1 Architecture

`DefaultAssessmentMarkingProvider` is the bridge between the practice module and the marking engine. It consumes:
- `RubricRepository` — loads rubric definitions from the database
- `TypedLLMOutput` (per-skill) — validates individual skill assessments
- `TypedLLMOutput` (aggregation) — validates summary/next-actions output
- `PromptLibrary` — in-memory versioned prompt templates

### 5.2 Processing Flow

```
mark_attempt()
├── Load rubric definition (RubricRepository)
├── _assess_skills() — fan-out with semaphore
│   ├── _assess_skill(criterion_1)  ← LLM CALL (per-skill)
│   ├── _assess_skill(criterion_2)  ← LLM CALL (per-skill)
│   └── _assess_skill(criterion_N)  ← LLM CALL (per-skill)
├── Deterministic aggregation (compute_overall_score, strengths, weaknesses)
├── _aggregate_assessment()  ← LLM CALL (summary + next_actions)  [non-quick-practice only]
└── Return AssessmentTransformPayload
```

### 5.3 Per-Skill Assessment

**LLM Call**: `_assess_skill()`:
- **Method**: `TypedLLMOutput.generate()` → `complete_json()`
- **Prompt**: `PER_SKILL_ASSESSMENT_PROMPT` (rendered via `PromptLibrary`)
- **System prompt**: `"You are a strict assessment engine. Return JSON only, without markdown fences."`
- **Output schema**: `PerSkillAssessment`
- **Verification retry**: On failure, appends the raw output + corrective message with specific error codes. For `SS-SCORING-004` (evidence grounding), adds: `"Evidence.quote must be an exact verbatim substring copied from the learner response, not a paraphrase, summary, or invented quote."`
- **Backup provider**: If configured and this is the last retry attempt, switches to `backup_llm_provider`

**Verification rules** (`_verify_per_skill_assessment`):
1. Output must be `PerSkillAssessment` instance
2. `skill_slug` must match `criterion.criterion_ref`
3. `score` must be one of the rubric level values
4. Every `evidence.quote` must be a normalized substring of the response text (min 6 chars)

**Quick-practice special case**: For `PracticeType.QUICK_PRACTICE`, aggregation is deterministic (no LLM call). Summary is `"Passed X of Y rubric areas."` and next_actions list failed criteria.

### 5.4 Aggregation Call

**LLM Call**: `_aggregate_assessment()`:
- **Method**: `TypedLLMOutput.generate()` → `complete_json()`
- **Prompt**: `ASSESSMENT_AGGREGATION_PROMPT`
- **System prompt**: `"You are a strict aggregation engine. Return JSON only."`
- **Output schema**: `AssessmentAggregationOutput` (fields: `summary`, `next_actions`)
- **Deterministic scores**: The aggregation LLM cannot override per-skill scores. It generates only `summary` and `next_actions`.

### 5.5 Deterministic Score Computation

After all per-skill assessments complete:
- `overall_score` = rounded weighted mean of per-skill scores (using rubric criterion weights)
- `strengths` = top 1–2 highest-scoring skills with grounded rationale
- `weaknesses` = bottom 1–2 lowest-scoring skills with evidence excerpts

### 5.6 Fail-Closed Semantics

If any required skill assessment fails after retries, the entire parent assessment fails. Partial results are never persisted.

### 5.7 TypedLLMOutput Configuration

| Output | Model Type | Schema Version |
|--------|-----------|----------------|
| Per-skill | `PerSkillAssessment` | `config.per_skill_output_schema_version` |
| Aggregation | `AssessmentAggregationOutput` | `config.aggregation_output_schema_version` |

Both use `max_validation_retries=settings.get_assessment_structured_output_retries()` and `timeout_seconds=settings.llm_marking_timeout_seconds`.

---

## 6. Evaluation: Benchmark Run

**File**: `modules/evaluation/workflows/service.py`
**Pipeline name**: `evaluation_run`
**Execution mode**: `evaluation_runtime`
**Timeout**: 240,000ms (4 minutes)

### 6.1 Stage DAG

```
input_guard                          (GUARD)
    │
    ▼
transform                            (TRANSFORM)  ← runs MarkingBenchmarkRunner (invokes marking pipeline)
    │
    ▼
work                                 (WORK)       ← persists evaluation results
```

### 6.2 LLM Calls

The evaluation pipeline does not make direct LLM calls. The `transform` stage invokes `MarkingBenchmarkRunner.execute()` which exercises the full marking pipeline (per-skill assessment, aggregation, validation) against golden benchmark cases. This means every evaluation run triggers the same LLM calls as the assessment marking pipeline (§5), one per benchmark case.

### 6.3 Idempotency

Key: `evaluation:{suite_id}:{model_slugs}:{case_ids}:{request_id}`

### 6.4 Suite Structure

Evaluation suites are defined in `modules/evaluation/domain/evaluation.py` as `BuiltinEvaluationSuite` instances. Each suite contains golden cases with expected scores and evidence patterns.

---

## 7. Assistant: Turn Runtime

**File**: `modules/assistant/workflows/service.py`
**Pipeline name**: `assistant_turn_runtime`
**Execution mode**: `assistant_runtime`
**Service namespace**: `soft_skills_backend.assistant`

### 7.1 Stage DAG

```
input_guard                          (GUARD)
    │
    ├─── history_enrich ──┬── profile_enrich ──┬── progress_enrich ──┬── attempts_enrich ──┬── session_state_enrich
    │     (ENRICH)        │    (ENRICH)        │    (ENRICH)        │    (ENRICH)         │    (ENRICH)
    │                     │                    │                    │                     │
    └─────────────────────┴────────────────────┴────────────────────┴─────────────────────┘
    │
    ▼
planning_prompt_request              (TRANSFORM)
    │
    ▼
planning_prompt_render               (TRANSFORM)
    │
    ▼
assistant_runtime                    (AGENT)      ← LLM CALLS (tool loop, up to 6 iterations)
    │
    ▼
final_response_prompt_request        (TRANSFORM)
    │
    ▼
final_response_prompt_render         (TRANSFORM)
    │
    ▼
final_response_work                  (WORK)       ← LLM CALL (streaming)
```

### 7.2 Parallel Enrichment Stages

All five ENRICH stages depend only on `input_guard`, so they execute in parallel:

| Stage | Data Loaded |
|-------|-------------|
| `history_enrich` | Conversation history (limited by `llm_assistant_conversation_history_limit`) |
| `profile_enrich` | User profile |
| `progress_enrich` | Progression dashboard (graceful 404 handling) |
| `attempts_enrich` | Recent practice attempts via SQL guard (limited by `llm_assistant_recent_attempt_limit`) |
| `session_state_enrich` | Practice session state from session metadata |

### 7.3 Agent Loop (Tool Execution)

**Stage**: `assistant_runtime` (StageKind.AGENT)

```
for _ in range(MAX_TOOL_ITERATIONS):  # MAX_TOOL_ITERATIONS = 6
    ├── Check cancellation
    ├── LLM call: complete_with_tools()
    │   ├── If no tool_calls → return final_response (break)
    │   └── If tool_calls → parse and execute
    ├── Parse tool requests via parse_assistant_tool_requests()
    ├── Execute tools: tools.execute_many() (asyncio.gather, parallel)
    ├── Security-harden tool results via PromptSecurityPolicy.build_tool_message()
    ├── Append tool results to messages
    └── Check cancellation
```

**LLM Call**: `self._llm_provider.complete_with_tools()`:
- **Messages**: System prompt (rendered from `assistant_orchestrator@v7`) + conversation history + tool results
- **Tools**: `build_assistant_tool_definitions()` — 7 tools (see §7.5)
- **Timeout**: `settings.llm_assistant_timeout_seconds`

### 7.4 Final Response Generation

**Stage**: `final_response_work`

After the agent loop completes:
1. If tools were used → calls `self._llm_provider.stream_text()` with the planning messages + final response prompt
2. If no tools were used → uses the draft response directly (passthrough)
3. Streams chunks via `AssistantRealtimeBroker` over WebSocket

**LLM Call**: `self._llm_provider.stream_text()`:
- **Messages**: Planning messages + `{role: "user", content: rendered_prompt}` (from `assistant_final_response@v1`)
- **Streaming**: Each chunk is published as a `response.delta` event via the realtime broker

### 7.5 Available Tools

| Tool | Purpose |
|------|---------|
| `query_user_context` | Run read-only SELECT against `assistant_safe_*` views |
| `start_collection_practice` | Start a practice run from a collection |
| `get_active_practice` | Fetch current active practice question |
| `submit_active_practice_response` | Submit learner's answer for active question |
| `end_active_practice` | End the active practice session |
| `generate_collection` | Generate a new collection (triggers catalog pipeline) |
| `generate_prompt_items` | Generate prompt items in existing collection |

### 7.6 Tool Approval

Certain tools require human approval:
- Configurable auto-allow list (`tool_approval_auto_allow`)
- Timeout-based approval waiting (`tool_approval_timeout_seconds`)
- Approval requests are streamed to the client in real-time

### 7.7 Prompt Security

`PromptSecurityPolicy` enforces:
- Max user message length: 12,000 characters
- Max tool output length: 12,000 characters
- Content sanitization via `build_user_message()` and `build_tool_message()`
- Raises `PromptSecurityError` on violations (translated to `SS-VALIDATION-204/205`)

### 7.8 Cancellation

- `input_guard` checks cancellation status immediately
- Agent loop checks `active.cancel_reason` before each iteration
- `_escalate_cancel()` sends `asyncio.Task.cancel()` after 1 second if the turn hasn't stopped gracefully
- Final response streaming checks cancellation on every chunk

### 7.9 Idempotency

Key: `assistant_turn:{turn_id}`

---

## 8. Admin Agent: Chat Runtime

**File**: `modules/admin_agent/workflows/service.py`
**Pipeline name**: `admin_agent_chat_runtime`
**Execution mode**: `admin_agent_chat`

### 8.1 Stage DAG

```
input_guard                          (GUARD)
    │
    ▼
context_enrich                       (ENRICH)
    │
    ▼
query_planning                       (AGENT)      ← LLM CALL
    │
    ▼
query_execution                      (WORK)
    │
    ▼
response_formulation                 (TRANSFORM)
```

### 8.2 LLM Calls

**Call 1 — SQL planning** (`query_planning`):
- **Method**: `TypedLLMOutput.generate()` → `complete_json()`
- **TypedLLMOutput config**: `TypedLLMOutput(AdminAgentPlan, repair_mode=FAIL_FAST, max_validation_retries=0)` — no retries, fail fast
- **System prompt**: `"You are an admin SQL planner. Return JSON with keys 'intent_summary', 'sql', and 'params'. Plan one SELECT query only. Do not use comments, subqueries, unions, or non-admin views. Do not use SELECT * except COUNT(*). Prefer simple aggregates and explicit aliases."`
- **User prompt**: Prompt version + conversation history + schema context + question
- **Output schema**: `AdminAgentPlan` (fields: `intent_summary`, `sql`, `params`)
- **Timeout**: `settings.llm_admin_agent_timeout_seconds`

### 8.3 SQL Guard

The `AdminAgentSqlGuard` validates:
- SQL must be a SELECT query
- No subqueries, unions, comments
- Row limits enforced (`admin_agent_query_row_limit`)
- Queries scoped to the user's organisation
- Results redacted via `ResultRedactor`

### 8.4 Authorization

`input_guard` enforces:
- `actor.organisation_id` must be non-null
- `actor.is_org_admin` must be true
- `query_admin_data` tool must be in `tool_approval_auto_allow`

### 8.5 Idempotency

Key: `admin_agent_chat:{workflow_id}:{request_id}:{message}`

---

## 9. Progression: Refresh

**File**: `modules/progression/workflows/service.py`
**Pipeline name**: `progression_refresh`
**Execution mode**: `progression_runtime`

### 9.1 Stage DAG

```
input_guard                          (GUARD)
    │
    ├─── snapshot_transform ───────────────────────── recommendation_enrich
    │     (TRANSFORM)                                  (ENRICH)
    │         │                                             │
    ▼         ▼                                             │
    snapshot_work ◄─────────────────────────────────────────┘
    (WORK)                │
                          ▼
              recommendation_transform
              (TRANSFORM)
                          │
                          ▼
              recommendation_work
              (WORK)
```

### 9.2 LLM Calls

**None** — this pipeline is entirely deterministic. It consumes the outputs of the marking engine (per-skill assessments) and applies:
- Decay weighting (linear decay over 180 days, min weight 0.35)
- Confidence computation (evidence volume 45%, recency 35%, time decay 20%)
- Gating rules (prevents aggregates from exceeding ceilings when critical dimensions fall below floors)
- Recommendation scoring (deficit alignment, stagnation relief, coverage gap fit, goal alignment, cooldown penalty)

### 9.3 Idempotency

Key: `progression_refresh:{learner_id}:{assessment_id}`

---

## 10. Prompt Template Reference

All prompt templates are defined in `platform/providers/llm/prompts.py` or managed via the database prompt registry.

### 10.1 Assessment Prompts (In-Memory PromptLibrary)

| Template | Prompt Name | System Message |
|----------|------------|----------------|
| Per-skill assessment | `assessment-per-skill` | `"You are a strict assessment engine. Return JSON only, without markdown fences."` |
| Aggregation | `assessment-aggregation` | `"You are a strict aggregation engine. Return JSON only."` |

**Per-skill prompt variables**: `practice_type`, `prompt_type`, `prompt_text`, `context_block`, `response_text`, `target_role`, `goals`, `prior_assessed_attempts`, `skill_slug`, `rubric_id`, `rubric_version`, `criterion_title`, `criterion_description`, `criterion_levels`

**Aggregation prompt variables**: `response_text`, `per_skill_json`

### 10.2 Catalog Generation Prompts (Database Registry)

| Template Name | Purpose | System Message |
|--------------|---------|----------------|
| `creator-structured-collection-blueprint` | Blueprint for structured mode | `"Plan a realistic SoftSkills collection blueprint. Return JSON only."` |
| `creator-chat-collection-blueprint` | Blueprint for chat mode | Same as above |
| `creator-prompt-items-structured-plan` | Prompt item planning (structured) | `"Plan realistic SoftSkills prompt items for an existing collection. Return JSON only."` |
| `creator-prompt-items-chat-plan` | Prompt item planning (chat) | Same as above |
| `creator-prompt-item-worker` | Individual prompt item generation | `"Generate one realistic SoftSkills prompt item. Return JSON only."` |
| `creator-scenario-worker` | Individual scenario generation | `"Generate one realistic SoftSkills scenario draft. Return JSON only."` |

### 10.3 Assistant Prompts (Database Registry)

| Template Name | Version | Purpose |
|--------------|---------|---------|
| `assistant_orchestrator` | `assistant_orchestrator@v7` | Main system prompt with tool-calling instructions, tone, and rules |
| `assistant_final_response` | `assistant_final_response@v1` | Final response generation from draft plan |

**Assistant orchestrator variables**: `learner_context`, `read_schema_context`, `taxonomy_context`, `practice_state`, `conversation_history`

### 10.4 Output Format Templates

All catalog prompts include an `output_format` variable populated from embedded templates:

| Template | Purpose |
|----------|---------|
| `CREATOR_COLLECTION_BLUEPRINT_OUTPUT_FORMAT` | Blueprint JSON schema instructions |
| `CREATOR_PROMPT_ITEM_PLAN_OUTPUT_FORMAT` | Plan batch JSON schema instructions |
| `CREATOR_PROMPT_ITEM_OUTPUT_FORMAT` | Single prompt item JSON schema instructions |
| `CREATOR_SCENARIO_OUTPUT_FORMAT` | Single scenario JSON schema instructions |

These enforce exact field names, types, and rules (e.g., quick-practice rubric must have exactly 2 levels).

---

## 11. Cross-Pipeline Patterns

### 11.1 Fan-Out / Fan-In

| Pipeline | Fan-Out | Mechanism | Fan-In |
|----------|---------|-----------|--------|
| Collection generation | Prompt items + scenarios | `asyncio.gather()` + semaphore | `assemble_transform` combines results |
| Prompt item generation | Prompt items | `asyncio.gather()` + semaphore | `output_guard` validates combined |
| Assessment marking | Per-skill assessments | `asyncio.gather()` + semaphore | Deterministic aggregation |

### 11.2 Subpipeline Spawning

Worker subpipelines (prompt items, scenarios) use `run_logged_subpipeline()`:
- Parent context snapshot is forked to the child
- Child gets a fresh `pipeline_run_id` but inherits `request_id`, `trace_id`, `user_id`
- `correlation_id` links parent and child in execution traces
- Child results returned as `SubpipelineResult` with payload and stage summaries

### 11.3 Semantic Retry Pattern

Used by catalog workers and assessment marking:

1. Call LLM with structured output schema
2. Parse response into typed model
3. Validate against domain rules
4. On failure: append `{error_code}: {message} Details: {details}. Return corrected JSON only.` and retry
5. Max retries: configurable per pipeline
6. Fail-closed: if all retries exhausted, parent pipeline fails

### 11.4 Idempotency Matrix

| Pipeline | Key Pattern | Scope |
|----------|-------------|-------|
| Collection generation | `catalog_{mode}_generation:{user_id}:{request_id}` | Pipeline |
| Prompt item generation | `{mode}:{user_id}:{collection_id}:{request_id}` | Pipeline |
| Prompt item worker | `catalog_prompt_item_worker:{request_id}:{worker_index}` | Subpipeline |
| Scenario worker | `catalog_scenario_worker:{request_id}:{worker_index}` | Subpipeline |
| Assistant turn | `assistant_turn:{turn_id}` | Pipeline |
| Admin agent | `admin_agent_chat:{workflow_id}:{request_id}:{message}` | Pipeline |
| Evaluation | `evaluation:{suite_id}:{model_slugs}:{case_ids}:{request_id}` | Pipeline |
| Progression refresh | `progression_refresh:{learner_id}:{assessment_id}` | Pipeline |

### 11.5 Observability

Every pipeline emits:
- **Wide events** via `AgentWideEventEmitter` per stage
- **Pipeline run logs** via `DatabasePipelineRunLogger` (started/completed/failed with duration)
- **Provider call logs** via `DatabaseProviderCallLogger` for every LLM call
- **Workflow events** via `WorkflowEventRecorder` for business-level events

### 11.6 Error Propagation

```
LLM call fails
    │
    ▼
TypedLLMOutput retries (if SELF_CORRECT mode)
    │
    ▼
StructuredOutputRejectionError
    │
    ▼
Translated to AppError (SS-VALIDATION-019 or SS-SCORING-xxx)
    │
    ▼
Pipeline error handler → HTTP response (422/500)
```

### 11.7 Timeout Configuration

| Pipeline | Timeout Setting | Default |
|----------|----------------|---------|
| Collection generation | `timeout_ms` parameter | Configurable |
| Assistant turn | `llm_assistant_timeout_seconds` × 2 (or 120s min) | Per settings |
| Admin agent | `llm_admin_agent_timeout_seconds` × 2 (or 120s min) | Per settings |
| Evaluation | Hardcoded 240,000ms | 4 minutes |
| Assessment marking | `llm_marking_timeout_seconds` | Per settings |

---

## Appendix A: File Index

| Pipeline | Primary File |
|----------|-------------|
| Collection generation | `modules/catalog/workflows/generation/collection_pipeline.py` |
| Prompt item generation | `modules/catalog/workflows/generation/prompt_item_pipeline.py` |
| Worker subpipelines | `modules/catalog/workflows/generation/workers.py` |
| Catalog prompting helpers | `modules/catalog/workflows/generation/prompting.py` |
| Assessment marking | `modules/practice/workflows/assessment/marking_provider.py` |
| TypedLLMOutput | `engines/marking/use_cases/structured_output.py` |
| Evaluation | `modules/evaluation/workflows/service.py` |
| Assistant | `modules/assistant/workflows/service.py` |
| Assistant prompting | `modules/assistant/workflows/prompting.py` |
| Assistant tools | `modules/assistant/workflows/tools.py` |
| Admin agent | `modules/admin_agent/workflows/service.py` |
| Progression | `modules/progression/workflows/service.py` |
| Prompt templates | `platform/providers/llm/prompts.py` |
| Prompt registry | `modules/admin/domain/prompt_registry.py` |
| Prompt render stage | `modules/admin/workflows/prompt_render_stage.py` |
| LLM provider protocol | `shared/ports/llm.py` |
| Config artifacts | `engines/config/artifacts/*.json` |
| Engine config models | `engines/config/models.py` |

## Appendix B: LLM Call Inventory

| Operation | Provider Method | Pipeline | Stage | Output Type |
|-----------|----------------|----------|-------|-------------|
| Blueprint generation | `complete_json` | Collection generation | `blueprint_llm_transform` | `GeneratedCollectionBlueprint` |
| Prompt item planning | `complete_json` | Prompt item generation | `plan_llm_transform` | `GeneratedPromptItemPlanBatch` |
| Prompt item generation | `complete_json` | Worker subpipeline | `llm_transform` | `GeneratedPromptItemDraft` |
| Scenario generation | `complete_json` | Worker subpipeline | `llm_transform` | `GeneratedScenarioDraft` |
| Per-skill assessment | `complete_json` | Assessment marking | `_assess_skill` | `PerSkillAssessment` |
| Assessment aggregation | `complete_json` | Assessment marking | `_aggregate_assessment` | `AssessmentAggregationOutput` |
| Assistant orchestration | `complete_with_tools` | Assistant turn | `assistant_runtime` | `ProviderToolCompletion` |
| Assistant final response | `stream_text` | Assistant turn | `final_response_work` | `AsyncIterator[ProviderTextChunk]` |
| Admin SQL planning | `complete_json` | Admin agent | `query_planning` | `AdminAgentPlan` |
