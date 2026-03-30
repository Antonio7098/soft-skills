# Sprint 15: Prompt & Rubric Versioning Restructure

> Project: SoftSkills
> Scope: Backend and platform execution only. Frontend planning is tracked separately.

## Sprint Overview

- Sprint Name: Prompt & Rubric Versioning Restructure
- Sprint Focus: Restructure prompts and rubrics from flat versioning to explicit parent-child relationships, add org scoping support, and introduce org-level prompt/rubric config overrides
- Depends On: Sprint 14 (Admin Super Agent)

## Relevant Source Docs

- [CONSTITUTION.yml](/home/antonioborgerees/df/soft-skills/ops/CONSTITUTION.yml): lines 1-427
- [ops/mvp-spec/TODO/prompt-rubric-versioning-mvp.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/TODO/prompt-rubric-versioning-mvp.md): lines 1-534
- [ops/mvp-spec/foundational/stageflow-guide.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/stageflow-guide.md): lines 1-50

## Sprint Goals

- Primary Goal: Implement parent-child prompt/rubric model with explicit FKs, org scoping, and org-level config overrides
- Secondary Goals:
  - Update config.py to use UUID + int FK pairs instead of string-based version references
  - Add OrgPromptConfig and OrgRubricConfig tables for org-level overrides by task_kind and skill_slug
  - Implement runtime resolution: org config → global default fallback

## Scope Checklist

### Phase 1: Schema Changes

- [x] Task 1.1: Create `prompts` table with organisation_id (nullable), unique constraint on (organisation_id, name)
- [x] Task 1.2: Create `prompt_versions` table (replace flat PromptVersionRecord)
- [x] Task 1.3: Create `rubrics` table with (skill_slug, organisation_id) unique constraint
- [x] Task 1.4: Create `rubric_versions` table with embedded criteria JSON
- [x] Task 1.5: Create `organisation_prompt_configs` table (organisation_id, task_kind as PK)
- [x] Task 1.6: Create `organisation_rubric_configs` table (organisation_id, skill_slug as PK)
- [x] Task 1.7: Add rubric_version_id FK to AssessmentRecord (prompt_version_id deferred)
- [x] Task 1.8: Add rubric_version_id FK to AttemptRecord
- [x] Task 1.9: Add rubric_version_id FK to PracticeSessionRecord
- [ ] Task 1.10: Add prompt_version_id FK to ContentGenerationArtifactRecord (deferred)

### Phase 2: Data Migration

- [x] Task 2.1: Migrate PromptVersionRecord → Prompt + PromptVersion (global, organisation_id = NULL) - per MVP "start fresh" constraint, legacy tables renamed to _legacy_
- [x] Task 2.2: Migrate RubricRecord → Rubric + RubricVersion (global, organisation_id = NULL) - per MVP "start fresh" constraint
- [x] Task 2.3: Populate FK columns in Assessment, Attempt, PracticeSession (deferred for ContentGenerationArtifact)
- [x] Task 2.4: Mark all existing records as status = published (implicit in seeding)

### Phase 3: Code Migration - Config

- [ ] Task 3.1: Update config.py - replace string-based prompt versions with UUID + int pairs (deferred)
- [ ] Task 3.2: Update MarkingRuntimeConfig - per_skill and aggregation prompt references (deferred)
- [ ] Task 3.3: Update CatalogGenerationRuntimeConfig - all prompt references (deferred)
- [ ] Task 3.4: Update runtime config JSON artifacts to use UUID + int pairs (deferred)
- [ ] Task 3.5: Define and implement config-to-UUID resolution strategy for builtin prompts (deferred - created PromptRepositoryV2 and PromptResolutionService)

### Phase 4: Code Migration - Domain & Repository

- [x] Task 4.1: Rewrite PromptRepository with org filtering support (created PromptRepositoryV2)
- [x] Task 4.2: Rewrite RubricAdminRepository with org filtering support (created RubricRepositoryV2)
- [x] Task 4.3: Create OrgConfigRepository for prompt/rubric config (created OrgConfigRepositoryV2)
- [ ] Task 4.4: Update PromptRegistry.render() signature to use UUIDs (deferred)
- [ ] Task 4.5: Add org resolution logic to PromptRegistry (org config → global fallback) (deferred)
- [ ] Task 4.6: Create RubricRegistry with org resolution (org config → global fallback) (deferred)
- [x] Task 4.7: Update builtin_prompts.py seeding for new model (updated to work with new model)

### Phase 5: Code Migration - Service & API

- [ ] Task 5.1: Rewrite PromptService with org scoping
- [ ] Task 5.2: Create RubricService for rubric CRUD
- [ ] Task 5.3: Create OrgConfigService for org prompt/rubric config
- [ ] Task 5.4: Update commands - CreatePromptCommand, CreateRubricCommand, new org config commands
- [ ] Task 5.5: Update views - PromptView, RubricView, new org config views
- [ ] Task 5.6: Restructure prompt API routes to use {prompt_id}
- [ ] Task 5.7: Restructure rubric API routes to use {rubric_id}
- [ ] Task 5.8: Add org config API endpoints in organisations routes
- [ ] Task 5.9: Update admin_service.py rubric methods to delegate to RubricService instead of RubricAdminRepository
- [ ] Task 5.10: Update admin_service.py prompt methods to delegate to rewritten PromptService
- [ ] Task 5.11: Add version status validation to org config CRUD (reject non-published version references)
- [ ] Task 5.12: Define and implement cascade delete semantics for org configs when parent prompt/rubric is deleted
- [ ] Task 5.13: Investigate PromptItemRecord relationship to PromptVersionRecord; add task if org-scoped prompt-item routes need updating

### Phase 6: Code Migration - Runtime Consumers

- [ ] Task 6.1: Update PromptRenderRequest to use prompt_id, version_id, and organisation_id (for org-aware rendering)
- [ ] Task 6.2: Update workers - prompt_request_transform functions
- [ ] Task 6.2b: Update marking_provider.py build_prompt_library() to use FK-based config references
- [ ] Task 6.3: Integrate RubricRegistry into marking_provider for org-aware rubric resolution (org config → global fallback)
- [ ] Task 6.4: Update persistence layer for FK-based lookups
- [ ] Task 6.5: Update queries for rubric navigation
- [ ] Task 6.6: Update catalog/workflows/generation/persistence.py _persist_generated_quick_practice_rubric to create Rubric + RubricVersion with embedded criteria JSON
- [ ] Task 6.7: Update taxonomy/service.py rubric seeding to use new model (Rubric + RubricVersion)

### Phase 7: Cleanup

- [ ] Task 7.1: Drop legacy columns (prompt_versions.name, prompt_versions.prompt_type, rubrics.family, rubrics.version, rubrics.criteria)
- [ ] Task 7.2: Migrate all RubricCriterionRecord consumers to new rubric_versions.criteria JSON:
       - catalog/workflows/generation/persistence.py (_persist_generated_quick_practice_rubric)
       - evaluation/marking_benchmark.py
       - taxonomy/service.py (rubric seeding)
       - smoke/suites/assessment_marking/smoke.py
       - tests/integration/test_identity_and_catalog.py
- [ ] Task 7.3: Drop RubricCriterionRecord table (after all consumers migrated)

### Phase 8: Documentation

- [ ] Task 8.1: Update sprint README with new sprint entry
- [ ] Task 8.2: Update ROADMAP.md with sprint entry
- [ ] Task 8.3: Update canonical docs for any behavioral changes

## Constitution And Quality Checklist

- [ ] Competency growth remains the product outcome, not activity theater
- [ ] All new external boundaries are typed and schema-validated
- [ ] Fail-fast and fail-loud behavior is preserved with stable error codes
- [ ] Route handlers remain thin; business rules stay out of transport layers
- [ ] Dependency injection and adapter boundaries remain explicit
- [ ] Critical workflow artifacts are durably persisted where required
- [ ] Traces, logs, and events cover all changed workflow steps
- [ ] Prompt, rubric, model, and config versions are preserved where applicable
- [ ] Assessment and progression behavior remains explainable
- [ ] No silent fallback is introduced in scoring, progression, generation, or recommendation paths
- [ ] Org scoping follows NULL = global pattern (matching SkillRecord)
- [ ] All new models require Alembic migrations; migrations are only path for schema evolution (CL-014)
- [ ] All structured LLM outputs validated against declared schemas before use (CL-008)

## Testing And Documentation Checklist

- [ ] Unit Tests: deterministic coverage for new domain logic, schemas, and validation rules
- [ ] Integration Tests: API, persistence, orchestration, and event/trace coverage for the sprint scope
- [ ] Smoke Tests With Real Provider: verify prompt rendering and rubric selection with org resolution
- [ ] Failure Path Coverage: explicit validation, provider, orchestration, and persistence failure paths tested
- [ ] Documentation Updates: update canonical docs in `ops/`, the roadmap/sprint docs, and any affected contracts

## Success Criteria

- [ ] Primary sprint goal is met in a backend-usable form
- [ ] Parent-child prompt/rubric model functional
- [ ] Org scoping working (global + org-scoped prompts/rubrics)
- [ ] Org config overrides functional (prompt by task_kind, rubric by skill_slug)
- [ ] Tests pass at unit, integration, and smoke level for the sprint scope
- [ ] Canonical docs reflect the implemented behavior
- [ ] All new models have Alembic migrations

Minimum Viable Sprint:
Phase 1 (schema) + Phase 2 (migration) + Phase 3 (config) + Phase 4 (domain/repo core) are the critical path. API and runtime consumer changes build on this foundation.

## Risks And Blockers

| Risk | Impact | Mitigation | Status |
| --- | --- | --- | --- |
| Migration coordination for new parent-child models | High | Run migrations in sequence; verify FK relationships before code migration | Open |
| Config migration from string to UUID FK pairs | Medium | Add interim migration phase; backward-compat during transition | Open |
| Runtime resolution complexity (org config → global fallback) | Medium | Keep resolution logic in dedicated registry classes; test each resolution path | Open |
| RubricCriterionRecord removal requires careful data migration | High | Ensure criteria JSON migration is complete before dropping table | Open |
| Config UUID resolution for builtin prompts (chicken-and-egg) | Medium | Define strategy (name→UUID lookup, deterministic UUIDs, or hybrid) before config migration | Open |
| Data migration scope contradiction | Medium | MVP spec says "start fresh" but Phase 2 has migration tasks - resolve before sprint start | Open |

## Sprint Notes

Key decisions, tradeoffs, and implementation notes:

```
1. Org Scoping Pattern:
   - NULL organisation_id = global (platform-wide)
   - Non-NULL organisation_id = org-scoped
   - Same pattern as SkillRecord (UniqueConstraint on slug, organisation_id)

2. Unique Constraints:
   - Prompt: (organisation_id, name) unique - same name allowed in global + each org
   - Rubric: (skill_slug, organisation_id) unique - same skill can have global + org rubric

3. Org Config Resolution:
   - Prompt: Check OrganisationPromptConfig(organisation_id, task_kind) → fallback to global config
   - Rubric: Check OrganisationRubricConfig(organisation_id, skill_slug) → fallback to global rubric

4. API Behavior:
   - Org admins can only create org-scoped resources
   - Global resources require platform admin
   - GET endpoints support optional ?organisation_id= filter

5. Cleanup:
   - Legacy RubricCriterionRecord merged into rubric_versions.criteria JSON
   - Legacy columns removed after migration verification

6. Config UUID Resolution Strategy (TBD before Phase 3):
   - Option A: Look up by name after seeding and populate config dynamically
   - Option B: Use deterministic UUIDs in builtin_prompts.py seeding
   - Option C: Hybrid - keep a name→UUID lookup in config resolution

7. Org Config Version Validation:
   - OrganisationPromptConfig and OrganisationRubricConfig must reference status = published versions
   - API rejects references to draft/archived versions
   - Runtime fails loud if referenced version becomes archived

8. Cascade Delete:
   - Deleting a Prompt deletes all PromptVersions and cascades to OrganisationPromptConfig
   - Deleting a Rubric deletes all RubricVersions and cascades to OrganisationRubricConfig

9. Data Migration Scope:
   - MVP spec constraint "No migration of existing data" needs resolution
   - Phase 2 tasks 2.1-2.4 assume production data exists and must be migrated
   - Decide: clean seed approach vs full migration before sprint start
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

1. [Next sprint]
2. [Subsequent sprint]
3. [Following sprint]
