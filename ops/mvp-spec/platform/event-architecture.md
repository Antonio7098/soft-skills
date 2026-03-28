# Event Architecture

## Overview

The backend uses a centralized event system for workflow observability. Events are persisted to the database and can be queried, updated, and deleted via the Events API.

## Event Types

### 1. Workflow Events (`workflow_events` table)

Generic workflow events used across all modules. The primary event sink for application-level observability.

**Schema:**
| Field | Type | Description |
|-------|------|-------------|
| `event_id` | string | Unique identifier (UUID hex) |
| `event_type` | string | Namespaced event type (e.g., `collection.created`) |
| `request_id` | string | HTTP request correlation ID |
| `trace_id` | string | Distributed trace ID |
| `workflow_id` | string | Workflow instance identifier |
| `error_code` | string | Error code if event represents an error |
| `organisation_id` | string | Organisation scope |
| `payload` | dict | Event-specific data |
| `occurred_at` | datetime | When the event occurred |

**Sources:**
All modules write workflow events through the unified `WorkflowEventRecorder`:

- `modules/evaluation` - Evaluation workflow events
- `modules/practice` - Practice session/attempt events
- `modules/progression` - Progression calculation events
- `modules/catalog` - Collection, scenario, prompt item events
- `modules/identity` - Identity/auth events
- `modules/admin` - Admin operation events
- `modules/taxonomy` - Taxonomy events

### 2. Pipeline Events (`pipeline_runs` table)

Structured pipeline execution logs with stage-level detail.

**Schema:**
| Field | Type | Description |
|-------|------|-------------|
| `pipeline_run_id` | string | Unique pipeline execution ID |
| `pipeline_name` | string | Name of the pipeline |
| `topology` | string | Pipeline topology |
| `execution_mode` | string | How the pipeline was executed |
| `status` | string | `started`, `completed`, `failed` |
| `request_id` | string | Request correlation ID |
| `trace_id` | string | Trace ID |
| `user_id` | string | User who initiated |
| `error` | string | Error message if failed |
| `failed_stage` | string | Stage that failed |
| `stage_results` | dict | Per-stage results |
| `started_at` | datetime | Execution start |
| `finished_at` | datetime | Execution end |

### 3. Provider Call Events (`provider_calls` table)

LLM provider call logs for cost and performance tracking.

**Schema:**
| Field | Type | Description |
|-------|------|-------------|
| `call_id` | string | Unique call ID |
| `operation` | string | Operation performed |
| `provider` | string | Provider name (e.g., `openai`) |
| `model_id` | string | Model identifier |
| `success` | bool | Whether call succeeded |
| `latency_ms` | int | Call latency |
| `error` | string | Error message if failed |
| `pipeline_run_id` | string | Associated pipeline run |
| `request_id` | string | Request correlation ID |
| `trace_id` | string | Trace ID |
| `metrics` | dict | Additional metrics |
| `created_at` | datetime | Call timestamp |

## Event Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        Application Code                          │
├──────────────┬──────────────┬───────────────┬───────────────────┤
│  Evaluation  │   Practice   │   Progression │      Catalog       │
│    Module    │    Module    │     Module    │       Module       │
└──────┬───────┴──────┬───────┴───────┬───────┴────────┬──────────┘
       │              │               │                │
       └──────────────┴───────────────┴────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │   WorkflowEventRecorder       │
              │   (platform/observability/     │
              │    events.py)                  │
              └───────────────┬───────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
     ┌────────────┐   ┌─────────────┐   ┌──────────────┐
     │ workflow_  │   │  pipeline_  │   │ provider_    │
     │  events   │   │   runs      │   │   calls      │
     └────────────┘   └─────────────┘   └──────────────┘
```

## Event Recorder API

### WorkflowEventRecorder

Unified recorder for all workflow events.

```python
from soft_skills_backend.platform.observability.events import WorkflowEventRecorder

recorder = WorkflowEventRecorder(
    repository=workflow_events_repo,
    logger_name="soft_skills_backend.module"  # optional
)

recorder.record(
    event_type="collection.created",
    request_id="req-123",
    trace_id="trace-456",
    workflow_id="col-789",
    payload={"collection_id": "col-789", "name": "My Collection"},
    error_code=None,
)
```

### Workflow ID Fallback

If `workflow_id` is not provided, the recorder auto-derives it from the payload:

1. `workflow_id` (if explicitly passed)
2. `payload.collection_id`
3. `payload.scenario_id`
4. `payload.generation_artifact_id`

## Event Naming Conventions

Event types use dot-notation namespacing:

| Prefix | Source |
|--------|--------|
| `evaluation.*` | Evaluation workflows |
| `practice.*` | Practice session/attempt workflows |
| `progression.*` | Progression calculation workflows |
| `collection.*` | Collection CRUD operations |
| `scenario.*` | Scenario CRUD operations |
| `prompt_item.*` | Prompt item CRUD operations |
| `stage.wide.*` | Stage execution events |
| `pipeline.wide.*` | Pipeline execution events |
| `tool.invoked` | Tool invocation events |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/events` | List events (filtered by org) |
| `GET` | `/api/events/{event_id}` | Get single event |
| `PATCH` | `/api/events/{event_id}` | Update event |
| `DELETE` | `/api/events/{event_id}` | Delete event |

## Architecture Decisions

### Why Three Separate Tables?

1. **workflow_events** - Generic key-value payload for application events
2. **pipeline_runs** - Structured schema with stage results, suitable for pipeline debugging
3. **provider_calls** - Structured schema with latency/metrics, suitable for cost analytics

### Why Not Event Sourcing?

Current implementation is append-only with update/delete for error correction. Event sourcing with CQRS could be considered for audit-heavy scenarios.

## Adding New Event Types

1. Use the existing `WorkflowEventRecorder` from your module
2. Choose an appropriate `event_type` following the naming conventions
3. Include relevant correlation IDs (`request_id`, `trace_id`, `workflow_id`)
4. Add payload data that aids debugging/analytics

No new recorder classes needed - just use the shared `WorkflowEventRecorder`.
