# Sprint 7: Admin Verification And Cohort Visibility

> Project: SoftSkills
> Scope: Backend and platform execution only. Frontend planning is tracked separately.

## Sprint Overview

- Sprint Name: Sprint 7: Admin Verification And Cohort Visibility
- Sprint Focus: Add the minimum operational and educational controls required for a credible MVP
- Depends On: Sprint 6

## Relevant Source Docs

- [CONSTITUTION.yml](/home/antonioborgerees/df/soft-skills/ops/CONSTITUTION.yml): lines 159-205, 291-323, 340-375
- [foundational/product-spec.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/product-spec.md): lines 120-175
- [operations/content-system.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/operations/content-system.md): lines 50-115
- [operations/observability-and-operations.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/operations/observability-and-operations.md): lines 9-125
- [platform/assessment-and-progression.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/platform/assessment-and-progression.md): lines 44-117
- [foundational/stageflow-guide.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/stageflow-guide.md): lines 206-279, 392-403, 618-622

## Sprint Goals

- Primary Goal: Admins can verify content, inspect learner/cohort performance, and audit critical backend behavior.
- Secondary Goals:
  - Implement verification workflow for elevated content trust.
  - Expose learner and cohort progress/usage views.
  - Strengthen replay and audit support for assessment disputes and operational debugging.

## Scope Checklist

- [ ] Task 1: Implement admin verification workflow and status transitions for user-created collections
- [ ] Task 2: Implement learner-level and cohort-level analytics APIs for progress, weak skills, and usage trends; lean on pipeline run logs, provider-call logs, and wide events for audit-friendly aggregation
- [ ] Task 3: Enforce visibility boundaries around learner attempt and assessment data
- [ ] Task 4: Implement replay/audit access to assessment-critical traces and artifacts; preserve Stageflow correlation IDs and trace lineage in admin-facing diagnostics
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

- [ ] Unit Tests: verification rules, access-control rules, analytics aggregation helpers, and audit query guards
- [ ] Integration Tests: admin APIs, verification transitions, cohort analytics, replay endpoints, and observability query behavior
- [ ] Smoke Tests With Real Provider: run the existing backend real-provider smoke suite and confirm no regressions in assessment/generation workflows
- [ ] Failure Path Coverage: forbidden access, invalid verification transitions, incomplete trace artifacts, and broken analytics inputs tested
- [ ] Documentation Updates: update canonical docs in `ops/`, the roadmap/sprint docs, and any affected contracts

## Success Criteria

- [ ] Admins can verify collections and elevate trust status through explicit backend workflows
- [ ] Learner and cohort analytics are available from versioned, explainable backend data
- [ ] Replay and audit paths exist for critical assessment-relevant workflows
- [ ] Existing provider-backed smoke flows still pass after admin and analytics changes

Minimum Viable Sprint:
Admin verification and core analytics work for the main MVP entities even if deeper cohort tooling remains limited.

## Risks And Blockers

| Risk | Impact | Mitigation | Status |
| --- | --- | --- | --- |
| Analytics expose more detail than the MVP trust model should allow | High | Keep access boundaries explicit and integration-tested | Open |
| Verification workflow becomes a manual exception path rather than a real state machine | Medium | Model verification states and transitions explicitly in the domain | Open |

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

1. Run full backend regression and release-hardening work.
2. Close remaining traceability and documentation gaps.
3. Cut non-essential scope before release.
