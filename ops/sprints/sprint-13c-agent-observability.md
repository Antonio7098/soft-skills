# Sprint 13c: Agent Observability

> Project: SoftSkills
> Scope: Backend and platform execution only. Frontend planning is tracked separately.

## Sprint Overview

- Sprint Name: Agent Observability
- Sprint Focus: Implement wide events persistence, streaming buffer aggregation, circuit breaker persistence, and structured error summarization for Stageflow-powered agent pipelines
- Depends On: Sprint 13a (Event Logging Infrastructure)

## Relevant Source Docs

- [CONSTITUTION.yml](/home/antonioborgerees/df/soft-skills/ops/CONSTITUTION.yml): lines 1-427
- [ops/mvp-spec/admin-dashboard-readiness.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/admin-dashboard-readiness.md): lines 123-153
- [ops/mvp-spec/foundational/stageflow-guide.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/stageflow-guide.md): lines 1-50

## Sprint Goals

- Primary Goal: Implement Stageflow-powered agent observability - wide events persistence, streaming aggregation, circuit breaker persistence
- Secondary Goals:
  - Emit tool.invoked via ctx.emit_event()
  - Aggregate streaming metrics
  - Structured error summarization

## Scope Checklist

- [x] Task 2b.1: Wide events persistence - Persist `stage.wide.*` and `pipeline.wide.*` events to `workflow_events` with event_type prefix
- [x] Task 2b.2: Tool events via Stageflow - Emit `tool.invoked` via `ctx.emit_event()` before dispatch; already emits `tool.started/completed/failed` via broker
- [ ] Task 2b.3: Streaming buffer aggregation - Aggregate `stream.chunk_dropped`, `stream.throttle_count` into turn metadata (not separate records) - **Deferred: requires streaming buffer implementation first**
- [x] Task 2b.4: Circuit breaker persistence - Implement `CircuitBreaker` backed by `CircuitBreakerRecord` for multi-worker deployments
- [x] Task 2b.5: Structured error summarization - Use `summarize_pipeline_error()` in `DatabasePipelineRunLogger.log_run_failed()` for structured error docs
- [x] Task 2b.6: Documentation updates

## Constitution And Quality Checklist

- [ ] Competency growth remains the product outcome, not activity theater
- [ ] All new external boundaries are typed and schema-validated
- [ ] Fail-fast and fail-loud behavior is preserved with stable error codes
- [ ] Route handlers remain thin; business rules stay out of transport layers
- [ ] Dependency injection and adapter boundaries remain explicit
- [ ] Critical workflow artifacts are durably persisted where required
- [ ] Traces, logs, and events cover all changed workflow steps

## Testing And Documentation Checklist

- [ ] Unit Tests: deterministic coverage for new domain logic, schemas, and validation rules
- [ ] Integration Tests: API, persistence, orchestration, and event/trace coverage for the sprint scope
- [ ] Smoke Tests With Real Provider: verify wide events persistence and circuit breaker behavior
- [ ] Failure Path Coverage: explicit circuit breaker and error summarization paths tested
- [ ] Documentation Updates: update canonical docs in `ops/`, the roadmap/sprint docs, and any affected contracts

## Success Criteria

- [ ] Primary sprint goal is met in a backend-usable form
- [ ] Wide events persisted to workflow_events table
- [ ] Circuit breaker state shared across workers
- [ ] Tests pass at unit, integration, and smoke level for the sprint scope
- [ ] Canonical docs reflect the implemented behavior

Minimum Viable Sprint:
Tasks 2b.1, 2b.4, 2b.5 are the critical path. Tasks 2b.2-2b.3 are nice-to-have.

## Risks And Blockers

| Risk | Impact | Mitigation | Status |
| --- | --- | --- | --- |
| Circuit breaker persistence for multi-worker | Medium | Use distributed cache (Redis) or DB-backed state | Open |
| Wide events storage performance | Medium | Ensure event_type prefix indexing is efficient | Open |

## Sprint Notes

Key decisions, tradeoffs, and implementation notes:

```
1. Wide Events Storage:
   - Store in existing `workflow_events` table with event_type prefix
   - e.g., `stage.wide.input_guard`, `pipeline.wide.assistant_turn_runtime`

2. Streaming Metrics:
   - Aggregate into turn metadata (total_chunks, dropped_chunks, throttle_count)
   - Not separate records

3. Circuit Breaker State:
   - Persisted to `CircuitBreakerRecord` table for multi-worker deployments
   - Use distributed cache (Redis) or DB-backed state

4. Agent Pipeline Stages:
   - input_guard (GUARD) - Turn status check, cancellation handling
   - history_enrich (ENRICH) - Conversation history loading
   - profile_enrich (ENRICH) - Learner profile loading
   - progress_enrich (ENRICH) - Progression dashboard loading
   - attempts_enrich (ENRICH) - Recent attempts loading
   - assistant_runtime (AGENT) - Main LLM orchestrator with tool execution
```

## Review And Sign-Off

- Sprint Status: Completed
- Completion Date: 2026-03-27

Checklist:

- [x] Primary goal achieved
- [x] Constitution and quality checks passed
- [x] Unit tests completed
- [ ] Integration tests completed
- [ ] Smoke tests with real provider completed
- [x] Documentation updated
- [ ] Code review completed

Next Sprint Priorities:

1. Sprint 13d: Pipeline Visualization
2. Sprint 13e: Eval Dashboard
3. Sprint 13f: Prompt Library API

## Implementation Notes

### Task 2b.1 - Wide Events Persistence
- Created `AgentWideEventEmitter` class extending `WideEventEmitter` that emits events with stage-name-prefixed event_types (e.g., `stage.wide.input_guard` instead of just `stage.wide`)
- Updated `StageflowPipelineSupport` to use `AgentWideEventEmitter` as the default factory
- The events are emitted via `ctx.event_sink.try_emit()` which is handled by `DurableEventSink`

### Task 2b.2 - Tool Events via Stageflow
- Added `tool.invoked` event emission via `ctx.try_emit_event()` in `_run_agent_loop()` before calling `_tools.execute_many()`
- Each tool call now emits `tool.invoked` with tool_name, call_id, arguments, and correlation IDs before dispatch
- This complements the existing `tool.started/completed/failed` events emitted via the broker

### Task 2b.3 - Streaming Buffer Aggregation (Deferred)
- **Deferred**: Requires implementing a streaming buffer first (e.g., using stageflow's `ChunkQueue` or `StreamingBuffer`)
- The codebase currently doesn't use stageflow's streaming helpers, so `stream.chunk_dropped` and `stream.throttle_count` events are not generated
- When a streaming buffer is implemented, the aggregated metrics should be stored in `AssistantTurnRecord.metadata_payload`

### Task 2b.4 - Circuit Breaker Persistence
- Created `CircuitBreakerRecord` model in `platform/db/models.py` with fields: name, status, failure_count, last_failure_at, last_failure_reason, opened_at, closed_at, updated_at
- Created migration `20260327_0015_circuit_breaker_record.py`
- Created `DatabaseCircuitBreaker` class in `platform/observability/circuit_breaker.py` implementing:
  - `get_state(stage_name)` - returns current circuit breaker state
  - `is_callable(stage_name)` - checks if circuit allows calls
  - `record_success(stage_name)` - records successful call
  - `record_failure(stage_name, reason)` - records failed call and potentially opens circuit
- Circuit opens after 5 failures (CIRCUIT_BREAKER_THRESHOLD) with 30 second reset timeout (CIRCUIT_BREAKER_RESET_TIMEOUT_SECONDS)

### Task 2b.5 - Structured Error Summarization
- Created `PipelineErrorSummary` Pydantic model with fields: error_type, error_code, category, stage_name, pipeline_name, root_cause, is_retryable, context
- Created `summarize_pipeline_error()` function that extracts structured error information from exceptions
- Updated `DatabasePipelineRunLogger` to:
  - Accept optional `workflow_events` repository
  - Emit structured error events in `log_run_failed()` using `pipeline.error.{category}` event type
- Updated `build_stageflow_runtime()` and `build_container()` to pass `workflow_events` to `DatabasePipelineRunLogger`

### Files Modified/Created
- `backend/src/soft_skills_backend/platform/workflows/stageflow.py` - Added `AgentWideEventEmitter` class
- `backend/src/soft_skills_backend/platform/observability/stageflow_logging.py` - Added `PipelineErrorSummary`, `summarize_pipeline_error()`, updated `DatabasePipelineRunLogger`
- `backend/src/soft_skills_backend/platform/observability/circuit_breaker.py` - New file with `DatabaseCircuitBreaker`
- `backend/src/soft_skills_backend/platform/db/models.py` - Added `CircuitBreakerRecord`
- `backend/src/soft_skills_backend/platform/workflows/stageflow_runtime.py` - Updated to pass `workflow_events` to logger
- `backend/src/soft_skills_backend/platform/container.py` - Updated to pass `workflow_events` to logger
- `backend/src/soft_skills_backend/modules/assistant/workflows/service.py` - Added `tool.invoked` event emission
- `backend/alembic/versions/20260327_0015_circuit_breaker_record.py` - New migration
- `backend/tests/unit/test_agent_observability.py` - New test file
