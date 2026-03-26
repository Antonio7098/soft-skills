# Chat Assistant

## Purpose

This document defines the MVP implementation plan for a user-facing chat
assistant that can:

- receive the user message plus durable session context
- be grounded in the user's skill profile and progress stats
- read the user's collections
- query the user's past attempts
- invoke existing content-generation workflows
- stream tool activity and the final assistant response to the UI
- persist conversations and replay them later
- emit Stageflow-native traces, events, metrics, and provider-call telemetry

This assistant is a product workflow, not a thin LLM proxy. It must satisfy the
constitution rules for typed contracts, explicit orchestration, fail-fast
behavior, and observability as truth.

This document should be read alongside:

- [CONSTITUTION.yml](/home/antonioborgerees/df/soft-skills/ops/CONSTITUTION.yml)
- [technical-architecture.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/technical-architecture.md)
- [domain-model.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/domain-model.md)
- [stageflow-guide.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/stageflow-guide.md)
- [generation.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/operations/generation.md)
- [observability-and-operations.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/operations/observability-and-operations.md)

## Product Decision

The MVP should introduce a separate assistant runtime instead of overloading the
existing practice-session or generation endpoints.

The assistant owns:

- conversational session lifecycle
- turn orchestration
- context enrichment
- tool invocation
- streaming delivery to the UI
- response persistence
- replayable observability

The assistant does not own:

- generation domain semantics
- collection domain rules
- attempt scoring semantics
- progression logic

Those remain in the existing application and domain services.

## Current Implementation Status

The first backend slice is now implemented with:

- dedicated `assistant_sessions`, `assistant_turns`, `assistant_messages`, and
  `assistant_tool_calls`
- `POST /api/assistant/sessions`
- `GET /api/assistant/sessions`
- `GET /api/assistant/sessions/{session_id}`
- `GET /api/assistant/sessions/{session_id}/messages`
- `POST /api/assistant/sessions/{session_id}/turns`
- `GET /api/assistant/turns/{turn_id}`
- `POST /api/assistant/turns/{turn_id}/cancel`
- `WS /api/assistant/streams/{stream_token}`
- Stageflow turn orchestration with parallel `history`, `profile`,
  `progress`, and `recent_attempts` enrich stages
- parallel execution of independent tool calls inside one agent step
- assistant-triggered generation tools executed through Stageflow subpipelines
- graceful cancellation built on Stageflow pipeline cancellation semantics with
  task-cancel escalation for slow in-flight work

Current constraints in this first implementation:

- the live stream endpoint is token-based rather than session-and-turn path-based
- provider-native token streaming is used for the final assistant response, but
  the structured tool-planning loop still uses JSON completions before that
- the WebSocket control surface is intentionally minimal and currently focused
  on stream delivery, ping, and cancellation rather than a broader live command
  protocol

Real-provider validation has now been executed for:

- assistant read flow
- assistant-triggered generation flow

## Transport Decision

### Use WebSocket For MVP

The default live transport should be WebSocket, not SSE.

Reasons:

- the product now needs both server-to-client streaming and client-to-server
  control messages
- graceful cancellation is a first-class feature, not a later add-on
- tool lifecycle events and response deltas can share one live channel with
  cancellation commands
- durable turn state still provides replay and recovery after disconnects

### Use An Event-Driven UI Model

The UI should not poll for tool state. The turn runtime should emit a stream of
typed events and the frontend should update as those events arrive.

The durable source of truth remains the database and observability artifacts.
WebSocket is the delivery transport for live state and control messages, not
the canonical data store.

## Core Design Rules

### Keep The Assistant As An Orchestrator

The assistant should call existing application services and Stageflow-backed
workflows. It should not reimplement generation, collection reads, or attempt
history logic inside prompts.

### Do Not Make Loopback HTTP Calls

The assistant may expose new HTTP endpoints, but internal tool handlers should
not call the backend's own HTTP generation endpoints over the network.

Instead, tool handlers should call the same underlying services used by:

- `POST /api/collections/generate/structured`
- `POST /api/collections/generate/chat`
- `POST /api/collections/{collection_id}/generate/prompt-items/structured`
- `POST /api/collections/{collection_id}/generate/prompt-items/chat`

This keeps contracts typed, preserves transaction boundaries, and produces
cleaner traces.

### Separate Chat Sessions From Practice Sessions

The existing `practice_sessions` model is for learner prompt delivery and
attempt lifecycle. Assistant conversations have different semantics and must
not be forced into that model.

Create dedicated assistant persistence for:

- conversational sessions
- turn execution state
- persisted messages
- tool-call audit rows

### Parallelise Aggressively Where Dependencies Allow

Parallelisation should be a first-class design goal across the full turn
topology, not only in enrichment.

Stageflow is especially strong when the workflow is modeled as explicit fan-out
and fan-in:

- independent reads should run concurrently
- independent transforms should run concurrently
- multiple independent tool calls in one agent step should run concurrently
- child subpipelines should run concurrently where semantics allow
- post-commit projection and event publication should run concurrently
- cancellation should fan out immediately to active executors and child runs

Do not serialize work unless one step truly depends on another.

## MVP Scope

### In Scope

- assistant session create/list/get APIs
- assistant turn create API
- WebSocket stream API
- durable assistant session, turn, message, and tool-call persistence
- graceful cancellation for running turns
- Stageflow orchestration for each chat turn
- user context enrichment from profile and progress snapshot
- tool access for collection reads and attempt-history reads
- tool access for generation workflows
- full trace and event correlation across turns and child workflows
- operational dashboards and queryable metrics

### Out Of Scope

- voice and audio streaming
- human approval flows for tools
- arbitrary external web tools
- direct mutation of attempts, assessments, or progress through the assistant
- automatic publication of generated content without existing validation paths

## Target Endpoint Surface

### Session Endpoints

- `POST /api/assistant/sessions`
- `GET /api/assistant/sessions/{session_id}`

### Turn Endpoints

- `POST /api/assistant/sessions/{session_id}/turns`
- `POST /api/assistant/turns/{turn_id}/cancel`
- `WS /api/assistant/streams/{stream_token}`

The canonical live path should be:

1. client `POST`s a turn
2. backend persists the user message and turn row
3. backend returns the turn payload with `turn_id` and `stream_token`
4. client opens WebSocket on `/api/assistant/streams/{stream_token}`
5. backend streams tool and response events until completion or cancellation

### Optional Session Control Endpoint

- `POST /api/assistant/sessions/{session_id}/archive`

## Request And Response Contract

### Create Session Request

The initial session create contract should be minimal:

- optional title
- optional `working_collection_id`
- optional `session_mode`

Recommended `session_mode` values:

- `general`
- `content_creation`
- `practice_review`

### Create Turn Request

The turn create contract should include:

- `message`
- optional `working_collection_id`
- optional `metadata`

Do not require the client to send profile, progress, collections, or attempts.
Those should be enriched server-side from trusted persistence.

### Create Turn Response

Return:

- `turn_id`
- `user_message_id`
- `stream_token`
- `trace_id`
- `workflow_id`

The final assistant message should arrive through the event stream and also be
durably queryable afterward through session message APIs.

### WebSocket Event Contract

Every streamed event should include:

- `event_id`
- `turn_id`
- `session_id`
- `trace_id`
- `workflow_id`
- `timestamp`
- `payload`

Reconnect should support tail replay using the last seen event sequence so the
client can request only unseen events after reconnect.

Recommended WebSocket event types:

- `turn.started`
- `turn.context_ready`
- `tool.requested`
- `tool.started`
- `tool.completed`
- `tool.failed`
- `response.delta`
- `response.completed`
- `turn.completed`
- `turn.failed`
- `turn.cancel_requested`
- `turn.cancelling`
- `turn.cancelled`

The same socket should also accept client-to-server control messages at minimum
for:

- `turn.cancel`
- `turn.ping`

## Persistence Model

### AssistantSession

Create `assistant_sessions` with at least:

- `id`
- `user_id`
- `organisation_id` where applicable
- `session_mode`
- `status`
- `title`
- `working_collection_id` nullable
- `last_message_id` nullable
- `created_at`
- `updated_at`
- `archived_at` nullable

Recommended status values:

- `active`
- `archived`
- `failed`

### AssistantTurn

Create `assistant_turns` with at least:

- `id`
- `session_id`
- `user_id`
- `user_message_id`
- `assistant_message_id` nullable
- `status`
- `stream_transport`
- `request_id` nullable
- `trace_id`
- `workflow_id`
- `pipeline_run_id` nullable
- `started_at`
- `completed_at` nullable

Recommended status values:

- `queued`
- `running`
- `cancelling`
- `cancelled`
- `completed`
- `failed`

Recommended `stream_transport` values:

- `websocket`
- `none`

### AssistantMessage

Create `assistant_messages` with at least:

- `id`
- `session_id`
- `turn_id`
- `user_id`
- `role`
- `message_kind`
- `turn_index`
- `content_text`
- `content_payload` JSON
- `status`
- `model_slug` nullable
- `provider` nullable
- `prompt_version` nullable
- `request_id` nullable
- `trace_id`
- `workflow_id`
- `pipeline_run_id` nullable
- `parent_message_id` nullable
- `created_at`

Recommended `role` values:

- `user`
- `assistant`
- `tool`
- `system`

Recommended `message_kind` values:

- `chat`
- `tool_result`
- `error`
- `summary`

Recommended `status` values:

- `accepted`
- `partial`
- `completed`
- `failed`

Persist the user message before running the assistant turn. Persist the
assistant message even on partial tool failure if the final response is still
valid. Persist failure messages explicitly when the workflow terminates without
a usable assistant answer.

### AssistantToolCall

Create `assistant_tool_calls` with at least:

- `id`
- `session_id`
- `turn_id`
- `message_id`
- `tool_name`
- `tool_call_id`
- `status`
- `arguments_payload`
- `result_payload`
- `error_code` nullable
- `started_at`
- `finished_at`
- `trace_id`
- `workflow_id`
- `pipeline_run_id` nullable
- `child_pipeline_run_id` nullable

Recommended status values:

- `requested`
- `started`
- `completed`
- `failed`
- `denied`

This table is required even though Stageflow emits tool events. It gives the
product a durable assistant-facing replay surface without forcing every UI query
through raw event logs.

### AssistantStreamEvent

Create `assistant_stream_events` with at least:

- `id`
- `event_id`
- `session_id`
- `turn_id`
- `user_id`
- `sequence_number`
- `event_type`
- `payload`
- `emitted_at`

This table is required for:

- durable WebSocket replay
- ordered reconnects using the last seen event sequence
- UI-safe reconstruction of tool and response activity after disconnects

## Context Model For Each Turn

Every turn should build a typed context envelope before the agent loop starts.

Recommended envelope sections:

- `user_profile`
- `progress_snapshot`
- `recent_attempt_summary`
- `working_collection_summary`
- `recent_session_messages`
- `assistant_capabilities`

### User Profile

Pull from learner profile and stable identity data:

- target role
- goals
- practice preferences

### Progress Snapshot

Pass a compact summary, not the full progression ledger. Include:

- key skill levels
- weak skills
- recent trend signals
- confidence or evidence counts if available

### Attempt Summary

Do not dump all attempts into the prompt. Include a bounded summary by default:

- latest attempts
- recent assessed scores
- flagged weak areas
- linked collection or content identifiers

Use tools for deeper attempt lookup when needed.

## Tool Surface

The MVP tool surface should stay narrow and product-specific.

### Read Tools

Implement:

- `list_user_collections`
- `get_collection_detail`
- `list_recent_attempts`
- `get_attempt_detail`

These should be read-only and access-controlled against the authenticated user
and organisation context.

### Generation Tools

Implement:

- `generate_collection_structured`
- `generate_collection_chat`
- `generate_prompt_items_structured`
- `generate_prompt_items_chat`

These tools should call the existing catalog generation services directly.

### Tool Contract Rule

Every tool must define:

- explicit JSON schema input
- typed output model
- stable tool name
- stable failure semantics

### Tool Execution Rule

For new assistant work, prefer Stageflow `Agent` plus `AgentStage` for the loop
and `AdvancedToolExecutor` for tool execution telemetry.

Use:

- `PromptLibrary` for versioned system prompts
- `PromptSecurityPolicy` for user and tool content
- `ToolRegistry.parse_and_resolve()` for model tool calls
- `AdvancedToolExecutor` for richer lifecycle events

The MVP does not need human approval workflows because the tool set is bounded
to reads and draft generation through existing guarded services.

### Parallel Tool Call Rule

If the model emits multiple independent tool calls in one agent step, execute
them in parallel and fan their results back into the next model turn together.

Do not force sequential tool execution when the calls are independent.

If a later tool depends on an earlier result, that dependency should be modeled
as a later agent-loop step, not hidden inside the executor.

## Orchestration Topology

### Session Create Flow

Recommended pipeline:

1. `GUARD`: validate request
2. `WORK`: persist session
3. `WORK`: emit `assistant.session_started.v1`

### Turn Flow

Recommended high-level pipeline:

1. `GUARD`: validate request and auth
2. `WORK`: persist user message and create turn record
3. parallel enrich stages
4. parallel transform stages where possible
5. `AGENT`: run assistant loop with tools and streaming callbacks
6. `GUARD`: validate final assistant output contract
7. `WORK`: persist assistant message and finalize turn
8. parallel post-commit projection and event emission

### Parallel Turn DAG

The default turn DAG should be:

```text
[request_guard] -> [persist_user_message]
                      |-> [session_enrich] ----------|
                      |-> [profile_enrich] ----------|
                      |-> [progress_enrich] ---------|
                      |-> [history_enrich] ----------|
                      |-> [attempts_enrich] ---------|-> [context_assemble] -> [prompt_render]
                      |-> [working_collection_enrich]-|                            |
                                                                               [tool_manifest]
                                                                                     |
                                                             [prompt_render] ---------|
                                                             [tool_manifest] ---------|-> [agent]
```

This is the minimum shape. The implementation should continue looking for
independent work beyond enrichments.

### Parallelisation Strategy

Parallelise these categories by default:

- all independent enrich stages
- independent context-normalisation transforms after reads complete
- prompt rendering and tool-manifest shaping if both depend only on assembled
  context
- parallel tool execution for independent calls in one agent step
- child subpipelines for independent generation units
- post-commit event projection, metrics projection, and stream fan-out
- cancellation fan-out to active tool executors and child subpipelines

Do not parallelise:

- writes that must stay in one transaction to preserve invariants
- tool calls with explicit data dependencies
- final turn completion before the authoritative assistant message is durable

### Streaming Execution Rule

The turn pipeline should emit UI-facing events as work progresses:

- immediately after turn start
- when context is ready
- on each tool lifecycle transition
- on response text deltas
- on final completion or failure

These events should be published through the same correlation model used for
durable observability. The WebSocket adapter should subscribe to turn-scoped
events and fan them out to connected clients.

### Graceful Cancellation Rule

Cancellation is a product feature and a workflow invariant.

The assistant runtime must support:

- cancellation requested by the client over WebSocket
- optional HTTP cancel as a fallback control surface
- transition from `running` to `cancelling` to `cancelled`
- prompt shutdown of active tool execution
- prompt shutdown or cancellation propagation to active child subpipelines
- deterministic persistence of the final cancelled turn state

Implement cancellation using Stageflow pipeline cancellation semantics rather
than only ad hoc application flags.

The preferred pattern is:

- mark the turn as cancellation-requested
- propagate cancellation into the active pipeline context
- let the relevant stage return `StageOutput.cancel(...)` when it observes the
  cancelled state
- rely on Stageflow cancellation propagation for outstanding parallel tasks and
  child subpipelines
- persist the resulting cancelled turn state and trace metadata

Graceful cancellation means:

- no orphaned running turn after the user cancels
- no silent socket close with unknown backend state
- no hidden continuation of child workflows after cancellation is accepted
- persisted cancellation metadata and trace events for replay

This should align with Stageflow-native cancellation behavior, including
pipeline cancellation events and child-run cancellation propagation.

### Child Workflow Rule

If a generation tool invokes an existing Stageflow-backed generation workflow,
run it as a Stageflow subpipeline rather than as an untracked nested service
call.

Use `PipelineContext.fork()` and the Stageflow subpipeline machinery so the
child run preserves:

- same `trace_id`
- explicit parent-child workflow linkage
- `parent_pipeline_run_id`
- `parent_stage_id`
- `assistant_session_id`
- `turn_id`
- `assistant_message_id`
- `tool_call_id`

This is required for LangSmith-style trace trees rather than flat unrelated
records, and it matches the intended Stageflow child-run model.

### Parallel Subpipeline Rule

If one assistant action produces multiple independent child jobs, run those
subpipelines in parallel and fan them in at the parent stage.

Examples:

- generating multiple prompt items
- generating multiple scenario drafts
- running multiple independent read-heavy helper pipelines

Serial subpipeline execution should be treated as the exception, not the
default.

## Prompting Strategy

### Prompt Library

Define a dedicated assistant prompt family in `PromptLibrary`.

Recommended first contract:

- `assistant.chat.v1`

The prompt should describe:

- the assistant's role
- available tools
- tool-use rules
- response style
- hard prohibitions

### Prompt Security

Apply `PromptSecurityPolicy` to:

- user message content
- tool-returned content
- collection free-text fields
- attempt-response excerpts

This is mandatory because the assistant will compose untrusted user and content
data into later model turns.

### Output Contract

The assistant final answer should use a typed output contract that supports:

- `message`
- optional `tool_actions_summary`
- optional `artifacts`
- optional `follow_up_questions`

If the model emits malformed output, fail the turn with a typed validation error
and persist the failure artifact.

### Streaming Response Rule

The final assistant response should stream incrementally to the client as
`response.delta` events and finish with one `response.completed` event that
includes the durable `assistant_message_id`.

The persisted assistant message remains the canonical final artifact. Streamed
deltas are transport events, not the authoritative record.

## Observability And Tracing

### Required Correlation Fields

In addition to the existing platform correlation fields, assistant workflows
must always propagate where applicable:

- `assistant_session_id`
- `turn_id`
- `assistant_message_id`
- `tool_call_id`
- `parent_pipeline_run_id`
- `working_collection_id`

### Required Event Set

Emit at minimum:

- `assistant.session_started.v1`
- `assistant.message_received.v1`
- `assistant.turn_started.v1`
- `assistant.turn_stream_opened.v1`
- `assistant.context_ready.v1`
- `assistant.tool_requested.v1`
- `assistant.tool_started.v1`
- `assistant.tool_completed.v1`
- `assistant.tool_failed.v1`
- `assistant.turn_cancel_requested.v1`
- `assistant.turn_cancelling.v1`
- `assistant.turn_cancelled.v1`
- `assistant.response_delta.v1`
- `assistant.response_completed.v1`
- `assistant.response_persisted.v1`
- `assistant.turn_failed.v1`

Generation child workflows should continue to emit their existing generation
events in the same trace lineage.

### Trace Shape

The target trace hierarchy is:

1. API request
2. assistant turn pipeline run
3. parallel enrich stages
4. parallel transform stages
5. agent stage
6. tool call span
7. child generation subpipeline where applicable
8. provider call span
9. persistence work stages
10. stream projection events
11. cancellation events where applicable

This is the minimum shape required to claim LangSmith- or Langfuse-style
reconstructability.

### What Must Be Queryable

Operators must be able to answer:

- what the user asked
- what context the assistant saw
- what the UI should have seen in stream order
- which tools were called
- which tool call failed
- which generation child run produced a draft
- which model and prompt version produced the final answer
- when the first response token was emitted
- whether and when the turn was cancelled
- how long each step took

If one of these questions cannot be answered from durable artifacts, the slice
is incomplete.

## Metrics

Track at minimum:

- assistant session count
- assistant turns per session
- turn success rate
- tool call success rate by tool
- tool latency p50 and p95
- generation tool invocation rate
- time to first event
- time to first response token
- assistant final-answer latency p50 and p95
- websocket reconnect rate
- dropped stream event rate
- cancellation request rate
- cancel-to-stop latency
- trace completeness rate
- malformed-output validation failure rate
- provider spend and token usage by assistant prompt version

## Storage And Replay Requirements

Persist enough information to replay a turn without maintainer memory:

- turn record and lifecycle timestamps
- user message
- assistant message
- bounded context envelope or reproducible context references
- tool arguments and results
- prompt version
- model slug
- provider
- trace linkage

For MVP, storing a bounded context snapshot on the assistant response message is
acceptable and preferable to lossy reconstruction.

## Backend Module Shape

Recommended new backend slices:

```text
backend/src/soft_skills_backend/modules/assistant/
  domain/
  contracts/
  use_cases/
  workflows/
  infra/
backend/src/soft_skills_backend/entrypoints/http/routes/assistant.py
```

Recommended responsibilities:

- `contracts/`: API and tool schemas
- `domain/`: session, turn, and message invariants
- `use_cases/`: session lifecycle and read APIs
- `workflows/`: Stageflow chat-turn orchestration
- `infra/`: repositories, websocket adapters, cancellation coordination, and event helpers

## Delivery Plan

### Phase 1: Schema And Read Models

Deliver:

- Alembic migration for `assistant_sessions`
- Alembic migration for `assistant_turns`
- Alembic migration for `assistant_messages`
- Alembic migration for `assistant_tool_calls`
- repositories and read models
- session list/get endpoints

Exit criteria:

- sessions, turns, and messages persist durably
- ownership checks are enforced
- a session can be replayed from database records

### Phase 2: Turn Orchestration Baseline

Deliver:

- create-turn endpoint
- WebSocket stream endpoint
- graceful cancellation path
- session and user-context enrichment
- Stageflow pipeline for chat turns
- parallel enrich fan-out/fan-in DAG
- typed assistant output contract
- assistant prompt family in `PromptLibrary`

Exit criteria:

- user message persists before model execution
- the UI receives streamed lifecycle events in order
- cancellation moves a running turn to a durable cancelled state without orphaned work
- assistant response persists on success
- failures persist with stable error codes

### Phase 3: Read Tools

Deliver:

- collection read tools
- attempt-history read tools
- tool-call audit persistence
- tool lifecycle events
- parallel tool execution for independent calls

Exit criteria:

- assistant can answer grounded questions about collections and recent attempts
- tool calls are visible in traces and durable audit rows
- tool lifecycle appears in the UI stream as it happens

### Phase 4: Generation Tools

Deliver:

- generation tools wired to existing catalog generation services
- Stageflow subpipeline linkage between assistant turn and generation runs
- parallel subpipeline execution where semantics allow
- generated artifact summaries returned in assistant responses

Exit criteria:

- assistant can trigger collection and prompt-item generation
- child generation runs are visible under the parent assistant trace
- generation subpipeline progress appears in the turn event stream
- generated drafts preserve existing validation and persistence rules

### Phase 5: Operations And Hardening

Deliver:

- dashboards and query surfaces for assistant metrics
- trace completeness checks
- stream completeness and reconnect checks
- graceful cancellation checks
- failure taxonomy coverage
- real-provider smoke coverage

Exit criteria:

- operators can debug a failed turn end to end
- metrics are queryable by prompt version, model, tool, and status

## Testing Requirements

### Unit

- session, turn, and message invariants
- tool schema validation
- assistant output contract validation
- prompt-security behavior
- stream event projection logic
- cancellation coordinator logic

### Integration

- session create/list/get
- create-turn success path
- create-turn failure path
- websocket reconnect path
- cancellation while a tool is running
- cancellation while a child subpipeline is running
- collection read tool path
- attempt read tool path
- generation tool path with child-run linkage
- parallel tool-call path
- observability artifact persistence

### Smoke

- real-provider assistant turn
- real-provider generation tool invocation through the assistant
- real-provider streamed response path

The first backend implementation has completed these real-provider smoke checks.

## Open Decisions

The implementation can proceed with the defaults above, but these should be
made explicit before Phase 4 finishes:

- whether one assistant serves both creator and learner use cases or whether
  `session_mode` should eventually split into separate prompt families
- whether attempt-history tools should return only the requesting user's data in
  MVP or support admin-to-learner delegated access from day one
- whether partial assistant text should persist as a first-class artifact on
  cancellation or remain transport-only

## Bottom Line

The MVP should add a dedicated assistant module with its own session, turn, and
message models, a Stageflow chat-turn pipeline, WebSocket streaming for UI
updates and cancellation control, aggressive parallelisation wherever
dependencies allow, a narrow read-and-generation tool surface, and first-class
trace linkage into existing generation subpipelines. The assistant must reuse
existing domain services, persist every turn, and produce a full replayable
trace tree rather than a best-effort chat log.
