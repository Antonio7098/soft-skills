# Sprint 13f: Prompt Library API

> Project: SoftSkills
> Scope: Backend and platform execution only. Frontend planning is tracked separately.

## Sprint Overview

- Sprint Name: Prompt Library API
- Sprint Focus: Implement database-backed PromptRegistry with versioning, CRUD, validation subpipeline, and admin API endpoints
- Depends On: Sprint 12 (Collections Enhancement)

## Relevant Source Docs

- [CONSTITUTION.yml](/home/antonioborgerees/df/soft-skills/ops/CONSTITUTION.yml): lines 1-427
- [ops/mvp-spec/admin-dashboard-readiness.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/admin-dashboard-readiness.md): lines 254-317
- [ops/mvp-spec/foundational/stageflow-guide.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/stageflow-guide.md): lines 1-50

## Sprint Goals

- Primary Goal: Implement PromptRegistry with versioning, CRUD operations, validation, and admin API
- Secondary Goals:
  - Prompt render stage with metrics tracking
  - Prompt lineage tracking
  - Prompt A/B testing via parent_version_id

## Scope Checklist

- [ ] Task 4.1: Prompt version database models - `PromptVersionRecord`, `PromptRenderMetricsRecord`, `PromptRenderEventRecord`
- [ ] Task 4.2: Prompt registry migration - Migrate from static `PromptLibrary` to database-backed `PromptRegistry`
- [ ] Task 4.3: Prompt validation subpipeline - Syntax check → Variable check → Output format check
- [ ] Task 4.4: Prompt render stage - `PromptRenderStage` (StageKind.TRANSFORM) with metrics tracking via `stage.summary`
- [ ] Task 4.5: Prompt lineage tracking - Link prompt versions via `parent_version_id` to `PipelineRunRecord.stage_results`
- [ ] Task 4.6: Admin prompts endpoint - `GET /admin/prompts` to list all prompt names with latest version
- [ ] Task 4.7: Prompt versions endpoint - `GET /admin/prompts/{name}/versions` to list all versions
- [ ] Task 4.8: Prompt version detail - `GET /admin/prompts/{name}/versions/{version}` to get specific version
- [ ] Task 4.9: Create prompt - `POST /admin/prompts` to create new prompt version (draft)
- [ ] Task 4.10: Update prompt - `PUT /admin/prompts/{name}/versions/{version}` to update draft version
- [ ] Task 4.11: Publish prompt - `POST /admin/prompts/{name}/versions/{version}/publish` to publish to production
- [ ] Task 4.12: Archive prompt - `POST /admin/prompts/{name}/versions/{version}/archive` to archive version
- [ ] Task 4.13: Prompt analytics - `GET /admin/prompts/{name}/analytics` for performance metrics per version
- [ ] Task 4.14: Prompt compare - `POST /admin/prompts/compare` to compare two versions (A/B)
- [ ] Task 4.15: Prompt variables_schema enforcement - JSON Schema required for all prompts
- [ ] Task 4.16: Prompt output_schema enforcement - Required for prompts expecting structured JSON output
- [ ] Task 4.17: Documentation updates

## Constitution And Quality Checklist

- [ ] Competency growth remains the product outcome, not activity theater
- [ ] All new external boundaries are typed and schema-validated
- [ ] Fail-fast and fail-loud behavior is preserved with stable error codes
- [ ] Route handlers remain thin; business rules stay out of transport layers
- [ ] Dependency injection and adapter boundaries remain explicit
- [ ] Critical workflow artifacts are durably persisted where required
- [ ] Traces, logs, and events cover all changed workflow steps
- [ ] Prompt, rubric, model, and config versions are preserved where applicable
- [ ] All admin API endpoints follow explicit schemas with Pydantic request/response models (CL-013)
- [ ] All admin endpoints delegate to domain/application services; no business logic in routes (CL-013)
- [ ] Prompt variables_schema and output_schema enforced for all prompts
- [ ] All structured LLM outputs validated against declared schemas before use
- [ ] All new models require Alembic migrations; migrations are only path for schema evolution (CL-014)

## Testing And Documentation Checklist

- [ ] Unit Tests: deterministic coverage for new domain logic, schemas, and validation rules
- [ ] Integration Tests: API, persistence, orchestration, and event/trace coverage for the sprint scope
- [ ] Smoke Tests With Real Provider: verify prompt rendering and validation
- [ ] Prompt Library Tests: verify prompt versioning, rendering, validation
- [ ] Documentation Updates: update canonical docs in `ops/`, the roadmap/sprint docs, and any affected contracts

## Success Criteria

- [ ] Primary sprint goal is met in a backend-usable form
- [ ] PromptRegistry functional with versioning and CRUD
- [ ] Admin API endpoints for prompt management
- [ ] Tests pass at unit, integration, and smoke level for the sprint scope
- [ ] Canonical docs reflect the implemented behavior
- [ ] All new models have Alembic migrations

Minimum Viable Sprint:
Tasks 4.1-4.5 (database models and registry migration) are the critical path. Admin endpoints (4.6-4.12) build on the foundation.

## Risks And Blockers

| Risk | Impact | Mitigation | Status |
| --- | --- | --- | --- |
| Migration coordination for new prompt models | Medium | Plan migration sequence early in sprint | Open |
| Prompt validation complexity | High | Design validation subpipeline carefully | Open |

## Sprint Notes

Key decisions, tradeoffs, and implementation notes:

```
1. Prompt Library Design:
   - Built-in prompts remain static strings in prompts.py (registered at startup)
   - User-created prompts persisted to DB via admin API
   - Explicit variables_schema (JSON Schema) required for all prompts
   - Explicit output_schema required for prompts expecting structured JSON output
   - parent_version_id supports simple A/B testing (no percentage-based routing)

2. Lifecycle:
   draft → published → archived

3. Database Models:
   - PromptVersionRecord: name, version, prompt_type, template, variables_schema, output_schema, status, parent_version_id
   - PromptRenderMetricsRecord: prompt_version_id, render_count, success_count, avg_latency_ms, total_tokens
   - PromptRenderEventRecord: prompt_version_id, success, latency_ms, tokens, error_code, trace_id

4. Stageflow Integration:
   - PromptRenderStage (StageKind.TRANSFORM) - Renders prompts and tracks metrics via stage.summary
   - stage.wide events - Per-prompt-version performance metrics
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
- [ ] All Alembic migrations created

Next Sprint Priorities:

1. Sprint 13g: User Management API
2. Sprint 13h: User/Cohort Analytics
3. Sprint 13i: Policy Layer
