# Backend Technical Architecture

## 1. System Overview

The Soft Skills backend is an AI-driven simulation, assessment, and progression platform built on FastAPI. It uses **Stageflow** as its core workflow orchestration engine to manage complex, multi-stage AI pipelines with built-in observability, idempotency, and cancellation support.

### 1.1 Technology Stack

| Layer | Technology |
|-------|------------|
| Web Framework | FastAPI (ASGI) |
| Workflow Engine | Stageflow (custom pipeline orchestration library) |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic |
| LLM Providers | OpenAI-compatible, Groq, OpenRouter (swappable via `LLMProvider` protocol) |
| Observability | OpenTelemetry, Prometheus, Grafana, Tempo |
| Database | SQLite (dev), PostgreSQL-compatible (prod) |

### 1.2 Entry Point

The application factory lives in `src/soft_skills_backend/app.py`. It creates a FastAPI app with:
- CORS middleware
- Request context middleware (propagates `request_id`, `trace_id`, `workflow_id`)
- OpenTelemetry instrumentation (when enabled)
- Lifespan management for async resource bootstrapping/shutdown

---

## 2. Composition Root

The dependency injection container (`AppContainer` in `platform/container.py`) is built at startup via `build_container()`. It constructs the entire service graph in a single composition root.

### 2.1 Container Components

```
AppContainer
├── settings: Settings
├── engine: Engine (SQLAlchemy)
├── session_factory: sessionmaker[Session]
├── stageflow_runtime: StageflowRuntime
├── background_tasks: BackgroundTaskRunner
│
├── Repositories
│   ├── workflow_events: SqlAlchemyWorkflowEventRepository
│   ├── pipeline_runs: SqlAlchemyPipelineRunRepository
│   ├── provider_calls: SqlAlchemyProviderCallRepository
│   ├── pipeline_definitions: SqlAlchemyPipelineDefinitionRepository
│   ├── stage_definitions: SqlAlchemyStageDefinitionRepository
│   └── pipeline_execution_traces: SqlAlchemyPipelineExecutionTraceRepository
│
├── Services
│   ├── health_service: HealthService
│   ├── identity_service: IdentityService
│   ├── admin_service: AdminService
│   ├── admin_agent_service: AdminAgentService
│   ├── taxonomy_service: TaxonomyService
│   ├── assistant_service: AssistantService
│   ├── catalog_service: CatalogService
│   ├── evaluation_service: EvaluationService
│   ├── practice_service: PracticeService
│   ├── progression_service: ProgressionService
│   ├── events_service: EventsService
│   └── organisation_service: OrganisationService
│
├── Realtime Brokers
│   ├── assistant_broker: AssistantRealtimeBroker
│   └── generation_broker: GenerationRealtimeBroker
│
└── Registries
    ├── prompt_registry: PromptRegistry
    └── auth_provider: HeaderAuthProvider
```

### 2.2 Bootstrap Sequence

1. `build_container()` constructs all infrastructure (engine, session factory, repositories)
2. `build_stageflow_runtime()` initializes the Stageflow runtime with event sinks, loggers, and telemetry
3. LLM providers are instantiated per task kind (default, assistant, admin-agent)
4. `container.bootstrap()` runs post-migration startup:
   - `prompt_registry.sync_builtins()` — syncs built-in prompt templates to the database
   - `taxonomy_service.bootstrap()` — seeds taxonomy data

### 2.3 Shutdown Sequence

1. Event sink is drained and stopped
2. Background task runner is shut down
3. SQLAlchemy engine is disposed

---

## 3. Stageflow Workflow Engine

Stageflow is the central orchestration primitive. Every AI workflow in the system is expressed as a **directed acyclic graph (DAG) of stages** executed by a `Pipeline`.

### 3.1 Core Concepts

| Concept | Description |
|---------|-------------|
| `Pipeline` | A DAG of stages with named dependencies |
| `Stage` | A single unit of work with a declared `StageKind` |
| `StageKind` | Classifies the stage: `GUARD`, `TRANSFORM`, `ENRICH`, `WORK`, `AGENT` |
| `PipelineContext` | Carries correlation IDs, user identity, metadata, and event sink through execution |
| `StageContext` | Per-stage view of the context with access to upstream stage outputs via `ctx.inputs` |
| `StageOutput` | Return type encoding success (`ok`), cancellation (`cancel`), or failure |
| `Interceptor` | Cross-cutting concerns: timeout, circuit breaker, tracing, metrics, logging, idempotency, OpenTelemetry |
| `WideEventEmitter` | Emits namespaced observability events per stage and pipeline |

### 3.2 Stage Kinds

- **`GUARD`** — Validation/precondition checks. May short-circuit with `StageOutput.cancel`.
- **`TRANSFORM`** — Data transformation, prompt building, rendering.
- **`ENRICH`** — Data loading from external sources (profile, history, progress).
- **`WORK`** — Side-effectful operations (persistence, external API calls).
- **`AGENT`** — LLM agent loops with tool execution.

### 3.3 Runtime Architecture

```
StageflowRuntime
├── pipeline_cls: Pipeline
├── pipeline_context_cls: PipelineContext
├── get_default_interceptors: callable
├── event_sink: BackpressureAwareEventSink
├── pipeline_run_logger: DatabasePipelineRunLogger
├── provider_call_logger: DatabaseProviderCallLogger
├── otel_tracer: StageflowTracer
└── otel_interceptor: OpenTelemetryInterceptor (optional)
```

**`BackpressureAwareEventSink`** wraps a `DurableEventSink` (backed by `SqlAlchemyWorkflowEventRepository`) with a configurable queue (`stageflow_event_queue_size`, default 1000) to prevent event emission from blocking pipeline execution.

### 3.4 Interceptor Stack

The default interceptor stack (built by `StageflowPipelineSupport.interceptors()`):

1. **TimeoutInterceptor** — Enforces per-pipeline timeout
2. **CircuitBreakerInterceptor** — Prevents cascading failures
3. **TracingInterceptor** — Distributed tracing
4. **MetricsInterceptor** — Prometheus metrics
5. **LoggingInterceptor** — Structured logging
6. **StageScopedIdempotencyInterceptor** (optional) — Scopes idempotency keys by stage name
7. **OpenTelemetryInterceptor** (optional) — OTel span creation

### 3.5 Pipeline Execution Flow

```
run_logged_pipeline()
├── Generate pipeline_run_id (UUID hex)
├── Create PipelineContext with correlation metadata
├── Log run started (database)
├── pipeline.run() with interceptors
│   ├── Execute stages in topological order
│   ├── Emit wide events per stage
│   └── Handle cancellation/errors
├── Log run completed/failed (database)
└── Return PipelineResults
```

### 3.6 Subpipelines

Pipelines can spawn child pipelines via `run_logged_subpipeline()`:

- Parent context snapshot is forked to the child
- Child gets a fresh `pipeline_run_id` but inherits `request_id`, `trace_id`, `user_id`
- `correlation_id` links parent and child in execution traces
- Child results are returned as `SubpipelineResult` with payload and stage summaries

### 3.7 Idempotency

Two levels of idempotency:

1. **Pipeline-level**: `idempotency_key` + `idempotency_params` in `run_logged_pipeline()`
2. **Stage-scoped**: `StageScopedIdempotencyInterceptor` scopes keys as `{stage_name}:{base_key}` for multi-stage DAGs

### 3.8 Correlation IDs

Every pipeline execution carries:

| ID | Source | Purpose |
|----|--------|---------|
| `request_id` | HTTP request | Correlates all work from a single HTTP request |
| `trace_id` | HTTP request (OTel) | Distributed tracing across services |
| `workflow_id` | Application | Business-level workflow grouping |
| `pipeline_run_id` | Generated (UUID hex) | Unique execution instance |
| `correlation_id` | Generated (UUID) | Links parent/child subpipelines |

---

## 4. AI Workflow: Catalog Generation

The catalog generation system creates assessment collections (prompt items + scenarios) using a **fan-out/fan-in** pattern.

### 4.1 Collection Generation Pipeline

**File**: `modules/catalog/workflows/generation/collection_pipeline.py`

#### DAG Structure

```
input_guard                          (GUARD)
    │
    ▼
blueprint_transform                  (TRANSFORM) — builds prompt request from command
    │
    ▼
blueprint_render                     (TRANSFORM) — renders prompt from registry template
    │
    ▼
blueprint_llm_transform              (TRANSFORM) — LLM call → GeneratedCollectionBlueprint
    │
    ▼
blueprint_guard                      (GUARD) — validates blueprint, enforces skill slugs
    │
    ├────────────────┬────────────────┐
    ▼                ▼                │
prompt_items_work  scenarios_work     │
    (WORK)          (WORK)            │
    │                │                │
    └────────────────┘                │
    │                │                │
    ▼                ▼                │
assemble_transform  (TRANSFORM) ◄─────┘
(fan-in: combines blueprint + prompt items + scenarios)
    │
    ▼
output_guard                         (GUARD) — validates assembled draft
    │
    ▼
persistence_work                     (WORK) — saves to DB, records manifest
```

#### Stage Details

| Stage | Kind | Dependencies | Output |
|-------|------|-------------|--------|
| `input_guard` | GUARD | — | Validated command |
| `blueprint_transform` | TRANSFORM | `input_guard` | `PromptRenderRequest` |
| `blueprint_render` | TRANSFORM | `blueprint_transform` | `RenderedPrompt` |
| `blueprint_llm_transform` | TRANSFORM | `blueprint_render` | `TypedLLMResult[GeneratedCollectionBlueprint]` |
| `blueprint_guard` | GUARD | `blueprint_llm_transform` | Validated blueprint with enforced skill slugs |
| `prompt_items_work` | WORK | `blueprint_guard` | `list[WorkerExecutionResult]` (fan-out) |
| `scenarios_work` | WORK | `blueprint_guard` | `list[WorkerExecutionResult]` (fan-out) |
| `assemble_transform` | TRANSFORM | `blueprint_guard`, `prompt_items_work`, `scenarios_work` | `GeneratedCollectionDraft` |
| `output_guard` | GUARD | `assemble_transform` | Validated draft |
| `persistence_work` | WORK | `output_guard`, `blueprint_guard`, `prompt_items_work`, `scenarios_work` | `CollectionGenerationView` |

#### Execution Parameters

- **Idempotency key**: `catalog_{mode}_generation:{user_id}:{request_id}`
- **Timeout**: Configurable via `timeout_ms`
- **Execution mode**: `catalog_generation`
- **Service namespace**: `soft_skills_backend.catalog`

### 4.2 Fan-Out: Worker Subpipelines

**File**: `modules/catalog/workflows/generation/workers.py`

Both `prompt_items_work` and `scenarios_work` stages fan out to worker subpipelines using `asyncio.gather()` with semaphore-controlled concurrency.

#### Prompt Item Workers

```
run_prompt_item_workers()
├── asyncio.Semaphore(config.max_parallel_prompt_item_children)
└── asyncio.gather(*[run_worker(i, plan) for plan in blueprint.prompt_items])
    └── _run_prompt_item_worker() → Subpipeline: "catalog_prompt_item_worker"
        ├── input_guard (GUARD)
        ├── prompt_request_transform (TRANSFORM) — builds prompt variables
        ├── prompt_render_transform (TRANSFORM) — renders from registry
        ├── llm_transform (TRANSFORM) — LLM call with retry loop
        └── output_guard (GUARD) — validates draft against plan
```

#### Scenario Workers

```
run_scenario_workers()
├── asyncio.Semaphore(config.max_parallel_scenario_children)
└── asyncio.gather(*[run_worker(i, plan) for plan in blueprint.scenarios])
    └── _run_scenario_worker() → Subpipeline: "catalog_scenario_worker"
        ├── input_guard (GUARD)
        ├── prompt_request_transform (TRANSFORM)
        ├── prompt_render_transform (TRANSFORM)
        ├── llm_transform (TRANSFORM) — LLM call with retry loop
        └── output_guard (GUARD) — validates draft against plan
```

#### Worker LLM Retry Loop

Each worker's `llm_transform` stage includes a validation retry loop:

1. Call LLM with structured output schema
2. Parse response into typed model (`GeneratedPromptItemDraft` / `GeneratedScenarioDraft`)
3. Validate against the plan (prompt type, rubric ID, skill slugs, artifact count)
4. On validation failure: append error feedback to messages and retry
5. Max retries: `config.max_validation_retries`
6. Semantic retry feedback format: `{error_code}: {message} Details: {details}. Return corrected JSON only.`

#### Worker Idempotency

Each worker has a unique idempotency key:
- Prompt items: `catalog_prompt_item_worker:{request_id}:{worker_index}`
- Scenarios: `catalog_scenario_worker:{request_id}:{worker_index}`

### 4.3 Fan-In: Assembly

The `assemble_transform` stage performs the fan-in:

```python
draft = GeneratedCollectionDraft(
    prompt_version=blueprint.prompt_version,
    provider=blueprint.provider,
    model_slug=typed_result.model_slug,
    title=blueprint.title,
    summary=blueprint.summary,
    target_audience=command.target_audience,
    difficulty=command.difficulty,
    content_format_mix=list(command.content_format_mix),
    target_skill_slugs=list(command.target_skill_slugs),
    target_competency_slugs=list(command.target_competency_slugs),
    rubric_ids=list(command.rubric_ids),
    prompt_items=[result.typed_result.parsed for result in prompt_item_results],
    scenarios=[result.typed_result.parsed for result in scenario_results],
)
```

### 4.4 Persistence and Manifest

The `persistence_work` stage creates a `GenerationManifest` for full auditability:

```
GenerationManifest
├── planner: PlannerArtifact
│   ├── provider_name
│   ├── pipeline_name: "catalog_{mode}_blueprint"
│   ├── prompt_version
│   ├── correlation_id
│   ├── typed_result (blueprint LLM output)
│   └── child_run_id
├── prompt_items: list[WorkerArtifact]
│   └── Each: provider_name, pipeline_name, prompt_version, worker result
└── scenarios: list[WorkerArtifact]
    └── Each: provider_name, pipeline_name, prompt_version, worker result
```

### 4.5 Progress Tracking

A `progress_callback` reports percentage completion at key stages:

| Stage | Progress |
|-------|----------|
| `input_guard` | 5% |
| `blueprint_guard` | 20% |
| `prompt_items_work` (start) | 35% |
| `prompt_items_work` (end) | 50% |
| `scenarios_work` (start) | 55% |
| `scenarios_work` (end) | 65% |
| `assemble_transform` | 75% |
| `output_guard` | 85% |
| `persistence_work` (start) | 90% |
| `persistence_work` (end) | 100% |

Progress events are streamed via `GenerationRealtimeBroker` over WebSocket.

### 4.6 Cancellation Support

Between expensive stages, the pipeline checks for cancellation:

```python
cancel_output = await _yield_for_cancel()
if cancel_output is not None:
    return cancel_output
```

The `_yield_for_cancel()` function:
1. Checks `execution.is_cancelled` flag
2. Yields briefly (`asyncio.sleep(0.15)`) to let WebSocket deliver cancel signal
3. Returns `StageOutput.cancel` if cancelled

### 4.7 Prompt Item Generation (Existing Collection)

**File**: `modules/catalog/workflows/generation/prompt_item_pipeline.py`

A separate pipeline for adding prompt items to an existing collection:

```
input_guard                          (GUARD) — validates collection ownership
    │
    ▼
plan_transform                       (TRANSFORM) — builds prompt request
    │
    ▼
plan_render                          (TRANSFORM) — renders from registry
    │
    ▼
plan_llm_transform                   (TRANSFORM) — LLM call → GeneratedPromptItemPlanBatch
    │
    ▼
plan_guard                           (GUARD) — validates plan batch
    │
    ▼
prompt_items_work                    (WORK) — fan-out to worker subpipelines
    │
    ▼
output_guard                         (GUARD) — validates uniqueness against existing items
    │
    ▼
persistence_work                     (WORK) — saves items, records manifest
```

---

## 5. AI Workflow: Assistant

The assistant workflow handles conversational turns with tool execution, streaming, and cancellation.

### 5.1 Assistant Turn Pipeline

**File**: `modules/assistant/workflows/service.py`

#### DAG Structure

```
input_guard                          (GUARD) — checks cancellation status
    │
    ├──────────┬──────────┬──────────┬──────────┐
    ▼          ▼          ▼          ▼          ▼
history_enrich profile_enrich progress_enrich attempts_enrich session_state_enrich
  (ENRICH)      (ENRICH)      (ENRICH)       (ENRICH)        (ENRICH)
    │            │            │              │                │
    └────────────┴────────────┴──────────────┴────────────────┘
    │
    ▼
planning_prompt_request              (TRANSFORM) — builds prompt with enriched context
    │
    ▼
planning_prompt_render               (TRANSFORM) — renders from registry
    │
    ▼
assistant_runtime                    (AGENT) — tool execution loop (up to 6 iterations)
    │
    ▼
final_response_prompt_request        (TRANSFORM) — builds final response prompt
    │
    ▼
final_response_prompt_render         (TRANSFORM) — renders from registry
    │
    ▼
final_response_work                  (WORK) — streams final response, persists turn
```

#### Enrichment Stages (Parallel)

All five enrichment stages depend only on `input_guard`, so they execute in parallel:

| Stage | Data Loaded |
|-------|-------------|
| `history_enrich` | Conversation history (limited by `llm_assistant_conversation_history_limit`) |
| `profile_enrich` | User profile |
| `progress_enrich` | Progression dashboard (graceful 404 handling) |
| `attempts_enrich` | Recent practice attempts (via SQL guard, limited by `llm_assistant_recent_attempt_limit`) |
| `session_state_enrich` | Practice session state from session metadata |

### 5.2 Agent Loop (Tool Execution)

The `assistant_runtime` stage runs an iterative tool execution loop:

```
for _ in range(MAX_TOOL_ITERATIONS):  # MAX_TOOL_ITERATIONS = 6
    ├── Check cancellation
    ├── LLM call: complete_with_tools()
    │   ├── If no tool_calls: return final_response
    │   └── If tool_calls: parse and execute
    ├── Parse tool requests
    ├── Execute tools: tools.execute_many()
    ├── Append tool results to messages (with security hardening)
    └── Check cancellation
```

#### Tool Execution

**File**: `modules/assistant/workflows/tools.py`

Tools are executed via `AssistantToolExecutor.execute_many()` using `asyncio.gather()`:

1. Each tool call is persisted to the database
2. If the tool requires human approval:
   - An approval request is sent via the realtime broker
   - The pipeline waits for approval (with timeout: `tool_approval_timeout_seconds`)
   - Auto-allowed tools bypass approval (`tool_approval_auto_allow` setting)
3. Tool results are security-hardened via `PromptSecurityPolicy.build_tool_message()`

#### Available Tools

The assistant has access to tools for:
- Querying user context (SQL with guard)
- Managing practice sessions
- Starting collection practice
- Catalog operations
- Progression queries

### 5.3 Final Response Generation

After the agent loop completes, the `final_response_work` stage:

1. Checks if response rewriting is needed (`_should_rewrite_final_response`)
2. If rewriting: calls LLM to generate a polished final response
3. If not: uses the draft response directly
4. Streams the response to the client via `AssistantRealtimeBroker`
5. Marks the turn as completed in the database

### 5.4 Realtime Communication

**AssistantRealtimeBroker** manages WebSocket streaming:

- `ActiveTurnExecution` tracks each running turn with its pipeline context and task reference
- Stream events are published to the client via `broker.publish()`
- Cancellation is propagated via `active.request_cancel()` and task cancellation

---

## 6. AI Workflow: Evaluation

**File**: `modules/evaluation/workflows/service.py`

The evaluation pipeline runs benchmark suites against the marking engine:

```
input_guard                          (GUARD) — prepares evaluation request
    │
    ▼
transform                            (TRANSFORM) — runs MarkingBenchmarkRunner
    │
    ▼
work                                 (WORK) — persists evaluation results
```

- **Idempotency key**: `evaluation:{suite_id}:{model_slugs}:{case_ids}:{request_id}`
- **Timeout**: 240,000ms (4 minutes)
- **Execution mode**: `evaluation_runtime`

---

## 7. LLM Provider Abstraction

### 7.1 Protocol

**File**: `shared/ports/llm.py`

```python
class LLMProvider(Protocol):
    @property
    def provider_name(self) -> str: ...
    @property
    def model_slug(self) -> str: ...

    async def complete_json(
        messages: list[dict[str, object]],
        response_schema: JsonSchemaResponseFormat | None = None,
        timeout_seconds: float | None = None,
    ) -> ProviderCompletion: ...

    async def complete_with_tools(
        messages: list[dict[str, object]],
        tools: list[ProviderToolDefinition],
        tool_choice: str | None = None,
        timeout_seconds: float | None = None,
    ) -> ProviderToolCompletion: ...

    def stream_text(
        messages: list[dict[str, object]],
    ) -> AsyncIterator[ProviderTextChunk]: ...
```

### 7.2 Implementations

| Provider | File |
|----------|------|
| OpenAI-compatible | `platform/providers/llm/openai_compatible.py` |
| Groq | `platform/providers/llm/groq.py` |
| OpenRouter | `platform/providers/llm/openrouter.py` |

### 7.3 Provider Selection

LLM providers are instantiated per task kind via `build_llm_provider()`:

| Task Kind | Purpose |
|-----------|---------|
| Default | General operations (catalog generation, evaluation) |
| `LLMTaskKind.ASSISTANT` | Assistant conversational turns |
| `LLMTaskKind.ADMIN_AGENT` | Admin agent SQL operations |

### 7.4 Telemetry

Every LLM call is logged via `ProviderCallContext` which carries:
- `operation` — Semantic operation name
- `request_id`, `trace_id`, `pipeline_run_id`, `workflow_id`, `user_id` — Correlation IDs

The `DatabaseProviderCallLogger` persists all provider calls to the database.

---

## 8. Prompt Registry

**File**: `modules/admin/domain/prompt_registry.py`

The prompt registry manages versioned prompt templates:

- Prompts are stored in the database with name, version, and content
- Built-in prompts are synced at startup via `sync_builtins()`
- `PromptRenderRequest` specifies prompt name, version, and template variables
- `create_prompt_render_stage()` creates a Stageflow stage that resolves and renders a prompt

### 8.1 Prompt Rendering Stage

**File**: `modules/admin/workflows/prompt_render_stage.py`

The prompt render stage is a reusable TRANSFORM stage that:
1. Reads a `PromptRenderRequest` from an upstream stage's output
2. Resolves the prompt template from the registry
3. Renders the template with the provided variables
4. Returns a `RenderedPrompt` with the final prompt content

---

## 9. Observability

### 9.1 Wide Events

Every stage emits wide events via `AgentWideEventEmitter`:

- Event types are namespaced: `{prefix}.{stage_name}` (e.g., `stage.wide.input_guard`, `pipeline.wide.assistant_turn_runtime`)
- Events include stage payload, summary, and correlation metadata
- Persisted via `DurableEventSink` → `SqlAlchemyWorkflowEventRepository`

### 9.2 Pipeline Run Logging

`DatabasePipelineRunLogger` records:

- Run started (pipeline name, topology, execution mode, user, request, trace)
- Run completed (duration, status, stage summaries)
- Run failed (error, stage name, request, trace)

### 9.3 OpenTelemetry

When `otel_enabled` is true:

- FastAPI app is instrumented via `FastAPIInstrumentor`
- HTTPX client is instrumented via `HTTPXClientInstrumentor`
- `OpenTelemetryInterceptor` creates spans for each stage execution
- `StageflowTracer` wraps the OTel tracer for pipeline-level spans

### 9.4 Circuit Breaker

The `CircuitBreakerInterceptor` (part of Stageflow's default interceptors) prevents cascading failures by:
- Tracking failure rates per circuit
- Opening the circuit when failure threshold is exceeded
- Allowing periodic half-open probes

---

## 10. API Surface

**File**: `entrypoints/http/router.py`

| Prefix | Module | Purpose |
|--------|--------|---------|
| `/health` | health | Health checks |
| `/auth` | auth | Authentication |
| `/admin` | admin | Administration |
| `/admin-agent` | admin_agent | Admin AI agent |
| `/admin/evaluations` | evaluations | Evaluation runs |
| `/events` | events | Workflow events |
| `/assistant` | assistant | Conversational assistant |
| `/users` | users | User management |
| `/skills` | skills | Skill taxonomy |
| `/` (root) | generation | Catalog generation |
| `/collections` | collections | Collection management |
| `/attempts` | attempts | Practice attempts |
| `/practice-runs` | practice_runs | Practice sessions |
| `/progress` | progress | Progression data |
| `/providers` | providers | LLM provider management |
| `/organisations` | organisations | Organisation management |
| `/voice` | voice | Voice transcription |

---

## 11. Module Architecture

The codebase follows a **modular monolith** pattern with clear domain boundaries:

```
modules/
├── admin/          — Prompt management, analytics, rubric administration
├── admin_agent/    — AI-powered admin agent with SQL execution
├── assistant/      — Conversational assistant with tool execution
├── catalog/        — Assessment collection generation and management
├── evaluation/     — Benchmark evaluation suites
├── events/         — Workflow event querying
├── identity/       — User identity management
├── organisations/  — Multi-tenancy support
├── practice/       — Practice session execution and assessment
├── progression/    — Skill progression tracking
├── taxonomy/       — Skill and competency taxonomy
└── voice/          — Voice transcription
```

Each module follows a consistent internal structure:

```
module/
├── contracts/      — Commands (input DTOs) and views (output DTOs)
├── domain/         — Business logic, models, validators
├── infra/          — Repository implementations, SQL executors
├── use_cases/      — Application services
└── workflows/      — Stageflow pipeline orchestration
```

---

## 12. Security Model

### 12.1 Authentication

- `HeaderAuthProvider` extracts user identity from HTTP headers
- `Actor` carries `user_id` and `organisation_id` through the request lifecycle
- Auth events are recorded via `WorkflowEventRepository`

### 12.2 Prompt Security

`PromptSecurityPolicy` enforces:
- Maximum user message length: 12,000 characters
- Maximum tool output length: 12,000 characters
- Content sanitization via `build_user_message()` and `build_tool_message()`
- `PromptSecurityError` is raised on policy violations

### 12.3 SQL Guard

Both the assistant and admin agent have SQL guards (`AssistantSqlGuard`, `AdminAgentSqlGuard`):
- Validate SQL queries against a schema registry
- Enforce row limits (`admin_agent_query_row_limit`)
- Scope queries to the user's organisation
- Results are redacted via `ResultRedactor` implementations

### 12.4 Approval Workflow

Certain assistant tool calls require human approval:
- Configurable auto-allow list (`tool_approval_auto_allow`)
- Timeout-based approval waiting (`tool_approval_timeout_seconds`)
- Approval requests are streamed to the client in real-time

---

## 13. Configuration

**File**: `config.py`

Key configuration categories:

| Category | Key Settings |
|----------|-------------|
| LLM | `llm_provider`, `llm_model`, `llm_api_key`, `llm_base_url` |
| Assistant | `llm_assistant_timeout_seconds`, `llm_assistant_conversation_history_limit`, `llm_assistant_recent_attempt_limit` |
| Generation | `creator_generation_validation_retries`, `max_parallel_prompt_item_children`, `max_parallel_scenario_children` |
| Stageflow | `stageflow_event_queue_size` |
| Observability | `otel_enabled`, `otel_service_name`, `otel_exporter_otlp_endpoint` |
| Security | `tool_approval_timeout_seconds`, `tool_approval_auto_allow`, `admin_agent_query_row_limit`, `admin_agent_query_timeout_seconds` |
| Database | `database_url` |
| Application | `app_name`, `app_version`, `environment`, `api_prefix`, `cors_allowed_origins` |

---

## 14. Error Handling

### 14.1 Error Codes

Errors use a structured code format:

| Prefix | Domain |
|--------|--------|
| `SS-ORCHESTRATION-xxx` | Pipeline orchestration failures |
| `SS-VALIDATION-xxx` | Validation failures |

### 14.2 Error Propagation

- `AppError` is the base application error with `code`, `message`, `details`, and `status_code`
- `orchestration_error()` — For pipeline-level failures
- `validation_error()` — For input/data validation failures
- Pipeline errors are caught, logged, and translated to appropriate HTTP responses via error handlers

### 14.3 Pipeline Error Handling

`run_logged_pipeline()` handles:
- `UnifiedPipelineCancelled` — Logged as "cancelled", results returned
- `UnifiedStageExecutionError` — Original exception re-raised after logging
- Generic `Exception` — Wrapped in `orchestration_error("SS-ORCHESTRATION-005")`
