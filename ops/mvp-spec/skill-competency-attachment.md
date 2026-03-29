# Skill & Competency Attachment Model

## Problem Statement

The current system tracks skill-level performance through assessments, and aggregates skill scores into competencies via weighted combinations in the progression engine. However, there is no mechanism to:

1. Attach **competencies directly to questions** (prompt items), as distinct from attaching individual skills
2. Express that **all skills within a competency** are being tested by a single question
3. **Filter competency display** in learner progress to only show competencies that were explicitly targeted by the learner's practice content

This document proposes a competency-aware attachment model that sits between content authoring and assessment results.

---

## Background: Current Architecture

### Skills vs. Competencies

| Concept | Description | Tracked in |
|---|---|---|
| **Skill** | Atomic, assessable unit (e.g., `active-listening`, `negotiation`) | `SkillRecord`, rubric criteria keyed by `skill_slug` |
| **Competency** | Weighted aggregate of skills (e.g., `stakeholder-management` → `active-listening`, `empathy`, `expectation-setting`, `negotiation`) | `CompetencyRecord` + `CompetencySkillMapRecord` |

The relationship is defined in `CompetencySkillMapRecord`:

```
competency_slug → skill_slug (with weight)
```

Each competency has a set of constituent skills with weights summing to 1.0.

### Current Data Flow

```
PromptItemRecord
  ├── target_skill_slugs: list[str]         ✓ exists
  └── target_competency_slugs: list[str]    ✓ exists (on PromptItemRecord)
         │
         ├────────────────────────┐
         ▼                        ▼
  [PromptItemCreateCommand]   [CollectionCreateCommand]
         │
         ▼
  PracticePromptView           ← LOST HERE: no target_competency_slugs field
         │
         ▼
  ValidatedAssessmentPayload   ← LOST HERE: no target_competency_slugs field
         │
         ▼
  AssessmentRecord             ← LOST HERE: no target_competency_slugs field
         │
         ▼
  AssessmentSignal (progression input)
         │
         ▼
  Progression Engine           ← Only receives skill scores; derives competencies internally
         │
         ▼
  ProgressionSnapshot
    ├── dimension_states: skill-level
    └── competency_states: all competencies (always computed)
         │
         ▼
  CompetencyProgressView (frontend)
    └── ALL competencies shown — no "directly attached" flag
```

**Problem:** `target_competency_slugs` from the prompt item never reaches the assessment record or progression engine. The frontend displays all competencies regardless of which ones were actually targeted by the learner's practice.

---

## Proposed Model

### Core Concept: Competency Attachment

A prompt item (question) can have **both** skills and competencies attached:

| Attachment | Effect |
|---|---|
| **Skill attached** | That skill is individually assessed and shown in results |
| **Competency attached** | All constituent skills are automatically assessed (derived), AND the competency shows in results |
| **Both attached** | Skill is assessed once, shown individually AND under the competency aggregate |

### Rules

1. **Auto-derivation:** When a competency is attached to a question, all its constituent skills are automatically added to `target_skill_slugs`. The rubric therefore covers all needed criteria.

2. **No duplication:** If a skill is both (a) a constituent of an attached competency AND (b) independently attached, it appears once in `target_skill_slugs` (union dedup).

3. **Always contributes:** A skill always contributes to any competency it belongs to — regardless of whether that competency was attached. This means skill scores feed into competency aggregates even for competencies not directly attached.

4. **Display filter:** A competency appears in the learner's progress card **only if** at least one of the learner's assessed questions had that competency directly attached.

5. **Persistence:** The `target_competency_slugs` must survive through to the `AssessmentRecord` so the progression engine knows which competencies were "activated" by this assessment.

---

## Data Model Changes

### 1. `AssessmentRecord` (platform/db/models.py)

Add:
```python
target_competency_slugs: Mapped[list[str]] = mapped_column(JSON, default=list)
```

This mirrors the existing field on `PromptItemRecord` and `CollectionRecord`.

### 2. `ValidatedAssessmentPayload` (modules/practice/models.py)

Add:
```python
target_competency_slugs: list[str] = Field(default_factory=list)
```

Carries the data through the assessment pipeline.

### 3. `PracticePromptView` (modules/practice/workflows/assessment/models.py)

Add:
```python
target_competency_slugs: list[str]
```

Must be populated when building the prompt view from `PromptItemRecord` in `queries.py:load_start_prompt_context`.

### 4. `AssessmentSignal` (modules/practice/domain/practice.py)

Add:
```python
competency_slugs: list[str] = Field(default_factory=list)
```

Feeds into `ProgressionRefreshInput`.

### 5. `CompetencyProgressView` (modules/progression/contracts/views.py)

Add:
```python
directly_attached: bool = False
```

### 6. `ProgressionRefreshInput` (modules/progression/infra/repository.py)

Add:
```python
attached_competency_slugs: set[str]
```

Computed as the union of `competency_slugs` from all validated `AssessmentSignal` records for the learner.

### 7. `compute_progression_snapshot` (modules/progression/domain/progression.py)

Accept `attached_competency_slugs: set[str]` as an input. The core aggregation logic remains unchanged — all competencies are always computed. The `directly_attached` flag is set at the view layer.

---

## Auto-Derivation Logic

When a prompt item is created with `target_competency_slugs`:

```
Input:  target_competency_slugs = ["stakeholder-management"]
        target_skill_slugs = ["active-listening"]

Lookup CompetencySkillMapRecord for "stakeholder-management":
  → ["active-listening", "empathy", "expectation-setting", "negotiation"]

Union with explicitly-attached skills:
  → ["active-listening", "empathy", "expectation-setting", "negotiation"]

Result stored on PromptItemRecord:
  target_skill_slugs = ["active-listening", "empathy", "expectation-setting", "negotiation"]
  target_competency_slugs = ["stakeholder-management"]
```

The rubric criteria (keyed by `skill_slug`) will be triggered for all four skills. The competency slug is separately stored for results display and progression tracking.

### Validation (modules/catalog/domain/validators.py)

When creating a prompt item:
- All slugs in `target_competency_slugs` must exist in `CompetencyRecord`
- All slugs in `target_skill_slugs` must exist in `SkillRecord`
- For each competency in `target_competency_slugs`, at least one of its constituent skills must be in the union of `target_skill_slugs` (enforced implicitly by the auto-derivation)

---

## Progression Engine Integration

### Input

The progression engine receives:
- `assessments: list[AssessmentEvent]` — each with skill-level `dimension_scores`
- `competency_definitions: list[AggregateDefinition]` — all system competencies with skill weights
- `attached_competency_slugs: set[str]` — which competencies were directly attached

### Aggregation (unchanged)

The engine computes `competency_states` for **all** competencies in `competency_definitions`, weighted combination of constituent skill scores. This remains unchanged.

### Output

```python
class CompetencyProgressView:
    competency_slug: str
    name: str
    score: float
    confidence: float
    confidence_band: str
    delta: float
    skills: list[SkillProgressView]
    directly_attached: bool   # NEW
```

`directly_attached = competency_slug in attached_competency_slugs`

---

## Frontend Changes

### Types (frontend/src/data/types/practice.ts)

```typescript
export interface CompetencyProgressView {
  readonly slug: string;
  readonly name: string;
  readonly description: string;
  readonly skills: SkillProgressView[];
  readonly overall_score: number;
  readonly confidence: 'low' | 'medium' | 'high';
  readonly directly_attached: boolean;  // NEW
}
```

### Display Filter (frontend/src/pages/Progress.tsx)

```tsx
{competencies
  .filter(c => c.directly_attached)
  .map(comp => (
    <CompetencyCard key={comp.slug} competency={...} />
  ))}
```

---

## Detailed Changes by File

### Backend

| File | Change |
|---|---|
| `platform/db/models.py` | Add `target_competency_slugs` to `AssessmentRecord` |
| `modules/practice/models.py` | Add `target_competency_slugs` to `ValidatedAssessmentPayload` |
| `modules/practice/workflows/assessment/models.py` | Add `target_competency_slugs` to `PracticePromptView` |
| `modules/practice/domain/practice.py` | Add `competency_slugs` to `AssessmentSignal` |
| `modules/practice/infra/queries.py` | Populate `target_competency_slugs` when building `PracticePromptView` |
| `modules/practice/infra/persistence.py` | Persist `target_competency_slugs` to `AssessmentRecord` |
| `modules/practice/workflows/assessment_service.py` | Pass `target_competency_slugs` through `ValidatedAssessmentPayload` |
| `modules/practice/infra/repository.py` | Populate `AssessmentSignal.competency_slugs` from `AssessmentRecord` |
| `modules/progression/infra/repository.py` | Build `attached_competency_slugs` as union across learner's assessments |
| `modules/progression/domain/progression.py` | Accept `attached_competency_slugs` (no change to aggregation math) |
| `modules/progression/contracts/views.py` | Add `directly_attached: bool` to `CompetencyProgressView` |
| `modules/progression/infra/repository.py` (snapshot view) | Set `directly_attached` when building `CompetencyProgressView` |
| `modules/catalog/domain/validators.py` | Validate competency slugs exist on prompt item creation |
| `modules/catalog/workflows/prompt_items/service.py` | Auto-derive skills from competencies before persistence |

### Frontend

| File | Change |
|---|---|
| `frontend/src/data/types/practice.ts` | Add `directly_attached: boolean` to `CompetencyProgressView` |
| `frontend/src/pages/Progress.tsx` | Filter competencies on `directly_attached` |

---

## Scenarios

### Scenario A: Competency attached, no standalone skills

```
target_competency_slugs = ["stakeholder-management"]
target_skill_slugs (after auto-derive) = all skills in stakeholder-management

Marking: all skills assessed
Results shown:
  - stakeholder-management: YES (competency score visible)
  - communication: NO (not attached, but skills still contribute internally)
```

### Scenario B: Standalone skill attached (no competency)

```
target_competency_slugs = []
target_skill_slugs = ["active-listening"]

Marking: active-listening assessed
Results shown:
  - stakeholder-management: NO (not attached)
  - communication: NO (not attached)
  - (active-listening score exists as a dimension but no competency card shown)
```

### Scenario C: Both competency and standalone skill

```
target_competency_slugs = ["stakeholder-management"]
target_skill_slugs (after auto-derive) = all skills in stakeholder-management
(where "active-listening" appears in both the competency AND was independently chosen)

Marking: all skills assessed (once)
Results shown:
  - stakeholder-management: YES
  - active-listening shown under the competency card
  - active-listening also potentially shown as its own standalone skill card
    (TBD: does a standalone skill show if it's already shown under a competency?)
```

### Scenario D: Multiple competencies across a scenario session

A scenario with 3 prompt steps:
- Step 1: competency `stakeholder-management` attached
- Step 2: competency `communication` attached
- Step 3: competency `stakeholder-management` attached again

After session completion:
```
attached_competency_slugs = {stakeholder-management, communication}

Competency progress cards shown:
  - stakeholder-management: YES (directly attached)
  - communication: YES (directly attached)
  - teamwork: NO (skills may contribute internally, but not displayed)
```

---

## Open Questions

### OQ1: Standalone skill display when competency also attached

If `active-listening` is (a) part of `stakeholder-management` (attached) AND (b) independently attached, should it appear TWICE in results (once under the competency card, once as its own card)?

**Proposed:** Yes — the model says skills always show individually. If a skill is attached standalone, it appears as its own result regardless of competency membership. The competency card shows the aggregate score; the skill card shows the individual score.

### OQ2: Skill auto-derive vs explicit override

Should an author be able to attach a competency but EXCLUDE some of its constituent skills (i.e., mark only a subset of skills even though the competency is attached)?

**Proposed:** No — attachment is binary. If a competency is attached, all its constituent skills are tested. If you want to test only some skills, attach only those skills individually.

### OQ3: Competency aggregation when not directly attached

When a competency is NOT directly attached, should its skills still contribute to it?

**Proposed:** Yes — this preserves the "skills always contribute" rule. A learner who practices `active-listening` (which belongs to `stakeholder-management`) will see their `stakeholder-management` competency score increase, even though the competency card is not displayed.

---

## Migration Considerations

### Existing data

Existing `AssessmentRecord` rows will have `target_competency_slugs = []`. These will be treated as:
- No competencies directly attached
- All competency states computed but `directly_attached = false`
- No visible competency cards for historical assessments (correct — the questions weren't competency-targeted)

### Backward compatibility

The `auto-derive` logic only fires when `target_competency_slugs` is non-empty. Existing prompt item creation (without competency attachment) is unaffected.

---

## Adoption Checklist

1. Add `target_competency_slugs` to `AssessmentRecord`, `ValidatedAssessmentPayload`, `PracticePromptView`
2. Wire `target_competency_slugs` from `PromptItemRecord` → `PracticePromptView` → `ValidatedAssessmentPayload` → `AssessmentRecord`
3. Add `competency_slugs` to `AssessmentSignal`; populate from `AssessmentRecord`
4. Add `attached_competency_slugs` computation in `ProgressionRepository.load_refresh_input`
5. Add `directly_attached` to `CompetencyProgressView`; set in snapshot view builder
6. Implement auto-derive skills logic in prompt item creation service
7. Add competency existence validation in prompt item validators
8. Update frontend types and filter in Progress page
