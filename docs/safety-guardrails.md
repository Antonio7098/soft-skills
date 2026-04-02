# Backend AI Safety and Guardrails

This document provides a comprehensive reference for all safety mechanisms, guardrails, and security controls in the Soft Skills backend AI flows.

## Table of Contents

1. [Pipeline Guard Stages](#1-pipeline-guard-stages)
2. [Prompt Security](#2-prompt-security)
3. [SQL Guardrails](#3-sql-guardrails)
4. [LLM Output Validation](#4-llm-output-validation)
5. [Approval Workflows](#5-approval-workflows)
6. [Cancellation and Timeouts](#6-cancellation-and-timeouts)
7. [Authentication and Authorization](#7-authentication-and-authorization)
8. [Circuit Breaker Pattern](#8-circuit-breaker-pattern)
9. [Error Handling](#9-error-handling)

---

## 1. Pipeline Guard Stages

The backend uses **Stageflow** as its workflow orchestration engine. Guard stages (`StageKind.GUARD`) perform validation and precondition checks, potentially short-circuiting pipeline execution by returning `StageOutput.cancel()`.

### 1.1 Guard Implementation Pattern

Guards are implemented as async functions that validate inputs and return early with cancellation if validation fails:

```python
async def input_guard(_ctx: StageContext) -> Any:
    # Validation logic
    if not valid:
        return StageOutput.cancel()
    return validated_input
```

### 1.2 Guard Stages by Module

| Module | Guard Stages | Location |
|--------|-------------|----------|
| `assistant` | `input_guard` | `modules/assistant/workflows/service.py:256` |
| `catalog/generation` | `input_guard`, `blueprint_guard`, `output_guard` | `modules/catalog/workflows/generation/collection_pipeline.py` |
| `catalog/prompt_items` | `input_guard`, `plan_guard`, `output_guard` | `modules/catalog/workflows/generation/prompt_item_pipeline.py` |
| `catalog/collections` | `input_guard` (multiple operations) | `modules/catalog/workflows/collections/service.py` |
| `practice` | `input_guard`, `output_guard` | `modules/practice/use_cases/practice_service.py` |
| `progression` | `input_guard` | `modules/progression/workflows/service.py` |
| `evaluation` | `input_guard` | `modules/evaluation/workflows/service.py` |
| `admin_agent` | `input_guard` | `modules/admin_agent/workflows/service.py` |

### 1.3 Guard Validation Types

- **Input validation**: Checks command validity, ownership, session state
- **Cancellation checks**: Early exit if execution was cancelled
- **Blueprint validation**: Validates LLM-generated structures
- **Output validation**: Ensures generated content meets requirements

### 1.4 Short-Circuit Behavior

When a guard returns `StageOutput.cancel()`, the pipeline:
1. Stops execution immediately
2. Returns partial results (if any stages completed)
3. Logs the cancellation reason
4. Emits cancellation events for observability

---

## 2. Prompt Security

### 2.1 PromptSecurityPolicy

**Location**: Imported from `stageflow.agent.security`

The `PromptSecurityPolicy` class provides content sanitization and guardrail detection:

```python
self._prompt_security = PromptSecurityPolicy(
    max_user_chars=12000,
    max_tool_chars=12000,
)
```

**Usage Locations**:
- Assistant service: `modules/assistant/workflows/service.py:121`
- Catalog generation: `modules/catalog/use_cases/catalog_service.py:95`

### 2.2 Content Sanitization

| Method | Purpose | Location |
|--------|---------|----------|
| `build_user_message()` | Sanitizes user input before LLM submission | `modules/assistant/workflows/service.py:616` |
| `build_tool_message()` | Sanitizes tool outputs before appending to context | `modules/assistant/workflows/service.py:715` |

### 2.3 Maximum Length Enforcement

| Input Type | Max Length | Location |
|------------|------------|----------|
| User message | 12,000 chars | `modules/assistant/contracts/commands.py:19` |
| Tool output | 12,000 chars | `config.py:59` |
| SQL query | 4,000 chars | `modules/assistant/contracts/sql.py:13` |

### 2.4 Error Codes

| Code | Description |
|------|-------------|
| `SS-VALIDATION-204` | Assistant blocked unsafe user content |
| `SS-VALIDATION-205` | Assistant blocked unsafe tool output |
| `SS-VALIDATION-056` | Generation input blocked by prompt security |
| `SS-VALIDATION-048` | Chat generation prompt blocked |
| `SS-VALIDATION-066` | Prompt item generation prompt blocked |

### 2.5 System Prompt Isolation

System prompts are isolated from user content:
- Set as the first message with `{"role": "system", "content": ...}`
- Never mixed with user content in the message array
- Security instructions explicitly prohibit information leakage

---

## 3. SQL Guardrails

### 3.1 SQL Guard Classes

| Class | Purpose | Location |
|-------|---------|----------|
| `AssistantSqlGuard` | Validates learner-safe read-only SQL | `modules/assistant/infra/sql_guard.py` |
| `AdminAgentSqlGuard` | Validates admin-agent read-only SQL | `modules/admin_agent/infra/sql_guard.py` |

### 3.2 Validation Pipeline

Each guard implements a multi-stage validation:

1. **Normalization**: Strip whitespace, remove trailing semicolons
2. **Disallowed SQL rejection**: Block INSERT, UPDATE, DELETE, ALTER, DROP, etc.
3. **Comment blocking**: Reject `--`, `/*`, `*/` comments
4. **Subquery/set operation blocking**: Reject UNION, INTERSECT, EXCEPT
5. **View extraction**: Validate FROM/JOIN targets against schema registry
6. **Column projection validation**: Reject `SELECT *` (except `COUNT(*)`)
7. **Organisation scoping**: Add `WHERE organisation_id = :organisation_id`
8. **Row limiting**: Apply `LIMIT` clause

### 3.3 Schema Registry

**Assistant Views** (`modules/assistant/domain/schema_registry.py`):
- `assistant_safe_skills_v` - Organisation-scoped skills
- `assistant_safe_competencies_v` - Organisation-scoped competencies
- `assistant_safe_collections_v` - Visible collections
- `assistant_safe_attempt_summaries_v` - Recent attempts
- `assistant_safe_progress_snapshots_v` - Progress data
- `assistant_safe_recommendations_v` - Recommendations

**Admin Agent Views** (`modules/admin_agent/domain/schema_registry.py`):
- `admin_agent_workflow_events_v` - Workflow events
- `admin_agent_pipeline_runs_v` - Pipeline telemetry
- `admin_agent_provider_calls_v` - Provider call telemetry
- `admin_agent_assistant_sessions_v` - Session metadata
- `admin_agent_evaluation_runs_v` - Evaluation records

### 3.4 Row Limits

| Guard | Default Limit | Config Location |
|-------|---------------|-----------------|
| Assistant | 50 rows | `config.py:88` (via row_limit param) |
| Admin Agent | 50 rows | `config.py:88` |

### 3.5 Result Redaction

Both guards use `ResultRedactor` implementations to sanitize query results:

- **Email masking**: `***@domain.com` format
- **Sensitive column detection**: Redacts columns with "email", "content", "prompt", "response", "text", "payload"
- **Length limiting**: Truncates strings >240 characters
- **Complex type handling**: Redacts lists, dicts, tuples, sets

### 3.6 Query Timeout

| Guard | Default Timeout | Error Code |
|-------|-----------------|------------|
| Assistant | Configurable (default 5s) | `SS-ORCHESTRATION-205` |
| Admin Agent | `admin_agent_query_timeout_seconds` (default 5s) | `SS-ORCHESTRATION-301` |

### 3.7 Validation Error Codes

| Code | Description |
|------|-------------|
| `SS-VALIDATION-301` | Assistant: Query must start with SELECT |
| `SS-VALIDATION-302` | Admin agent: Query must start with SELECT |
| `SS-VALIDATION-313` | Assistant: SQL comments not allowed |
| `SS-VALIDATION-303` | Admin agent: SQL comments not allowed |
| `SS-VALIDATION-314` | Assistant: Subqueries not allowed |
| `SS-VALIDATION-304` | Admin agent: Subqueries not allowed |
| `SS-VALIDATION-315` | Assistant: Denied SQL token |
| `SS-VALIDATION-305` | Admin agent: Denied SQL token |
| `SS-VALIDATION-316` | Assistant: Invalid view |
| `SS-VALIDATION-306` | Admin agent: Invalid view |
| `SS-VALIDATION-317` | Assistant: SELECT wildcard not allowed |
| `SS-VALIDATION-307` | Admin agent: SELECT wildcard not allowed |

---

## 4. LLM Output Validation

### 4.1 TypedLLMOutput

**Location**: `engines/marking/use_cases/structured_output.py:90`

The `TypedLLMOutput` class provides Pydantic-backed typed output parsing with bounded corrective retries:

```python
TypedLLMOutput(
    model_type=MyModel,
    schema_version="1.0",
    max_validation_retries=3,
    repair_mode=StructuredOutputRepairMode.SELF_CORRECT,
    timeout_seconds=30.0,
)
```

### 4.2 Validation Flow

1. **Schema-based parsing**: Uses Pydantic `model_validate()` for strict schema enforcement
2. **Retry on failure**: Up to `max_validation_retries` attempts with corrective feedback
3. **Fail-closed**: Raises `StructuredOutputRejectionError` if all retries fail

### 4.3 StructuredOutputRejectionError

```python
@dataclass(slots=True)
class StructuredOutputRejectionError(Exception):
    app_error: AppError
    raw_payload: dict[str, Any]
```

**Error code**: `SS-VALIDATION-019` - "Provider returned malformed structured output"

### 4.4 Per-Skill Fan-Out (Marking Engine)

The marking engine assesses each skill independently via `asyncio.gather()` with semaphore-bounded concurrency:

- Each skill receives exactly one rubric criterion with full level definitions
- Returns `PerSkillAssessment` with score, rationale, and 1-2 evidence quotes
- Undergoes deterministic verification (skill slug match, score range, evidence grounding)
- Supports bounded corrective retries for malformed output

**Fail-closed behavior**: If any required skill assessment fails after retries, the entire parent assessment fails. Partial results are never persisted.

### 4.5 Evidence Grounding

Evidence validation ensures:
- Extracted evidence text exists in the candidate response
- Rationale is grounded in the assessment
- No hallucinations in scoring justification

### 4.6 Score Range Validation

- Rubric-specific scales (1-5) mapped to canonical 0-1 range
- Deterministic aggregation: `overall_score` = rounded weighted mean of per-skill scores

---

## 5. Approval Workflows

### 5.1 Approval Service

**Location**: `modules/assistant/workflows/approval_service.py`

The `AssistantApprovalService` manages tool approval workflows:

- `request_tool_approval()`: Creates persistent approval request
- `await_decision()`: Waits for human approval with timeout
- `record_decision()`: Records approval/denial decision

### 5.2 Approval Request Model

```python
# Database: assistant_approval_requests
- session_id, turn_id, tool_call_id, user_id
- tool_name, status (PENDING/APPROVED/DENIED/EXPIRED)
- approval_message, payload_summary
- decision_reason, decided_by_user_id
- requested_at, expires_at, decided_at
```

### 5.3 Auto-Allow Configuration

**Location**: `config.py:59-68`

```python
tool_approval_auto_allow = (
    "query_user_context",
    "query_admin_data",
    "start_collection_practice",
    "get_active_practice",
    "submit_active_practice_response",
    "end_active_practice",
    "generate_collection",
    "generate_prompt_items",
)
```

Tools in the auto-allow list skip human approval. All other tools require explicit approval.

### 5.4 Approval Timeout

| Setting | Default | Max | Error Code |
|---------|---------|-----|------------|
| `tool_approval_timeout_seconds` | 60.0s | 300s | `SS-ORCHESTRATION-202` |

If approval not received within timeout, status is set to `EXPIRED` and pipeline continues.

### 5.5 Approval API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/assistant/approvals` | List approval requests |
| POST | `/assistant/approvals/{request_id}` | Decide on approval request |

---

## 6. Cancellation and Timeouts

### 6.1 Cancellation Function

**Location**: `modules/catalog/workflows/generation/collection_pipeline.py:118`

```python
async def _yield_for_cancel():
    # Check if execution is cancelled
    # Refresh cancellation state from stream repository
    # Yield briefly (0.15s) for WebSocket delivery
    # Return StageOutput.cancel() if cancelled
```

### 6.2 Cancellation Flow

1. **User request**: Cancellation via HTTP endpoint or WebSocket message
2. **Service layer**: `request_cancel()` updates repository and publishes events
3. **Execution tracking**: `ActiveTurnExecution`/`GenerationExecution` objects track state
4. **Pipeline integration**: Context marked as cancelled via `mark_canceled()`
5. **Stage checks**: Stages check `is_cancelled` flag and return `StageOutput.cancel()`
6. **Task cancellation**: `asyncio.Task.cancel()` after grace period
7. **Cleanup**: Resources released, events emitted

### 6.3 Timeout Configuration

| Timeout | Default | Location |
|---------|---------|----------|
| `smoke_timeout_seconds` | 10.0s | `config.py` |
| `llm_assistant_timeout_seconds` | 20.0s (max 120s) | `config.py:55` |
| `llm_admin_agent_timeout_seconds` | 20.0s (max 120s) | `config.py:56` |
| `llm_marking_timeout_seconds` | 30.0s (max 300s) | `config.py:57` |
| Pipeline timeout | Calculated from settings | Per-operation |

### 6.4 LLM Provider Timeout Handling

**Location**: `platform/providers/llm/openai_compatible.py`

- Uses `httpx.Timeout` with separate connect, read, write timeouts
- Wraps calls in `asyncio.timeout()` context manager
- Implements exponential backoff retry on timeout
- Error message: "Provider request exceeded the configured timeout budget"

### 6.5 Graceful Shutdown

**Location**: `app.py:40-57`

FastAPI lifespan handles:
1. `background_tasks.shutdown()` - Cancel running tasks
2. `container.shutdown()` - Drain event sink
3. `container.dispose()` - Dispose database engine

---

## 7. Authentication and Authorization

### 7.1 HeaderAuthProvider

**Location**: `shared/auth.py:57`

```python
class HeaderAuthProvider:
    async def get_actor(request: Request) -> Actor | None
    async def require_actor(request: Request) -> Actor  # Raises SS-AUTH-001
    async def require_org_admin(request: Request) -> Actor  # Raises SS-AUTH-004
```

### 7.2 Actor Dataclass

```python
@dataclass(slots=True)
class Actor:
    user_id: str
    email: str
    organisation_id: str | None = None
    organisation_role: str | None = None
```

### 7.3 Authentication Flow

1. Extract `X-User-ID` header
2. Validate user exists in database
3. Resolve organisation context via `X-Organisation-ID` header or auto-resolve
4. Record auth events (`auth.login.success.v1`, `auth.login.failed.v1`)

### 7.4 Auth Error Codes

| Code | Description |
|------|-------------|
| `SS-AUTH-001` | Authentication required |
| `SS-AUTH-004` | Organisation admin access required |

### 7.5 Organisation Scoping

- SQL guards automatically add `WHERE organisation_id = :organisation_id`
- Repository queries filter by organisation
- Multi-tenancy enforced at database query level

---

## 8. Circuit Breaker Pattern

### 8.1 Implementation

**Location**: `platform/observability/circuit_breaker.py`

Database-backed circuit breaker for multi-worker deployments:

```python
class DatabaseCircuitBreaker:
    def get_state(name: str) -> CircuitBreakerStatus
    def is_callable(name: str) -> bool
    def record_success(name: str)
    def record_failure(name: str)
```

### 8.2 Configuration

| Setting | Default |
|---------|---------|
| `CIRCUIT_BREAKER_THRESHOLD` | 5 failures |
| `CIRCUIT_BREAKER_RESET_TIMEOUT_SECONDS` | 30 seconds |

### 8.3 States

- **CLOSED**: Normal operation
- **OPEN**: Failures exceeded threshold
- **HALF_OPEN**: Testing recovery

### 8.4 Integration

The `CircuitBreakerInterceptor` is part of Stageflow's default interceptor stack in `platform/workflows/stageflow_runtime.py:41`.

---

## 9. Error Handling

### 9.1 Error Code Prefixes

| Prefix | Domain |
|--------|--------|
| `SS-ORCHESTRATION-xxx` | Pipeline orchestration failures |
| `SS-VALIDATION-xxx` | Validation failures (input, schema, engine config) |
| `SS-SCORING-xxx` | Assessment scoring and marking failures |
| `SS-DOMAIN-xxx` | Domain logic violations |
| `SS-AUTH-xxx` | Authentication and authorization |

### 9.2 Error Creation Functions

| Function | Status Code | Usage |
|----------|-------------|-------|
| `orchestration_error()` | 500 | Pipeline-level failures |
| `validation_error()` | 422 | Input/data validation |
| `scoring_error()` | 500 | Assessment marking failures |
| `domain_error()` | 400 | Domain logic violations |
| `auth_error()` | 401 | Authentication failures |

### 9.3 Pipeline Error Handling

`run_logged_pipeline()` handles:
- `UnifiedPipelineCancelled` → Logged as "cancelled", results returned
- `UnifiedStageExecutionError` → Original exception re-raised after logging
- Generic `Exception` → Wrapped in `orchestration_error("SS-ORCHESTRATION-005")`

### 9.4 Engine Error Semantics

| Engine | Fail-Closed Behavior |
|--------|---------------------|
| Marking | Per-skill failures after retries → pipeline fails |
| Progression | Missing version metadata → rejection |
| Recommendation | Empty candidate list → rejection |

---

## Summary

The backend implements defense-in-depth safety through multiple layers:

1. **Pipeline Guards**: Input validation with early short-circuit
2. **Prompt Security**: Content sanitization and length limits
3. **SQL Guardrails**: Allowlisted views, query validation, row limits, redaction
4. **LLM Output Validation**: Typed schema parsing with bounded retries
5. **Approval Workflows**: Human-in-the-loop for sensitive operations
6. **Cancellation**: Graceful early termination at multiple levels
7. **Authentication**: Actor-based identity with organisation scoping
8. **Circuit Breaker**: Failure isolation to prevent cascading issues

All mechanisms work together to ensure safe, reliable AI workflow execution while maintaining observability and operational integrity.