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

- [x] Task 1: Implement admin verification workflow and status transitions for user-created collections
- [x] Task 2: Implement learner-level and cohort-level analytics APIs for progress, weak skills, and usage trends; lean on pipeline run logs, provider-call logs, and wide events for audit-friendly aggregation
- [x] Task 3: Enforce visibility boundaries around learner attempt and assessment data
- [x] Task 4: Implement replay/audit access to assessment-critical traces and artifacts; preserve Stageflow correlation IDs and trace lineage in admin-facing diagnostics
- [x] Task 5: Documentation updates for all changed behavior and contracts

## Constitution And Quality Checklist

- [x] Competency growth remains the product outcome, not activity theater
- [x] All new external boundaries are typed and schema-validated
- [x] Fail-fast and fail-loud behavior is preserved with stable error codes
- [x] Route handlers remain thin; business rules stay out of transport layers
- [x] Dependency injection and adapter boundaries remain explicit
- [x] Critical workflow artifacts are durably persisted where required
- [x] Traces, logs, and events cover all changed workflow steps
- [x] Prompt, rubric, model, and config versions are preserved where applicable
- [x] Assessment and progression behavior remains explainable
- [x] No silent fallback is introduced in scoring, progression, generation, or recommendation paths

## Testing And Documentation Checklist

- [x] Unit Tests: verification rules, access-control rules, analytics aggregation helpers, and audit query guards
- [x] Integration Tests: admin APIs, verification transitions, cohort analytics, replay endpoints, and observability query behavior
- [x] Smoke Tests With Real Provider: passed on 2026-03-26 via `PYTHONPATH=src python -m soft_skills_backend.smoke`
- [x] Failure Path Coverage: forbidden access, invalid verification transitions, incomplete trace artifacts, and broken analytics inputs tested
- [x] Documentation Updates: update canonical docs in `ops/`, the roadmap/sprint docs, and any affected contracts

## Success Criteria

- [x] Admins can verify collections and elevate trust status through explicit backend workflows
- [x] Learner and cohort analytics are available from versioned, explainable backend data
- [x] Replay and audit paths exist for critical assessment-relevant workflows
- [x] Existing provider-backed smoke flows still pass after admin and analytics changes

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
- Added explicit admin endpoints under /api/admin for collection verification,
  verification queue inspection, learner analytics, cohort analytics,
  relationship management, and relationship-aware attempt audit/replay.
- Persisted verification history in collection_verification_reviews so
  verification transitions remain queryable and audit-friendly.
- Tightened learner attempt visibility: learner-facing attempt read/submit flows
  now require the owning learner; admin diagnostics use the new redacted audit
  contract instead of the learner API.
- Added explicit admin-to-learner relationship grants so full attempt content is
  only exposed through admin audit when an active manager/educator/coach
  relationship exists.
- Learner and cohort analytics aggregate durable practice/progression data and
  observability artifacts from workflow_events, pipeline_runs, and provider_calls.
- Full backend automated suite passed on 2026-03-26 via
  `PYTHONPATH=src pytest tests -q` with result `47 passed, 1 skipped`.
- Real-provider smoke passed on 2026-03-26 via
  `PYTHONPATH=src python -m soft_skills_backend.smoke` against the configured
  OpenRouter-backed model after increasing smoke timeout budgets.
```

## Review And Sign-Off

- Sprint Status: Completed
- Completion Date: 2026-03-26

Checklist:

- [x] Primary goal achieved
- [x] Constitution and quality checks passed
- [x] Unit tests completed
- [x] Integration tests completed
- [x] Smoke tests with real provider completed
- [x] Documentation updated
- [x] Code review completed

Next Sprint Priorities:

1. Run full backend regression and release-hardening work.
2. Monitor OpenRouter smoke latency and decide whether the smoke model should move off the current free-tier route before release.
3. Close remaining release documentation and operational checklists.
