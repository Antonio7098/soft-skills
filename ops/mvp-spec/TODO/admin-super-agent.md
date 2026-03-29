# Admin Super Agent - Proposal

## Overview

An AI-powered admin assistant that enables natural language queries and actions across the admin dashboard. The agent operates within a strict security boundary with PII redaction before any external LLM calls.

## Motivation

Current admin dashboard requires navigating multiple endpoints to investigate issues, query events, or manage users. An admin super agent allows:
- Natural language investigation of events, pipelines, and user activity
- Unified interface for user management operations
- Context-aware analytics queries across the system
- Faster incident investigation with correlated event data

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Admin Agent Module                          │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────────┐   │
│  │ Admin Tools│───▶│PII Redactor │───▶│  LLM Provider      │   │
│  │ (Read-only)│    │ (Before API │    │  (OpenAI/etc.)     │   │
│  └─────────────┘    │  calls)     │    └─────────────────────┘   │
│         │          └──────────────┘              │               │
│         ▼                     │                 ▼               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Admin Agent Pipeline (Stageflow)           │    │
│  │  guard → enrich → plan → execute_tools → respond        │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌────────────────┐  ┌─────────────────┐  ┌─────────────────────┐
│AdminService    │  │Repositories     │  │AnalyticsRepository  │
│(existing)      │  │(WorkflowEvent, │  │(existing)           │
│                │  │ PipelineRun,    │  │                     │
│                │  │ ProviderCall)   │  │                     │
└────────────────┘  └─────────────────┘  └─────────────────────┘
```

## Module Structure

```
backend/src/soft_skills_backend/modules/admin_agent/
├── __init__.py
├── contracts/
│   ├── __init__.py
│   ├── tools.py          # Tool definitions (AdminToolName, AdminToolRequest)
│   └── views.py          # Response schemas
├── domain/
│   ├── __init__.py
│   └── redactor.py       # PIIRedactor class
├── infra/
│   ├── __init__.py
│   ├── tool_executor.py  # Executes admin tools with redaction
│   └── query_services.py # Repository wrappers for agent queries
├── workflows/
│   ├── __init__.py
│   └── admin_agent_pipeline.py  # Stageflow pipeline
└── entrypoints/
    ├── __init__.py
    └── routes.py         # POST /admin-agent/chat
```

## Tool Definitions

### Category 1: Event Query Tools (Read-Only SQL via Repository)

| Tool | Signature | Description |
|------|-----------|-------------|
| `query_workflow_events` | `(event_types?, user_id?, trace_id?, from?, to?, limit?)` | Query workflow_events table |
| `query_pipeline_runs` | `(pipeline_name?, status?, user_id?, from?, to?, limit?)` | Query pipeline_runs table |
| `query_provider_calls` | `(operation?, provider?, success?, from?, to?, limit?)` | Query provider_calls table |
| `query_assistant_sessions` | `(user_id?, status?, from?, to?, limit?)` | Query assistant_sessions |
| `query_evaluation_runs` | `(suite_id?, status?, learner_id?, from?, to?, limit?)` | Query evaluation_runs |

### Category 2: User Management Tools (via AdminService)

| Tool | Signature | Description |
|------|-----------|-------------|
| `list_users` | `(search?, role?, is_active?, offset?, limit?)` | Paginated user listing |
| `get_user` | `(user_id)` | Single user details |
| `get_user_activity` | `(user_id)` | Activity summary (sessions, attempts, logins) |
| `update_user_role` | `(user_id, role)` | Change user role |
| `update_user_status` | `(user_id, is_active)` | Suspend/activate user |

### Category 3: Analytics Tools (via AdminService)

| Tool | Signature | Description |
|------|-----------|-------------|
| `get_analytics_overview` | `(from?, to?)` | Dashboard aggregates |
| `get_learner_analytics` | `(learner_id, from?, to?)` | Individual learner metrics |
| `get_cohort_analytics` | `(cohort_id, from?, to?)` | Cohort-level metrics |
| `compare_cohorts` | `(cohort_ids[], from?, to?)` | Side-by-side comparison |

### Category 4: Eval & Prompt Tools

| Tool | Signature | Description |
|------|-----------|-------------|
| `list_evaluation_suites` | `()` | List all eval suites |
| `get_evaluation_run` | `(run_id)` | Run details with case results |
| `list_prompts` | `()` | Prompt library summary |
| `get_prompt_analytics` | `(prompt_name, version?)` | Per-version performance |

### Category 5: Pipeline Visualization Tools

| Tool | Signature | Description |
|------|-----------|-------------|
| `list_pipelines` | `()` | All pipeline DAG definitions |
| `get_pipeline_runs` | `(pipeline_name, limit?)` | Recent runs for a pipeline |
| `get_pipeline_trace` | `(run_id)` | Execution trace for visualization |

## PII Redaction Strategy

**Critical: No PII reaches external LLM providers.**

### Redaction Layers

1. **User Identifiers** → Pseudonymized before LLM sees them
   - Internal `user_abc123` → `learner_001` (stable per admin-learner pair)

2. **Email Addresses** → Masked
   - `john.smith@company.com` → `j***@company.com`

3. **Assistant Message Content** → Stripped or summarized
   - Full user messages replaced with `[user message redacted]`

4. **Assessment Responses** → Scores kept, response text redacted

5. **Raw Payload Fields** → Scanned and redacted by field name patterns

### Data Classification for LLM Consumption

| Can Send to LLM | Must NOT Send to LLM |
|-----------------|---------------------|
| Aggregated metrics | Raw learner responses |
| Pipeline names, stage names | Email addresses |
| Event types, status codes | Assistant conversation content |
| Eval scores, skill scores | Identifiable user content |
| Pseudonym mappings (internal) | Full trace/request IDs from payloads |
| Timestamps, latency percentiles | Any content that identifies individuals |

### Pseudonymization Implementation

```python
class PIIRedactor:
    """Redacts PII before sending to external LLM providers."""
    
    def pseudonymize_user_ids(self, data: dict, admin_user_id: str, learner_user_id: str) -> dict:
        """Generate stable pseudonym mapping per admin-learner pair."""
        
    def redact_workflow_event(self, event: WorkflowEventRecord) -> WorkflowEventRecord:
        """Replace user_id with pseudonym, strip sensitive payload fields."""
        
    def redact_assistant_messages(self, messages: list[AssistantMessageRecord]) -> list:
        """Replace user content with [content redacted]."""
        
    def mask_email(self, email: str) -> str:
        """Mask email preserving first char and domain."""
```

## Agent Pipeline (Stageflow)

```
┌─────────┐   ┌─────────┐   ┌───────┐   ┌────────────────┐   ┌──────────┐
│  guard  │──▶│ enrich  │──▶│ plan  │──▶│ execute_tools  │──▶│ respond  │
└─────────┘   └─────────┘   └───────┘   └────────────────┘   └──────────┘
    │             │            │              │
    ▼             ▼            ▼              ▼
Validate   Load admin     Determine      Call tools with
request    context,      which tools    PII redaction
authority  user info      to call,      applied, collect
                           ordering      results
```

### Stage Definitions

| Stage | Kind | Purpose |
|-------|------|---------|
| `input_guard` | GUARD | Validate admin authority, check request validity |
| `context_enrich` | ENRICH | Load admin context, learner relationships, permissions |
| `tool_planning` | WORK | Determine which tools to call, in what order |
| `tool_execution` | AGENT | Execute tools with PII redaction, handle errors |
| `response_formulation` | TRANSFORM | Synthesize results into natural language response |

## API Endpoint

```
POST /admin-agent/chat
Authorization: X-User-ID, X-Organisation-ID (admin role required)

Request:
{
  "message": "Show me workflow events for user abc123 in the last hour",
  "conversation_id": "optional-for-context"
}

Response:
{
  "message": "Found 15 workflow events...",
  "tool_results": [...],
  "conversation_id": "..."
}
```

## Security Model

1. **Authentication**: Header-based auth same as existing admin endpoints
2. **Authorization**: `require_admin_actor()` - only org admins can access
3. **Data Isolation**: PII redaction applied BEFORE any LLM call
4. **Audit**: All agent actions logged to `workflow_events` with `admin.agent.*` event types
5. **No Write Operations**: Agent only reads data (no user modifications via agent initially)

## Dependencies

| Component | Effort | Notes |
|-----------|--------|-------|
| Module scaffolding | Low | Package structure |
| Tool definitions | Medium | ~15-20 tools |
| PII Redactor | Medium | Pattern-based + field name scanning |
| Repository wrappers | Low | Reuse existing repositories |
| AdminService integration | Low | Call existing service methods |
| Stageflow pipeline | Medium | 5 stages |
| API endpoint | Low | Single POST endpoint |
| Tests | Medium | Tools, redaction, pipeline |

## Implementation Order

1. **Module scaffolding** - Package structure, __init__.py files
2. **Tool definitions** - contracts/tools.py with all tool schemas
3. **PII Redactor** - domain/redactor.py
4. **Query Services** - infra/query_services.py wrapping repositories
5. **Tool Executor** - infra/tool_executor.py
6. **Admin Agent Pipeline** - workflows/admin_agent_pipeline.py
7. **API Endpoint** - entrypoints/routes.py
8. **Tests** - Tool tests, redaction tests, pipeline tests

## Future Enhancements (Out of Scope for MVP)

- Write operations (user management via agent)
- Multi-turn conversation with full context
- Custom report generation
- Automated action execution with approval workflows
- Integration with external tools (Slack notifications, etc.)
