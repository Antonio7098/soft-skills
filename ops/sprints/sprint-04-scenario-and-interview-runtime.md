# Sprint 4: Scenario And Interview Runtime

> Project: SoftSkills
> Scope: Backend and platform execution only. Frontend planning is tracked separately.

## Sprint Overview

- Sprint Name: Sprint 4: Scenario And Interview Runtime
- Sprint Focus: Extend the trusted assessment loop to richer text practice modes
- Depends On: Sprint 3

## Relevant Source Docs

- [CONSTITUTION.yml](/home/antonioborgerees/df/soft-skills/ops/CONSTITUTION.yml): lines 83-133, 159-175, 223-237, 308-323
- [foundational/product-spec.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/product-spec.md): lines 89-109
- [operations/content-system.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/operations/content-system.md): lines 36-48, 80-93
- [platform/assessment-and-progression.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/platform/assessment-and-progression.md): lines 8-60, 105-117
- [engines/marking-engine.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/engines/marking-engine.md): lines 21-58, 102-116, 188-219
- [foundational/stageflow-guide.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/stageflow-guide.md): lines 129-204, 206-279, 504-518, 600-604

## Sprint Goals

- Primary Goal: Support scenario practice and text interview flows on the same backend assessment backbone as quick practice.
- Secondary Goals:
  - Add richer prompt/context payloads, including scenario actors and artifacts.
  - Reuse the same validation, persistence, and explainability standards across modes.
  - Expand regression coverage for the broader runtime surface.

## Scope Checklist

- [x] Task 1: Extend runtime APIs and domain models for scenario practice and text interview sessions; keep them on the same Stageflow pipeline shape as quick practice
- [x] Task 2: Support richer prompt payloads, scenario context, stakeholder data, and artifacts; use composition for shared guard and enrichment components
- [x] Task 3: Reuse and extend the marking pipeline for all MVP text practice modes; keep typed outputs, prompt versions, and provider telemetry identical across modes
- [x] Task 4: Expand traces, events, and persistence so richer flows remain replayable and debuggable; use wide events on critical runs
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

- [x] Unit Tests: richer prompt payload validation, scenario coherence rules, and mode-specific orchestration guards
- [x] Integration Tests: scenario and interview session flows, persistence, assessment reuse, and trace/event coverage
- [x] Smoke Tests With Real Provider: run backend smokes for scenario and interview assessments against the real provider
- [x] Failure Path Coverage: invalid scenario mappings, bad artifacts, provider failures, and partial workflow failures tested
- [x] Documentation Updates: update canonical docs in `ops/`, the roadmap/sprint docs, and any affected contracts

## Success Criteria

- [x] Scenario and text interview flows run through the same trusted assessment path as quick practice
- [x] Richer context payloads remain validated, versioned, persisted, and traceable
- [x] Expanded real-provider smokes pass for all MVP text practice modes
- [x] Regression coverage grows with the runtime surface instead of trailing behind it

Minimum Viable Sprint:
Scenario and interview runtime exists and shares the same core assessment guarantees, even if dashboards and recommendations are not yet implemented.

## Risks And Blockers

| Risk | Impact | Mitigation | Status |
| --- | --- | --- | --- |
| New practice modes fork the assessment contracts | High | Force contract reuse and mode adapters rather than separate pipelines | Mitigated |
| Rich scenario content becomes inconsistent or under-validated | High | Validate mappings, actors, artifacts, and rubric links at the boundary | Mitigated |
| Practice runtime drifts away from the real Stageflow runtime | Medium | Run the text practice DAGs directly through `Pipeline.run(...)`, enable wide events, and verify with the real-provider smoke harness | Mitigated |

## Sprint Notes

Key decisions, tradeoffs, and implementation notes:

```text
- Widened the persisted prompt snapshot into a shared typed practice prompt that carries practice type, prompt type, rubric metadata, and optional interview/scenario context.
- Kept one submit/assessment path for all text practice modes instead of forking route handlers or marker contracts.
- Scenario runtime currently accepts typed artifacts at session start and persists them with the prompt snapshot for replay.
- Removed the custom quick-practice executor and now run all text-practice orchestration directly through the Stageflow `Pipeline` API with Stageflow interceptors, wide events, and persisted pipeline runs.
- Ran the backend real-provider smoke successfully on 2026-03-25 against `openrouter` with returned model slug `openai/gpt-oss-20b:free`.
- Real-provider smoke now covers all MVP text practice modes in one run:
  - quick practice overall score: `4`
  - interview overall score: `3`
  - scenario overall score: `3`
```

## Review And Sign-Off

- Sprint Status: Completed
- Completion Date: 2026-03-25

Checklist:

- [x] Primary goal achieved
- [x] Constitution and quality checks passed
- [x] Unit tests completed
- [x] Integration tests completed
- [x] Smoke tests with real provider completed
- [x] Documentation updated
- [x] Code review completed

Next Sprint Priorities:

1. Convert validated assessments into progress state.
2. Build recommendation outputs from evidence rather than raw activity.
3. Keep replay and drift-monitoring requirements explicit.
