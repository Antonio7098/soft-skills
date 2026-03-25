# Sprint Execution Report: Sprint 3: Quick Practice Vertical Slice

> Project: SoftSkills
> Report Type: Sprint execution retrospective and delivery report
> Output Location: `ops/reports/sprint-03-quick-practice-vertical-slice-report.md`
> Scope: Backend and platform execution only. Frontend work is tracked separately.

## Report Overview

- Sprint Name: Sprint 3: Quick Practice Vertical Slice
- Sprint Window: 2026-03-25 -> 2026-03-25
- Sprint Status: Completed
- Report Author: Codex
- Related Sprint Doc: [ops/sprints/sprint-03-quick-practice-vertical-slice.md](/home/antonioborgerees/df/soft-skills/ops/sprints/sprint-03-quick-practice-vertical-slice.md)
- Related Branch / PR: `sprint/03-quick-practice-vertical-slice`

## Source Docs Used

- [ops/CONSTITUTION.yml](/home/antonioborgerees/df/soft-skills/ops/CONSTITUTION.yml)
- [ops/process/sprint-execution.md](/home/antonioborgerees/df/soft-skills/ops/process/sprint-execution.md)
- [ops/mvp-spec/foundational/product-spec.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/product-spec.md)
- [ops/mvp-spec/platform/assessment-and-progression.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/platform/assessment-and-progression.md)
- [ops/mvp-spec/engines/marking-engine.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/engines/marking-engine.md)
- [ops/mvp-spec/operations/observability-and-operations.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/operations/observability-and-operations.md)
- [ops/mvp-spec/foundational/stageflow-guide.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/stageflow-guide.md)

## Sprint Summary

- Sprint Goal: Deliver the first complete backend quick-practice loop from prompt delivery to validated feedback persistence.
- Actual Outcome: Delivered quick-practice session start, durable attempt lifecycle persistence, provider-backed assessment orchestration, strict structured-output validation, explainable learner feedback payloads, wide workflow events, and a real-provider smoke harness for the same backend path.
- Overall Result: The quick-practice vertical slice is implemented and verified with unit, integration, lint, and type checks. The real-provider smoke runs through the built LLM provider adapter and backend quick-practice flow and now completes successfully within the bounded timeout budget.

## Planned Vs Delivered

| Area | Planned | Delivered | Status | Notes |
| --- | --- | --- | --- | --- |
| Session start | Session creation and prompt delivery contracts | Added `POST /api/attempts/quick-practice/sessions` and persisted session plus initial attempt | Done | Prompt delivery now has a durable backend contract |
| Attempt lifecycle | Submission, lifecycle transitions, durable state | Added persisted attempt statuses and explicit transition guards | Done | Invalid resubmission fails with stable domain error |
| Marking orchestration | Explicit DAG, provider-backed structured output validation | Added fallback DAG executor, prompt library, typed output wrapper, bounded provider retry/backoff | Done | Preserves guard/enrich/transform/work boundaries without local Stageflow install |
| Feedback artifacts | Explainable learner payload plus durable storage | Added validated and rejected assessment persistence with version metadata and trace linkage | Done | Rejected outputs are stored separately from learner-facing validated artifacts |
| Observability | Wide events, traces, pipeline metadata, provider logs | Added quick-practice and assessment events plus pipeline run persistence | Done | Provider call logs are emitted by the real provider adapter |
| Real-provider smoke | End-to-end backend smoke | Added smoke harness that constructs `OpenAICompatibleLLMProvider` and drives the full quick-practice API path | Done | Executed against `openrouter`; current result completed successfully with provider-returned model slug `openai/gpt-5.4-nano-20260317` |

## Key Outcomes

- The backend now supports a full quick-practice text flow without frontend dependencies.
- Assessment artifacts are validated before user delivery and before downstream progress consumption.
- Failure modes are explicit: malformed or incomplete model output is rejected, provider failure marks the attempt failed, and invalid attempt transitions are blocked.
- The smoke harness now proves the real provider adapter path, not just config resolution, by instantiating the shared `OpenAICompatibleLLMProvider` and submitting a real quick-practice attempt through the backend.
- The real smoke surfaced a provider metadata mismatch: OpenRouter returned a canonical model slug different from the configured alias. Validation now compares normalized equivalent slugs and persists the execution-observed slug.
- The provider adapter now enforces a hard wall-clock timeout per completion request, and the smoke harness applies zero retries plus a hard outer timeout so provider regressions fail fast and loudly.
- After switching the configured OpenRouter model, the real-provider smoke completed successfully inside the enforced timeout budget.

## Constitution Conformance

- Competency growth: The slice strengthens the core `practice -> assess -> reflect -> progress -> repeat` loop with an actual assessable practice path.
- Schema validation: Request bodies, response bodies, persisted artifacts, and model output contracts are typed and validated.
- Fail-fast behavior: Invalid attempt transitions, malformed structured outputs, contradictory evidence, and missing metadata fail loudly with stable codes.
- Explainability: Feedback persists evidence, strengths, weaknesses, next actions, and skill-level scores.
- Observability: Practice and assessment workflows now emit structured events and persisted pipeline runs.
- Persistence: Sessions, attempts, validated assessments, and rejected assessment artifacts are stored durably under Alembic migration discipline.
- Modularity: Routes remain thin; business rules live in a dedicated practice service and supporting orchestration/domain modules.
- No silent fallback: Validation and evidence failures reject the assessment instead of degrading output.

## Testing And Verification

- Unit Tests: Added coverage for lifecycle transitions, evidence validation, contradiction detection, scoring guards, and typed-output retry behavior.
- Integration Tests: Added full start -> submit -> assess -> persist coverage plus rejected-output and provider-failure cases.
- Smoke Tests With Real Provider: Executed successfully against the backend-configured provider path. Result:
  - provider: `openrouter`
  - model slug: `openai/gpt-5.4-nano-20260317`
  - overall score: `5`
- Manual Verification:
  - `PYTHONPATH=src python - <<'PY' ... run_provider_smoke() ... PY`
  - `PYTHONPATH=src python -m pytest -q`
  - `PYTHONPATH=src python -m ruff check src tests`
  - `PYTHONPATH=src python -m mypy src`

## Documentation Updates

- [ops/sprints/sprint-03-quick-practice-vertical-slice.md](/home/antonioborgerees/df/soft-skills/ops/sprints/sprint-03-quick-practice-vertical-slice.md)
- [ops/mvp-spec/platform/assessment-and-progression.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/platform/assessment-and-progression.md)
- [ops/mvp-spec/operations/observability-and-operations.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/operations/observability-and-operations.md)
- [ops/reports/sprint-03-quick-practice-vertical-slice-report.md](/home/antonioborgerees/df/soft-skills/ops/reports/sprint-03-quick-practice-vertical-slice-report.md)

## Technical And Architectural Debt

| Debt Item | Type | Why It Exists | Impact | Recommended Follow-Up | Owner |
| --- | --- | --- | --- | --- | --- |
| Fallback DAG executor instead of installed Stageflow runtime | Architectural | `stageflow` is not installed in this environment | The workflow shape is explicit, but not using the real runtime package yet | Swap the fallback executor for real Stageflow pipeline definitions when the runtime is available | Backend |
| Quick-practice-only scope | Product | Sprint intentionally targeted the smallest vertical slice | Scenario/interview modes still need reuse of the same marking contract | Extend the same contract and persistence model in Sprint 4 | Backend |

## Open Risks

| Risk | Severity | Why It Matters | Mitigation | Carry To Next Sprint |
| --- | --- | --- | --- | --- |
| Provider metadata normalization may vary across models/providers | Medium | Different providers may return canonical model identifiers that differ from configured aliases | Keep validation tied to execution-observed metadata and add regression coverage for equivalent slug normalization | Yes |
| External provider latency may vary across models | Medium | Smoke coverage depends on bounded provider response time | Keep the smoke timeout budget explicit and use a model suitable for deterministic smoke runs | Yes |
| Broader practice modes may pressure the current prompt snapshot model | Medium | Scenario/interview payloads will be richer than quick-practice text | Reuse the same attempt/assessment core while widening the prompt payload shape deliberately | Yes |

## Deferred Work

- Reuse the marking contract for scenario and interview flows
- Add progression updates on top of the validated assessment artifact

## Next Sprint Recommendations

1. Extend the runtime to scenario and interview content using the same assessment artifact contract.
2. Reuse the same evidence-validation and feedback-validation rules across richer practice payloads.
3. Keep the smoke harness on the real provider adapter path as new provider-backed flows are added, and keep its timeout budget explicit.

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
