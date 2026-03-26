# Generation

## Purpose

This document defines how SoftSkills should implement and evolve AI-backed
content generation in the MVP and immediate post-MVP backend foundation. It is
the project-specific generation architecture and delivery guide for:

- collection generation
- prompt-item generation inside existing collections
- generation workflow modularization
- Stageflow topology choices for generation
- generation observability, persistence, retries, and validation

This document is subordinate only to
[CONSTITUTION.yml](/home/antonioborgerees/df/soft-skills/ops/CONSTITUTION.yml)
and should be read alongside:

- [content-system.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/operations/content-system.md)
- [stageflow-guide.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/stageflow-guide.md)
- [technical-architecture.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/technical-architecture.md)
- [observability-and-operations.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/operations/observability-and-operations.md)

## Why This Exists

SoftSkills already has provider-backed creator generation, but the current
implementation is intentionally simple:

- one request
- one typed LLM call
- one validated draft
- one persistence path

That was sufficient to establish the initial creator workflows, but it is not
the right long-term shape for:

- generating additional prompt items inside existing collections
- scaling content generation across multiple LLM calls
- isolating failures to a single generated unit
- improving realism and consistency through staged planning
- making generation traces more granular and replayable

The constitution requires typed contracts, fail-fast behavior, modular service
boundaries, explicit orchestration, and observability as truth. The generation
system must therefore move from a monolithic single-call draft generator to a
modular Stageflow-backed generation architecture.

## Generation Principles

### Generation Must Serve Learning, Not Volume

The goal is not to maximize question count or content throughput. The goal is
to produce realistic, coherent, editable content that supports competency
growth.

The system must therefore prefer:

- realistic workplace context
- skill and competency alignment
- rubric-compatible generation
- useful variation without drift
- editable drafts before publication

The system must reject:

- generic filler
- contradictory content
- taxonomy drift
- hidden best-effort degradation

### Known Metadata Should Be Deterministic

If the request or collection already determines a field, the model should not
be trusted to invent or echo it unless there is a clear reason.

In particular, generation should treat these as deterministic whenever possible:

- target audience
- difficulty
- enabled content formats
- target skill slugs
- target competency slugs
- rubric ids
- collection ownership and lifecycle metadata

The model should focus on what actually needs generation:

- titles
- summaries
- prompt text
- scenario context
- scenario tensions
- mock world details
- supporting artifacts

This reduces token usage, validation surface area, and retry volume.

### Validation Is A Hard Boundary

Every generation boundary must be schema validated before any downstream use.

Generation must fail loudly when:

- typed output schema validation fails
- generated metadata drifts from the request
- prompt types do not match rubric content types
- generated skills exceed collection skill scope
- duplicate or near-duplicate prompt items are detected where prohibited
- scenario internals are inconsistent

No silent fallback or partial hidden acceptance is allowed for invalid
artifacts.

### Persistence And Observability Are Product Features

Generation is not complete when text exists in memory. It is complete when the
system can explain:

- what was requested
- what prompt contract ran
- which provider and model produced each artifact
- which child runs were spawned
- which outputs passed validation
- which outputs failed and why
- what was persisted

This is required both for debugging and for creator trust.

## Current State

### Existing Full Collection Generation

The backend currently exposes two generation entrypoints:

- structured collection generation
- chat-based collection generation

The current implementation lives in:

- `backend/src/soft_skills_backend/modules/catalog/workflows/generation/service.py`
- `backend/src/soft_skills_backend/entrypoints/http/routes/collections.py`
- `backend/src/soft_skills_backend/platform/providers/llm/prompts.py`
- `backend/src/soft_skills_backend/modules/catalog/domain/models.py`

The current runtime shape is:

1. `input_guard`
2. `generate_transform`
3. `output_guard`
4. `persistence_work`

Both the structured and chat paths perform a single typed LLM call that
attempts to generate an entire `GeneratedCollectionDraft`, including:

- collection title and summary
- collection audience and difficulty
- content format mix
- target skill and competency slugs
- rubric ids
- multiple prompt items
- multiple scenarios
- nested mock companies, people, and supporting artifacts

The current design is valid but broad. One model call is responsible for too
many concerns simultaneously.

### Existing Prompt-Item Authoring

The backend already supports manually adding prompt items to collections via:

- `POST /api/collections/{collection_id}/prompt-items`

This uses existing typed contracts and validation:

- `PromptItemCreateCommand`
- `validate_prompt_command(...)`

There is currently no LLM-backed endpoint for generating prompt items inside an
existing collection.

## Current Pain Points

The current one-call generation shape creates several practical limits.

### Single Failure Domain

If one generated prompt item is malformed, the entire collection draft is
rejected. This is simple but inefficient and produces coarse-grained failure
handling.

### Oversized Prompt Contract

The model is asked to generate:

- collection metadata
- multiple prompts
- multiple scenarios
- nested mock world data

This makes the prompt contract large and increases the chance of:

- schema violations
- count drift
- inconsistent nested objects
- lower realism in individual items

### Weak Isolation

The current architecture cannot retry one bad prompt item or one bad scenario
in isolation. It has to retry the full draft generation.

### Missing Existing-Collection Generation

Creators can manually author prompt items in existing collections, but they
cannot ask the system to generate more questions that remain aligned to the
collection’s skills, formats, and rubrics.

### Tight Coupling Inside One Service

The current generation service owns:

- prompt rendering
- provider calling
- metadata validation
- persistence
- artifact recording
- scenario child persistence

That is workable for an MVP seed, but it is not the right shape for a scalable
generation surface.

## Target Capabilities

The generation system should support all of the following.

### Full Collection Generation

The system should generate a new collection draft with:

- generated title and summary
- deterministic request metadata
- requested prompt items
- requested scenarios
- validated mock-world content
- durable generation artifacts

### Prompt-Item Generation In Existing Collections

The system should generate one or more prompt items inside an existing
collection while preserving collection invariants.

Generated prompt items must:

- belong to the target collection
- use only prompt types enabled by the collection
- use only skill slugs that are a subset of the collection skill slugs
- use compatible rubrics
- land in `draft` lifecycle state
- remain editable before publication

### Multi-Call Generation

The system should support multiple LLM calls per user generation request in
order to:

- reduce the responsibility of each call
- improve reliability
- isolate retries
- enable bounded concurrency
- improve observability and replay

### Reusable Worker Pipelines

The system should expose reusable generation worker topologies for:

- prompt-item generation
- scenario generation

These workers should be callable from:

- full collection generation
- existing-collection prompt-item generation
- future creator tools if needed

## Scope

### In Scope

- new prompt-item generation endpoints for existing collections
- modularization of collection generation
- Stageflow parent pipelines and child subpipelines
- typed generation worker contracts
- fan-out generation orchestration
- generation artifact expansion
- duplicate detection and semantic guards
- generation-specific tests and smoke coverage

### Out Of Scope

- unconstrained agent loops for learner-facing assessment workflows
- marketplace publishing mechanics
- automatic publication of AI-generated content without creator review
- hidden best-effort acceptance of invalid child outputs
- provider-specific business logic leaking into catalog domain semantics

## API Design

### Existing Collection Prompt-Item Generation Endpoints

The system should add dedicated endpoints for generating prompt items inside an
existing collection.

Recommended endpoints:

- `POST /api/collections/{collection_id}/generate/prompt-items/structured`
- `POST /api/collections/{collection_id}/generate/prompt-items/chat`

These routes should remain thin and delegate into catalog generation services,
consistent with the architecture rules in the constitution.

### Proposed Commands

The exact names may evolve, but the backend should introduce typed request
contracts equivalent to:

- `PromptItemGenerationCounts`
- `StructuredPromptItemGenerationCommand`
- `ChatPromptItemGenerationCommand`
- `PromptItemGenerationView`

The structured request should capture:

- count
- desired prompt types or mix
- difficulty
- optional title or topic hints
- optional realism or domain notes
- optional exclusions or anti-goals

The chat request should capture:

- free-form prompt
- count
- optional desired prompt types or mix

Both commands should inherit deterministic collection context from the target
collection rather than asking the caller to resubmit the full collection
metadata.

### Response Shape

The response should return:

- the generated prompt items that were persisted
- generation artifact id
- generation mode
- prompt version
- provider
- model slug

If the implementation chooses to persist items and return the updated
collection view instead, that is acceptable, but generation metadata must still
be exposed clearly.

## Service Boundaries

### Catalog Generation Should Be Split

The current `CatalogGenerationService` should not continue growing as one
all-purpose generation file.

Generation responsibilities should be split across focused modules.

Recommended module layout:

- `modules/catalog/workflows/generation/contracts.py`
- `modules/catalog/workflows/generation/prompts.py`
- `modules/catalog/workflows/generation/validators.py`
- `modules/catalog/workflows/generation/persistence.py`
- `modules/catalog/workflows/generation/context.py`
- `modules/catalog/workflows/generation/subpipelines.py`
- `modules/catalog/workflows/generation/collection_service.py`
- `modules/catalog/workflows/generation/prompt_item_service.py`

If the team prefers a slightly different directory split, the important point
is the separation of responsibilities, not the exact file names.

### Responsibilities

The modular split should look like this.

`contracts.py`

- typed Pydantic models for generation requests and worker payloads
- typed draft contracts for prompt-item workers and scenario workers
- typed manifest or artifact payloads

`prompts.py`

- prompt names and versions
- prompt rendering helpers
- output format helpers
- no persistence or database access

`validators.py`

- metadata validation
- count validation
- duplicate checks
- coherence checks
- reuse of existing domain validators where possible

`context.py`

- loading collection context
- loading allowed skill, competency, and rubric scope
- shaping deterministic generation inputs

`persistence.py`

- atomic persistence of collection and child items
- atomic persistence of generated prompt items inside existing collections
- generation artifact persistence

`subpipelines.py`

- Stageflow child pipeline definitions
- child pipeline execution helpers
- parent-child correlation helpers

`collection_service.py`

- parent orchestration for full collection generation

`prompt_item_service.py`

- parent orchestration for existing-collection prompt-item generation

### Existing Validators Must Remain The Invariant Source

The existing catalog validators already encode important content invariants and
should remain authoritative.

In particular:

- `validate_collection_command(...)`
- `validate_prompt_command(...)`
- `validate_scenario_command(...)`

The new generation system should call these validators rather than re-encoding
their rules in parallel logic.

## Stageflow Design

### Stageflow Is The Right Orchestrator

Stageflow is a strong fit for generation because SoftSkills requires:

- explicit orchestration
- durable observability
- typed stage boundaries
- structured retries
- clear parent-child execution lineage

This aligns with the project’s Stageflow baseline in
[stageflow-guide.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/stageflow-guide.md)
and with the Stageflow docs for:

- pipeline DAGs
- parallel fan-out and fan-in
- subpipeline runs
- retry and backoff patterns

### When To Use Plain DAG Fan-Out

Use plain Stageflow DAG fan-out when the branches are structurally known at
pipeline-build time.

Examples:

- loading generation context in parallel
- running prompt-item branch and scenario branch in parallel after blueprint validation
- joining results in an assembly stage

This maps directly to Stageflow’s native fan-out and fan-in topology.

### When To Use Subpipelines

Use Stageflow subpipelines when the amount of work is discovered at runtime and
each unit benefits from isolated execution.

Examples:

- generating `N` prompt items after a blueprint determines there are `N`
- generating `M` scenarios after planning determines there are `M`
- retrying one invalid child output without rerunning the whole parent request

This is the correct place to use subpipelines, because child work needs:

- its own pipeline run id
- parent-child correlation
- cancellation propagation
- isolated retry behavior
- dedicated trace and observability lineage

### SoftSkills Rule For Generation Topology

Generation should use both patterns:

- parent pipelines for fixed high-level workflow stages
- child subpipelines for runtime-variable content units

This is the recommended architecture for collection generation and existing
collection prompt-item generation.

## Recommended Parent Pipelines

### Full Collection Generation Parent Pipeline

The recommended parent pipeline for full collection generation is:

1. `input_guard`
2. `context_enrich`
3. `blueprint_transform`
4. `blueprint_guard`
5. `prompt_items_work`
6. `scenarios_work`
7. `assemble_transform`
8. `output_guard`
9. `persistence_work`

#### Stage Responsibilities

`input_guard`

- validate request contract
- validate requested counts and format compatibility
- run prompt-security inspection for chat input where applicable

`context_enrich`

- resolve deterministic collection metadata inputs
- resolve allowed taxonomies
- resolve rubric compatibility and any lookup data needed by workers

`blueprint_transform`

- perform the planning call
- generate a `CollectionBlueprint`
- produce only generated planning content, not the full final draft

`blueprint_guard`

- validate blueprint count and structure
- validate required branches are present
- validate the blueprint does not drift from deterministic request metadata

`prompt_items_work`

- spawn prompt-item worker child pipelines
- collect validated prompt-item drafts
- collect child-run metadata

`scenarios_work`

- spawn scenario worker child pipelines
- collect validated scenario drafts
- collect child-run metadata

`assemble_transform`

- merge deterministic request metadata, blueprint output, prompt-item outputs,
  and scenario outputs into one final assembled generation artifact

`output_guard`

- perform final typed validation
- enforce collection-wide coherence and duplicate checks

`persistence_work`

- persist collection and children atomically
- persist generation artifact manifest
- emit catalog and generation events

### Existing Collection Prompt-Item Generation Parent Pipeline

The recommended parent pipeline for generating questions in an existing
collection is:

1. `input_guard`
2. `collection_context_enrich`
3. `plan_transform`
4. `plan_guard`
5. `prompt_items_work`
6. `output_guard`
7. `persistence_work`

This pipeline omits scenario generation and uses the target collection as the
primary source of deterministic metadata.

#### Stage Responsibilities

`input_guard`

- load the target collection
- require owner or admin
- validate requested prompt counts and requested prompt types

`collection_context_enrich`

- load collection metadata
- load existing prompt items for duplicate detection
- resolve enabled prompt types and compatible rubrics

`plan_transform`

- generate a prompt-item plan or mini-blueprint
- decide prompt-type mix and topical variation within the collection’s bounds

`plan_guard`

- validate counts
- validate prompt types are collection-enabled
- validate the plan remains inside collection scope

`prompt_items_work`

- spawn prompt-item worker child pipelines
- collect validated child results

`output_guard`

- validate the proposed prompt items against the collection using existing
  prompt validators
- run duplicate and near-duplicate checks

`persistence_work`

- persist generated prompt items in one transaction
- persist generation artifact
- update collection `updated_at`

## Recommended Child Pipelines

### Prompt-Item Worker Pipeline

The reusable prompt-item child pipeline should be:

1. `input_guard`
2. `draft_transform`
3. `output_guard`

Responsibilities:

- validate the worker input brief
- render a prompt-item-specific generation prompt
- call the model once for one prompt item or a tightly bounded mini-batch
- validate typed output
- return the validated draft plus artifact metadata

This child pipeline should not persist prompt items directly. Persistence stays
in the parent workflow.

### Scenario Worker Pipeline

The reusable scenario child pipeline should be:

1. `input_guard`
2. `draft_transform`
3. `output_guard`

Responsibilities:

- validate the scenario brief
- render a scenario-specific prompt
- call the model for one scenario
- validate nested mock-world content
- return the validated scenario draft plus artifact metadata

### Why Workers Should Not Persist

Persistence should remain in the parent pipeline because:

- the parent owns transactional boundaries
- the parent can fail the entire request before any domain write
- the parent can persist a single coherent artifact manifest
- creators should not receive partially written collections when sibling
  generation units fail

This preserves fail-fast behavior and keeps domain persistence explicit.

## Blueprint Strategy

### Move From Full-Draft Generation To Planning Plus Assembly

The current one-call shape asks the model to do too much in one pass. The
target architecture should use a blueprint-driven flow instead.

Recommended shape:

1. planner call generates a `CollectionBlueprint`
2. worker calls generate prompt-item drafts from prompt-item briefs
3. worker calls generate scenario drafts from scenario briefs
4. the system assembles the final result deterministically

### What The Blueprint Should Contain

The blueprint should focus on generative planning, not fully expanded content.

Recommended blueprint responsibilities:

- generated collection title and summary
- high-level thematic framing
- item-level briefs for each prompt item
- item-level briefs for each scenario
- optional diversity signals to avoid repetition

The blueprint should not redundantly own deterministic request metadata that
the system already has.

### Deterministic Assembly

The final assembled draft should be created by application code, not by another
large model call.

Assembly should:

- take deterministic request metadata directly from validated input
- take generated title and summary from the blueprint
- take validated prompt-item and scenario drafts from child workers
- attach artifact metadata and manifest details

This reduces drift and improves reproducibility.

## Prompt Design Guidance

### Separate Prompt Contracts By Responsibility

The system should introduce separate prompt contracts for:

- full collection planning
- existing-collection prompt-item planning
- prompt-item worker generation
- scenario worker generation

Do not keep one oversized prompt contract responsible for everything.

### Versioning

Each prompt contract must have an explicit prompt name and version.

Recommended categories:

- collection blueprint prompt
- prompt-item planner prompt
- prompt-item worker prompt
- scenario worker prompt

These versions must be persisted on generation artifacts or manifest entries.

### Prompt Security

Prompt-security enforcement should remain in place for user-supplied chat
generation inputs.

Structured requests should still sanitize free-form text fields such as:

- realism notes
- domain notes
- optional exclusions

## Validation Strategy

### Reuse Existing Domain Validators

Generated drafts should be converted into the existing command models where
possible and passed through current validators.

For prompt items:

- convert worker output into `PromptItemCreateCommand`
- validate against the target collection using `validate_prompt_command(...)`

For scenarios:

- convert worker output into `ScenarioCreateCommand`
- validate using `validate_scenario_command(...)`

For full collections:

- build a deterministic `CollectionCreateCommand`
- validate using `validate_collection_command(...)`

### New Generation-Specific Validators

Add generation-specific validation for:

- blueprint count alignment
- duplicate or near-duplicate prompt items
- repeated prompt-item titles within the same batch
- repeated scenario themes where disallowed
- scenario internal consistency beyond schema shape
- prompt-item novelty relative to existing collection items

### Duplicate Detection

Existing-collection prompt-item generation needs duplicate protection.

The system should compare normalized prompt candidates against:

- existing prompt-item titles
- existing prompt-item text
- already generated prompt items in the same batch

This can start with deterministic normalization and string comparison and later
expand to stronger semantic deduplication if needed.

### Hard Stop Rules

The generation flow should hard fail when:

- the count does not match the request
- worker output drifts outside collection scope
- no valid content remains after validation
- the final assembled output violates collection or scenario rules

The system must not silently drop invalid children and pretend the request
fully succeeded unless the request explicitly allowed partial success and the
API contract clearly models that state. MVP should prefer strict full success
or explicit failure.

## Retry Strategy

### Distinguish Semantic Retry From Transport Retry

SoftSkills should use two retry layers for different problems.

Provider-level retries:

- network issues
- rate limits
- transient upstream failures

These already belong in the provider adapter and should remain there.

Stageflow guard retries:

- invalid structured output
- count drift
- duplicate prompt items
- scenario coherence failures
- guard-reported semantic rejection

These belong at the workflow level and should be localized to the stage or
child pipeline that failed.

### Guard Retry Usage

Use Stageflow `GuardRetryStrategy` and `GuardRetryPolicy` for correction loops
where a guard validates an LLM result and asks the immediately preceding
generation stage to run again.

Recommended use cases:

- prompt-item worker `output_guard` retrying `draft_transform`
- scenario worker `output_guard` retrying `draft_transform`
- blueprint guard retrying `blueprint_transform` if the planner output drifts

This should be configured conservatively. Generation should not loop
indefinitely.

### Retry Scope

Prefer the smallest safe retry scope.

Good:

- retry one prompt-item worker
- retry one scenario worker
- retry one blueprint planner

Bad:

- rerun the full parent collection generation because one prompt item drifted

This is one of the main reasons to adopt subpipelines for runtime-variable
generation units.

## Concurrency Strategy

### Use Bounded Concurrency

The system should fan out generation, but not unboundedly.

Child subpipeline execution should use configurable concurrency caps such as:

- `max_prompt_item_children`
- `max_scenario_children`

These limits should be defined in versioned runtime config, not hidden in code.

### Why Bounded Concurrency Matters

It protects:

- provider rate limits
- database pressure during final persistence
- event sink throughput
- trace readability
- predictable latency

### Concurrency Shape

Use concurrency at two levels:

- parent-level branch parallelism between prompt-item and scenario work
- child-level worker parallelism within each branch

This gives good throughput without collapsing all work into one opaque step.

## Subpipeline Execution Strategy

### Use Direct Subpipeline Spawning, Not Tool Loops

SoftSkills generation should use Stageflow subpipeline primitives directly
rather than introducing the tool-executor layer for this problem.

This means generation stages should:

- reconstruct a `PipelineContext` from the parent `StageContext`
- fork or spawn child pipeline runs with correlation ids
- run dedicated child pipelines for each generation unit

This keeps the orchestration explicit and aligned with the current codebase,
which already uses direct `Pipeline` execution rather than Stageflow tool
agents.

### Parent-Child Correlation

Every child generation unit should carry:

- parent run id
- parent stage id
- correlation id
- child run id

This is important for:

- observability
- replay
- debugging bad generations
- creator-facing support investigations

### Repo Integration Requirement

SoftSkills currently uses a `run_logged_pipeline(...)` helper to ensure
application-level pipeline run logging. Raw child `Pipeline.run(...)` calls
would bypass that helper.

The generation system should therefore add a project-level helper for logged
child pipeline execution so that subpipelines preserve:

- DB-backed pipeline-run visibility
- event sink wiring
- interceptor stack consistency
- correlation metadata

This helper should be introduced in the shared Stageflow platform layer rather
than duplicated inside catalog services.

## Persistence Strategy

### Atomic Parent Persistence

Full collection generation should persist:

- collection record
- prompt item records
- scenario records
- mock company records
- mock person records
- supporting artifact records
- generation artifact record

in one transaction.

Existing-collection prompt-item generation should persist:

- generated prompt item records
- generation artifact record
- collection timestamp updates

in one transaction.

### Generation Artifact Evolution

The existing `ContentGenerationArtifactRecord` is a useful baseline, but
multi-call generation needs a richer manifest payload.

The generation artifact should include:

- top-level request input
- planner prompt version and output
- per-child worker prompt version and output metadata
- provider and model metadata per worker
- child run ids and correlation ids
- usage metrics where available
- final assembled validated output

This can be stored as a structured manifest inside the existing artifact table
if schema evolution is not yet necessary, or with a refined persistence model
if a clearer normalized representation becomes justified later.

### Draft Lifecycle

All AI-generated content should continue landing in `draft` state first.

Generation should assist authoring, not bypass review.

## Observability Requirements

### Observability Is Mandatory

Generation workflows must emit enough structured telemetry to support:

- trace-linked debugging
- provider analysis
- reliability monitoring
- content quality investigations
- replay and contract auditing

### Parent Pipeline Visibility

Parent generation pipelines should record:

- request mode
- target collection id where applicable
- requested counts
- generated counts
- generation artifact id
- pipeline duration
- failure stage and error code

### Child Pipeline Visibility

Child generation runs should record:

- child pipeline name
- parent run id
- parent stage id
- correlation id
- provider
- model slug
- prompt version
- success or failure
- retry count
- validation failure reason where applicable

### Domain Events

Generation should emit explicit domain events for major milestones such as:

- generation started
- blueprint generated
- child item generated
- generation failed
- draft persisted

The exact event taxonomy can evolve, but the workflow must remain traceable
end-to-end.

## Runtime Config

### Expand Generation Runtime Config

The catalog generation runtime config should move beyond the current
single-prompt shape.

It should eventually include:

- collection blueprint prompt name and version
- prompt-item planner prompt name and version
- prompt-item worker prompt name and version
- scenario worker prompt name and version
- schema version identifiers
- config version identifier
- concurrency limits
- optional child timeout limits
- optional guard retry tuning

### Versioning Rules

Prompt and config changes that alter behavior or output contracts must be
explicitly versioned and reflected in persisted artifacts.

## Proposed Implementation Phases

### Phase 1: Add Existing-Collection Prompt-Item Generation

Objective:

- add the missing creator capability with minimal disruption

Work:

- add structured and chat prompt-item generation commands and views
- add two new HTTP endpoints
- add a dedicated prompt-item generation workflow service
- reuse existing prompt-item validators
- persist generated prompt items and generation artifacts atomically
- add integration tests and provider smoke coverage

Why first:

- it delivers immediate creator value
- it exercises the new prompt-item worker model
- it avoids refactoring the whole collection generator upfront

### Phase 2: Extract Shared Generation Components

Objective:

- break the current monolithic generation service into reusable modules

Work:

- extract prompt rendering helpers
- extract shared validation helpers
- extract persistence helpers
- extract context-loading helpers
- add runtime config expansion

Why:

- this reduces coupling before the larger orchestration refactor

### Phase 3: Refactor Full Collection Generation To Blueprint Plus Fan-Out

Objective:

- replace the one-call collection generator with a modular multi-call pipeline

Work:

- add collection blueprint contract and prompt
- add prompt-item and scenario child pipelines
- add parent collection generation pipeline with branch fan-out and assembly
- add manifest-style generation artifacts
- keep persistence atomic at the parent

Why:

- this addresses the main scalability and reliability limits in the current
  design

### Phase 4: Reliability And Quality Hardening

Objective:

- make generation more resilient and operationally legible

Work:

- add duplicate and near-duplicate checks
- add guard retry policies for semantic correction loops
- tune concurrency and timeout controls
- improve observability dashboards and diagnostics
- expand real-provider smoke coverage

## Testing Requirements

Generation work is not complete without tests across all relevant boundaries.

### Required Coverage

Contracts:

- positive and negative validation for all new commands and views

Validators:

- prompt-type and rubric alignment
- collection-scope enforcement
- count validation
- duplicate detection
- drift rejection

Pipelines:

- successful structured prompt-item generation
- successful chat prompt-item generation
- child worker failure path
- blueprint failure path
- output guard rejection path
- artifact persistence path
- child correlation and logging path where possible

HTTP:

- route contracts for new endpoints
- auth and ownership enforcement
- failure-code assertions

Smoke:

- real-provider structured prompt-item generation
- real-provider chat prompt-item generation
- real-provider multi-call collection generation once refactored

### Testing Philosophy

Mock-only testing is not sufficient for provider-backed generation. Real
provider smoke coverage is mandatory before release readiness.

## Migration Guidance

### Do Not Break Existing Routes Prematurely

The current collection generation endpoints should remain available while the
new internal architecture is introduced.

Refactoring should preserve public route contracts until a deliberate API change
is approved and documented.

### Prefer Internal Refactoring Before External Expansion

When introducing new generation endpoints, share internals where safe, but do
not prematurely force the old and new workflows into one oversized abstraction.

The correct sequence is:

1. add focused worker and prompt-item generation flows
2. extract shared internals
3. move full collection generation onto the new architecture

## Final Recommendation

SoftSkills should adopt a Stageflow-native generation architecture with:

- parent pipelines for request-level orchestration
- child subpipelines for runtime-variable generation units
- deterministic metadata assembly
- typed worker contracts
- strict validation guards
- atomic persistence at the parent boundary
- rich manifest-style generation artifacts
- bounded concurrency and localized retries

In practical terms, this means:

- add prompt-item generation inside existing collections first
- do not extend the current single-call generator as the long-term architecture
- split generation into planning, worker generation, validation, assembly, and
  persistence concerns
- use DAG fan-out for fixed branches and subpipelines for runtime-discovered
  units

This is the architecture that best satisfies the constitution’s requirements
for typing, modularity, fail-fast behavior, observability, and realism-focused
content generation.
