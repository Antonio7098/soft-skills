# Org-Scoped Prompts and Skills Proposal

## Current State

### What is Org-Scoped vs Global

| Entity | Has `organisation_id` | Current Scoping |
|--------|----------------------|-----------------|
| `Collection` | ✅ Yes (nullable) | Org-scoped or global (NULL = global hub) |
| `PromptItem` | ❌ No | Inherits from parent `Collection` |
| `Scenario` | ❌ No | Inherits from parent `Collection` |
| `Skill` | ❌ No | **Global platform-wide** |
| `Competency` | ❌ No | **Global platform-wide** |
| `Rubric` | ❌ No | **Global platform-wide** |

### Data Model Details

**CollectionRecord** (`backend/src/soft_skills_backend/platform/db/models.py:188-217`)
```python
class CollectionRecord(Base):
    __tablename__ = "collections"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    author_user_id: Mapped[str] = mapped_column(String(32), index=True)
    organisation_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("organisations.id"), index=True, nullable=True
    )  # ← ORG SCOPING
    # ... rest of fields
```

**PromptItemRecord** (`backend/src/soft_skills_backend/platform/db/models.py:219-236`)
```python
class PromptItemRecord(Base):
    __tablename__ = "prompt_items"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    collection_id: Mapped[str] = mapped_column(String(32), index=True)
    author_user_id: Mapped[str] = mapped_column(String(32), index=True)
    # NOTE: NO organisation_id - inherits from Collection
    # ... rest of fields
```

**SkillRecord** (`backend/src/soft_skills_backend/platform/db/models.py:126-134`)
```python
class SkillRecord(Base):
    __tablename__ = "skills"
    slug: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    description: Mapped[str] = mapped_column(Text)
    # NOTE: NO organisation_id - global platform-defined
```

**CompetencyRecord** (`backend/src/soft_skills_backend/platform/db/models.py:136-144`)
```python
class CompetencyRecord(Base):
    __tablename__ = "competencies"
    slug: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    description: Mapped[str] = mapped_column(Text)
    # NOTE: NO organisation_id - global platform-defined
```

**RubricRecord** (`backend/src/soft_skills_backend/platform/db/models.py:156-168`)
```python
class RubricRecord(Base):
    __tablename__ = "rubrics"
    rubric_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    family: Mapped[str] = mapped_column(String(64), index=True)
    version: Mapped[str] = mapped_column(String(32))
    content_type: Mapped[str] = mapped_column(String(64), index=True)
    # ... rest of fields
    # NOTE: NO organisation_id - global platform-defined
```

### Current Discovery Tier Logic

From `validators.py:55-62`:
- `private`: `lifecycle_state != "published_public"`
- `global_public`: `organisation_id is None AND verification_state == "verified" AND lifecycle_state == "published_public"`
- `org_public`: `organisation_id is not None AND lifecycle_state == "published_public"`
- `standard_public`: `organisation_id is None AND verification_state != "verified" AND lifecycle_state == "published_public"`

### Current API Routes

**Collections** (`/api/collections`):
- `GET /` - List with optional `organisation_id` filter
- `POST /` - Create with optional `organisation_id`
- `GET /discover` - Global hub (org_id=NULL, verified_public)

**Skills/Taxonomy** (`/api/skills`):
- `GET /catalog` - Returns global taxonomy snapshot (skills, competencies, rubrics)
- `POST /bootstrap-canon` - Seed global taxonomy

**Admin** (`/api/admin`):
- Rubric management (global)

---

## Problem Statement

### 1. PromptItems and Scenarios Cannot Exist Independently

Currently, `PromptItemRecord` and `ScenarioRecord` have no `organisation_id`. They **must** belong to a `Collection`. This means:

- A standalone prompt item cannot be org-scoped without being part of a collection
- Organisations cannot maintain a library of reusable prompt items separate from collections
- Prompt items cannot be shared across collections within an org without manual duplication

### 2. Skills, Competencies, and Rubrics Are Fully Global

The entire taxonomy (skills, competencies, rubrics) is seeded once globally via `TaxonomyService.bootstrap()` and is shared across all organisations. This is problematic because:

- Organisations may need **custom skills** relevant to their industry (e.g., "healthcare communication" for a healthcare org)
- Organisations may need **custom competencies** that map to their internal frameworks
- Organisations may need **custom rubrics** with different criteria or weightings
- The platform-defined taxonomy cannot accommodate org-specific specializations

### 3. No Separation Between Platform Canon and Org Customization

The current model doesn't distinguish between:
- Platform-wide canonical skills/competencies (the "canon")
- Organisation-specific custom skills/competencies

---

## Proposed Solution

### Core Principle

Allow organisations to have their own custom prompts, skills, competencies, and rubrics while preserving the platform-wide canonical taxonomy. Org-specific content coexists with global content.

### Data Model Changes

#### 1. Add `organisation_id` to `PromptItemRecord`

```python
class PromptItemRecord(Base):
    __tablename__ = "prompt_items"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    collection_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)  # nullable now
    author_user_id: Mapped[str] = mapped_column(String(32), index=True)
    organisation_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("organisations.id"), index=True, nullable=True
    )  # NEW: allows standalone org-scoped prompts
    # ... rest unchanged
```

#### 2. Add `organisation_id` to `ScenarioRecord`

```python
class ScenarioRecord(Base):
    __tablename__ = "scenarios"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    collection_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)  # nullable now
    author_user_id: Mapped[str] = mapped_column(String(32), index=True)
    organisation_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("organisations.id"), index=True, nullable=True
    )  # NEW
    # ... rest unchanged
```

#### 3. Add `organisation_id` to `SkillRecord`

```python
class SkillRecord(Base):
    __tablename__ = "skills"
    slug: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)  # unique constraint needs adjustment
    description: Mapped[str] = mapped_column(Text)
    organisation_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("organisations.id"), index=True, nullable=True
    )  # NEW: NULL = platform canon
    # composite unique constraint: (slug, organisation_id)
```

**Key insight**: Platform canonical skills have `organisation_id=NULL`. Org-specific skills have a non-NULL `organisation_id`. The (slug, organisation_id) pair must be unique.

#### 4. Add `organisation_id` to `CompetencyRecord`

```python
class CompetencyRecord(Base):
    __tablename__ = "competencies"
    slug: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)  # unique constraint needs adjustment
    description: Mapped[str] = mapped_column(Text)
    organisation_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("organisations.id"), index=True, nullable=True
    )  # NEW: NULL = platform canon
    # composite unique constraint: (slug, organisation_id)
```

#### 5. Add `organisation_id` to `RubricRecord`

```python
class RubricRecord(Base):
    __tablename__ = "rubrics"
    rubric_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    family: Mapped[str] = mapped_column(String(64), index=True)
    version: Mapped[str] = mapped_column(String(32))
    content_type: Mapped[str] = mapped_column(String(64), index=True)
    organisation_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("organisations.id"), index=True, nullable=True
    )  # NEW: NULL = platform canon
    # ... rest unchanged
```

#### 6. Add `OrganisationSkillMapRecord` (for org-specific skill-to-competency mappings)

```python
class OrganisationSkillMapRecord(Base):
    """Mapping between org competencies and org skills (overrides canon for that org)."""
    __tablename__ = "org_skill_maps"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organisation_id: Mapped[str] = mapped_column(String(32), index=True)
    competency_slug: Mapped[str] = mapped_column(String(64), index=True)
    skill_slug: Mapped[str] = mapped_column(String(64), index=True)
    weight: Mapped[float]
    __table_args__ = (
        UniqueConstraint("organisation_id", "competency_slug", "skill_slug"),
    )
```

**Note**: Platform canonical `CompetencySkillMapRecord` remains unchanged. When an org has its own competency/skill mapping, it uses `OrganisationSkillMapRecord` instead.

### API Changes

#### 1. Taxonomy/Catalog Endpoint Enhancement

**Current**: `GET /api/skills/catalog` returns global taxonomy only.

**Proposed**: Add optional query parameter:
```
GET /api/skills/catalog?organisation_id={org_id}
```

Response includes:
- Platform canonical skills/competencies (organisation_id=NULL)
- Org-specific skills/competencies (organisation_id=matching org)

**Access control**: Org members can see their org's custom taxonomy. Non-members cannot.

#### 2. New Endpoints for Org-Scoped Taxonomy Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/organisations/{org_id}/skills` | Create org-specific skill |
| `GET` | `/organisations/{org_id}/skills` | List org skills |
| `PATCH` | `/organisations/{org_id}/skills/{skill_slug}` | Update org skill |
| `DELETE` | `/organisations/{org_id}/skills/{skill_slug}` | Delete org skill |
| `POST` | `/organisations/{org_id}/competencies` | Create org competency |
| `GET` | `/organisations/{org_id}/competencies` | List org competencies |
| `PATCH` | `/organisations/{org_id}/competencies/{competency_slug}` | Update org competency |
| `DELETE` | `/organisations/{org_id}/competencies/{competency_slug}` | Delete org competency |
| `POST` | `/organisations/{org_id}/rubrics` | Create org rubric |
| `GET` | `/organisations/{org_id}/rubrics` | List org rubrics |
| `PATCH` | `/organisations/{org_id}/rubrics/{rubric_id}` | Update org rubric |
| `DELETE` | `/organisations/{org_id}/rubrics/{rubric_id}` | Delete org rubric |

#### 3. New Endpoints for Standalone PromptItems and Scenarios

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/organisations/{org_id}/prompt-items` | Create standalone org prompt |
| `GET` | `/organisations/{org_id}/prompt-items` | List org prompts |
| `GET` | `/organisations/{org_id}/prompt-items/{item_id}` | Get org prompt |
| `PATCH` | `/organisations/{org_id}/prompt-items/{item_id}` | Update org prompt |
| `DELETE` | `/organisations/{org_id}/prompt-items/{item_id}` | Delete org prompt |
| `POST` | `/organisations/{org_id}/scenarios` | Create standalone org scenario |
| `GET` | `/organisations/{org_id}/scenarios` | List org scenarios |
| `GET` | `/organisations/{org_id}/scenarios/{scenario_id}` | Get org scenario |
| `PATCH` | `/organisations/{org_id}/scenarios/{scenario_id}` | Update org scenario |
| `DELETE` | `/organisations/{org_id}/scenarios/{scenario_id}` | Delete org scenario |

#### 4. Collection Creation with Org Prompts/Skills

Existing `CollectionCreateCommand` and related commands already have `organisation_id: str | None`. These remain unchanged.

When creating a collection, the org can reference:
- Platform canonical skills/competencies
- Org-specific skills/competencies (if org_id matches)

Validation in `validators.py` must be updated to allow both.

### Visibility Rules

#### Skills/Competencies
- Platform canon (organisation_id=NULL): Visible to all
- Org-specific: Visible only to org members

#### PromptItems/Scenarios
- With collection_id: Visibility governed by collection rules
- Standalone with organisation_id: Visible to org members

#### Rubrics
- Platform canon (organisation_id=NULL): Visible to all
- Org-specific: Visible only to org members

### Updated Discovery Tier Logic

With org-scoped skills/competencies, the `discovery_tier_for_collection` function remains unchanged since it operates at the collection level. However, the taxonomy catalog now returns a merged view:

```
GET /api/skills/catalog?organisation_id=X
Response:
{
  "skills": [
    ... platform canonical skills ...,
    ... org X specific skills ...
  ],
  "competencies": [
    ... platform canonical competencies ...,
    ... org X specific competencies ...
  ],
  "rubrics": [
    ... platform canonical rubrics ...,
    ... org X specific rubrics ...
  ]
}
```

---

## Migration Approach

### Phase 1: Database Schema Migration

```sql
-- Add organisation_id to prompt_items (nullable to preserve existing)
ALTER TABLE prompt_items ADD COLUMN organisation_id VARCHAR(32)
  REFERENCES organisations(id) INDEXABLE;

-- Add organisation_id to scenarios (nullable to preserve existing)
ALTER TABLE scenarios ADD COLUMN organisation_id VARCHAR(32)
  REFERENCES organisations(id) INDEXABLE;

-- Add organisation_id to skills (nullable for platform canon)
ALTER TABLE skills ADD COLUMN organisation_id VARCHAR(32)
  REFERENCES organisations(id) INDEXABLE;
-- Add composite unique constraint
ALTER TABLE skills ADD CONSTRAINT uq_skill_org_slug
  UNIQUE (slug, organisation_id);

-- Add organisation_id to competencies (nullable for platform canon)
ALTER TABLE competencies ADD COLUMN organisation_id VARCHAR(32)
  REFERENCES organisations(id) INDEXABLE;
-- Add composite unique constraint
ALTER TABLE competencies ADD CONSTRAINT uq_competency_org_slug
  UNIQUE (slug, organisation_id);

-- Add organisation_id to rubrics (nullable for platform canon)
ALTER TABLE rubrics ADD COLUMN organisation_id VARCHAR(32)
  REFERENCES organisations(id) INDEXABLE;

-- New table for org-specific competency-skill mappings
CREATE TABLE org_skill_maps (
  id SERIAL PRIMARY KEY,
  organisation_id VARCHAR(32) NOT NULL REFERENCES organisations(id),
  competency_slug VARCHAR(64) NOT NULL,
  skill_slug VARCHAR(64) NOT NULL,
  weight FLOAT NOT NULL DEFAULT 1.0,
  UNIQUE (organisation_id, competency_slug, skill_slug)
);
CREATE INDEX ix_org_skill_maps_org ON org_skill_maps(organisation_id);
```

### Phase 2: Code Updates

1. **Update SQLAlchemy models** (`models.py`)
   - Add `organisation_id` to all relevant records
   - Update unique constraints for skills/competencies

2. **Update domain models** (`catalog/domain/models.py`)
   - Add `organisation_id` to `PromptItemView`, `ScenarioView`
   - Add `organisation_id` to command models

3. **Update validators** (`catalog/domain/validators.py`)
   - Allow both platform canon and org-specific skills/competencies in content validation
   - Update `require_existing_skills` and `require_existing_competencies` to check org context

4. **Update services** (`catalog/*/service.py`, `taxonomy/service.py`)
   - Handle org-scoped content in CRUD operations
   - Merge platform canon with org-specific in taxonomy snapshot

5. **Update routes** (`entrypoints/http/routes/`)
   - Add new endpoints for org-scoped taxonomy management
   - Add new endpoints for standalone prompt items and scenarios
   - Update existing catalog endpoint to accept `organisation_id` query param

6. **Update auth/permissions**
   - Ensure only org members can access org-specific content
   - Platform canon remains globally readable

### Phase 3: Backward Compatibility

- All existing `collection_id`-linked prompt items and scenarios continue to work
- Existing code that doesn't pass `organisation_id` continues to function (NULL = platform canon)
- Taxonomies without `organisation_id` are treated as platform canon

### Rollout Sequence

1. **Deploy schema migration** (backward compatible - all columns nullable)
2. **Deploy code changes** (fully backward compatible)
3. **Seed any required org-specific taxonomy** (post-migration, as needed)

---

## Priority and Effort Estimate

### Priority: HIGH

**Justification**:
- Organisations cannot customize skills/competencies to match their internal frameworks
- Standalone prompt items cannot be org-scoped without collection dependency
- Blocks org-specific assessment criteria customization

### Effort Estimate

| Component | Effort | Notes |
|-----------|--------|-------|
| Schema migration | Medium | 5 tables modified, 1 new table |
| SQLAlchemy model updates | Small | Add 1 field each to 5 models |
| Domain model updates | Small | Add org_id to view/command models |
| Validator updates | Medium | Handle both canon and org-specific in lookups |
| TaxonomyService updates | Medium | Merge canon + org-specific in snapshot |
| CatalogService updates | Medium | Handle standalone org-scoped prompts/scenarios |
| New API routes (skills) | Medium | 4 endpoints × 3 entities (skills, competencies, rubrics) |
| New API routes (prompts) | Medium | 5 endpoints × 2 entities (prompts, scenarios) |
| Auth/permission updates | Small | Org-only access for org-specific content |
| Testing | Large | Integration tests for all new paths |
| Documentation updates | Small | API docs, spec docs |

**Total estimated**: ~3-4 sprints (assuming 2-week sprints)

### Risk Factors

1. **Slug collision**: Org-specific skills could have same slug as platform canon. Solution: composite unique constraint (slug, organisation_id) handles this naturally.
2. **Content validation complexity**: Validating that org content references valid skills becomes more complex. Solution: validators check both canon and org-specific tables.
3. **Taxonomy snapshot performance**: Merging canon + org-specific could slow the catalog endpoint. Solution: index on organisation_id, consider caching.

---

## Alternatives Considered

### Alternative 1: Clone Entire Taxonomy Per Org

Instead of allowing NULL (canon) and non-NULL (org), clone the entire taxonomy per org.

**Rejected because**:
- Massive data duplication
- Platform canon updates don't propagate to orgs
- Much higher migration complexity

### Alternative 2: "Extension" Model (Canon + Org Overrides)

Have orgs only define "extensions" to the canon (delta only).

**Rejected because**:
- Complex override logic
- Harder to understand which skills are canon vs org
- The simpler nullable approach works well

### Alternative 3: Separate Tables for Org Content

Create entirely separate `org_skills`, `org_competencies` tables.

**Rejected because**:
- More complex joins for taxonomy snapshot
- Harder to reason about (which table do I query?)
- The nullable FK approach is cleaner

---

## Open Questions

1. **Org skill deletion**: If an org deletes a skill that is used in published content, what happens? (Same issue exists for platform canon skills.)
2. **Skill slug namespaces**: Should org-specific skill slugs be namespaced (e.g., `acme:healthcare-communication`) or just co-exist with canon slugs?
3. **Cross-org content sharing**: Can content created in one org be shared to another? (Not in scope for MVP, but worth considering for future.)
