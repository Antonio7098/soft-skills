# Sprint 14: Admin Super Agent

> Project: SoftSkills
> Scope: Backend and platform execution only. Frontend planning is tracked separately.

## Sprint Overview

- Sprint Name: Admin Super Agent
- Sprint Focus: Implement a read-only admin investigation agent powered by schema-aware SQL over org-scoped, PII-safe views
- Depends On: Sprint 13h (User Cohort Analytics) and completion of `ops/mvp-spec/TODO/human-approval-workflows.md`

## Relevant Source Docs

- [CONSTITUTION.yml](/home/antonioborgerees/df/soft-skills/ops/CONSTITUTION.yml): lines 1-253
- [ops/mvp-spec/README.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/README.md): lines 10-24, 41-50
- [ops/mvp-spec/foundational/stageflow-guide.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/stageflow-guide.md): lines 368-379, 498-532
- [ops/mvp-spec/operations/admin-dashboard-readiness.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/operations/admin-dashboard-readiness.md): lines 125-152
- [ops/mvp-spec/TODO/admin-super-agent.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/TODO/admin-super-agent.md): lines 5-278
- [ops/mvp-spec/TODO/human-approval-workflows.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/TODO/human-approval-workflows.md): lines 21-67, 109-157, 193-202

## Sprint Goals

- Primary Goal: Deliver a backend-usable admin chat endpoint that answers investigative questions through one constrained read-only SQL tool over admin-safe views
- Secondary Goals:
  - Enforce organisation scoping, allowlisted views, and PII-safe result handling below the LLM boundary
  - Reuse Stageflow agent patterns and approval-ready execution infrastructure without introducing write actions
  - Emit enough audit and trace data to explain every agent query and denial

## Scope Checklist

- [ ] Task 14.1: Add `admin_agent_*` SQL views with allowlisted columns, org scoping hooks, and PII-safe payload shaping
- [ ] Task 14.2: Implement schema registry/context for allowed views, columns, joins, field descriptions, and example query patterns
- [ ] Task 14.3: Add typed request/response contracts for `query_admin_data` and `POST /admin-agent/chat`
- [ ] Task 14.4: Implement SQL guardrails for `SELECT`-only validation, approved target enforcement, bounded limits, and denial errors
- [ ] Task 14.5: Implement scoped SQL executor with org predicate injection, timeout/row caps, auditing, and defensive output redaction
- [ ] Task 14.6: Implement Stageflow admin-agent pipeline with guard, enrich, planning, query, and respond stages
- [ ] Task 14.7: Integrate with approval-capable tooling infrastructure from `human-approval-workflows.md`, keeping the read-only SQL tool auto-allowed for MVP
- [ ] Task 14.8: Expose `POST /admin-agent/chat` behind admin auth and organisation context
- [ ] Task 14.9: Emit `admin.agent.*`, tool, approval-state, and query audit events sufficient for replay and debugging
- [ ] Task 14.10: Documentation updates for canonical spec, contracts, and sprint sequencing

## Constitution And Quality Checklist

- [ ] Competency growth remains the product outcome, not activity theater
- [ ] All new external boundaries are typed and schema-validated
- [ ] Fail-fast and fail-loud behavior is preserved with stable error codes
- [ ] Route handlers remain thin; business rules stay out of transport layers
- [ ] Dependency injection and adapter boundaries remain explicit
- [ ] Critical workflow artifacts are durably persisted where required
- [ ] Traces, logs, and events cover all changed workflow steps
- [ ] Prompt, model, and config versions are preserved for admin-agent runs where applicable
- [ ] No silent fallback is introduced in SQL validation, scoping, redaction, or tool execution
- [ ] The agent can read only from admin-safe views and never from raw base tables

## Testing And Documentation Checklist

- [ ] Unit Tests: deterministic coverage for SQL validation, schema registry, redaction rules, pseudonymization, and request/response schemas
- [ ] Integration Tests: API, persistence, Stageflow pipeline, audit events, and org-scoped query execution coverage
- [ ] Smoke Tests With Real Provider: add and run an `admin-agent` smoke that performs representative read-only investigations against seeded safe views
- [ ] Failure Path Coverage: explicit tests for invalid SQL, disallowed views/columns, missing org scope, timeout/row-limit failures, provider failures, and redaction/approval configuration errors
- [ ] Documentation Updates: update canonical docs in `ops/`, the roadmap/sprint docs, and any affected contracts

## Success Criteria

- [ ] Primary sprint goal is met in a backend-usable form
- [ ] Admins can query investigation-safe data via `POST /admin-agent/chat` using the single read-only SQL tool
- [ ] Queries are restricted to approved admin-safe views with enforced org scoping and bounded execution
- [ ] No raw PII or disallowed content reaches the external LLM provider
- [ ] Tests pass at unit, integration, and smoke level for the sprint scope
- [ ] Canonical docs reflect the implemented behavior and security boundary
- [ ] Observability artifacts are sufficient to explain every successful and denied agent query

Minimum Viable Sprint:
Tasks 14.1, 14.3, 14.4, 14.5, 14.6, and 14.8 are the critical path. Approval infrastructure is assumed to exist already; this sprint only needs to consume it safely for a read-only auto-allowed tool.

## Risks And Blockers

| Risk | Impact | Mitigation | Status |
| --- | --- | --- | --- |
| SQL validator misses a bypass and exposes raw tables or unsafe clauses | High | Parse queries structurally, allowlist views/columns, reject multi-statement/comment tricks, and test denial paths aggressively | Open |
| PII leakage through payload fragments or error messages | High | Prefer pre-redacted DB views, run a second application-layer backstop, and keep error contracts sanitized | Open |
| Ad hoc investigative queries become too slow on large event tables | Medium | Use bounded windows, indexes, hard row/time caps, and shape views for common investigations | Open |
| Approval workflow dependency lands with different executor assumptions | Medium | Build against the finalized approval abstraction and keep the admin agent limited to the read-only auto-allowed path for MVP | Open |

## Sprint Notes

Key decisions, tradeoffs, and implementation notes:

```text
1. This sprint intentionally does not expose a wide catalog of bespoke admin tools.
   The MVP read surface is one typed SQL tool plus schema context.

2. The security boundary is the query layer and the admin-safe views, not the prompt.
   The model should never be able to query raw base tables.

3. Human approval is a prerequisite for the broader tool framework, but the MVP
   admin agent remains read-only. The single SQL tool should be marked safe to
   auto-allow under the approval system once its validator and view restrictions
   are in place.

4. PromptSecurityPolicy still matters because tool-returned content can flow back
   into later model turns inside the agent loop.

5. Audit artifacts should record query text, normalized parameters, denial reasons,
   row counts, timing, prompt/model metadata, and correlation identifiers.

6. Future write actions are explicitly out of scope here. If they are ever added,
   they should be separate typed tools with approval required by default.
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

1. Frontend admin investigation UI for `POST /admin-agent/chat`
2. Saved/admin-curated investigation queries and reusable reports
3. Approval-gated write tools only after the read-only agent is stable and audited
