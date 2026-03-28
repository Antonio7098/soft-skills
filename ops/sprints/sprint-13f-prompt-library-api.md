# Sprint 13f: Prompt Library API

> Project: SoftSkills
> Scope: Backend and platform execution only. Frontend planning is tracked separately.

## Sprint Overview

- Sprint Name: Prompt Library API
- Sprint Focus: Implement database-backed PromptRegistry with versioning, CRUD, validation, admin API endpoints, and centralized prompt rendering for assistant and catalog workflows
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
  - Centralize assistant and catalog prompt rendering through a shared Stageflow render stage

## Scope Checklist

- [x] Task 4.1: Prompt version database models - `PromptVersionRecord`, `PromptRenderMetricsRecord`, `PromptRenderEventRecord`
- [x] Task 4.2: Prompt registry migration - Replace static runtime prompt resolution with database-backed `PromptRegistry`
- [x] Task 4.3: Prompt validation subpipeline - Syntax check → Variable check → Output format check
- [x] Task 4.4: Prompt render stage - Shared `prompt_render` transform stage with metrics/event tracking and strict missing-prompt failure
- [x] Task 4.5: Prompt lineage tracking - Link prompt versions via `parent_version_id` to `PipelineRunRecord.stage_results`
- [x] Task 4.6: Admin prompts endpoint - `GET /admin/prompts` to list all prompt names with latest version
- [x] Task 4.7: Prompt versions endpoint - `GET /admin/prompts/{name}/versions` to list all versions
- [x] Task 4.8: Prompt version detail - `GET /admin/prompts/{name}/versions/{version}` to get specific version
- [x] Task 4.9: Create prompt - `POST /admin/prompts` to create new prompt version (draft)
- [x] Task 4.10: Update prompt - `PUT /admin/prompts/{name}/versions/{version}` to update draft version
- [x] Task 4.11: Publish prompt - `POST /admin/prompts/{name}/versions/{version}/publish` to publish to production
- [x] Task 4.12: Archive prompt - `POST /admin/prompts/{name}/versions/{version}/archive` to archive version
- [x] Task 4.13: Prompt analytics - `GET /admin/prompts/{name}/analytics` for performance metrics per version
- [x] Task 4.14: Prompt compare - `POST /admin/prompts/compare` to compare two versions (A/B)
- [x] Task 4.15: Prompt variables_schema enforcement - JSON Schema required for all prompts
- [x] Task 4.16: Prompt output_schema enforcement - Required for prompts expecting structured JSON output
- [x] Task 4.17: Documentation updates
- [x] Task 4.18: Centralize assistant prompt rendering through the shared prompt registry path
- [x] Task 4.19: Centralize catalog generation prompt rendering through the shared prompt registry path

## Constitution And Quality Checklist

- [x] Competency growth remains the product outcome, not activity theater
- [x] All new external boundaries are typed and schema-validated
- [x] Fail-fast and fail-loud behavior is preserved with stable error codes
- [x] Route handlers remain thin; business rules stay out of transport layers
- [x] Dependency injection and adapter boundaries remain explicit
- [x] Critical workflow artifacts are durably persisted where required
- [x] Traces, logs, and events cover all changed workflow steps
- [x] Prompt, rubric, model, and config versions are preserved where applicable
- [x] All admin API endpoints follow explicit schemas with Pydantic request/response models (CL-013)
- [x] All admin endpoints delegate to domain/application services; no business logic in routes (CL-013)
- [x] Prompt variables_schema and output_schema enforced for all prompts
- [x] All structured LLM outputs validated against declared schemas before use
- [x] All new models require Alembic migrations; migrations are only path for schema evolution (CL-014)

## Testing And Documentation Checklist

- [x] Unit Tests: deterministic coverage for new domain logic, schemas, and validation rules
- [x] Integration Tests: API, persistence, orchestration, and event/trace coverage for the sprint scope
- [ ] Smoke Tests With Real Provider: verify prompt rendering and validation (deferred)
- [ ] Prompt Library Tests: verify prompt versioning, rendering, validation (deferred)
- [x] Documentation Updates: update canonical docs in `ops/`, the roadmap/sprint docs, and any affected contracts

## Success Criteria

- [x] Primary sprint goal is met in a backend-usable form
- [x] PromptRegistry functional with versioning and CRUD
- [x] Admin API endpoints for prompt management
- [x] Tests pass at unit and integration level for the sprint scope
- [x] Canonical docs reflect the implemented behavior
- [x] All new models have Alembic migrations

Minimum Viable Sprint:
Tasks 4.1-4.5 (database models and registry migration) are the critical path. Admin endpoints (4.6-4.12) build on the foundation.

## Risks And Blockers

| Risk | Impact | Mitigation | Status |
| --- | --- | --- | --- |
| Migration coordination for new prompt models | Medium | Lazy built-in seeding avoids pre-migration app bootstrap issues in tests and local runtime | Mitigated |
| Prompt validation complexity | High | Keep validation focused on renderability and declared-variable coverage; extend only when justified by failures | Mitigated |
| Prompt inventory drift between code and DB | Medium | Seed built-in prompts idempotently through PromptRepository and PromptRegistry before first use | Mitigated |

## Sprint Notes

Key decisions, tradeoffs, and implementation notes:

```
1. Prompt Library Design:
   - Prompt definitions are persisted in PromptVersionRecord and resolved through PromptRegistry at runtime
   - Built-in assistant and catalog prompts are lazily seeded into the database on first safe post-migration use
   - User-created prompts are persisted through the admin API using the same model and lifecycle
   - Explicit variables_schema (JSON Schema) required for all prompts
   - Explicit output_schema required for prompts expecting structured JSON output
   - parent_version_id supports lineage and simple A/B comparison

2. Lifecycle:
   draft → published → archived

3. Database Models:
   - PromptVersionRecord: name, version, prompt_type, template, variables_schema, output_schema, status, parent_version_id
   - PromptRenderMetricsRecord: prompt_version_id, render_count, success_count, avg_latency_ms, total_tokens
   - PromptRenderEventRecord: prompt_version_id, success, latency_ms, tokens, error_code, trace_id

4. Stageflow Integration:
   - Shared pattern: prompt_request → prompt_render → llm_transform
   - prompt_request emits prompt_name, prompt_version, variables
   - prompt_render resolves through PromptRegistry, validates, renders, records metrics/events, and fails loudly if the prompt is missing
   - assistant planning and final-response prompts use the shared render stage
   - catalog collection planning, prompt-item planning, prompt-item generation, and scenario generation use the shared render stage

5. Runtime Strictness:
   - No fallback to static PromptLibrary rendering on registry miss
   - Missing prompt versions are orchestration failures, not degradations
```

## Review And Sign-Off

- Sprint Status: Completed
- Completion Date: 2026-03-28

Checklist:

- [x] Primary goal achieved
- [x] Constitution and quality checks passed
- [x] Unit tests completed
- [x] Integration tests completed
- [ ] Smoke tests with real provider completed (deferred to next sprint)
- [x] Documentation updated
- [x] Code review completed
- [x] All Alembic migrations created

Next Sprint Priorities:

1. Sprint 13g: User Management API
2. Sprint 13h: User/Cohort Analytics
3. Sprint 13i: Policy Layer
