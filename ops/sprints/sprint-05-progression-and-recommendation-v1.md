# Sprint 5: Progression And Recommendation V1

> Project: SoftSkills
> Scope: Backend and platform execution only. Frontend planning is tracked separately.

## Sprint Overview

- Sprint Name: Sprint 5: Progression And Recommendation V1
- Sprint Focus: Turn validated assessments into meaningful progress state and next-practice guidance
- Depends On: Sprint 4

## Relevant Source Docs

- [CONSTITUTION.yml](/home/antonioborgerees/df/soft-skills/ops/CONSTITUTION.yml): lines 223-253, 308-323, 356-375
- [platform/assessment-and-progression.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/platform/assessment-and-progression.md): lines 62-123
- [platform/soft-skill-progression.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/platform/soft-skill-progression.md): lines 15-43, 44-99, 101-125
- [platform/soft-skill-recommendation.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/platform/soft-skill-recommendation.md): lines 15-57, 59-113
- [engines/progression-engine.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/engines/progression-engine.md): lines 7-75, 77-96
- [engines/recommendation-engine.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/engines/recommendation-engine.md): lines 7-76, 78-103
- [foundational/stageflow-guide.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/stageflow-guide.md): lines 163-187, 206-279, 291-418, 534-576, 606-610

## Sprint Goals

- Primary Goal: The backend can explain learner progress and compute evidence-based next-step recommendations.
- Secondary Goals:
  - Implement skill and competency progression from validated assessments only.
  - Persist explainable snapshots and supporting evidence ledgers.
  - Implement recommendation generation from weak skills, stagnation, goals, and content fit.

## Scope Checklist

- [ ] Task 1: Implement progression adapters that ingest validated assessments and update skill state; use Stageflow for orchestration only, not progression semantics
- [ ] Task 2: Implement competency aggregation, confidence handling, and snapshot persistence; use typed outputs and explicit schema versions for snapshot and evidence-ledger artifacts
- [ ] Task 3: Implement recommendation candidate retrieval, scoring, constraints, and reason codes; emit wide events and pipeline/provider logs for recommendation generation
- [ ] Task 4: Implement replay-ready update and recalculation scaffolding for progression and recommendation artifacts; use checkpoint patterns only for heavy replay/recalc jobs
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

- [ ] Unit Tests: aggregation math, confidence rules, threshold floors, recommendation scoring, and reason-code generation
- [ ] Integration Tests: progression updates from validated assessments, snapshot persistence, recommendation APIs, and event emission
- [ ] Smoke Tests With Real Provider: run backend smokes that start from a real-provider assessment and verify progression/recommendation updates
- [ ] Failure Path Coverage: rejected assessments, stale versions, bad config, empty candidate sets, and replay failures tested
- [ ] Documentation Updates: update canonical docs in `ops/`, the roadmap/sprint docs, and any affected contracts

## Success Criteria

- [ ] Progress state updates only from validated assessments and remains reproducible
- [ ] Competency state is explainable through underlying skill evidence and weighting
- [ ] Recommendations carry clear reason codes tied to stored evidence and learner context
- [ ] Backend smokes prove the assessment -> progress -> recommendation chain works with real provider input

Minimum Viable Sprint:
Skill progression and recommendation work for core cases even if more advanced recalculation and governance tooling remains thin.

## Risks And Blockers

| Risk | Impact | Mitigation | Status |
| --- | --- | --- | --- |
| Progress inflates too quickly from sparse evidence | High | Add minimum evidence thresholds, confidence separation, and capped deltas | Open |
| Recommendations drift toward novelty instead of learning value | High | Keep weakness, stagnation, and goal alignment as primary scoring drivers | Open |

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

1. Strengthen creator workflows on top of stable content contracts.
2. Add provider-backed draft generation while preserving content quality rules.
3. Keep recommendation inputs aligned with catalog trust states.
