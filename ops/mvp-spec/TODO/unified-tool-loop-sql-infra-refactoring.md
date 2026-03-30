# Unified Tool Loop & SQL Infrastructure Refactoring

## Context

The assistant and admin agent both implement SQL-backed tool execution with real duplication:

1. SQL contracts are duplicated
2. SQL guards are largely duplicated
3. SQL executors are largely duplicated
4. Schema registries share the same shape and rendering patterns
5. Result redactors are identical

The assistant already uses provider-native tool calling via `complete_with_tools()`.
The admin agent still uses `TypedLLMOutput.generate()` to produce structured JSON,
then executes SQL outside the LLM interaction.

This document defines a refactor with two goals:

1. Remove duplicated SQL infrastructure
2. Extract the assistant tool loop into a shared implementation that preserves the
   current assistant behavior exactly enough to avoid the regressions seen in earlier
   loop redesign attempts

## Scope

- Backend only: `backend/src/soft_skills_backend/`
- No API contract changes
- No frontend changes
- No deliberate behavior changes for the assistant
- No deliberate response-semantics change for the admin agent

## Non-Goals

- Redesigning the assistant tool loop
- Introducing async-generator loop semantics
- Replacing deterministic admin-agent response formatting with an LLM-authored final answer
- Standardizing all error-code ranges across assistant and admin in the same change
- Migrating to new framework-level tool abstractions unless that can be done without
  changing behavior

---

## Current State

### Duplication Matrix

| Component | Assistant | Admin Agent | Duplication |
|-----------|-----------|-------------|-------------|
| Scalar types | `AssistantSqlScalar` | `AdminAgentScalar` | 100% |
| SQL commands | `QueryUserContextCommand` | `QueryAdminDataCommand` | ~95% |
| Result views | `QueryUserContextResultView` | `QueryAdminDataResultView` | ~95% |
| SQL executors | `AssistantSqlExecutor` | `AdminAgentSqlExecutor` | ~90% |
| SQL guards | `AssistantSqlGuard` | `AdminAgentSqlGuard` | ~80% |
| Schema registries | `AssistantSchemaRegistry` | `AdminAgentSchemaRegistry` | ~70% |
| Redactors | `AssistantResultRedactor` | `AdminAgentResultRedactor` | 100% |

### Assistant Tool Loop Is The Source Of Truth

The current assistant `_run_agent_loop()` is the reference behavior for Stage 2.
The shared loop must be extracted from it, not redesigned around an abstract ideal.

The current assistant behavior includes all of the following:

1. Synchronous iterative execution with a hard iteration cap
2. Prompt hardening for user messages before provider calls
3. Provider-native `complete_with_tools()` calls
4. Optional forced `tool_choice` when `_required_tool_name(...)` determines a tool is mandatory
5. Typed validation of provider tool calls
6. Clarification fallbacks for invalid tool requests
7. Clarification fallbacks for certain tool execution errors
8. `tool.invoked` event emission
9. Tool execution with persistence, approvals, streaming hooks, and child subpipeline metadata
10. Prompt hardening for tool-result messages before they are fed back to the model
11. Cancellation checks before and after major loop steps
12. `planning_messages` capture for downstream final-response generation

If the shared loop does not preserve these semantics, the refactor is not complete.

### Assistant Architecture Today

Current flow in `modules/assistant/workflows/service.py`:

```text
1. Build messages from rendered system prompt + history
2. Harden user messages with PromptSecurityPolicy
3. For up to MAX_TOOL_ITERATIONS:
   a. call complete_with_tools(...)
   b. if no tool calls:
      - enforce required tool if one was mandated
      - return final response
   c. parse tool calls into typed AssistantToolRequest
   d. emit tool.invoked events
   e. execute tools
   f. if supported tool/validation error:
      - return clarification response
   g. harden tool outputs
   h. append tool messages and continue
4. Raise orchestration error if iteration budget is exceeded
```

The assistant also has a separate final-response generation step that may rewrite the
draft response after tool use.

### Admin-Agent Architecture Today

Current flow in `modules/admin_agent/workflows/service.py`:

```text
Pipeline:
  input_guard -> context_enrich -> query_planning -> query_execution -> response_formulation

query_planning:
  - build messages with schema context and history
  - call TypedLLMOutput.generate()
  - parse AdminAgentPlan

query_execution:
  - validate and scope SQL
  - execute SQL
  - return QueryAdminDataResultView

response_formulation:
  - deterministically format the final user-facing response
```

This is not a tool loop. SQL execution happens after planning, outside the LLM turn.

---

## Design Decisions

### 1. Stage 1 And Stage 2 Stay Separate

Stage 1 is the SQL deduplication refactor.
Stage 2 is the tool-loop extraction and admin-agent migration.

Do not mix these into one large PR. Stage 1 should land and stabilize first.

### 2. Stage 2 Is Assistant-Parity Extraction, Not Redesign

The shared tool loop must behave like the current assistant loop.

That means:

- no async-generator redesign
- no event-stream redesign
- no new “generic agent runtime” abstractions that require changing assistant semantics
- no removal of assistant-specific hardening, fallback, or cancellation behavior

If extra abstraction makes parity unclear, prefer duplication over premature generalization.

### 3. Admin-Agent Pipeline Structure Is Preserved

Keep the admin-agent stage structure:

- `input_guard`
- `context_enrich`
- `query_planning`
- `response_formulation`

The change is inside planning/execution behavior, not in the overall DAG shape.

Specifically:

- replace `TypedLLMOutput.generate()` planning with a tool loop inside the planning stage
- let that planning stage return a payload containing:
  - final drafted answer
  - tool results
  - prompt/provider/model metadata
- keep `response_formulation` as a deterministic formatter or thin adapter

Do not flatten the admin agent into a single monolithic loop stage. The current stage
boundaries provide useful observability and stable behavior.

### 4. Admin-Agent Response Semantics Must Remain Stable

Today the admin agent returns a deterministic summary built from `QueryAdminDataResultView`.
Stage 2 should preserve that behavior unless there is a separate decision to change product
semantics.

The tool loop should let the model choose and run `query_admin_data`, but the final
response should still be shaped by the existing admin response path, not replaced by a new,
free-form LLM answer in this refactor.

### 5. Shared SQL Infrastructure Should Be Selectively Abstracted

Use shared bases where the behavior is truly the same:

- scalar types
- SQL command/result model shapes
- redaction logic
- executor timing and DB call wrapper
- shared schema-registry rendering helpers
- shared guard helpers for:
  - normalization
  - denied token detection
  - top-level select parsing
  - wildcard rejection

Do not force the guards into a deep base class that hides real differences.

The assistant guard currently supports behavior the admin guard does not:

- safe view-name canonicalization
- column alias resolution
- wildcard expansion for single-view projections
- more nuanced org/user scoping rules

So the preferred approach is:

- shared helper functions and small shared primitives
- thin domain guards that compose those helpers
- optional base classes only where they reduce code without obscuring domain differences

Executors are a better fit for inheritance than guards.

### 6. Error-Code Ranges Stay Domain-Specific

Do not unify assistant and admin SQL error codes in this refactor.

Keep the existing domain-specific ranges and preserve current codes where possible.
This is lower risk for tests, telemetry, and debugging.

### 7. Redactor Should Be Shared And Configurable

Use a single shared `ResultRedactor` implementation with:

- current sensitive-keyword defaults
- optional extra keywords at construction time

This preserves current behavior while allowing future variation.

### 8. Framework Tooling Is A Follow-Up Concern

The Stageflow guide prefers framework-level tool resolution and advanced executors for
new agentic work. That is useful guidance, but this refactor should not chase a second
migration at the same time if it risks assistant-loop parity.

For this refactor:

- preserve current assistant semantics first
- extract shared code second
- evaluate migration to framework-native tool abstractions in a later, isolated change

---

## Two-Stage Implementation Plan

## Stage 1: Shared SQL Infrastructure

### Goal

Eliminate SQL duplication without changing tool-loop behavior.

### New Shared Files

**`backend/src/soft_skills_backend/shared/domain/sql/types.py`**

- `SqlScalar = str | int | float | bool | None`
- `SqlCommand(sql: str, params: dict[str, SqlScalar])`
- `GuardedQuery(sql, scoped_sql, params, source_views, row_cap_applied)`
- `SqlResultView(tool_name, approval_state, sql, params, source_views, row_count, row_cap_applied, duration_ms, rows)`

**`backend/src/soft_skills_backend/shared/domain/sql/schema_registry.py`**

- shared dataclasses:
  - `ViewSchema`
  - `JoinHint`
- shared protocol:
  - `allowed_views()`
  - `get_view(name)`
  - `has_view(name)`
  - `render_prompt_context()`
- shared helpers for:
  - prompt-context rendering
  - optional view-name resolution
  - optional column-alias resolution

**`backend/src/soft_skills_backend/shared/domain/sql/sql_guard.py`**

- shared helper functions and/or a minimal base for:
  - SQL normalization
  - denied-token detection
  - subquery/set-operation rejection
  - select-clause extraction
  - top-level CSV splitting
  - wildcard rejection

Important: do not force assistant/admin onto identical guard pipelines where they are
not actually identical.

**`backend/src/soft_skills_backend/shared/domain/sql/sql_executor.py`**

- shared executor wrapper for:
  - DB execution timing
  - timeout enforcement
  - SQLAlchemy error mapping
  - redaction
- subclass or composition hook for:
  - actor validation
  - scoped bind parameters
  - result-view construction
  - row-limit parameter naming

**`backend/src/soft_skills_backend/shared/domain/sql/redactor.py`**

- `ResultRedactor(extra_sensitive_keywords: tuple[str, ...] = ())`
- same default redaction behavior as today

### Refactored Assistant Files

- `modules/assistant/contracts/sql.py`
- `modules/assistant/contracts/views.py`
- `modules/assistant/domain/schema_registry.py`
- `modules/assistant/infra/sql_guard.py`
- `modules/assistant/infra/sql_executor.py`
- remove `modules/assistant/domain/redactor.py` after replacement

### Refactored Admin-Agent Files

- `modules/admin_agent/contracts/commands.py`
- `modules/admin_agent/contracts/views.py`
- `modules/admin_agent/domain/schema_registry.py`
- `modules/admin_agent/infra/sql_guard.py`
- `modules/admin_agent/infra/sql_executor.py`
- remove `modules/admin_agent/domain/redactor.py` after replacement

### Backward-Compatibility Constraints

Keep public method signatures stable:

- `AssistantSqlGuard.validate_and_scope(QueryUserContextCommand) -> ...`
- `AdminAgentSqlGuard.validate_and_scope(QueryAdminDataCommand) -> ...`
- `AssistantSqlExecutor.execute(...)`
- `AdminAgentSqlExecutor.execute(...)`

Preserve existing result-view shapes and default `tool_name` / `approval_state` fields.

### Stage 1 Exit Criteria

All of the following must pass:

- existing assistant SQL unit tests
- existing admin-agent SQL unit tests
- `test_assistant_api`
- `test_admin_agent_api`
- `test_assistant_runtime_smoke`
- `test_admin_agent_smoke`
- `test_full_user_journey_smoke`

Add or update unit coverage for:

- shared redactor defaults and overrides
- shared SQL helper parsing behavior
- assistant-specific alias canonicalization still working
- admin-agent org scoping still working

---

## Stage 2: Shared Tool Loop Extraction And Admin-Agent Tool Adoption

### Goal

Extract the assistant tool loop into shared code without changing assistant behavior,
then migrate the admin agent to use that same loop pattern for `query_admin_data`.

### Hard Constraints

The shared loop must preserve current assistant semantics:

1. synchronous iterative loop
2. same iteration budget behavior
3. same prompt hardening behavior
4. same required-tool forcing behavior
5. same invalid-tool clarification behavior
6. same tool-error clarification behavior
7. same cancellation checks
8. same `planning_messages` behavior
9. same interaction with tool execution persistence and streaming hooks
10. same child subpipeline metadata flow for generation tools

If the extracted loop cannot preserve these semantics cleanly, stop and narrow the
abstraction instead of “improving” the runtime.

### Shared Tool-Loop Files

**`backend/src/soft_skills_backend/shared/tool_loop/models.py`**

- `ToolDefinition`
- `ToolRequest`
- `ToolResult`
- `ToolLoopConfig`
- `ToolLoopResult`

These should be kept minimal and shaped around current assistant needs.

**`backend/src/soft_skills_backend/shared/tool_loop/executor.py`**

A behavior-preserving extraction of the current assistant loop.

Responsibilities:

- call `complete_with_tools(...)`
- enforce iteration budget
- handle required `tool_choice`
- validate/parse tool calls
- emit invocation hooks
- call dispatcher / tool executor
- construct provider-compatible tool-result messages
- preserve clarification fallbacks
- preserve cancellation checks
- capture `planning_messages`

Do not convert this into a generator API in this change.

**`backend/src/soft_skills_backend/shared/tool_loop/context.py`**

- `ToolExecutionContext`
- any loop context object needed to preserve request/trace/workflow/session/turn data

### Assistant Refactor In Stage 2

Refactor `modules/assistant/workflows/service.py` to call the shared loop, but keep:

- existing prompt rendering
- existing history building
- existing required-tool heuristics
- existing final-response rewrite path
- existing event emission semantics

Refactor `modules/assistant/workflows/tools.py` only as far as needed to separate:

- generic loop execution concerns
- assistant-specific tool dispatch concerns

Do not remove persistence, approval, broker publishing, or child subpipeline behavior
from the assistant tool execution path.

### Admin-Agent Refactor In Stage 2

Add a tool-dispatch path for:

- `query_admin_data`

The admin-agent planning stage should:

1. build prompt + history + schema context
2. run the shared assistant-style tool loop
3. allow the model to call `query_admin_data`
4. return a structured payload containing:
   - final draft or intent summary from the loop
   - tool results
   - prompt/provider/model metadata

The admin-agent response stage should continue to produce the external response shape.
If needed, it may adapt the loop result into the existing `AdminAgentChatView`, but it
should not become a new free-form LLM response step in this refactor.

### Admin-Agent Tool Definition

`query_admin_data` should use provider-native tool calling with arguments:

- `sql: string`
- `params: [{key, value}]` or an equivalent shape that can be converted cleanly into
  the existing command model

Keep the tool contract intentionally narrow:

- one read-only `SELECT`
- admin-safe views only
- explicit projection only
- no comments
- no subqueries
- no set operations

### Stage 2 Exit Criteria

All Stage 1 criteria remain green, plus:

- assistant behavior is unchanged in practice
- admin agent uses provider-native tool calls rather than structured JSON planning
- admin-agent integration tests still pass without response-shape changes
- admin-agent smoke covers tool-call flow

Add or update unit coverage for:

- shared loop parity on no-tool final response
- shared loop parity on valid tool-call roundtrip
- shared loop parity on invalid tool-call clarification
- shared loop parity on tool-error clarification
- required-tool forcing behavior
- cancellation behavior

---

## Resolved Questions

### 1. Tool Loop Style

Decision: keep the current synchronous iterative style.

Reason:

- it matches the assistant runtime
- it is already proven in this codebase
- earlier redesigns were unstable
- streaming flexibility is not worth the risk in this refactor

Any async-generator or richer event API is a separate follow-up.

### 2. Admin-Agent Pipeline Structure

Decision: keep the existing stage structure.

Reason:

- current stage boundaries are useful for observability
- `response_formulation` currently gives deterministic behavior
- flattening the DAG would create an unnecessary semantic change

The tool loop should live inside the planning/execution part of the pipeline, not
replace the whole pipeline.

### 3. Inheritance Vs Composition

Decision:

- redactor: shared concrete implementation
- executor: inheritance or thin base is acceptable
- schema registry: shared dataclasses/helpers with thin domain registries
- guard: prefer shared helpers and selective composition over a deep template-method base

Reason:

- executors are genuinely similar
- guards have meaningful domain differences that should stay visible

### 4. SQL Guard Error Codes

Decision: keep domain-specific ranges and preserve current codes where possible.

Reason:

- lower migration risk
- simpler telemetry continuity
- easier diff review in a refactor whose purpose is reuse, not semantics cleanup

### 5. Redactor Sensitive Keywords

Decision: shared implementation with configurable extra keywords and current defaults.

Reason:

- preserves behavior now
- keeps future flexibility

### 6. Test Scope

Decision: run the full relevant suite after Stage 1 and Stage 2, not only narrow SQL tests.

Reason:

- these changes touch shared runtime paths
- smoke and integration coverage are needed to catch orchestration regressions

---

## Review Checklist

Before approving implementation:

- assistant loop behavior is demonstrably unchanged
- assistant generation tools still preserve child subpipeline metadata
- admin-agent response shape is unchanged
- assistant and admin SQL guards still enforce their domain-specific scoping rules
- no error-code churn without explicit reason
- no silent migration to a new framework tool runtime

## Bottom Line

This refactor is worth doing, but only if it stays disciplined:

1. Stage 1 removes obvious SQL duplication
2. Stage 2 extracts the assistant loop without redesigning it
3. The admin agent adopts provider-native tool calling without losing its current stage
   structure or deterministic response behavior

If the implementation starts to look like a new runtime architecture rather than a
behavior-preserving extraction, the scope has drifted.
