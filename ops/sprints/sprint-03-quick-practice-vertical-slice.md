# Sprint 3: Quick Practice Vertical Slice

> Project: SoftSkills
> Scope: Backend and platform execution only. Frontend planning is tracked separately.

## Sprint Overview

- Sprint Name: Sprint 3: Quick Practice Vertical Slice
- Sprint Focus: Deliver the first complete text-first practice -> assess -> reflect loop on the smallest viable practice mode
- Depends On: Sprint 2

## Relevant Source Docs

- [CONSTITUTION.yml](/home/antonioborgerees/df/soft-skills/ops/CONSTITUTION.yml): lines 83-133, 159-221, 223-237, 308-375
- [foundational/product-spec.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/product-spec.md): lines 44-109
- [platform/assessment-and-progression.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/platform/assessment-and-progression.md): lines 8-60, 105-117
- [engines/marking-engine.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/engines/marking-engine.md): lines 21-116, 146-219
- [operations/observability-and-operations.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/operations/observability-and-operations.md): lines 9-125
- [foundational/stageflow-guide.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/stageflow-guide.md): lines 129-162, 206-279, 291-430, 534-576, 592-599

## Sprint Goals

- Primary Goal: Deliver one trustworthy backend practice flow from prompt delivery to validated scored result.
- Secondary Goals:
  - Implement quick-practice session start, prompt delivery, and attempt lifecycle.
  - Implement marking orchestration with schema validation and hard failure behavior.
  - Persist learner-facing assessment artifacts with complete version metadata and trace linkage.

## Scope Checklist

- [ ] Task 1: Implement quick-practice session start and prompt delivery contracts; model the flow as an explicit Stageflow DAG with guard, enrich, transform, and work stages
- [ ] Task 2: Implement attempt submission, lifecycle transitions, and durable attempt persistence
- [ ] Task 3: Implement marking pipeline orchestration, structured output validation, and artifact persistence; use `PromptLibrary`, `TypedLLMOutput`, provider-call logging, and bounded retry/backoff for transient provider failures
- [ ] Task 4: Expose feedback payloads with score, evidence, strengths, weaknesses, and next actions; emit wide events for assessment runs and use typed stage outputs for persisted artifacts
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

- [ ] Unit Tests: attempt state transitions, assessment schemas, evidence validation, and scoring guards
- [ ] Integration Tests: session start, attempt submission, marking workflow, persistence, and trace/event emission
- [ ] Smoke Tests With Real Provider: run an end-to-end quick-practice assessment flow against the real provider from the backend
- [ ] Failure Path Coverage: malformed model output, missing version metadata, provider failure, and invalid attempt transitions tested
- [ ] Documentation Updates: update canonical docs in `ops/`, the roadmap/sprint docs, and any affected contracts

## Success Criteria

- [ ] Quick practice can be started, answered, assessed, and persisted end to end
- [ ] Assessment artifacts are validated before user delivery and progress consumption
- [ ] Feedback is explainable and grounded in evidence from the response
- [ ] Real-provider smoke proves the backend core loop works outside mocks

Minimum Viable Sprint:
The quick-practice backend flow works reliably even if broader scenario and interview modes are still unavailable.

## Risks And Blockers

| Risk | Impact | Mitigation | Status |
| --- | --- | --- | --- |
| Marking output is structured but not actually trustworthy | High | Enforce evidence and contradiction validation before persistence | Open |
| Attempt/assessment states drift from real workflow behavior | High | Keep lifecycle states explicit and integration-tested | Open |

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

1. Extend the runtime to scenarios and text interviews.
2. Reuse the same marking contracts across richer prompt payloads.
3. Increase regression coverage as the practice surface expands.
