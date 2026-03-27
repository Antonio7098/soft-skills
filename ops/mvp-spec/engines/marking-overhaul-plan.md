# Marking Overhaul Plan

## Status

This document is the implementation plan for fully replacing the current MVP
marking runtime.

It is not a compatibility patch. The target state is a new marking system with:

- real relational rubric criteria storage
- per-skill assessment as the primary judgment unit
- Stageflow fan-out across skill assessments
- deterministic aggregation where the machine should be deterministic
- removal of the current single-pass assessment contract once the new system is
  in place

This plan supplements, and where necessary narrows, the general rules in
[`marking-engine.md`](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/engines/marking-engine.md).

## Decision

SoftSkills should replace the current text-practice marking flow with a
per-skill marking architecture, with assessment mode chosen by practice type.

The replacement is mandatory because the current implementation has three core
problems:

- rubric criteria stored in the database are generic field names rather than
  actual criterion text
- the runtime produces one monolithic marking judgment instead of explicit
  skill-level decisions
- validation reconstructs a synthetic rubric from target skill slugs instead of
  validating against the real stored rubric definition

The new system must make the rubric text explicit, the criterion-level judgment
explicit, and the aggregation rules explicit.

It must also avoid false precision for short-form practice. Quick practice is a
repetition loop, not a progression-grade competency measurement flow.

## Replacement Scope

The overhaul replaces all of the following runtime concerns for practice
assessment:

- rubric storage and loading
- assessment prompts
- typed LLM output contracts
- practice assessment orchestration
- marking validation rules
- persistence shape for skill-level results
- eval metrics and smoke expectations

The current single-pass assessment path should be deleted after the new path is
verified. Do not keep two semantic marking systems alive in production.

The replacement runtime is intentionally split:

- `quick_practice`
  - lightweight pass/fail per rubric area
  - rubric attached to the individual quick question
  - no progression contribution
  - no heavy aggregation requirement
- `interview`
  - richer multi-level scoring
  - progression-bearing
- `scenario`
  - richer multi-level scoring
  - progression-bearing

## Target Architecture

### 1. Rubric Storage

Rubric criteria must move to a real relational model.

The target schema is:

- `rubrics`
  - one row per rubric family version
- `rubric_criteria`
  - one row per criterion or skill judgment rule inside a rubric version

Minimum `rubric_criteria` fields:

- `id`
- `rubric_id`
- `rubric_version`
- `criterion_ref`
- `skill_slug`
- `title`
- `description`
- `weight`
- `required`
- `position`
- `levels_json`

Each rubric criterion must store explicit level definitions rather than a small
set of loose anchor strings.

Canonical level shape:

```python
levels = [
    {
        "level_1": {
            "description": "Does not demonstrate the skill.",
            "examples": ["...", "..."],
        }
    },
    {
        "level_2": {
            "description": "Shows weak or inconsistent demonstration.",
            "examples": ["...", "..."],
        }
    },
    {
        "level_3": {
            "description": "Shows adequate but partial demonstration.",
            "examples": ["...", "..."],
        }
    },
    {
        "level_4": {
            "description": "Shows strong demonstration with minor gaps.",
            "examples": ["...", "..."],
        }
    },
    {
        "level_5": {
            "description": "Shows excellent, consistent demonstration.",
            "examples": ["...", "..."],
        }
    },
]
```

The runtime should validate that:

- every required level for the rubric scale is present
- every level contains a non-blank description
- every level contains at least one concrete example
- levels match the rubric scale and ordering

The existing JSON `rubrics.criteria` field should stop being the runtime source
of truth. It may remain briefly during migration, but the new runtime must not
read criteria text from it.

Quick-practice rubrics use a 2-level scale and are attached to individual
prompt items, not to a shared rubric family reused across unrelated quick
questions.

That means:

- every quick-practice prompt item carries its own `rubric_id`
- that rubric describes the exact pass/fail areas for that specific question
- the runtime scores only the areas attached to that prompt item

Quick-practice canonical scale:

```python
levels = [
    {
        "level_1": {
            "description": "Fail: the response does not demonstrate the target behavior.",
            "examples": ["No direct signal of the target behavior."],
        }
    },
    {
        "level_2": {
            "description": "Pass: the response demonstrates the target behavior.",
            "examples": ["Direct signal of the target behavior is present."],
        }
    },
]
```

Interview and scenario rubrics continue to use the richer reusable multi-level
ladder.

Generated quick-practice content must follow the same rule. If the system
generates a quick-practice prompt item, it must also generate the item-specific
binary rubric for that prompt item and persist it as a real rubric record before
the prompt item is saved.

### 2. Marking Contracts

Per-skill assessment becomes the primary LLM output unit.

There are two valid internal contracts:

- progressive assessment
  - used by interview and scenario
- rep assessment
  - used by quick practice

Canonical internal contracts:

```python
class EvidenceItem(BaseModel):
    quote: str
    explanation: str


class PerSkillAssessment(BaseModel):
    skill_slug: str
    score: int = Field(ge=1, le=5)
    rationale: str
    evidence: list[EvidenceItem] = Field(min_length=1, max_length=2)


class AssessmentAggregationOutput(BaseModel):
    summary: str
    next_actions: list[str] = Field(min_length=1)


class AssessmentArtifact(BaseModel):
    prompt_version: str
    rubric_id: str
    rubric_version: str
    provider: str
    model_slug: str
    schema_version: str
    config_version: str
    overall_score: int = Field(ge=1, le=5)
    summary: str
    per_skill_assessments: list[PerSkillAssessment] = Field(min_length=1)
    strengths: list[str] = Field(min_length=1)
    weaknesses: list[str] = Field(min_length=1)
    next_actions: list[str] = Field(min_length=1)
    raw_payload: dict[str, object]
```

`EvidenceItem` does not need `skill_slug` because it is nested inside
`PerSkillAssessment`. If a flattened projection is needed for a view or export,
the `skill_slug` is inherited from the parent assessment.

Quick-practice uses the same shape, but its score range is constrained to
`1..2`, where:

- `1` = fail
- `2` = pass

This keeps the persistence model simple while preserving the product meaning of
pass/fail per rubric area.

### 3. Persistence Model

The learner-facing artifact should be backed by explicit skill result records.

Target persistence shape:

- `assessments`
  - overall metadata, summary, overall score, trace metadata, raw payload
- `assessment_skill_results`
  - one row per skill judgment
- `assessment_skill_evidence`
  - one row per evidence item attached to a skill judgment

This is the preferred end state because progression, analytics, and dispute
review all benefit from queryable skill-level rows instead of opaque JSON blobs.

Quick-practice rows are still persisted for auditability and learner history,
but they are not inputs to longitudinal progression.

If transitional JSON snapshots are retained for audit or replay, they are a
secondary serialization of the canonical relational data, not the source of
truth.

### 4. Runtime Boundaries

The marking engine owns:

- rubric loading
- skill-level assessment execution
- aggregation
- validation
- persistence-ready assessment artifacts

The practice module owns:

- attempt lifecycle
- prompt resolution
- learner context resolution
- durable assessment persistence
- API projections

## Stageflow Execution Model

### Parent Pipeline

The canonical assessment parent pipeline should be:

1. `GUARD`: validate submit payload and active versions
2. `ENRICH`: resolve prompt and rubric metadata
3. `ENRICH`: resolve learner context
4. `WORK`: persist submission and mark attempt as assessing
5. `TRANSFORM`: fan out per-skill marking child pipelines
6. `TRANSFORM`: aggregate per-skill results
7. `GUARD`: validate final assessment artifact against the real rubric
8. `WORK`: persist assessment rows
9. `WORK`: emit downstream progression trigger or event when the practice type
   is progression-bearing

### Per-Skill Fan-Out

Per-skill marking should run as Stageflow child subpipelines, not as hidden
nested service calls.

This is the right fit because:

- the number of target skills is discovered at runtime from the prompt
- each skill assessment is independently traceable
- each child run can emit its own provider call logs and failure events
- timeout, cancellation, and concurrency controls can be applied cleanly

Each child skill pipeline should contain:

1. `GUARD`: validate worker input
2. `ENRICH`: load criterion text for the target skill
3. `TRANSFORM`: call the LLM for one skill only
4. `GUARD`: verify and validate `PerSkillAssessment`

The parent fan-out stage should use bounded concurrency. The runtime config
should define a maximum parallel child count for skill assessment.

If any required child skill pipeline fails after retries, the parent assessment
must fail closed. Partial validated results must not be persisted.

### Aggregation

Aggregation should be split into deterministic logic and optional LLM synthesis.

Deterministic aggregation must compute:

- `overall_score`
- `strengths`
- `weaknesses`
- ranking or ordering of assessed skills

An aggregation LLM call may generate only:

- overall summary
- next actions

The aggregation model must not be allowed to override per-skill scores or the
computed overall score.

## Rubric Seed Model

Rubric seed data must include real criterion text per skill for each rubric
family version.

Minimum seed shape:

```python
RUBRIC_CRITERIA_SEEDS = {
    "quick_practice_text@v1": {
        "active-listening": {
            "title": "Active Listening",
            "description": "Assess whether the learner demonstrates active listening.",
            "weight": 1.0,
            "required": True,
            "levels": [
                {"level_1": {"description": "...", "examples": ["...", "..."]}},
                {"level_2": {"description": "...", "examples": ["...", "..."]}},
                {"level_3": {"description": "...", "examples": ["...", "..."]}},
                {"level_4": {"description": "...", "examples": ["...", "..."]}},
                {"level_5": {"description": "...", "examples": ["...", "..."]}},
            ],
        },
    },
}
```

Rubric criteria seeding should live alongside the platform taxonomy and rubric
bootstrap flow so the database is initialized with the full versioned rubric
definition in one place.

## Prompting Model

### Per-Skill Prompt

The child worker prompt should:

- assess exactly one skill
- include the rubric criteria text for that skill
- include the full rubric level definitions for that skill
- include the original prompt and learner response
- return `PerSkillAssessment` JSON only

Required prompt rules:

- do not assess any skill other than the supplied `skill_slug`
- cite only direct quotes from the learner response
- keep rationale specific to the supplied rubric levels
- return one to two evidence items only

### Aggregation Prompt

The aggregation prompt should receive:

- all validated per-skill assessments
- the learner response

It should return:

- summary
- next actions

It must not return:

- per-skill scores
- overall score
- skill rankings

## Validation Rules

The new validator must validate against the real stored rubric definition, not a
synthesized placeholder rubric.

The final assessment artifact should be rejected when:

- any required rubric skill is missing
- any unexpected skill is present
- any score is outside the rubric scale
- any evidence quote is not present in the learner response
- any skill has zero evidence items
- the overall score does not match the configured aggregation rule
- strengths and weaknesses contradict the ranked skill results
- prompt, rubric, provider, model, schema, or trace metadata is missing

The validator should also enforce that aggregation uses the stored rubric
weights where weights are present.

Each per-skill output should also pass verification before the parent pipeline
accepts it.

Minimum per-skill verification checks:

- returned `skill_slug` exactly matches the requested skill
- score is compatible with the rubric level descriptions
- rationale is consistent with the selected score level
- evidence quotes appear in the learner response
- evidence explanations support the rationale rather than contradict it
- evidence is specific enough to justify the assigned score

## Aggregation Rules

Aggregation must be deterministic and reviewed.

Default rule set:

- overall score = rounded weighted mean of per-skill scores
- strengths = top one or two highest-weighted high-scoring skills with grounded
  rationale
- weaknesses = bottom one or two lowest-scoring skills with grounded rationale
  and evidence excerpt
- next actions = aggregation LLM output after grounded per-skill assessment is
  complete

If the rubric defines different thresholds or weighting rules, the rubric wins.

Aggregation may only run after all required per-skill outputs have passed
verification and validation.

## Reliability, Retries, And Hardening

The new marking runtime must fail closed at the parent level while being
aggressive about preventing avoidable child failures.

### Retry Strategy

Per-skill workers must support bounded corrective retries for:

- malformed JSON
- schema validation errors
- missing or invalid evidence
- returned `skill_slug` mismatch
- unsupported score or rationale mismatch against rubric levels

Retry prompts should identify the concrete violation and request a schema-only
correction rather than a fresh unconstrained reassessment.

### Verification Strategy

After a worker returns parseable output, the runtime should run deterministic
verification before accepting the result.

Deterministic verification is mandatory. An additional LLM verifier may be
added later, but it is optional and cannot replace deterministic checks.

### Hardening Requirements

To reduce child failures, the runtime should:

- give each worker exactly one skill and one rubric criterion definition
- include the full level structure in the prompt
- forbid assessment of any skill other than the requested one
- require one to two direct quotes from the learner response
- require concise rationale tied to rubric levels
- use bounded concurrency rather than unbounded fan-out
- apply explicit timeouts to child runs
- propagate timeout and cancellation budgets into child subpipelines

### Failure Semantics

Failure semantics are strict:

- if one required skill fails after retries and verification, the whole parent
  assessment fails
- no validated assessment artifact is persisted in that case
- the attempt may be persisted as rejected or failed with trace-linked reasons
- downstream progression must not run on partial or degraded assessment output

The runtime should prefer rejection over silently dropping a failed skill or
inventing a fallback score.

## File-Level Plan

### Database And Taxonomy

- add SQLAlchemy models and migration for `rubric_criteria`
- add SQLAlchemy models and migration for `assessment_skill_results`
- add SQLAlchemy models and migration for `assessment_skill_evidence`
- replace generic rubric seeds with real per-skill criterion seeds
- update taxonomy bootstrap to seed full rubric criteria rows

### Marking Engine

- add rubric repository or loader backed by the new tables
- add per-skill worker contracts
- add aggregation contracts
- add deterministic aggregation utilities
- replace synthetic-rubric validation with real-rubric validation

### LLM Provider Layer

- replace the single assessment prompt with:
  - per-skill assessment prompt
  - aggregation prompt
- add typed output contracts for `PerSkillAssessment` and
  `AssessmentAggregationOutput`

### Practice Workflow

- replace the current `assessment_transform` implementation with child skill
  fan-out plus aggregation
- persist the new assessment artifact shape
- update learner-facing projections to read from per-skill result storage

### Evaluation And Smoke Coverage

- replace legacy single-pass mocks and fixtures
- update marking benchmark scoring to compare per-skill outputs directly
- add smoke expectations for:
  - child subpipeline counts
  - provider call counts
  - timeout budget propagation
  - evidence coverage

## Deletion Plan

The overhaul is not complete until the old runtime is removed.

Delete or replace:

- the current single-pass assessment prompt contract
- the current single-pass typed output schema
- the current provider path that returns one monolithic `AssessmentDraft`
- the synthetic-rubric validation logic
- tests that only validate the legacy single-pass shape

Do not leave dead compatibility branches in the production runtime once the new
path is stable.

## Migration Sequence

### Phase 1. Schema And Seeds

- add new rubric and assessment child tables
- seed real rubric criteria text for all active rubric versions
- ship read paths for the new rubric storage

### Phase 2. Internal Contracts And Validation

- add `PerSkillAssessment`, `AssessmentAggregationOutput`, and
  `AssessmentArtifact`
- implement real-rubric validation and deterministic aggregation

### Phase 3. Workflow Replacement

- implement per-skill child pipelines
- implement aggregation stage
- replace the current assessment transform path in practice runtime

### Phase 4. Persistence And Views

- persist overall and per-skill assessment rows
- update API projections and downstream consumers
- update progression triggers to read the new structure

### Phase 5. Evals, Smokes, And Cutover

- replace benchmark fixtures and smoke suites
- run provider-backed latency and quality checks
- remove the legacy marking runtime

## Acceptance Criteria

The overhaul is complete only when all of the following are true:

- every active rubric version has real criteria rows in the database
- every validated assessment artifact contains one result per required target
  skill
- every per-skill result contains grounded evidence
- overall score is computed programmatically from per-skill scores
- Stageflow traces show one child run per skill assessment
- provider-backed evals and smoke tests pass on the new runtime
- the legacy single-pass marking path is removed

## Non-Goals

This overhaul does not require:

- unconstrained agent loops in the assessment path
- model-generated overall score authority
- keeping the old JSON-only rubric criteria model as a permanent dependency
- dual-running two production marking semantics indefinitely

## Notes For Implementation

- Prefer Stageflow child subpipelines over ad hoc `asyncio.gather` inside a
  hidden service when the work item is a first-class per-skill judgment.
- Keep concurrency bounded and configurable.
- Persist enough raw payload and trace metadata for replay and dispute review.
- Treat criterion text, aggregation rules, prompt versions, and schema versions
  as explicit versioned contracts.
