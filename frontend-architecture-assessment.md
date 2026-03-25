# Frontend Architecture Assessment

Assessment of `frontend-drafts/frontend-opus/` focused on component reuse
and modularity.

## Current Filesystem

```
src/
  components/
    layout/
      MainLayout.tsx
      Sidebar.tsx
      TopBar.tsx
    navigation/
      NavItem.tsx
      ThemeSwitcher.tsx
  contexts/
    ThemeContext.tsx
  design-system/
    primitives/
      Avatar.tsx    Badge.tsx     Button.tsx
      Card.tsx      Input.tsx     ProgressBar.tsx
      Skeleton.tsx
    patterns/
      EmptyState.tsx  ErrorState.tsx  LoadingState.tsx
      PageShell.tsx   StatCard.tsx
    tokens/
      themes.ts
    index.ts
  lib/
    cn.ts
    nav-config.ts
  pages/
    Collections.tsx   Dashboard.tsx   Practice.tsx
    Progress.tsx      Settings.tsx
  index.css
  main.tsx
  vite-env.d.ts
```

## What Works Well

### Token-driven design system
CSS custom properties in `index.css` map cleanly to Tailwind config tokens.
Three themes share the same semantic color names. Adding a new theme is a
single CSS block. This is solid.

### Primitives / patterns split
`design-system/primitives/` for atoms, `design-system/patterns/` for
compositions. Clean separation. `PageShell` as a consistent page wrapper is
a good pattern.

### Typed component props
All components use explicit `readonly` interfaces with discriminated unions
for variants. Good foundation for reuse.

### Utility layer
`cn()` utility is the right call. `@/` alias keeps imports clean.

## Problems

### 1. Duplicated helper functions across pages

`getDifficultyColor` is defined identically in both `Practice.tsx:143-154`
and `Collections.tsx:101-112`. `getSessionTypeColor` exists only in
`Practice.tsx:128-141` but will be needed by Dashboard, attempt history,
and admin views.

**Fix**: Extract to `src/lib/variant-helpers.ts` or add `variant` presets to
Badge directly (e.g., a `difficulty` prop or a `status-*` variant mapping).

### 2. Badge variant naming inconsistency

Badge has variants: `default`, `accent`, `success`, `warning`, `error`, `info`.
But `Practice.tsx:181` passes `status-success`, `status-warning`, `status-error`
as Badge variants. These are not valid `BadgeVariant` types. This compiles
only because of loose prop spreading or will fail at runtime.

**Fix**: Either add `status-success` etc. to the Badge variant union, or
standardize page code to use the existing variant names.

### 3. Imported but unused components

- `Avatar` is imported in `Collections.tsx:5` but only used inside the JSX
  map — actually it IS used. Correction: it is used.
- `EmptyState` and `ErrorState` patterns are exported from the design system
  but never used anywhere. They exist for future use but should be wired to
  placeholder states in current pages.

**Fix**: Use `EmptyState` in Collections when filtering yields no results,
and in Progress when no data exists. Use `ErrorState` as a fallback boundary.

### 4. Pages mix concerns — no feature layer

Every page is a monolith that contains:
- Data definition (hardcoded arrays)
- Presentation layout
- Helper functions
- Variant logic

The recommended repo shape from `technical-architecture.md:106-123` calls for:

```
frontend/
  app/
  features/
  components/
  design-system/
  lib/
```

There is no `features/` layer. This means every new page will duplicate
layout patterns and data-handling concerns.

**Fix**: Introduce `src/features/` for feature-specific compositions:

```
features/
  practice/
    PracticeModeCard.tsx       # Reusable card for a single practice mode
    RecentSessionRow.tsx       # Single row in recent sessions list
    SkillFocusCard.tsx         # Single skill focus area card
    RecommendedPracticeCard.tsx # Single recommendation card
  collections/
    CollectionCard.tsx         # Grid card view
    CollectionFeatured.tsx     # Featured/hero card view
    CollectionFilters.tsx      # Filter bar
  progress/
    CompetencyCard.tsx         # Single competency with skill bars
    SkillProgressRow.tsx       # Single skill bar with metadata
  dashboard/
    RecentActivityRow.tsx      # Single activity item
    RecommendedNextCard.tsx    # Recommended next practice
  assessment/
    ScoreDisplay.tsx           # Overall score visualization
    SkillBreakdown.tsx         # Skill-level score bars
    EvidencePanel.tsx          # Evidence excerpt display
    FeedbackSection.tsx        # Strengths/weaknesses/next actions
  authoring/
    CollectionEditor.tsx       # Manual collection creation form
    GenerationForm.tsx         # Structured AI generation form
    ChatGeneration.tsx         # Chat-based content generation
  admin/
    LearnerTable.tsx           # Learner progress table
    CohortSummary.tsx          # Cohort performance overview
    VerificationQueue.tsx      # Content verification list
```

Pages then become thin shells:

```tsx
// Practice.tsx — page is just layout + data wiring
<PageShell title="Practice Hub" ...>
  <PracticeModesGrid modes={practiceModes} onSelect={handleStart} />
  <RecommendedSection items={recommendations} />
  <RecentSessionsList sessions={sessions} />
  <SkillFocusGrid skills={skillFocus} />
</PageShell>
```

### 5. No shared hook layer

Only `useTheme` exists. Missing hooks for common patterns:

```
hooks/
  usePracticeSession.ts    # Session state, turn tracking, submission
  useProgress.ts           # Progress data fetching + caching
  useCollections.ts        # Collection list, filter, search
  useAttemptHistory.ts     # Past attempts with pagination
  useRecommendations.ts    # Recommendation fetching
  useDebounce.ts           # Debounced search input
  usePagination.ts         # Generic paginated list
```

### 6. Missing design system primitives

The current primitives cover basics but are missing components the MVP
pages will need repeatedly:

| Missing Primitive | Needed By |
| --- | --- |
| `Modal` / `Dialog` | Confirmation dialogs, content preview, feedback detail |
| `Textarea` | Practice response input, content authoring |
| `Select` / `Dropdown` | Filter bars, form selects, difficulty pickers |
| `Tabs` | Practice mode switching, settings sections, admin views |
| `Tooltip` | Score explanations, icon descriptions, help text |
| `Divider` | Section separation in cards and forms |
| `Typography` | Consistent text rendering without inline classes |
| `TagInput` | Skill/competency tagging in authoring |
| `Toast` | Action confirmations, error notifications |
| `Table` / `DataGrid` | Admin learner table, attempt history |

### 7. No barrel exports per directory

Only `design-system/index.ts` exists. Adding `components/index.ts`,
`features/*/index.ts`, and `hooks/index.ts` would simplify imports and
enforce public API boundaries.

### 8. Nav config is static and limited

`nav-config.ts` defines 5 flat routes. The MVP needs:
- Nested routes (e.g., `/collections/:id`, `/practice/:mode/:sessionId`,
  `/admin/learners`)
- Conditional nav items (admin-only routes)
- Badge indicators (e.g., pending verification count on admin nav)

**Fix**: Extend `NavRoute` to support `children`, `roles`, and `badge` props.
Or separate auth-gated routes from public nav config.

### 9. No layout variants

`MainLayout` is the only layout. The MVP needs:
- `AuthLayout` for login/signup (centered, no sidebar)
- `SessionLayout` for active practice (minimal chrome, focus mode)
- `AdminLayout` with admin-specific nav

**Fix**: Add layout wrappers or use route-level layout composition:

```tsx
{ element: <AuthLayout />, children: [login, signup] },
{ element: <MainLayout />, children: [dashboard, practice, ...] },
{ element: <SessionLayout />, children: [activeSession] },
{ element: <AdminLayout />, children: [adminDashboard, verification] },
```

### 10. No type exports from pages

Pages don't export their data shapes. When API integration comes, every
page will need typed response interfaces. These should be defined now
alongside feature modules.

**Fix**: Define domain types in `src/types/`:

```
types/
  assessment.ts    # Attempt, Assessment, Score, Feedback
  collection.ts    # Collection, Scenario, PromptItem
  progress.ts      # SkillProgress, CompetencyProgress, Snapshot
  recommendation.ts # Recommendation, ReasonCode
  user.ts          # User, Profile, Goals
  content.ts       # MockCompany, MockPerson, Artifact
  admin.ts         # LearnerSummary, CohortData, VerificationItem
```

### 11. Global transition on everything

`index.css:129-132` applies `transition-property: color, background-color,
border-color, box-shadow` to ALL elements. This causes transition jank on
scroll, layout shifts, and list re-renders. It should be scoped.

**Fix**: Remove the global `*` selector rule. Let individual components
opt in via Tailwind `transition-*` utilities, which is already the pattern
used by Button, Card, and NavItem.

## Recommended Target Structure

```
src/
  types/                        # Shared domain types
    assessment.ts
    collection.ts
    progress.ts
    recommendation.ts
    user.ts
    content.ts
    admin.ts
    index.ts

  lib/                          # Utilities
    cn.ts
    variant-helpers.ts          # Difficulty/session/color mappers
    format.ts                   # Date, duration, score formatting
    api.ts                      # API client (fetch wrapper)
    constants.ts                # Skill names, competency names, rubric types

  hooks/                        # Shared hooks
    useDebounce.ts
    usePagination.ts
    usePracticeSession.ts
    useProgress.ts
    useCollections.ts
    useAttemptHistory.ts
    useRecommendations.ts

  contexts/                     # React contexts
    ThemeContext.tsx
    AuthContext.tsx

  design-system/                # Unchanged — token-driven primitives
    tokens/
    primitives/
      Avatar.tsx  Badge.tsx  Button.tsx  Card.tsx
      Divider.tsx  Input.tsx  Modal.tsx  ProgressBar.tsx
      Select.tsx   Skeleton.tsx  Table.tsx  Tabs.tsx
      Textarea.tsx  Toast.tsx  Tooltip.tsx  Typography.tsx
    patterns/
      EmptyState.tsx  ErrorState.tsx  LoadingState.tsx
      PageShell.tsx   StatCard.tsx    FilterBar.tsx
      Pagination.tsx  ConfirmDialog.tsx
    index.ts

  features/                     # Feature compositions
    practice/
      PracticeModeCard.tsx
      RecentSessionRow.tsx
      RecommendedPracticeCard.tsx
      SkillFocusCard.tsx
      index.ts
    collections/
      CollectionCard.tsx
      CollectionFeatured.tsx
      CollectionFilters.tsx
      CollectionDetail.tsx
      index.ts
    progress/
      CompetencyCard.tsx
      SkillProgressRow.tsx
      ProgressTimeline.tsx
      index.ts
    assessment/
      SessionContainer.tsx
      PromptDisplay.tsx
      ResponseInput.tsx
      ScoreDisplay.tsx
      SkillBreakdown.tsx
      EvidencePanel.tsx
      FeedbackSection.tsx
      index.ts
    dashboard/
      RecentActivityRow.tsx
      RecommendedNextCard.tsx
      FocusSkillCard.tsx
      index.ts
    onboarding/
      GoalSelector.tsx
      RoleSelector.tsx
      PreferenceSetup.tsx
      index.ts
    authoring/
      CollectionEditor.tsx
      GenerationForm.tsx
      ChatGeneration.tsx
      MockEntityEditor.tsx
      index.ts
    admin/
      LearnerTable.tsx
      CohortSummary.tsx
      VerificationQueue.tsx
      DiagnosticViewer.tsx
      index.ts
    auth/
      LoginForm.tsx
      SignupForm.tsx
      index.ts

  components/                   # Shared layout + navigation
    layout/
      MainLayout.tsx
      AuthLayout.tsx
      SessionLayout.tsx
      AdminLayout.tsx
      Sidebar.tsx
      TopBar.tsx
    navigation/
      NavItem.tsx
      ThemeSwitcher.tsx
      NotificationBell.tsx
      UserMenu.tsx

  pages/                        # Thin page shells
    Dashboard.tsx
    Practice.tsx
    PracticeSession.tsx         # NEW
    Collections.tsx
    CollectionDetail.tsx        # NEW
    Progress.tsx
    AttemptHistory.tsx          # NEW
    AttemptDetail.tsx           # NEW
    Authoring.tsx               # NEW
    Settings.tsx
    Login.tsx                   # NEW
    Signup.tsx                  # NEW
    AdminDashboard.tsx          # NEW
    AdminVerification.tsx       # NEW
    NotFound.tsx                # NEW

  routes.tsx                    # Centralized route config
  main.tsx
  index.css
```

## Summary of Key Actions

| # | Action | Impact |
| --- | --- | --- |
| 1 | Extract `getDifficultyColor` / `getSessionTypeColor` to shared utils | Eliminates duplication |
| 2 | Fix Badge variant inconsistency (`status-*` vs actual variants) | Prevents runtime errors |
| 3 | Introduce `features/` layer | Enables component reuse across pages |
| 4 | Create `types/` for domain models | Typed contracts before API integration |
| 5 | Add missing primitives (Modal, Textarea, Select, Tabs, Table, Toast) | Unblocks every future page |
| 6 | Add `hooks/` layer | Reusable data patterns, DRY pages |
| 7 | Create layout variants (Auth, Session, Admin) | Supports different chrome needs |
| 8 | Remove global CSS transition rule | Eliminates render jank |
| 9 | Extend nav config for nested/conditional routes | Supports admin + detail routes |
| 10 | Add barrel exports per directory | Clean public APIs, enforce boundaries |
| 11 | Wire EmptyState/ErrorState to current pages | Validates primitives work |
