# Sprint Execution Report: Sprint 4: Scenario And Interview Runtime

> Project: SoftSkills
> Report Type: Sprint execution retrospective and delivery report
> Output Location: `ops/reports/sprint-04-scenario-and-interview-runtime-report.md`
> Scope: Backend and platform execution only. Frontend work is tracked separately.

## Report Overview

- Sprint Name: Sprint 4: Scenario And Interview Runtime
- Sprint Window: 2026-03-25 -> 2026-03-25
- Sprint Status: Completed
- Report Author: Codex
- Related Sprint Doc: [ops/sprints/sprint-04-scenario-and-interview-runtime.md](/home/antonioborgerees/df/soft-skills/ops/sprints/sprint-04-scenario-and-interview-runtime.md)
- Related Branch / PR: `sprint/04-scenario-and-interview-runtime`

## Source Docs Used

- [ops/CONSTITUTION.yml](/home/antonioborgerees/df/soft-skills/ops/CONSTITUTION.yml)
- [ops/process/sprint-execution.md](/home/antonioborgerees/df/soft-skills/ops/process/sprint-execution.md)
- [ops/process/stageflow-reporting.md](/home/antonioborgerees/df/soft-skills/ops/process/stageflow-reporting.md)
- [ops/mvp-spec/foundational/product-spec.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/product-spec.md)
- [ops/mvp-spec/operations/content-system.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/operations/content-system.md)
- [ops/mvp-spec/platform/assessment-and-progression.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/platform/assessment-and-progression.md)
- [ops/mvp-spec/engines/marking-engine.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/engines/marking-engine.md)
- [ops/mvp-spec/foundational/stageflow-guide.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/stageflow-guide.md)

## Sprint Summary

- Sprint Goal: Extend the trusted assessment runtime from quick practice to scenario and interview text flows without forking contracts.
- Actual Outcome: Delivered shared practice prompt/session/attempt contracts, interview and scenario session-start APIs, richer persisted prompt payloads with interview/scenario context, assessment-path reuse across all three text modes, direct Stageflow `Pipeline` execution for the full text-practice runtime, and provider-backed smoke coverage across quick practice, interview, and scenario.
- Overall Result: The shared runtime goal is complete. All MVP text practice modes now execute through Stageflow and passed the real-provider smoke harness.

## Planned Vs Delivered

| Area | Planned | Delivered | Status | Notes |
| --- | --- | --- | --- | --- |
| Shared runtime contracts | Reuse one typed assessment backbone across modes | Added shared practice prompt/session models and widened prompt snapshots for interview/scenario context | Done | No separate attempt or assessment contract was introduced |
| Runtime APIs | Add scenario and interview session start flows | Added `POST /api/attempts/interview/sessions` and `POST /api/attempts/scenario/sessions` on top of the existing submit path | Done | Submit and read paths remain shared |
| Rich prompt payloads | Carry actors, artifacts, and richer context | Added typed interview context plus scenario company, people, tensions, and runtime artifacts in the persisted prompt payload | Done | Scenario artifacts are accepted at session start and stored for replay |
| Assessment reuse | Keep typed outputs and version metadata identical across modes | Reused the same marking provider, output guard, persistence shape, and failure taxonomy | Done | Practice type is now part of the prompt snapshot and observability payloads |
| Observability and persistence | Keep richer flows replayable and traceable | Extended session, prompt-delivered, assessment-started, validated, rejected, and failed events with practice-type metadata | Done | Persisted prompt payload is the replay artifact |
| Real-provider smoke | Run backend smokes for richer modes | Extended and ran the backend smoke harness successfully for quick practice, interview, and scenario | Done | Real-provider verification now covers all MVP text practice modes |

## Key Outcomes

- Scenario and interview runtime now use the same submit and assessment flow as quick practice.
- The prompt snapshot is now a typed shared contract with optional interview and scenario sections instead of a quick-practice-only shape.
- The shared text-practice runtime now executes directly through Stageflow `Pipeline.run(...)` instead of the removed custom executor.
- Integration coverage now exercises happy paths and failure guards for interview and scenario modes.
- The existing quick-practice slice kept passing after the shared-runtime and Stageflow execution changes.

## What Worked Well

- Widening the prompt snapshot was enough to reuse the assessment path without schema drift.
- The existing guard/enrich/transform/work split scaled to multiple text practice modes cleanly on the real Stageflow DAG runtime.
- Keeping persistence generic from Sprint 3 made the richer runtime mostly an application-layer change.
- The real-provider smoke harness scaled cleanly once interview and scenario session starts were added to it.

## Challenges And Friction

- The local Python environment resolved a stale editable `soft_skills_backend` package before this repo, so verification had to be run with `PYTHONPATH=src`.
- Collection fixtures had to respect seeded competency-to-skill mappings, which surfaced quickly in integration tests.
- Stageflow's current type hints still model `stage()` as stage classes/instances only, so the runtime uses narrow registration-boundary casts for async callable stages even though the installed runtime supports them.

## Constitution Conformance

- Competency growth: The runtime now supports richer practice situations without changing the assessment outcome model.
- Schema validation: New start commands, prompt payloads, interview context, scenario stakeholders, and runtime artifacts are typed and validated.
- Fail-fast behavior: Invalid prompt-mode mappings, invalid scenario rubric mappings, blank artifact fields, and structured-output failures still stop the workflow with stable codes.
- Explainability: Feedback remains the same evidence-based artifact with strengths, weaknesses, next actions, and skill-level scores.
- Observability: Practice and assessment events now carry practice-type and content metadata across all text modes.
- Stageflow runtime: Text-practice orchestration now runs only through Stageflow with Stageflow interceptors, wide events, and persisted pipeline-run records.
- Persistence: Sessions, attempts, assessments, and the richer prompt snapshot remain durably stored for replay.
- Modularity: Routes stayed thin; query, persistence, view, and assessment helpers remained split inside the feature package.
- No silent fallback: No alternate scoring path or degraded mode was introduced for the new practice types.

## Testing And Verification

- Unit Tests: Added request/payload validation tests for interview context normalization and scenario artifact rejection.
- Integration Tests: Added interview and scenario start -> submit -> assess -> persist coverage plus failure checks for wrong-mode prompt use and invalid scenario rubric mapping.
- Smoke Tests With Real Provider: Ran the existing backend smoke harness successfully. Result:
  - provider: `openrouter`
  - model slug: `openai/gpt-oss-20b:free`
  - quick practice overall score: `4`
  - interview overall score: `3`
  - scenario overall score: `3`
- Failure Path Coverage: Covered invalid scenario mapping, invalid artifact input, wrong-mode start request, rejected structured output, and provider failure.
- Manual Verification:
  - `cd backend && SOFT_SKILLS_STAGEFLOW_REQUIRED=true PYTHONPATH=src .venv/bin/python -m pytest -q tests/integration/test_quick_practice_attempts.py tests/integration/test_richer_practice_runtime.py tests/unit/test_practice_runtime.py tests/unit/test_provider_smoke.py tests/unit/test_openai_compatible_provider.py`
  - `ruff check backend/src/soft_skills_backend/application/container.py backend/src/soft_skills_backend/application/practice/quick_practice/service.py backend/src/soft_skills_backend/application/practice/quick_practice/repository.py backend/src/soft_skills_backend/application/practice/quick_practice/assessment_service.py backend/src/soft_skills_backend/application/practice/quick_practice/queries.py backend/src/soft_skills_backend/application/practice/quick_practice/persistence.py backend/src/soft_skills_backend/application/practice/quick_practice/stageflow.py`
  - `PYTHONPATH=backend/src backend/.venv/bin/python -m mypy backend/src/soft_skills_backend/application/container.py backend/src/soft_skills_backend/application/practice/quick_practice/service.py backend/src/soft_skills_backend/application/practice/quick_practice/repository.py backend/src/soft_skills_backend/application/practice/quick_practice/assessment_service.py backend/src/soft_skills_backend/application/practice/quick_practice/queries.py backend/src/soft_skills_backend/application/practice/quick_practice/persistence.py backend/src/soft_skills_backend/application/practice/quick_practice/stageflow.py`
  - `cd backend && SOFT_SKILLS_STAGEFLOW_REQUIRED=true PYTHONPATH=src .venv/bin/python -m soft_skills_backend.smoke`

## Documentation Updates

- [ops/sprints/sprint-04-scenario-and-interview-runtime.md](/home/antonioborgerees/df/soft-skills/ops/sprints/sprint-04-scenario-and-interview-runtime.md)
- [ops/mvp-spec/platform/assessment-and-progression.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/platform/assessment-and-progression.md)
- [ops/mvp-spec/operations/content-system.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/operations/content-system.md)
- [ops/process/stageflow-reporting.md](/home/antonioborgerees/df/soft-skills/ops/process/stageflow-reporting.md)
- [ops/reports/sprint-04-scenario-and-interview-runtime-report.md](/home/antonioborgerees/df/soft-skills/ops/reports/sprint-04-scenario-and-interview-runtime-report.md)

## Stageflow Usage And Reporting

- Stageflow Used: Yes
- Relevant Features Used: Explicit guard/enrich/transform/work pipelines, typed payloads, correlated workflow IDs, persisted pipeline runs, and domain events
- What Worked: The same DAG shape handled all three text practice modes once prompt resolution was widened behind typed enrich stages, and the real Stageflow runtime dropped in cleanly for execution, wide events, and persisted pipeline runs.
- What Hurt: The installed Stageflow typing for `stage()` is narrower than the runtime behavior for async callable runners, so a narrow cast is still needed at stage registration time.
- Follow-Up Logged In `ops/process/stageflow-reporting.md`: Yes

## Technical And Architectural Debt

| Debt Item | Type | Why It Exists | Impact | Recommended Follow-Up | Owner |
| --- | --- | --- | --- | --- | --- |
| `QuickPracticeService` naming now fronts shared text runtime behavior | Architectural | Reused the existing service package to avoid a broader rename during the sprint | The service name is narrower than its actual responsibility | Rename the package and service to a generic text-practice runtime in a follow-up cleanup | Backend |
| Stageflow callable runner typing is narrower than runtime support | DX | The installed `stageflow-core` type surface does not admit async callable runners in `stage()` even though the runtime executes them correctly | Local registration sites need explicit casts to satisfy static checks | Upstream or locally patch the Stageflow typing for callable stage runners | Backend |

## Open Risks

| Risk | Severity | Why It Matters | Mitigation | Carry To Next Sprint |
| --- | --- | --- | --- | --- |
| Scenario artifacts are runtime-only today | Medium | Content authoring still lacks durable scenario-artifact management | Add authored artifact storage and authoring/edit flows | Yes |

## Deferred Work

- Rename the shared practice runtime package away from quick-practice-specific naming
- Add authored scenario-artifact persistence instead of runtime-only artifact injection

## Retrospective

- Stop: Treating quick-practice naming as if it still reflects the full responsibility of the runtime layer
- Start: Patching or upstreaming Stageflow callable-runner typing so static analysis matches the installed runtime behavior
- Continue: Reusing one typed assessment contract across practice modes instead of forking pipelines

## Next Sprint Recommendations

1. Turn validated assessments from all text modes into progress-state updates.
2. Move shared text-practice orchestration into a more accurately named feature package once the runtime surface stabilizes.
3. Patch or upstream the Stageflow callable-runner typing gap.

## Sign-Off

- Report Status: Final
- Reviewed By: Codex
- Review Date: 2026-03-25

Checklist:

- [x] Outcomes are recorded honestly
- [x] Constitution conformance is assessed explicitly
- [x] Testing and smoke status is documented
- [x] Debt and risks are captured
- [x] Follow-ups for next sprint are clear
- [x] Report is saved in `ops/reports/`
