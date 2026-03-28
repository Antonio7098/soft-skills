# Admin Dashboard Frontend Specification

> This document specifies the frontend API requirements and page layout proposal for the admin dashboard.
> It is derived from the backend implementation in `backend/src/soft_skills_backend/entrypoints/http/routes/admin.py`, `evaluations.py`, `events.py`, and the sprint docs in `ops/sprints/sprint-13a-13h`.

---

## A. Frontend API Endpoints

All endpoints are prefixed with `/api/admin` and return `ApiEnvelope<T>` (Pydantic wrapper with `data: T` field). Auth requires an admin actor via `Authorization` header. All timestamps are ISO-8601 strings.

### A1. Users & User Management

| Method | Path | Purpose | Query Params | Response Shape |
|--------|------|---------|--------------|----------------|
| `GET` | `/admin/users` | List users with pagination and filters | `offset` (int, default 0), `limit` (int, default 50, max 100), `search` (string, optional, matches email or display_name), `role` (string, optional: "admin"\|"member"), `is_active` (bool, optional) | `AdminUserListView: { users: AdminUserView[], total: int, offset: int, limit: int }` |
| `GET` | `/admin/users/{user_id}` | Get a specific user's details | — | `AdminUserView \| null` |
| `PUT` | `/admin/users/{user_id}/role` | Change a user's org role | — (body: `{ role: "admin" \| "member" }`) | `AdminUserView` |
| `PATCH` | `/admin/users/{user_id}/status` | Suspend or activate a user | — (body: `{ is_active: bool }`) | `AdminUserView` |
| `POST` | `/admin/users` | Add/invite a user to the org | — (body: `{ email: string, role: "admin" \| "member" }`) | `AdminUserView` |
| `POST` | `/admin/users/bulk` | Bulk user operations | — (body: `{ user_ids: string[], operation: "suspend" \| "activate" \| "change_role" \| "export", payload?: { role?: string } }`) | `BulkOperationResultView: { operation, requested_count, success_count, failure_count, failed_user_ids[] }` |
| `GET` | `/admin/users/{user_id}/activity` | Get user activity summary | — | `UserActivityView: { user_id, email, display_name, organisation_id?, organisation_role?, total_sessions, total_attempts, recent_sessions: UserSessionView[], recent_attempts: UserAttemptSummaryView[], recent_logins: UserLoginEventView[] }` |

**`AdminUserView`** shape:
```json
{
  "user_id": "string",
  "email": "string",
  "display_name": "string",
  "auth_provider": "string",
  "is_active": "boolean",
  "organisation_id": "string | null",
  "organisation_role": "string | null",
  "created_at": "string | null"
}
```

**`UserSessionView`** shape:
```json
{
  "session_id": "string",
  "practice_type": "string",
  "content_item_id": "string",
  "status": "string",
  "created_at": "string | null",
  "completed_at": "string | null"
}
```

**`UserAttemptSummaryView`** shape:
```json
{
  "attempt_id": "string",
  "session_id": "string",
  "practice_type": "string",
  "content_item_id": "string",
  "content_item_type": "string",
  "status": "string",
  "overall_score": "int | null",
  "submitted_at": "string | null",
  "assessed_at": "string | null"
}
```

**`UserLoginEventView`** shape:
```json
{
  "event_type": "string",
  "occurred_at": "string | null",
  "trace_id": "string | null"
}
```

---

### A2. Learners & Relationships

| Method | Path | Purpose | Query Params | Response Shape |
|--------|------|---------|--------------|----------------|
| `GET` | `/admin/learners/{learner_id}/analytics` | Learner analytics with time range | `from_date` (datetime, optional), `to_date` (datetime, optional) | `LearnerAnalyticsView` |
| `GET` | `/admin/learners/{learner_id}/relationship` | Get admin-learner relationship | — | `AdminLearnerRelationshipView \| null` |
| `PUT` | `/admin/learners/{learner_id}/relationship` | Set admin-learner relationship | — (body: `{ relationship_type: string }`) | `AdminLearnerRelationshipView` |
| `DELETE` | `/admin/learners/{learner_id}/relationship` | Remove relationship | — | `{ status: "deleted" }` |

**`LearnerAnalyticsView`** shape:
```json
{
  "learner_id": "string",
  "target_role": "string | null",
  "latest_progress_snapshot_id": "string | null",
  "latest_recommendation_id": "string | null",
  "weak_skill_slugs": ["string"],
  "stagnating_skill_slugs": ["string"],
  "coverage_gap_skill_slugs": ["string"],
  "usage": "UsageSummaryView",
  "recent_attempts": ["AdminAttemptSummaryView"],
  "usage_trend": ["UsageTrendPointView"],
  "provider_summary": ["ProviderUsageView"]
}
```

**`AdminLearnerRelationshipView`** shape:
```json
{
  "learner_user_id": "string",
  "admin_user_id": "string",
  "relationship_type": "string",
  "created_at": "string",
  "updated_at": "string"
}
```

---

### A3. Analytics Overview

| Method | Path | Purpose | Query Params | Response Shape |
|--------|------|---------|--------------|----------------|
| `GET` | `/admin/analytics/overview` | Aggregated platform analytics | `from_date` (datetime, optional), `to_date` (datetime, optional) | `AnalyticsOverviewView` |
| `GET` | `/admin/cohorts/analytics` | Cohort analytics | `target_role` (string, optional), `from_date`, `to_date` | `CohortAnalyticsView` |
| `GET` | `/admin/cohorts/comparison` | Compare multiple cohorts | `cohort_keys` (string, comma-separated), `from_date`, `to_date` | `CohortComparisonView` |
| `GET` | `/admin/analytics/export` | Export analytics as CSV or JSON | `format` ("csv"\|"json", default "json"), `from_date`, `to_date` | StreamingResponse |

**`AnalyticsOverviewView`** shape:
```json
{
  "total_learners": "int",
  "active_learners_30d": "int",
  "total_sessions": "int",
  "total_attempts": "int",
  "submitted_attempts": "int",
  "validated_assessments": "int",
  "rejected_assessments": "int",
  "avg_validated_score": "float | null",
  "overall_usage_trend": ["UsageTrendPointView"],
  "top_weak_skills": ["SkillClusterView"],
  "cohort_breakdown": [{"cohort_key": "string", "learner_count": "int}"],
  "provider_summary": ["ProviderUsageView"]
}
```

**`CohortAnalyticsView`** shape:
```json
{
  "cohort_key": "string",
  "learner_count": "int",
  "usage": "UsageSummaryView",
  "weak_skill_clusters": ["SkillClusterView"],
  "average_skill_scores": ["SkillAverageView"],
  "usage_trend": ["UsageTrendPointView"],
  "provider_summary": ["ProviderUsageView"]
}
```

**`UsageSummaryView`** shape:
```json
{
  "total_sessions": "int",
  "total_attempts": "int",
  "submitted_attempts": "int",
  "assessed_attempts": "int",
  "validated_assessments": "int",
  "rejected_assessments": "int",
  "workflow_event_count": "int",
  "pipeline_run_count": "int",
  "provider_call_count": "int",
  "avg_validated_score": "float | null",
  "last_activity_at": "string | null"
}
```

**`UsageTrendPointView`** shape:
```json
{
  "bucket_date": "string",
  "sessions_started": "int",
  "attempts_submitted": "int",
  "assessments_validated": "int",
  "assessments_rejected": "int"
}
```

**`ProviderUsageView`** shape:
```json
{
  "provider": "string",
  "model_slug": "string | null",
  "call_count": "int",
  "success_count": "int",
  "failure_count": "int",
  "avg_latency_ms": "float | null"
}
```

**`SkillClusterView`** shape:
```json
{
  "skill_slug": "string",
  "learner_count": "int"
}
```

**`SkillAverageView`** shape:
```json
{
  "skill_slug": "string",
  "avg_score": "float",
  "learner_count": "int"
}
```

---

### A4. Collections & Verification

| Method | Path | Purpose | Response Shape |
|--------|------|---------|---------------|
| `GET` | `/admin/collections/verification-queue` | List collections pending verification | `CollectionVerificationQueueItemView[]` |
| `GET` | `/admin/collections/{collection_id}/verification` | Full verification audit trail | `CollectionVerificationAuditView` |
| `POST` | `/admin/collections/{collection_id}/verification` | Update verification state | `CollectionVerificationAuditView` (body: `{ verification_state: string, note?: string }`) |
| `PATCH` | `/admin/collections/{collection_id}/feature` | Feature/unfeature a collection | `CollectionView` (body: `{ featured: boolean }`) |

**`CollectionVerificationQueueItemView`** shape:
```json
{
  "collection_id": "string",
  "author_user_id": "string",
  "title": "string",
  "lifecycle_state": "string",
  "verification_state": "string",
  "discovery_tier": "string",
  "source_type": "string",
  "prompt_item_count": "int",
  "scenario_count": "int",
  "created_at": "string",
  "updated_at": "string",
  "latest_reviewed_at": "string | null",
  "latest_reviewer_user_id": "string | null",
  "latest_note": "string | null"
}
```

**`CollectionVerificationAuditView`** shape:
```json
{
  "collection": "CollectionView",
  "latest_review": "CollectionVerificationReviewView | null",
  "history": ["CollectionVerificationReviewView"]
}
```

---

### A5. Evaluation Dashboard

| Method | Path | Purpose | Query Params | Response Shape |
|--------|------|---------|--------------|----------------|
| `GET` | `/admin/evaluations/suites` | List eval suites | — | `EvaluationSuiteView[]` |
| `GET` | `/admin/evaluations/runs` | List recent eval runs | `limit` (int, default 20) | `EvaluationRunView[]` |
| `GET` | `/admin/evaluations/runs/{run_id}` | Get specific run | — | `EvaluationRunView` |
| `POST` | `/admin/evaluations/runs` | Trigger new eval run | — (body: `{ suite_id: string, ... }`) | `EvaluationRunView` |
| `GET` | `/admin/evaluations/dashboard` | Eval dashboard aggregated view | `from_date`, `to_date` | `EvaluationDashboardView` |
| `GET` | `/admin/evaluations/runs/compare` | Compare historical runs | `run_ids` (string, comma-separated IDs), `from_date`, `to_date` | `EvaluationComparisonView` |
| `GET` | `/admin/evaluations/benchmark` | Model performance tracking | `from_date`, `to_date` | `BenchmarkDashboardView` |
| `GET` | `/admin/evaluations/cases/{case_id}` | Individual case drill-down | — | `EvaluationCaseDetailView` |

**`EvaluationDashboardView`** shape:
```json
{
  "total_runs": "int",
  "pass_fail": { "passed": "int", "failed": "int", "pass_rate": "float" },
  "latency_percentiles": { "p50_ms": "float", "p95_ms": "float", "p99_ms": "float" },
  "error_breakdown": [{ "error_code": "string", "count": "int", "percentage": "float" }],
  "total_cases": "int",
  "total_tokens": "int",
  "estimated_cost_usd": "float | null",
  "suite_breakdown": { "[suite_id]": "EvalPassFailRateView" },
  "from_date": "string | null",
  "to_date": "string | null"
}
```

**`EvaluationComparisonView`** shape:
```json
{
  "runs": [{
    "evaluation_run_id": "string",
    "suite_id": "string",
    "suite_type": "string",
    "passed": "bool",
    "pass_rate": "float | null",
    "avg_latency_ms": "float | null",
    "total_tokens": "int",
    "case_count": "int",
    "model_slugs": ["string"],
    "started_at": "string"
  }],
  "run_count": "int",
  "total_cases": "int",
  "avg_pass_rate": "float | null",
  "avg_latency_ms": "float | null"
}
```

**`BenchmarkDashboardView`** shape:
```json
{
  "models": [{
    "model_slug": "string",
    "provider": "string | null",
    "run_count": "int",
    "passed_count": "int",
    "failed_count": "int",
    "pass_rate": "float | null",
    "avg_latency_ms": "float | null",
    "total_prompt_tokens": "int",
    "total_completion_tokens": "int",
    "total_tokens": "int",
    "estimated_cost_usd": "float | null"
  }],
  "total_runs": "int",
  "total_cases": "int",
  "from_date": "string | null",
  "to_date": "string | null"
}
```

**`EvaluationCaseDetailView`** shape:
```json
{
  "case_id": "string",
  "case_label": "string",
  "status": "string",
  "error_code": "string | null",
  "suite_id": "string",
  "suite_type": "string",
  "suite_version": "string",
  "evaluation_run_id": "string",
  "passed": "bool",
  "metrics": "dict",
  "detail_payload": "dict",
  "started_at": "string",
  "completed_at": "string | null"
}
```

---

### A6. Prompts

| Method | Path | Purpose | Response Shape |
|--------|------|---------|---------------|
| `GET` | `/admin/prompts` | List all prompt families with latest version | `PromptSummaryView[]` |
| `GET` | `/admin/prompts/{name}/versions` | List all versions of a prompt | `PromptVersionView[]` |
| `GET` | `/admin/prompts/{name}/versions/{version}` | Get specific version detail | `PromptVersionView` |
| `POST` | `/admin/prompts` | Create new prompt version (draft) | `PromptVersionView` (body: `{ name, version, prompt_type, template, variables_schema, output_schema?, parent_version_id? }`) |
| `PUT` | `/admin/prompts/{name}/versions/{version}` | Update draft version | `PromptVersionView` (body: `{ template?, variables_schema?, output_schema? }`) |
| `POST` | `/admin/prompts/{name}/versions/{version}/publish` | Publish to production | `PromptVersionView` (body: `{}`) |
| `POST` | `/admin/prompts/{name}/versions/{version}/archive` | Archive version | `PromptVersionView` (body: `{}`) |
| `GET` | `/admin/prompts/{name}/versions/{version}/analytics` | Performance metrics | `PromptAnalyticsView` |
| `POST` | `/admin/prompts/compare` | A/B compare two versions | `PromptCompareView` (body: `{ name, version_a, version_b }`) |

**`PromptSummaryView`** shape:
```json
{
  "name": "string",
  "prompt_type": "string",
  "latest_version": "string",
  "status": "string",
  "created_at": "string"
}
```

**`PromptVersionView`** shape:
```json
{
  "id": "int",
  "name": "string",
  "version": "string",
  "prompt_type": "string",
  "template": "string",
  "variables_schema": "dict",
  "output_schema": "dict | null",
  "status": "string",
  "parent_version_id": "int | null",
  "created_at": "string",
  "updated_at": "string"
}
```

**`PromptAnalyticsView`** shape:
```json
{
  "prompt_version_id": "int",
  "name": "string",
  "version": "string",
  "render_count": "int",
  "success_count": "int",
  "failure_count": "int",
  "avg_latency_ms": "float | null",
  "total_tokens": "int",
  "last_rendered_at": "string | null"
}
```

**`PromptCompareView`** shape:
```json
{
  "name": "string",
  "version_a": "string",
  "version_b": "string",
  "template_a": "string",
  "template_b": "string",
  "variables_schema_a": "dict",
  "variables_schema_b": "dict",
  "metrics_a": "PromptAnalyticsView | null",
  "metrics_b": "PromptAnalyticsView | null"
}
```

---

### A7. Pipelines

| Method | Path | Purpose | Response Shape |
|--------|------|---------|---------------|
| `GET` | `/admin/pipelines` | List all pipeline definitions | `PipelineDefinitionView[]` |
| `GET` | `/admin/pipelines/{pipeline_name}` | Get full DAG with stages and dependencies | `PipelineDAGView` |
| `GET` | `/admin/pipelines/{pipeline_name}/runs` | List recent runs | `PipelineRunSummaryView[]` (query: `offset`, `limit`) |
| `GET` | `/admin/pipelines/{pipeline_name}/runs/{pipeline_run_id}/trace` | Get execution trace for visualization | `PipelineTraceView` |
| `GET` | `/admin/pipelines/{pipeline_name}/metrics` | Aggregate stage metrics | `PipelineMetricsView` |

**`PipelineDefinitionView`** shape:
```json
{
  "pipeline_name": "string",
  "topology": "string | null",
  "description": "string | null",
  "stage_count": "int",
  "created_at": "string | null",
  "updated_at": "string | null"
}
```

**`PipelineDAGView`** shape:
```json
{
  "pipeline_name": "string",
  "topology": "string | null",
  "description": "string | null",
  "stages": [{
    "name": "string",
    "kind": "string (TRANSFORM|ENRICH|ROUTE|GUARD|WORK|AGENT)",
    "dependencies": ["string"],
    "runner_class": "string | null",
    "description": "string | null"
  }]
}
```

**`PipelineRunSummaryView`** shape:
```json
{
  "pipeline_run_id": "string",
  "pipeline_name": "string",
  "status": "string",
  "execution_mode": "string | null",
  "user_id": "string | null",
  "request_id": "string | null",
  "trace_id": "string | null",
  "error": "string | null",
  "failed_stage": "string | null",
  "started_at": "string | null",
  "finished_at": "string | null",
  "duration_ms": "int | null"
}
```

**`PipelineTraceView`** shape:
```json
{
  "pipeline_run_id": "string",
  "pipeline_name": "string",
  "execution_sequence": [{
    "stage_name": "string",
    "event_type": "string",
    "timestamp": "string",
    "duration_ms": "int | null",
    "status": "string | null",
    "error": "string | null"
  }],
  "total_duration_ms": "int",
  "started_at": "string | null",
  "completed_at": "string | null"
}
```

**`PipelineMetricsView`** shape:
```json
{
  "pipeline_name": "string",
  "total_runs": "int",
  "success_count": "int",
  "failure_count": "int",
  "cancel_count": "int",
  "stage_metrics": [{
    "stage_name": "string",
    "invocation_count": "int",
    "success_count": "int",
    "failure_count": "int",
    "skip_count": "int",
    "cancel_count": "int",
    "retry_count": "int",
    "avg_duration_ms": "float | null",
    "p50_duration_ms": "int | null",
    "p95_duration_ms": "int | null",
    "p99_duration_ms": "int | null"
  }]
}
```

---

### A8. Rubrics

| Method | Path | Purpose | Response Shape |
|--------|------|---------|---------------|
| `GET` | `/admin/rubrics` | List all rubrics | `RubricView[]` |
| `GET` | `/admin/rubrics/{rubric_id}` | Get rubric detail | `RubricView` |
| `POST` | `/admin/rubrics` | Create rubric | `RubricView` (body: `{ rubric_id, family, version, content_type, schema_version, name, criteria[] }`) |
| `PATCH` | `/admin/rubrics/{rubric_id}` | Update rubric | `RubricView` (body: `{ family?, version?, name? }`) |
| `DELETE` | `/admin/rubrics/{rubric_id}` | Delete rubric | `{ status: "deleted" }` |
| `POST` | `/admin/rubrics/{rubric_id}/criteria` | Add criterion | `RubricView` (body: criterion object) |
| `PATCH` | `/admin/rubrics/{rubric_id}/criteria/{criterion_ref}` | Update criterion | `RubricView` (body) |
| `DELETE` | `/admin/rubrics/{rubric_id}/criteria/{criterion_ref}` | Delete criterion | `RubricView` |

**`RubricView`** shape:
```json
{
  "rubric_id": "string",
  "family": "string",
  "version": "string",
  "content_type": "string",
  "schema_version": "string",
  "name": "string",
  "criteria": [{
    "criterion_ref": "string",
    "skill_slug": "string",
    "title": "string",
    "description": "string",
    "weight": "float",
    "required": "bool",
    "position": "int",
    "levels": [{ "level": "int", "description": "string", "examples": ["string"] }]
  }]
}
```

---

### A9. Audit & Events

| Method | Path | Purpose | Query Params | Response Shape |
|--------|------|---------|--------------|----------------|
| `GET` | `/events` | List workflow events (paginated) | `event_type`, `trace_id`, `workflow_id`, `request_id`, `error_code`, `offset` (default 0), `limit` (default 50, max 200) | `PaginatedWorkflowEventsView: { items: WorkflowEventListView[], total, offset, limit }` |
| `GET` | `/events/{event_id}` | Get single event | — | `WorkflowEventView` |
| `PATCH` | `/events/{event_id}` | Update event | — (body: `{ error_code?, payload? }`) | `WorkflowEventView` |
| `DELETE` | `/events/{event_id}` | Delete event | — | `{ status: "deleted" }` |
| `GET` | `/admin/attempts/{attempt_id}/audit` | Full attempt audit trail | — | `AttemptAuditView` |

**`WorkflowEventListView`** / **`WorkflowEventView`** shape:
```json
{
  "event_id": "string",
  "event_type": "string",
  "request_id": "string | null",
  "trace_id": "string | null",
  "workflow_id": "string | null",
  "error_code": "string | null",
  "payload": "dict",
  "occurred_at": "string"
}
```

**`AttemptAuditView`** shape:
```json
{
  "attempt": "AdminAttemptSummaryView",
  "response_visibility": "string",
  "access_relationship": "AdminLearnerRelationshipView | null",
  "prompt": "AdminPromptAuditView",
  "response_text": "string | null",
  "assessment": "AdminAssessmentAuditView | null",
  "latest_progress_snapshot_id": "string | null",
  "latest_recommendation_id": "string | null",
  "workflow_events": ["WorkflowEventAuditView"],
  "pipeline_runs": ["PipelineRunAuditView"],
  "provider_calls": ["ProviderCallAuditView"]
}
```

**`AdminAssessmentAuditView`** shape:
```json
{
  "assessment_id": "string",
  "validation_status": "string",
  "prompt_version": "string",
  "rubric_id": "string",
  "rubric_version": "string",
  "schema_version": "string",
  "config_version": "string",
  "provider": "string",
  "model_slug": "string",
  "overall_score": "int | null",
  "rejection_code": "string | null",
  "trace_id": "string",
  "pipeline_run_id": "string",
  "evidence_count": "int",
  "strengths_count": "int",
  "weaknesses_count": "int",
  "next_actions_count": "int",
  "evidence_quotes": ["string"],
  "strengths": ["string"],
  "weaknesses": ["string"],
  "next_actions": ["string"],
  "skill_scores": [{ "skill_slug": "string", "score": "int", "rationale": "string" }],
  "created_at": "string"
}
```

---

## B. Admin Dashboard Pages & Layout Proposal

### B1. Overall Layout

**Navigation Structure:**

```
┌─────────────────────────────────────────────────────────────┐
│  [Logo]  Soft Skills Admin               [Admin: name] [�_POWER] │
├──────────────┬──────────────────────────────────────────────┤
│              │                                              │
│  Overview    │   Page Content Area                          │
│  Users       │                                              │
│  Learners    │                                              │
│  Analytics   │                                              │
│  Collections │                                              │
│  Evaluations │                                              │
│  Prompts     │                                              │
│  Pipelines   │                                              │
│  Rubrics     │                                              │
│  Audit Logs  │                                              │
│              │                                              │
└──────────────┴──────────────────────────────────────────────┘
```

**Global Components:**
- **Top bar**: Logo, breadcrumbs, admin user info, power/user menu
- **Left sidebar nav**: Collapsible, active state highlighted, icon + label per section
- **Date range picker** (persistent in top bar or each page header, default last 30d)
- **API error toasts**: Structured error display using `AppError` shape

---

### B2. Page Specifications

#### B2.1 Overview Dashboard (`/admin`)

**Purpose:** At-a-glance platform health and key metrics.

**What it shows:**
- **KPI Cards row**: Total learners, active (last 30d), total sessions, avg assessment score, validation rate
- **Usage trend chart**: Line/area chart of `sessions_started`, `attempts_submitted`, `assessments_validated` over time (from `overall_usage_trend`)
- **Top weak skills table**: skill slug + learner count from `top_weak_skills`
- **Provider summary**: Table of provider calls, success rates, avg latency from `provider_summary`
- **Cohort breakdown**: Bar chart or table of learner counts per cohort
- **Recent alerts/errors**: From `error_breakdown` (if eval section populated), or recent failed pipeline runs

**Key workflows:**
- Click any KPI card → navigate to relevant detail page
- Change date range → refresh all widgets
- Export button → triggers `/admin/analytics/export`

---

#### B2.2 Users Page (`/admin/users`)

**Purpose:** Manage all users in the organisation.

**What it shows:**
- **Search + filter bar**: Search by email/name, filter by role (admin/member), filter by status (active/inactive)
- **User table**: Columns: Name, Email, Role, Status, Joined, Actions
  - Row click → User detail drawer or page
- **Bulk actions toolbar**: Select multiple → Suspend, Activate, Change Role, Export
- **Pagination**: offset/limit controls, total count

**User Detail Page (`/admin/users/{user_id}`):**
- Profile card: name, email, auth provider, role, status, joined date
- Tab: **Activity** — recent sessions, attempts, login events (from `UserActivityView`)
- Tab: **Analytics** — same as learner analytics (from `LearnerAnalyticsView`) — reused component
- Tab: **Relationship** — admin-learner relationship management
- Actions: Change Role button, Suspend/Activate toggle, Delete relationship

**Key workflows:**
- Search and filter users → paginated list
- Click user row → slide-over panel or dedicated page
- Bulk select + suspend → confirmation modal → `POST /admin/users/bulk`
- Invite user → modal with email + role → `POST /admin/users`

---

#### B2.3 Learners Page (`/admin/learners`)

**Purpose:** View learner progress and manage learner-admin relationships.

**What it shows:**
- **Learner list** (pulled from user list filtered by role=member, or separate learner index)
- **Search** by learner name/email
- **Relationship filter**: Show all, My assigned learners only, Unassigned
- **Relationship status badges**

**Learner Detail Page (`/admin/learners/{learner_id}`):**
- Learner profile header
- **Progress Summary card**: weak skill slugs, stagnating skills, coverage gaps
- **Usage stats**: sessions, attempts, submitted, validated, rejected
- **Usage trend chart**: daily buckets from `usage_trend`
- **Recent attempts table**: from `recent_attempts` with status, score, date
- **Provider usage table**: from `provider_summary`
- **Actions**: Create/Edit relationship, View full attempt audit

---

#### B2.4 Analytics Page (`/admin/analytics`)

**Purpose:** Platform-wide and cohort analytics with drill-down.

**Sub-pages / tabs:**

**Overview tab** (default):
- Same as overview dashboard but full-page, more chart types
- `GET /admin/analytics/overview`

**Cohorts tab**:
- Cohort selector/grid
- `GET /admin/cohorts/analytics` per cohort
- Weak skill clusters, average skill scores table
- `GET /admin/cohorts/comparison` for side-by-side

**Learner Drill-down tab**:
- Select learner → shows full `LearnerAnalyticsView`
- Progress snapshot and recommendation IDs shown (not rendered, just stored)

**Key workflows:**
- Date range selection → all analytics queries re-fetch
- Export → `GET /admin/analytics/export?format=csv`
- Cohort comparison → multi-select cohorts → `GET /admin/cohorts/comparison?cohort_keys=a,b`

---

#### B2.5 Collections & Verification Page (`/admin/collections`)

**Sub-pages / tabs:**

**Verification Queue tab:**
- Queue list from `GET /admin/collections/verification-queue`
- Columns: Title, Author, State, Verification Status, Items, Scenarios, Submitted date, Last reviewed
- Click row → verification detail

**Verification Detail (`/admin/collections/{collection_id}/verification`):**
- Collection preview (title, author, content summary)
- Verification history timeline (`history[]`)
- Current state + state transition form
- Note/comment field
- Action: Approve / Reject / Request Changes → `POST /admin/collections/{id}/verification`

**All Collections tab:**
- Searchable, filterable collection list
- Actions: Feature/unfeature toggle (`PATCH /admin/collections/{id}/feature`)

**Key workflows:**
- Reviewer picks item from queue → reviews → submits decision
- Admin can feature collections to highlight them

---

#### B2.6 Evaluations Page (`/admin/evaluations`)

**Purpose:** View eval suite results, run comparisons, track model performance.

**Sub-pages / tabs:**

**Dashboard tab** (default):
- KPI row: Total runs, Pass rate %, Avg latency, Total cost
- Pass/fail trend chart over time
- Error breakdown table
- Suite breakdown cards

**Runs tab:**
- Paginated list of `EvaluationRunView`
- Filter by suite, date range
- Click row → run detail

**Run Detail (`/admin/evaluations/runs/{run_id}`):**
- Run metadata: suite, started at, duration, status
- Results summary: passed/failed counts
- Trigger new run button → `POST /admin/evaluations/runs`

**Compare tab:**
- Multi-select runs → `GET /admin/evaluations/runs/compare`
- Historical comparison chart (pass rate over time, latency over time)
- Table: run_id, suite, pass_rate, avg_latency, total_tokens, model_slugs

**Benchmark tab:**
- Model performance leaderboard from `GET /admin/evaluations/benchmark`
- Table: model_slug, provider, pass_rate, avg_latency, total_tokens, cost
- Sortable by any column

**Case Drill-down (`/admin/evaluations/cases/{case_id}`):**
- Full `EvaluationCaseDetailView` rendered
- Metrics and detail payload displayed
- Useful for debugging a specific failing case

**Key workflows:**
- Compare runs → checkboxes → compare button
- Trigger new eval → modal with suite selector → POST

---

#### B2.7 Prompts Page (`/admin/prompts`)

**Purpose:** Manage, version, publish, and analyze prompt templates.

**Sub-pages / tabs:**

**Prompt Library tab:**
- Card grid or table of `PromptSummaryView[]`
- Columns: Name, Type, Latest Version, Status (draft/published/archived)
- Click card → version list

**Prompt Version List (`/admin/prompts/{name}`):**
- Timeline of versions from `GET /admin/prompts/{name}/versions`
- Each version: version string, status, created_at, parent_version_id
- Actions: Edit (if draft), Publish (if draft), Archive (if published)

**Prompt Version Editor:**
- Template editor (code/monaco editor)
- Variables schema editor (JSON schema form)
- Output schema editor (JSON schema form)
- Preview/test panel
- Save (draft) / Publish actions

**Analytics tab (per prompt):**
- `GET /admin/prompts/{name}/versions/{version}/analytics`
- Render count, success/failure rate, avg latency, total tokens
- Time series chart of renders

**Compare tab:**
- Select two versions → `POST /admin/prompts/compare`
- Side-by-side template diff
- Metrics comparison table

**Key workflows:**
- Create new prompt → modal (name, type, template, schema) → `POST /admin/prompts`
- Edit draft → `PUT /admin/prompts/{name}/versions/{version}`
- Publish → `POST /admin/prompts/{name}/versions/{version}/publish`
- Archive → `POST /admin/prompts/{name}/versions/{version}/archive`

---

#### B2.8 Pipelines Page (`/admin/pipelines`)

**Purpose:** Visualize pipeline DAGs, inspect runs, analyze stage metrics.

**Sub-pages / tabs:**

**Pipeline List tab:**
- `GET /admin/pipelines` → table
- Columns: Pipeline name, Topology, Stage count, Description
- Click row → DAG view

**DAG View (`/admin/pipelines/{pipeline_name}`):**
- `GET /admin/pipelines/{pipeline_name}` → full DAG
- Visual DAG graph: nodes = stages (color-coded by `StageKind`), edges = dependencies
- Node colors: TRANSFORM=blue, ENRICH=green, ROUTE=yellow, GUARD=orange, WORK=purple, AGENT=red
- Click any node → stage detail (kind, runner class, description)
- Tabs: DAG | Runs | Metrics

**Runs List tab:**
- `GET /admin/pipelines/{pipeline_name}/runs` (paginated)
- Columns: Run ID, Status, User, Started, Duration, Failed Stage
- Click row → trace view

**Trace View (`/admin/pipelines/{pipeline_name}/runs/{run_id}/trace`):**
- `GET /admin/pipelines/{pipeline_name}/runs/{run_id}/trace`
- Sequential stage execution timeline (flame-chart style or waterfall)
- Each stage: name, status (OK/SKIP/CANCEL/FAIL/RETRY), duration, timestamp
- Expandable error details per stage

**Metrics tab:**
- `GET /admin/pipelines/{pipeline_name}/metrics`
- Summary: total runs, success/fail/cancel counts
- Per-stage metrics table: invocation count, success/fail/skip/cancel/retry counts, avg/p50/p95/p99 duration
- Latency histogram per stage (if data available)

**Key workflows:**
- Inspect failed run → find failed stage → view error message
- Compare latency across runs → runs list with sort by duration
- Monitor stage health → metrics table shows success rate per stage

---

#### B2.9 Rubrics Page (`/admin/rubrics`)

**Purpose:** View and manage assessment rubrics.

**What it shows:**
- Rubric list from `GET /admin/rubrics`
- Card per rubric: name, family, version, criteria count
- Click → rubric detail

**Rubric Detail (`/admin/rubrics/{rubric_id}`):**
- `GET /admin/rubrics/{rubric_id}` → full `RubricView`
- Criterion accordion: each criterion shows title, skill_slug, weight, required flag, levels
- Actions: Add Criterion, Edit Criterion, Delete Criterion

**CRUD operations:**
- Create rubric → `POST /admin/rubrics`
- Update rubric metadata → `PATCH /admin/rubrics/{rubric_id}`
- Add criterion → `POST /admin/rubrics/{rubric_id}/criteria`
- Update criterion → `PATCH /admin/rubrics/{rubric_id}/criteria/{criterion_ref}`
- Delete criterion → `DELETE /admin/rubrics/{rubric_id}/criteria/{criterion_ref}`
- Delete rubric → `DELETE /admin/rubrics/{rubric_id}`

---

#### B2.10 Audit Logs Page (`/admin/audit`)

**Sub-pages / tabs:**

**Events tab:**
- `GET /events` with filter controls
- Filters: event_type (dropdown/autocomplete), trace_id, workflow_id, request_id, error_code
- Table columns: Event ID, Event Type, Trace ID, Workflow ID, Error Code, Occurred At
- Click row → event detail modal/drawer
- Pagination: offset/limit, total count

**Event Detail modal:**
- Full `WorkflowEventView` rendered as key-value pairs
- JSON payload viewer (collapsible tree)

**Attempt Audit tab:**
- Search by attempt_id
- `GET /admin/attempts/{attempt_id}/audit` → full `AttemptAuditView`
- Sections: Attempt Summary, Prompt, Response, Assessment (if any), Workflow Events, Pipeline Runs, Provider Calls
- Useful for debugging learner assessment issues

**Key workflows:**
- Search events by trace_id → trace execution path through system
- Search events by error_code → all failures of a type
- Inspect failed attempt → full artifact lineage

---

## C. Priority

### Phase 1: Core Admin Operations (Must Have)

These pages are the minimum viable admin dashboard — essential for daily operations and content quality.

| Priority | Page | Why |
|----------|------|-----|
| **P0** | Overview Dashboard | First landing page; immediate platform health visibility |
| **P0** | Users Page | User management is foundational; all other features depend on it |
| **P0** | Collections Verification Queue | Content quality gate; blocks public content from going live |
| **P0** | Analytics Overview | Core reporting; org-level KPIs |
| **P1** | User/Learner Detail + Analytics | Drill-down from user list; required for learner coaching |
| **P1** | Cohort Analytics | Segmentation view; team leads need cohort data |
| **P1** | Audit Logs (Events tab) | Operational debugging; trace issues through correlation IDs |

### Phase 2: Evaluation & Monitoring

| Priority | Page | Why |
|----------|------|-----|
| **P1** | Evaluations Dashboard + Runs | Track assessment quality; identify regressions |
| **P2** | Evaluation Compare + Benchmark | Model performance; decide when to switch providers |
| **P2** | Evaluation Case Drill-down | Debug individual eval failures |
| **P2** | Pipelines List + DAG View | Understand system topology; diagnose failures |
| **P2** | Pipeline Run Trace | Debug specific pipeline execution failures |
| **P2** | Pipeline Metrics | Long-term stage health; identify bottlenecks |

### Phase 3: Advanced Features

| Priority | Page | Why |
|----------|------|-----|
| **P2** | Prompt Library | Prompt versioning and A/B testing for content quality |
| **P2** | Prompt Version Editor | Create/edit prompts without code deploys |
| **P3** | Rubrics Management | Fine-tune assessment criteria; requires deep domain knowledge |
| **P3** | Cohort Comparison | Compare cohort performance side-by-side |
| **P3** | Bulk User Operations | Efficient org administration for large teams |
| **P3** | Analytics Export | Offline analysis; reporting to stakeholders |
| **P3** | Learner-Admin Relationship Management | Coach/learner assignment workflow |

### Phase 4: Future (Backlog)

| Page | Notes |
|------|-------|
| Policy Layer UI | Sprint 13i (Policy Layer) not yet started; UI depends on backend policy definitions |
| OpenTelemetry Trace Explorer | Distributed tracing UI; depends on Tempo/Jaeger/Grafana stack deployment |
| Alerting and Notifications | Based on OpenTelemetry data; future sprint |

---

## Appendix: Component Hierarchy Suggestion

```
<AppShell>
  <TopBar>
    <DateRangePicker />
    <AdminUserMenu />
  </TopBar>
  <SideNav>
    <NavItem icon label="Overview" route="/admin" />
    <NavItem icon label="Users" route="/admin/users" />
    <NavItem icon label="Learners" route="/admin/learners" />
    <NavItem icon label="Analytics" route="/admin/analytics" />
    <NavItem icon label="Collections" route="/admin/collections" />
    <NavItem icon label="Evaluations" route="/admin/evaluations" />
    <NavItem icon label="Prompts" route="/admin/prompts" />
    <NavItem icon label="Pipelines" route="/admin/pipelines" />
    <NavItem icon label="Rubrics" route="/admin/rubrics" />
    <NavItem icon label="Audit Logs" route="/admin/audit" />
  </SideNav>
  <PageContent>
    <PageHeader title breadcrumb actions />
    <FiltersBar />
    <DataTable | CardGrid | Charts />
    <Pagination />
  </PageContent>
</AppShell>

Shared Components:
  <KPICard label value trend delta />
  <DataTable columns rows pagination sortable />
  <StatusBadge status />
  <DateRangePicker from to onChange />
  <SearchInput onSearch />
  <FilterDropdown options onChange />
  <Modal open onClose title>
    <Form>
    <FormActions />
  </Modal>
  <Drawer open onClose title>
    <DetailView />
  </Drawer>
  <Toast type="error|success" message />
  <SchemaViewer json />
  <DAGGraph nodes edges />
  <FlameChart stages />
  <LatencyHistogram data />
  <TrendChart data points />
```

---

## Appendix: Error Handling

All API errors follow the `AppError` shape from the backend:

```json
{
  "error": {
    "code": "SS-DOMAIN-003",
    "category": "DOMAIN",
    "message": "User was not found",
    "status_code": 404,
    "details": { "user_id": "abc123" }
  }
}
```

Frontend should:
- Map `error.category` to toast color/type
- Display `error.message` as primary text
- Show `error.code` as secondary/debug info
- Log `error.details` for support tickets
- 401/403 → redirect to login or show access denied
- Network errors → show "Connection error, please retry"

## Appendix: Mock Data Shapes

For frontend development before backend is ready, use these representative shapes:

**`AnalyticsOverviewView`** (mock):
```json
{
  "total_learners": 1247,
  "active_learners_30d": 834,
  "total_sessions": 18932,
  "total_attempts": 4521,
  "submitted_attempts": 4102,
  "validated_assessments": 3891,
  "rejected_assessments": 211,
  "avg_validated_score": 72.4,
  "overall_usage_trend": [
    { "bucket_date": "2026-03-01", "sessions_started": 142, "attempts_submitted": 38, "assessments_validated": 35, "assessments_rejected": 3 },
    { "bucket_date": "2026-03-02", "sessions_started": 158, "attempts_submitted": 44, "assessments_validated": 41, "assessments_rejected": 3 }
  ],
  "top_weak_skills": [
    { "skill_slug": "active-listening", "learner_count": 312 },
    { "skill_slug": "conflict-resolution", "learner_count": 287 }
  ],
  "cohort_breakdown": [
    { "cohort_key": "sales-team", "learner_count": 42 },
    { "cohort_key": "engineering", "learner_count": 89 }
  ],
  "provider_summary": [
    { "provider": "openrouter", "model_slug": "gpt-4o-mini", "call_count": 18432, "success_count": 18200, "failure_count": 232, "avg_latency_ms": 842.3 }
  ]
}
```

**`PipelineDAGView`** (mock):
```json
{
  "pipeline_name": "assistant_turn",
  "topology": "assistant_turn",
  "description": "Single assistant turn through input guard to runtime",
  "stages": [
    { "name": "input_guard", "kind": "GUARD", "dependencies": [], "runner_class": "InputGuardStage", "description": "Turn status check, cancellation handling" },
    { "name": "history_enrich", "kind": "ENRICH", "dependencies": ["input_guard"], "runner_class": "HistoryEnrichStage", "description": "Conversation history loading" },
    { "name": "profile_enrich", "kind": "ENRICH", "dependencies": ["input_guard"], "runner_class": "ProfileEnrichStage", "description": "Learner profile loading" },
    { "name": "progress_enrich", "kind": "ENRICH", "dependencies": ["input_guard"], "runner_class": "ProgressEnrichStage", "description": "Progression dashboard loading" },
    { "name": "attempts_enrich", "kind": "ENRICH", "dependencies": ["input_guard"], "runner_class": "AttemptsEnrichStage", "description": "Recent attempts loading" },
    { "name": "assistant_runtime", "kind": "AGENT", "dependencies": ["history_enrich", "profile_enrich", "progress_enrich", "attempts_enrich"], "runner_class": "AssistantRuntimeStage", "description": "Main LLM orchestrator with tool execution" }
  ]
}
```
