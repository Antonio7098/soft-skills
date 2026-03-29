# Admin Dashboard MVP - Backend Readiness Assessment

## Feature Gap Analysis

### 1. Event Logging (Comprehensive)

**Current State:**
- `WorkflowEventRecord`, `PipelineRunRecord`, `ProviderCallRecord` stored in DB
- Structured JSON logging via structlog to stdout
- Events API endpoint at `/events`
- Existing event types: identity, catalog, practice, progression, evaluation, assistant, taxonomy
- `AssistantStreamEventRecord` for assistant stream events (turns, tools, responses)

**Event Architecture:**
| Record Model | Purpose | Key Fields |
|-------------|---------|------------|
| `WorkflowEventRecord` | Generic domain events | event_type, request_id, trace_id, workflow_id, payload, error_code |
| `PipelineRunRecord` | Pipeline execution | pipeline_name, status, stage_results, started_at, finished_at |
| `ProviderCallRecord` | LLM provider calls | operation, provider, model_id, latency_ms, success, metrics |
| `EvaluationSuiteRecord` | Eval suite definitions | suite_type, version, definition_payload |
| `EvaluationRunRecord` | Eval execution | status, passed, aggregate_metrics, learner_id |
| `EvaluationCaseResultRecord` | Per-case results | case_id, status, metrics, detail_payload |
| `AssistantStreamEventRecord` | Assistant turn events | event_type, sequence_number, payload |
| `AssistantSessionRecord` | Assistant sessions | user_id, status, title |
| `AssistantMessageRecord` | Assistant messages | role, content, metadata_payload |
| `AssistantToolCallRecord` | Tool executions | tool_name, status, args_payload, result_payload |

**Verified Event Coverage (Already Hooked to DB):**
- `identity.user_registered.v1`, `identity.profile_updated.v1`
- `catalog.collection.created.v1`, `catalog.collection.updated.v1`, `catalog.collection.lifecycle_changed.v1`, `catalog.collection.verification_changed.v1`
- `practice.session_started.v1`, `practice.prompt_delivered.v1`, `practice.run_started.v1`, `practice.attempt_submitted.v1`
- `assessment.validated.v1`, `assessment.rejected.v1`, `workflow.failed.v1`
- `progression.snapshot.created.v1`, `progression.recalculation.started.v1`, `progression.recalculation.completed.v1`, `recommendation.generated.v1`
- `evaluation.run.started.v1`, `evaluation.run.completed.v1`, `evaluation.run.failed.v1`
- `assistant.session.created.v1`, `assistant.turn.created.v1`
- `taxonomy.catalog_seeded.v1`
- `tool.started`, `tool.completed`, `tool.failed` (via `AssistantStreamEventRecord`)
- `turn.started`, `turn.completed`, `turn.failed`, `turn.cancelled`, `turn.cancelling` (via `AssistantStreamEventRecord`)

**What to Add/Improve:**
| Task | Effort | Description |
|------|--------|-------------|
| Response delta aggregation | Medium | Aggregate `response.delta` events into single `response.completed` record with full content, token counts, latency; emit deltas only to realtime broker |
| HTTP request audit logging | Medium | Add `http.request.received.v1` and `http.request.completed.v1` events with method, path, query params, user agent, IP, response status, latency; field-level PII scrubbing |
| Auth event logging | Medium | Add `auth.login.success.v1`, `auth.login.failed.v1`, `auth.token_refresh.v1`, `auth.access_denied.v1` |
| Typed error events | Low | Replace generic `workflow.failed.v1` with typed events: `error.validation.v1`, `error.authentication.v1`, `error.authorization.v1`, `error.not_found.v1`, `error.rate_limited.v1` |
| Admin action audit trail | Medium | Add `admin.user.suspended.v1`, `admin.user.role_changed.v1`, `admin.cohort.created.v1`, `admin.cohort.updated.v1` |
| Catalog generation events | Low | Verify and wire `catalog.generation.started.v1`, `catalog.generation.completed.v1`, `catalog.generation.failed.v1` |
| Provider call enrichment | Medium | Add token counts (prompt/completion), model version, finish reason to `ProviderCallRecord.metrics` |
| Prompt render events | Low | Add `prompt.rendered.v1` tracking prompt ID, version, template name, latency |
| Session/realtime events | Low | Add `session.connected.v1`, `session.disconnected.v1` for WebSocket/SSE connections |
| Collection save/rating events | Low | Verify `catalog.collection.saved.v1`, `catalog.collection.unsaved.v1`, `catalog.collection.rated.v1`, `catalog.collection.unrated.v1` are persisted |
| Log aggregation infrastructure | High | Add Loki or Elasticsearch for structlog stdout aggregation (docker-compose) |
| Log search API | Medium | New `/admin/logs` endpoint with filtering (level, timeframe, correlation ID, user ID) |
| Log retention policy | Low | Add cleanup job for old log entries (same retention for all event types) |
| Log viewer endpoint | Medium | Paginated, filterable log retrieval with export option |

---

### 2. Monitoring/Telemetry

**Current State:**
- Request context middleware with correlation IDs
- Database-based pipeline/provider call logging
- Basic health endpoints (`/health`)
- Stageflow interceptors active: Timeout, CircuitBreaker, Tracing, Metrics, Logging
- `BackpressureAwareEventSink` wrapping `DurableEventSink` for event persistence
- `WideEventEmitter` initialized but not emitting to DB

**Stageflow Event Architecture:**
| Stageflow Component | Current Usage | Destination |
|--------------------|---------------|-------------|
| `BackpressureAwareEventSink` | ✅ Wired | `DurableEventSink` → `WorkflowEventRecord` |
| `DatabasePipelineRunLogger` | ✅ Wired | `PipelineRunRecord` |
| `DatabaseProviderCallLogger` | ✅ Wired | `ProviderCallRecord` |
| `WideEventEmitter` | Initialized | Not persisting (in-memory only) |
| `TracingInterceptor` | Active | In-memory context only |
| `MetricsInterceptor` | Active | In-memory context only |
| `CircuitBreakerInterceptor` | Active | In-memory only |

**Stageflow Event Types Flowing to DB:**
- `stage.{name}.started`, `stage.{name}.completed`, `stage.{name}.failed`
- `pipeline.started`, `pipeline.completed`, `pipeline.failed`, `pipeline.cancelled`

**Design Decision: OpenTelemetry Directly**
- Skip Prometheus; go straight to OpenTelemetry for unified traces + metrics
- OTLP exporter sends to backend (Tempo, Jaeger, Prometheus + Grafana)
- Visibility first; alerting deferred

**OpenTelemetry Integration:**
| Component | Implementation | Effort |
|-----------|---------------|--------|
| `StageflowTracer` | Wire to existing interceptors via `StageflowTracer` | Medium |
| Span context propagation | `ctx.data["_otel_span.{stage}"]` via `TracingInterceptor` | Low |
| OTLP exporter | Configure `OTEL_EXPORTER_OTLP_ENDPOINT` | Low |
| Service name | `soft-skills-backend` | Low |
| Span attributes | `pipeline.name`, `stage.name`, `pipeline.run_id`, `user_id` | Low |

**Scope: LLM-Involving Pipelines Only**
All telemetry focused on pipelines/stages that call LLM providers:
- Assistant turn pipeline (all 6 stages)
- Catalog generation pipelines (blueprint, prompt_item, scenario)
- Assessment/practice pipelines (marking stage)
- Evaluation pipelines

**Metrics Retention:**
- Hot storage (Tempo/Jaeger): 30 days for traces
- Aggregated metrics (Prometheus): 90 days
- Pipeline run summaries in DB: 1 year

**What to Add:**
| Task | Effort | Description |
|------|--------|-------------|
| OpenTelemetry integration | High | `opentelemetry-sdk`, `opentelemetry-exporter-otlp`, wire `StageflowTracer` to interceptors |
| OTLP endpoint configuration | Low | Environment variable `OTEL_EXPORTER_OTLP_ENDPOINT` |
| Span attributes enrichment | Low | Add `pipeline.name`, `stage.name`, `pipeline.run_id`, `user_id`, `provider`, `model` to spans |
| Trace context propagation | Medium | Ensure trace context flows through async boundaries and HTTP headers |
| Tempo/Jaeger/Grafana stack | High | Docker-compose with OpenTelemetry backend |
| Distributed tracing UI | Medium | Connect admin dashboard to Jaeger/Tempo for trace visualization |
| Health dashboard endpoint | Low | Extended `/health` with component status (DB, external services) |
| LLM span attributes | Low | Add `llm.operation`, `llm.provider`, `llm.model`, `llm.tokens` to spans |

---

### 2b. Agent Observability (Stageflow-Powered)

**Assistant Pipeline Stages:**
- `input_guard` (GUARD) - Turn status check, cancellation handling
- `history_enrich` (ENRICH) - Conversation history loading
- `profile_enrich` (ENRICH) - Learner profile loading
- `progress_enrich` (ENRICH) - Progression dashboard loading
- `attempts_enrich` (ENRICH) - Recent attempts loading
- `assistant_runtime` (AGENT) - Main LLM orchestrator with tool execution

**Agent Event Flow:**
```
turn.started → stage.input_guard.started → ... → stage.assistant_runtime.completed → turn.completed
                                                              ↓
                                                    tool.started → tool.completed
                                                              ↓
                                                    response.delta × N → response.completed
```

**What to Add:**
| Task | Effort | Description |
|------|--------|-------------|
| Wide events persistence | Low | Persist `stage.wide.*` and `pipeline.wide.*` events to `workflow_events` with event_type prefix (e.g., `stage.wide.input_guard`, `pipeline.wide.assistant_turn_runtime`) |
| Tool events via Stageflow | Medium | Emit `tool.invoked` via `ctx.emit_event()` before dispatch; already emits `tool.started/completed/failed` via broker |
| Streaming buffer aggregation | Medium | Aggregate `stream.chunk_dropped`, `stream.throttle_count` into turn metadata (not separate records) |
| Circuit breaker persistence | High | Implement `CircuitBreaker` backed by `CircuitBreakerRecord` for multi-worker deployments |
| Structured error summarization | Low | Use `summarize_pipeline_error()` in `DatabasePipelineRunLogger.log_run_failed()` for structured error docs |
| Response delta aggregation | Medium | Collect chunks in memory, emit single `response.completed` with full content + aggregated metrics; emit deltas only to realtime broker |

---

### 2c. Pipeline Visualization (Admin Dashboard)

**Stageflow Provides:**
| Stageflow Type | Fields | Usage |
|----------------|--------|-------|
| `StageKind` | `TRANSFORM`, `ENRICH`, `ROUTE`, `GUARD`, `WORK`, `AGENT` | Node color/style in diagram |
| `StageStatus` | `OK`, `SKIP`, `CANCEL`, `FAIL`, `RETRY` | Node status in execution trace |
| `Pipeline.stages` | `{name: UnifiedStageSpec}` | Stage names, runner class, kind, dependencies |
| `PipelineRunRecord.stage_results` | `{stage_name: {kind, ...summary}}` | Per-stage execution results |
| `pipeline.wide` event | Topology, execution_mode, duration_ms, stage_summaries | End-to-end pipeline metrics |

**Pipeline Definition Storage (at startup):**
```python
class PipelineDefinitionRecord(Base):
    """Static pipeline DAG definition."""
    pipeline_name: str  # Primary key
    topology: str  # e.g., "assistant_turn", "catalog_generation"
    stage_definitions: JSON  # [{name, kind, dependencies, runner_class}]
    created_at: datetime
    updated_at: datetime

class StageDefinitionRecord(Base):
    """Individual stage metadata."""
    pipeline_name: str
    stage_name: str
    stage_kind: str  # GUARD, TRANSFORM, ENRICH, etc.
    dependencies: list[str]
    description: str
```

**Pipeline Execution Trace Storage:**
```python
class PipelineExecutionTraceRecord(Base):
    """Actual pipeline execution for visualization replay."""
    pipeline_run_id: str  # Links to PipelineRunRecord
    pipeline_name: str
    execution_sequence: JSON  # Ordered list of stage events with timestamps
    # [{stage_name, event_type, timestamp, duration_ms, status, error}]
    total_duration_ms: int
    started_at: datetime
    completed_at: datetime
```

**Admin API Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/pipelines` | List all pipeline definitions |
| GET | `/admin/pipelines/{name}` | Get pipeline DAG (stages, dependencies, kinds) |
| GET | `/admin/pipelines/{name}/runs` | List recent runs of a pipeline |
| GET | `/admin/pipelines/{name}/runs/{run_id}/trace` | Get execution trace for visualization |
| GET | `/admin/pipelines/{name}/metrics` | Aggregate stage metrics (latency p50/p95/p99, success rate) |

**Visualization Types:**
| View | Description |
|------|-------------|
| **Pipeline DAG View** | Static graph showing stages, dependencies, kinds (color-coded by StageKind) |
| **Execution Trace View** | Animated sequential replay of actual execution with timing |
| **Stage Metrics View** | Per-stage latency histograms, success/failure rates |
| **Flame Chart View** | Hierarchical timing breakdown of pipeline stages |

**Pipeline Discovery (at startup):**
```python
def discover_pipelines(stageflow_runtime: StageflowRuntime) -> list[PipelineDefinition]:
    """Discover all registered pipelines and extract DAG definitions."""
    pipelines = []
    for pipeline_name, pipeline in stageflow_runtime.pipeline_registry.items():
        stages = []
        for stage_name, spec in pipeline.stages.items():
            stages.append({
                "name": stage_name,
                "kind": spec.kind.name,
                "dependencies": spec.dependencies or [],
                "runner_class": spec.runner.__class__.__name__,
            })
        pipelines.append(PipelineDefinition(name=pipeline_name, stages=stages))
    return pipelines
```

---

### 3. Eval

**Current State:**
- `EvaluationSuiteRecord`, `EvaluationRunRecord`, `EvaluationCaseResultRecord`
- Endpoints at `/admin/evaluations/suites` and `/admin/evaluations/runs`
- `EvaluationService`, `MarkingBenchmarkRunner`
- **Sprint 13e**: Added dashboard APIs for aggregated views, historical comparison, benchmarking, and case drill-down

**Implemented in Sprint 13e:**
| Task | Endpoint | Description |
|------|----------|-------------|
| Evaluation result dashboard view | `GET /admin/evaluations/dashboard` | Aggregate pass/fail rates, latency percentiles, error breakdown |
| Historical comparison | `GET /admin/evaluations/runs/compare` | Compare evaluation runs over time |
| Benchmarking dashboard | `GET /admin/evaluations/benchmark` | Track provider model performance |
| Evaluation case drill-down | `GET /admin/evaluations/cases/{case_id}` | Individual case result inspection |

**What to Add:**
| Task | Effort | Description |
|------|--------|-------------|
| Ad-hoc evaluation trigger UI API | Medium | `POST /admin/evaluations/runs` already exists, need workflow to trigger |

---

### 4. Prompt Library (Stageflow-Powered)

**Current State:**
- `PromptLibrary` class with `register()`, `render()` in `engines/marking/use_cases/structured_output.py`
- Prompt templates in `platform/providers/llm/prompts.py`
- Static string registration at startup via `build_*_prompt_library()` functions
- No database persistence, no admin UI, no runtime modification

**Stageflow Patterns Applied:**
| Stageflow Pattern | Application to Prompts |
|-------------------|----------------------|
| `PipelineRegistry` pattern | Create `PromptRegistry` for managing prompt versions by name |
| Stage `summary` dict | Track prompt render metrics (latency, token count, success rate) |
| Subpipeline lineage | Track prompt version → generation artifact lineage |
| `stage.wide` events | Per-prompt-version performance metrics |

**Prompt Types (Explicit):**
| Type | Description | Example Prompts |
|------|-------------|----------------|
| `assessment` | Learner response evaluation | `quick-practice-assessment` |
| `generation` | Content generation | `creator-collection-blueprint`, `creator-prompt-items-plan` |
| `chat` | Chat-based generation | `creator-chat-draft` |
| `worker` | Parallel item generation | `creator-prompt-item-worker`, `creator-scenario-worker` |

**Database Models:**
| Record Model | Purpose | Key Fields |
|-------------|---------|------------|
| `PromptVersionRecord` | Versioned prompt template | name, version, prompt_type, template, variables_schema, output_schema, status, parent_version_id |
| `PromptRenderMetricsRecord` | Aggregated render metrics | prompt_version_id, render_count, success_count, avg_latency_ms, total_tokens |
| `PromptRenderEventRecord` | Individual render events | prompt_version_id, success, latency_ms, tokens, error_code, trace_id |

**Lifecycle:**
```
draft → published → archived
         ↑
    parent_version_id (for A/B variants)
```

**Admin API Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/prompts` | List all prompt names with latest version |
| GET | `/admin/prompts/{name}/versions` | List all versions of a prompt |
| GET | `/admin/prompts/{name}/versions/{version}` | Get specific version |
| POST | `/admin/prompts` | Create new prompt version (draft) |
| PUT | `/admin/prompts/{name}/versions/{version}` | Update draft version |
| POST | `/admin/prompts/{name}/versions/{version}/publish` | Publish to production |
| POST | `/admin/prompts/{name}/versions/{version}/archive` | Archive version |
| GET | `/admin/prompts/{name}/analytics` | Get performance metrics per version |
| POST | `/admin/prompts/compare` | Compare two versions (A/B) |

**Stageflow Integration:**
- `PromptRenderStage` (StageKind.TRANSFORM) - Renders prompts and tracks metrics via `stage.summary`
- `prompt_registry` - In-memory registry (migrated from static registration) following stageflow's registry pattern
- Prompt validation subpipeline - Syntax check → Variable check → Output format check
- Lineage tracking via `parent_version_id` linking to `PipelineRunRecord.stage_results`

**Design Decisions:**
- Built-in prompts remain static strings in `prompts.py` (registered at startup)
- User-created prompts persisted to DB via admin API
- Explicit `variables_schema` (JSON Schema) required for all prompts
- Explicit `output_schema` required for prompts expecting structured JSON output
- `parent_version_id` supports simple A/B testing (no percentage-based routing)

---

### 5. User Management

**Current State:**
- `UserAccountRecord`, `LearnerProfileRecord`
- `POST /auth/register`, `GET/PUT /users/{id}`
- `AdminLearnerRelationshipRecord` for admin-learner relationships

**What to Add:**
| Task | Effort | Description |
|------|--------|-------------|
| Admin user listing | Medium | `GET /admin/users` with pagination, search, filter by role/status |
| User deactivation/suspension | Low | `DELETE /admin/users/{id}` or status toggle |
| Role management | Low | `PUT /admin/users/{id}/role` to promote to admin |
| Bulk user operations | Medium | `POST /admin/users/bulk` for bulk role changes, exports |
| User activity view | Medium | Recent attempts, sessions, logins per user |

---

### 6. User/Cohort Analytics

**Current State:**
- `LearnerAnalyticsView`, `CohortAnalyticsView`
- Usage trends, skill clusters, skill averages, provider usage summary
- `AdminAnalyticsRepository` with `get_learner_analytics()`, `get_cohort_analytics()`

**What to Add:**
| Task | Effort | Description |
|------|--------|-------------|
| Analytics dashboard API | Medium | `GET /admin/analytics/overview` aggregated view |
| Time-range selection | Low | Add `from`/`to` params to existing queries |
| Export functionality | Medium | CSV/JSON export of analytics data |
| Cohort comparison | Medium | Side-by-side cohort performance |
| Drill-down to attempts | Low | Link analytics to individual attempt details |

---

### 7. Policy Layer

**Current State:**
- `ReleaseGateDecisionRecord` (evaluation gates only)
- `AdminCollectionVerificationCommand` for content verification
- No dedicated policy module

**What to Add:**
| Task | Effort | Description |
|------|--------|-------------|
| Policy data model | Medium | `PolicyRecord`, `PolicyVersionRecord`, `PolicyAuditRecord` |
| Policy definition API | Medium | CRUD endpoints `/admin/policies` |
| Policy rule engine | High | Evaluate policies against requests/actions |
| Policy conditions | High | Define conditions (user role, cohort, time, etc.) |
| Policy versioning | Medium | Track policy changes with audit trail |
| Policy enforcement middleware | High | Apply policies at API gateway level |

---

## Error Taxonomy (CL-006 Compliant)

**Existing Backend Error Infrastructure:**
- `AppError` class in `shared/errors.py` with `code`, `category`, `message`, `status_code`, `details`
- `ErrorCategory` StrEnum: VALIDATION, DOMAIN, SCORING, ORCHESTRATION, PROVIDER, PERSISTENCE, AUTH, UI
- Error code format: `SS-{CATEGORY}-{NUMBER}` (e.g., `SS-VALIDATION-017`, `SS-ORCHESTRATION-005`)
- Factory functions: `validation_error()`, `domain_error()`, `provider_error()`, etc.
- `StructuredOutputRejectionError` for LLM validation failures (wraps AppError + raw_payload)

**Error Categories and Ranges:**
| Category | Range | Default Status | Purpose |
|----------|-------|---------------|---------|
| VALIDATION | 001-077 | 422 | Request/input validation, schema mismatch |
| DOMAIN | 001-027 | 400 | Business domain rule violations |
| SCORING | 001-018 | 422 | Assessment/scoring errors |
| PROVIDER | 001-099 | 503 | LLM provider errors, smoke tests |
| ORCHESTRATION | 001-006 | 500 | Pipeline/workflow execution failures |
| AUTH | 001-008 | 401 | Authentication/authorization errors |
| PERSISTENCE | 001+ | 503 | Database/repository errors |

**StructuredOutputRejectionError:**
```python
@dataclass(slots=True)
class StructuredOutputRejectionError(Exception):
    app_error: AppError      # The error to report
    raw_payload: dict[str, Any]  # The invalid payload that caused rejection
```
**Enforcement**: Validation failure is a **hard stop** - `StructuredOutputRejectionError` must be raised, not silently logged or best-effort continued.

---

## Event Logging Design Decisions

- **Response deltas**: Aggregate into single `response.completed` record with full content + token counts + latency; emit deltas only to realtime broker (not DB)
- **PII handling**: Field-level scrubbing (not full redaction); sensitive fields identified and masked per event type
- **Retention**: Same retention policy for all event types (no tiered retention)
- **Token counting**: Track prompt/completion/total token counts for ALL LLM provider operations in `ProviderCallRecord.metrics`
- **Wide events storage**: Store in existing `workflow_events` table with event_type prefix (e.g., `stage.wide.input_guard`, `pipeline.wide.assistant_turn_runtime`)
- **Streaming metrics**: Aggregate into turn metadata (total_chunks, dropped_chunks, throttle_count), not separate records
- **Circuit breaker state**: Persisted to `CircuitBreakerRecord` table for multi-worker deployments
- **Prompt types**: Explicit types required (`assessment`, `generation`, `chat`, `worker`)
- **Prompt variables_schema**: JSON Schema required for all prompts to validate variables before rendering
- **Prompt output_schema**: Required for prompts expecting structured JSON output
- **Prompt migration**: Built-in prompts remain static; user-created prompts persisted to DB
- **Prompt A/B testing**: Simple via `parent_version_id` linkage; no percentage-based routing
- **Pipeline visualization**: Pipeline DAG definitions discovered at startup and stored; execution traces stored per-run for replay
- **Telemetry approach**: OpenTelemetry directly (no Prometheus first); OTLP exporter to Tempo/Jaeger/Grafana stack
- **Telemetry scope**: LLM-involving pipelines only (assistant, catalog generation, assessment, evaluation)
- **Metrics retention**: Traces 30 days (hot), aggregated metrics 90 days, pipeline run summaries 1 year
- **Event correlation**: All events must emit `request_id`, `user_id`, `session_id`, `attempt_id`, `workflow_id`, `prompt_version`, `error_code` where applicable (CL-007)
- **LLM artifact metadata**: Every LLM artifact must include `prompt_version`, `model_slug`, `provider` in `ProviderCallRecord.metrics`; stored in persisted records (CL-008)
- **LLM validation**: All structured LLM outputs must be validated against declared schemas before use; validation failure is a **hard stop** via `StructuredOutputRejectionError` (CL-008)
- **Error codes required**: All emitted failures must attach stable `error_code` from the existing taxonomy (CL-006)
- **Migration discipline**: All new models require Alembic migrations; migrations are the only path for production schema evolution (CL-014)
- **Data classification**: Explicitly distinguish transactional domain data from observability/event data in model definitions (CL-014)

---

## API Design Principles (CL-013 Compliant)

All admin API endpoints must follow:
- **Explicit schemas**: Pydantic request/response models required for all endpoints
- **Thin handlers**: Route handlers delegate to domain/application services; no business logic in routes
- **Validation first**: Input validation before orchestration or persistence side effects
- **Versionable contracts**: Backward-incompatible changes must be deliberate and documented
- **No ORM leakage**: Raw ORM models not exposed through API

Example admin endpoint pattern:
```python
@router.get("/admin/prompts", response_model=list[PromptSummary])
async def list_prompts(
    admin: AdminActor = Depends(require_admin_actor),
    service: PromptService = Depends(get_prompt_service),
) -> list[PromptSummary]:
    """List all prompt names with latest version."""
    return await service.list_prompts()
```

---

## Testing Requirements (CL-017 Compliant)

Before each feature release:
- **Core domain logic**: Deterministic automated tests
- **Pydantic validation**: Positive and negative coverage
- **FastAPI contracts**: Endpoint tests with request/response validation
- **Stageflow workflows**: Tests for success, failure, retry, and trace emission paths
- **Schema/scoring regression**: Protected test suite for scoring semantics and artifact compatibility
- **Provider-backed flows**: Smoke tests hitting real providers before release (not mock-only)
- **Error taxonomy**: Tests verify correct error codes and categories are raised

Prohibited:
- Manual testing as sole validation for assessment-critical behavior
- Mock-only testing for complex auth, scoring, generation, and provider-mediated workflows
- Untested schema or scoring changes

---

## Summary Effort Estimate

| Feature | Backend Effort |
|---------|----------------|
| Event Logging (improvements) | Medium |
| Monitoring/Telemetry | High |
| Eval | Medium |
| Prompt Library | Medium |
| User Management | Medium |
| User/Cohort Analytics | Medium |
| Policy Layer | **High** (most complex) |

## Key Architectural Gaps

1. **Response delta aggregation** - Currently every token chunk creates a DB row; needs aggregation into single `response.completed` record
2. **Wide events not persisted** - `WideEventEmitter` is initialized but `stage.wide.*` and `pipeline.wide.*` events go nowhere
3. **No OpenTelemetry integration** - Tracing interceptor active but no OTLP exporter; spans not persisted
4. **Incomplete HTTP audit logging** - Only logs completion, not request details; needs full request/response audit trail
5. **No auth event logging** - Login attempts, token refresh, access denied not tracked
6. **Provider call records lack token counts** - Latency tracked but not prompt/completion/total tokens for all operations
7. **No dedicated policy module** - Policy layer needs to be built from scratch
8. **No consolidated admin dashboard API** - No single endpoint serving a dashboard view
9. **Circuit breakers in-memory only** - Cannot share circuit state across workers
10. **Streaming buffer health untracked** - No visibility into backpressure, chunk drops, throttle events
11. **No prompt library persistence** - `PromptLibrary` is in-memory only; no DB model, no admin API
12. **No pipeline visualization** - Pipeline DAG definitions and execution traces not stored; cannot visualize workflows in admin dashboard
13. **No trace visualization backend** - Jaeger/Tempo/Grafana stack not deployed
14. **Incomplete event correlation** - Not all events emit required identifiers (request_id, user_id, session_id, attempt_id, workflow_id, prompt_version, error_code)

## Recommended Implementation Order

1. **Event Logging Improvements** - Response aggregation, HTTP audit, auth events, typed errors with error codes (foundational for admin visibility)
2. **User Management API** - Foundation for all other features (least dependencies)
3. **User/Cohort Analytics** - Depends on user management, straightforward extension
4. **Eval Dashboard API** - Extensions to existing evaluation infrastructure
5. **Prompt Library API** - Extensions to existing PromptLibrary class
6. **Logs Search API** - New endpoint, minimal dependencies
7. **Monitoring/Telemetry** - OpenTelemetry directly with OTLP exporter to Tempo/Jaeger/Grafana
8. **Policy Layer** - Most complex, requires careful design; do last

## Existing Backend Foundation

The backend already has significant infrastructure in place:

- **Framework:** FastAPI 0.109+ with Uvicorn
- **Database:** SQLAlchemy 2.0+ with Alembic migrations
- **Auth:** Header-based auth with admin role (`require_admin_actor()`)
- **Error taxonomy:** `AppError` with `ErrorCategory` enum (VALIDATION, DOMAIN, SCORING, ORCHESTRATION, PROVIDER, PERSISTENCE, AUTH, UI); error codes `SS-{CATEGORY}-{NUMBER}`; factory functions; `StructuredOutputRejectionError` for LLM validation failures
- **Logging:** structlog with correlation IDs (stdout JSON)
- **Event recording:** Module-specific `*EventRecorder` classes for Practice, Evaluation, Progression; `CatalogEventRecorder` for Catalog; `_record_event()` in Assistant
- **Pipeline/Provider logging:** `DatabasePipelineRunLogger`, `DatabaseProviderCallLogger` via stageflow integration
- **Stageflow runtime:** `BackpressureAwareEventSink`, built-in interceptors (Timeout, CircuitBreaker, Tracing, Metrics, Logging), `WideEventEmitter`
- **Stageflow events to DB:** `pipeline.started/completed/failed`, `stage.{name}.started/completed/failed` via `DurableEventSink`
- **Stageflow types:** `StageKind` (TRANSFORM, ENRICH, ROUTE, GUARD, WORK, AGENT), `StageStatus` (OK, SKIP, CANCEL, FAIL, RETRY)
- **Prompt library:** `PromptLibrary` class (in-memory), static templates in `platform/providers/llm/prompts.py`
- **Admin module:** `modules/admin/` with services, repositories, views
- **Key admin endpoints:** `/admin/collections/verification-queue`, `/admin/learners/{id}/analytics`, `/admin/cohorts/analytics`, `/admin/evaluations/suites`, `/admin/evaluations/runs`, `/events`
- **Event models:** `WorkflowEventRecord`, `PipelineRunRecord`, `ProviderCallRecord`, `EvaluationSuiteRecord`, `EvaluationRunRecord`, `EvaluationCaseResultRecord`, `AssistantStreamEventRecord`, `AssistantSessionRecord`, `AssistantMessageRecord`, `AssistantToolCallRecord`
- **Agent pipelines:** Assistant turn pipeline (input_guard → history_enrich → profile_enrich → progress_enrich → attempts_enrich → assistant_runtime), tool execution sub-pipelines
