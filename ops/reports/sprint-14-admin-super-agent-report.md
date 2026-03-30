# Sprint Execution Report: Sprint 14 - Admin Super Agent

> Project: SoftSkills
> Report Type: Sprint execution retrospective and delivery report
> Output Location: `ops/reports/sprint-14-admin-super-agent-report.md`
> Scope: Backend and platform execution only. Frontend work is tracked separately.

## Report Overview

- Sprint Name: Sprint 14 - Admin Super Agent
- Sprint Window: 2026-03-29 -> 2026-03-30
- Sprint Status: Completed
- Report Author: Assistant
- Related Sprint Doc: [sprint-14-admin-super-agent.md](/home/antonioborgerees/df/soft-skills/ops/sprints/sprint-14-admin-super-agent.md)
- Related Branch / PR: `sprint/14-admin-super-agent` / PR not opened in this session

## Source Docs Used

- [ops/CONSTITUTION.yml](/home/antonioborgerees/df/soft-skills/ops/CONSTITUTION.yml)
- [ops/sprints/sprint-14-admin-super-agent.md](/home/antonioborgerees/df/soft-skills/ops/sprints/sprint-14-admin-super-agent.md)
- [ops/mvp-spec/README.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/README.md)
- [ops/mvp-spec/foundational/stageflow-guide.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/foundational/stageflow-guide.md)
- [ops/mvp-spec/operations/admin-dashboard-readiness.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/operations/admin-dashboard-readiness.md)
- [ops/mvp-spec/TODO/admin-super-agent.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/TODO/admin-super-agent.md)
- [ops/mvp-spec/TODO/human-approval-workflows.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/TODO/human-approval-workflows.md)
- [ops/process/sprint-execution.md](/home/antonioborgerees/df/soft-skills/ops/process/sprint-execution.md)
- [ops/process/stageflow-reporting.md](/home/antonioborgerees/df/soft-skills/ops/process/stageflow-reporting.md)

## Sprint Summary

- Sprint Goal: Deliver a backend-usable admin investigation agent that answers read-only operational questions through one constrained SQL tool over admin-safe views.
- Actual Outcome: Sprint 14 shipped the admin-agent module, safe investigation views, SQL guard and executor, Stageflow pipeline, admin route, audit events, provider-backed smoke coverage, and canonical doc updates. Follow-up verification also uncovered and fixed adjacent admin-smoke regressions in user-management and analytics, and fixed the assistant generation child-subpipeline timeout path exposed by the broader sweep.
- Overall Result: The sprint goal was met. The admin-agent backend surface is complete for MVP, and the broader admin and assistant verification sweep now closes cleanly.

## Planned Vs Delivered

| Area | Planned | Delivered | Status | Notes |
| --- | --- | --- | --- | --- |
| Safe investigation data surface | Add allowlisted `admin_agent_*` views with org scoping and PII-safe shaping | Added admin-safe investigation views for assistant sessions, workflow events, pipeline runs, provider calls, and evaluation runs | Done | Delivered through migration `20260329_0021` |
| Admin-agent contracts and execution path | Add typed contracts, SQL tool, Stageflow workflow, and `POST /admin-agent/chat` | Added contracts, schema registry, SQL guard, scoped executor, Stageflow orchestration, and admin chat route | Done | Read-only tool remains auto-allowed for MVP |
| Security and observability | Enforce view allowlist, row/time bounds, org scoping, and replayable audit events | Added validator, org-scoped execution, response shaping, and `admin.agent.*` event persistence | Done | Observability now explains successful and denied queries |
| Verification | Add unit, integration, and real-provider smoke coverage | Added targeted tests plus `admin-agent` real-provider smoke | Done | Smoke strengthened after first live run exposed zero-row nondeterminism |
| Documentation | Update sprint doc, roadmap, and canonical admin-agent docs | Updated sprint doc, roadmap, TODO spec, and Stageflow reporting | Done | Report added here as final closeout artifact |
| Broader admin and assistant follow-up verification | Run adjacent suites and address regressions discovered after core sprint completion | Fixed admin user-management event-order locking, fixed analytics export smoke hang, fixed assistant generation child-wrapper timeout, and reran broader admin and assistant smokes | Done | Admin and assistant follow-up smokes now pass |

## Key Outcomes

- `POST /api/admin-agent/chat` now supports read-only investigative questions for org admins.
- The admin-agent is constrained to allowlisted admin-safe SQL views and never queries raw base tables.
- Query planning, execution, and response completion are auditable through structured `admin.agent.*` workflow events.
- The real-provider `admin-agent` smoke now proves non-zero investigative rows against seeded safe views.
- Follow-up admin verification improved by fixing a SQLite lock in user-management event recording and replacing an unnecessary analytics export `StreamingResponse` with direct `Response` objects.

## What Worked Well

- The Stageflow split of guard, enrich, planning, execution, and response stages kept the admin-agent flow easy to reason about.
- The SQL security boundary lived in code and schema metadata rather than in prompt wording, which kept the trust model defensible.
- Provider-backed smoke coverage exposed real operational issues quickly, especially around timeout sizing and nondeterministic agent prompts.
- The existing smoke harness made it straightforward to broaden verification into adjacent admin and assistant surfaces after the core sprint landed.

## Challenges And Friction

- **Initial live admin-agent smoke was too open-ended**
  - Root cause: the prompt allowed the provider to choose a syntactically valid but operationally useless zero-row investigation.
  - Impact: the first smoke passed transport and planning, but did not prove the intended admin-safe view path.
  - Fix: seeded explicit investigation rows and constrained the smoke question to `admin_agent_assistant_sessions_v`.

- **Cross-session event persistence locked SQLite in admin user management**
  - Root cause: `add_user_to_org()` flushed a new user in one session and wrote a workflow event through a second session before the first transaction committed.
  - Impact: broader admin smoke verification failed with `database is locked`.
  - Fix: deferred `identity.user_registered.v1` emission until after the owning transaction committed.

- **Analytics export endpoint hung under in-process smoke transport**
  - Root cause: the endpoint materialized the full payload and still wrapped it in `StreamingResponse`.
  - Impact: admin analytics smoke timed out on export verification.
  - Fix: returned plain `Response` objects for both JSON and CSV exports.

- **Assistant generation child wrapper inherited the default 30-second Stageflow budget**
  - Root cause: the tool-layer `run_logged_subpipeline(...)` wrapper around `generate_collection` did not set an explicit timeout even though the parent assistant turn and the inner catalog generation service both had larger budgets.
  - Impact: broader assistant generation verification failed at roughly 30 seconds with `SS-ORCHESTRATION-204`.
  - Fix: aligned the assistant tool subpipeline wrapper timeout with the catalog generation service budget and required completed turn status in the smoke assertion.

## Constitution Conformance

- Competency growth: The sprint adds an admin operational investigation surface, not a learner-facing loop change, but it supports the core loop indirectly by making runtime, evaluation, and assistant behavior diagnosable.
- Schema validation: Request and response boundaries are typed for admin-agent chat, SQL planning output, and SQL tool results.
- Fail-fast behavior: Disallowed SQL, missing org context, invalid view access, and provider planning failures stop the workflow with explicit error codes.
- Explainability: The response includes source views, row counts, SQL audit metadata, and replayable workflow events sufficient to explain what happened.
- Observability: The sprint emits `admin.agent.request.received.v1`, `admin.agent.context.loaded.v1`, `admin.agent.plan.generated.v1`, `admin.agent.query.executed.v1`, `admin.agent.query.denied.v1`, and `admin.agent.response.completed.v1`.
- Persistence: Safe investigation views, workflow events, provider calls, and pipeline runs are all persisted and queryable through the admin-safe layer.
- Modularity: Route, contracts, domain schema registry, SQL validation, SQL execution, repository, and Stageflow orchestration are separated cleanly.
- No silent fallback: Unsafe SQL is denied, provider planning is typed, and the smoke now fails if the provider returns zero investigative rows against seeded data.

## Testing And Verification

- Unit Tests:
  - `tests/unit/test_admin_agent_sql.py`
  - `tests/unit/test_admin_user_management.py`
  - `tests/unit/test_assistant_runtime.py`
  - Latest targeted run: `45 passed in 1.80s`

- Integration Tests:
  - `tests/integration/test_admin_agent_api.py`
  - Admin-agent integration assertions cover org scoping, audit events, allowlisted SQL execution, and denial paths.

- Smoke Tests With Real Provider:
  - `admin-agent`: passed after strengthening seed data and prompt constraints
    - returned `session_row_count=2`
    - used `admin_agent_assistant_sessions_v`
  - `assistant-read-runtime`: passed
  - `assistant-generation-runtime`: passed after aligning the assistant tool child-subpipeline timeout with the catalog generation runtime budget

- Broader Admin Smokes:
  - `admin-user-management`: passed after fixing transaction ordering and removing the smoke’s duplicate membership step
  - `admin-analytics`: passed after replacing materialized streaming exports with direct responses
  - `admin-telemetry`: passed with network access

- Failure Path Coverage:
  - unsafe raw-table SQL denied
  - unexpected source-view usage and zero-row live admin-agent smoke outputs now fail explicitly
  - admin user add flow no longer locks SQLite on event write ordering
  - assistant generation no longer dies at the child wrapper's default 30-second timeout

- Manual Verification:
  - route wiring, container wiring, smoke registry registration, and roadmap/sprint doc updates were checked directly in the repo

## Documentation Updates

- [ops/sprints/sprint-14-admin-super-agent.md](/home/antonioborgerees/df/soft-skills/ops/sprints/sprint-14-admin-super-agent.md): marked complete and recorded delivered scope
- [ops/ROADMAP.md](/home/antonioborgerees/df/soft-skills/ops/ROADMAP.md): Sprint 14 marked completed
- [ops/mvp-spec/TODO/admin-super-agent.md](/home/antonioborgerees/df/soft-skills/ops/mvp-spec/TODO/admin-super-agent.md): implementation status added
- [ops/process/stageflow-reporting.md](/home/antonioborgerees/df/soft-skills/ops/process/stageflow-reporting.md): new findings added for transaction ordering and deterministic agent smokes
- [ops/reports/sprint-14-admin-super-agent-report.md](/home/antonioborgerees/df/soft-skills/ops/reports/sprint-14-admin-super-agent-report.md): this final execution report

## Stageflow Usage And Reporting

- Stageflow Used: Yes
- Relevant Features Used: multi-stage pipeline orchestration, typed planning output, logged runs, workflow event correlation, request/trace/workflow IDs, and approval-ready tool infrastructure with an auto-allowed read-only SQL tool
- What Worked: The explicit Stageflow stage boundaries made security review and observability straightforward.
- What Hurt: Provider-backed agent smokes are only useful when the seeded data and prompt wording prove the exact tool/view path the sprint introduced.
- Follow-Up Logged In `ops/process/stageflow-reporting.md`: Yes

## Technical And Architectural Debt

| Debt Item | Type | Why It Exists | Impact | Recommended Follow-Up | Owner |
| --- | --- | --- | --- | --- | --- |
| Cross-session event persistence ordering | Architectural | Workflow events are still persisted through separate repository sessions rather than a shared unit-of-work | SQLite and test environments are sensitive to transaction ordering mistakes | Introduce an outbox or shared write unit for mutating workflows | Backend |
| Tool-layer child pipeline budgets are easy to miss | Architectural | Parent, wrapper, and inner Stageflow pipelines each need explicit timeout treatment | Long-running provider-backed child tools can fail at an intermediate wrapper boundary | Standardize timeout propagation helpers for subpipeline wrappers | Backend |

## Open Risks

| Risk | Severity | Why It Matters | Mitigation | Carry To Next Sprint |
| --- | --- | --- | --- | --- |
| SQL validator bypass in future query shapes | High | The admin-agent trust boundary is the validator and safe views, not the prompt | Keep allowlist strict, expand denial tests, and avoid widening SQL surface casually | Yes |
| PII leakage through future view expansion | High | New admin-safe views could weaken the current redaction boundary if not reviewed carefully | Keep safe-view design explicit and require layered redaction checks | Yes |

## Deferred Work

- Frontend admin investigation UI for `POST /api/admin-agent/chat`
- Saved and curated admin investigations or reports
- Approval-gated write tools beyond the MVP read-only SQL tool

## Retrospective

- Stop: Treating open-ended provider-backed agent prompts as sufficient smoke coverage when the goal is to prove a specific tool contract.
- Start: Seeding explicit live-smoke fixtures that guarantee a meaningful non-zero result for the intended investigative view.
- Continue: Using Stageflow and structured workflow events as first-class design tools rather than bolting observability on after the fact.

## Next Sprint Recommendations

1. Build the frontend admin investigation surface on top of `POST /api/admin-agent/chat`.
2. Add saved/admin-curated investigations and reusable reporting flows.
3. Standardize timeout propagation for long-running tool-spawned child pipelines.

## Sign-Off

- Report Status: Final
- Reviewed By: Pending
- Review Date: 2026-03-30

---

Checklist:

- [x] Outcomes are recorded honestly
- [x] Constitution conformance is assessed explicitly
- [x] Testing and smoke status is documented
- [x] Debt and risks are captured
- [x] Follow-ups for next sprint are clear
- [x] Report is saved in `ops/reports/`
