# Multi-Question Scenarios Implementation Plan

## Overview

Scenarios currently resolve to one prompt, one session, and one attempt at runtime.
Adding authored multi-question scenarios should not introduce a second step-state
machine inside practice attempts.

For MVP, the correct design is:

- persist authored scenario questions
- expand each authored question into its own scenario run item at practice-run start
- keep the existing session, attempt, assessment, and run progression model intact

This preserves current runtime semantics, keeps observability legible, and avoids
mutating stored prompt payloads after session start.

---

## Core Design Decision

### Rejected approach

Do not keep one scenario run item and pass `step` during submission.

Why this is rejected:

- `PracticeSessionRecord` stores one immutable `prompt_payload`
- `AttemptView` and assessment reload that stored payload
- current run progression expects one active attempt per run item
- step state, retries, refresh/resume, and history would all need a new persistence model

This would add complexity in the hottest runtime path for limited product value.

### Recommended MVP approach

When a scenario has authored questions:

- each question becomes one scenario run item
- each run item gets its own `session_id`, `attempt_id`, and prompt snapshot
- all run items share the same scenario context and artifacts
- the learner experiences one scenario as a sequence of questions across adjacent run items

This uses the current runtime architecture as-is.

---

## Goals

- Store authored multi-question scenarios durably.
- Let generation create compact progressive scenario questions.
- Reuse the existing practice session and attempt lifecycle.
- Preserve explainable per-question assessment and run-level aggregation.
- Keep generation latency low by minimizing LLM calls and output payload size.

## Non-Goals

- No new per-attempt step state machine.
- No dynamic question generation during practice runtime.
- No follow-up LLM call solely to generate questions after scenario generation.
- No hidden fallback that silently fabricates authored questions for stored scenarios.

---

## Current State

### Authoring and persistence

`ScenarioRecord` has no `questions` field.

### Practice runtime

- scenario prompt text is built once from scenario context
- one run item maps to one session and one attempt
- session persistence stores one immutable `prompt_payload`
- assessment reads that same persisted prompt payload

### Implication

Any design that depends on changing prompt meaning between submissions conflicts with
the current runtime model.

---

## Recommended Data Model

### 1. Persist authored questions on scenarios

Add `questions: list[str]` to:

- `ScenarioRecord`
- `ScenarioCreateCommand`
- `ScenarioUpdateCommand`
- `ScenarioView`
- `GeneratedScenarioDraft`

### 2. Add question planning metadata

Add `question_count` to `GeneratedScenarioPlan`.

Use a bounded default:

- default `3`
- minimum `2`
- maximum `5`

Rationale:

- fewer than 2 is not meaningfully multi-question
- more than 5 increases generation payload size and practice fatigue for MVP

### 3. Keep question payload shape minimal for MVP

Use `list[str]` for now, not a richer object schema.

Reason:

- smallest possible structured output
- easiest validation contract
- fastest generation payload
- compatible with future migration if we later need richer step metadata

If richer metadata becomes necessary later, migrate to typed question objects.

---

## Generation Pipeline Changes

## Design constraints

Generation must stay fast and parallel:

- keep one scenario worker call per scenario
- do not add a second question-generation worker
- do not add serial follow-up LLM calls for refinement
- keep the scenario output schema minimal
- validate aggressively and retry only on real schema or semantic violations

### 1. Blueprint output

Update the collection blueprint contract to include `question_count` on each scenario plan.

The planner should decide question count once. The worker must then honor it exactly.

### 2. Scenario worker prompt

Update the scenario worker prompt to require:

- exactly `{question_count}` authored questions
- questions must be concise and distinct
- questions must progress from foundational to more complex
- questions must remain grounded in the same scenario context
- no duplicate wording
- no extra commentary outside the JSON contract

### 3. Scenario worker output format

Add:

- `questions: array[string]`

Keep the rest of the contract unchanged.

### 4. Worker variables

Pass `question_count` into the scenario worker prompt render request.

### 5. Validation

Extend `_validate_generated_scenario_draft` to reject:

- question count mismatch
- blank questions
- duplicate normalized questions
- fewer than 2 questions

Validation should remain deterministic and cheap.

### 6. Fast-path prompt discipline

Keep prompt instructions short and explicit. Avoid adding prose-heavy formatting
requirements that increase tokens without improving quality.

Recommended worker instruction emphasis:

- one scenario only
- JSON only
- concise field values
- exactly `N` questions
- distinct progression

---

## Database Changes

### 1. Model

Add:

```python
questions: Mapped[list[str]] = mapped_column(JSON, default=list)
```

to `ScenarioRecord`.

### 2. Migration

Add a non-null `questions` JSON column with server default `[]`.

Do not backfill generated questions in the migration. Existing rows should remain
explicitly questionless until edited or regenerated.

---

## Catalog Contract Changes

Update all scenario-related commands and views to carry `questions`.

This includes:

- scenario create/update contracts
- collection/scenario view builders
- generation draft models
- generation persistence mapping
- organisation-scoped scenario services if they construct `ScenarioView` directly

Validation should reject blank question strings on create and update.

---

## Practice Runtime Changes

## Design principle

Do not add step progression to `submit_attempt`.

The runtime change belongs at run-item expansion time, before sessions and attempts
are persisted.

### 1. Extend scenario run items

Extend `StartScenarioRunItemCommand` with optional authored-question metadata:

- `question_text: str | None = None`
- `question_index: int | None = None`
- `question_count: int | None = None`

This metadata is only used when a scenario is expanded into multiple run items.

### 2. Extend start input and scenario context

Carry the optional authored-question metadata through:

- `StartInputPayload`
- `ScenarioContextView`

Suggested fields:

- `questions: list[str] = []`
- `active_question_text: str | None = None`
- `active_question_index: int | None = None`
- `question_count: int | None = None`

### 3. Build prompt text from active authored question

When `active_question_text` is present, the prompt text should include:

- a short scenario framing line
- question progress, e.g. `Question 2 of 4`
- the active authored question
- the existing scenario context block
- the final response instruction

Do not replace the prompt with the question string alone. Later questions still need
scenario grounding for learner clarity and assessment consistency.

### 4. Expand scenario questions into run items

At run construction time:

- prompt items remain one run item each
- scenarios without authored questions remain one run item each
- scenarios with authored questions expand into one run item per question

Each expanded run item should:

- point to the same `scenario_id`
- include the same artifacts
- carry one `question_text`
- carry stable `question_index` and `question_count`

### 5. Assistant practice flow

No assistant-specific state-model redesign is needed.

Because assistant practice already reads the current run item and current attempt from
the practice run, expanded scenario questions will naturally appear as sequential
questions.

---

## Assessment and Progression Semantics

Assessment remains per run item, therefore per authored question.

This is acceptable for MVP because:

- each authored question is now a normal scenario prompt snapshot
- assessments remain explainable and tied to a single response
- run-level summary already aggregates across items

No special final-step-only assessment logic is required in this phase.

Progression refresh should continue to use validated non-quick-practice assessments as it does today.

---

## Observability Changes

Because authored questions are expanded into normal run items, existing practice
events remain largely correct.

Recommended additions:

- include `question_index` and `question_count` in prompt/session start events for expanded scenario items
- include authored-question metadata in stored prompt payload

This preserves traceability without introducing new workflow types.

---

## Backward Compatibility

- Existing scenarios with `questions=[]` continue to behave as single-question scenarios.
- Existing practice session start for standalone scenario sessions can continue to use the current single-prompt behavior unless separately upgraded.
- New generated or manually authored scenarios can opt into multi-question runtime automatically through stored questions.

No hidden question synthesis should occur for legacy scenarios.

---

## Testing Requirements

Add thorough coverage in:

- `backend/tests/unit`
- `backend/tests/integration`
- `backend/src/soft_skills_backend/smoke`

### Unit tests

- scenario command validation accepts non-empty questions and rejects blank ones
- scenario worker validation rejects wrong counts, blanks, and duplicates
- prompt building uses authored-question metadata when present
- run-item expansion produces one item per question and preserves ordering

### Integration tests

- creating and fetching a scenario persists `questions`
- practice run start expands a multi-question scenario into multiple run items
- each expanded item has its own prompt text and stable question progress metadata
- assessment submission still works unchanged for expanded scenario items
- assistant collection practice advances correctly through expanded scenario questions

### Smoke tests

- content generation smoke verifies generated scenarios include authored questions
- practice smoke verifies multi-question scenarios work end-to-end without custom submit-step logic

---

## Performance Guidance

To keep generation fast:

- preserve planner fan-out into prompt-item and scenario branches
- preserve worker parallelism with current child subpipeline caps
- keep scenario worker output schema minimal
- avoid extra question-generation subpipelines
- keep validation local and deterministic

If latency tuning is needed later, first adjust:

- scenario prompt verbosity
- planner output size
- max parallel scenario child count

Do not split one scenario into multiple serial LLM calls unless quality data proves it is necessary.

---

## Implementation Order

1. Update this plan and align contracts around the expanded-run-item design.
2. Add `questions` to scenario persistence, domain models, and views.
3. Update scenario generation planner, prompt contracts, worker variables, and validation.
4. Persist generated questions into scenarios.
5. Extend scenario run-item/start-input metadata for authored-question expansion.
6. Expand multi-question scenarios into multiple run items at practice-run build time.
7. Update scenario prompt rendering to include active question plus scenario context.
8. Add observability metadata for expanded scenario questions.
9. Add unit, integration, and smoke coverage.

---

## Open Follow-Ups

- whether standalone scenario sessions should also expand into multi-question sessions in a later phase
- whether future authored questions should become typed objects instead of plain strings
- whether run summaries should show grouped scenario-level progress in the frontend
