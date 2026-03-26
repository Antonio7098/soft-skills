# Sprint 8: Evaluation Framework

> Project: SoftSkills
> Scope: Backend and platform execution only. Frontend planning is tracked separately.

## Sprint Overview

- Sprint Name: Sprint 8: Evaluation Framework
- Sprint Focus: Build one provider-backed evaluation framework for LLM marking quality against a versioned golden dataset
- Depends On: Sprint 7

## Relevant Source Docs

- [CONSTITUTION.yml](/home/antonioborgerees/df/soft-skills/ops/CONSTITUTION.yml)
- [ops/mvp-spec/README.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/README.md)
- [foundational/stageflow-guide.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/stageflow-guide.md)
- [engines/marking-engine.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/engines/marking-engine.md)
- [operations/observability-and-operations.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/operations/observability-and-operations.md)

## Sprint Goals

- Primary Goal: Evaluate real marking models against a reviewed golden dataset and persist the results so model quality can be compared over time.
- Secondary Goals:
  - Version the dataset, suite metadata, and persisted run artifacts so every result is explainable and replayable.
  - Record useful operator metrics per case and per model, including pass rate, score error, latency, tokens, and estimated cost.
  - Support model-sweep execution over a chosen set of golden cases without dragging progression or recommendation into the framework.

## Scope Checklist

- [x] Task 1: Replace the generic eval scaffolding with a marking-only, provider-backed evaluation flow
- [x] Task 2: Externalize the initial golden dataset into a versioned artifact instead of embedding benchmark cases in code paths
- [x] Task 3: Allow one run to evaluate `x` models over `y` selected golden dataset entries
- [x] Task 4: Persist run-level and case-level results with model metadata, latency, token usage, estimated cost, and score-quality metrics
- [x] Task 5: Expose the eval runner through the admin API and keep it Stageflow-orchestrated
- [x] Task 6: Run a real provider-backed benchmark and record the outcome
- [x] Task 7: Rewrite sprint documentation to reflect the corrected scope and delete the incorrect sprint report

## Delivered Design

### 1. Single Responsibility

- The evaluation framework now does one thing only: judge LLM marking quality against a versioned golden dataset.
- Progression and recommendation eval logic was removed from the framework scope.
- Contract-only “evaluation” of marking outputs was removed as the primary eval path. Contract validation still exists as an acceptance guard for model outputs, but it is no longer the thing being benchmarked.

### 2. Versioned Golden Dataset

- Added a versioned golden dataset artifact:
  - `backend/src/soft_skills_backend/modules/evaluation/artifacts/marking_golden_dataset.v1.json`
- Added a pricing artifact for cost estimation:
  - `backend/src/soft_skills_backend/modules/evaluation/artifacts/model_pricing.v1.json`
- Dataset selection is explicit and validated by case id.

### 3. Provider-Backed Marking Eval

- The benchmark runner now calls the real assessment-marking provider path, not a local contract validator pretending to be an eval.
- Each case is rendered through the same marking prompt stack used by the application.
- Model outputs are scored against golden expectations using:
  - overall score band error
  - skill score band error
  - skill band pass rate
  - evidence coverage rate
  - accepted output rate

### 4. Model Sweep And Persistence

- One run can execute across multiple models and a selected subset of dataset entries.
- Runs and case results persist through the existing evaluation tables.
- Persisted metrics include:
  - pass/fail
  - latency
  - prompt tokens
  - completion tokens
  - total tokens
  - estimated cost
  - score-error metrics
  - raw provider payload and actual assessment payload where available

### 5. Orchestration And API

- The evaluation flow remains Stageflow-orchestrated.
- Admin API endpoints remain the operator surface:
  - `GET /api/admin/evaluations/suites`
  - `GET /api/admin/evaluations/runs`
  - `GET /api/admin/evaluations/runs/{run_id}`
  - `POST /api/admin/evaluations/runs`

## Constitution And Quality Checklist

- [x] Competency growth remains the product outcome, but evaluation now measures the real marking model rather than local validators
- [x] New external boundaries are typed and schema-validated
- [x] Fail-fast and fail-loud behavior is preserved with stable error codes
- [x] Route handlers remain thin; orchestration lives in Stageflow workflows
- [x] Dependency injection and provider boundaries remain explicit
- [x] Critical workflow artifacts are durably persisted
- [x] Traces, logs, and events cover the evaluation workflow
- [x] Prompt version, dataset version, model slug, provider, and token/cost metadata are preserved where available
- [x] Marking outputs remain explainable because actual assessments and raw payloads are stored with case results
- [x] No fake “contract evaluation” remains as the primary benchmark path

## Testing And Verification Checklist

- [x] Unit Tests: golden dataset selection and metric aggregation
- [x] Integration Tests: admin API run persistence for provider-backed model sweeps using fake providers
- [x] Full Backend Suite: `PYTHONPATH=src pytest tests -q` passed with `62 passed, 1 skipped`
- [x] Real Provider Run: executed the live benchmark against `openai/gpt-oss-20b:free`
- [x] Documentation Updated: sprint doc rewritten and incorrect report deleted

## Live Benchmark Result

Executed on 2026-03-26 against provider `openrouter` with model slug `openai/gpt-oss-20b:free`.

- Evaluation run id: `f3d87e6ce91b44659230b714c71b8edb`
- Suite: `marking_benchmark_v1`
- Dataset: `marking-golden-dataset.v1`
- Selected cases: 3
- Result: failed

Observed aggregate metrics:

- pass rate: `0.0`
- average latency ms: `30815.67`
- validation error rate: `1.0`
- total tokens: `0`
- estimated cost usd: `0.0`

Observed case failures:

- all 3 cases failed with `SS-PROVIDER-005`
- provider returned no token usage before failure
- this first live run therefore established a persisted provider-failure baseline, not a passing quality baseline

## Success Criteria

- [x] The framework evaluates real marking models against a versioned golden dataset
- [x] The framework can run a model sweep over a selected set of golden entries
- [x] Runs are persisted with enough metadata to compare models and track progress over time
- [x] Operators can inspect case-level quality, latency, tokens, and cost signals from persisted results
- [x] The first live provider-backed benchmark run completed and was recorded honestly, even though the model/provider combination failed

Minimum Viable Sprint:
One real provider-backed golden-dataset marking eval path exists, is runnable through the backend, persists results, and records enough metadata to compare model behavior over time.

## Risks And Follow-Up

| Risk | Impact | Mitigation | Status |
| --- | --- | --- | --- |
| Golden dataset coverage is still small | High | Expand reviewed cases and add governance around dataset revisions | Open |
| Pricing coverage is currently narrow | Medium | Extend the pricing registry beyond the initial free-model entry set | Open |
| Provider/model combinations may fail before returning usage or tokens | High | Keep failed runs persisted, improve retry strategy, and compare alternative providers/models | Open |
| Long provider-backed evals need explicit Stageflow timeout budgeting | Medium | Keep evaluation workflows on an explicit long timeout budget | Mitigated |

## Sprint Notes

```text
- The earlier generic eval design was wrong for the actual goal and was replaced.
- This sprint now treats evaluation as model benchmarking, not contract validation.
- Progression and recommendation are no longer part of this framework.
- The framework uses the installed stageflow-core runtime and the real marking provider path.
- Versioned artifacts now exist for the golden dataset and pricing registry.
- The first live run against openai/gpt-oss-20b:free completed and persisted a provider-failure result with SS-PROVIDER-005 across all cases.
```

## Review And Sign-Off

- Sprint Status: Completed
- Completion Date: 2026-03-26

Checklist:

- [x] Primary goal achieved
- [x] Constitution and quality checks passed
- [x] Unit tests completed
- [x] Integration tests completed
- [x] Real provider benchmark executed
- [x] Documentation updated
- [ ] Code review completed

Next Sprint Priorities:

1. Expand and curate the golden dataset so model comparisons are decision-grade.
2. Add richer pricing coverage and better surfacing of provider failure diagnostics.
3. Compare multiple real models against the same dataset and start tracking trend lines across runs.
