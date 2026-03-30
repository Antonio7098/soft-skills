# Assistant Read SQL Surface - Proposal

## Overview

The learner-facing assistant should keep explicit typed tools for state-changing and generation operations, but it should not need a growing catalog of bespoke read tools.

For assistant reads, prefer:

- curated schema context for assistant-safe views
- one constrained read-only SQL tool
- strict user and organisation scoping enforced below the model

This lets the model do what it is good at for investigative and retrieval tasks, while preserving hard product semantics for practice and generation workflows.

## Recommendation

Use a hybrid tool model for `backend/src/soft_skills_backend/modules/assistant/`:

- **Read path**: one schema-aware SQL read tool over assistant-safe views
- **Write path**: explicit typed tools for practice state changes and generation workflows
- **Security boundary**: enforced in the SQL execution layer and assistant-safe views, not in prompt instructions

This should replace most read-only retrieval tools such as collection and attempt lookups, but it should not replace:

- `start_collection_practice`
- `submit_active_practice_response`
- `end_active_practice`
- generation tools and any future approval-gated write tools

Those actions carry domain invariants and side effects that should remain explicit, typed, and auditable as first-class operations.

## Why This Fits The Assistant

The current assistant already has the right split in spirit:

- read tools for collections and attempts
- explicit action tools for practice flow
- explicit generation tools for content creation

The problem is that the read side will bloat over time if every new retrieval need becomes a new tool. A single constrained SQL read surface is more flexible for:

- filtering and combining collection metadata
- comparing recent attempts
- grounding answers in progress and recommendation summaries
- answering ad hoc learner questions without adding another narrow read tool

## Where This Principle Applies

Strong fit:

- admin and internal ops agents
- creator and reviewer assistants
- learner-facing read/query tasks over safe, bounded user context

Poor fit:

- assessment and scoring paths
- progression computation
- recommendation computation
- practice/session state transitions
- any tool with side effects or approval requirements

SQL is good for reads. It is not a substitute for domain services with product invariants.

## Current Assistant Surface

Today the assistant runtime effectively mixes:

### Read Tools

- list collections
- get collection detail
- list recent attempts
- get attempt detail

### Write / Stateful Tools

- start practice
- read active practice state
- submit practice response
- end practice

### Generation Tools

- generate collection
- generate prompt items

The recommendation is to collapse the read tools into one read surface while keeping the write and generation tools explicit.

## Proposed Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                    Learner Assistant Module                        │
│                                                                    │
│  ┌──────────────────┐   ┌─────────────────────┐   ┌──────────────┐ │
│  │ Schema Context   │──▶│ SQL Guardrail       │──▶│ LLM Provider │ │
│  │ (views, joins,   │   │ (validate/normalize │   │              │ │
│  │ examples)        │   │ read SQL intent)    │   └──────────────┘ │
│  └──────────────────┘   └─────────────────────┘          │         │
│                │                     │                    ▼         │
│                ▼                     ▼         ┌──────────────────┐ │
│       ┌──────────────────────────────────────┐ │ Assistant        │ │
│       │ Scoped Read-Only SQL Executor        │ │ Agent Loop       │ │
│       │ - SELECT only                        │ │                  │ │
│       │ - actor/org predicate injection      │ │ explicit write   │ │
│       │ - approved views only                │ │ tools remain     │ │
│       │ - row/time limits                    │ │ available        │ │
│       │ - output shaping                     │ └──────────────────┘ │
│       └──────────────────────────────────────┘                      │
└────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────────┐
│                 Database Assistant-Safe Read Surface               │
│                                                                    │
│  assistant_safe_collections_v                                      │
│  assistant_safe_attempt_summaries_v                                │
│  assistant_safe_attempt_details_v                                  │
│  assistant_safe_progress_snapshots_v                               │
│  assistant_safe_recommendations_v                                  │
│                                                                    │
│  All views are user-scoped, org-scoped, and column-allowlisted     │
└────────────────────────────────────────────────────────────────────┘
```

## Primary Tool

| Tool | Signature | Description |
|------|-----------|-------------|
| `query_user_context` | `(sql, params?)` | Execute validated read-only SQL against assistant-safe views for the authenticated learner |

The model also receives schema context for:

- allowed views
- allowed columns per view
- common joins
- field meanings
- example query patterns

## SQL Guardrails

The SQL tool must be constrained aggressively.

### Allowed

- `SELECT` queries only
- reads from approved assistant-safe views
- bounded filtering, ordering, grouping, and aggregates
- parameterized predicates

### Denied

- `INSERT`, `UPDATE`, `DELETE`, `ALTER`, `DROP`, `TRUNCATE`
- reads from raw base tables
- access to disallowed columns
- multi-statement queries
- SQL comments or syntax used to smuggle extra statements
- unbounded scans beyond configured limits

### Required Runtime Enforcement

1. Parse and validate SQL before execution
2. Reject any non-`SELECT` statement
3. Restrict `FROM` / `JOIN` targets to allowlisted views
4. Inject actor and organisation scoping predicates if not already present
5. Enforce max row count, timeout, and default ordering where useful
6. Shape or redact outputs before they are fed back into later model turns
7. Audit each query, denial, and response shape

The model must never query raw production tables directly; it may query only pre-scoped, allowlisted views with enforced bounds and audited execution.

## Assistant-Safe View Strategy

Do not expose raw application tables. Expose only assistant-safe views shaped for the learner assistant.

Example view families:

| View | Purpose | Notes |
|------|---------|-------|
| `assistant_safe_collections_v` | Browse collections available to the learner | Metadata only; no hidden authoring internals |
| `assistant_safe_attempt_summaries_v` | Summarize recent attempts | Bounded scores, timestamps, content links |
| `assistant_safe_attempt_details_v` | Fetch explainable attempt detail | No oversized payloads by default |
| `assistant_safe_progress_snapshots_v` | Ground progress questions | Snapshot-level metrics only |
| `assistant_safe_recommendations_v` | Ground next-step suggestions | Read model over recommendation outputs, not live computation |

These views should:

- include `user_id` and `organisation_id` for mandatory scoping
- omit internal-only and oversized columns
- expose summaries by default instead of full blobs
- preserve explainable evidence where needed without dumping raw artifacts unnecessarily

## Data Minimization

For the learner assistant, the issue is not only PII. It is also context discipline and prompt safety.

The read surface should prefer:

- attempt summaries over raw response payloads
- score/rubric summaries over full internal traces
- recommendation outputs over recommendation engine internals
- compact progress snapshots over unbounded history dumps

Full raw text from prior learner responses should not be broadly queryable unless there is a clear product need and a bounded safe view for it.

## Why Not Use SQL For Writes

The assistant should not mutate product state through generic SQL or generic database-oriented tools.

Keep explicit typed tools for:

- starting practice
- submitting learner responses
- ending practice
- triggering generation workflows
- any future saved-item, preference, or workflow mutations

Reasons:

- domain services enforce product invariants
- write operations need stable typed contracts and failure semantics
- approval, undo, and audit are clearer with explicit tools
- practice and generation actions are not simple CRUD

## Prompt And Agent Loop Implications

The assistant prompt should stop enumerating many narrow read tools and instead provide:

- one read tool definition for `query_user_context`
- explicit typed write/generation tool definitions
- schema context for the assistant-safe read surface

`PromptSecurityPolicy` still matters because:

- tool-returned content is injected into later turns
- even user-scoped data can contain prompt-shaped text
- bounded safe views reduce but do not eliminate prompt injection risk

## Suggested Module Changes

```
backend/src/soft_skills_backend/modules/assistant/
├── contracts/
│   ├── commands.py
│   ├── stream.py
│   ├── views.py
│   └── sql.py                # SQL read tool contracts
├── domain/
│   └── schema_registry.py    # Allowed views, columns, joins, examples
├── infra/
│   ├── repository.py
│   ├── realtime.py
│   ├── sql_guard.py          # SELECT-only validation for assistant reads
│   ├── sql_executor.py       # Scoped read execution
│   └── assistant_views.sql   # Assistant-safe DB views
└── workflows/
    ├── prompting.py          # Replace narrow read tool list with SQL tool + schema context
    ├── runtime_models.py
    └── tools.py              # Keep explicit write tools; route reads through SQL executor
```

## Migration Strategy

### Phase 1: Preserve Behavior, Add Read Surface

- add assistant-safe views
- add schema registry
- add SQL contracts, guard, and executor
- add `query_user_context` tool alongside existing read tools

### Phase 2: Update Prompt Contract

- teach the assistant to prefer `query_user_context` for read questions
- keep existing practice/generation tool rules unchanged

### Phase 3: Remove Redundant Read Tools

- remove narrow collection/attempt read tools once parity is proven
- keep explicit typed write and generation tools

### Phase 4: Approval Integration

- if approval infrastructure is present, mark `query_user_context` as safe to auto-allow
- keep future write tools approval-aware by default

## Example Queries

Good fit:

- "Show my last 5 scored attempts for interview practice"
- "Which saved collections focus on stakeholder communication?"
- "What skills have I improved most recently?"
- "What did you recommend I practice next and why?"

Bad fit:

- "Start a practice session from this collection"
- "Submit this answer for me"
- "Generate a new collection on negotiation"

The first set is read retrieval. The second set is action and should stay as explicit tools.

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| SQL read surface becomes too broad and leaks internal semantics | High | Use assistant-safe views only; no raw tables |
| Oversized query results bloat model context | High | Hard row caps, compact views, and summary-first shaping |
| Learner-facing prompts ingest unsafe text from tool results | High | Apply PromptSecurityPolicy and avoid broad raw-text access |
| Product semantics get hidden behind generic reads | Medium | Keep practice/generation tools explicit and typed |

## Bottom Line

The learner assistant should adopt the same core principle as the admin agent, but with a stricter boundary:

- one constrained SQL tool for safe reads
- explicit typed tools for writes and generation
- assistant-safe views instead of raw schema exposure

This reduces read-tool sprawl without weakening product invariants.
