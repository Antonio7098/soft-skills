# Admin Super Agent - Proposal

## Overview

An AI-powered admin assistant for investigation and analytics across the admin dashboard. For MVP, the agent should not get a large catalog of bespoke tools. Instead, it should receive:

- curated schema context for admin-safe tables/views
- a constrained read-only SQL tool
- strict organisation scoping and PII redaction enforced before results reach the model

This keeps the system more flexible for debugging and analytics while reducing implementation cost and tool-surface complexity.

## Recommendation

The current shape of this feature should be:

- **Read path**: one schema-aware read-only SQL capability over admin-safe views
- **Write path**: out of scope for MVP
- **Security boundary**: enforced in the query layer, not left to prompt instructions

This is preferable to exposing 15-20 narrow tools because:

- investigations are inherently relational and ad hoc
- SQL is a better fit for correlated debugging than pre-baked endpoint wrappers
- fewer tools means lower maintenance and less planning overhead for the model
- security controls are easier to harden around one constrained interface than around many custom tools

## Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                       Admin Agent Module                           │
│                                                                    │
│  ┌──────────────────┐   ┌─────────────────────┐   ┌──────────────┐ │
│  │ Schema Context   │──▶│ Query Guardrail     │──▶│ LLM Provider │ │
│  │ (models/views,   │   │ (validate/normalize │   │ (OpenAI/etc) │ │
│  │ joins, examples) │   │ SQL intent)         │   └──────────────┘ │
│  └──────────────────┘   └─────────────────────┘          │         │
│                │                     │                    ▼         │
│                ▼                     ▼         ┌──────────────────┐ │
│       ┌──────────────────────────────────────┐ │ Admin Agent      │ │
│       │ Scoped Read-Only SQL Executor        │ │ Pipeline         │ │
│       │ - SELECT only                        │ │ guard → enrich   │ │
│       │ - org predicate injection            │ │ → plan → query   │ │
│       │ - approved views only                │ │ → respond        │ │
│       │ - row/time limits                    │ └──────────────────┘ │
│       │ - result redaction / pseudonyms      │                      │
│       └──────────────────────────────────────┘                      │
└────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────────┐
│                    Database Admin-Safe Surface                     │
│                                                                    │
│  admin_agent_workflow_events_v                                     │
│  admin_agent_pipeline_runs_v                                       │
│  admin_agent_provider_calls_v                                      │
│  admin_agent_assistant_sessions_v                                  │
│  admin_agent_evaluation_runs_v                                     │
│                                                                    │
│  All views enforce column allowlisting, org scoping, and PII rules │
└────────────────────────────────────────────────────────────────────┘
```

## Module Structure

```
backend/src/soft_skills_backend/modules/admin_agent/
├── __init__.py
├── contracts/
│   ├── __init__.py
│   ├── sql.py                # SQL tool request/response contracts
│   └── views.py              # Agent response schemas
├── domain/
│   ├── __init__.py
│   ├── schema_registry.py    # Allowed views, columns, joins, examples
│   └── redactor.py           # Final row/result redaction helpers
├── infra/
│   ├── __init__.py
│   ├── sql_guard.py          # Validate SELECT-only SQL and apply limits
│   ├── sql_executor.py       # Executes scoped read-only queries
│   └── admin_views.sql       # DB views for admin-safe querying
├── workflows/
│   ├── __init__.py
│   └── admin_agent_pipeline.py
└── entrypoints/
    ├── __init__.py
    └── routes.py             # POST /admin-agent/chat
```

## Core Capability

### Primary Tool: Scoped Read-Only SQL

| Tool | Signature | Description |
|------|-----------|-------------|
| `query_admin_data` | `(sql, params?)` | Execute validated read-only SQL against admin-safe views |

The model should also receive schema context for:

- allowed views
- allowed columns per view
- common joins
- field meanings
- example query patterns

This gives the model enough structure to ask useful questions without exposing arbitrary database access.

## SQL Guardrails

The SQL tool must be constrained aggressively.

### Allowed

- `SELECT` queries only
- reads from approved `admin_agent_*` views
- bounded filtering, grouping, ordering, aggregates
- parameterized predicates

### Denied

- `INSERT`, `UPDATE`, `DELETE`, `ALTER`, `DROP`, `TRUNCATE`
- reads from raw base tables
- access to disallowed columns
- multi-statement queries
- comments or syntax used to smuggle extra statements
- unbounded scans beyond configured limits

### Required Runtime Enforcement

1. Parse and validate SQL before execution
2. Reject any non-`SELECT` statement
3. Restrict `FROM` / `JOIN` targets to allowlisted views
4. Inject org scoping predicates if not already present
5. Enforce max row count, timeout, and default ordering where needed
6. Redact or pseudonymize results before any LLM consumption
7. Audit each executed query and response shape

The model must never query raw production tables directly; it may query only pre-scoped, allowlisted views with enforced bounds and audited execution.

## Admin-Safe View Strategy

The strongest design is not "run raw SQL and redact later." The strongest design is to expose only pre-scoped, pre-redacted views.

Example view families:

| View | Purpose | Notes |
|------|---------|-------|
| `admin_agent_workflow_events_v` | Investigate workflow event streams | Payload fields trimmed to safe subset |
| `admin_agent_pipeline_runs_v` | Inspect pipeline executions | Safe run metadata and timing only |
| `admin_agent_provider_calls_v` | Debug provider latency/failures | No raw prompts or message content |
| `admin_agent_assistant_sessions_v` | Investigate session state | No full conversation text |
| `admin_agent_evaluation_runs_v` | Review eval outcomes | Scores retained, response text removed |

These views should:

- include `organisation_id` for mandatory scoping
- omit high-risk columns entirely
- replace raw user IDs with stable pseudonyms where possible
- expose only investigation-safe payload fields

## PII Redaction Strategy

**Critical: no raw PII should reach external LLM providers.**

Prefer removing or masking sensitive data in the database view layer first, with a second defensive redaction pass in the application layer.

### Primary Controls

1. **Org scoping**
   - every query is restricted to the admin's organisation

2. **Column allowlisting**
   - risky fields are not queryable at all

3. **Pseudonymization**
   - internal user identifiers become stable aliases like `learner_001`

4. **Content suppression**
   - free-text assistant/user content is removed or replaced with placeholders

5. **Field-level masking**
   - emails and similar identifiers are masked if they must appear

### Data Classification for LLM Consumption

| Can Send to LLM | Must NOT Send to LLM |
|-----------------|---------------------|
| Aggregated metrics | Raw learner responses |
| Pipeline names, stage names | Email addresses |
| Event types, status codes | Assistant conversation content |
| Eval scores, skill scores | Identifiable user content |
| Pseudonyms | Raw prompts/completions |
| Timestamps, latency percentiles | Full sensitive payload blobs |

### Redaction Implementation Notes

Application-layer redaction still has value, but it should be a backstop:

- verify output rows only contain allowed keys
- mask residual identifiers missed upstream
- redact unexpected text payloads conservatively
- prevent accidental leakage through error messages

## Agent Pipeline

```
┌─────────┐   ┌─────────┐   ┌───────┐   ┌──────────┐   ┌──────────┐
│  guard  │──▶│ enrich  │──▶│ plan  │──▶│  query   │──▶│ respond  │
└─────────┘   └─────────┘   └───────┘   └──────────┘   └──────────┘
    │             │            │             │
    ▼             ▼            ▼             ▼
Validate   Load admin     Decide query   Execute validated
request    context and    strategy and   SQL against scoped
authority  org scope      parameters     views, then redact
```

### Stage Definitions

| Stage | Kind | Purpose |
|-------|------|---------|
| `input_guard` | GUARD | Validate admin authority and request shape |
| `context_enrich` | ENRICH | Load admin context, org scope, permissions |
| `query_planning` | WORK | Form SQL intent using schema context |
| `query_execution` | AGENT | Run validated SQL with limits and redaction |
| `response_formulation` | TRANSFORM | Summarize findings in natural language |

## API Endpoint

```
POST /admin-agent/chat
Authorization: X-User-ID, X-Organisation-ID (admin role required)

Request:
{
  "message": "Show failed pipeline runs in the last hour for my org",
  "conversation_id": "optional-for-context"
}

Response:
{
  "message": "Found 12 failed runs across 3 pipelines...",
  "tool_results": [...],
  "conversation_id": "..."
}
```

## Security Model

1. **Authentication**: Header-based auth same as existing admin endpoints
2. **Authorization**: admin-only access via existing auth guard
3. **Data isolation**: org scoping enforced in the SQL execution layer and/or admin-safe views
4. **PII protection**: sensitive columns excluded upstream, residual values redacted before LLM calls
5. **Audit**: log query text, parameter values, row counts, latency, and denial reasons
6. **No write operations**: no mutation capability in MVP

## Dependencies

| Component | Effort | Notes |
|-----------|--------|-------|
| Module scaffolding | Low | Package structure |
| Admin-safe SQL views | Medium | Core security boundary |
| Schema registry/context | Medium | View docs, joins, examples |
| SQL guard/validator | Medium | SELECT-only enforcement |
| SQL executor | Medium | Scoping, pagination, timeout, auditing |
| Redaction backstop | Low | Defensive output filtering |
| Stageflow pipeline | Medium | 5 stages |
| API endpoint | Low | Single POST endpoint |
| Tests | Medium | SQL validation, scoping, redaction, pipeline |

## Implementation Order

1. **Admin-safe views** - define `admin_agent_*` views with scoped/redacted columns
2. **Schema registry** - document allowed views, columns, joins, and examples
3. **SQL contracts** - request/response types for the single SQL tool
4. **SQL guard** - parse and validate `SELECT`-only queries
5. **SQL executor** - inject scope/limits, execute, audit, redact outputs
6. **Admin agent pipeline** - guard, enrich, plan, query, respond
7. **API endpoint** - expose `POST /admin-agent/chat`
8. **Tests** - validator, org scoping, view safety, redaction, end-to-end flow

## Future Enhancements (Out of Scope for MVP)

- explicit write tools with approval gates
- saved investigation queries and reusable report templates
- multi-turn investigative context
- visual result rendering in the admin dashboard
- richer non-SQL helper tools where SQL is genuinely a poor fit
