# Sprint Execution Report: Sprint 5: Progression And Recommendation V1

> Project: SoftSkills
> Report Type: Sprint execution retrospective and delivery report
> Output Location: `ops/reports/sprint-05-progression-and-recommendation-v1-report.md`
> Scope: Backend and platform execution only. Frontend work is tracked separately.

## Report Overview

- Sprint Name: Sprint 5: Progression And Recommendation V1
- Sprint Window: 2026-03-25 -> 2026-03-26
- Sprint Status: Completed
- Report Author: Codex
- Related Sprint Doc: [ops/sprints/sprint-05-progression-and-recommendation-v1.md](/home/antonioborgerees/df/soft-skills/ops/sprints/sprint-05-progression-and-recommendation-v1.md)
- Related Branch / PR: `sprint/05-progression-and-recommendation-v1`

## Source Docs Used

- [ops/CONSTITUTION.yml](/home/antonioborgerees/df/soft-skills/ops/CONSTITUTION.yml)
- [ops/process/sprint-execution.md](/home/antonioborgerees/df/soft-skills/ops/process/sprint-execution.md)
- [ops/process/stageflow-reporting.md](/home/antonioborgerees/df/soft-skills/ops/process/stageflow-reporting.md)
- [ops/mvp-spec/platform/assessment-and-progression.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/platform/assessment-and-progression.md)
- [ops/mvp-spec/platform/soft-skill-progression.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/platform/soft-skill-progression.md)
- [ops/mvp-spec/platform/soft-skill-recommendation.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/platform/soft-skill-recommendation.md)
- [ops/mvp-spec/engines/progression-engine.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/engines/progression-engine.md)
- [ops/mvp-spec/engines/recommendation-engine.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/engines/recommendation-engine.md)
- [ops/mvp-spec/foundational/stageflow-guide.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/stageflow-guide.md)

## Sprint Summary

- Sprint Goal: Turn validated assessments into meaningful learner progress state and evidence-based next-practice recommendations.
- Actual Outcome: Delivered a dedicated progression module with replayable skill and competency aggregation, persisted progression snapshots and recommendation artifacts, automatic progression refresh after validated assessments, learner-facing progress APIs, admin recalculation scaffolding, migration support, and real-provider smoke confirmation for the full assessment -> progress -> recommendation chain.
- Overall Result: The sprint goal is complete. The backend now maintains explainable progress state and next-step guidance from validated assessment history with durable artifacts, typed contracts, Stageflow orchestration, and passing verification.

## Planned Vs Delivered

| Area | Planned | Delivered | Status | Notes |
| --- | --- | --- | --- | --- |
| Progression ingestion | Update skill state from validated assessments only | Added validated-assessment ingestion into a dedicated progression workflow triggered from assessment completion | Done | Rejected or failed assessments do not update progress |
| Skill and competency state | Aggregate skills, confidence, and competency projections with explainability | Implemented deterministic score normalization, decay-weighted aggregation, confidence bands, competency weighting, gating rules, and evidence-ledger contributions | Done | Config and schema versions are stored on every snapshot |
| Recommendation generation | Rank next-practice content from weaknesses, stagnation, and goals | Added candidate retrieval from the catalog, composite scoring, reason codes, cooldown handling, and persisted recommendation artifacts | Done | Output includes alternatives and component breakdowns |
| Replay and audit | Add recalculation-ready scaffolding and durable audit records | Added recalculation records, synchronous replay refresh, diff summaries, and recalculation events | Done | Heavy async checkpoint/replay jobs are still deferred |
| API surface | Expose progress and recommendation state to the learner and recalculation to admins | Added `/api/progress/me`, `/api/progress/me/recommendations`, and `/api/progress/recalculate` | Done | Route handlers remain thin |
| Smoke verification | Prove the full chain with a real provider | Ran backend smoke successfully against the live provider config on 2026-03-26 | Done | Provider was `openrouter`, model `openai/gpt-oss-20b:free` |

## Key Outcomes

- The backend now recomputes progression and recommendations automatically after validated assessment persistence.
- Progress artifacts are durable, replayable, versioned, and explainable down to contributing assessment IDs and quotes.
- Recommendations are no longer ad hoc content suggestions; they are evidence-driven artifacts with reason codes and scored candidates.
- Admin-triggered recalculation exists as a typed, auditable backend workflow instead of an implicit manual operation.
- The full backend test suite stayed green after the new module, migration, and routing changes.

## What Worked Well

- Adding a dedicated `modules/progression` slice preserved clear feature boundaries instead of overloading the practice module.
- Reusing the existing catalog, learner profile, and validated assessment records made the first recommendation version tractable without inventing new persistence models.
- Inline progression refresh after assessment persistence kept the first implementation simple and made integration testing straightforward.
- The existing smoke harness scaled cleanly to verify the new chain once the credentials were confirmed in `backend/.env`.

## Challenges And Friction

- The repo still requires `PYTHONPATH=src` for reliable local verification because the environment can otherwise resolve a stale editable package before this checkout.
- SQLite returns mixed naive/aware datetime values during tests, so the progression engine had to normalize timestamps explicitly before decay and recency calculations.
- Recommendation scoring needed a lighter repeat penalty than the first pass, otherwise the immediate post-assessment candidate set could fail closed in small fixture datasets.
- Recalculation is audit-ready but still synchronous, which is acceptable for single-learner V1 usage but not for heavier backfills or multi-learner repair runs.

## Constitution Conformance

- Competency growth: The sprint closes the `practice -> assess -> reflect -> progress -> repeat` loop by converting validated assessments into persisted progress state and targeted next practice.
- Schema validation: New progression commands, read views, persistence payloads, recommendation outputs, and recalculation contracts are typed and validated.
- Fail-fast behavior: Missing validated history, missing candidates, invalid artifacts, and non-validated assessment sources fail closed with explicit application errors.
- Explainability: Skill states persist contributing assessments, normalized scores, weights, quotes, and competency gating reasons; recommendations persist reason codes and component breakdowns.
- Observability: Added progression snapshot, recommendation generation, recalculation started, and recalculation completed events, plus Stageflow pipeline-run logs and workflow IDs for the new workflows.
- Persistence: Added durable snapshot, recommendation, and recalculation tables plus a migration for schema evolution discipline.
- Modularity: Routes stayed thin; business rules live in progression domain code; Stageflow orchestration lives in progression workflows; persistence stays in feature infra and platform DB models.
- No silent fallback: Recommendation generation fails closed when no valid candidates remain, and progression updates only run from validated assessments.

## Testing And Verification

- Unit Tests: Added deterministic coverage for progression aggregation, confidence behavior, competency gating, recommendation ranking, and empty-candidate fail-closed behavior in `backend/tests/unit/test_progression_domain.py`.
- Integration Tests: Added `backend/tests/integration/test_progression_api.py` for learner progress reads, recommendation reads, and admin recalculation; extended `backend/tests/integration/test_quick_practice_attempts.py` to assert automatic snapshot and recommendation persistence and event emission.
- Smoke Tests With Real Provider: Ran `cd backend && make smoke` successfully on 2026-03-26. Result:
  - provider: `openrouter`
  - model slug: `openai/gpt-oss-20b:free`
  - quick practice overall score: `4`
  - interview overall score: `3`
  - scenario overall score: `3`
- Failure Path Coverage: Covered rejected assessments, provider failure, recommendation empty-candidate rejection, missing validated history, and replay audit persistence.
- Manual Verification:
  - `cd backend && PYTHONPATH=src pytest -q`
  - `cd backend && make smoke`

## Documentation Updates

- [ops/sprints/sprint-05-progression-and-recommendation-v1.md](/home/antonioborgerees/df/soft-skills/ops/sprints/sprint-05-progression-and-recommendation-v1.md)
- [ops/process/stageflow-reporting.md](/home/antonioborgerees/df/soft-skills/ops/process/stageflow-reporting.md)
- [ops/reports/sprint-05-progression-and-recommendation-v1-report.md](/home/antonioborgerees/df/soft-skills/ops/reports/sprint-05-progression-and-recommendation-v1-report.md)

## Stageflow Usage And Reporting

- Stageflow Used: Yes
- Relevant Features Used: Guard/transform/enrich/work pipelines, request correlation, persisted pipeline-run logs, idempotency support, structured workflow events, and nested workflow orchestration from the assessment path into progression refresh.
- What Worked: Stageflow continued to fit the vertical-slice approach well. The progression refresh pipeline stayed explicit and replayable, and the existing logging/idempotency infrastructure reused cleanly.
- What Hurt: Progression refresh currently runs inline after assessment completion, so the submit path now includes a nested Stageflow pipeline. That is acceptable for V1 but increases latency coupling between assessment and recommendation readiness.
- Follow-Up Logged In `ops/process/stageflow-reporting.md`: Yes

## Technical And Architectural Debt

| Debt Item | Type | Why It Exists | Impact | Recommended Follow-Up | Owner |
| --- | --- | --- | --- | --- | --- |
| Inline progression refresh on assessment submit | Architectural | The first version optimizes for simplicity and immediate consistency by running progression synchronously after assessment persistence | Assessment latency now includes progression/recommendation work and recalculation reuse is limited to small workloads | Move refresh/recalc to an async workflow trigger with explicit checkpoint/replay support once operational tooling exists | Backend |
| Hard-coded progression and recommendation config versions in code | Technical | The sprint needed stable versioned semantics before a separate config-loading layer existed | Future tuning requires code edits instead of config-only rollouts | Externalize progression and recommendation weight/config artifacts into reviewed source-controlled config files | Backend |
| Recommendation candidate retrieval reuses existing catalog visibility instead of a dedicated recommendation view | Architectural | The MVP uses current collection/prompt/scenario records directly to stay within sprint scope | Recommendation-specific policy filters may get crowded into the repo layer over time | Introduce a catalog recommendation adapter/view when content governance grows in Sprint 6+ | Backend |

## Open Risks

| Risk | Severity | Why It Matters | Mitigation | Carry To Next Sprint |
| --- | --- | --- | --- | --- |
| Synchronous recalculation does not scale to larger replay windows | Medium | Admin repair or config drift backfills will eventually need batch-safe replay rather than per-request recompute | Keep the current recalculation scoped to single-learner V1 use and add heavy-job orchestration later | Yes |
| Recommendation quality is still heuristic and uncalibrated | Medium | The scoring model is explainable and deterministic, but it has not yet been tuned against real learner-outcome data | Preserve weights/config versions and add offline replay/effectiveness analysis in later sprints | Yes |
| Current smoke harness proves provider-backed assessment flows, but not persisted progress content inspection | Low | The smoke confirms the chain ran end to end but does not yet assert the learner-facing progress payload contents inside the smoke command | Add post-smoke API assertions for `/api/progress/me` once smoke output shape is expanded | Yes |

## Deferred Work

- Heavy async checkpoint/replay infrastructure for progression backfills and wider recalculation jobs
- External config artifacts for progression decay profiles and recommendation weight sets
- Richer recommendation policy inputs such as prerequisite graphs and admin overrides beyond the current MVP heuristics

## Retrospective

- Stop: Treating smoke completion alone as enough evidence for new workflow quality when richer artifact-level assertions could be added cheaply.
- Start: Externalizing versioned progression and recommendation configs before tuning work begins in earnest.
- Continue: Building new backend slices as explicit modules with typed contracts, durable artifacts, and focused integration coverage.

## Next Sprint Recommendations

1. Build on the stable recommendation inputs by improving catalog/creator workflows without breaking the new contracts.
2. Move progression and recommendation semantics into reviewed external config artifacts before tuning or governance work expands.
3. Introduce async replay infrastructure for recalculation before any multi-learner backfill or drift-repair use case lands.

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
