# Stageflow Guide

## Purpose

This document explains how SoftSkills should use Stageflow in the MVP. It is a
project-specific guide, not a generic framework summary. The goal is to use as
many Stageflow features as are useful for the product while staying aligned
with `CONSTITUTION.yml`.

Stageflow is a good fit for SoftSkills because the constitution requires:

- explicit orchestration rather than hidden workflow behavior
- schema-validated boundaries
- observability as the source of truth
- fail-fast behavior with stable error semantics
- modular service boundaries and reusable components

This guide should be read alongside:

- [CONSTITUTION.yml](/home/antonioborgerees/df/soft-skills/ops/CONSTITUTION.yml)
- [technical-architecture.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/technical-architecture.md)
- [assessment-and-progression.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/platform/assessment-and-progression.md)
- [observability-and-operations.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/operations/observability-and-operations.md)

## Adoption Principles

### Use Stageflow For Orchestration, Not Business Semantics

Stageflow should own:

- stage ordering
- dependency execution
- interceptor middleware
- event emission
- tracing and correlation
- provider-call observability
- retries, checkpointing, and subpipeline orchestration where needed

Stageflow should not absorb:

- rubric semantics
- scoring interpretation
- progression math
- recommendation policy
- domain invariants

Those remain in SoftSkills domain and application services.

### Prefer Explicit Stage Kinds

Use Stageflow stage kinds consistently:

- `GUARD`: schema validation, policy checks, prompt-security checks, output validation
- `ENRICH`: profile lookup, prior-attempt retrieval, rubric loading, prompt/rubric metadata loading
- `ROUTE`: practice-mode branching, recommendation path selection, content-generation mode routing
- `TRANSFORM`: prompt rendering, LLM assessment, feedback shaping, recommendation scoring transforms
- `WORK`: persistence, event publication, progress snapshot writes, analytics writes, replay bookkeeping
- `AGENT`: creator-facing content-generation loops or other prompt-tool loops where an actual agent loop is required

### Keep Pipelines Thin And Reusable

Prefer multiple small pipelines and reusable components over one monolithic DAG.

Use composition for:

- shared guard components
- shared enrichment components
- shared observability setup
- shared assessment flow fragments

Use subpipelines only when the child run genuinely needs:

- execution isolation
- distinct topology or execution mode
- separate tracing lineage
- cancellation boundaries
- replayable nested orchestration

## SoftSkills Runtime Baseline

### Canonical Runtime Shape

For new code, use:

- `Pipeline`
- `PipelineContext`
- `pipeline.run(...)`
- `pipeline.build(...)` when graph reuse or build-time options are needed
- `stage_metadata(...)` or explicit stage registration with clear names and kinds

Do not build new MVP flows on deprecated `StageGraph` or `PipelineBuilder`
paths unless there is a specific compatibility reason.

### Standard Interceptor Baseline

Start from `get_default_interceptors()` for all production pipelines.

This gives SoftSkills:

- idempotency protection for `WORK` stages
- timeout handling
- circuit breaking
- tracing
- metrics
- child-run metrics
- logging

Use `include_auth=True` only where the pipeline is directly tied to an
authenticated request boundary and the auth adapter is ready.

### Default Event Sink Strategy

For production-oriented MVP workflows, prefer `BackpressureAwareEventSink`
instead of fire-and-forget-only sinks.

SoftSkills should use:

- `BackpressureAwareEventSink` for critical workflows
- `LoggingEventSink` in local development and simple tests
- a custom durable sink for persisted observability artifacts

The custom sink should persist enough data to support:

- replay
- dispute review
- trace-linked debugging
- assessment quality analysis

## Pipeline Design For SoftSkills

### Practice Runtime Pipelines

Use DAGs with parallel enrichments and explicit joins.

Recommended shape for assessment-backed text practice:

1. input guard
2. prompt/rubric/content enrich
3. learner/profile/attempt-history enrich
4. optional route stage
5. assessment transform
6. output guard
7. persistence work stages

This fits SoftSkills because content metadata, learner context, and rubric
context can load in parallel before the LLM call.

### Assessment Pipelines

Assessment pipelines should be explicit multi-stage flows, not one giant LLM
stage.

Recommended structure:

1. `GUARD`: validate attempt payload and required versions
2. `ENRICH`: load rubric, prompt contract, skills, competencies
3. `TRANSFORM`: render prompt and call model
4. `GUARD`: validate typed assessment output and evidence coherence
5. `TRANSFORM`: normalize for learner-facing feedback
6. `WORK`: persist assessment artifact
7. `WORK`: emit progress-update trigger/event

### Progression Pipelines

Use Stageflow for update orchestration, not for the progression algorithm
itself.

Recommended structure:

1. `GUARD`: ensure assessment is validated and version-complete
2. `TRANSFORM`: normalize skill evidence
3. `TRANSFORM`: compute skill updates
4. `TRANSFORM`: compute competency updates
5. `WORK`: persist snapshot and explainability ledger
6. `WORK`: emit downstream recommendation refresh event

### Recommendation Pipelines

Recommended structure:

1. `ENRICH`: learner context
2. `ENRICH`: latest progress snapshot
3. `ENRICH`: candidate content metadata
4. `GUARD`: verify candidate contracts and trust state
5. `TRANSFORM`: score candidates
6. `TRANSFORM`: explain reason codes
7. `WORK`: persist recommendation artifact

### Content Generation Pipelines

Use Stageflow AGENT features here before using them in assessment-critical
flows.

Recommended use:

- `PromptLibrary` for versioned generation prompts
- `PromptSecurityPolicy` for handling user authoring prompts and tool output
- `TypedLLMOutput` for structured draft payloads
- `Agent` or `AgentStage` only if the generation flow truly benefits from a
  tool loop
- `AdvancedToolExecutor` if generation becomes tool-driven and needs approvals,
  undo, or richer telemetry

Do not use unconstrained agent loops for learner assessment paths in MVP.

## Observability And Tracing

### Treat Observability As A First-Class Product Artifact

SoftSkills should use Stageflow observability features to satisfy the
constitution rule that observability is truth.

Adopt by default:

- stage events
- pipeline events
- custom domain events
- provider call logs
- correlation IDs
- tracing interceptor
- pipeline run logging

### Correlation Model

Map Stageflow correlation fields onto SoftSkills identifiers.

Always populate where applicable:

- `pipeline_run_id`
- `request_id`
- `trace_id`
- `session_id`
- `user_id`
- `org_id`
- `interaction_id`

Also carry domain IDs in event/log payloads when known:

- `attempt_id`
- `assessment_id`
- `collection_id`
- `recommendation_id`
- `workflow_id`
- `prompt_version`
- `rubric_version`
- `model_slug`
- `provider`

### Wide Events

Use Stageflow wide events for critical backend flows where one denormalized
record per stage or run is valuable.

Use on:

- assessment runs
- progression updates
- recommendation generation
- content generation

This is a strong fit for SoftSkills because it simplifies audit queries and
dispute review.

### Provider Call Logging

Use `ProviderCallLogger` for all external provider-backed stages:

- LLM assessment
- LLM content generation
- future STT/TTS flows if added

Every provider-backed stage should record:

- operation
- provider
- model id
- latency
- success/failure
- token usage or equivalent metrics

### Backpressure And Streaming Telemetry

If a flow uses `ChunkQueue`, `StreamingBuffer`, or `BufferedExporter`, wire the
event emitter so `stream.*` and `analytics.overflow` events are emitted.

This is not central to the text-first MVP, but it should be used for:

- any future streaming/voice work
- analytics exporters that may build pressure under load

## Structured Outputs And Contracts

### Typed Stage Outputs

Use `TypedStageOutput` for any stage that emits structured payloads consumed by
other stages or persisted for replay.

This is strongly recommended for:

- assessment artifacts
- feedback payloads
- progress snapshot payloads
- recommendation payloads
- content generation draft payloads

Benefits:

- Pydantic validation
- explicit schema version tagging
- compatibility diffing
- contract registration and linting support

### Typed LLM Outputs

Use `TypedLLMOutput` whenever a model must return structured JSON.

This is a strong fit for:

- assessment output contracts
- draft collection/scenario generation
- recommendation explanation artifacts if model-generated

SoftSkills should not trust raw model text for structured outputs.

### Prompt Versioning

Use `PromptLibrary` and `PromptTemplate` for versioned prompts.

This should be the standard for:

- assessment prompts
- feedback prompts
- generation prompts

Prompt versions must be persisted on produced artifacts so replay and quality
review remain possible.

### Prompt Security

Use `PromptSecurityPolicy` for AGENT flows and any place where user-authored or
tool-returned content gets injected into later model turns.

Use especially for:

- chat-based content generation
- tool-driven agent loops

It is less relevant for fixed-form assessment prompts unless the assessment flow
actually composes untrusted model/tool output into later turns.

## Interceptor Strategy For SoftSkills

### Use The Built-In Stack Everywhere Practical

SoftSkills should rely on the default Stageflow stack for baseline reliability
and observability.

### Add Project-Specific Interceptors Selectively

Recommended custom additions:

- custom retry/backoff interceptor for transient provider failures
- checkpoint interceptor for expensive generation and replay/recalculation flows
- context-size interceptor in development/staging
- immutability interceptor in development/testing
- rate-limiting interceptor at request-sensitive boundaries if needed
- analytics overflow interceptor if exporter pressure becomes meaningful

### Retry And Backoff

Adopt the retry/backoff pattern for transient provider-backed stages only.

Use for:

- LLM calls
- rate-limited external services

Do not retry:

- invalid schema outputs that reflect a prompt/contract problem after bounded
  corrective attempts
- auth failures
- rubric/content mapping failures
- policy failures

Pair retries with:

- circuit breaker behavior
- idempotent `WORK` stages
- retry events and metrics

### Idempotency

Use the built-in idempotency behavior for `WORK` stages that mutate state.

Apply to:

- assessment persistence
- progress snapshot writes
- recommendation artifact writes
- content publication state changes

Set stable keys and parameter hashes in `ctx.data` before the stage executes.

### Checkpointing

Use checkpointing selectively rather than everywhere.

Recommended uses:

- long-running content generation
- benchmark/replay jobs
- progression recalculation jobs
- expensive batch diagnostics

Not recommended for:

- normal low-latency request-response practice scoring

### Custom Interceptors

Use custom interceptors for cross-cutting concerns that should not live inside
stages, such as:

- central retry logic
- centralized analytics overflow hooks
- policy enforcement over pending tool calls
- request-level rate limiting

Keep them focused and use namespaced `ctx.data` keys.

## Guard And Security Guidance

### Fail Closed By Default

SoftSkills is assessment- and trust-sensitive, so `GUARD` stages should fail
closed by default.

Use guard stages for:

- request schema validation
- attempt/rubric compatibility checks
- assessment output contract validation
- evidence coherence checks
- content-generation safety checks
- cross-tenant or unauthorized access checks

### Output Guards Matter

Do not stop at input guards. Use output guards to validate:

- required fields
- score ranges
- evidence coverage
- contradiction rules
- prompt/rubric/model metadata presence

### Injection Detection

Use prompt-security and injection-detection patterns for:

- chat-based creator prompts
- agent/tool loops

This is less central to the core assessment MVP but should still be available in
the content-generation path.

## Agent And Tooling Guidance

### Where To Use AgentStage

Use `AgentStage` only where a real iterative tool loop is justified.

Good MVP fit:

- creator chat generation
- internal ops helpers

Poor MVP fit:

- core learner assessment path
- progression computation
- recommendation scoring

### Tool Resolution

Use `ToolRegistry.parse_and_resolve()` instead of hand-parsing provider tool
calls.

Emit `tools.unresolved` whenever resolution fails.

### AdvancedToolExecutor

Prefer `AdvancedToolExecutor` over legacy tool executors for new agentic work if
you need:

- approval workflows
- undo metadata
- richer lifecycle events
- stronger execution telemetry

This is most relevant to creator/admin tooling, not learner practice flows.

## Subpipelines And Composition

### Composition

Use pipeline composition to build shared components for:

- input/output guards
- content/rubric/profile enrichment
- common persistence fragments
- shared observability hooks

### Subpipelines

Use subpipelines only when child-run semantics are useful.

Recommended MVP uses:

- agentic content-generation helpers
- heavy recalculation/replay jobs
- isolated tool-execution flows

If used, always preserve:

- parent-child correlation IDs
- child-run metrics
- child event lineage
- cancellation propagation

Avoid deep nesting. One level is usually enough for MVP.

## Testing Strategy

### Use Stageflow Testing Utilities

Adopt the built-in test helpers:

- `create_test_snapshot`
- `create_test_stage_context`
- `create_test_pipeline_context`
- snapshot validation helpers

### Contract Testing

Use typed outputs and contract registration so CI can diff versions and catch
breaking changes early.

This is especially valuable for:

- assessment artifact schemas
- progress snapshot schemas
- recommendation artifact schemas

### Test Pyramid

For Stageflow-backed SoftSkills pipelines:

- unit test stages and domain adapters
- integration test full pipeline execution and data flow
- test event and trace emission
- test failure paths and cancellation
- test retry behavior and idempotency
- run real-provider smokes for provider-backed pipelines

### Observability Tests

Explicitly test:

- stage and pipeline events
- wide-event emission on critical flows
- provider call logging
- unresolved tool-call events when relevant
- streaming/backpressure telemetry if used

## Recommended MVP Adoption By Sprint

### Sprint 1

- `Pipeline`, `PipelineContext`, `get_default_interceptors()`
- `BackpressureAwareEventSink`
- `PipelineRunLogger`
- `ProviderCallLogger`

### Sprint 2

- typed outputs for identity/content contracts
- auth interceptors where request boundaries need them
- composition for reusable catalog/guard fragments

### Sprint 3

- versioned prompts
- `TypedLLMOutput` for assessment artifacts
- wide events for assessment runs
- provider call logging
- idempotent persistence on assessment writes

### Sprint 4

- shared assessment pipeline components reused across practice modes
- guard stages for scenario/interview payload validation
- regression tests on richer DAGs

### Sprint 5

- typed outputs for progress and recommendation artifacts
- pipeline run logging and wide events for update/recommend flows
- replay-friendly artifact persistence

### Sprint 6

- `PromptLibrary`, `PromptSecurityPolicy`, `TypedLLMOutput`
- `AgentStage` and `AdvancedToolExecutor` only if chat generation truly needs a
  tool loop

### Sprint 7

- audit-friendly pipeline and provider logs
- auth/org enforcement where admin visibility boundaries matter
- replay hooks and trace-linked diagnostics

### Sprint 8

- contract diff checks
- trace/event completeness checks
- real-provider smokes for all provider-backed DAGs
- optional hardening interceptors in non-prod verification

## Features To Defer Or Use Sparingly

- duplex systems for voice/realtime paths
- fail-open guards in trust-sensitive flows
- deep subpipeline nesting
- agent loops in core assessment orchestration
- checkpointing on every low-latency request path
- immutability interceptor in production hot paths

## Bottom Line

SoftSkills should use Stageflow aggressively for orchestration, observability,
typed contracts, retries, idempotent work, and agentic content-generation
support. It should not outsource domain truth to the framework. The framework
provides the execution substrate; SoftSkills must still own scoring semantics,
progress meaning, recommendation policy, and constitution compliance.
