# Sprint 0: Canon Lock And Delivery Rules

> Project: SoftSkills
> Scope: Backend and platform execution only. Frontend planning is tracked separately.

## Sprint Overview

- Sprint Name: Sprint 0: Canon Lock And Delivery Rules
- Sprint Focus: Freeze the MVP shape, versioning rules, and sprint-level definition of done
- Depends On: None

## Relevant Source Docs

- [CONSTITUTION.yml](/home/antonioborgerees/df/soft-skills/ops/CONSTITUTION.yml): lines 5-81, 83-175, 413-427
- [ops/mvp-spec/README.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/README.md): lines 10-21, 23-45
- [foundational/product-spec.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/product-spec.md): lines 44-60, 61-109, 133-175
- [foundational/domain-model.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/domain-model.md): lines 100-193
- [foundational/technical-architecture.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/technical-architecture.md): lines 26-67, 125-164
- [foundational/stageflow-guide.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/stageflow-guide.md): lines 25-127, 577-590
- [platform/assessment-and-progression.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/platform/assessment-and-progression.md): lines 8-60, 105-123
- [operations/observability-and-operations.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/operations/observability-and-operations.md): lines 9-91

## Sprint Goals

- Primary Goal: Freeze the initial MVP operating model so implementation can start without ambiguity on core semantics.
- Secondary Goals:
  - Freeze the initial skill taxonomy, competency mapping, rubric set, and text-first practice modes.
  - Define versioning rules for prompts, rubrics, configs, events, and errors.
  - Define sprint-level done criteria for schema validation, persistence, observability, testing, and docs.

## Scope Checklist

- [ ] Task 1: Confirm the active source-of-truth stack and precedence order for implementation decisions
- [ ] Task 2: Freeze initial MVP skills, competencies, rubric types, and assessable content types
- [ ] Task 3: Freeze initial versioning strategy for prompts, rubrics, engine configs, events, and error codes; include Stageflow prompt/version, typed-output, and wide-event conventions
- [ ] Task 4: Define roadmap-wide definition of done for backend slices; freeze the Stageflow baseline around `Pipeline`, default interceptors, provider-call logging, and real-provider smokes
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

- [ ] Unit Tests: validation tests for frozen config artifacts and seed contracts
- [ ] Integration Tests: bootstrap/config loading and source-of-truth enforcement checks
- [ ] Smoke Tests With Real Provider: establish or refresh the baseline provider smoke harness used by later sprints
- [ ] Failure Path Coverage: invalid config, missing version metadata, and schema mismatch cases tested
- [ ] Documentation Updates: update canonical docs in `ops/`, the roadmap/sprint docs, and any affected contracts

## Success Criteria

- [ ] Initial taxonomy, rubric set, and MVP text practice modes are frozen in canonical docs
- [ ] Versioning and error/event conventions are written down and ready for implementation
- [ ] Sprint definition of done is explicit and reusable across later sprints
- [ ] A baseline real-provider smoke harness exists for backend use

Minimum Viable Sprint:
Initial MVP semantics and delivery gates are frozen well enough that Sprint 1 can begin without reopening product fundamentals.

## Risks And Blockers

| Risk | Impact | Mitigation | Status |
| --- | --- | --- | --- |
| Taxonomy or rubric churn after implementation starts | High | Freeze a deliberately narrow v1 set and defer expansions | Open |
| Ambiguous precedence between docs | High | Keep `CONSTITUTION.yml` and `ops/mvp-spec/` explicitly referenced in every sprint doc | Open |

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

1. Stand up the composition root and repository skeleton.
2. Implement shared schemas, errors, observability primitives, and migrations.
3. Keep the smoke harness working as infrastructure evolves.
