# Admin Dashboard MVP - Backend Readiness Assessment

## Feature Gap Analysis

### 1. Logs

**Current State:**
- `WorkflowEventRecord`, `PipelineRunRecord`, `ProviderCallRecord` stored in DB
- Structured JSON logging via structlog to stdout
- Events API endpoint at `/events`

**What to Add:**
| Task | Effort | Description |
|------|--------|-------------|
| Log aggregation infrastructure | High | Add Loki or Elasticsearch for log storage (docker-compose) |
| Log search API | Medium | New `/admin/logs` endpoint with filtering (level, timeframe, correlation ID, user ID) |
| Log retention policy | Low | Add cleanup job for old log entries |
| Log viewer endpoint | Medium | Paginated, filterable log retrieval with export option |

---

### 2. Monitoring/Telemetry

**Current State:**
- Request context middleware with correlation IDs
- Database-based pipeline/provider call logging
- Basic health endpoints (`/health`)

**What to Add:**
| Task | Effort | Description |
|------|--------|-------------|
| Prometheus metrics endpoint | Medium | New `/metrics` endpoint exposing request counts, latencies, error rates |
| OpenTelemetry integration | High | Instrument code with traces, add OTLP exporter |
| Health dashboard endpoint | Low | Extended `/health` with component status (DB, external services) |
| Alerting system | High | Define alert rules, add notification channel (Slack, PagerDuty) |
| Distributed tracing UI | Medium | Connect to Jaeger/Zipkin for trace visualization |

---

### 3. Eval

**Current State:**
- `EvaluationSuiteRecord`, `EvaluationRunRecord`, `EvaluationCaseResultRecord`
- Endpoints at `/admin/evaluations/suites` and `/admin/evaluations/runs`
- `EvaluationService`, `MarkingBenchmarkRunner`

**What to Add:**
| Task | Effort | Description |
|------|--------|-------------|
| Ad-hoc evaluation trigger UI API | Medium | `POST /admin/evaluations/runs` already exists, need workflow to trigger |
| Evaluation result dashboard view | Medium | Aggregate pass/fail rates, latency percentiles, error breakdown |
| Historical comparison | Medium | Compare evaluation runs over time |
| Benchmarking dashboard | Medium | Track provider model performance |
| Evaluation case drill-down | Low | Individual case result inspection |

---

### 4. Prompt Library

**Current State:**
- `PromptLibrary` class with `register()`, `render()` in `engines/marking/use_cases/structured_output.py`
- Prompt templates in `platform/providers/llm/prompts.py`
- Versioned via config files

**What to Add:**
| Task | Effort | Description |
|------|--------|-------------|
| Prompt registry API | Medium | `GET/POST /admin/prompts` to list and register templates |
| Prompt versioning | Medium | Add version field, `GET /admin/prompts/{id}/versions` |
| Prompt editing workflow | Medium | `PUT /admin/prompts/{id}` with approval state |
| Prompt analytics | Medium | Track prompt success rates, failure modes, latency |
| Prompt search/filter | Low | Filter by name, version, use case |

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

## Summary Effort Estimate

| Feature | Backend Effort |
|---------|----------------|
| Logs | Medium |
| Monitoring/Telemetry | High |
| Eval | Medium |
| Prompt Library | Medium |
| User Management | Medium |
| User/Cohort Analytics | Medium |
| Policy Layer | **High** (most complex) |

## Key Architectural Gaps

1. **No metrics system** - Needs Prometheus/OpenTelemetry integration
2. **No log aggregation** - Logs go to stdout only; needs Loki/Elasticsearch + search API
3. **No dedicated policy module** - Policy layer needs to be built from scratch
4. **No consolidated admin dashboard API** - No single endpoint serving a dashboard view

## Recommended Implementation Order

1. **User Management API** - Foundation for all other features (least dependencies)
2. **User/Cohort Analytics** - Depends on user management, straightforward extension
3. **Eval Dashboard API** - Extensions to existing evaluation infrastructure
4. **Prompt Library API** - Extensions to existing PromptLibrary class
5. **Logs Search API** - New endpoint, minimal dependencies
6. **Monitoring/Telemetry** - Prometheus metrics first, then OpenTelemetry
7. **Policy Layer** - Most complex, requires careful design; do last

## Existing Backend Foundation

The backend already has significant infrastructure in place:

- **Framework:** FastAPI 0.109+ with Uvicorn
- **Database:** SQLAlchemy 2.0+ with Alembic migrations
- **Auth:** Header-based auth with admin role (`require_admin_actor()`)
- **Logging:** structlog with correlation IDs
- **Admin module:** `modules/admin/` with services, repositories, views
- **Key admin endpoints:** `/admin/collections/verification-queue`, `/admin/learners/{id}/analytics`, `/admin/cohorts/analytics`, `/admin/evaluations/suites`, `/admin/evaluations/runs`
