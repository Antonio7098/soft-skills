# Sprint 13h: User/Cohort Analytics

> Project: SoftSkills
> Scope: Backend and platform execution only. Frontend planning is tracked separately.

## Sprint Overview

- Sprint Name: User/Cohort Analytics
- Sprint Focus: Implement analytics dashboard API, time-range selection, export functionality, cohort comparison, and drill-down
- Depends On: Sprint 13g (User Management API)

## Relevant Source Docs

- [CONSTITUTION.yml](/home/antonioborgerees/df/soft-skills/ops/CONSTITUTION.yml): lines 1-427
- [ops/mvp-spec/admin-dashboard-readiness.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/admin-dashboard-readiness.md): lines 338-353
- [ops/mvp-spec/foundational/stageflow-guide.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/stageflow-guide.md): lines 1-50

## Sprint Goals

- Primary Goal: Implement comprehensive analytics APIs - dashboard overview, cohort comparison, drill-down
- Secondary Goals:
  - Time-range selection
  - CSV/JSON export functionality

## Scope Checklist

- [x] Task 6.1: Analytics dashboard API - `GET /admin/analytics/overview` aggregated view
- [x] Task 6.2: Time-range selection - Add `from`/`to` params to existing queries
- [x] Task 6.3: Export functionality - CSV/JSON export of analytics data
- [x] Task 6.4: Cohort comparison - Side-by-side cohort performance
- [x] Task 6.5: Drill-down to attempts - Link analytics to individual attempt details
- [x] Task 6.6: Documentation updates

## Constitution And Quality Checklist

- [x] Competency growth remains the product outcome, not activity theater
- [x] All new external boundaries are typed and schema-validated
- [x] Fail-fast and fail-loud behavior is preserved with stable error codes
- [x] Route handlers remain thin; business rules stay out of transport layers
- [x] Dependency injection and adapter boundaries remain explicit
- [x] Critical workflow artifacts are durably persisted where required
- [x] Traces, logs, and events cover all changed workflow steps
- [x] All admin API endpoints follow explicit schemas with Pydantic request/response models (CL-013)
- [x] All admin endpoints delegate to domain/application services; no business logic in routes (CL-013)

## Testing And Documentation Checklist

- [x] Unit Tests: deterministic coverage for new domain logic, schemas, and validation rules
- [x] Integration Tests: API, persistence, orchestration, and event/trace coverage for the sprint scope
- [x] Smoke Tests With Real Provider: verify analytics queries
- [x] Documentation Updates: update canonical docs in `ops/`, the roadmap/sprint docs, and any affected contracts

## Success Criteria

- [x] Primary sprint goal is met in a backend-usable form
- [x] Analytics dashboard API functional
- [x] Tests pass at unit, integration, and smoke level for the sprint scope
- [x] Canonical docs reflect the implemented behavior

Minimum Viable Sprint:
Tasks 6.1 and 6.2 are the critical path.

## Risks And Blockers

| Risk | Impact | Mitigation | Status |
| --- | --- | --- | --- |
| Analytics query performance | Medium | Index optimization and query caching | Open |

## Sprint Notes

Key decisions, tradeoffs, and implementation notes:

```
1. Existing Analytics Infrastructure:
   - LearnerAnalyticsView, CohortAnalyticsView
   - Usage trends, skill clusters, skill averages, provider usage summary
   - AdminAnalyticsRepository with get_learner_analytics(), get_cohort_analytics()

2. Note: Cohort analytics depends on user management (Section 5) being implemented first.
```

## Review And Sign-Off

- Sprint Status: Completed
- Completion Date: 2026-03-28

Checklist:

- [x] Primary goal achieved
- [x] Constitution and quality checks passed
- [x] Unit tests completed
- [x] Integration tests completed
- [x] Smoke tests with real provider completed
- [x] Documentation updated
- [x] Code review completed

Next Sprint Priorities:

1. Sprint 13i: Policy Layer
2. Frontend admin dashboard integration (separate frontend sprint)
3. Alerting and notifications based on OpenTelemetry data
