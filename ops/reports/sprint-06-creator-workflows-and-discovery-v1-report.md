# Sprint Execution Report: Sprint 6: Creator Workflows And Discovery V1

> Project: SoftSkills
> Report Type: Sprint execution retrospective and delivery report
> Output Location: `ops/reports/sprint-06-creator-workflows-and-discovery-v1-report.md`
> Scope: Backend and platform execution only. Frontend work is tracked separately.

## Report Overview

- Sprint Name: Sprint 6: Creator Workflows And Discovery V1
- Sprint Window: 2026-03-26 -> 2026-03-26
- Sprint Status: Completed
- Report Author: Codex
- Related Sprint Doc: [ops/sprints/sprint-06-creator-workflows-and-discovery-v1.md](/home/antonioborgerees/df/soft-skills/ops/sprints/sprint-06-creator-workflows-and-discovery-v1.md)
- Related Branch / PR: `sprint/06-creator-workflows-and-discovery-v1`

## Source Docs Used

- [ops/CONSTITUTION.yml](/home/antonioborgerees/df/soft-skills/ops/CONSTITUTION.yml)
- [ops/process/sprint-execution.md](/home/antonioborgerees/df/soft-skills/ops/process/sprint-execution.md)
- [ops/process/stageflow-reporting.md](/home/antonioborgerees/df/soft-skills/ops/process/stageflow-reporting.md)
- [ops/mvp-spec/foundational/product-spec.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/product-spec.md)
- [ops/mvp-spec/operations/content-system.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/operations/content-system.md)
- [ops/mvp-spec/operations/observability-and-operations.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/operations/observability-and-operations.md)
- [ops/mvp-spec/foundational/stageflow-guide.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/stageflow-guide.md)

## Sprint Summary

- Sprint Goal: Support complete creator workflows from draft authoring through trusted publication and discovery without weakening validation or observability.
- Actual Outcome: Delivered draft editing for collections, prompt items, and scenarios; scenario supporting-artifact authoring; save/unsave reuse flows; discovery-tiered catalog reads; durable generation artifacts; structured and chat generation pipelines with prompt security and typed output validation; migration support; route coverage; and passing real-provider smoke for both generation entrypoints and the baseline assessment modes.
- Overall Result: The sprint goal is complete. Creator flows now cover manual editing, provider-backed draft generation, publication semantics, and discovery semantics on typed, replayable backend contracts.

## Planned Vs Delivered

| Area | Planned | Delivered | Status | Notes |
| --- | --- | --- | --- | --- |
| Manual authoring maturity | Move beyond bare create-only CRUD | Added collection, prompt-item, and scenario updates plus scenario supporting-artifact persistence and validation | Done | Validation stays in explicit guard stages |
| Structured generation | Add constrained provider-backed draft generation | Added Stageflow-backed structured generation with versioned prompts, typed output validation, prompt-security sanitization, and durable generation artifacts | Done | Generated drafts persist input/output payloads and execution metadata |
| Chat generation | Add natural-language draft generation under the same rules | Added chat generation with `PromptSecurityPolicy`, typed output validation, and the same downstream validation/persistence path as structured generation | Done | No `AgentStage` or tool loop was added because the sprint did not justify one |
| Publish and discovery semantics | Distinguish standard public from verified public and support reuse | Added direct public publication, save/unsave, actor-aware saved state, `private`/`standard_public`/`verified_public` discovery tiers, and tier filtering | Done | Public verification remains admin-controlled |
| Smoke verification | Prove the new provider-backed flows through the backend | Updated smoke to hit both generation endpoints and ran it successfully on 2026-03-26 | Done | Runtime practice assertions still use stable manual fixtures to keep smoke deterministic |

## Key Outcomes

- Creator drafts are now editable after initial creation rather than being locked to create-only flows.
- Scenario authoring now includes persisted supporting artifacts alongside mock-company and mock-person state.
- Structured and chat generation both go through typed output validation, shared catalog validation, and durable artifact persistence.
- Public catalog reads now distinguish private, standard-public, and verified-public content explicitly.
- Save/unsave behavior is part of the backend contract instead of an implied frontend-only state.
- The smoke harness now proves both generation entrypoints against the configured real provider before running the practice baseline.

## What Worked Well

- Reusing the existing Stageflow helpers, provider adapter, and typed-output wrapper kept the new generation slice consistent with earlier backend work.
- Treating generated drafts as first-class catalog records avoided a separate “temporary draft” subsystem and kept editability simple.
- Persisting collection-scoped generation artifacts made validation failures and replay questions concrete instead of inferential.
- Splitting smoke generation checks from the practice runtime fixtures kept the real-provider verification stable enough to pass repeatedly.

## Challenges And Friction

- The initial generation contract was too strict for the configured provider/model pair; nested scenario fields were often omitted even when the top-level draft was coherent.
- The default Stageflow 30-second stage timeout was too small for generation plus corrective validation retries and had to be overridden explicitly for this workflow.
- Using generated content directly for the interview smoke made the overall smoke path less deterministic than the prior manual fixtures.
- The Stageflow callable-stage typing gap remains, so the catalog pipelines still need local casts at registration sites.

## Constitution Conformance

- Competency growth: The sprint supports the learner-as-creator use case without shifting the product away from competency growth. Content remains mapped to skills, competencies, and rubrics before publication.
- Schema validation: Added typed commands and views for updates, saves, generation, scenario artifacts, and discovery filters; provider outputs are validated through `TypedLLMOutput`.
- Fail-fast behavior: Invalid lifecycle transitions, invalid saved-state transitions, generation metadata drift, malformed provider JSON, and publishability failures all hard-stop with stable error codes.
- Explainability: Generated artifacts persist the validated payload, input payload, prompt version, provider, model slug, trace ID, and workflow ID so a draft’s provenance is inspectable.
- Observability: Added catalog update/save/unsave/generation events, retained Stageflow pipeline-run logs, and persisted generation metadata and workflow correlation fields.
- Persistence: Added migration-backed tables/columns for scenario supporting artifacts, collection saves, content-generation artifacts, source type, and latest generation artifact linkage.
- Modularity: Routes stayed thin; collection/prompt/scenario/generation workflows are separate services; provider access remains behind the shared LLM adapter; catalog orchestration is explicit.
- No silent fallback: Provider output normalization was not introduced. The fix path was prompt/timeout tuning plus explicit validation retries, and malformed output still fails closed.

## Testing And Verification

- Unit Tests: Added `backend/tests/unit/test_catalog_validators.py` for generation-count validation, discovery-tier validation, supporting-artifact validation, and mock-world guard behavior.
- Integration Tests: Expanded `backend/tests/integration/test_identity_and_catalog.py` to cover draft editing, supporting artifacts, save/unsave, verified discovery, structured generation, chat generation, and generation failure paths.
- Smoke Tests With Real Provider: Ran `cd backend && make smoke` successfully on 2026-03-26. The smoke now hits both generation endpoints and then runs the baseline quick-practice, interview, and scenario assessments. Result:
  - provider: `openrouter`
  - model slug: `openai/gpt-oss-20b:free`
  - quick practice overall score: `4`
  - interview overall score: `3`
  - scenario overall score: `3`
- Failure Path Coverage: Covered invalid generation metadata drift, unsupported scenario artifact types, missing mock-company context, saved-state misuse, and invalid publication semantics in tests.
- Manual Verification:
  - `cd backend && PYTHONPATH=src pytest -q`
  - `cd backend && make smoke`

## Documentation Updates

- [ops/mvp-spec/operations/content-system.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/operations/content-system.md)
- [ops/mvp-spec/operations/observability-and-operations.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/operations/observability-and-operations.md)
- [ops/process/stageflow-reporting.md](/home/antonioborgerees/df/soft-skills/ops/process/stageflow-reporting.md)
- [ops/sprints/sprint-06-creator-workflows-and-discovery-v1.md](/home/antonioborgerees/df/soft-skills/ops/sprints/sprint-06-creator-workflows-and-discovery-v1.md)
- [ops/reports/sprint-06-creator-workflows-and-discovery-v1-report.md](/home/antonioborgerees/df/soft-skills/ops/reports/sprint-06-creator-workflows-and-discovery-v1-report.md)

## Stageflow Usage And Reporting

- Stageflow Used: Yes
- Relevant Features Used: Guard/transform/work pipelines, scoped idempotency, prompt-security inspection before provider calls, typed output validation, pipeline-run logging, provider-call logging, and explicit per-pipeline timeout budgeting for generation.
- What Worked: The same pipeline shape scaled cleanly to catalog generation, and Stageflow kept the provider-backed path observable and replayable.
- What Hurt: The default timeout interceptor and callable-stage typing remain awkward for long-running generation stages and async callables.
- Follow-Up Logged In `ops/process/stageflow-reporting.md`: Yes

## Technical And Architectural Debt

| Debt Item | Type | Why It Exists | Impact | Recommended Follow-Up | Owner |
| --- | --- | --- | --- | --- | --- |
| Generic typed output helper still lives under the practice module | Architectural | Sprint 6 reused the existing `PromptLibrary` and `TypedLLMOutput` implementation instead of extracting a shared platform module mid-sprint | Cross-feature reuse now points through the practice package, which is semantically awkward | Move prompt-library and typed-output helpers into a shared platform location before a third provider-backed feature reuses them | Backend |
| Discovery filtering computes actor-aware view state in Python | Technical | The sprint optimized for correctness and clear contracts instead of query-level optimization | Large catalogs could eventually pay unnecessary per-record query cost for save counts and discovery-tier rendering | Introduce catalog read-model queries or repository helpers once scale or admin listing breadth justifies it | Backend |
| Smoke still uses manual runtime fixtures for assessment modes | Test | Using generated content for both generation verification and assessment verification made the smoke path less deterministic | The smoke proves generation endpoints and assessment modes in one run, but not assessment-on-generated-content in the same command | Add a second smoke variant or post-generation runtime assertions once provider behavior is stable enough for that broader proof | Backend |

## Open Risks

| Risk | Severity | Why It Matters | Mitigation | Carry To Next Sprint |
| --- | --- | --- | --- | --- |
| Generation quality still depends on prompt discipline rather than stronger post-generation realism scoring | Medium | Typed validity is necessary but not sufficient for editorial quality | Keep drafts editable, preserve artifacts, and tighten realism scoring/verification in the next governance sprint | Yes |
| Save/discovery queries are still synchronous read paths over the primary tables | Low | Actor-aware catalog rendering may grow more expensive as content volume increases | Track query pressure and split a read model only if catalog volume or admin listing breadth justifies it | Yes |
| Generation pipelines now need explicit timeout budgets | Low | Future provider/model changes could shift latency again and reintroduce timeout tuning work | Keep the timeout override local to generation and revisit once Stageflow exposes a better per-pipeline config surface | Yes |

## Deferred Work

- Admin-facing verification workflow UX and richer verification-state transitions beyond the current admin patch path
- Generation-time editorial scoring or quality ranking beyond contract validation and publish-time checks
- Using generated content directly inside the smoke runtime assertions for all practice modes

## Retrospective

- Stop: Treating provider-backed smoke as a copy-paste extension of the assessment smoke when generation has materially different latency and schema-risk characteristics.
- Start: Isolating the minimum reliable real-provider proof for each new flow before expanding smoke breadth.
- Continue: Building each backend slice as typed contracts plus migrations, observability, tests, and docs in the same change.

## Next Sprint Recommendations

1. Build the explicit admin verification workflow on top of the new verified/public discovery contract instead of mutating verification state ad hoc.
2. Extract shared prompt-library and typed-output helpers out of the practice module before more provider-backed workflows accumulate.
3. Add richer audit/replay inspection endpoints for generation artifacts so admin trust and verification work can use them directly.

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
