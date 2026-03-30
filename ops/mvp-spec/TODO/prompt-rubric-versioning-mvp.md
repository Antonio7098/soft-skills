# Prompt & Rubric Versioning Restructure - MVP Specification

**Date:** 2026-03-30  
**Status:** Approved for Implementation

---

## Overview

Restructure the prompt and rubric system from implicit family-based versioning to explicit parent-child relationship:

- **Prompt** (parent) → **PromptVersion** (child)
- **Rubric** (parent) → **RubricVersion** (child)

Each agent/worker references one Prompt + specific PromptVersion via explicit FKs.

---

## Data Model

### Prompt (parent)

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | PK |
| `name` | str | unique, indexed |
| `description` | str | |
| `prompt_type` | str | e.g., "assistant", "generation" |
| `variables_schema` | JSON | inherited by all versions |
| `created_at` | datetime | |
| `updated_at` | datetime | |

### PromptVersion (child)

| Field | Type | Notes |
|-------|------|-------|
| `id` | int | PK, autoincrement |
| `prompt_id` | UUID | FK → prompts.id |
| `version` | str | semantic (v1, v2...) |
| `template` | Text | |
| `output_schema` | JSON \| None | |
| `status` | str | draft/published/archived |
| `parent_version_id` | int \| None | for branching |
| `created_at` | datetime | |
| `updated_at` | datetime | |

Unique constraint: (prompt_id, version)

### Rubric (parent)

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | PK |
| `skill_slug` | str | FK → skills.slug, UNIQUE |
| `name` | str | |
| `description` | str | |
| `content_type` | str | |
| `schema_version` | str | |
| `created_at` | datetime | |
| `updated_at` | datetime | |

Constraint: 1:1 relationship with Skill (enforced at DB + application level)

### RubricVersion (child, collapsed)

| Field | Type | Notes |
|-------|------|-------|
| `id` | int | PK, autoincrement |
| `rubric_id` | UUID | FK → rubrics.id |
| `version` | str | semantic |
| `criteria` | JSON | array of criterion objects |
| `status` | str | draft/published/archived |
| `created_at` | datetime | |
| `updated_at` | datetime | |

Unique constraint: (rubric_id, version)

### Criterion Object Structure (within criteria JSON)

```json
{
  "ref": "clarity",
  "title": "Clarity of Communication",
  "description": "How clearly...",
  "weight": 1.0,
  "required": true,
  "position": 0,
  "levels": [
    {"level": 1, "description": "...", "examples": ["..."]},
    {"level": 2, "description": "...", "examples": ["..."]},
    {"level": 3, "description": "...", "examples": ["..."]},
    {"level": 4, "description": "...", "examples": ["..."]},
    {"level": 5, "description": "...", "examples": ["..."]}
  ]
}
```

---

## Tables to Modify

### New Tables

- `prompts` - parent prompt records
- `prompt_versions` - versioned prompt templates (replaces current prompt_versions)
- `rubrics` - parent rubric records
- `rubric_versions` - rubric versions with embedded criteria

### Tables to Update (add FK columns)

| Table | New Columns | Replace |
|-------|-------------|---------|
| `AssessmentRecord` | `prompt_version_id`, `rubric_version_id` | string-based `prompt_version`, `rubric_id`, `rubric_version` |
| `AttemptRecord` | `rubric_version_id` | `rubric_id`, `rubric_version` |
| `PracticeSessionRecord` | `rubric_version_id` | `rubric_id`, `rubric_version` |
| `ContentGenerationArtifactRecord` | `prompt_version_id` | `prompt_version` |

### Tables to Drop (after migration)

- `RubricCriterionRecord` - merged into rubric_versions.criteria JSON

### Legacy Columns to Remove (after migration)

- `PromptVersionRecord.name` → use FK to Prompt
- `PromptVersionRecord.prompt_type` → moved to Prompt
- `RubricRecord.family` → use rubric_id
- `RubricRecord.version` → use FK to RubricVersion
- `RubricRecord.criteria` → moved to RubricVersion.criteria

---

## Config Changes

### config.py

Replace all string-based `*_prompt_version` fields with explicit FK pairs:

```python
# BEFORE
llm_assistant_prompt_version: str = "assistant.chat.v1"
llm_marking_per_skill_prompt_version: str = "assessment.quick-practice.v1"
llm_marking_aggregation_prompt_version: str = "assessment.aggregation.v1"
llm_creator_blueprint_prompt_version: str = "creator.collection.structured-blueprint.v2"
llm_creator_prompt_item_prompt_version: str = "creator.prompt-item.worker.v1"
llm_creator_scenario_prompt_version: str = "creator.scenario.worker.v1"

# AFTER
llm_assistant_prompt_id: UUID
llm_assistant_prompt_version_id: int
llm_marking_per_skill_prompt_id: UUID
llm_marking_per_skill_prompt_version_id: int
llm_marking_aggregation_prompt_id: UUID
llm_marking_aggregation_prompt_version_id: int
llm_creator_blueprint_prompt_id: UUID
llm_creator_blueprint_prompt_version_id: int
llm_creator_prompt_item_prompt_id: UUID
llm_creator_prompt_item_prompt_version_id: int
llm_creator_scenario_prompt_id: UUID
llm_creator_scenario_prompt_version_id: int
llm_admin_agent_planning_prompt_id: UUID
llm_admin_agent_planning_prompt_version_id: int
```

### engines/config/models.py

**MarkingRuntimeConfig:**

```python
# BEFORE
per_skill_prompt_name: str
per_skill_prompt_version: str
aggregation_prompt_name: str
aggregation_prompt_version: str

# AFTER
per_skill_prompt_id: UUID
per_skill_prompt_version_id: int
aggregation_prompt_id: UUID
aggregation_prompt_version_id: int
```

**CatalogGenerationRuntimeConfig:**

```python
# BEFORE
structured_prompt_name: str
structured_prompt_version: str
chat_prompt_name: str
chat_prompt_version: str
prompt_item_structured_prompt_name: str
prompt_item_structured_prompt_version: str
prompt_item_chat_prompt_name: str
prompt_item_chat_prompt_version: str
prompt_item_worker_prompt_name: str
prompt_item_worker_prompt_version: str
scenario_worker_prompt_name: str
scenario_worker_prompt_version: str

# AFTER
structured_prompt_id: UUID
structured_prompt_version_id: int
chat_prompt_id: UUID
chat_prompt_version_id: int
prompt_item_structured_prompt_id: UUID
prompt_item_structured_prompt_version_id: int
prompt_item_chat_prompt_id: UUID
prompt_item_chat_prompt_version_id: int
prompt_item_worker_prompt_id: UUID
prompt_item_worker_prompt_version_id: int
scenario_worker_prompt_id: UUID
scenario_worker_prompt_version_id: int
```

---

## API Endpoints

### Prompt API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/prompts` | List all prompts |
| GET | `/prompts/{prompt_id}` | Get prompt details |
| POST | `/prompts` | Create prompt + first version |
| GET | `/prompts/{prompt_id}/versions` | List versions |
| GET | `/prompts/{prompt_id}/versions/{version_id}` | Get specific version |
| POST | `/prompts/{prompt_id}/versions` | Create new version |
| PUT | `/prompts/{prompt_id}/versions/{version_id}` | Update draft |
| POST | `/prompts/{prompt_id}/versions/{version_id}/publish` | Publish version |
| POST | `/prompts/{prompt_id}/versions/{version_id}/archive` | Archive version |
| GET | `/prompts/{prompt_id}/versions/{version_id}/analytics` | Get render analytics |

### Rubric API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/rubrics` | List all rubrics |
| GET | `/rubrics/{rubric_id}` | Get rubric details |
| POST | `/rubrics` | Create rubric + first version |
| GET | `/rubrics/{rubric_id}/versions` | List versions |
| GET | `/rubrics/{rubric_id}/versions/{version_id}` | Get specific version |
| POST | `/rubrics/{rubric_id}/versions` | Create new version |
| PUT | `/rubrics/{rubric_id}/versions/{version_id}` | Update draft |
| POST | `/rubrics/{rubric_id}/versions/{version_id}/publish` | Publish version |
| POST | `/rubrics/{rubric_id}/versions/{version_id}/archive` | Archive version |
| DELETE | `/rubrics/{rubric_id}` | Delete rubric and all versions |

---

## Runtime Changes

### PromptRegistry.render()

```python
# BEFORE
def render(self, name: str, *, version: str, variables: dict, ...) -> RenderResult

# AFTER
def render(self, prompt_id: UUID, *, version_id: int, variables: dict, ...) -> RenderResult
```

### PromptRenderRequest

```python
# BEFORE
class PromptRenderRequest:
    name: str
    version: str
    variables: dict[str, object]

# AFTER
class PromptRenderRequest:
    prompt_id: UUID
    version_id: int
    variables: dict[str, object]
```

### All PromptRenderRequest construction sites must be updated:
- `modules/catalog/workflows/generation/workers.py` - prompt_request_transform functions
- Any other workflows that create PromptRenderRequest

---

## File Impact Map

### New Files

- `modules/admin/domain/rubric_registry.py` - rubric registry for rendering
- `modules/admin/use_cases/rubric_service.py` - rubric CRUD operations
- Migration scripts for data transformation

### Layer-by-Layer Changes

**Models (platform/db/models.py):**
- Add `PromptRecord`, `PromptVersionRecord` (replace existing)
- Add `RubricRecord`, `RubricVersionRecord` (new)
- Update `AssessmentRecord` - add prompt_version_id, rubric_version_id FKs
- Update `AttemptRecord` - add rubric_version_id FK
- Update `PracticeSessionRecord` - add rubric_version_id FK
- Update `ContentGenerationArtifactRecord` - add prompt_version_id FK
- Remove `RubricCriterionRecord` (merged into RubricVersion.criteria)

**Repository (modules/admin/infra/):**
- `prompt_repository.py` - complete rewrite for new model
- `rubric_admin_repository.py` - complete rewrite for new model

**Domain (modules/admin/domain/):**
- `prompt_registry.py` - change render() signature to use UUIDs
- `builtin_prompts.py` - update seeding to create Prompt + PromptVersion parents

**Config (config.py):**
- Change all `llm_*_prompt_version: str` to `llm_*_prompt_id: UUID` + `llm_*_prompt_version_id: int`

**Runtime Config (engines/config/models.py):**
- `MarkingRuntimeConfig` - update per_skill and aggregation prompt references
- `CatalogGenerationRuntimeConfig` - update all prompt references

**Commands (modules/admin/contracts/commands.py):**
- `CreatePromptCommand` - add prompt_id, version at parent level
- `UpdatePromptCommand` - adapt for new structure
- `CreateRubricCommand` - add skill_slug at parent level
- Remove `RubricCriterionCommand`, `CreateRubricCriterionCommand` (criteria now embedded)

**Views (modules/admin/contracts/views.py):**
- `PromptVersionView` - add prompt_id, restructure
- `RubricView` - restructure for parent + versions
- `RubricCriterionView` - now embedded JSON, not separate model

**Services (modules/admin/use_cases/):**
- `prompt_service.py` - complete rewrite
- `admin_service.py` - update rubric methods to new service

**Routes (entrypoints/http/routes/admin.py):**
- Restructure all prompt endpoints to use {prompt_id}
- Restructure all rubric endpoints to use {rubric_id}

**Workers (modules/catalog/workflows/generation/workers.py):**
- Update PromptRenderRequest creation in prompt_request_transform
- Update config references to use ID-based lookups

**Assessment (modules/practice/workflows/assessment/marking_provider.py):**
- Update to use prompt_version_id, rubric_version_id FKs

**Persistence (modules/practice/infra/persistence.py):**
- Update to use FK-based lookups

**Queries (modules/practice/infra/queries.py):**
- Update rubric lookups to navigate rubric → rubric_version

---

## Migration Steps

### Phase 1: Schema Changes

1. Create new `prompts` table
2. Create new `prompt_versions` table  
3. Create new `rubrics` table
4. Create new `rubric_versions` table
5. Add FK columns to AssessmentRecord, AttemptRecord, PracticeSessionRecord, ContentGenerationArtifactRecord

### Phase 2: Data Migration

6. Migrate PromptVersionRecord → Prompt + PromptVersion
   - Group by unique `name` → create Prompt parent
   - Link existing rows to parent via `prompt_id`
   - Set `variables_schema`, `prompt_type` on parent

7. Migrate RubricRecord → Rubric + RubricVersion
   - Create Rubric parent for each unique rubric_id
   - Create RubricVersion records
   - Move `criteria` JSON from RubricRecord into RubricVersion

8. Populate FK columns in Assessment, Attempt, PracticeSession, ContentGenerationArtifact by joining on legacy string fields

9. Mark all existing records as `status = published`

### Phase 3: Code Migration

10. Update config.py - replace all string-based prompt versions with UUID + int pairs
11. Update runtime config models
12. Update PromptRegistry.render() signature
13. Update PromptRenderRequest
14. Update all workers and workflows
15. Update API routes
16. Update repository layer
17. Update service layer

### Phase 4: Verification

18. Run all tests
19. Run smoke tests
20. Verify data integrity

### Phase 5: Cleanup

21. Drop legacy columns (prompt_versions.name, prompt_versions.prompt_type, rubrics.family, rubrics.version, rubrics.criteria)
22. Drop RubricCriterionRecord table

---

## Implementation Order

1. **Database layer** - new models, migrations
2. **Config** - update settings and runtime config models
3. **Repository layer** - prompt_repository, rubric_admin_repository
4. **Domain layer** - prompt_registry (update), rubric_registry (new)
5. **Service layer** - prompt_service (rewrite), rubric_service (new)
6. **API layer** - routes, commands, views
7. **Runtime consumers** - workers, assessment, practice
8. **Verification** - run tests, smoke tests

---

## Constraints & Decisions

- **Skills must exist before creating Rubrics** - no auto-creation
- **One Rubric per Skill** - enforced at DB (unique constraint on skill_slug) + application level
- **Semantic versioning** - v1, v2, v3 (no dot notation)
- **Version selection is explicit** - agents must specify version_id at runtime
- **No migration of existing data** - current skills are placeholders, start fresh
- **RubricCriterionRecord removed** - criteria embedded directly in RubricVersion as JSON

---

## Open Questions

None - all decisions finalized.