# Sprint 10: Chat Assistant And Streaming V1

> Project: SoftSkills
> Scope: Backend and platform execution only. Frontend planning is tracked separately.

## Sprint Overview

- Sprint Name: Sprint 10: Chat Assistant And Streaming V1
- Sprint Focus: Deliver a Stageflow-orchestrated assistant runtime with durable sessions and turns, WebSocket streaming, graceful cancellation, read and generation tools, and aggressive parallelisation across the turn workflow
- Depends On: Sprint 5, Sprint 6, Sprint 7, and Sprint 9

## Relevant Source Docs

- [CONSTITUTION.yml](/home/antonioborgerees/df/soft-skills/ops/CONSTITUTION.yml)
- [ops/mvp-spec/README.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/README.md)
- [foundational/technical-architecture.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/technical-architecture.md)
- [foundational/domain-model.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/domain-model.md)
- [foundational/stageflow-guide.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/stageflow-guide.md)
- [platform/assessment-and-progression.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/platform/assessment-and-progression.md)
- [operations/generation.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/operations/generation.md)
- [operations/observability-and-operations.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/operations/observability-and-operations.md)
- [operations/chat-assistant.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/operations/chat-assistant.md)

## Sprint Goals

- Primary Goal: Deliver a backend-usable assistant chat runtime that can stream tool activity and final responses to the UI over WebSocket, support graceful cancellation, and preserve typed contracts, replayable traces, and durable session state.
- Secondary Goals:
  - Introduce dedicated assistant persistence for sessions, turns, messages, and tool-call audit rows.
  - Use Stageflow DAG parallelism aggressively across the turn workflow, not only for enrichments.
  - Use Stageflow subpipelines for generation child workflows so assistant-triggered generation remains traceable and isolated.
  - Reuse existing collection, attempt, progress, and generation services rather than creating loopback HTTP or duplicate business logic.

## Constitution Translation

- Competency growth:
  - The assistant is in scope only insofar as it helps users navigate practice, reflection, past attempts, content selection, and generation without bypassing the existing competency loop.
  - The assistant must not become a side-channel that mutates assessments or progression outside validated flows.
- Schema validation:
  - New request and response boundaries for sessions, turns, WebSocket events, cancellation commands, tool inputs, tool outputs, and persisted assistant artifacts must be typed.
  - LLM outputs used as final assistant responses must validate against an explicit output contract.
- Fail-fast behavior:
  - Invalid session state, malformed tool calls, unauthorized data access, malformed final output, and missing metadata must terminate the turn with stable error codes.
  - Streaming transport and cancellation must surface explicit state transitions rather than hanging or silently stopping.
- Explainability:
  - Tool-backed answers about collections, attempts, and generation must remain grounded in persisted system data.
  - Generation actions initiated by the assistant must preserve the same prompt, model, provider, and artifact metadata as direct generation workflows.
- Observability:
  - Every turn must be replayable from durable artifacts and correlated traces.
  - Operators must be able to reconstruct stream order, tool activity, child workflows, and the final persisted answer.
- Persistence:
  - Sessions, turns, messages, tool calls, and enough context metadata for replay must be stored durably.
  - User messages must persist before orchestration starts.
- Modularity:
  - Routes stay thin.
  - Assistant orchestration lives in a dedicated module.
  - Existing domain services remain the source of truth for collections, attempts, progression, and generation.

## Scope Checklist

- [x] Task 1: Add typed assistant contracts, routes, repositories, and persistence models for sessions, turns, messages, and tool calls
- [x] Task 2: Implement `POST /api/assistant/sessions/{session_id}/turns`, `WS /api/assistant/streams/{stream_token}`, and graceful cancellation
- [x] Task 3: Build a Stageflow chat-turn pipeline with explicit fan-out and fan-in parallelism across all independent stages
- [x] Task 4: Add read-only tools for user collections, collection detail, recent attempts, and attempt detail
- [x] Task 5: Add assistant-triggered generation tools that call existing catalog generation services through Stageflow subpipelines
- [x] Task 6: Persist replayable observability artifacts, stream events, and tool-call audit data with full correlation
- [x] Task 7: Extend unit, integration, and real-provider smoke coverage for assistant turns, streaming, tools, and generation child workflows
- [x] Task 8: Update roadmap, sprint docs, and canonical assistant docs if implementation changes any planned behavior

## Delivered Design Target

### 1. Dedicated Assistant Runtime

- Add a new backend module for assistant behavior rather than forcing assistant semantics into `practice_sessions`.
- Introduce dedicated persistence for:
  - `assistant_sessions`
  - `assistant_turns`
  - `assistant_messages`
  - `assistant_tool_calls`
- Keep route handlers thin and orchestration in Stageflow workflows.

### 2. WebSocket Streaming, Event-Driven UI, And Cancellation

- Use WebSocket for live turn delivery in MVP.
- A turn starts through a normal HTTP request and streams through a separate WebSocket endpoint.
- Stream:
  - turn lifecycle events
  - tool lifecycle events
  - response deltas
  - final completion or failure
- Support client-driven cancellation and durable cancellation state.

### 3. Full-Turn Parallelisation

- Treat Stageflow fan-out and fan-in as a core implementation technique.
- Run all independent enrich stages in parallel.
- Run independent post-read transforms in parallel where dependencies allow.
- Execute multiple independent tool calls from one agent step in parallel.
- Execute independent child generation subpipelines in parallel.
- Run post-commit metrics projection, event projection, and stream fan-out in parallel where transaction boundaries allow.

### 4. Subpipeline-Based Child Workflows

- Assistant-triggered generation must run as Stageflow subpipelines, not hidden nested service calls.
- Child runs must preserve:
  - parent pipeline run linkage
  - parent stage linkage
  - assistant session and turn identifiers
  - tool call identifiers
  - prompt, model, provider, and artifact metadata

### 5. Use Stageflow Pipeline Cancellation Directly

- Graceful cancellation should be implemented on top of Stageflow pipeline
  cancellation support, not a parallel custom stop mechanism.
- Running assistant turns should propagate cancellation through the active
  pipeline and any spawned child subpipelines.
- The sprint should use Stageflow-native cancellation events and cancelled run
  semantics as part of the observability contract.

### 6. Reuse Existing Domain Services

- Collection and attempt tools must read through existing typed services and repositories.
- Generation tools must call the existing catalog generation application surface directly.
- No loopback HTTP calls.
- No duplicated domain validation inside assistant prompts or tool handlers.

## Constitution And Quality Checklist

- [x] Competency growth remains the product outcome rather than generic chat engagement
- [x] All new external boundaries are typed and schema-validated
- [x] Fail-fast and fail-loud behavior is preserved with stable error codes
- [x] Route handlers remain thin; orchestration stays in Stageflow workflows
- [x] Dependency injection and adapter boundaries remain explicit
- [x] Critical workflow artifacts are durably persisted where required
- [x] Traces, logs, events, and stream projections cover all changed workflow steps
- [x] Graceful cancellation propagates through active tool and child-run execution
- [x] Prompt, model, provider, config, and correlation metadata are preserved where applicable
- [x] Existing assessment, progression, and generation invariants are not bypassed
- [x] No silent fallback is introduced in streaming, assistant responses, or tool execution

## Testing And Documentation Checklist

- [x] Unit Tests: session and turn invariants, tool schema validation, stream event projection, cancellation coordination, and assistant output validation
- [x] Integration Tests: API, persistence, orchestration, WebSocket reconnect, cancellation, tool execution, child-run linkage, and observability coverage
- [x] Smoke Tests With Real Provider: assistant final-response generation and assistant-triggered generation tool path
- [x] Failure Path Coverage: schema rejection, auth rejection, malformed final output, tool failure, stream disconnect, cancellation during active work, and child subpipeline failure
- [x] Documentation Updates: sprint docs, roadmap entries, and any canon changes discovered during implementation

## Success Criteria

- [x] The backend supports assistant sessions and turns with durable replayable state
- [x] The UI can receive live WebSocket events for tool activity and final response streaming
- [x] The user can cancel a running turn and the backend shuts it down gracefully
- [x] The turn workflow uses explicit Stageflow parallelism across all independent stages, not only enrichments
- [x] Assistant tools can read user collections and past attempts without bypassing access control or domain services
- [x] Assistant-triggered generation runs through subpipelines and remains fully traced and replayable
- [x] Real-provider smoke coverage exists for the provider-backed assistant surface

Minimum Viable Sprint:
One assistant turn can be created, streamed over WebSocket, cancelled
gracefully while active, call at least one read tool and one generation tool,
persist its artifacts durably, and produce a trace tree that includes parallel
stage execution and child subpipeline linkage.

## Risks And Blockers

| Risk | Impact | Mitigation | Status |
| --- | --- | --- | --- |
| Streaming transport is added but stream events are not durably replayable | High | Treat WebSocket as a projection layer over durable turn, message, tool, and workflow-event artifacts | Closed |
| The turn DAG is implemented mostly sequentially, underusing Stageflow strengths | High | Review every stage for dependency constraints and parallelise by default when no dependency exists | Mitigated |
| Parallel tool or subpipeline execution makes event ordering ambiguous in the UI | Medium | Use monotonic event ids and turn-scoped event sequencing rules | Closed |
| Assistant tools accidentally duplicate business logic or call loopback HTTP | High | Route all tool execution through existing use-case and workflow boundaries | Closed |
| Graceful cancellation leaves active provider work or child subpipelines orphaned | High | Add explicit cancellation propagation and test cancellation while tools and child runs are active | Mitigated |
| WebSocket reconnect behavior becomes fragile under provider latency | Medium | Persist turn state aggressively, add reconnect semantics, and test reconnect paths explicitly | Mitigated |
| Child subpipeline logging may need extra platform helpers to preserve trace lineage cleanly | Medium | Extend the shared Stageflow platform wrapper instead of ad hoc per-feature child-run code | Mitigated |

## Sprint Notes

Key decisions, tradeoffs, and implementation notes:

```text
- This sprint should be executed as a backend and platform vertical slice, not as transport-only scaffolding.
- The assistant is an orchestration surface, not a new domain authority.
- WebSocket is the default MVP transport because cancellation is now a first-class product requirement.
- Parallelisation is a sprint requirement, not an optimization pass.
- The team should inspect every stage in the turn workflow and justify any remaining serialization.
- Generation actions initiated by the assistant should use Stageflow subpipelines so the resulting trace tree remains coherent.
- Graceful cancellation is part of done for this sprint, not a later enhancement.
- The implementation should lean on Stageflow pipeline cancellation and child-run cancellation propagation rather than inventing a separate cancellation model.
- Existing generation, collection, attempt, and progression services remain the source of truth; the assistant only coordinates them.
- The implemented live stream route is token-based: `WS /api/assistant/streams/{stream_token}`.
- The final assistant response now uses provider-native text streaming after the typed tool-planning pass.
- Session listing, message listing, turn lookup, and reconnect replay coverage are now implemented.
- Durable ordered stream events now back live delivery and reconnect replay with monotonic `sequence_number` ordering.
- Real-provider smoke suites were executed from `backend/` so `backend/.env` was loaded correctly.
- `assistant-read-runtime` passed against the live provider.
- `assistant-generation-runtime` passed against the live provider after tightening the smoke prompt to canonical slugs, hardening the assistant prompt to require generation-tool use for generation requests, and increasing the assistant pipeline timeout budget for child generation work.
- The implemented assistant surface now includes session list, session message list, turn lookup, durable event replay, provider-native final-response streaming, and real-provider smoke coverage.
```

## Verification Plan

Targeted verification required before sprint sign-off:

- `python -m py_compile` for the changed assistant, platform, and smoke modules
- `python -m ruff check` for changed backend, tests, and sprint documentation
- targeted unit tests for assistant contracts, orchestration helpers, websocket adapters, cancellation coordination, and event projection
- targeted integration tests for assistant session APIs, turn APIs, WebSocket reconnects, cancellation, tool execution, and child-run linkage
- backend smoke for the new provider-backed assistant path
- backend smoke for assistant-triggered generation path
- migration verification for all new assistant tables

Expected verification concerns:

- mypy may still report repo-wide debt outside the sprint surface
- WebSocket test harnesses may need custom helpers or async fixtures
- child-run tracing may require additions to the current shared Stageflow logging wrapper

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

1. Refine cancellation semantics, retry rules, and richer live-control behavior after the first WebSocket runtime is stable and trace-complete.
2. Evaluate whether the assistant should branch into separate creator and learner prompt families once the first runtime is proven.
3. Add deeper assistant evaluation and quality-governance once the live runtime exists and real traces are available.
