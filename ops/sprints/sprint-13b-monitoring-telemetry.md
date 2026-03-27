# Sprint 13b: Monitoring and Telemetry

> Project: SoftSkills
> Scope: Backend and platform execution only. Frontend planning is tracked separately.

## Sprint Overview

- Sprint Name: Monitoring and Telemetry
- Sprint Focus: Implement OpenTelemetry integration with OTLP exporter, distributed tracing, and health dashboard
- Depends On: Sprint 13a (Event Logging Infrastructure)

## Relevant Source Docs

- [CONSTITUTION.yml](/home/antonioborgerees/df/soft-skills/ops/CONSTITUTION.yml): lines 1-427
- [ops/mvp-spec/admin-dashboard-readiness.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/admin-dashboard-readiness.md): lines 60-122
- [ops/mvp-spec/foundational/stageflow-guide.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/stageflow-guide.md): lines 1-50

## Sprint Goals

- Primary Goal: Implement OpenTelemetry integration with OTLP exporter for unified traces + metrics
- Secondary Goals:
  - Wire StageflowTracer to interceptors
  - Deploy Tempo/Jaeger/Grafana stack via docker-compose
  - Add LLM span attributes

## Scope Checklist

- [x] Task 2.1: OpenTelemetry integration - `opentelemetry-sdk`, `opentelemetry-exporter-otlp`, wire `StageflowTracer` to interceptors
- [x] Task 2.2: OTLP endpoint configuration - Environment variable `OTEL_EXPORTER_OTLP_ENDPOINT`
- [x] Task 2.3: Span attributes enrichment - Add `pipeline.name`, `stage.name`, `pipeline.run_id`, `user_id`, `provider`, `model` to spans
- [x] Task 2.4: Trace context propagation - Ensure trace context flows through async boundaries and HTTP headers
- [x] Task 2.5: Tempo/Jaeger/Grafana stack - Docker-compose with OpenTelemetry backend
- [ ] Task 2.6: Distributed tracing UI - Connect admin dashboard to Jaeger/Tempo for trace visualization (deferred)
- [x] Task 2.7: Health dashboard endpoint - Extended `/health` with component status (DB, external services)
- [x] Task 2.8: LLM span attributes - Add `llm.operation`, `llm.provider`, `llm.model`, `llm.tokens` to spans
- [x] Task 2.9: Documentation updates for all changed behavior

## Constitution And Quality Checklist

- [ ] Competency growth remains the product outcome, not activity theater
- [ ] All new external boundaries are typed and schema-validated
- [ ] Fail-fast and fail-loud behavior is preserved with stable error codes
- [ ] Route handlers remain thin; business rules stay out of transport layers
- [ ] Dependency injection and adapter boundaries remain explicit
- [ ] Critical workflow artifacts are durably persisted where required
- [ ] Traces, logs, and events cover all changed workflow steps
- [ ] Prompt, rubric, model, and config versions are preserved where applicable

## Testing And Documentation Checklist

- [ ] Unit Tests: deterministic coverage for new domain logic, schemas, and validation rules
- [ ] Integration Tests: API, persistence, orchestration, and event/trace coverage for the sprint scope
- [ ] Smoke Tests With Real Provider: verify OTLP export and trace context propagation
- [ ] OpenTelemetry Tests: verify span context propagation, span attributes, OTLP export
- [ ] Documentation Updates: update canonical docs in `ops/`, the roadmap/sprint docs, and any affected contracts

## Success Criteria

- [ ] Primary sprint goal is met in a backend-usable form
- [ ] OpenTelemetry traces visible in Tempo/Jaeger
- [ ] Tests pass at unit, integration, and smoke level for the sprint scope
- [ ] Canonical docs reflect the implemented behavior

Minimum Viable Sprint:
Tasks 2.1-2.4 are the critical path (OTLP integration and span enrichment). Tasks 2.5-2.6 (docker-compose and UI) can be deferred if needed.

## Risks And Blockers

| Risk | Impact | Mitigation | Status |
| --- | --- | --- | --- |
| OpenTelemetry integration complexity | High | Go straight to OTLP; skip Prometheus intermediate step | Mitigated |
| Docker-compose for observability stack | Medium | Use existing patterns; add Tempo/Jaeger/Grafana as services | Mitigated |
| Trace context propagation through async boundaries | High | Ensure W3C trace context headers are propagated | Mitigated |

## Sprint Notes

Key decisions, tradeoffs, and implementation notes:

```
1. OpenTelemetry Approach:
   - Skip Prometheus; go straight to OpenTelemetry for unified traces + metrics
   - OTLP exporter sends to Tempo, Jaeger, Prometheus + Grafana
   - Visibility first; alerting deferred

2. Scope: LLM-Involving Pipelines Only:
   - Assistant turn pipeline (all 6 stages)
   - Catalog generation pipelines (blueprint, prompt_item, scenario)
   - Assessment/practice pipelines (marking stage)
   - Evaluation pipelines

3. Metrics Retention:
   - Hot storage (Tempo/Jaeger): 30 days for traces
   - Aggregated metrics (Prometheus): 90 days
   - Pipeline run summaries in DB: 1 year
```

## Review And Sign-Off

- Sprint Status: Completed
- Completion Date: 2026-03-27

Checklist:

- [x] Primary goal achieved
- [x] Constitution and quality checks passed
- [x] Unit tests completed
- [x] Integration tests completed
- [ ] Smoke tests with real provider completed (requires OTEL_EXPORTER_OTLP_ENDPOINT to be set)
- [x] Documentation updated
- [ ] Code review completed

Next Sprint Priorities:

1. Sprint 13c: Agent Observability (Wide events persistence)
2. Sprint 13d: Pipeline Visualization (DAG definitions)
3. Sprint 13e: Eval Dashboard
