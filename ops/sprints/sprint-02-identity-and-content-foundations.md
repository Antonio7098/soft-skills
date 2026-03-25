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

- [ ] Task 1: Implement account, auth adapter boundary, profile, goals, and target role models/APIs; use auth interceptors only at request boundaries that are ready for them
- [ ] Task 2: Implement skills, competencies, rubrics, collections, prompt items, scenarios, mock companies, and mock people models; use typed outputs and schema versions for shared catalog payloads where they cross workflow boundaries
- [ ] Task 3: Implement content lifecycle and verification states with invariant checks
- [ ] Task 4: Implement collection browse/filter APIs and private draft authoring APIs; use Stageflow composition for reusable guard/enrichment fragments where useful
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

- [ ] Unit Tests: domain invariants, lifecycle transitions, auth/profile validation, and rubric/content mapping rules
- [ ] Integration Tests: account/profile APIs, content CRUD/filtering APIs, persistence, and event emission
- [ ] Smoke Tests With Real Provider: keep the baseline provider smoke suite green and validate provider wiring after identity/content changes
- [ ] Failure Path Coverage: unauthorized access, invalid content mapping, invalid lifecycle transitions, and bad schema payloads tested
- [ ] Documentation Updates: update canonical docs in `ops/`, the roadmap/sprint docs, and any affected contracts

## Success Criteria

- [ ] Users and learner profiles can be stored and retrieved behind stable auth boundaries
- [ ] Initial taxonomy and rubric model is persisted and versioned
- [ ] Collections and assessable content can be created only when they satisfy mapping rules
- [ ] Backend catalog APIs support valid browsing and draft authoring behavior

Minimum Viable Sprint:
Identity, profile, taxonomy, rubric, and core catalog primitives are available and enforced even if practice runtime is not yet implemented.

## Risks And Blockers

| Risk | Impact | Mitigation | Status |
| --- | --- | --- | --- |
| Content contracts are too loose and allow invalid assessable items | High | Enforce skill/rubric mapping and lifecycle validation at the boundary | Open |
| Auth implementation leaks vendor logic into core services | High | Keep auth behind adapter interfaces and composition-root wiring | Open |

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

1. Add the first end-to-end quick practice runtime.
2. Introduce marking orchestration and validated assessment artifacts.
3. Preserve traceability from prompt delivery through attempt persistence.
