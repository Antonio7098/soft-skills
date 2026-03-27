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

- [ ] Task 2b.1: Wide events persistence - Persist `stage.wide.*` and `pipeline.wide.*` events to `workflow_events` with event_type prefix
- [ ] Task 2b.2: Tool events via Stageflow - Emit `tool.invoked` via `ctx.emit_event()` before dispatch; already emits `tool.started/completed/failed` via broker
- [ ] Task 2b.3: Streaming buffer aggregation - Aggregate `stream.chunk_dropped`, `stream.throttle_count` into turn metadata (not separate records)
- [ ] Task 2b.4: Circuit breaker persistence - Implement `CircuitBreaker` backed by `CircuitBreakerRecord` for multi-worker deployments
- [ ] Task 2b.5: Structured error summarization - Use `summarize_pipeline_error()` in `DatabasePipelineRunLogger.log_run_failed()` for structured error docs
- [ ] Task 2b.6: Documentation updates

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

- Sprint Status: Not Started
- Completion Date: [Date]

Checklist:

- [ ] Primary goal achieved
- [ ] Constitution and quality checks passed
- [ ] Unit tests completed
- [ ] Integration tests completed
- [ ] Smoke tests with real provider completed
- [ ] Documentation updated
- [ ] Code review completed

Next Sprint Priorities:

1. Sprint 13d: Pipeline Visualization
2. Sprint 13e: Eval Dashboard
3. Sprint 13f: Prompt Library API
