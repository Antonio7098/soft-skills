# Prompt & Rubric Versioning Restructure - MVP Specification

**Date:** 2026-03-30
**Status:** Approved for Implementation

---

## Overview

Restructure the prompt and rubric system from implicit family-based versioning to explicit parent-child relationship, with org scoping support:

- **Prompt** (parent) → **PromptVersion** (child)
- **Rubric** (parent) → **RubricVersion** (child)
- **OrganisationPromptConfig** - org-level prompt overrides by LLMTaskKind
- **OrganisationRubricConfig** - org-level rubric overrides by skill_slug

Each agent/worker references one Prompt + specific PromptVersion via explicit FKs.

Org scoping follows the standard pattern (NULL organisation_id = global, non-NULL = org-scoped).

---

## Data Model

### Prompt (parent)

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | PK |
| `organisation_id` | UUID \| None | FK → organisations.id, nullable, indexed |
| `name` | str | indexed, unique with organisation_id |
| `description` | str \| None | |
| `prompt_type` | str | e.g., "assistant", "generation" |
| `variables_schema` | JSON | inherited by all versions |
| `created_at` | datetime | |
| `updated_at` | datetime | |

Unique constraint: `(organisation_id, name)` — allows same name in global + org scope
- `organisation_id = NULL` → global (platform-wide) prompt
- `organisation_id = <uuid>` → org-scoped prompt (only accessible to that org)

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
| `skill_slug` | str | FK → skills.slug |
| `organisation_id` | UUID \| None | FK → organisations.id, nullable |
| `name` | str | |
| `description` | str \| None | |
| `content_type` | str | |
| `schema_version` | str | |
| `created_at` | datetime | |
| `updated_at` | datetime | |

- `organisation_id = NULL` → global rubric (default for all orgs)
- `organisation_id = <uuid>` → org-scoped rubric (override for that org)
- Unique constraint: `(skill_slug, organisation_id)` — allows global + org-specific rubric per skill

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

### OrganisationPromptConfig (new)

Org-level overrides for prompts by LLMTaskKind. When set, org uses this prompt instead of the global default.

| Field | Type | Notes |
|-------|------|-------|
| `organisation_id` | UUID | FK → organisations.id, PK |
| `task_kind` | str | LLMTaskKind value, PK |
| `prompt_id` | UUID | FK → prompts.id |
| `prompt_version_id` | int | FK → prompt_versions.id |
| `created_at` | datetime | |

PK: `(organisation_id, task_kind)` — one override per task kind per org

### OrganisationRubricConfig (new)

Org-level overrides for rubrics by skill_slug. When set, org uses this rubric instead of the global default for that skill.

| Field | Type | Notes |
|-------|------|-------|
| `organisation_id` | UUID | FK → organisations.id, PK |
| `skill_slug` | str | FK → skills.slug, PK |
| `rubric_id` | UUID | FK → rubrics.id |
| `rubric_version_id` | int | FK → rubric_versions.id |
| `created_at` | datetime | |

PK: `(organisation_id, skill_slug)` — one override per skill per org

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

- `prompts` - parent prompt records (with organisation_id)
- `prompt_versions` - versioned prompt templates (replaces current prompt_versions)
- `rubrics` - parent rubric records (with organisation_id)
- `rubric_versions` - rubric versions with embedded criteria
- `organisation_prompt_configs` - org prompt overrides by LLMTaskKind
- `organisation_rubric_configs` - org rubric overrides by skill_slug

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
| GET | `/prompts` | List prompts (optional `?organisation_id=` filter) |
| GET | `/prompts/{prompt_id}` | Get prompt details |
| POST | `/prompts` | Create prompt + first version (org admin → org-scoped only) |
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
| GET | `/rubrics` | List rubrics (optional `?organisation_id=` filter) |
| GET | `/rubrics/{rubric_id}` | Get rubric details |
| POST | `/rubrics` | Create rubric + first version (org admin → org-scoped only) |
| GET | `/rubrics/{rubric_id}/versions` | List versions |
| GET | `/rubrics/{rubric_id}/versions/{version_id}` | Get specific version |
| POST | `/rubrics/{rubric_id}/versions` | Create new version |
| PUT | `/rubrics/{rubric_id}/versions/{version_id}` | Update draft |
| POST | `/rubrics/{rubric_id}/versions/{version_id}/publish` | Publish version |
| POST | `/rubrics/{rubric_id}/versions/{version_id}/archive` | Archive version |
| DELETE | `/rubrics/{rubric_id}` | Delete rubric and all versions |

### Organisation Prompt Config API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/organisations/{organisation_id}/prompt-config` | List org's prompt overrides |
| POST | `/organisations/{organisation_id}/prompt-config` | Set prompt override for a task_kind |
| DELETE | `/organisations/{organisation_id}/prompt-config/{task_kind}` | Remove prompt override |

### Organisation Rubric Config API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/organisations/{organisation_id}/rubric-config` | List org's rubric overrides |
| POST | `/organisations/{organisation_id}/rubric-config` | Set rubric override for a skill |
| DELETE | `/organisations/{organisation_id}/rubric-config/{skill_slug}` | Remove rubric override |

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

### Org Config Resolution

#### Prompt Resolution (at render time)

```
1. Worker calls PromptRegistry.render(task_kind=LLMTaskKind.ASSISTANT, organisation_id=org_id, ...)
2. If organisation_id is not None:
   a. Look up OrganisationPromptConfig(organisation_id, task_kind)
   b. If found → use prompt_id + version_id from config
3. If not found → use global config (llm_assistant_prompt_id + llm_assistant_prompt_version_id)
```

#### Rubric Resolution (at marking time)

```
1. Assessment needs rubric for skill_slug="clarity" in organisation_id="org-123"
2. Look up OrganisationRubricConfig(organisation_id="org-123", skill_slug="clarity")
3. If found → use rubric_id + version_id from config
4. If not found → look up global rubric for skill_slug="clarity" (organisation_id IS NULL)
5. If found → use that rubric
6. If not found → error (no rubric available)
```

---

## File Impact Map

### New Files

- `modules/admin/domain/rubric_registry.py` - rubric registry for rendering
- `modules/admin/use_cases/rubric_service.py` - rubric CRUD operations
- `modules/admin/use_cases/org_config_service.py` - org prompt/rubric config CRUD
- `modules/admin/infra/org_config_repository.py` - org config persistence
- Migration scripts for data transformation

### Layer-by-Layer Changes

**Models (platform/db/models.py):**
- Add `PromptRecord` with organisation_id (replace existing flat table)
- Add `PromptVersionRecord` (replace existing)
- Add `RubricRecord` with unique (skill_slug, organisation_id) constraint
- Add `RubricVersionRecord` (new)
- Add `OrganisationPromptConfigRecord`
- Add `OrganisationRubricConfigRecord`
- Update `AssessmentRecord` - add prompt_version_id, rubric_version_id FKs
- Update `AttemptRecord` - add rubric_version_id FK
- Update `PracticeSessionRecord` - add rubric_version_id FK
- Update `ContentGenerationArtifactRecord` - add prompt_version_id FK
- Remove `RubricCriterionRecord` (merged into RubricVersion.criteria)

**Repository (modules/admin/infra/):**
- `prompt_repository.py` - complete rewrite for new model with org filtering
- `rubric_admin_repository.py` - complete rewrite for new model with org filtering
- `org_config_repository.py` - new for org prompt/rubric config

**Domain (modules/admin/domain/):**
- `prompt_registry.py` - change render() signature to use UUIDs, add org resolution
- `rubric_registry.py` - new, handles rubric resolution with org override
- `builtin_prompts.py` - update seeding to create Prompt + PromptVersion parents (global)

**Config (config.py):**
- Change all `llm_*_prompt_version: str` to `llm_*_prompt_id: UUID` + `llm_*_prompt_version_id: int`

**Runtime Config (engines/config/models.py):**
- `MarkingRuntimeConfig` - update per_skill and aggregation prompt references
- `CatalogGenerationRuntimeConfig` - update all prompt references

**Commands (modules/admin/contracts/commands.py):**
- `CreatePromptCommand` - add organisation_id field
- `CreateRubricCommand` - add organisation_id field
- `CreateOrganisationPromptConfigCommand` - new
- `CreateOrganisationRubricConfigCommand` - new
- Remove `RubricCriterionCommand`, `CreateRubricCriterionCommand` (criteria now embedded)

**Views (modules/admin/contracts/views.py):**
- `PromptView` - add organisation_id
- `PromptVersionView` - add prompt_id, restructure
- `RubricView` - add organisation_id, restructure
- `RubricCriterionView` - now embedded JSON, not separate model
- `OrganisationPromptConfigView` - new
- `OrganisationRubricConfigView` - new

**Services (modules/admin/use_cases/):**
- `prompt_service.py` - complete rewrite with org scoping
- `rubric_service.py` - new, handles rubric CRUD
- `org_config_service.py` - new, handles org prompt/rubric config
- `admin_service.py` - update rubric methods to new service

**Routes (entrypoints/http/routes/admin.py):**
- Restructure all prompt endpoints to use {prompt_id}
- Restructure all rubric endpoints to use {rubric_id}
- Add org config endpoints in organisations routes

**Workers (modules/catalog/workflows/generation/workers.py):**
- Update PromptRenderRequest creation in prompt_request_transform
- Update config references to use ID-based lookups
- Add organisation_id to request context where needed

**Assessment (modules/practice/workflows/assessment/marking_provider.py):**
- Update to use prompt_version_id, rubric_version_id FKs
- Add org-aware rubric resolution via RubricRegistry

**Persistence (modules/practice/infra/persistence.py):**
- Update to use FK-based lookups

**Queries (modules/practice/infra/queries.py):**
- Update rubric lookups to navigate rubric → rubric_version

---

## Migration Steps

### Phase 1: Schema Changes

1. Create new `prompts` table with organisation_id (nullable)
2. Create new `prompt_versions` table
3. Create new `rubrics` table with (skill_slug, organisation_id) unique constraint
4. Create new `rubric_versions` table
5. Create `organisation_prompt_configs` table
6. Create `organisation_rubric_configs` table
7. Add FK columns to AssessmentRecord, AttemptRecord, PracticeSessionRecord, ContentGenerationArtifactRecord

### Phase 2: Data Migration

8. Migrate PromptVersionRecord → Prompt + PromptVersion
   - Create global Prompt records (organisation_id = NULL) for each unique name
   - Link existing rows to parent via prompt_id
   - Set variables_schema, prompt_type on parent

9. Migrate RubricRecord → Rubric + RubricVersion
   - Create global Rubric records (organisation_id = NULL) for existing rubrics
   - Create RubricVersion records with criteria JSON
   - Drop RubricCriterionRecord table after migration

10. Populate FK columns in Assessment, Attempt, PracticeSession, ContentGenerationArtifact by joining on legacy string fields

11. Mark all existing records as status = published

### Phase 3: Code Migration

12. Update config.py - replace all string-based prompt versions with UUID + int pairs
13. Update runtime config models
14. Update PromptRegistry.render() signature and add org resolution
15. Create RubricRegistry with org resolution
16. Update PromptRenderRequest
17. Update all workers and workflows
18. Update API routes
19. Update repository layer
20. Update service layer

### Phase 4: Verification

21. Run all tests
22. Run smoke tests
23. Verify data integrity

### Phase 5: Cleanup

24. Drop legacy columns (prompt_versions.name, prompt_versions.prompt_type, rubrics.family, rubrics.version, rubrics.criteria)
25. Drop RubricCriterionRecord table

---

## Implementation Order

1. **Database layer** - new models, migrations
2. **Config** - update settings and runtime config models
3. **Repository layer** - prompt_repository, rubric_admin_repository, org_config_repository
4. **Domain layer** - prompt_registry (update with org resolution), rubric_registry (new)
5. **Service layer** - prompt_service (rewrite), rubric_service (new), org_config_service (new)
6. **API layer** - routes, commands, views for prompts, rubrics, and org configs
7. **Runtime consumers** - workers, assessment, practice
8. **Verification** - run tests, smoke tests

---

## Constraints & Decisions

- **Skills must exist before creating Rubrics** - no auto-creation
- **Org scoping pattern**: NULL organisation_id = global (platform-wide), non-NULL = org-scoped
- **Unique constraint on (skill_slug, organisation_id)** for Rubrics - allows global + org-specific per skill
- **Org admins can only create org-scoped resources** - global requires platform admin
- **Org prompt/rubric config is optional** - when not set, falls back to global defaults
- **Semantic versioning** - v1, v2, v3 (no dot notation)
- **Version selection is explicit** - agents must specify version_id at runtime
- **No migration of existing data** - current skills are placeholders, start fresh
- **RubricCriterionRecord removed** - criteria embedded directly in RubricVersion as JSON

---

## Open Questions

None - all decisions finalized.
