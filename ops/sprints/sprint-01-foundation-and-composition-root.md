# Sprint 1: Foundation And Composition Root

> Project: SoftSkills
> Scope: Backend and platform execution only. Frontend planning is tracked separately.

## Sprint Overview

- Sprint Name: Sprint 1: Foundation And Composition Root
- Sprint Focus: Establish the backend skeleton, infrastructure boundaries, persistence discipline, and observability primitives
- Depends On: Sprint 0

## Relevant Source Docs

- [CONSTITUTION.yml](/home/antonioborgerees/df/soft-skills/ops/CONSTITUTION.yml): lines 37-58, 135-175, 291-323, 394-427
- [foundational/technical-architecture.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/technical-architecture.md): lines 8-19, 26-94, 125-164
- [foundational/domain-model.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/domain-model.md): lines 100-157
- [foundational/stageflow-guide.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/stageflow-guide.md): lines 79-127, 206-279, 351-430, 534-576, 577-585
- [operations/observability-and-operations.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/operations/observability-and-operations.md): lines 9-125

## Sprint Goals

- Primary Goal: Deliver a stable backend composition root so later features land on explicit contracts instead of ad hoc scaffolding.
- Secondary Goals:
  - Set up modular repository structure, dependency injection, and infrastructure adapters.
  - Establish persistence and migration discipline.
  - Establish shared error, logging, trace, and event primitives.

## Scope Checklist

- [ ] Task 1: Stand up backend service, settings, strict typing, and core developer tooling; standardize on `Pipeline`, `PipelineContext`, and explicit stage kinds
- [ ] Task 2: Establish repository structure and composition root with adapter boundaries; wire Stageflow through clean orchestration modules rather than domain services
- [ ] Task 3: Implement base persistence layer and migration workflow
- [ ] Task 4: Implement shared API envelope, error taxonomy, structured logs, traces, and base events; adopt default interceptors, `BackpressureAwareEventSink`, `PipelineRunLogger`, and `ProviderCallLogger`
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

- [ ] Unit Tests: settings, schemas, error envelopes, DI wiring, and observability helpers
- [ ] Integration Tests: app startup, migrations, persistence bootstrap, and trace/event emission
- [ ] Smoke Tests With Real Provider: verify the baseline provider smoke harness still runs from the backend environment
- [ ] Failure Path Coverage: invalid settings, failed migrations, provider health failures, and bad schema payloads tested
- [ ] Documentation Updates: update canonical docs in `ops/`, the roadmap/sprint docs, and any affected contracts

## Success Criteria

- [ ] Backend service boots with explicit composition boundaries and shared conventions
- [ ] Persistence and migration workflow is operational
- [ ] Base observability primitives exist and can be reused by later slices
- [ ] Real-provider smoke harness runs from backend infrastructure

Minimum Viable Sprint:
The service skeleton, migrations, and observability foundations exist even if no learner-facing business flow is implemented yet.

## Risks And Blockers

| Risk | Impact | Mitigation | Status |
| --- | --- | --- | --- |
| Repository structure drifts into feature sprawl too early | High | Freeze module responsibilities now and keep reviews strict | Open |
| Observability is added too late or too thinly | High | Make trace/log/event primitives part of the foundation sprint exit bar | Open |

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

1. Add identity and profile models and APIs.
2. Seed taxonomy, rubrics, collections, prompts, and scenarios.
3. Keep observability and smoke harness coverage current.
