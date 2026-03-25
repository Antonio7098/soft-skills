# Sprint Template: [Sprint Name]

> Project: SoftSkills
> Scope: Backend and platform execution only. Frontend planning is tracked separately.

## Sprint Overview

- Sprint Name: [Insert sprint name]
- Sprint Focus: [Primary backend outcome for this sprint]
- Depends On: [Earlier sprint outputs or "None"]

## Relevant Source Docs

- [CONSTITUTION.yml](/home/antonioborgerees/df/soft-skills/ops/CONSTITUTION.yml): lines [x-y]
- [ops/mvp-spec/README.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/README.md): lines [x-y]
- [foundational/stageflow-guide.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/stageflow-guide.md): lines [x-y]
- [Add sprint-specific canonical spec files here]: lines [x-y]

## Sprint Goals

- Primary Goal: [Clear end-of-sprint backend outcome]
- Secondary Goals:
  - [Secondary goal 1]
  - [Secondary goal 2]
  - [Secondary goal 3]

## Scope Checklist

- [ ] Task 1: [Major deliverable]
- [ ] Task 2: [Major deliverable]
- [ ] Task 3: [Major deliverable]
- [ ] Task 4: [Major deliverable]
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

- [ ] Unit Tests: deterministic coverage for new domain logic, schemas, and validation rules
- [ ] Integration Tests: API, persistence, orchestration, and event/trace coverage for the sprint scope
- [ ] Smoke Tests With Real Provider: update and run backend smoke flows for provider-backed behavior; if no new provider flow is added, the baseline suite must still pass
- [ ] Failure Path Coverage: explicit validation, provider, orchestration, and persistence failure paths tested
- [ ] Documentation Updates: update canonical docs in `ops/`, the roadmap/sprint docs, and any affected contracts

## Success Criteria

- [ ] Primary sprint goal is met in a backend-usable form
- [ ] Tests pass at unit, integration, and smoke level for the sprint scope
- [ ] Canonical docs reflect the implemented behavior
- [ ] Observability artifacts are sufficient to debug the changed workflows

Minimum Viable Sprint:
[Define what partial completion is still acceptable without corrupting roadmap sequencing]

## Risks And Blockers

| Risk | Impact | Mitigation | Status |
| --- | --- | --- | --- |
| [Risk 1] | [High/Med/Low] | [Mitigation] | [Open/Mitigated/Closed] |
| [Risk 2] | [High/Med/Low] | [Mitigation] | [Open/Mitigated/Closed] |

## Sprint Notes

Key decisions, tradeoffs, and implementation notes:

```text
[Notes go here]
```

## Review And Sign-Off

- Sprint Status: [Not Started / In Progress / Completed / Blocked]
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

1. [Priority 1]
2. [Priority 2]
3. [Priority 3]
