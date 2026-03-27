# Sprint 13d: Pipeline Visualization

> Project: SoftSkills
> Scope: Backend and platform execution only. Frontend planning is tracked separately.

## Sprint Overview

- Sprint Name: Pipeline Visualization
- Sprint Focus: Implement pipeline definition discovery, execution trace storage, and admin API endpoints for DAG visualization
- Depends On: Sprint 13b (Monitoring/Telemetry)

## Relevant Source Docs

- [CONSTITUTION.yml](/home/antonioborgerees/df/soft-skills/ops/CONSTITUTION.yml): lines 1-427
- [ops/mvp-spec/admin-dashboard-readiness.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/admin-dashboard-readiness.md): lines 156-215
- [ops/mvp-spec/foundational/stageflow-guide.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/stageflow-guide.md): lines 1-50

## Sprint Goals

- Primary Goal: Implement admin API endpoints for pipeline DAG view, execution trace view, stage metrics view, and flame chart view
- Secondary Goals:
  - Pipeline definition discovery at startup
  - Execution trace storage per run
  - Aggregate stage metrics

## Scope Checklist

- [ ] Task 2c.1: Pipeline definition discovery - Discover all registered pipelines at startup and store `PipelineDefinitionRecord`
- [ ] Task 2c.2: Stage definition records - Store `StageDefinitionRecord` for each stage (name, kind, dependencies, runner_class)
- [ ] Task 2c.3: Pipeline execution trace storage - Store `PipelineExecutionTraceRecord` per run for visualization replay
- [ ] Task 2c.4: Admin pipelines endpoint - `GET /admin/pipelines` to list all pipeline definitions
- [ ] Task 2c.5: Pipeline DAG endpoint - `GET /admin/pipelines/{name}` to get pipeline DAG (stages, dependencies, kinds)
- [ ] Task 2c.6: Pipeline runs endpoint - `GET /admin/pipelines/{name}/runs` to list recent runs
- [ ] Task 2c.7: Pipeline trace endpoint - `GET /admin/pipelines/{name}/runs/{run_id}/trace` for execution trace
- [ ] Task 2c.8: Pipeline metrics endpoint - `GET /admin/pipelines/{name}/metrics` for aggregate stage metrics (latency p50/p95/p99, success rate)
- [ ] Task 2c.9: Trace visualization backend - API support for pipeline DAG view, execution trace view, stage metrics view, flame chart view
- [ ] Task 2c.10: Documentation updates

## Constitution And Quality Checklist

- [ ] Competency growth remains the product outcome, not activity theater
- [ ] All new external boundaries are typed and schema-validated
- [ ] Fail-fast and fail-loud behavior is preserved with stable error codes
- [ ] Route handlers remain thin; business rules stay out of transport layers
- [ ] Dependency injection and adapter boundaries remain explicit
- [ ] Critical workflow artifacts are durably persisted where required
- [ ] Traces, logs, and events cover all changed workflow steps
- [ ] All admin API endpoints follow explicit schemas with Pydantic request/response models (CL-013)
- [ ] All admin endpoints delegate to domain/application services; no business logic in routes (CL-013)

## Testing And Documentation Checklist

- [ ] Unit Tests: deterministic coverage for new domain logic, schemas, and validation rules
- [ ] Integration Tests: API, persistence, orchestration, and event/trace coverage for the sprint scope
- [ ] Smoke Tests With Real Provider: verify pipeline discovery and trace storage
- [ ] Documentation Updates: update canonical docs in `ops/`, the roadmap/sprint docs, and any affected contracts

## Success Criteria

- [ ] Primary sprint goal is met in a backend-usable form
- [ ] Pipeline definitions discoverable and stored at startup
- [ ] Admin API endpoints functional for all 6 visualization types
- [ ] Tests pass at unit, integration, and smoke level for the sprint scope
- [ ] Canonical docs reflect the implemented behavior

Minimum Viable Sprint:
Tasks 2c.1-2c.4 are the critical path. Tasks 2c.5-2c.9 build on the foundation.

## Risks And Blockers

| Risk | Impact | Mitigation | Status |
| --- | --- | --- | --- |
| Trace storage volume | Medium | Implement retention policy and efficient indexing | Open |
| Performance of metrics aggregation | Low | Use materialized views or background aggregation | Open |

## Sprint Notes

Key decisions, tradeoffs, and implementation notes:

```
1. Pipeline Visualization Types:
   - Pipeline DAG View: Static graph showing stages, dependencies, kinds (color-coded by StageKind)
   - Execution Trace View: Animated sequential replay of actual execution with timing
   - Stage Metrics View: Per-stage latency histograms, success/failure rates
   - Flame Chart View: Hierarchical timing breakdown of pipeline stages

2. Pipeline Discovery (at startup):
   def discover_pipelines(stageflow_runtime: StageflowRuntime) -> list[PipelineDefinition]:
       for pipeline_name, pipeline in stageflow_runtime.pipeline_registry.items():
           for stage_name, spec in pipeline.stages.items():
               stages.append({name, kind, dependencies, runner_class})

3. Stageflow Types:
   - StageKind: TRANSFORM, ENRICH, ROUTE, GUARD, WORK, AGENT
   - StageStatus: OK, SKIP, CANCEL, FAIL, RETRY
```

## Review And Sign-Off

- Sprint Status: Not Started
- Completion Date: [Date]

Checklist:

- [ ] Primary goal achieved
- [ ] Constitution and quality checks passed
- [ ] Unit tests completed
- [ ] Integration tests completed
- [ ] Smoke tests with real provider completed
- [ ] Documentation updated
- [ ] Code review completed

Next Sprint Priorities:

1. Sprint 13e: Eval Dashboard
2. Sprint 13f: Prompt Library API
3. Sprint 13g: User Management API
