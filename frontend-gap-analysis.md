# Frontend Gap Analysis

## Overview

Comparison of `ops/mvp-spec/` against `frontend-drafts/frontend-opus/` to identify
missing frontend functionality required for MVP completeness.

## What Exists

The current frontend has a solid foundation:

- **Design system**: Primitives (Button, Card, Badge, Input, Skeleton, Avatar,
  ProgressBar) and patterns (PageShell, StatCard, EmptyState, ErrorState,
  LoadingState)
- **Theme system**: Three themes (obsidian, chalk, verdant) with persistence
- **Layout**: Sidebar + TopBar shell with collapsible navigation
- **Routing**: Five routes configured (Dashboard, Practice, Collections,
  Progress, Settings)
- **Pages**: All five pages exist but are entirely static with hardcoded data

## What Is Missing

### P0 — Core Practice Loop (must have)

These are the pages/flows that make the product work. Without them, the
platform cannot deliver its core value.

#### 1. Practice Session View

No session UI exists. Clicking "Start Practice" or "Begin Scenario" leads
nowhere. The spec requires a full practice flow for each mode.

Needed:

- Session container with step/turn progression indicator
- Prompt display with context, scenario details, and supporting artifacts
- Text input area for learner responses
- Submit and end-session controls
- Timer display (session duration)
- Loading/assessment-pending state while AI scores
- Session completion screen with score reveal

**Spec references**: `PRD.md:209-246`, `product-spec.md:89-109`,
`domain-model.md:75-88`

#### 2. Interview Simulation Flow

A multi-turn interview experience with follow-up probing.

Needed:

- Question display with competency context
- Follow-up question generation after each answer
- Turn-by-turn history within the session
- Final summary after all questions complete

**Spec references**: `PRD.md:212-221`, `product-spec.md:92-94`

#### 3. Scenario Practice Flow

A multi-step scenario with stakeholder context and artifacts.

Needed:

- Scenario context panel (business context, constraints, objectives)
- Mock company and mock person display
- Supporting artifact rendering (emails, reports, messages)
- Multi-step progression within one scenario
- Stakeholder actor information cards

**Spec references**: `PRD.md:223-231`, `content-system.md:36-48`,
`domain-model.md:59-72`

#### 4. Quick Practice Flow

Short single-response practice.

Needed:

- Single prompt display
- Text response input
- Immediate scoring feedback

**Spec references**: `PRD.md:233-236`, `product-spec.md:101-103`

#### 5. Assessment & Feedback Screen

No feedback display exists. After submission, the user has no way to see
their score or learn from the attempt.

Needed:

- Overall score display
- Skill-level score breakdown with visual bars
- Evidence excerpts from the learner's response
- Rationale tied to rubric dimensions
- Strengths section
- Weaknesses/areas for improvement section
- Suggested next actions
- Link to attempt history
- Option to retry or move to next recommended practice

**Spec references**: `PRD.md:271-288`, `assessment-and-progression.md:21-49`,
`marking-engine.md:80-100`

#### 6. Attempt History View

No way to review past attempts. The "Review" buttons on Dashboard and
Practice pages are non-functional.

Needed:

- Chronological list of attempts with score, date, type, and linked skills
- Ability to drill into any past attempt and see the full feedback
- Filter by practice mode, skill, date range

**Spec references**: `PRD.md:497`, `domain-model.md:79-83`

### P1 — User Onboarding & Profile

#### 7. Onboarding Flow

No onboarding exists. New users land directly on Dashboard with no context.

Needed:

- Goal selection screen (what are you practicing for?)
- Target role selection (consultant, tech lead, graduate, etc.)
- Practice preference setup (session length, focus areas)
- Brief explanation of skills vs competencies
- Initial skill assessment or skip option

**Spec references**: `PRD.md:414-416`, `product-spec.md:66-67`,
`technical-architecture.md:37-39`

#### 8. Profile & Account Management

Settings page only has theme switching.

Needed:

- Edit name, email, avatar
- Update goals and target role
- Practice preferences (session length, notification settings)
- Account security (password change if applicable)

**Spec references**: `PRD.md:481-483`, `product-spec.md:66`

### P2 — Progress & Dashboards

#### 9. Enhanced Progress Page

Current Progress page shows 2 hardcoded competency cards with 3 skills each.
The spec defines 8 competencies and 10 skills with confidence tracking.

Needed:

- All 8 MVP competencies with their mapped skills
- Time-series chart or timeline showing progression over time
- Confidence indicator per skill (Low/Medium/High or numeric)
- Evidence count and recency per skill
- Drill-down from competency to constituent skills
- Strongest/weakest skill indicators
- Trend indicators (improving, stagnating, declining)

**Spec references**: `PRD.md:343-348`, `soft-skill-progression.md:26-51`,
`assessment-and-progression.md:63-83`

#### 10. Enhanced Dashboard

Current Dashboard uses hardcoded stats. Needs to reflect real data.

Needed:

- Live streak data
- Real recommendation from the recommendation engine (with reason codes)
- Real recent activity linked to attempt history
- Actual skill gaps with evidence-backed scores
- Recommended next practice with reason display
- Competency progress overview (3/8 shown but needs real data)

**Spec references**: `PRD.md:337-348`, `soft-skill-recommendation.md:40-57`

### P3 — Content Authoring

#### 11. Content Creation Pages

No authoring UI exists at all. The spec requires three creation flows.

Needed:

- Manual collection editor (title, description, audience, difficulty, skill
  mapping, item creation)
- Structured generation form (constrain AI generation by audience, domain,
  difficulty, scenario type, skill targets)
- Chat-based generation interface (natural language prompt input, draft
  preview, edit before publish)
- Draft management (list drafts, edit, delete)
- Publication workflow (save private, publish public, submit for verification)
- Item editor within a collection (prompt text, linked skills, rubric type,
  supporting artifacts)

**Spec references**: `PRD.md:314-323`, `content-system.md:50-68`,
`product-spec.md:127-131`

#### 12. Mock Company & Mock Person Management

No mock entity creation UI.

Needed:

- Create/edit mock companies (name, industry, context, size)
- Create/edit mock people (name, role, communication style, goals,
  relationship to scenario)
- Link mock entities to scenarios
- Browse/manage existing mock entities

**Spec references**: `PRD.md:298-300`, `domain-model.md:64-72`,
`content-system.md:36-48`

#### 13. Collection Detail & Management

No way to view a collection's contents or manage it.

Needed:

- Collection detail page (items list, metadata, author info, verification
  status)
- Browse items within a collection
- Edit collection metadata (if author)
- Add/remove items from a collection
- Collection verification status display

**Spec references**: `content-system.md:20-33`, `domain-model.md:52-58`

### P4 — Community & Discovery

#### 14. Search & Filtering

Collections page has non-functional Search and Filter buttons.

Needed:

- Search across collections by title, description, tags
- Filter by difficulty, skill, competency, format, verified status
- Sort by rating, recency, item count

**Spec references**: `PRD.md:487-489`, `content-system.md:97-103`

#### 15. Save & Upvote System

No way to save collections or upvote content.

Needed:

- Save collection to personal library
- Upvote useful collections
- View saved collections
- Browse public content

**Spec references**: `PRD.md:328-335`, `PRD.md:517-519`

### P5 — Admin & Educator

#### 16. Admin Dashboard

No admin views exist.

Needed:

- Learner activity overview
- Cohort performance summary
- Weak skill identification across learners/cohort
- Collection usage analytics
- Assessment trend views
- Trace-linked diagnostic metadata viewer

**Spec references**: `PRD.md:350-360`, `PRD.md:460-464`,
`product-spec.md:120-124`

#### 17. Content Verification Queue

No admin content management.

Needed:

- View pending user-created public collections
- Verify/reject collections
- Verified collection browsing
- Content quality overview

**Spec references**: `content-system.md:70-78`, `domain-model.md:129-133`

### P6 — Cross-Cutting

#### 18. API Integration Layer

No fetch calls, no API client, no data fetching patterns.

Needed:

- API client abstraction (fetch/axios wrapper)
- Request/response type definitions matching backend schemas
- Error handling aligned with the error taxonomy
- Auth token management
- Loading/error state patterns for all data views

**Spec references**: `technical-architecture.md:73-88`,
`observability-and-operations.md:80-109`

#### 19. State Management

No global state beyond theme. No data stores.

Needed:

- User/auth state
- Practice session state (current attempt, turn history, scoring pending)
- Progress data store
- Content/collection cache
- Recommendation state

**Spec references**: `technical-architecture.md:95-101`

#### 20. Auth Pages

No login, signup, or auth flow.

Needed:

- Login page
- Signup page
- Password reset (if applicable)
- Auth guards on protected routes
- Role-based route access (user vs admin)

**Spec references**: `PRD.md:481`, `product-spec.md:148-151`

#### 21. Notifications

TopBar has a bell icon with a static indicator dot.

Needed:

- Notification list dropdown/panel
- Notification types (assessment complete, recommendation ready, collection
  verified, etc.)
- Mark as read
- Notification preferences in settings

**Spec references**: `PRD.md:337-348` (implied by recommendation + dashboard)

#### 22. Error Handling & Empty States

ErrorState and EmptyState primitives exist but are not used anywhere.

Needed:

- Empty states for: no attempts yet, no collections found, no
  recommendations, no progress data
- Error states for: API failures, assessment failures, content load failures
- Retry mechanisms wired to actual API calls

**Spec references**: `observability-and-operations.md:80-109`,
`technical-architecture.md:127-136`

## Priority Summary

| Priority | Category | Items |
| --- | --- | --- |
| P0 | Core practice loop | Session view, 3 practice modes, feedback, attempt history |
| P1 | Onboarding & profile | Onboarding flow, profile management |
| P2 | Progress & dashboards | Enhanced progress page, real dashboard data |
| P3 | Content authoring | Creation flows, mock entities, collection management |
| P4 | Community | Search/filter, save/upvote |
| P5 | Admin | Admin dashboard, verification queue |
| P6 | Cross-cutting | API layer, state management, auth, notifications, error states |
