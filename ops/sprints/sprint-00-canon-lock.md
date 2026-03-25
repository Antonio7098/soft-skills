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

- [x] Task 1: Confirm the active source-of-truth stack and precedence order for implementation decisions
- [x] Task 2: Freeze initial MVP skills, competencies, rubric types, and assessable content types
- [x] Task 3: Freeze initial versioning strategy for prompts, rubrics, engine configs, events, and error codes; include Stageflow prompt/version, typed-output, and wide-event conventions
- [x] Task 4: Define roadmap-wide definition of done for backend slices; freeze the Stageflow baseline around `Pipeline`, default interceptors, provider-call logging, and real-provider smokes
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

- [ ] Unit Tests: validation tests for frozen config artifacts and seed contracts
- [ ] Integration Tests: bootstrap/config loading and source-of-truth enforcement checks
- [ ] Smoke Tests With Real Provider: establish or refresh the baseline provider smoke harness used by later sprints
- [ ] Failure Path Coverage: invalid config, missing version metadata, and schema mismatch cases tested
- [x] Documentation Updates: update canonical docs in `ops/`, the roadmap/sprint docs, and any affected contracts

## Success Criteria

- [x] Initial taxonomy, rubric set, and MVP text practice modes are frozen in canonical docs
- [x] Versioning and error/event conventions are written down and ready for implementation
- [x] Sprint definition of done is explicit and reusable across later sprints
- [ ] A baseline real-provider smoke harness exists for backend use

Minimum Viable Sprint:
Initial MVP semantics and delivery gates are frozen well enough that Sprint 1 can begin without reopening product fundamentals.

## Risks And Blockers

| Risk | Impact | Mitigation | Status |
| --- | --- | --- | --- |
| Taxonomy or rubric churn after implementation starts | High | Freeze a deliberately narrow v1 set and defer expansions | Mitigated |
| Ambiguous precedence between docs | High | Keep `CONSTITUTION.yml` and `ops/mvp-spec/` explicitly referenced in every sprint doc | Mitigated |
| Smoke harness still not implemented in code | High | Carry baseline provider smoke harness into Sprint 1 foundation work and keep it mandatory for later sprints | Open |

## Sprint Notes

Key decisions, tradeoffs, and implementation notes:

```text
- Source precedence is locked as: CONSTITUTION.yml -> relevant ops/mvp-spec file -> active sprint doc for execution detail -> foundational/PRD.md.
- The backend roadmap of record is ops/ROADMAP.md because this repo does not contain a root ROADMAP.md.
- MVP v1 remains text-first and only freezes three assessable content types: quick_practice_prompt, scenario_step, interview_prompt.
- MVP v1 freezes eight competencies, ten skills, and three platform-defined rubric families: quick_practice_text, scenario_text, interview_text.
- Stageflow baseline is locked to Pipeline, PipelineContext, get_default_interceptors(), PipelineRunLogger, provider-call logging, typed structured outputs, and wide events for critical workflows.
- Versioning convention is explicit for prompts, rubrics, configs, typed-output schemas, events, and stored LLM artifacts.
- Error code convention is SS-<CATEGORY>-<NUMBER> with stable categories and stable numeric assignments.
- Sprint 0 is documentation-complete but not implementation-complete for tests or real-provider smoke coverage; those remain delivery requirements for Sprint 1 execution.
```

## Review And Sign-Off

- Sprint Status: Executed With Follow-On Implementation Work
- Completion Date: 2026-03-25

Checklist:

- [x] Primary goal achieved
- [x] Constitution and quality checks passed
- [ ] Unit tests completed
- [ ] Integration tests completed
- [ ] Smoke tests with real provider completed
- [x] Documentation updated
- [ ] Code review completed

Next Sprint Priorities:

1. Stand up the composition root and repository skeleton.
2. Implement shared schemas, errors, observability primitives, and migrations.
3. Keep the smoke harness working as infrastructure evolves.
