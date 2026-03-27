# Sprint 13e: Eval Dashboard API

> Project: SoftSkills
> Scope: Backend and platform execution only. Frontend planning is tracked separately.

## Sprint Overview

- Sprint Name: Eval Dashboard API
- Sprint Focus: Implement evaluation result dashboard view, historical comparison, benchmarking, and case drill-down APIs
- Depends On: Sprint 12 (Collections Enhancement)

## Relevant Source Docs

- [CONSTITUTION.yml](/home/antonioborgerees/df/soft-skills/ops/CONSTITUTION.yml): lines 1-427
- [ops/mvp-spec/admin-dashboard-readiness.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/admin-dashboard-readiness.md): lines 236-251
- [ops/mvp-spec/foundational/stageflow-guide.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/stageflow-guide.md): lines 1-50

## Sprint Goals

- Primary Goal: Implement eval dashboard backend APIs - aggregated views, historical comparison, benchmarking, case drill-down
- Secondary Goals:
  - Provider model performance tracking
  - Evaluation case inspection

## Scope Checklist

- [ ] Task 3.1: Evaluation result dashboard view - Aggregate pass/fail rates, latency percentiles, error breakdown
- [ ] Task 3.2: Historical comparison - Compare evaluation runs over time
- [ ] Task 3.3: Benchmarking dashboard - Track provider model performance
- [ ] Task 3.4: Evaluation case drill-down - Individual case result inspection
- [ ] Task 3.5: Documentation updates

## Constitution And Quality Checklist

- [ ] Competency growth remains the product outcome, not activity theater
- [ ] All new external boundaries are typed and schema-validated
- [ ] Fail-fast and fail-loud behavior is preserved with stable error codes
- [ ] Route handlers remain thin; business rules stay out of transport layers
- [ ] Dependency injection and adapter boundaries remain explicit
- [ ] Critical workflow artifacts are durably persisted where required
- [ ] Traces, logs, and events cover all changed workflow steps
- [ ] All admin API endpoints follow explicit schemas with Pydantic request/response models (CL-013)
- [ ] All admin endpoints delegate to domain/application services; no business logic in routes (CL-013)

## Testing And Documentation Checklist

- [ ] Unit Tests: deterministic coverage for new domain logic, schemas, and validation rules
- [ ] Integration Tests: API, persistence, orchestration, and event/trace coverage for the sprint scope
- [ ] Smoke Tests With Real Provider: verify eval runs and benchmark tracking
- [ ] Documentation Updates: update canonical docs in `ops/`, the roadmap/sprint docs, and any affected contracts

## Success Criteria

- [ ] Primary sprint goal is met in a backend-usable form
- [ ] Eval dashboard APIs functional
- [ ] Tests pass at unit, integration, and smoke level for the sprint scope
- [ ] Canonical docs reflect the implemented behavior

Minimum Viable Sprint:
Tasks 3.1 and 3.4 are the critical path.

## Risks And Blockers

| Risk | Impact | Mitigation | Status |
| --- | --- | --- | --- |
| Benchmarking data volume | Medium | Implement aggregation and retention policy | Open |

## Sprint Notes

Key decisions, tradeoffs, and implementation notes:

```
1. Existing Evaluation Infrastructure:
   - EvaluationSuiteRecord, EvaluationRunRecord, EvaluationCaseResultRecord
   - Endpoints at `/admin/evaluations/suites` and `/admin/evaluations/runs`
   - EvaluationService, MarkingBenchmarkRunner

2. Evaluation Event Flow:
   - evaluation.run.started.v1
   - evaluation.run.completed.v1
   - evaluation.run.failed.v1
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

1. Sprint 13f: Prompt Library API
2. Sprint 13g: User Management API
3. Sprint 13h: User/Cohort Analytics
