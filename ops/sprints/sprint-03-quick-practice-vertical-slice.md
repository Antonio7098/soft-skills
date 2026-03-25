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

- [x] Task 1: Implement quick-practice session start and prompt delivery contracts; model the flow as an explicit Stageflow DAG with guard, enrich, transform, and work stages
- [x] Task 2: Implement attempt submission, lifecycle transitions, and durable attempt persistence
- [x] Task 3: Implement marking pipeline orchestration, structured output validation, and artifact persistence; use `PromptLibrary`, `TypedLLMOutput`, provider-call logging, and bounded retry/backoff for transient provider failures
- [x] Task 4: Expose feedback payloads with score, evidence, strengths, weaknesses, and next actions; emit wide events for assessment runs and use typed stage outputs for persisted artifacts
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

- [x] Unit Tests: attempt state transitions, assessment schemas, evidence validation, and scoring guards
- [x] Integration Tests: session start, attempt submission, marking workflow, persistence, and trace/event emission
- [x] Smoke Tests With Real Provider: execute an end-to-end quick-practice assessment flow against the real provider from the backend and record the result
- [x] Failure Path Coverage: malformed model output, missing version metadata, provider failure, and invalid attempt transitions tested
- [x] Documentation Updates: update canonical docs in `ops/`, the roadmap/sprint docs, and any affected contracts

## Success Criteria

- [x] Quick practice can be started, answered, assessed, and persisted end to end
- [x] Assessment artifacts are validated before user delivery and progress consumption
- [x] Feedback is explainable and grounded in evidence from the response
- [x] Real-provider smoke proves the backend core loop works outside mocks

Minimum Viable Sprint:
The quick-practice backend flow works reliably even if broader scenario and interview modes are still unavailable.

## Risks And Blockers

| Risk | Impact | Mitigation | Status |
| --- | --- | --- | --- |
| Marking output is structured but not actually trustworthy | High | Enforce evidence and contradiction validation before persistence | Mitigated in code; still monitor with real-provider smoke and replay review |
| Attempt/assessment states drift from real workflow behavior | High | Keep lifecycle states explicit and integration-tested | Mitigated for quick-practice v1 |
| Provider/model metadata can diverge between configured alias and provider-returned canonical slug | Medium | Strict validation can reject valid provider executions if metadata is normalized upstream | Mitigated by validating against execution-observed provider metadata and persisting the provider-returned model slug |

## Sprint Notes

Key decisions, tradeoffs, and implementation notes:

```text
- Added persistent `practice_sessions`, `attempts`, and `assessments` tables with Alembic migration `20260325_0003`.
- Added quick-practice API contracts:
  - `POST /api/attempts/quick-practice/sessions`
  - `POST /api/attempts/{attempt_id}/submit`
  - `GET /api/attempts/{attempt_id}`
- Implemented explicit fallback DAG executor to preserve guard/enrich/transform/work stage boundaries while `stageflow` is not installed locally.
- Added versioned assessment prompting via local `PromptLibrary` and strict structured output parsing via local `TypedLLMOutput` wrapper.
- Persisted validated learner-facing assessment artifacts and separately persisted rejected structured outputs for replay.
- Added quick-practice events:
  - `practice.session_started.v1`
  - `practice.prompt_delivered.v1`
  - `practice.attempt_submitted.v1`
  - `assessment.started.v1`
  - `assessment.validated.v1`
  - `assessment.rejected.v1`
  - `workflow.failed.v1`
- Added a real-provider smoke harness that constructs the built `OpenAICompatibleLLMProvider` adapter and drives the full quick-practice backend loop through the real submit path.
- Executed the real-provider smoke with backend environment credentials against the built adapter path.
- Fixed a real-provider validation bug where the provider returned a canonical model slug that differed from the configured alias; validation now accepts normalized equivalent slugs and persists the execution-observed model slug.
- Fixed fail-fast behavior for provider-backed smoke and provider calls:
  - provider retries disabled in smoke
  - assessment validation retries disabled in smoke
  - hard outer smoke timeout added
  - hard wall-clock timeout added around each provider completion request
- Current smoke result succeeds within the bounded runtime budget:
  - provider: `openrouter`
  - model slug: `openai/gpt-5.4-nano-20260317`
  - overall score: `5`
- Verification run:
  - `PYTHONPATH=src python - <<'PY' ... run_provider_smoke() ... PY`
  - `PYTHONPATH=src python -m pytest -q`
  - `PYTHONPATH=src python -m ruff check src tests`
  - `PYTHONPATH=src python -m mypy src`
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

1. Extend the runtime to scenarios and text interviews.
2. Reuse the same marking contracts across richer prompt payloads.
3. Increase regression coverage as the practice surface expands.
