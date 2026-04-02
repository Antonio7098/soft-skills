# App-Agnostic Engine Layer

## 1. Overview

The `engines/` package (`backend/src/soft_skills_backend/engines/`) contains three app-agnostic engines that provide reusable assessment, progression, and recommendation logic independent of any domain-specific taxonomy. These engines contain zero assumptions about skills, competencies, or soft-skills — domain modules supply prompt content, rubric criteria, criterion semantics, and score interpretation rules through adapter layers.

**Dependency flow**: `Stageflow orchestrates → Engines compute → Modules adapt`.

All three engines are pure deterministic computation engines (marking includes LLM interaction but its aggregation/validation is deterministic). Progression and recommendation have no external dependencies whatsoever.

### 1.1 Package Structure

```
engines/
├── __init__.py                    — Exports marking, progression, recommendation subpackages
├── config/                        — Versioned JSON config artifacts + typed loaders
│   ├── __init__.py                — Re-exports the four loader functions
│   ├── models.py                  — Pydantic config models (MarkingRuntimeConfig, CatalogGenerationRuntimeConfig)
│   ├── loader.py                  — Artifact loading with validation and @lru_cache
│   └── artifacts/                 — Reviewed JSON files
│       ├── soft_skills_marking_runtime.v1.json
│       ├── soft_skills_progression_engine.v1.json
│       ├── soft_skills_recommendation_engine.v1.json
│       └── soft_skills_catalog_generation_runtime.v1.json
├── marking/                       — Assessment judgment engine
│   ├── __init__.py                — Re-exports all contracts + domain + use_case types
│   ├── contracts/
│   │   ├── __init__.py
│   │   └── models.py              — Canonical schemas (Prompt, Rubric, Decision)
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── validation.py          — Decision validation rules
│   │   ├── rubric_repository.py   — RubricRepository protocol + SqlAlchemyRubricRepository
│   │   └── per_skill_aggregation.py — Deterministic score/strength/weakness aggregation
│   └── use_cases/
│       ├── __init__.py
│       ├── decision_builder.py    — MarkingDecision assembly from criterion results
│       └── structured_output.py   — TypedLLMOutput, PromptLibrary, StructuredOutputRejectionError
├── progression/                   — Learner capability aggregation engine
│   ├── __init__.py                — Re-exports all contracts + domain types
│   ├── contracts/
│   │   ├── __init__.py
│   │   └── models.py              — Assessment events, dimension/aggregate states, config
│   └── domain/
│       ├── __init__.py
│       └── progression.py         — Decay weighting, confidence, gating, snapshot computation
└── recommendation/                — Next-step recommendation engine
    ├── __init__.py                — Re-exports all contracts + domain types
    ├── contracts/
    │   ├── __init__.py
    │   └── models.py              — Candidate items, weights, config, recommendation output
    └── domain/
        ├── __init__.py
        └── recommendation.py      — Scoring components, constraint enforcement, ranking
```

### 1.2 Module Consumption Map

| Module | Engine | Integration Point |
|--------|--------|-------------------|
| `practice/` | Marking | `AssessmentMarkingProvider` uses `RubricRepository`, `TypedLLMOutput`, per-skill aggregation |
| `progression/` | Progression | `compute_progression_snapshot()` adapts `AssessmentSignal` → `AssessmentEvent` |
| `progression/` | Recommendation | `compute_recommendation()` adapts `CatalogCandidate` → `CandidateItem` |
| `evaluation/` | Marking | `MarkingBenchmarkRunner` exercises full marking pipeline against golden cases |

---

## 2. Configuration System

### 2.1 Config Loader (`config/loader.py`)

All engine configuration is loaded from versioned JSON artifacts in `config/artifacts/`. Each loader is decorated with `@lru_cache(maxsize=1)` for single-load performance.

**Loader functions**:

| Function | Artifact | Returns |
|----------|----------|---------|
| `load_marking_runtime_config()` | `soft_skills_marking_runtime.v1.json` | `MarkingRuntimeConfig` |
| `load_progression_engine_config()` | `soft_skills_progression_engine.v1.json` | `ProgressionEngineConfig` |
| `load_recommendation_engine_config()` | `soft_skills_recommendation_engine.v1.json` | `RecommendationEngineConfig` |
| `load_catalog_generation_runtime_config()` | `soft_skills_catalog_generation_runtime.v1.json` | `CatalogGenerationRuntimeConfig` |

**Error codes**:

| Code | Condition |
|------|-----------|
| `SS-VALIDATION-038` | Artifact file not found (`FileNotFoundError`) |
| `SS-VALIDATION-039` | Invalid JSON in artifact (`json.JSONDecodeError`) |
| `SS-VALIDATION-040` | Schema validation failure (`pydantic.ValidationError`) |

The internal `_load_json_artifact()` helper handles all three error paths uniformly, wrapping each in `validation_error()` with the artifact path and specific reason.

### 2.2 Config Models (`config/models.py`)

#### `MarkingRuntimeConfig`

```python
class MarkingRuntimeConfig(BaseModel):
    per_skill_prompt_name: str
    per_skill_prompt_version: str
    aggregation_prompt_name: str
    aggregation_prompt_version: str
    per_skill_output_schema_version: str
    aggregation_output_schema_version: str
    output_schema_version: str
    config_version: str
    engine_version: str
    max_parallel_skill_children: int
```

Properties:
- `prompt_name` → delegates to `per_skill_prompt_name`
- `prompt_version` → delegates to `per_skill_prompt_version`

**Current artifact values** (`soft_skills_marking_runtime.v1.json`):
```json
{
  "per_skill_prompt_name": "assessment-per-skill",
  "per_skill_prompt_version": "assessment.quick-practice.v1",
  "aggregation_prompt_name": "assessment-aggregation",
  "aggregation_prompt_version": "assessment.aggregation.v1",
  "max_parallel_skill_children": 4
}
```

#### `CatalogGenerationRuntimeConfig`

```python
class CatalogGenerationRuntimeConfig(BaseModel):
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
    output_schema_version: str
    config_version: str
    max_parallel_prompt_item_children: int
    max_parallel_scenario_children: int
```

---

## 3. Marking Engine

**Purpose**: Takes a prompt, candidate response, and rubric → produces a validated judgment artifact. Portable across domains (soft skills, education, certification, QA review).

### 3.1 Contracts (`marking/contracts/models.py`)

#### `PromptTemplate`

Versioned prompt template used to render an evaluator prompt.

```python
class PromptTemplate(BaseModel):
    name: str
    version: str
    template: str
```

#### `RenderedPrompt`

Resolved prompt payload with stable version metadata.

```python
class RenderedPrompt(BaseModel):
    name: str
    version: str
    content: str
```

#### `PromptArtifact`

Optional structured context supplied alongside a prompt.

```python
class PromptArtifact(BaseModel):
    artifact_id: str
    artifact_type: str
    title: str
    body: str
```

#### `PromptContract`

Versioned marking prompt contract. All text fields are validated non-blank.

```python
class PromptContract(BaseModel):
    prompt_id: str
    prompt_version: str
    prompt_type: str
    prompt_text: str
    response_mode: str
    rubric_id: str
    artifacts: list[PromptArtifact] = Field(default_factory=list)
    domain_tags: list[str] = Field(default_factory=list)
```

#### `CandidateResponse`

Canonical response contract submitted for marking. All text fields validated non-blank.

```python
class CandidateResponse(BaseModel):
    response_id: str
    prompt_id: str
    actor_id: str
    response_mode: str
    content: str
    submitted_at: datetime
```

#### `RubricScale`

Numeric scale used by a rubric.

```python
class RubricScale(BaseModel):
    minimum_score: int
    maximum_score: int
```

#### `RubricLevel`

One scored rubric level with examples. Level must be ≥ 1. Examples must be non-empty with at least one non-blank item.

```python
class RubricLevel(BaseModel):
    level: int = Field(ge=1)
    description: str
    examples: list[str] = Field(min_length=1)
```

Default levels (1-5) are generated by `_default_rubric_levels()` when none are specified.

#### `RubricCriterion`

One rubric criterion. Weight must be > 0 (default 1.0). `required` defaults to `True`.

```python
class RubricCriterion(BaseModel):
    criterion_ref: str
    title: str | None = None
    description: str
    weight: float = Field(default=1.0, gt=0)
    required: bool = True
    levels: list[RubricLevel] = Field(default_factory=_default_rubric_levels, min_length=1)
```

#### `RubricDefinition`

Versioned rubric contract. Must contain at least one criterion.

```python
class RubricDefinition(BaseModel):
    rubric_id: str
    rubric_version: str
    scale: RubricScale
    criteria: list[RubricCriterion] = Field(min_length=1)
```

#### `EvidenceReference`

Response-linked evidence supporting a judgment. All text fields validated non-blank.

```python
class EvidenceReference(BaseModel):
    criterion_ref: str
    quote: str
    explanation: str
```

#### `CriterionJudgment`

Judgment for a single rubric criterion. Must include at least one evidence reference.

```python
class CriterionJudgment(BaseModel):
    criterion_ref: str
    score: int
    rationale: str
    evidence: list[EvidenceReference] = Field(min_length=1)
```

#### `MarkingDecision`

Finalized generic marking decision contract. All lists require at least one non-blank item.

```python
class MarkingDecision(BaseModel):
    marking_id: str
    response_id: str
    prompt_id: str
    prompt_version: str
    rubric_id: str
    rubric_version: str
    engine_version: str
    provider: str
    model_slug: str
    overall_score: int
    criterion_judgments: list[CriterionJudgment] = Field(min_length=1)
    rationale: str
    strengths: list[str] = Field(min_length=1)
    weaknesses: list[str] = Field(min_length=1)
    next_actions: list[str] = Field(min_length=1)
    trace_id: str
    created_at: datetime
```

### 3.2 Domain Logic

#### Validation (`marking/domain/validation.py`)

`validate_marking_decision()` performs cross-contract validation of a finalized `MarkingDecision` against the source `PromptContract`, `CandidateResponse`, and `RubricDefinition`.

**Validation rules** (all raise on failure):

| Check | Error Code | Description |
|-------|------------|-------------|
| Prompt ID match | `SS-VALIDATION-034` | `decision.prompt_id == prompt.prompt_id` |
| Response ID match | `SS-VALIDATION-035` | `decision.response_id == response.response_id` |
| Prompt version match | `SS-VALIDATION-036` | `decision.prompt_version == prompt.prompt_version` |
| Rubric metadata match | `SS-VALIDATION-037` | `decision.rubric_id` and `decision.rubric_version` match rubric |
| No repeated criteria | `SS-SCORING-010` | All `criterion_ref` values in judgments are unique |
| Full criterion coverage | `SS-SCORING-011` | Judgment criteria match required rubric criteria exactly |
| Score in range | `SS-SCORING-012` | Each criterion score within `[minimum_score, maximum_score]` |
| Evidence ref match | `SS-SCORING-013` | Each evidence `criterion_ref` matches its parent judgment |
| Evidence grounding | `SS-SCORING-014` | Evidence quotes must be ≥ 6 chars and found in normalized response text |
| Overall score in range | `SS-SCORING-015` | Overall score within rubric scale bounds |
| No contradictions | `SS-SCORING-016` | Strengths and weaknesses must not overlap (normalized) |
| Score consistency | `SS-SCORING-017` | `|overall_score - round(average_criterion_score)| ≤ 1` |

Evidence grounding uses `_normalize_text()` (lowercase, collapse whitespace) to check that the normalized quote appears as a substring of the normalized response content.

#### Rubric Repository (`marking/domain/rubric_repository.py`)

**Protocol**:

```python
class RubricRepository(Protocol):
    def get_rubric_definition(
        self,
        rubric_id: str,
        *,
        required_skill_slugs: Iterable[str] | None = None,
    ) -> RubricDefinition: ...

    def get_skill_criterion(self, rubric_id: str, skill_slug: str) -> RubricCriterion: ...
```

**`SqlAlchemyRubricRepository`**: SQLAlchemy-backed implementation.

`get_rubric_definition()`:
1. Loads `RubricRecord` by ID; raises `SS-VALIDATION-071` if not found
2. Queries latest published `RubricVersionRecord`; raises `SS-VALIDATION-074` if none
3. Filters criteria by `required_skill_slugs` (if provided); raises `SS-VALIDATION-072` if none match
4. Computes `maximum_score` from the highest level across all criteria
5. Returns `RubricDefinition` with `minimum_score=1`

`get_skill_criterion()`:
1. Loads latest published `RubricVersionRecord`; raises `SS-VALIDATION-074` if not found
2. Iterates criteria for matching `criterion_ref == skill_slug`; raises `SS-VALIDATION-073` if not found

The internal `_to_criterion()` method parses the JSON criteria format, extracting level values from keys like `"level_1"`, `"level_2"`, etc.

#### Per-Skill Aggregation (`marking/domain/per_skill_aggregation.py`)

Deterministic aggregation helpers that operate on `PerSkillAssessment` results (imported from `modules/practice/domain/practice.py`).

**`compute_overall_score()`**:
- Computes the rounded weighted mean of per-skill scores using rubric criterion weights
- Falls back to simple `round(fmean())` if no weights match

**`compute_strengths()`**:
- Ranks assessments by `(score, weight)` descending
- Returns top 2 if ≥ 5 assessments, otherwise top 1
- Format: `"{skill_slug}: {rationale}"`

**`compute_weaknesses()`**:
- Ranks assessments by `(score, weight)` ascending
- Returns bottom 2 if ≥ 5 assessments, otherwise bottom 1
- Format: `"{skill_slug}: {rationale}"` with optional evidence quote: `(e.g. "{quote}")`

The internal `_ranked()` function sorts by `(score, weight)` tuple.

### 3.3 Use Cases

#### Decision Builder (`marking/use_cases/decision_builder.py`)

**`CriterionResultInput`**: Raw criterion result before evidence attachment.

```python
class CriterionResultInput(BaseModel):
    criterion_ref: str
    score: int
    rationale: str
```

**`build_marking_decision()`**: Assembles a canonical `MarkingDecision` from:
- Criterion results (`list[CriterionResultInput]`)
- Evidence references (`list[EvidenceReference]`)
- Pre-computed `overall_score`, `strengths`, `weaknesses`, `next_actions`
- Metadata: `marking_id`, `prompt`, `response_id`, `rubric`, `engine_version`, `provider`, `model_slug`, `trace_id`, `created_at`

Evidence is grouped by `criterion_ref` using a `defaultdict(list)` and attached to matching criterion judgments.

#### Structured Output (`marking/use_cases/structured_output.py`)

**`PromptLibrary`**: Small in-memory versioned prompt registry.

```python
class PromptLibrary:
    def register(self, template: PromptTemplate, *, make_default: bool = False) -> None
    def render(self, name: str, *, variables: dict[str, object], version: str | None = None) -> RenderedPrompt
```

- Templates stored keyed by `(name, version)` tuple
- Default version tracked per prompt name
- `render()` raises `SS-VALIDATION-017` (no default version) or `SS-VALIDATION-018` (template not found)
- Uses `str.format(**variables)` for template rendering

**`TypedLLMResult`**: Validated typed model output.

```python
@dataclass(slots=True)
class TypedLLMResult:
    parsed: BaseModel
    raw_payload: dict[str, Any]
    schema_version: str
    usage: dict[str, int]
    model_slug: str
```

**`StructuredOutputRejectionError`**: Exception raised when provider returns data that must be rejected.

```python
@dataclass(slots=True)
class StructuredOutputRejectionError(Exception):
    app_error: AppError
    raw_payload: dict[str, Any]
```

**`StructuredOutputRepairMode`**: Controls retry behavior.

| Mode | Behavior |
|------|----------|
| `FAIL_FAST` | Raise `StructuredOutputRejectionError` on first validation failure |
| `SELF_CORRECT` | Append error feedback and retry up to `max_validation_retries` times |

**`TypedLLMOutput`**: Pydantic-backed typed output parser with bounded corrective retries.

```python
class TypedLLMOutput:
    def __init__(
        self,
        model_type: type[ModelT],
        *,
        schema_version: str,
        max_validation_retries: int,
        repair_mode: StructuredOutputRepairMode = StructuredOutputRepairMode.SELF_CORRECT,
        timeout_seconds: float | None = None,
        transport_schema_name: str | None = None,
    ) -> None
```

`generate()` method:
1. Constructs `JsonSchemaResponseFormat` from the Pydantic model's JSON schema
2. Loops up to `max_validation_retries + 1` attempts
3. Calls `provider.complete_json()` with the schema
4. Parses response via `_coerce_json_payload()` → `model_type.model_validate()`
5. On `JSONDecodeError` or `ValidationError`:
   - If `FAIL_FAST` or max retries exceeded: raises `StructuredOutputRejectionError` with `SS-VALIDATION-019`
   - Otherwise: appends the malformed response as an assistant message, followed by a user message with the error details, and retries
6. Returns `TypedLLMResult` on success

---

## 4. Progression Engine

**Purpose**: Converts validated assessments into persistent views of learner capability across arbitrary dimensions (skills) and aggregates (competencies). Pure deterministic functions — no external dependencies.

### 4.1 Contracts (`progression/contracts/models.py`)

#### `AssessmentDimensionScore`

Canonical dimension score from a validated assessment. Score is pre-normalized to 0.0–1.0 range.

```python
class AssessmentDimensionScore(BaseModel):
    dimension_ref: str
    normalized_score: float = Field(ge=0.0, le=1.0)
```

#### `AssessmentEvidenceReference`

Evidence linked to a dimension score.

```python
class AssessmentEvidenceReference(BaseModel):
    dimension_ref: str
    quote: str
    explanation: str
```

#### `AssessmentEvent`

Validated assessment event consumed by the progression engine. Carries full audit metadata.

```python
class AssessmentEvent(BaseModel):
    assessment_id: str
    attempt_ref: str
    entity_ref: str
    created_at: datetime
    prompt_version: str
    rubric_version: str
    trace_id: str
    dimension_scores: list[AssessmentDimensionScore] = Field(default_factory=list)
    evidence: list[AssessmentEvidenceReference] = Field(default_factory=list)
```

#### `AggregateDefinition`

Weighted aggregate of dimensions.

```python
class AggregateDefinition(BaseModel):
    aggregate_ref: str
    dimension_weights: dict[str, float] = Field(default_factory=dict)
```

#### `AggregateGateRule`

Optional gate preventing an aggregate from exceeding a ceiling when a critical dimension falls below a floor.

```python
class AggregateGateRule(BaseModel):
    aggregate_ref: str
    dimension_ref: str
    floor: float = Field(ge=0.0, le=1.0)
    ceiling: float = Field(ge=0.0, le=1.0)
```

#### `DecayProfileConfig`

Decay config applied to historical evidence.

```python
class DecayProfileConfig(BaseModel):
    retention_window_days: int = Field(default=180, ge=1)
    minimum_weight: float = Field(default=0.35, ge=0.0, le=1.0)
```

#### `ConfidenceProfileConfig`

Confidence config based on evidence volume and recency.

```python
class ConfidenceProfileConfig(BaseModel):
    min_recent_evidence: int = Field(default=2, ge=1)
    min_total_evidence: int = Field(default=3, ge=1)
    recent_window_days: int = Field(default=30, ge=1)
```

#### `ProgressionEngineConfig`

Versioned config artifact for the progression engine.

```python
class ProgressionEngineConfig(BaseModel):
    engine_version: str
    schema_version: str
    evidence_ledger_schema_version: str
    config_version: str
    decay_profile: DecayProfileConfig = Field(default_factory=DecayProfileConfig)
    confidence_profile: ConfidenceProfileConfig = Field(default_factory=ConfidenceProfileConfig)
    aggregate_gate_rules: list[AggregateGateRule] = Field(default_factory=list)
    weak_dimension_threshold: float = Field(default=0.65, ge=0.0, le=1.0)
    stagnation_score_threshold: float = Field(default=0.75, ge=0.0, le=1.0)
    stagnation_delta_threshold: float = Field(default=0.05, ge=0.0)
```

**Current artifact values** (`soft_skills_progression_engine.v1.json`):
```json
{
  "engine_version": "progression-engine.v1",
  "schema_version": "progression-snapshot.v1",
  "evidence_ledger_schema_version": "progression-evidence-ledger.v1",
  "config_version": "progress-config-2026-03",
  "decay_profile": { "retention_window_days": 180, "minimum_weight": 0.35 },
  "confidence_profile": { "min_recent_evidence": 2, "min_total_evidence": 3, "recent_window_days": 30 },
  "aggregate_gate_rules": [
    { "aggregate_ref": "stakeholder-management", "dimension_ref": "expectation-setting", "floor": 0.4, "ceiling": 0.6 }
  ],
  "weak_dimension_threshold": 0.65,
  "stagnation_score_threshold": 0.75,
  "stagnation_delta_threshold": 0.05
}
```

#### `PriorProgressState`

Previous persisted scores used for delta reporting.

```python
class PriorProgressState(BaseModel):
    snapshot_id: str
    dimension_scores: dict[str, float] = Field(default_factory=dict)
    aggregate_scores: dict[str, float] = Field(default_factory=dict)
```

#### `DimensionContribution`

Explainability ledger item for one assessment contribution.

```python
class DimensionContribution(BaseModel):
    assessment_id: str
    attempt_ref: str
    normalized_score: float
    weight: float
    contributed_at: str
    prompt_version: str
    rubric_version: str
    trace_id: str
    quotes: list[str] = Field(default_factory=list)
```

#### `DimensionState`

Current state for one dimension.

```python
class DimensionState(BaseModel):
    dimension_ref: str
    score: float
    confidence: float
    confidence_band: str
    evidence_count: int
    recent_evidence_count: int
    streak: int
    delta: float
    last_assessment_at: str | None = None
    contributions: list[DimensionContribution] = Field(default_factory=list)
```

#### `AggregateState`

Current state for one aggregate.

```python
class AggregateState(BaseModel):
    aggregate_ref: str
    score: float
    confidence: float
    confidence_band: str
    delta: float
    gating_applied: bool = False
    gating_reasons: list[str] = Field(default_factory=list)
    supporting_dimension_refs: list[str] = Field(default_factory=list)
```

#### `ComputedProgressionSnapshot`

Computed progression snapshot before persistence IDs are assigned.

```python
class ComputedProgressionSnapshot(BaseModel):
    weak_dimension_refs: list[str] = Field(default_factory=list)
    stagnating_dimension_refs: list[str] = Field(default_factory=list)
    coverage_gap_dimension_refs: list[str] = Field(default_factory=list)
    dimension_states: list[DimensionState] = Field(default_factory=list)
    aggregate_states: list[AggregateState] = Field(default_factory=list)
```

### 4.2 Domain Logic (`progression/domain/progression.py`)

#### `compute_progression_snapshot()`

Main entry point. Builds deterministic dimension and aggregate state from validated history.

```python
def compute_progression_snapshot(
    *,
    assessments: list[AssessmentEvent],
    dimension_refs: list[str],
    aggregate_definitions: list[AggregateDefinition],
    previous_state: PriorProgressState | None,
    config: ProgressionEngineConfig,
    now: datetime,
) -> ComputedProgressionSnapshot
```

**Preconditions**:
- Raises `SS-DOMAIN-017` if `assessments` is empty

**Algorithm**:

1. **Dimension aggregation**: For each `dimension_ref`, calls `_compute_dimension_aggregate()`
2. **Dimension states**: Maps internal `_DimensionAggregate` → `DimensionState` with delta computation against `previous_state`
3. **Aggregate computation**: For each `AggregateDefinition`:
   - Computes weighted score: `Σ(dimension_score × weight)`
   - Computes weighted confidence: `Σ(dimension_confidence × weight)`
   - Applies gate rules: if a gate dimension score < floor and aggregate score > ceiling, clamps score to ceiling
   - Computes delta against previous aggregate score
4. **Classification**:
   - `weak_dimension_refs`: dimensions with `evidence_count > 0` and `score < weak_dimension_threshold` (default 0.65)
   - `stagnating_dimension_refs`: dimensions with sufficient evidence, `score < stagnation_score_threshold` (default 0.75), and `|delta| < stagnation_delta_threshold` (default 0.05)
   - `coverage_gap_dimension_refs`: dimensions with `evidence_count < min_recent_evidence` (default 2)

#### `_compute_dimension_aggregate()`

Internal function that computes the aggregated state for a single dimension.

Algorithm:
1. Collects all `(AssessmentEvent, AssessmentDimensionScore)` pairs matching the dimension
2. If no matches: returns zeroed state
3. For each matching assessment (sorted by `created_at`):
   - Computes decay weight via `_decay_weight()`
   - Accumulates `weighted_score` and `total_weight`
   - Tracks `recent_evidence_count` (within `recent_window_days`)
   - Tracks `streak` (consecutive scores ≥ 0.60)
   - Creates `DimensionContribution` with full audit trail
4. Computes final score: `weighted_score / total_weight`
5. Computes confidence via `_confidence()`
6. Returns contributions in reverse chronological order

#### Decay Weighting

```python
def _decay_weight(*, assessment_at, now, config) -> float
```

Linear decay over `retention_window_days`:
- If age ≥ retention window: returns `minimum_weight` (floor)
- Otherwise: `max(minimum_weight, 1.0 - age_days × slope)` where `slope = (1.0 - minimum_weight) / retention_window_days`

**Example** (default config: 180 days, floor 0.35):
- Day 0: weight = 1.0
- Day 90: weight ≈ 0.675
- Day 180+: weight = 0.35

#### Confidence Computation

```python
def _confidence(*, evidence_count, recent_evidence_count, last_assessment_at, config, now) -> float
```

Composite formula: `min(1.0, evidence_ratio × 0.45 + recent_ratio × 0.35 + recency × 0.20)`

| Component | Weight | Calculation |
|-----------|--------|-------------|
| Evidence volume | 45% | `min(1.0, evidence_count / min_total_evidence)` |
| Recent evidence | 35% | `min(1.0, recent_evidence_count / min_recent_evidence)` |
| Recency | 20% | `max(0.0, 1.0 - age_days / retention_window_days)` |

**Confidence bands**:

| Band | Threshold |
|------|-----------|
| `high` | ≥ 0.75 |
| `medium` | ≥ 0.40 |
| `low` | < 0.40 |

#### `diff_summary()`

Builds a compact replay audit summary comparing current snapshot against previous state.

```python
def diff_summary(*, previous_state, snapshot) -> dict[str, float | int | str]
```

Returns:
- `changed_dimension_count`: dimensions with score delta > 0.001
- `changed_aggregate_count`: aggregates with score delta > 0.001
- `mode`: `"bootstrap"` (no previous state) or `"replay"`
- `lowest_dimension` (replay mode only): dimension_ref with lowest score

---

## 5. Recommendation Engine

**Purpose**: Turns learner state plus content metadata into transparent, explainable next-step recommendations. Pure deterministic functions — no external dependencies.

### 5.1 Contracts (`recommendation/contracts/models.py`)

#### `LearnerContext`

Recommendation-relevant learner context.

```python
class LearnerContext(BaseModel):
    entity_ref: str
    target_role: str | None = None
    goals: list[str] = Field(default_factory=list)
    persona_tags: list[str] = Field(default_factory=list)
```

#### `CandidateItem`

Recommendation-ready content candidate.

```python
class CandidateItem(BaseModel):
    content_ref: str
    content_type: str
    collection_ref: str
    title: str
    summary: str
    difficulty: str
    verification_state: str
    target_dimension_refs: list[str] = Field(default_factory=list)
    target_aggregate_refs: list[str] = Field(default_factory=list)
    lifecycle_state: str
    attempt_count: int = 0
    last_attempted_at: datetime | None = None
```

#### `RecommendationWeights`

Weighted scoring components. All weights must be ≥ 0.

```python
class RecommendationWeights(BaseModel):
    dimension_deficit_alignment: float = Field(ge=0.0)
    stagnation_relief: float = Field(ge=0.0)
    coverage_gap_fit: float = Field(ge=0.0)
    goal_alignment: float = Field(ge=0.0)
    verification_boost: float = Field(ge=0.0)
```

#### `RecommendationEngineConfig`

Versioned config artifact for the recommendation engine.

```python
class RecommendationEngineConfig(BaseModel):
    engine_version: str
    schema_version: str
    config_version: str
    weights: RecommendationWeights
    cooldown_hours: int = Field(default=12, ge=1)
    max_recommendations: int = Field(default=3, ge=1)
    max_alternatives: int = Field(default=2, ge=0)
    minimum_score: float = 0.0
    allowed_lifecycle_states: list[str] = Field(default_factory=list)
    verified_states: list[str] = Field(default_factory=list)
    advanced_difficulty_labels: list[str] = Field(default_factory=list)
    advanced_readiness_threshold: float = Field(default=0.45, ge=0.0, le=1.0)
    immediate_repeat_penalty: float = Field(default=0.08, ge=0.0)
    repeat_penalty_cap: float = Field(default=0.08, ge=0.0)
    repeat_penalty_per_attempt: float = Field(default=0.02, ge=0.0)
```

**Current artifact values** (`soft_skills_recommendation_engine.v1.json`):
```json
{
  "engine_version": "recommendation-engine.v1",
  "schema_version": "recommendation-output.v1",
  "config_version": "rec-config-2026-03",
  "weights": {
    "dimension_deficit_alignment": 0.4,
    "stagnation_relief": 0.2,
    "coverage_gap_fit": 0.15,
    "goal_alignment": 0.15,
    "verification_boost": 0.1
  },
  "cooldown_hours": 12,
  "max_recommendations": 3,
  "max_alternatives": 2,
  "allowed_lifecycle_states": ["published_public", "published_private", "draft", "review"],
  "verified_states": ["verified"],
  "advanced_difficulty_labels": ["advanced"],
  "advanced_readiness_threshold": 0.45,
  "immediate_repeat_penalty": 0.08,
  "repeat_penalty_cap": 0.08,
  "repeat_penalty_per_attempt": 0.02
}
```

#### `RecommendedCandidate`

One ranked recommendation candidate with full score breakdown.

```python
class RecommendedCandidate(BaseModel):
    content_ref: str
    content_type: str
    collection_ref: str
    title: str
    difficulty: str
    score: float
    component_breakdown: dict[str, float] = Field(default_factory=dict)
    reasons: list[str] = Field(default_factory=list)
    cooldown_expires_at: str | None = None
    verification_state: str
    target_dimension_refs: list[str] = Field(default_factory=list)
    target_aggregate_refs: list[str] = Field(default_factory=list)
```

#### `ComputedRecommendation`

Computed recommendation artifact before persistence IDs are assigned.

```python
class ComputedRecommendation(BaseModel):
    context_snapshot_id: str
    candidate_count: int
    items: list[RecommendedCandidate]
    alternatives: list[RecommendedCandidate]
```

### 5.2 Domain Logic (`recommendation/domain/recommendation.py`)

#### `compute_recommendation()`

Main entry point. Scores visible content candidates against the current progression snapshot.

```python
def compute_recommendation(
    *,
    learner: LearnerContext,
    snapshot: ComputedProgressionSnapshot,
    candidates: list[CandidateItem],
    config: RecommendationEngineConfig,
    now: datetime,
) -> ComputedRecommendation
```

**Preconditions**:
- Raises `SS-VALIDATION-031` if `candidates` is empty
- Raises `SS-VALIDATION-032` if no candidates pass scoring/filtering

**Algorithm**:

1. **Build lookup maps**: `dimension_map` and `aggregate_map` from snapshot states
2. **Tokenize learner goals**: `_goal_tokens()` extracts lowercase tokens (≥ 4 chars) from `target_role` and `goals`
3. **Score each candidate**:
   - Skip candidates with empty `target_dimension_refs`
   - **Lifecycle filter**: skip if `lifecycle_state` not in `allowed_lifecycle_states`
   - **Advanced readiness gate**: if difficulty in `advanced_difficulty_labels` and max aggregate score < `advanced_readiness_threshold`, skip
   - Compute six scoring components
   - Compute total: `Σ(component × weight) - repeat_penalty`
4. **Rank and select**:
   - Sort by `(-score, title, content_ref)` for deterministic tie-breaking
   - Select top `max_recommendations` items with `score > minimum_score`
   - Select top `max_alternatives` from remaining items
5. **Generate `context_snapshot_id`**: SHA-256 hash of `entity_ref | sorted weak_dimension_refs | sorted content_refs` (first 24 hex chars)

#### Scoring Components

The `_recommendation_components()` function computes six components for each candidate:

```
score = Σ(component_i × weight_i) - repeat_penalty
```

| Component | Logic | Default Weight |
|-----------|-------|----------------|
| `dimension_deficit_alignment` | `(1 - score) × max(confidence, 0.35)` averaged over overlapping weak dimensions with evidence | 0.4 |
| `stagnation_relief` | `1 - score` for dimensions with `|delta| < 0.05` and `evidence_count ≥ 2` | 0.2 |
| `coverage_gap_fit` | `1 - min(1, evidence_count / 2)` for overlapping dimensions | 0.15 |
| `goal_alignment` | Token overlap ratio between learner goals and candidate text | 0.15 |
| `verification_boost` | 0.5 if `verification_state` in `verified_states`, else 0.0 | 0.1 |
| `recent_repeat_penalty` | Cooldown-based penalty (subtracted, not weighted) | N/A |

**Repeat penalty logic**:
- If `last_attempted_at` is within `cooldown_hours`: `immediate_repeat_penalty` (default 0.08)
- Otherwise: `min(repeat_penalty_cap, attempt_count × repeat_penalty_per_attempt)` (default cap 0.08, per-attempt 0.02)

#### Reason Codes

The `_reason_codes()` function generates explainable reason codes for each recommendation:

| Code Pattern | Condition |
|--------------|-----------|
| `weak_dimension:{ref}` | Candidate targets a dimension with `score < 0.65` and `evidence_count > 0` |
| `stagnation:{ref}` | Candidate targets a dimension with `|delta| < 0.05` and `evidence_count ≥ 2` |
| `coverage_gap:{ref}` | Candidate targets a dimension with `evidence_count < 2` |
| `goal_match:{token}` | Candidate text contains a learner goal token |
| `verified_content` | Candidate `verification_state` in `verified_states` |

#### Cooldown Tracking

```python
def _cooldown_expires_at(candidate, config, now) -> str | None
```

- Returns `None` if never attempted or cooldown has expired
- Returns ISO 8601 timestamp of `last_attempted_at + cooldown_hours` otherwise

#### Goal Alignment

Tokenization uses `_tokenize()` which splits on non-alphanumeric characters and filters tokens with `len ≥ 4`. Goal alignment is computed as the ratio of matched tokens to total goal tokens, capped at 1.0.

Candidate text for matching includes: `title`, `summary`, `difficulty`, `target_dimension_refs`, `target_aggregate_refs`.

---

## 6. Adapter Pattern

Modules translate between domain-specific types and engine-generic types:

```
┌─────────────────────────────────────────────────────────────┐
│  Modules (Domain-Specific)                                   │
│  practice/  progression/  evaluation/  catalog/              │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│  Adapter Layer (modules/progression/domain/progression.py)   │
│  - AssessmentSignal → EngineAssessmentEvent                  │
│  - SkillProgressView ↔ DimensionState                        │
│  - CatalogCandidate → EngineCandidateItem                    │
│  - normalize_score(): rubric 1-5 → canonical 0-1             │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│  Engines (App-Agnostic)                                      │
│  marking/  progression/  recommendation/                     │
└─────────────────────────────────────────────────────────────┘
```

Engines contain no domain assumptions about skills, competencies, or soft-skills. Domain projects supply:
- Prompt content and rubric content
- Criterion semantics (what each `criterion_ref` means)
- Score interpretation rules (what a score of 3 means in context)
- Aggregate definitions (which dimensions compose into which competencies)
- Lifecycle state semantics (what "published_public" means)

---

## 7. Error Reference

### Marking Engine Errors

| Code | Source | Description |
|------|--------|-------------|
| `SS-VALIDATION-017` | `PromptLibrary.render()` | Prompt library default version not found |
| `SS-VALIDATION-018` | `PromptLibrary.render()` | Prompt library template not found |
| `SS-VALIDATION-019` | `TypedLLMOutput.generate()` | Provider returned malformed structured output |
| `SS-VALIDATION-034` | `validate_marking_decision()` | Decision prompt_id mismatch |
| `SS-VALIDATION-035` | `validate_marking_decision()` | Decision response_id mismatch |
| `SS-VALIDATION-036` | `validate_marking_decision()` | Decision prompt_version mismatch |
| `SS-VALIDATION-037` | `validate_marking_decision()` | Decision rubric metadata mismatch |
| `SS-VALIDATION-071` | `SqlAlchemyRubricRepository` | Rubric not found |
| `SS-VALIDATION-072` | `SqlAlchemyRubricRepository` | Rubric criteria not found |
| `SS-VALIDATION-073` | `SqlAlchemyRubricRepository` | Specific rubric criterion not found |
| `SS-VALIDATION-074` | `SqlAlchemyRubricRepository` | Rubric version not found |
| `SS-SCORING-010` | `validate_marking_decision()` | Repeated criterion judgment |
| `SS-SCORING-011` | `validate_marking_decision()` | Incomplete criterion coverage |
| `SS-SCORING-012` | `validate_marking_decision()` | Criterion score out of range |
| `SS-SCORING-013` | `validate_marking_decision()` | Evidence criterion_ref mismatch |
| `SS-SCORING-014` | `validate_marking_decision()` | Evidence quote not grounded in response |
| `SS-SCORING-015` | `validate_marking_decision()` | Overall score out of range |
| `SS-SCORING-016` | `validate_marking_decision()` | Strengths/weaknesses contradiction |
| `SS-SCORING-017` | `validate_marking_decision()` | Overall score inconsistent with criteria |

### Progression Engine Errors

| Code | Source | Description |
|------|--------|-------------|
| `SS-DOMAIN-017` | `compute_progression_snapshot()` | No assessments provided |

### Recommendation Engine Errors

| Code | Source | Description |
|------|--------|-------------|
| `SS-VALIDATION-031` | `compute_recommendation()` | No candidates provided |
| `SS-VALIDATION-032` | `compute_recommendation()` | No valid candidates after filtering |

### Config Loader Errors

| Code | Source | Description |
|------|--------|-------------|
| `SS-VALIDATION-038` | `_load_json_artifact()` | Config artifact file not found |
| `SS-VALIDATION-039` | `_load_json_artifact()` | Invalid JSON in config artifact |
| `SS-VALIDATION-040` | `_load_json_artifact()` | Config artifact schema validation failure |

---

## 8. Design Principles

1. **App-agnosticism**: Engines contain zero domain assumptions. All domain semantics are injected through contracts and config.

2. **Determinism**: Progression and recommendation engines are pure functions. Identical inputs + config produce identical outputs. The marking engine's LLM interaction is isolated; its aggregation and validation are deterministic.

3. **Fail-closed**: The marking engine enforces strict fail-closed behavior — if any skill assessment fails after retries, the entire assessment fails. Partial results are never persisted.

4. **Versioned contracts**: All config artifacts carry explicit `engine_version`, `schema_version`, and `config_version` fields. Changes require deliberate review and version bumping.

5. **Explainability**: Every engine produces transparent, auditable outputs:
   - Marking: evidence quotes grounded in response text
   - Progression: contribution ledger with assessment IDs, weights, and trace IDs
   - Recommendation: per-component score breakdowns and human-readable reason codes

6. **Separation of concerns**: Engines compute; adapters translate; Stageflow orchestrates. This three-layer architecture enables independent evolution of each layer.
