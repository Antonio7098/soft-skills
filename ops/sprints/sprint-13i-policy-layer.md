# Sprint 13i: Policy Layer

> Project: SoftSkills
> Scope: Backend and platform execution only. Frontend planning is tracked separately.

## Sprint Overview

- Sprint Name: Policy Layer
- Sprint Focus: Implement policy data model, CRUD API, rule engine, conditions, versioning, and enforcement middleware
- Depends On: Sprint 13g (User Management API)

## Relevant Source Docs

- [CONSTITUTION.yml](/home/antonioborgerees/df/soft-skills/ops/CONSTITUTION.yml): lines 1-427
- [ops/mvp-spec/admin-dashboard-readiness.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/admin-dashboard-readiness.md): lines 356-373
- [ops/mvp-spec/foundational/stageflow-guide.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/stageflow-guide.md): lines 1-50

## Sprint Goals

- Primary Goal: Implement policy infrastructure - data model, CRUD API, rule engine, conditions, versioning, enforcement
- Secondary Goals:
  - Policy audit trail
  - Policy enforcement middleware

## Scope Checklist

- [ ] Task 7.1: Policy data model - `PolicyRecord`, `PolicyVersionRecord`, `PolicyAuditRecord`
- [ ] Task 7.2: Policy definition API - CRUD endpoints `/admin/policies`
- [ ] Task 7.3: Policy rule engine - Evaluate policies against requests/actions
- [ ] Task 7.4: Policy conditions - Define conditions (user role, cohort, time, etc.)
- [ ] Task 7.5: Policy versioning - Track policy changes with audit trail
- [ ] Task 7.6: Policy enforcement middleware - Apply policies at API gateway level
- [ ] Task 7.7: Documentation updates

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
- [ ] All new models require Alembic migrations; migrations are only path for schema evolution (CL-014)

## Testing And Documentation Checklist

- [ ] Unit Tests: deterministic coverage for new domain logic, schemas, and validation rules
- [ ] Integration Tests: API, persistence, orchestration, and event/trace coverage for the sprint scope
- [ ] Smoke Tests With Real Provider: verify policy evaluation
- [ ] Policy Tests: verify policy evaluation, versioning, enforcement
- [ ] Documentation Updates: update canonical docs in `ops/`, the roadmap/sprint docs, and any affected contracts

## Success Criteria

- [ ] Primary sprint goal is met in a backend-usable form
- [ ] Policy CRUD API functional
- [ ] Policy enforcement working
- [ ] Tests pass at unit, integration, and smoke level for the sprint scope
- [ ] Canonical docs reflect the implemented behavior
- [ ] All new models have Alembic migrations

Minimum Viable Sprint:
Tasks 7.1-7.3 are the critical path. Tasks 7.4-7.6 build on the foundation.

## Risks And Blockers

| Risk | Impact | Mitigation | Status |
| --- | --- | --- | --- |
| Policy layer complexity (rule engine) | High | Design carefully; consider drools-like rule engine vs simple conditions | Open |
| Alembic migration coordination for new policy models | Medium | Plan migration sequence early in sprint | Open |

## Sprint Notes

Key decisions, tradeoffs, and implementation notes:

```
1. Policy Layer Design:
   - PolicyRecord: policy_id, name, description, created_at, updated_at
   - PolicyVersionRecord: version_id, policy_id, version, rules_json, conditions_json, status
   - PolicyAuditRecord: audit_id, policy_id, version_id, action, actor, timestamp, changes_json

2. Existing Policy Infrastructure:
   - ReleaseGateDecisionRecord (evaluation gates only)
   - AdminCollectionVerificationCommand for content verification
   - No dedicated policy module

3. Note: This is the most complex section of the admin dashboard backend. Consider careful design before implementation.
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
- [ ] All Alembic migrations created

Next Sprint Priorities:

1. Frontend admin dashboard integration (separate frontend sprint)
2. Alerting and notifications based on OpenTelemetry data
3. Advanced analytics (predictive, cohort trends)
