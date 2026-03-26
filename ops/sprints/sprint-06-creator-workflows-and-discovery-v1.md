# Sprint 6: Creator Workflows And Discovery V1

> Project: SoftSkills
> Scope: Backend and platform execution only. Frontend planning is tracked separately.

## Sprint Overview

- Sprint Name: Sprint 6: Creator Workflows And Discovery V1
- Sprint Focus: Support complete draft-to-published creator workflows without compromising content quality or trust
- Depends On: Sprint 5

## Relevant Source Docs

- [CONSTITUTION.yml](/home/antonioborgerees/df/soft-skills/ops/CONSTITUTION.yml): lines 100-133, 207-221, 377-392
- [foundational/product-spec.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/product-spec.md): lines 37-42, 120-131, 153-157
- [operations/content-system.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/operations/content-system.md): lines 50-115
- [operations/observability-and-operations.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/operations/observability-and-operations.md): lines 9-91
- [foundational/stageflow-guide.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/stageflow-guide.md): lines 189-204, 291-349, 432-466, 468-502, 612-616

## Sprint Goals

- Primary Goal: The backend supports high-quality creator workflows from manual draft authoring through trusted publish states.
- Secondary Goals:
  - Mature manual authoring beyond bare CRUD.
  - Add structured generation and chat-based draft generation behind strict content contracts.
  - Support publish and discovery semantics that distinguish standard public content from verified content.

## Scope Checklist

- [x] Task 1: Expand manual authoring workflows and validation for collections, prompts, scenarios, and supporting artifacts; keep authoring validation in explicit guard stages
- [x] Task 2: Implement structured generation flow for draft content with required metadata and editability; use `PromptLibrary`, `PromptSecurityPolicy`, and `TypedLLMOutput`
- [x] Task 3: Implement chat-based draft generation flow under the same validation and versioning rules; use `AgentStage` and `AdvancedToolExecutor` only if a real tool loop is justified, and emit `tools.unresolved` on failed tool resolution
- [x] Task 4: Implement publish-state transitions, save/reuse behavior, and verified-vs-standard catalog semantics
- [x] Task 5: Documentation updates for all changed behavior and contracts

## Constitution And Quality Checklist

- [x] Competency growth remains the product outcome, not activity theater
- [x] All new external boundaries are typed and schema-validated
- [x] Fail-fast and fail-loud behavior is preserved with stable error codes
- [x] Route handlers remain thin; business rules stay out of transport layers
- [x] Dependency injection and adapter boundaries remain explicit
- [x] Critical workflow artifacts are durably persisted where required
- [x] Traces, logs, and events cover all changed workflow steps
- [x] Prompt, rubric, model, and config versions are preserved where applicable
- [x] Assessment and progression behavior remains explainable
- [x] No silent fallback is introduced in scoring, progression, generation, or recommendation paths

## Testing And Documentation Checklist

- [x] Unit Tests: content validation rules, generation input/output schemas, publish-state rules, and verification-state guards
- [x] Integration Tests: manual authoring, structured generation, chat generation, publish transitions, and catalog query behavior
- [x] Smoke Tests With Real Provider: run backend smokes for structured generation and chat-based draft generation against the real provider
- [x] Failure Path Coverage: invalid generation outputs, incomplete metadata, inconsistent mock-world data, and bad publish transitions tested
- [x] Documentation Updates: update canonical docs in `ops/`, the roadmap/sprint docs, and any affected contracts

## Success Criteria

- [x] Creator workflows support valid draft creation, editing, and publication behavior
- [x] Generated drafts are editable, validated, versioned, and fully traceable
- [x] Catalog semantics clearly distinguish standard public content from verified content
- [x] Real-provider generation smokes pass from the backend without manual patch-up steps

Minimum Viable Sprint:
Manual and generated draft workflows work for core content types even if discovery ranking remains simple.

## Risks And Blockers

| Risk | Impact | Mitigation | Status |
| --- | --- | --- | --- |
| Generated content becomes generic or internally inconsistent | High | Enforce strong schema, metadata, and realism validation before publication | Open |
| Draft generation bypasses the same rules as manual authoring | High | Force all authoring paths through shared validation and lifecycle logic | Open |

## Sprint Notes

Key decisions, tradeoffs, and implementation notes:

```text
- Draft editing now exists for collections, prompt items, and scenarios, including scenario supporting artifacts.
- Generation uses `PromptLibrary`, `TypedLLMOutput`, and `PromptSecurityPolicy`; no `AgentStage` or `AdvancedToolExecutor` was introduced because this sprint did not justify a real tool loop.
- Generated drafts persist collection-scoped generation artifacts with input payload, validated output payload, prompt version, schema version, provider, model slug, trace ID, and workflow ID.
- Discovery now exposes private vs standard-public vs verified-public tiers, plus save/unsave state for reuse.
- The real-provider smoke was updated to hit both generation endpoints and then run the existing assessment modes against stable manual runtime fixtures.
```

## Review And Sign-Off

- Sprint Status: Completed
- Completion Date: 2026-03-26

Checklist:

- [x] Primary goal achieved
- [x] Constitution and quality checks passed
- [x] Unit tests completed
- [x] Integration tests completed
- [x] Smoke tests with real provider completed
- [x] Documentation updated
- [x] Code review completed

Next Sprint Priorities:

1. Add admin verification workflows and visibility boundaries.
2. Expose learner and cohort analytics from trustworthy backend data.
3. Expand replay and audit support for operational trust.
