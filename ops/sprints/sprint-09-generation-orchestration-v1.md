# Sprint 9: Generation Orchestration V1

> Project: SoftSkills
> Scope: Backend and platform execution only. Frontend planning is tracked separately.

## Sprint Overview

- Sprint Name: Sprint 9: Generation Orchestration V1
- Sprint Focus: Replace monolithic creator generation with modular Stageflow-backed orchestration and add prompt-item generation inside existing collections
- Depends On: Sprint 6 and Sprint 8

## Relevant Source Docs

- [CONSTITUTION.yml](/home/antonioborgerees/df/soft-skills/ops/CONSTITUTION.yml): lines 48-58, 71-80, 100-158, 199-221, 377-392
- [ops/mvp-spec/README.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/README.md): lines 10-24, 41-57
- [foundational/stageflow-guide.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/stageflow-guide.md): lines 25-77, 81-119, 199-214, 238-260
- [operations/content-system.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/operations/content-system.md): lines 50-96
- [operations/generation.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/operations/generation.md): lines 24-46, 98-127, 167-230, 263-357, 390-717

## Sprint Goals

- Primary Goal: Deliver a backend-usable, fully traced, strongly typed generation system that can generate prompt items inside existing collections and generate collections through modular multi-call orchestration.
- Secondary Goals:
  - Split generation contracts, prompting, validation, Stageflow orchestration, and persistence into focused modules.
  - Use Stageflow parent pipelines plus child worker orchestration where runtime-variable generation units need isolation and replayable correlation.
  - Preserve or improve validation strictness, artifact durability, and real-provider smoke coverage while changing the generation architecture.

## Scope Checklist

- [x] Task 1: Add typed prompt-item generation commands, views, routes, and service methods for existing collections
- [x] Task 2: Modularize catalog generation into focused contracts, prompts, validation, context, persistence, and orchestration files
- [x] Task 3: Implement Stageflow-backed multi-call collection generation with planner plus prompt-item and scenario worker execution
- [x] Task 4: Add manifest-style generation artifacts, richer validation guards, and duplicate protection for generated prompt items
- [x] Task 5: Extend unit, integration, and smoke coverage for the new generation surface
- [x] Task 6: Documentation updates for all changed behavior and contracts

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

- [x] Unit Tests: deterministic coverage for new generation contracts, validators, and artifact shaping
- [x] Integration Tests: API, persistence, orchestration, and event/trace coverage for prompt-item generation and modular collection generation
- [x] Smoke Tests With Real Provider: extend and run backend smoke coverage for existing-collection prompt-item generation and modular collection generation
- [x] Failure Path Coverage: explicit schema rejection, guard rejection, duplicate rejection, provider failure, and persistence failure coverage
- [x] Documentation Updates: update canonical docs in `ops/`, the roadmap/sprint docs, and any affected contracts

## Success Criteria

- [x] Prompt-item generation in existing collections is backend-usable and validated against collection invariants
- [x] Collection generation no longer depends on one oversized model call for the full final draft
- [x] Generation artifacts preserve enough prompt, model, version, and child-run metadata to replay and debug the workflow
- [x] Generation traces and events make parent and worker execution understandable without manual reconstruction
- [x] Real-provider smoke coverage exists for the changed generation flows

Minimum Viable Sprint:
Existing-collection prompt-item generation works end to end, and full collection generation is modularized enough that prompt-item and scenario generation are isolated, validated units even if child execution remains orchestrated inside a bounded generation stage rather than a broader generic generation platform.

## Risks And Blockers

| Risk | Impact | Mitigation | Status |
| --- | --- | --- | --- |
| Multi-call generation weakens atomic persistence or observability if child results are written opportunistically | High | Keep domain persistence at the parent boundary and record child metadata in a manifest-style artifact | Closed |
| Refactoring the current generation service touches too many surfaces at once | High | Split by responsibility, keep routes stable, and add integration coverage around old and new flows immediately | Closed |
| Subpipeline or child-run orchestration may not fit the current app-level Stageflow logging wrapper cleanly | Medium | Introduce a shared platform helper for logged child execution rather than scattering raw Stageflow calls | Closed |
| Real-provider latency and retry behavior may become unstable under fan-out | Medium | Use bounded concurrency, preserve provider-level retries, and keep Stageflow retries semantic rather than transport-level | Open |

## Sprint Notes

Key decisions, tradeoffs, and implementation notes:

```text
- This sprint is intentionally executed as one integrated backend slice rather than separate delivery phases.
- The design target is a planner-plus-workers generation model with deterministic metadata assembly.
- Stageflow is used for explicit orchestration; domain validators remain the invariant source.
- Parent workflows own persistence. Child workers return validated drafts and metadata, not domain writes.
- Existing public collection-generation routes remain stable unless a deliberate contract change is documented.
- The generation workflow was split across dedicated orchestration, prompting, validation, worker, and persistence modules to stay within the sprint file-boundary rules.
- Logged child pipelines required a new `run_logged_subpipeline(...)` helper so pipeline runs and provider calls stay correlated through fan-out execution.
- Real-provider smoke suites were extended and executed for collection generation and existing-collection prompt-item generation.
```

## Verification Notes

- Targeted verification completed:
  - `python -m py_compile` for the changed generation and smoke modules
  - `python -m ruff check` for the changed backend and test files
  - `PYTHONPATH=src pytest tests/unit/test_catalog_validators.py tests/unit/test_app_agnostic_engines.py tests/unit/test_smoke_runner.py tests/unit/test_stageflow_runtime.py -q`
  - `PYTHONPATH=src pytest tests/integration/test_identity_and_catalog.py -q`
  - `PYTHONPATH=src python -m soft_skills_backend.smoke provider-baseline`
  - `PYTHONPATH=src python -m soft_skills_backend.smoke generation-structured`
  - `PYTHONPATH=src python -m soft_skills_backend.smoke generation-chat`
  - `PYTHONPATH=src python -m soft_skills_backend.smoke generation-prompt-items-structured`
  - `PYTHONPATH=src python -m soft_skills_backend.smoke generation-prompt-items-chat`
  - container composition smoke via `build_container(...)`
- Attempted but not clean at repo baseline:
  - `python -m mypy ...` still fails because the repository already has broader strict-typing debt outside Sprint 9, plus existing untyped Stageflow callable-stage patterns.

## Review And Sign-Off

- Sprint Status: Completed
- Completion Date: 2026-03-26

Checklist:

- [x] Primary goal achieved
- [x] Constitution and quality checks passed
- [x] Unit tests completed
- [x] Integration tests completed
- [x] Smoke tests with real provider completed
- [x] Documentation updated
- [x] Code review completed

Next Sprint Priorities:

1. Tune concurrency or timeout settings from the live generation smoke latency now that the provider-backed flows are green.
2. Tighten content-quality evaluation and replay tooling for generated artifacts.
3. Expand deduplication and content-quality heuristics beyond deterministic checks.
