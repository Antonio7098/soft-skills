# MVP Roadmap

Backend-first roadmap for delivering the SoftSkills MVP defined in `docs/`.

## 0. Canon Lock

- [ ] Confirm `docs/` as the active MVP source of truth for implementation decisions
- [ ] Freeze initial MVP skill and competency framework
- [ ] Freeze initial rubric set and versioning strategy
- [ ] Freeze initial content types for MVP: collections, interview prompts, scenario prompts, quick practice prompts
- [ ] Define MVP acceptance criteria for the core loop: practice -> assess -> reflect -> progress -> repeat

## 1. Backend Foundation

- [ ] Initialize backend service with FastAPI, typed settings, and environment configuration
- [ ] Establish repository structure for `api`, `domain`, `application`, `orchestration`, `persistence`, `schemas`, `prompts`, and `observability`
- [ ] Enable strict typing, linting, formatting, and test tooling
- [ ] Define explicit interfaces and dependency injection patterns for services, repositories, provider adapters, and infrastructure clients
- [ ] Define base Pydantic request and response conventions
- [ ] Define base error envelope and stable error code strategy
- [ ] Implement structured logging with correlation IDs
- [ ] Implement trace and event primitives for all major workflows
- [ ] Set up SQLAlchemy models and Alembic migration workflow
- [ ] Keep database access behind repository or adapter interfaces so database backends can be swapped without domain rewrites
- [ ] Add health and readiness endpoints

## 2. Identity And Profile Backend

- [ ] Implement user account model and authentication flow
- [ ] Define an auth provider interface and dependency injection boundary for auth flows
- [ ] Ensure in-house auth, Google, Clerk, or another provider can be added via adapters and configuration rather than application rewrites
- [ ] Implement learner profile model with goals, target role, and preferred practice areas
- [ ] Implement authorization model with standard user accounts plus admin
- [ ] Ensure any authenticated user can author collections without a separate creator role
- [ ] Add API contracts for account creation, login, profile read, and profile update
- [ ] Add tests for auth flows, profile validation, role enforcement, and provider adapter behavior

## 3. Domain And Content Backend

- [ ] Implement core domain models for skills, competencies, rubrics, collections, scenarios, mock companies, mock people, prompt items, attempts, assessments, and progress history
- [ ] Encode domain invariants from `docs/domain-model.md`
- [ ] Implement versioned rubric storage and retrieval
- [ ] Implement collection and content item persistence
- [ ] Implement content lifecycle states: draft, review, published private, published public, archived
- [ ] Implement collection verification states: unverified, verified, rejected
- [ ] Implement APIs for browsing collections with filtering by difficulty, skill, competency, format, and verification status
- [ ] Implement APIs for user-authored content CRUD
- [ ] Implement validation that all assessable items map to skills and a rubric
- [ ] Ensure domain and application layers remain database-agnostic behind persistence interfaces
- [ ] Add tests for content validation, lifecycle transitions, verification transitions, and filtering

## 4. Practice Runtime Backend

- [ ] Implement session start workflow for interview, scenario, and quick practice modes
- [ ] Implement prompt delivery contracts for each practice mode
- [ ] Implement attempt submission endpoint and persistence flow
- [ ] Implement attempt state transitions: started, submitted, assessment pending, assessed, assessment failed
- [ ] Persist all attempt metadata required for replay and diagnostics
- [ ] Emit structured events for session start, prompt delivery, and attempt submission
- [ ] Add tests for session flows, attempt persistence, and invalid state transitions

## 5. Assessment Pipeline Backend

- [ ] Define typed assessment input and output schemas
- [ ] Implement prompt contract versioning and model metadata capture
- [ ] Implement Stageflow-based assessment orchestration
- [ ] Validate all LLM outputs before use or persistence
- [ ] Reject malformed, partial, or contradictory assessment artifacts
- [ ] Persist validated assessment outputs with rubric version, prompt version, model slug, provider, and trace linkage
- [ ] Generate learner-facing feedback with strengths, weaknesses, evidence, and next actions
- [ ] Add benchmark fixtures for scoring consistency checks
- [ ] Add tests for success, validation failure, provider failure, retry behavior, and trace emission
- [ ] Add smoke tests for complex assessment and generation flows using real provider calls, not mocks

## 6. Progress And Recommendation Backend

- [ ] Implement skill progression aggregation from validated assessments only
- [ ] Implement competency progression derived from weighted skill evidence
- [ ] Track proficiency separately from confidence internally
- [ ] Prevent one-off attempts from causing inflated level changes
- [ ] Implement recommendation logic based on weak skills, stagnation, and learner goals
- [ ] Implement dashboard aggregation services for learner progress history
- [ ] Add tests for progression math, versioned recalculation, and recommendation rules

## 7. Admin And Content Backend

- [ ] Implement admin APIs for learner progress views
- [ ] Implement cohort-level analytics APIs
- [ ] Implement collection usage and assessment trend APIs
- [ ] Implement user authoring workflows for manual, structured generation, and chat-based draft generation
- [ ] Implement admin verification workflow to elevate user-created collections
- [ ] Add tests for admin visibility boundaries, user authoring permissions, and verification rules

## 8. Observability And Operational Backend

- [ ] Finalize structured event taxonomy for MVP workflows
- [ ] Finalize error taxonomy across validation, domain, scoring, orchestration, provider, persistence, auth, and UI-facing API errors
- [ ] Ensure every critical workflow emits end-to-end traces
- [ ] Store replayable artifacts for assessment-critical workflows
- [ ] Implement monitoring for validation failures, prompt failures, retry rates, and incomplete trace coverage
- [ ] Add operational dashboards or queries for core trust metrics
- [ ] Document prompt lifecycle, rubric lifecycle, and migration discipline
- [ ] Document which complex flows require non-negotiable real-provider smoke tests before release

## 9. Backend Hardening

- [ ] Complete deterministic domain tests for core business logic
- [ ] Complete FastAPI contract tests for core endpoints
- [ ] Complete persistence tests for critical models and migrations
- [ ] Complete orchestration tests for success and failure paths
- [ ] Complete regression coverage for scoring semantics and artifact compatibility
- [ ] Run smoke tests for complex flows against real auth providers, real model providers, and the target database stack where applicable
- [ ] Verify no critical workflow relies on silent fallbacks
- [ ] Verify no critical workflow can complete without versioned metadata
- [ ] Verify infrastructure dependencies are composed through interfaces and dependency injection rather than direct vendor coupling
- [ ] Mark backend MVP core loop as feature-complete

## 10. Frontend Foundation

- [ ] Initialize frontend app with React, Vite, strict TypeScript, and test setup
- [ ] Establish feature-oriented structure plus shared design system foundations
- [ ] Define design tokens for color, spacing, typography, and motion
- [ ] Implement reusable primitives for layout, text, buttons, forms, cards, and feedback states
- [ ] Implement typed API client layer matching backend contracts
- [ ] Implement global app shell, routing, and session handling
- [ ] Implement consistent loading, error, empty, and success states

## 11. Learner Frontend

- [ ] Implement onboarding flow for goals, target role, and practice preferences
- [ ] Implement collection browsing and filtering UI
- [ ] Implement collection detail and practice entry surfaces
- [ ] Implement interview practice UI
- [ ] Implement scenario practice UI
- [ ] Implement quick practice UI
- [ ] Implement attempt submission and assessment result surfaces
- [ ] Implement feedback view with score breakdown, evidence, strengths, weaknesses, and next steps
- [ ] Implement learner dashboard for recent activity, skill progression, competency progression, and recommended next practice
- [ ] Ensure async states always show visible progress and never blank waiting states

## 12. Content And Admin Frontend

- [ ] Implement content authoring workspace for authenticated users
- [ ] Implement structured generation form UI
- [ ] Implement chat-based content draft generation UI
- [ ] Implement publish and verification status flow
- [ ] Implement admin dashboard for learner and cohort insight
- [ ] Implement admin views for weak-skill analysis, collection usage, assessment trends, and collection verification
- [ ] Enforce frontend visibility rules for privileged data access

## 13. Frontend Hardening

- [ ] Add tests for critical learner flows
- [ ] Add tests for typed API integrations and failure states
- [ ] Add tests for content authoring and admin workflows
- [ ] Verify consistency of interaction patterns across similar surfaces
- [ ] Verify loading and transition behavior meets the “app must feel alive” requirement
- [ ] Mark frontend MVP surfaces as feature-complete

## 14. MVP Integration And Release Readiness

- [ ] Run end-to-end tests for the full learner core loop
- [ ] Run end-to-end tests for user draft-to-verified-collection flow
- [ ] Run end-to-end tests for admin progress visibility flow
- [ ] Run non-negotiable smoke tests for all complex provider-backed flows using real provider calls before release
- [ ] Verify trace coverage across practice, assessment, progress, generation, and recommendation workflows
- [ ] Verify all persisted assessment artifacts include rubric version, prompt version, model slug, provider, and trace ID
- [ ] Verify auth providers can be swapped through adapter wiring without core application changes
- [ ] Verify database backends can be swapped through persistence adapters without domain rewrites
- [ ] Verify documentation matches implemented behavior
- [ ] Review scope against MVP exclusions and remove non-essential work
- [ ] Prepare release notes or equivalent MVP change summary
- [ ] Declare MVP ready for internal use
