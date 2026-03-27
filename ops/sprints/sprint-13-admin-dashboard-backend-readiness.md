# Sprint 13: Admin Dashboard Backend Readiness

> Project: SoftSkills
> Scope: Backend and platform execution only. Frontend planning is tracked separately.

## Sprint Overview

- Sprint Name: Admin Dashboard Backend Readiness
- Sprint Focus: Implement foundational admin dashboard backend capabilities - event logging improvements, typed error taxonomy, and user management API
- Depends On: Sprint 12 (Collections Enhancement)

## Relevant Source Docs

- [CONSTITUTION.yml](/home/antonioborgerees/df/soft-skills/ops/CONSTITUTION.yml): lines 1-427
- [ops/mvp-spec/admin-dashboard-readiness.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/admin-dashboard-readiness.md): lines 1-531
- [ops/mvp-spec/foundational/stageflow-guide.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/stageflow-guide.md): lines 1-50
- [backend/src/soft_skills_backend/shared/errors.py](/home/antonioborgerees/df/soft-skills/backend/src/soft_skills_backend/shared/errors.py): Error taxonomy implementation

## Sprint Goals

- Primary Goal: Implement comprehensive event logging infrastructure for admin dashboard visibility, including response delta aggregation, HTTP audit logging, auth events, and typed error events
- Secondary Goals:
  - Implement admin user management API (listing, suspension, role management)
  - Wire up wide events persistence via Stageflow
  - Enrich provider call records with token counts

## Scope Checklist

### Event Logging Improvements (Section 1)

- [ ] Task 1: Response delta aggregation - Aggregate `response.delta` events into single `response.completed` record with full content, token counts, latency; emit deltas only to realtime broker
- [ ] Task 2: HTTP request audit logging - Add `http.request.received.v1` and `http.request.completed.v1` events with method, path, query params, user agent, IP, response status, latency; field-level PII scrubbing
- [ ] Task 3: Auth event logging - Add `auth.login.success.v1`, `auth.login.failed.v1`, `auth.token_refresh.v1`, `auth.access_denied.v1`
- [ ] Task 4: Typed error events - Replace generic `workflow.failed.v1` with typed events: `error.validation.v1`, `error.authentication.v1`, `error.authorization.v1`, `error.not_found.v1`, `error.rate_limited.v1`
- [ ] Task 5: Provider call enrichment - Add token counts (prompt/completion/total), model version, finish reason to `ProviderCallRecord.metrics`
- [ ] Task 6: Prompt render events - Add `prompt.rendered.v1` tracking prompt ID, version, template name, latency

### User Management API (Section 5)

- [ ] Task 7: Admin user listing - `GET /admin/users` with pagination, search, filter by role/status
- [ ] Task 8: User deactivation/suspension - Status toggle via `DELETE /admin/users/{id}` or status endpoint
- [ ] Task 9: Role management - `PUT /admin/users/{id}/role` to promote to admin

### Agent Observability (Section 2b)

- [ ] Task 10: Wide events persistence - Persist `stage.wide.*` and `pipeline.wide.*` events to `workflow_events` with event_type prefix

### Documentation

- [ ] Task 11: Documentation updates for all changed behavior and contracts

## Constitution And Quality Checklist

- [ ] Competency growth remains the product outcome, not activity theater
- [ ] All new external boundaries are typed and schema-validated
- [ ] Fail-fast and fail-loud behavior is preserved with stable error codes from existing taxonomy (CL-006)
- [ ] Route handlers remain thin; business rules stay out of transport layers
- [ ] Dependency injection and adapter boundaries remain explicit
- [ ] Critical workflow artifacts are durably persisted where required
- [ ] Traces, logs, and events cover all changed workflow steps
- [ ] Prompt, rubric, model, and config versions are preserved where applicable
- [ ] Assessment and progression behavior remains explainable
- [ ] No silent fallback is introduced in scoring, progression, generation, or recommendation paths
- [ ] All events emit required correlation identifiers: `request_id`, `user_id`, `session_id`, `attempt_id`, `workflow_id`, `prompt_version`, `error_code` (CL-007)
- [ ] Every LLM artifact includes `prompt_version`, `model_slug`, `provider` in `ProviderCallRecord.metrics` (CL-008)
- [ ] LLM validation failures raise `StructuredOutputRejectionError` (hard stop, not silent) (CL-008)
- [ ] Error codes attached to all emitted failures from existing taxonomy (CL-006)
- [ ] All new models require Alembic migrations; migrations are only path for schema evolution (CL-014)
- [ ] Data classification distinguishes transactional domain data from observability/event data (CL-014)

## Testing And Documentation Checklist

- [ ] Unit Tests: deterministic coverage for new domain logic, schemas, and validation rules
- [ ] Integration Tests: API, persistence, orchestration, and event/trace coverage for the sprint scope
- [ ] Smoke Tests With Real Provider: update and run backend smoke flows for provider-backed behavior; if no new provider flow is added, the baseline suite must still pass
- [ ] Failure Path Coverage: explicit validation, provider, orchestration, and persistence failure paths tested
- [ ] Error Taxonomy Tests: verify correct error codes and categories are raised
- [ ] Documentation Updates: update canonical docs in `ops/`, the roadmap/sprint docs, and any affected contracts

## Success Criteria

- [ ] Primary sprint goal is met in a backend-usable form
- [ ] Tests pass at unit, integration, and smoke level for the sprint scope
- [ ] Canonical docs reflect the implemented behavior
- [ ] Observability artifacts are sufficient to debug the changed workflows

Minimum Viable Sprint:
Event logging improvements (Tasks 1-6) are the critical path. User management API and wide events persistence are secondary but should be completed. If time permits, partial user management is acceptable but event logging must be fully implemented.

## Risks And Blockers

| Risk | Impact | Mitigation | Status |
| --- | --- | --- | --- |
| Response delta aggregation requires changes to streaming buffer architecture | High | Design carefully; ensure realtime broker still receives deltas while DB gets aggregated record | Open |
| PII scrubbing complexity for HTTP audit logging | Medium | Start with conservative field-level redaction; iterate | Open |
| Alembic migration coordination for new event models | Low | Plan migration sequence early in sprint | Open |

## Sprint Notes

Key decisions, tradeoffs, and implementation notes:

```
1. Response Delta Aggregation Design:
   - Collect chunks in memory during streaming
   - On response.completed, emit single aggregated record with:
     - Full content (truncated if > 64KB)
     - token_count_prompt, token_count_completion, token_count_total
     - latency_ms
     - chunk_count
   - Realtime broker still receives per-chunk deltas for streaming UX

2. HTTP Audit Events:
   - http.request.received.v1: method, path, query_params (sanitized), user_agent, client_ip
   - http.request.completed.v1: status_code, latency_ms, error_code (if applicable)
   - Field-level PII: client_ip stored but anonymized after 90 days; user_agent truncated

3. Error Event Types:
   - error.validation.v1: SS-VALIDATION-* codes
   - error.authentication.v1: SS-AUTH-* codes
   - error.authorization.v1: SS-AUTH-* codes (access denied)
   - error.not_found.v1: SS-DOMAIN-* codes
   - error.rate_limited.v1: SS-ORCHESTRATION-* codes

4. Provider Call Metrics Schema:
   metrics JSON: {
     "latency_ms": int,
     "prompt_tokens": int | null,
     "completion_tokens": int | null,
     "total_tokens": int | null,
     "finish_reason": str | null,
     "model_version": str | null
   }
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

1. Monitoring/Telemetry - OpenTelemetry integration with OTLP exporter
2. Prompt Library API - Admin CRUD for prompts
3. Pipeline Visualization - DAG definitions and execution traces
4. User/Cohort Analytics - Dashboard API
