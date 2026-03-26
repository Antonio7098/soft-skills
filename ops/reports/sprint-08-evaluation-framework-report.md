# Sprint Execution Report: Sprint 8: Evaluation Framework

> Project: SoftSkills
> Report Type: Sprint execution retrospective and delivery report
> Output Location: `ops/reports/sprint-08-evaluation-framework-report.md`
> Scope: Backend and platform execution only. Frontend work is tracked separately.

## Report Overview

- Sprint Name: Sprint 8: Evaluation Framework
- Sprint Window: 2026-03-26 -> 2026-03-26
- Sprint Status: Completed
- Report Author: Codex
- Related Sprint Doc: [ops/sprints/sprint-08-evaluation-framework.md](/home/antonioborgerees/df/soft-skills/ops/sprints/sprint-08-evaluation-framework.md)
- Related Branch / PR: `working tree`

## Source Docs Used

- [ops/CONSTITUTION.yml](/home/antonioborgerees/df/soft-skills/ops/CONSTITUTION.yml)
- [ops/process/sprint-execution.md](/home/antonioborgerees/df/soft-skills/ops/process/sprint-execution.md)
- [ops/process/sprint-template.md](/home/antonioborgerees/df/soft-skills/ops/process/sprint-template.md)
- [ops/process/stageflow-reporting.md](/home/antonioborgerees/df/soft-skills/ops/process/stageflow-reporting.md)
- [ops/mvp-spec/foundational/stageflow-guide.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/stageflow-guide.md)
- [ops/mvp-spec/engines/marking-engine.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/engines/marking-engine.md)
- [ops/mvp-spec/operations/observability-and-operations.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/operations/observability-and-operations.md)

## Sprint Summary

- Sprint Goal: Build one provider-backed evaluation framework that benchmarks LLM marking quality against a reviewed, versioned golden dataset.
- Actual Outcome: Delivered a marking-only evaluation framework with versioned golden dataset artifacts, Stageflow-backed orchestration, persisted run and case-result records, a real admin API surface, real-provider execution, token and latency capture, and replayable run metadata.
- Overall Result: The sprint goal is complete. The framework now evaluates real marking models instead of local validators and produces persisted evidence for model comparison over time.

## Planned Vs Delivered

| Area | Planned | Delivered | Status | Notes |
| --- | --- | --- | --- | --- |
| Eval scope | Build a robust eval system | Narrowed to one responsibility: LLM marking evaluation against a golden dataset | Done | Progression and recommendation were intentionally removed from scope |
| Golden dataset | Create benchmark cases | Externalized reviewed marking cases into a versioned artifact | Done | Dataset is now a first-class artifact instead of in-code fixtures |
| Real provider execution | Evaluate actual models | Runs now execute through the real marking provider path and Stageflow workflow | Done | This replaced the earlier incorrect contract-only benchmark shape |
| Operator surface | Make eval runnable | Added admin API endpoints for suite listing, run execution, run listing, and run inspection | Done | Route surface is `/api/admin/evaluations/*` |
| Persistence and metrics | Persist enough detail for model comparison | Persisted run summaries, per-case outputs, prompt/model/provider metadata, token usage, latency, and raw payloads | Done | Estimated cost works when pricing coverage exists for the model slug |
| Documentation and reporting | Rewrite sprint docs honestly | Sprint doc rewritten, old incorrect report removed, final execution report added | Done | Report now reflects the corrected scope and live runs |

## Key Outcomes

- The evaluation framework now has one job: benchmark marking models against a reviewed golden dataset.
- The benchmark path uses the real LLM provider integration rather than local contract validation.
- A versioned golden dataset exists at [marking_golden_dataset.v1.json](/home/antonioborgerees/df/soft-skills/backend/src/soft_skills_backend/modules/evaluation/artifacts/marking_golden_dataset.v1.json).
- The eval runner is exposed through the admin API:
  - `GET /api/admin/evaluations/suites`
  - `GET /api/admin/evaluations/runs`
  - `GET /api/admin/evaluations/runs/{run_id}`
  - `POST /api/admin/evaluations/runs`
- Runs are Stageflow-orchestrated and persisted with enough detail to compare models across time.
- The framework captures operational metrics that matter for evaluation decisions:
  - pass rate
  - score-band agreement
  - evidence coverage
  - latency
  - prompt, completion, and total tokens
  - estimated cost when pricing is configured for the evaluated model

## What Worked Well

- Collapsing scope to marking-only made the framework coherent. It now measures the thing that actually matters for model iteration.
- Reusing the real marking pipeline preserved fidelity between production behavior and evaluation behavior.
- Stageflow remained a good orchestration fit because the eval path needed durable events, provider-call logging, and replayable workflow metadata.
- Persisting raw payloads alongside accepted assessments makes later audit and rubric tuning practical instead of speculative.

## Challenges And Friction

- The initial implementation drifted into “contract evaluation,” which was not the real product need and had to be removed.
- The first real-provider run used `openai/gpt-oss-20b:free` and failed across all cases with `SS-PROVIDER-005`, which exposed provider/model reliability issues before quality measurement could even start.
- The first pricing artifact only covered the free model slug, so non-free runs captured tokens but not estimated cost yet.
- Evaluation persistence currently shares the main application database path, which is workable for now but not the right long-term boundary.
- Direct service execution currently still accepts an `Actor`, which is convenient for API symmetry but not the cleanest interface for system- or CI-triggered evals.

## Constitution Conformance

- Competency growth: The product outcome is unchanged. The framework evaluates the quality of the marking system that feeds learner progression, rather than adding unrelated infrastructure theater.
- Schema validation: Eval commands, views, and persisted artifacts are typed. Marking outputs are still validated before being accepted as benchmark results.
- Fail-fast behavior: Provider failures, malformed outputs, and validation failures persist with explicit status and error codes.
- Explainability: Run records preserve dataset version, suite version, provider, model slug, prompt and rubric metadata, actual assessment payloads, and raw provider payloads.
- Observability: Stageflow workflow ids, trace ids, pipeline run ids, workflow events, and provider-call logs remain part of the eval path.
- Persistence: Run-level and case-level results are durably persisted and can be inspected after the run completes.
- Modularity: Route handlers stay thin; the benchmark logic lives in the evaluation module; provider access remains behind the existing marking provider boundary.
- No silent fallback: The framework does not silently substitute local grading for provider execution. Failed provider runs are recorded honestly as failed eval runs.

## Testing And Verification

- Unit Tests: `backend/tests/unit/test_evaluation_domain.py`
- Integration Tests: `backend/tests/integration/test_evaluation_api.py`
- Full Backend Suite:
  - `cd backend && PYTHONPATH=src pytest tests -q`
  - Result: `62 passed, 1 skipped`
- Real Provider Runs:
  - First live run on 2026-03-26 against `openai/gpt-oss-20b:free`
  - Persisted run id: `f3d87e6ce91b44659230b714c71b8edb`
  - Outcome: failed baseline with `SS-PROVIDER-005` on all 3 cases
  - Follow-up live run on 2026-03-26 against `openai/gpt-oss-20b`
  - Persisted run id: `c5b0a54d8789411e90bf97940d7acd06`
  - Outcome: passed all 3 golden cases

## Live Benchmark Results

### Failure Baseline

Executed on 2026-03-26 against provider `openrouter` with model slug `openai/gpt-oss-20b:free`.

- Evaluation run id: `f3d87e6ce91b44659230b714c71b8edb`
- Result: failed
- Aggregate observations:
  - pass rate: `0.0`
  - average latency ms: `30815.67`
  - validation error rate: `1.0`
  - total tokens: `0`
  - estimated cost usd: `0.0`
- Interpretation: this run established a persisted provider-failure baseline and proved the framework records failures honestly instead of masking them

### Passing Benchmark

Executed on 2026-03-26 against provider `openrouter` with model slug `openai/gpt-oss-20b`.

- Evaluation run id: `c5b0a54d8789411e90bf97940d7acd06`
- Result: passed
- Aggregate observations:
  - case count: `3`
  - passed case count: `3`
  - pass rate: `1.0`
  - average latency ms: `6975.67`
  - average overall score absolute error: `0.0`
  - average skill score absolute error mean: `0.0`
  - average evidence coverage rate: `1.0`
  - validation error rate: `0.0`
  - total prompt tokens: `1024`
  - total completion tokens: `2207`
  - total tokens: `3231`
  - estimated cost usd: `null`
- Interpretation: the non-free model/provider path is viable for this dataset and currently produces a clean pass across the initial reviewed cases

## Documentation Updates

- [ops/sprints/sprint-08-evaluation-framework.md](/home/antonioborgerees/df/soft-skills/ops/sprints/sprint-08-evaluation-framework.md)
- [ops/process/stageflow-reporting.md](/home/antonioborgerees/df/soft-skills/ops/process/stageflow-reporting.md)
- [ops/reports/sprint-08-evaluation-framework-report.md](/home/antonioborgerees/df/soft-skills/ops/reports/sprint-08-evaluation-framework-report.md)

## Stageflow Usage And Reporting

- Stageflow Used: Yes
- Relevant Features Used: workflow execution, durable event logging, pipeline-run correlation, provider-call logging, timeout budgeting for long-running provider stages
- What Worked: Stageflow kept the provider-backed eval flow observable and replayable without adding feature-specific orchestration code
- What Hurt: Real-provider evals need explicit timeout budgeting, and long-running model calls make failure and retry handling more visible than in test doubles
- Follow-Up Logged In `ops/process/stageflow-reporting.md`: Yes

## Technical And Architectural Debt

| Debt Item | Type | Why It Exists | Impact | Recommended Follow-Up | Owner |
| --- | --- | --- | --- | --- | --- |
| Eval persistence shares the main app database path | Architectural | Sprint delivery optimized for speed and reuse of the existing persistence setup | Eval runs and raw payloads are not fully isolated from operational data concerns | Introduce `EVAL_DATABASE_URL` or equivalent separate storage and move eval persistence onto an isolated database path | Backend |
| Direct eval execution still requires an `Actor` shape | Architectural | The eval service currently mirrors the admin API boundary | System and CI launches have to synthesize an admin actor even when no user is actually involved | Add first-class eval trigger metadata for `user`, `system`, and `ci` without requiring a user account | Backend |
| Pricing coverage is incomplete | Technical | Initial pricing artifact only included the first model slugs used during bring-up | Estimated cost can remain `null` even when token usage is captured | Expand the pricing registry and keep it versioned alongside the dataset | Backend |

## Open Risks

| Risk | Severity | Why It Matters | Mitigation | Carry To Next Sprint |
| --- | --- | --- | --- | --- |
| Golden dataset coverage is still small | High | A 3-case benchmark is useful for bring-up but not enough for model-selection decisions | Expand reviewed cases and add dataset governance before using the framework for serious provider comparisons | Yes |
| Pricing registry drift can hide cost comparisons | Medium | Cost is one of the main operator metrics and missing entries weaken decision quality | Maintain model pricing as a versioned artifact and review it alongside model changes | Yes |
| Shared DB path can complicate retention and isolation | Medium | Eval payloads and run histories have different operational concerns than learner data | Split eval storage onto a dedicated database path in a follow-up sprint | Yes |

## Deferred Work

- Split eval persistence onto a dedicated eval database or equivalent isolated storage path
- Add first-class system and CI triggers so eval runs do not conceptually depend on user identities
- Expand the golden dataset and define review/versioning workflow for benchmark revisions
- Add broader model pricing coverage, including the configured non-free `openai/gpt-oss-20b` rates

## Retrospective

- Stop: Calling contract validation an evaluation framework when the real goal is model benchmarking.
- Start: Treating the golden dataset, pricing registry, and run metadata as versioned operator artifacts from the beginning.
- Continue: Running at least one real-provider benchmark during the sprint so the system is proven against actual provider behavior rather than only test doubles.

## Next Sprint Recommendations

1. Expand the golden dataset so benchmark results are decision-grade rather than bring-up-grade.
2. Isolate eval persistence from the main application database path.
3. Add richer run comparison and operator inspection views on top of the persisted eval records.

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
