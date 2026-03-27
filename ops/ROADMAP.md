# SoftSkills Sprint Roadmap

This document is intentionally lightweight. It names each backend-oriented
sprint, states the purpose, and defines the exit bar. Detailed execution lives
in the linked sprint documents under `ops/sprints/`.

---

## Sprint 0: Canon Lock And Delivery Rules

**Purpose:** Freeze the MVP shape, contracts, and non-negotiable delivery rules from the constitution and spec canon.

**Key Outcomes:**
- MVP scope frozen
- Initial taxonomy and rubric set frozen
- Versioning and error/event conventions agreed
- Reusable backend definition of done and Stageflow baseline locked

**Exit Criteria:** The team can build without reopening core MVP semantics each week.

**Detail:** [ops/sprints/sprint-00-canon-lock.md](ops/sprints/sprint-00-canon-lock.md)

---

## Sprint 1: Foundation And Composition Root

**Purpose:** Establish the backend skeleton, dependency boundaries, persistence discipline, and observability primitives.

**Key Outcomes:**
- Service skeleton
- Migrations, shared schemas/errors
- Traces/logs/events
- Provider adapter boundaries
- Smoke harness baseline

**Exit Criteria:** New features can land on stable contracts and infrastructure instead of ad hoc setup.

**Detail:** [ops/sprints/sprint-01-foundation-and-composition-root.md](ops/sprints/sprint-01-foundation-and-composition-root.md)

---

## Sprint 2: Identity And Content Foundations

**Purpose:** Introduce users, profiles, taxonomy, rubrics, collections, prompts, and core content validation.

**Key Outcomes:**
- Account/profile APIs
- Seeded skill and competency model
- Rubric storage
- Content lifecycle
- Collection browse and draft authoring

**Exit Criteria:** The system can hold valid users and valid assessable content.

**Detail:** [ops/sprints/sprint-02-identity-and-content-foundations.md](ops/sprints/sprint-02-identity-and-content-foundations.md)

---

## Sprint 3: Quick Practice Vertical Slice

**Purpose:** Deliver the first complete text-first learner loop on the smallest viable practice mode.

**Key Outcomes:**
- Quick practice runtime
- Attempt lifecycle
- Validated marking
- Persisted assessment artifact
- Feedback delivery
- End-to-end traces

**Exit Criteria:** One trustworthy backend practice flow works from prompt delivery to scored result.

**Detail:** [ops/sprints/sprint-03-quick-practice-vertical-slice.md](ops/sprints/sprint-03-quick-practice-vertical-slice.md)

---

## Sprint 4: Scenario And Interview Runtime

**Purpose:** Extend the same trusted loop to richer text modes without weakening contracts or explainability.

**Key Outcomes:**
- Scenario and text interview runtime
- Richer content payloads
- Assessment reuse
- Regression coverage for expanded flows

**Exit Criteria:** All MVP text practice modes run on the same backend assessment backbone.

**Detail:** [ops/sprints/sprint-04-scenario-and-interview-runtime.md](ops/sprints/sprint-04-scenario-and-interview-runtime.md)

---

## Sprint 5: Progression And Recommendation V1

**Purpose:** Turn validated assessments into meaningful progress state and next-step guidance.

**Key Outcomes:**
- Skill progression
- Competency aggregation
- Explainable snapshots
- Recommendation service
- Replay-ready update path

**Exit Criteria:** The backend can explain where a learner stands and what they should practice next.

**Detail:** [ops/sprints/sprint-05-progression-and-recommendation-v1.md](ops/sprints/sprint-05-progression-and-recommendation-v1.md)

---

## Sprint 6: Creator Workflows And Discovery V1

**Purpose:** Make the catalog useful by supporting complete creator flows and trusted publish states.

**Key Outcomes:**
- Manual authoring maturity
- Structured generation
- Chat draft generation
- Publish states
- Verified vs. standard catalog behavior

**Exit Criteria:** The backend supports draft-to-published content creation without breaking content quality rules.

**Detail:** [ops/sprints/sprint-06-creator-workflows-and-discovery-v1.md](ops/sprints/sprint-06-creator-workflows-and-discovery-v1.md)

---

## Sprint 7: Admin Verification And Cohort Visibility

**Purpose:** Add the minimum operational and educational controls needed for a credible MVP.

**Key Outcomes:**
- Admin verification workflow
- Learner and cohort analytics
- Usage and trend views
- Replay and audit support

**Exit Criteria:** Admins can oversee trust, verify content, and inspect learner/cohort performance.

**Detail:** [ops/sprints/sprint-07-admin-verification-and-cohort-visibility.md](ops/sprints/sprint-07-admin-verification-and-cohort-visibility.md)

---

## Sprint 8: Hardening And Release Readiness

**Purpose:** Prove the backend MVP is coherent, traceable, and release-worthy.

**Key Outcomes:**
- Full backend regression coverage
- Real-provider smokes across core flows
- Docs sync
- Scope trim
- Release checklist

**Exit Criteria:** The core backend workflows are reliable enough for internal MVP release.

**Detail:** [ops/sprints/sprint-08-hardening-and-release-readiness.md](ops/sprints/sprint-08-hardening-and-release-readiness.md)

---

## Sprint 9: Generation Orchestration V1

**Purpose:** Replace the monolithic collection-generation call with a modular Stageflow-backed generation system and add prompt-item generation inside existing collections.

**Key Outcomes:**
- Existing-collection prompt-item generation endpoints
- Modular generation contracts, prompts, validators, and persistence
- Stageflow parent pipelines with child generation workers
- Manifest-style generation artifacts for multi-call workflows
- Real-provider coverage for the new generation surface

**Exit Criteria:** The backend can generate prompt items inside existing collections and generate collections through a modular, replayable, multi-call architecture without weakening validation or observability.

**Detail:** [ops/sprints/sprint-09-generation-orchestration-v1.md](ops/sprints/sprint-09-generation-orchestration-v1.md)

---

## Sprint 10: Chat Assistant And Streaming V1

**Purpose:** Deliver a Stageflow-orchestrated assistant runtime with durable chat state, WebSocket streaming, graceful cancellation, aggressive workflow parallelisation, and traceable tool-driven generation.

**Key Outcomes:**
- assistant session and turn runtime
- WebSocket event streaming for tool activity and response deltas
- graceful cancellation for active turns
- parallel Stageflow turn orchestration across independent stages
- read tools for collections and attempts
- generation tools backed by child subpipelines
- full trace, event, and replay coverage

**Exit Criteria:** The backend can run a replayable assistant turn that streams to the UI, uses tools safely, parallelises independent work, and preserves trace linkage through child generation workflows.

**Detail:** [ops/sprints/sprint-10-chat-assistant-and-streaming-v1.md](ops/sprints/sprint-10-chat-assistant-and-streaming-v1.md)

---

## Sprint 11: Org Enforcement

**Purpose:** Add organization-level enforcement, multi-tenancy boundaries, and role-based access control for enterprise readiness.

**Key Outcomes:**
- Organization-level isolation
- Role-based access control (admin, creator, learner)
- Org-scoped content and learner management
- Enforcement middleware

**Exit Criteria:** The backend can enforce organization boundaries and role-based permissions across all major workflows.

**Detail:** [ops/sprints/sprint-11-org-enforcement.md](ops/sprints/sprint-11-org-enforcement.md)

---

## Sprint 12: Collections Enhancement

**Purpose:** Extend collections with enhanced features including catalog generation improvements, content verification, and publishing workflows.

**Key Outcomes:**
- Enhanced catalog generation with structured output
- Collection verification workflow improvements
- Content quality gates
- Publishing automation

**Exit Criteria:** The backend supports enhanced collection management with improved generation and verification.

**Detail:** [ops/sprints/sprint-12-collections-enhancement.md](ops/sprints/sprint-12-collections-enhancement.md)

---

## Sprint 13: Admin Dashboard Backend Readiness (Split Into 9 Sprints)

Sprint 13 was too large and has been split into 9 focused sprints for better manageability:

### Sprint 13a: Event Logging Infrastructure
**Status:** Completed
**Detail:** [ops/sprints/sprint-13a-event-logging-infrastructure.md](ops/sprints/sprint-13a-event-logging-infrastructure.md)

**Key Outcomes:**
- Response delta aggregation (single record instead of per-token)
- HTTP request audit logging with field-level PII scrubbing
- Auth event logging (login success/failure, access denied)
- Typed error events (validation, authentication, authorization, not_found, rate_limited)
- Catalog generation lifecycle events
- Provider call enrichment with token counts and finish_reason

### Sprint 13b: Monitoring/Telemetry
**Status:** Not Started
**Detail:** [ops/sprints/sprint-13b-monitoring-telemetry.md](ops/sprints/sprint-13b-monitoring-telemetry.md)

### Sprint 13c: Agent Observability
**Status:** Not Started
**Detail:** [ops/sprints/sprint-13c-agent-observability.md](ops/sprints/sprint-13c-agent-observability.md)

### Sprint 13d: Pipeline Visualization
**Status:** Not Started
**Detail:** [ops/sprints/sprint-13d-pipeline-visualization.md](ops/sprints/sprint-13d-pipeline-visualization.md)

### Sprint 13e: Eval Dashboard
**Status:** Not Started
**Detail:** [ops/sprints/sprint-13e-eval-dashboard.md](ops/sprints/sprint-13e-eval-dashboard.md)

### Sprint 13f: Prompt Library API
**Status:** Not Started
**Detail:** [ops/sprints/sprint-13f-prompt-library-api.md](ops/sprints/sprint-13f-prompt-library-api.md)

### Sprint 13g: User Management API
**Status:** Not Started
**Detail:** [ops/sprints/sprint-13g-user-management-api.md](ops/sprints/sprint-13g-user-management-api.md)

### Sprint 13h: User Cohort Analytics
**Status:** Not Started
**Detail:** [ops/sprints/sprint-13h-user-cohort-analytics.md](ops/sprints/sprint-13h-user-cohort-analytics.md)

### Sprint 13i: Policy Layer
**Status:** Not Started
**Detail:** [ops/sprints/sprint-13i-policy-layer.md](ops/sprints/sprint-13i-policy-layer.md)

**Combined Exit Criteria:** The backend provides comprehensive event logging, observability infrastructure, and APIs sufficient for admin dashboard visibility.

---

## Rules For Using This Roadmap

- Frontend is intentionally omitted here and can move on its own cadence.
- Every sprint must update canonical documentation, add unit tests, add
  integration tests, and run backend smoke coverage with a real provider. If a
  sprint does not add a new provider-backed flow, the existing baseline smoke
  suite must still pass.
- `CONSTITUTION.yml` and the relevant `ops/mvp-spec/` files are mandatory input
  to sprint planning and sprint execution.
- If no repo-root `ROADMAP.md` exists, this file is the roadmap of record for backend sprint sequencing.
