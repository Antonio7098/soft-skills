# Sprint 13g: User Management API

> Project: SoftSkills
> Scope: Backend and platform execution only. Frontend planning is tracked separately.

## Sprint Overview

- Sprint Name: User Management API
- Sprint Focus: Implement admin user listing, suspension, role management, bulk operations, and activity view APIs
- Depends On: Sprint 12 (Collections Enhancement)

## Relevant Source Docs

- [CONSTITUTION.yml](/home/antonioborgerees/df/soft-skills/ops/CONSTITUTION.yml): lines 1-427
- [ops/mvp-spec/admin-dashboard-readiness.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/admin-dashboard-readiness.md): lines 320-335
- [ops/mvp-spec/foundational/stageflow-guide.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/stageflow-guide.md): lines 1-50
- [ops/mvp-spec/platform/swappable-auth-adapters.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/platform/swappable-auth-adapters.md): full doc - adapter interface design for Firebase/WorkOS/Clerk/native swap

## Sprint Goals

- Primary Goal: Implement admin user management APIs - listing, suspension, role management
- Secondary Goals:
  - Admin action audit trail events (enables Task 1.5)
  - Bulk user operations
  - User activity view

## Scope Checklist

- [ ] Task 5.1: Admin user listing - `GET /admin/users` with pagination, search, filter by role/status
- [ ] Task 5.2: User deactivation/suspension - Status toggle via `DELETE /admin/users/{id}` or status endpoint
- [ ] Task 5.3: Role management - `PUT /admin/users/{id}/role` to promote to admin
- [ ] Task 5.4: Bulk user operations - `POST /admin/users/bulk` for bulk role changes, exports
- [ ] Task 5.5: User activity view - Recent attempts, sessions, logins per user
- [ ] Task 5.6: Admin action audit events - Wire `admin.user.suspended.v1`, `admin.user.role_changed.v1` when above endpoints are implemented
- [ ] Task 5.7: Documentation updates
- [ ] Task 5.8: Add user to org - `POST /admin/users` to create/invite user to organization
- [ ] Task 5.9: Swappable auth provider interface - Refactor `HeaderAuthProvider` into `AuthProvider` protocol with adapter pattern per [swappable-auth-adapters.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/platform/swappable-auth-adapters.md)

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
- [ ] Smoke Tests With Real Provider: verify user management operations
- [ ] Documentation Updates: update canonical docs in `ops/`, the roadmap/sprint docs, and any affected contracts

## Success Criteria

- [ ] Primary sprint goal is met in a backend-usable form
- [ ] Admin user management APIs functional
- [ ] Admin action audit events wired
- [ ] Tests pass at unit, integration, and smoke level for the sprint scope
- [ ] Canonical docs reflect the implemented behavior

Minimum Viable Sprint:
Tasks 5.1-5.3 are the critical path. Tasks 5.4-5.5 are high priority.

## Risks And Blockers

| Risk | Impact | Mitigation | Status |
| --- | --- | --- | --- |
| User data sensitivity | High | Ensure PII is handled according to data classification | Open |

## Sprint Notes

Key decisions, tradeoffs, and implementation notes:

```
1. Existing User Infrastructure:
   - UserAccountRecord, LearnerProfileRecord
   - POST /auth/register, GET/PUT /users/{id}
   - AdminLearnerRelationshipRecord for admin-learner relationships

2. Admin Action Audit Events:
   - admin.user.suspended.v1
   - admin.user.role_changed.v1
   - admin.cohort.created.v1
   - admin.cohort.updated.v1

3. Note: These events require corresponding admin endpoints to be implemented first.

4. Auth Adapter Decisions (see swappable-auth-adapters.md):
   - Token refresh: Frontend/SDK (delegated to provider SDK)
   - Session storage: App-managed for all (SessionRecord table)
   - Org role sync: DB lookup with 30s TTL cache; invalidate on change
   - Migration: AuthIdentityRecord table for provider identity mapping
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

1. Sprint 13h: User/Cohort Analytics
2. Sprint 13i: Policy Layer
3. Frontend admin dashboard integration (separate frontend sprint)
