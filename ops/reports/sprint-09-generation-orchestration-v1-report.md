# Sprint Execution Report: Sprint 9 Generation Orchestration V1

> Project: SoftSkills
> Report Type: Sprint execution retrospective and delivery report
> Output Location: `ops/reports/sprint-09-generation-orchestration-v1-report.md`
> Scope: Backend and platform execution only. Frontend work is tracked separately.

## Report Overview

- Sprint Name: Sprint 9 Generation Orchestration V1
- Sprint Window: 2026-03-26 -> 2026-03-26
- Sprint Status: Completed
- Report Author: Codex
- Related Sprint Doc: [ops/sprints/sprint-09-generation-orchestration-v1.md](/home/antonioborgerees/df/soft-skills/ops/sprints/sprint-09-generation-orchestration-v1.md)
- Related Branch / PR: `sprint/09-generation-orchestration-v1`

## Source Docs Used

- [ops/CONSTITUTION.yml](/home/antonioborgerees/df/soft-skills/ops/CONSTITUTION.yml)
- [ops/sprints/sprint-09-generation-orchestration-v1.md](/home/antonioborgerees/df/soft-skills/ops/sprints/sprint-09-generation-orchestration-v1.md)
- [ops/mvp-spec/README.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/README.md)
- [ops/mvp-spec/operations/content-system.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/operations/content-system.md)
- [ops/mvp-spec/operations/generation.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/operations/generation.md)
- [ops/process/sprint-execution.md](/home/antonioborgerees/df/soft-skills/ops/process/sprint-execution.md)
- [ops/process/stageflow-reporting.md](/home/antonioborgerees/df/soft-skills/ops/process/stageflow-reporting.md)

## Sprint Summary

- Sprint Goal: Replace monolithic collection generation with modular Stageflow-backed generation and add prompt-item generation inside existing collections.
- Actual Outcome: The backend now supports existing-collection prompt-item generation, collection generation runs as planner plus worker fan-out, artifacts persist a manifest of planner and child-worker runs, the generation code is split into focused modules, the provider-backed generation smoke suites ran successfully, and the heavier latency-envelope smoke exposed and helped fix both provider-shape retry gaps and dropped child-timeout propagation in Stageflow subpipelines.
- Overall Result: The sprint landed cleanly. The implementation, verification, smoke coverage, and docs now line up, with the remaining `mypy` instability recorded as repo-wide debt rather than an unverified Sprint 9 gap. Live-provider latency risk is now narrower and better understood after the heavier smoke investigation.

## Planned Vs Delivered

| Area | Planned | Delivered | Status | Notes |
| --- | --- | --- | --- | --- |
| Existing collection expansion | Add endpoints to generate prompt items in existing collections | Added structured and chat prompt-item generation routes, commands, views, service methods, validators, artifacts, and persistence | Done | Endpoints create draft prompt items under collection invariants |
| Modular collection generation | Replace single oversized LLM draft call with modular orchestration | Added blueprint planner call plus prompt-item and scenario worker fan-out with parent persistence | Done | Collection generation is now multi-call and manifest-backed |
| Stageflow orchestration | Use Stageflow fan-out and child execution with traceability | Added parent pipelines, worker child pipelines, and `run_logged_subpipeline(...)` logging support | Done | Parent and child runs now both persist pipeline-run records |
| Validation and artifacts | Preserve fail-fast validation and durable metadata | Added plan/draft validation, duplicate rejection, prompt/rubric compatibility checks, and manifest artifact persistence | Done | Child worker metadata is stored alongside final generation artifacts |
| Verification and smoke | Extend unit, integration, and smoke coverage | Added unit and integration coverage, wired content-generation smoke suites into the default registry, and ran the provider-backed generation smoke suites successfully | Done | Real provider smoke passed for collection generation and existing-collection prompt-item generation |

## Key Outcomes

- Added `POST /api/collections/{collection_id}/generate/prompt-items/structured` and `POST /api/collections/{collection_id}/generate/prompt-items/chat`.
- Replaced all-in-one collection generation with blueprint planning plus worker fan-out for prompt items and scenarios.
- Split generation implementation across prompt library, prompting, validation, worker execution, persistence, and parent pipeline modules.
- Added manifest-style generation artifacts with planner and worker metadata.
- Extended smoke registry coverage to include structured/chat collection generation and structured/chat prompt-item generation.

## What Worked Well

- Typed contracts at each boundary made the planner-plus-workers split feasible without losing validation rigor.
- The `run_logged_subpipeline(...)` helper preserved Stageflow observability while introducing child pipelines.
- Integration tests around persistence, artifacts, and pipeline names caught orchestration regressions quickly.
- The heavier provider-backed latency smoke was useful because it failed on real runtime behavior, not just schema wiring, and exposed two distinct operational bugs that the smaller smokes did not.

## Challenges And Friction

- The first refactor still left generation orchestration concentrated in one oversized service file, which had to be split again to meet the sprint’s file-boundary rule.
- Child pipelines initially failed because provider call contexts need the child pipeline run ID from Stageflow context, not a raw metadata lookup.
- The first latency-envelope runs failed for two different reasons: malformed provider response shapes were not retried in the smoke environment, and child subpipelines silently dropped the parent timeout budget and fell back to Stageflow's 30-second default.
- `mypy` is not a clean verification gate for this repository today; it surfaces a broad pre-existing strict-typing backlog outside Sprint 9.
- The collection-generation smoke payload currently surfaces the generated collection snapshot but not the artifact/provider metadata that the prompt-item generation smoke payload already returns.

## Constitution Conformance

- Competency growth: The sprint improves authoring and generation quality around the same collection and prompt-item content used in the `practice -> assess -> reflect -> progress -> repeat` loop.
- Schema validation: New request and response boundaries for prompt-item generation are typed, planner outputs are typed, worker outputs are typed, and final artifacts remain versioned.
- Fail-fast behavior: Planner drift, worker drift, invalid rubric/type alignment, skill-scope violations, and duplicates fail with explicit validation codes.
- Explainability: Generated content remains editable draft content, and manifest artifacts make the planner/worker decomposition inspectable instead of opaque.
- Observability: Parent and child pipeline runs, workflow events, provider-call context, request IDs, trace IDs, prompt versions, config versions, model slugs, and provider names are persisted.
- Persistence: Collections and generated prompt items persist only at the parent workflow boundary; generation artifacts now include a manifest of planner and worker outputs.
- Modularity: Prompting, orchestration, validation, persistence, and smoke coverage are split into dedicated modules rather than being collapsed into a single service file.
- No silent fallback: Invalid generation outputs raise typed validation errors; workers do not silently drop failures or partial outputs.

## Testing And Verification

- Unit Tests: Added validator coverage for prompt-item generation counts and duplicate protection, updated runtime config assertions, and extended smoke registry coverage assertions.
- Integration Tests: Added full-flow coverage for modular collection generation and existing-collection prompt-item generation, including artifact persistence and duplicate rejection.
- Smoke Tests With Real Provider:
  - `PYTHONPATH=src python -m soft_skills_backend.smoke provider-baseline`
  - `PYTHONPATH=src python -m soft_skills_backend.smoke generation-structured`
  - `PYTHONPATH=src python -m soft_skills_backend.smoke generation-chat`
  - `PYTHONPATH=src python -m soft_skills_backend.smoke generation-prompt-items-structured`
  - `PYTHONPATH=src python -m soft_skills_backend.smoke generation-prompt-items-chat`
  - All five passed against the configured provider.
- Heavier Live-Provider Smoke Investigation:
  - Added and ran `PYTHONPATH=src python -m soft_skills_backend.smoke generation-latency-envelope`
  - The first failing runs exposed:
    - malformed provider payload shape failures that should have retried but did not in the smoke environment
    - `SS-VALIDATION-071` scenario-worker failures caused by a child-stage timeout of `30000ms`
  - Fixes applied during the sprint:
    - provider payload-shape parsing failures are now treated as retryable in [`openai_compatible.py`](/home/antonioborgerees/df/soft-skills/backend/src/soft_skills_backend/platform/providers/llm/openai_compatible.py)
    - latency-envelope smoke now enables provider retries through [`environment.py`](/home/antonioborgerees/df/soft-skills/backend/src/soft_skills_backend/smoke/support/environment.py)
    - worker timeout budgets are now passed from parent generation pipelines into child worker launches
    - [`run_logged_subpipeline(...)`](/home/antonioborgerees/df/soft-skills/backend/src/soft_skills_backend/platform/workflows/stageflow.py) now rehydrates child `PipelineContext.data` from Stageflow `_parent_data`, so timeout and idempotency controls survive `SubpipelineSpawner.spawn()`
  - Post-fix verification:
    - isolated heavy structured collection run passed against the live provider
    - isolated heavy chat collection run passed against the live provider
    - the latency-envelope suite now gets past the original scenario-worker timeout failure and exposes remaining live-provider variability as a tuning problem rather than a broken timeout path
- Failure Path Coverage: Exercised blueprint count drift, generated prompt-item duplication, validation-code changes, and child-worker pipeline failures during implementation.
- Manual Verification:
  - `python -m py_compile` for changed generation and smoke modules
  - `python -m ruff check ...` on changed backend files
  - `PYTHONPATH=src pytest tests/unit/test_catalog_validators.py tests/unit/test_app_agnostic_engines.py tests/unit/test_smoke_runner.py tests/unit/test_stageflow_runtime.py -q`
  - `PYTHONPATH=src pytest tests/integration/test_identity_and_catalog.py -q`
  - container composition check via `build_container(...)`
  - attempted `python -m mypy ...`, but the repository still has broader strict-typing failures outside Sprint 9 scope

## Documentation Updates

- Added [ops/mvp-spec/operations/generation.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/operations/generation.md)
- Updated [ops/mvp-spec/README.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/README.md)
- Updated [ops/mvp-spec/operations/content-system.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/operations/content-system.md)
- Updated [ops/sprints/sprint-09-generation-orchestration-v1.md](/home/antonioborgerees/df/soft-skills/ops/sprints/sprint-09-generation-orchestration-v1.md)
- Updated [ops/process/stageflow-reporting.md](/home/antonioborgerees/df/soft-skills/ops/process/stageflow-reporting.md)

## Stageflow Usage And Reporting

- Stageflow Used: Yes
- Relevant Features Used: typed pipelines, fan-out/fan-in DAGs, child pipelines, request-scoped idempotency, persisted pipeline-run logging, and provider-call correlation
- What Worked: Stageflow handled explicit parent orchestration and child worker isolation well once logging and context rehydration were wrapped locally.
- What Hurt: Child pipeline execution needed application-level `PipelineContext` reconstruction, and `SubpipelineSpawner.spawn()` forks child contexts with fresh `data={}` so application timeout/idempotency controls are lost unless the wrapper rehydrates them before `Pipeline.run(...)`.
- Follow-Up Logged In `ops/process/stageflow-reporting.md`: Yes

## Technical And Architectural Debt

| Debt Item | Type | Why It Exists | Impact | Recommended Follow-Up | Owner |
| --- | --- | --- | --- | --- | --- |
| Collection-generation smoke payload does not surface artifact metadata | Test | The smoke backend wrapper returns the collection snapshot rather than the top-level generation response for collection generation | Smoke diagnostics for collection generation are thinner than prompt-item generation | Update the collection-generation smoke backend wrapper to expose `provider`, `model_slug`, and `generation_artifact_id` directly | Backend |
| Repo-wide strict typing baseline remains red | Technical | `mypy` already fails across unrelated modules and strict callable-stage patterns | Type-check verification cannot be used as a green gate yet | Triage and reduce baseline mypy debt before relying on it as a sprint close-out check | Backend platform |
| Duplicate detection is still exact-match normalization | Architectural | Sprint 9 only needed deterministic duplicate protection | Near-duplicate content may still slip through | Add semantic or rubric-aware duplicate heuristics in a follow-up sprint | Catalog |

## Open Risks

| Risk | Severity | Why It Matters | Mitigation | Carry To Next Sprint |
| --- | --- | --- | --- | --- |
| Fan-out latency under live provider load may exceed current timeout/concurrency assumptions | Medium | The heavier latency smoke flushed out a real child-timeout propagation bug, and isolated heavy runs now pass, but repeated larger runs still need to establish a stable operating envelope | Tune `max_parallel_*`, retain child timeout propagation, and repeat provider-backed latency-envelope runs to set budgets from evidence | Yes |
| Child manifest payloads may grow quickly with larger generation counts | Medium | Manifest persistence now stores worker-level output and raw payloads | Add artifact size monitoring and consider compression or archival policy | Yes |
| Strict typing debt can mask new regressions in future workflow changes | Medium | `mypy` is not yet usable as a trustworthy gate | Reduce global type-check backlog incrementally | Yes |

## Deferred Work

- Richer near-duplicate and quality heuristics for generated prompt items
- Additional replay tooling or inspection UIs for manifest artifacts

## Retrospective

- Stop: letting major orchestration refactors stay in an oversized service file after the first implementation pass
- Start: creating the smoke suite wiring in the same change that introduces provider-backed endpoints
- Continue: using integration tests to lock down pipeline names, artifact persistence, and failure codes during workflow refactors

## Next Sprint Recommendations

1. Tune concurrency and timeout settings from repeated real-provider generation smoke runs.
2. Add semantic duplicate detection and content-quality evaluation on top of the current deterministic guards.
3. Build creator-facing replay or review tooling on top of the new generation manifest artifacts.

## Sign-Off

- Report Status: Final
- Reviewed By: Codex
- Review Date: 2026-03-26

Checklist:

- [x] Outcomes are recorded honestly
- [x] Constitution conformance is assessed explicitly
- [x] Testing and smoke status is documented
- [x] Debt and risks are captured
- [x] Follow-ups for next sprint are clear
- [x] Report is saved in `ops/reports/`
