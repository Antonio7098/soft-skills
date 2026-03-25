# Sprint 8: Hardening And Release Readiness

> Project: SoftSkills
> Scope: Backend and platform execution only. Frontend planning is tracked separately.

## Sprint Overview

- Sprint Name: Sprint 8: Hardening And Release Readiness
- Sprint Focus: Prove the backend MVP is reliable, replayable, and ready for internal release
- Depends On: Sprint 7

## Relevant Source Docs

- [CONSTITUTION.yml](/home/antonioborgerees/df/soft-skills/ops/CONSTITUTION.yml): lines 176-221, 308-427
- [ops/mvp-spec/README.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/README.md): lines 10-21, 23-45
- [foundational/technical-architecture.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/technical-architecture.md): lines 125-164
- [platform/assessment-and-progression.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/platform/assessment-and-progression.md): lines 105-123
- [operations/observability-and-operations.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/operations/observability-and-operations.md): lines 58-125
- [engines/marking-engine.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/engines/marking-engine.md): lines 146-219
- [foundational/stageflow-guide.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/stageflow-guide.md): lines 534-646

## Sprint Goals

- Primary Goal: Reach a release-quality backend MVP for internal use.
- Secondary Goals:
  - Run full regression coverage across all core backend flows.
  - Prove real-provider smoke coverage for every provider-backed MVP workflow.
  - Align canonical docs and remove non-essential scope before release.

## Scope Checklist

- [ ] Task 1: Run and fix full unit and integration coverage across identity, content, runtime, assessment, progression, recommendation, creator, and admin flows
- [ ] Task 2: Run and harden end-to-end backend smoke flows against the real provider for assessment and generation workflows; exercise the real Stageflow DAGs rather than only direct provider calls
- [ ] Task 3: Verify complete traceability, replayability, version metadata, and migration discipline across critical workflows; check typed-output versions, wide events, provider-call logs, and optional non-prod hardening interceptors
- [ ] Task 4: Review MVP scope and cut non-essential work that does not strengthen the core loop
- [ ] Task 5: Documentation updates for all changed behavior and contracts

## Constitution And Quality Checklist

- [ ] Competency growth remains the product outcome, not activity theater
- [ ] All new external boundaries are typed and schema-validated
- [ ] Fail-fast and fail-loud behavior is preserved with stable error codes
- [ ] Route handlers remain thin; business rules stay out of transport layers
- [ ] Dependency injection and adapter boundaries remain explicit
- [ ] Critical workflow artifacts are durably persisted where required
- [ ] Traces, logs, and events cover all changed workflow steps
- [ ] Prompt, rubric, model, and config versions are preserved where applicable
- [ ] Assessment and progression behavior remains explainable
- [ ] No silent fallback is introduced in scoring, progression, generation, or recommendation paths

## Testing And Documentation Checklist

- [ ] Unit Tests: full deterministic coverage for domain logic, validation, and shared contracts
- [ ] Integration Tests: full API, persistence, orchestration, and observability coverage for MVP backend workflows
- [ ] Smoke Tests With Real Provider: run assessment and content-generation smokes end to end against the real provider from the backend
- [ ] Failure Path Coverage: provider outages, schema breaks, persistence failures, replay issues, and migration problems tested
- [ ] Documentation Updates: update canonical docs in `ops/`, the roadmap/sprint docs, and any affected contracts

## Success Criteria

- [ ] Core backend MVP flows pass unit, integration, and real-provider smoke coverage
- [ ] Critical artifacts remain versioned, persisted, traceable, and replayable
- [ ] Canonical docs accurately describe the shipped backend behavior
- [ ] Remaining scope has been trimmed to protect MVP trustworthiness and release focus

Minimum Viable Sprint:
The backend is reliable enough for internal MVP use even if some non-core polish items are explicitly deferred.

## Risks And Blockers

| Risk | Impact | Mitigation | Status |
| --- | --- | --- | --- |
| Late hardening exposes gaps that should have been caught earlier | High | Treat this sprint as final tightening, not first discovery of core quality gaps | Open |
| Real-provider smoke suite is too thin to prove production-like behavior | High | Ensure every provider-backed core flow has a backend-driven smoke path | Open |

## Sprint Notes

Key decisions, tradeoffs, and implementation notes:

```text
[Notes go here]
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

1. Start internal MVP usage and collect operational feedback.
2. Feed findings into the next roadmap cut before post-MVP expansion.
3. Revisit post-MVP items only after the core loop remains trustworthy in use.
