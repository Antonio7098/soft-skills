# Sprint 2: Identity And Content Foundations

> Project: SoftSkills
> Scope: Backend and platform execution only. Frontend planning is tracked separately.

## Sprint Overview

- Sprint Name: Sprint 2: Identity And Content Foundations
- Sprint Focus: Introduce users, learner profiles, taxonomy, rubrics, collections, prompts, scenarios, and content validation
- Depends On: Sprint 1

## Relevant Source Docs

- [CONSTITUTION.yml](/home/antonioborgerees/df/soft-skills/ops/CONSTITUTION.yml): lines 83-157, 291-323, 394-407
- [foundational/product-spec.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/product-spec.md): lines 61-76, 133-175
- [foundational/domain-model.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/domain-model.md): lines 100-193
- [operations/content-system.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/operations/content-system.md): lines 20-85
- [foundational/technical-architecture.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/technical-architecture.md): lines 69-94
- [foundational/stageflow-guide.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/stageflow-guide.md): lines 291-349, 432-446, 504-513, 586-590

## Sprint Goals

- Primary Goal: Make the platform capable of holding valid users and valid assessable content.
- Secondary Goals:
  - Implement standard user/admin identity and learner profile semantics.
  - Seed and persist the initial skill, competency, and rubric model.
  - Support collection and content authoring for private draft use.

## Scope Checklist

- [x] Task 1: Implement account, auth adapter boundary, profile, goals, and target role models/APIs; use auth interceptors only at request boundaries that are ready for them
- [x] Task 2: Implement skills, competencies, rubrics, collections, prompt items, scenarios, mock companies, and mock people models; use typed outputs and schema versions for shared catalog payloads where they cross workflow boundaries
- [x] Task 3: Implement content lifecycle and verification states with invariant checks
- [x] Task 4: Implement collection browse/filter APIs and private draft authoring APIs; use Stageflow composition for reusable guard/enrichment fragments where useful
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

- [x] Unit Tests: domain invariants, lifecycle transitions, auth/profile validation, and rubric/content mapping rules
- [x] Integration Tests: account/profile APIs, content CRUD/filtering APIs, persistence, and event emission
- [ ] Smoke Tests With Real Provider: keep the baseline provider smoke suite green and validate provider wiring after identity/content changes
- [x] Failure Path Coverage: unauthorized access, invalid content mapping, invalid lifecycle transitions, and bad schema payloads tested
- [x] Documentation Updates: update canonical docs in `ops/`, the roadmap/sprint docs, and any affected contracts

## Success Criteria

- [x] Users and learner profiles can be stored and retrieved behind stable auth boundaries
- [x] Initial taxonomy and rubric model is persisted and versioned
- [x] Collections and assessable content can be created only when they satisfy mapping rules
- [x] Backend catalog APIs support valid browsing and draft authoring behavior

Minimum Viable Sprint:
Identity, profile, taxonomy, rubric, and core catalog primitives are available and enforced even if practice runtime is not yet implemented.

## Risks And Blockers

| Risk | Impact | Mitigation | Status |
| --- | --- | --- | --- |
| Content contracts are too loose and allow invalid assessable items | High | Enforce skill/rubric mapping and lifecycle validation at the boundary | Mitigated |
| Auth implementation leaks vendor logic into core services | High | Keep auth behind adapter interfaces and composition-root wiring | Mitigated |
| Auth is still an internal header-based adapter rather than an external provider integration | Medium | Keep the provider boundary explicit and swap the adapter in a later sprint without changing route or service contracts | Open |
| Real-provider smoke coverage was intentionally deferred | Medium | Preserve the harness and run it before provider-backed business flows expand further | Open |

## Sprint Notes

Key decisions, tradeoffs, and implementation notes:

```text
- Created a backend venv at backend/.venv, installed the backend package in editable mode, and verified Stageflow imports plus default interceptor resolution inside that venv.
- Implemented a request-bound auth adapter, account registration, profile retrieval/update, and stable actor resolution from headers without leaking auth logic into domain services.
- Added persisted user, profile, taxonomy, rubric, collection, prompt item, scenario, mock company, and mock person models plus an Alembic migration for the new tables.
- Added catalog bootstrap for the frozen Sprint 0 taxonomy and rubric set and exposed it behind an admin-only API.
- Implemented collection draft authoring, browse/filter, prompt/scenario creation, lifecycle transitions, and verification-state rules with explicit invariant checks.
- Added observability events for user registration, profile updates, taxonomy bootstrap, collection creation, prompt creation, scenario creation, and lifecycle changes.
- Stageflow did not need to orchestrate these CRUD-heavy flows yet; the verified runtime boundary remains available for later pipeline-oriented work.
- Real-provider smoke execution was deferred by explicit user instruction and remains open in the sprint checklist.
```

## Review And Sign-Off

- Sprint Status: Partially Completed
- Completion Date: 2026-03-25

Checklist:

- [x] Primary goal achieved
- [x] Constitution and quality checks passed
- [x] Unit tests completed
- [x] Integration tests completed
- [ ] Smoke tests with real provider completed
- [x] Documentation updated
- [ ] Code review completed

Next Sprint Priorities:

1. Add the first end-to-end quick practice runtime.
2. Introduce marking orchestration and validated assessment artifacts.
3. Preserve traceability from prompt delivery through attempt persistence.
