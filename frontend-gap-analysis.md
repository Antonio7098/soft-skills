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

### P0 — Core Practice Loop (must have) ✅ **COMPLETED**

These are the pages/flows that make the product work. Without them, the
platform cannot deliver its core value.

#### 1. Practice Session View ✅

**Implemented**: Full session container with step/turn progression, timer, prompt display, response input, and completion screen.

**Components added**:
- `SessionShell` - Layout with header, timer, step indicator, and end button
- `PromptDisplay` - Shows prompt text, context, difficulty, and skill tags
- `ResponseInput` - Textarea with character count and submit controls
- `AssessingOverlay` - Loading state while AI evaluates responses
- `SessionComplete` - Score reveal and next actions
- `useSessionTimer` - Hook for elapsed time tracking

**Routes**: `/session/quick/:promptId`, `/session/interview/:promptId`, `/session/scenario/:scenarioId`

**Completed**: 2025-03-25

**Spec references**: `PRD.md:209-246`, `product-spec.md:89-109`,
`domain-model.md:75-88`

#### 2. Interview Simulation Flow ✅

**Implemented**: Multi-turn interview with competency context, follow-up questions, and turn history.

**Features**:
- 3-turn interview flow with simulated follow-up questions
- Turn-by-turn history display showing previous Q&A pairs
- Competency context for each question
- Final assessment after all turns complete

**Mock logic**: Generates realistic follow-ups and stores turn history in memory.

**Completed**: 2025-03-25

**Spec references**: `PRD.md:212-221`, `product-spec.md:92-94`

#### 3. Scenario Practice Flow ✅

**Implemented**: Multi-step scenario with stakeholder context, company info, and step-by-step progression.

**Features**:
- Context sidebar with company details, objectives, constraints, tensions
- Stakeholder cards showing person info, communication style, and goals
- 3-step scenario progression with contextual prompts
- Step history showing previous responses

**Mock logic**: Uses first available scenario with realistic step prompts.

**Completed**: 2025-03-25

**Spec references**: `PRD.md:223-231`, `content-system.md:36-48`,
`domain-model.md:59-72`

#### 4. Quick Practice Flow ✅

**Implemented**: Single-prompt practice with immediate feedback.

**Features**:
- Single prompt display with difficulty and skills
- Text response input with minimum character validation
- Immediate scoring and assessment after submission
- Session completion screen with score and retry option

**Completed**: 2025-03-25

**Spec references**: `PRD.md:233-236`, `product-spec.md:101-103`

#### 5. Assessment & Feedback Screen ✅

**Implemented**: Comprehensive feedback view with score breakdown, evidence, and actionable insights.

**Components added**:
- `ScoreBreakdown` - Overall score ring, skill scores with rationale
- `EvidenceList` - Quoted excerpts with explanations and skill tags
- `FeedbackSection` - Strengths, weaknesses, and next actions in 3-column layout

**Route**: `/assessment/:attemptId`

**Features**:
- Visual score ring with color-coded performance
- Skill-level breakdown with progress bars
- Evidence excerpts pulled from user responses
- Structured feedback with strengths/weaknesses/actions

**Completed**: 2025-03-25

**Spec references**: `PRD.md:271-288`, `assessment-and-progression.md:21-49`,
`marking-engine.md:80-100`

#### 6. Attempt History View ✅

**Implemented**: Filterable chronological list of all attempts with drill-down to feedback.

**Components added**:
- `AttemptListItem` - Card with score ring, metadata, and review button
- `HistoryFilters` - Search and practice type filtering

**Route**: `/history`

**Features**:
- List view with score rings, dates, skills, and practice types
- Search by title/skills, filter by practice mode
- Click any attempt to view full assessment
- Empty state when no attempts exist

**Completed**: 2025-03-25

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
| P0 ✅ | Core practice loop | Session view, 3 practice modes, feedback, attempt history |
| P1 | Onboarding & profile | Onboarding flow, profile management |
| P2 | Progress & dashboards | Enhanced progress page, real dashboard data |
| P3 | Content authoring | Creation flows, mock entities, collection management |
| P4 | Community | Search/filter, save/upvote |
| P5 | Admin | Admin dashboard, verification queue |
| P6 | Cross-cutting | API layer, state management, auth, notifications, error states |

---

## Implementation Summary

### Completed (2025-03-25)

**P0 Core Practice Loop - Fully Implemented**

All 6 core practice loop features are now functional with a complete end-to-end user experience:

1. **Practice Session View** - Full session container with timer, step progression, and responsive layout
2. **Interview Simulation** - Multi-turn flow with follow-up questions and turn history
3. **Scenario Practice** - Multi-step scenarios with stakeholder context and company information
4. **Quick Practice** - Single-prompt flow with immediate feedback
5. **Assessment & Feedback** - Comprehensive feedback with score breakdown, evidence, and actionable insights
6. **Attempt History** - Filterable list with drill-down to full assessments

**Design System Enhancements**
- Added `Textarea` primitive for multi-line input
- Added `ScoreRing`, `StepIndicator`, `SectionHeader` patterns
- Extended variant helpers for domain difficulty and score mapping

**Data Layer**
- Added `InterviewSessionView` and `ScenarioSessionView` types
- Extended `DataProvider` interface with interview/scenario methods
- Implemented mock providers with realistic session simulation
- Added session state management and turn/step tracking

**Architecture**
- Session routes under `SessionLayout` (no sidebar for focused practice)
- Assessment and history routes under main layout
- Component reuse maximized across all practice modes
- Centralized styling with theme tokens and Tailwind CSS

**Navigation & UX**
- All "Start Practice" buttons now navigate to appropriate sessions
- "Review" buttons navigate to attempt history
- Dashboard buttons link to practice and history pages
- Responsive sidebar context panel for scenarios

### Next Steps

**Immediate (P1 Priority)**
1. **User Onboarding Flow** - Goal selection, role setup, skill assessment
2. **Profile Management** - Edit user info, goals, preferences in Settings

**High Impact (P2 Priority)**
3. **Enhanced Progress Page** - Real competency data, time-series charts, confidence tracking
4. **Live Dashboard Data** - Replace hardcoded stats with real metrics and recommendations

**Content Enablement (P3 Priority)**
5. **Content Creation Pages** - Manual, structured, and chat-based generation flows
6. **Collection Management** - View/edit collections, add/remove items
7. **Mock Entity Management** - Create/edit companies and people for scenarios

**Community Features (P4 Priority)**
8. **Search & Filtering** - Functional search and filters on Collections page
9. **Save/Upvote System** - User libraries and content rating

**Platform Foundation (P6 Priority)**
10. **API Integration** - Replace mock provider with real API client
11. **Auth System** - Login/signup pages and route guards
12. **Error Handling** - Wire up ErrorState and EmptyState components throughout

**Admin Tools (P5 Priority)**
13. **Admin Dashboard** - Learner analytics and content management
14. **Verification Queue** - Review and approve user-created collections

### Technical Debt & Improvements

- Add loading skeletons for better perceived performance
- Implement proper error boundaries and retry mechanisms
- Add accessibility testing and improvements
- Optimize bundle size and implement code splitting
- Add end-to-end tests for critical user flows
