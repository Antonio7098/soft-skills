import type { DataProvider } from './provider';
import type {
  UserView,
  AuthSessionView,
  AuthProfileView,
  OrganisationMembershipView,
  TaxonomySnapshot,
  CollectionView,
  CollectionListFilters,
  CollectionCreateCommand,
  PromptItemCreateCommand,
  ScenarioCreateCommand,
  LoginUserCommand,
  RegisterUserCommand,
  UpdateProfileCommand,
  DeleteAccountResult,
  QuickPracticeSessionView,
  StartQuickPracticeSessionCommand,
  SubmitAttemptCommand,
  AttemptView,
  CompetencyProgressView,
  AttemptHistoryItem,
  InterviewSessionView,
  ScenarioSessionView,
  PracticeRunView,
  PracticeRunItemSummary,
  PracticeSessionView,
  StartPracticeRunCommand,
  StructuredCollectionGenerationCommand,
  ChatCollectionGenerationCommand,
  CollectionGenerationView,
  PromptItemView,
  ScenarioView,
  MockCompanyView,
  MockPersonView,
  PerSkillAssessment,
  EvidenceItem,
  AdminUserView,
  AdminUserListView,
  BulkOperationResultView,
  UserActivityView,
  LearnerAnalyticsView,
  AdminLearnerRelationshipView,
  AnalyticsOverviewView,
  CohortAnalyticsView,
  CohortComparisonView,
  CollectionVerificationQueueItemView,
  CollectionVerificationAuditView,
  EvaluationSuiteView,
  EvaluationRunView,
  EvaluationDashboardView,
  EvaluationComparisonView,
  BenchmarkDashboardView,
  EvaluationCaseDetailView,
  ProviderModel,
  PromptSummaryView,
  PromptVersionView,
  PromptAnalyticsView,
  PromptCompareView,
  PipelineDefinitionView,
  PipelineDAGView,
  PipelineRunSummaryView,
  PipelineTraceView,
  PipelineMetricsView,
  RubricView,
  RubricCriterionInput,
  RubricCriterionAdminView,
  RubricAdminView,
  WorkflowEventView,
  PaginatedWorkflowEventsView,
  AttemptAuditView,
  UsageTrendPointView,
  ProviderUsageView,
  SkillClusterView,
  SkillAverageView,
  AssistantSessionView,
  AssistantTurnView,
  AssistantMessageView,
  AssistantToolCallView,
  CreateAssistantSessionCommand,
  CreateAssistantTurnCommand,
  CancelAssistantTurnCommand,
  AssistantStreamCallbacks,
  TelemetryOverviewView,
  TelemetryTraceListView,
  TelemetryTraceListItemView,
  TelemetryTraceView,
  OrgSkillView,
  OrgCompetencyView,
  OrgRubricView,
  OrganisationView,
  OrganisationListView,
  CreateOrganisationCommand,
} from './types';
import {
  SEED_SKILLS,
  SEED_COMPETENCIES,
  SEED_RUBRICS,
  SEED_RUBRIC_CRITERIA,
  SEED_COLLECTIONS,
  SEED_CURRENT_USER,
  SEED_ATTEMPT_HISTORY,
  SEED_COMPETENCY_PROGRESS,
  SEED_ASSISTANT_SESSIONS,
  SEED_TURNS,
} from './mock';

// ---------------------------------------------------------------------------
// MockDataProvider — all data comes from in-memory seed arrays.
// Simulates async API latency for realistic UX.
// ---------------------------------------------------------------------------

/**
 * Build a realistic mock AttemptView with full assessment data.
 * Used by Interview & Scenario session pages to generate results
 * without a dedicated backend endpoint.
 */
export function buildMockAttemptView(opts: {
  attemptId: string;
  sessionId: string;
  title: string;
  promptText: string;
  difficulty: 'introductory' | 'intermediate' | 'advanced';
  skillSlugs: string[];
  responseText: string;
}): AttemptView {
  const score = Math.floor(Math.random() * 3) + 3; // 3-5

  const per_skill_assessments: PerSkillAssessment[] = opts.skillSlugs.map((slug) => {
    const skillScore = Math.max(1, Math.min(5, score + (Math.random() > 0.5 ? 0 : -1)));
    const evidence: EvidenceItem[] = [{
      quote: opts.responseText.slice(0, 80) || 'Response demonstrated relevant competency.',
      explanation: `This shows ${slug.replace(/-/g, ' ')} through the learner's structured approach and situational awareness.`,
    }];
    return {
      skill_slug: slug,
      score: skillScore,
      rationale: `Demonstrated ${score >= 4 ? 'strong' : score >= 3 ? 'solid' : 'developing'} ${slug.replace(/-/g, ' ')} throughout the session.`,
      evidence,
    };
  });

  return {
    id: opts.attemptId,
    session_id: opts.sessionId,
    workflow_id: `wf-${uid()}`,
    status: 'assessed',
    response_mode: 'text',
    response_text: opts.responseText,
    last_error_code: null,
    submitted_at: new Date().toISOString(),
    assessed_at: new Date().toISOString(),
    prompt: {
      content_item_id: `pi-${uid()}`,
      prompt_type: 'quick_practice_prompt',
      title: opts.title,
      prompt_text: opts.promptText,
      difficulty: opts.difficulty,
      delivery_version: 'quick-practice.delivery.v1',
      target_skill_slugs: opts.skillSlugs,
      rubric_id: 'quick_practice_text@v1',
      rubric_version: 'v1',
    },
    assessment: {
      assessment_id: `assess-${uid()}`,
      attempt_id: opts.attemptId,
      session_id: opts.sessionId,
      validation_status: 'validated',
      prompt_version: 'assessment.quick-practice.v1',
      rubric_id: 'quick_practice_text@v1',
      rubric_version: 'v1',
      schema_version: 'quick-practice-assessment-output.v1',
      config_version: 'quick-practice-marking-config.v1',
      provider: 'mock',
      model_slug: 'mock-v1',
      overall_score: score,
      per_skill_assessments,
      summary: score >= 4
        ? 'Excellent performance across all assessed competencies. Responses were well-structured, demonstrated strong situational awareness, and addressed key stakeholder concerns effectively.'
        : score >= 3
          ? 'Solid performance with good foundational skills. The responses addressed the core requirements with a practical approach that could benefit from more specific examples and deeper analysis.'
          : 'The response shows developing skills with a reasonable foundation. Focus on providing more structured responses with concrete examples to strengthen your delivery.',
      strengths: score >= 3
        ? ['Clear and structured communication', 'Good situational awareness', 'Appropriate stakeholder consideration']
        : ['Attempted to address the core prompt', 'Showed awareness of the situation'],
      weaknesses: score < 5
        ? ['Could provide more specific, concrete examples', 'Strengthen the conclusion with actionable next steps', 'Consider additional stakeholder perspectives']
        : ['Minor refinements possible in phrasing'],
      next_actions: [
        'Practice structuring responses using the STAR framework',
        'Review similar scenarios to build pattern recognition',
        'Focus on quantifying impact in your examples',
      ],
      trace_id: `trace-${uid()}`,
      pipeline_run_id: `run-${uid()}`,
      rejection_code: null,
      created_at: new Date().toISOString(),
      raw_payload: {},
    },
  };
}

let _collections = [...SEED_COLLECTIONS];
let _user = { ...SEED_CURRENT_USER };
let _attempts = [...SEED_ATTEMPT_HISTORY];
const _interviewSessions = new Map<string, InterviewSessionView>();
const _scenarioSessions = new Map<string, ScenarioSessionView>();
const _practiceRuns = new Map<string, PracticeRunView>();
const _practiceSessions = new Map<string, PracticeSessionView>();
const _saves = new Map<string, Set<string>>();
const _ratings = new Map<string, Map<string, number>>();
const MOCK_PROFILE_STORAGE_KEY = 'ss_mock_auth_profile_id';
const MOCK_ACTIVE_ORG_STORAGE_KEY = 'ss_mock_active_organisation_id';
const _createdOrganisations: OrganisationView[] = [];
const _createdMemberships: OrganisationMembershipView[] = [];

function delay(ms = 300): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}

function uid(): string {
  return Math.random().toString(36).slice(2, 10);
}

function isoDate(daysAgo = 0): string {
  const d = new Date();
  d.setDate(d.getDate() - daysAgo);
  return d.toISOString();
}

const DEFAULT_MEMBER_PERMISSIONS = ['collections:read', 'practice:run'];
const DEFAULT_ORG_ADMIN_PERMISSIONS = ['collections:read', 'practice:run', 'admin:access', 'org:read', 'org:write'];

function createMembership(
  organisation_id: string,
  organisation_name: string,
  role: 'member' | 'org_admin',
  permissions = role === 'org_admin' ? DEFAULT_ORG_ADMIN_PERMISSIONS : DEFAULT_MEMBER_PERMISSIONS,
): OrganisationMembershipView {
  return { organisation_id, organisation_name, role, permissions };
}

const MOCK_AUTH_PROFILES: AuthProfileView[] = [
  {
    id: 'learner-alex',
    label: 'Alex Chen',
    description: 'Learner in Acme Sales',
    session: {
      status: 'authenticated',
      actor: { ...SEED_CURRENT_USER, org_memberships: [createMembership('org-001', 'Acme Sales', 'member')] },
      platform_role: 'learner',
      org_memberships: [createMembership('org-001', 'Acme Sales', 'member')],
      active_organisation_id: 'org-001',
      capabilities: ['app:access'],
      data_mode: 'mock',
    },
  },
  {
    id: 'org-admin-alex',
    label: 'Alex Chen (Org Admin)',
    description: 'Org admin for Acme Sales',
    session: {
      status: 'authenticated',
      actor: { ...SEED_CURRENT_USER, role: 'admin', org_memberships: [createMembership('org-001', 'Acme Sales', 'org_admin')] },
      platform_role: 'admin',
      org_memberships: [createMembership('org-001', 'Acme Sales', 'org_admin')],
      active_organisation_id: 'org-001',
      capabilities: ['app:access', 'admin:access'],
      data_mode: 'mock',
    },
  },
  {
    id: 'superadmin-henry',
    label: 'Henry Patel',
    description: 'Platform admin across multiple organisations',
    session: {
      status: 'authenticated',
      actor: {
        id: 'user-900',
        email: 'henry.patel@acme.com',
        display_name: 'Henry Patel',
        role: 'superadmin',
        auth_provider: 'google',
        created_at: '2026-01-05T10:00:00Z',
        profile: {
          target_role: 'Platform Admin',
          goals: ['Audit org content', 'Manage platform configuration'],
          practice_preferences: {},
        },
        org_memberships: [
          createMembership('org-001', 'Acme Sales', 'org_admin'),
          createMembership('org-002', 'Acme Support', 'org_admin'),
        ],
      },
      platform_role: 'superadmin',
      org_memberships: [
        createMembership('org-001', 'Acme Sales', 'org_admin'),
        createMembership('org-002', 'Acme Support', 'org_admin'),
      ],
      active_organisation_id: 'org-001',
      capabilities: ['app:access', 'admin:access', 'platform:superadmin'],
      data_mode: 'mock',
    },
  },
];

function getStoredProfileId(): string {
  return sessionStorage.getItem(MOCK_PROFILE_STORAGE_KEY) ?? 'org-admin-alex';
}

function setStoredProfileId(profileId: string): void {
  sessionStorage.setItem(MOCK_PROFILE_STORAGE_KEY, profileId);
}

function getStoredActiveOrgId(): string | null {
  return sessionStorage.getItem(MOCK_ACTIVE_ORG_STORAGE_KEY);
}

function setStoredActiveOrgId(orgId: string | null): void {
  if (orgId) {
    sessionStorage.setItem(MOCK_ACTIVE_ORG_STORAGE_KEY, orgId);
    return;
  }
  sessionStorage.removeItem(MOCK_ACTIVE_ORG_STORAGE_KEY);
}

function getProfileDefinition(profileId = getStoredProfileId()): AuthProfileView {
  return MOCK_AUTH_PROFILES.find((profile) => profile.id === profileId) ?? MOCK_AUTH_PROFILES[1]!;
}

function materializeSession(profileId = getStoredProfileId()): AuthSessionView {
  const profile = getProfileDefinition(profileId);
  const storedOrgId = getStoredActiveOrgId();
  const actorId = profile.session.actor?.id ?? null;
  const createdMemberships = actorId
    ? _createdMemberships.filter((m) => m.organisation_id !== undefined)
    : [];
  const allMemberships = [...profile.session.org_memberships, ...createdMemberships];
  const availableOrgIds = new Set(allMemberships.map((membership) => membership.organisation_id));
  const activeOrgId = storedOrgId && availableOrgIds.has(storedOrgId)
    ? storedOrgId
    : profile.session.active_organisation_id ?? allMemberships[0]?.organisation_id ?? null;

  return {
    ...profile.session,
    actor: profile.session.actor ? { ...profile.session.actor } : null,
    org_memberships: allMemberships.map((membership) => ({ ...membership })),
    active_organisation_id: activeOrgId,
    capabilities: [...profile.session.capabilities],
  };
}

function syncMockUserFromSession(): AuthSessionView {
  const session = materializeSession();
  const actorId = session.actor?.id ?? null;
  const createdMemberships = actorId
    ? _createdMemberships.filter((m) => m.organisation_id !== undefined)
    : [];
  _user = session.actor
    ? {
        ...session.actor,
        org_memberships: [...(session.actor.org_memberships ?? []), ...createdMemberships],
      }
    : { ...SEED_CURRENT_USER, org_memberships: [] };
  return session;
}

function hasCapability(session: AuthSessionView, capability: string): boolean {
  return session.capabilities.includes(capability);
}

function getMembership(session: AuthSessionView, organisationId: string): OrganisationMembershipView | undefined {
  return session.org_memberships.find((membership) => membership.organisation_id === organisationId);
}

function requireAuthenticatedSession(): AuthSessionView {
  const session = syncMockUserFromSession();
  if (session.status !== 'authenticated' || !session.actor) {
    throw new Error('Authentication required');
  }
  return session;
}

function requireAdminSession(): AuthSessionView {
  const session = requireAuthenticatedSession();
  if (!hasCapability(session, 'admin:access')) {
    throw new Error('Admin access required');
  }
  return session;
}

function requireOrgAccess(orgId: string, permission: 'org:read' | 'org:write' = 'org:read'): AuthSessionView {
  const session = requireAdminSession();
  if (session.platform_role === 'superadmin') {
    return session;
  }
  const membership = getMembership(session, orgId);
  if (!membership || !membership.permissions.includes(permission)) {
    throw new Error(`Not authorized for organisation ${orgId}`);
  }
  return session;
}

function getScopedAdminOrganisationId(session: AuthSessionView): string | null {
  if (session.platform_role === 'superadmin') {
    return session.active_organisation_id;
  }
  return session.active_organisation_id ?? session.org_memberships[0]?.organisation_id ?? null;
}

// ---------------------------------------------------------------------------
// Admin mock data
// ---------------------------------------------------------------------------

const SEED_ADMIN_USERS: AdminUserView[] = [
  { user_id: 'usr-001', email: 'alice.chen@acme.com', display_name: 'Alice Chen', auth_provider: 'google', is_active: true, organisation_id: 'org-001', organisation_role: 'admin', created_at: '2025-01-15T10:00:00Z' },
  { user_id: 'usr-002', email: 'bob.martinez@acme.com', display_name: 'Bob Martinez', auth_provider: 'google', is_active: true, organisation_id: 'org-001', organisation_role: 'member', created_at: '2025-02-01T14:30:00Z' },
  { user_id: 'usr-003', email: 'carol.smith@acme.com', display_name: 'Carol Smith', auth_provider: 'google', is_active: true, organisation_id: 'org-001', organisation_role: 'member', created_at: '2025-02-10T09:15:00Z' },
  { user_id: 'usr-004', email: 'david.kim@acme.com', display_name: 'David Kim', auth_provider: 'google', is_active: false, organisation_id: 'org-001', organisation_role: 'member', created_at: '2025-02-20T11:00:00Z' },
  { user_id: 'usr-005', email: 'emma.wilson@acme.com', display_name: 'Emma Wilson', auth_provider: 'google', is_active: true, organisation_id: 'org-001', organisation_role: 'admin', created_at: '2025-03-01T08:45:00Z' },
  { user_id: 'usr-006', email: 'frank.nguyen@acme.com', display_name: 'Frank Nguyen', auth_provider: 'google', is_active: true, organisation_id: 'org-001', organisation_role: 'member', created_at: '2025-03-05T16:20:00Z' },
  { user_id: 'usr-007', email: 'grace.liu@acme.com', display_name: 'Grace Liu', auth_provider: 'google', is_active: true, organisation_id: 'org-001', organisation_role: 'member', created_at: '2025-03-10T13:00:00Z' },
  { user_id: 'usr-008', email: 'henry.patel@acme.com', display_name: 'Henry Patel', auth_provider: 'google', is_active: true, organisation_id: 'org-002', organisation_role: 'admin', created_at: '2025-03-12T10:30:00Z' },
  { user_id: 'usr-009', email: 'iris.johnson@acme.com', display_name: 'Iris Johnson', auth_provider: 'google', is_active: false, organisation_id: 'org-001', organisation_role: 'member', created_at: '2025-03-15T15:45:00Z' },
  { user_id: 'usr-010', email: 'jack.brown@acme.com', display_name: 'Jack Brown', auth_provider: 'google', is_active: true, organisation_id: 'org-001', organisation_role: 'member', created_at: '2025-03-20T12:00:00Z' },
];

const SEED_LEARNER_ANALYTICS: Record<string, LearnerAnalyticsView> = {
  'usr-002': {
    learner_id: 'usr-002',
    target_role: 'sales representative',
    latest_progress_snapshot_id: 'snap-001',
    latest_recommendation_id: 'rec-001',
    weak_skill_slugs: ['conflict-resolution', 'active-listening'],
    stagnating_skill_slugs: ['presentation-skills'],
    coverage_gap_skill_slugs: ['negotiation'],
    usage: {
      total_sessions: 45,
      total_attempts: 120,
      submitted_attempts: 115,
      assessed_attempts: 110,
      validated_assessments: 98,
      rejected_assessments: 12,
      workflow_event_count: 340,
      pipeline_run_count: 120,
      provider_call_count: 890,
      avg_validated_score: 3.8,
      last_activity_at: isoDate(1),
    },
    recent_attempts: [
      { attempt_id: 'att-001', session_id: 'sess-001', practice_type: 'quick_practice', content_item_id: 'pi-001', content_item_type: 'prompt_item', status: 'assessed', overall_score: 4, submitted_at: isoDate(1), assessed_at: isoDate(1) },
      { attempt_id: 'att-002', session_id: 'sess-002', practice_type: 'quick_practice', content_item_id: 'pi-002', content_item_type: 'prompt_item', status: 'assessed', overall_score: 3, submitted_at: isoDate(2), assessed_at: isoDate(2) },
      { attempt_id: 'att-003', session_id: 'sess-003', practice_type: 'quick_practice', content_item_id: 'pi-003', content_item_type: 'prompt_item', status: 'assessed', overall_score: 5, submitted_at: isoDate(3), assessed_at: isoDate(3) },
    ],
    usage_trend: [
      { bucket_date: '2026-03-01', sessions_started: 12, attempts_submitted: 8, assessments_validated: 7, assessments_rejected: 1 },
      { bucket_date: '2026-03-02', sessions_started: 15, attempts_submitted: 10, assessments_validated: 9, assessments_rejected: 1 },
      { bucket_date: '2026-03-03', sessions_started: 10, attempts_submitted: 7, assessments_validated: 6, assessments_rejected: 1 },
      { bucket_date: '2026-03-04', sessions_started: 8, attempts_submitted: 6, assessments_validated: 5, assessments_rejected: 1 },
    ],
    provider_summary: [
      { provider: 'openrouter', model_slug: 'gpt-4o-mini', call_count: 890, success_count: 875, failure_count: 15, avg_latency_ms: 820 },
    ],
  },
};

const SEED_ANALYTICS_OVERVIEW: AnalyticsOverviewView = {
  total_learners: 1247,
  active_learners_30d: 834,
  total_sessions: 18932,
  total_attempts: 4521,
  submitted_attempts: 4102,
  validated_assessments: 3891,
  rejected_assessments: 211,
  avg_validated_score: 72.4,
  overall_usage_trend: [
    { bucket_date: '2026-03-01', sessions_started: 142, attempts_submitted: 38, assessments_validated: 35, assessments_rejected: 3 },
    { bucket_date: '2026-03-02', sessions_started: 158, attempts_submitted: 44, assessments_validated: 41, assessments_rejected: 3 },
    { bucket_date: '2026-03-03', sessions_started: 135, attempts_submitted: 36, assessments_validated: 33, assessments_rejected: 3 },
    { bucket_date: '2026-03-04', sessions_started: 168, attempts_submitted: 48, assessments_validated: 45, assessments_rejected: 3 },
    { bucket_date: '2026-03-05', sessions_started: 152, attempts_submitted: 42, assessments_validated: 39, assessments_rejected: 3 },
    { bucket_date: '2026-03-06', sessions_started: 145, attempts_submitted: 40, assessments_validated: 37, assessments_rejected: 3 },
    { bucket_date: '2026-03-07', sessions_started: 130, attempts_submitted: 35, assessments_validated: 32, assessments_rejected: 3 },
  ] as UsageTrendPointView[],
  top_weak_skills: [
    { skill_slug: 'active-listening', learner_count: 312 },
    { skill_slug: 'conflict-resolution', learner_count: 287 },
    { skill_slug: 'presentation-skills', learner_count: 245 },
    { skill_slug: 'negotiation', learner_count: 198 },
    { skill_slug: 'feedback-delivery', learner_count: 176 },
  ] as SkillClusterView[],
  cohort_breakdown: [
    { cohort_key: 'sales-team', learner_count: 42 },
    { cohort_key: 'engineering', learner_count: 89 },
    { cohort_key: 'customer-success', learner_count: 67 },
    { cohort_key: 'new-hires', learner_count: 124 },
  ],
  provider_summary: [
    { provider: 'openrouter', model_slug: 'gpt-4o-mini', call_count: 18432, success_count: 18200, failure_count: 232, avg_latency_ms: 842.3 },
    { provider: 'openrouter', model_slug: 'claude-3-haiku', call_count: 5420, success_count: 5390, failure_count: 30, avg_latency_ms: 620.5 },
  ] as ProviderUsageView[],
};

const SEED_COHORT_ANALYTICS: Record<string, CohortAnalyticsView> = {
  'sales-team': {
    cohort_key: 'sales-team',
    learner_count: 42,
    usage: {
      total_sessions: 892,
      total_attempts: 234,
      submitted_attempts: 210,
      assessed_attempts: 198,
      validated_assessments: 178,
      rejected_assessments: 20,
      workflow_event_count: 1240,
      pipeline_run_count: 234,
      provider_call_count: 4521,
      avg_validated_score: 74.2,
      last_activity_at: isoDate(1),
    },
    weak_skill_clusters: [
      { skill_slug: 'conflict-resolution', learner_count: 18 },
      { skill_slug: 'negotiation', learner_count: 15 },
    ] as SkillClusterView[],
    average_skill_scores: [
      { skill_slug: 'active-listening', avg_score: 3.9, learner_count: 40 },
      { skill_slug: 'conflict-resolution', avg_score: 2.8, learner_count: 38 },
      { skill_slug: 'presentation-skills', avg_score: 3.5, learner_count: 36 },
      { skill_slug: 'negotiation', avg_score: 3.1, learner_count: 34 },
    ] as SkillAverageView[],
    usage_trend: [
      { bucket_date: '2026-03-01', sessions_started: 8, attempts_submitted: 3, assessments_validated: 3, assessments_rejected: 0 },
      { bucket_date: '2026-03-02', sessions_started: 10, attempts_submitted: 4, assessments_validated: 4, assessments_rejected: 0 },
    ] as UsageTrendPointView[],
    provider_summary: [
      { provider: 'openrouter', model_slug: 'gpt-4o-mini', call_count: 4521, success_count: 4480, failure_count: 41, avg_latency_ms: 835 },
    ] as ProviderUsageView[],
  },
  'engineering': {
    cohort_key: 'engineering',
    learner_count: 89,
    usage: {
      total_sessions: 1456,
      total_attempts: 412,
      submitted_attempts: 390,
      assessed_attempts: 380,
      validated_assessments: 362,
      rejected_assessments: 18,
      workflow_event_count: 2100,
      pipeline_run_count: 412,
      provider_call_count: 8234,
      avg_validated_score: 78.5,
      last_activity_at: isoDate(0),
    },
    weak_skill_clusters: [
      { skill_slug: 'presentation-skills', learner_count: 24 },
      { skill_slug: 'feedback-delivery', learner_count: 20 },
    ] as SkillClusterView[],
    average_skill_scores: [
      { skill_slug: 'active-listening', avg_score: 4.2, learner_count: 85 },
      { skill_slug: 'conflict-resolution', avg_score: 3.6, learner_count: 82 },
      { skill_slug: 'presentation-skills', avg_score: 2.9, learner_count: 80 },
      { skill_slug: 'feedback-delivery', avg_score: 3.2, learner_count: 78 },
    ] as SkillAverageView[],
    usage_trend: [
      { bucket_date: '2026-03-01', sessions_started: 15, attempts_submitted: 6, assessments_validated: 6, assessments_rejected: 0 },
      { bucket_date: '2026-03-02', sessions_started: 18, attempts_submitted: 8, assessments_validated: 7, assessments_rejected: 1 },
    ] as UsageTrendPointView[],
    provider_summary: [
      { provider: 'openrouter', model_slug: 'gpt-4o-mini', call_count: 8234, success_count: 8150, failure_count: 84, avg_latency_ms: 855 },
    ] as ProviderUsageView[],
  },
};

const SEED_VERIFICATION_QUEUE: CollectionVerificationQueueItemView[] = [
  { collection_id: 'col-vq-001', author_user_id: 'usr-003', title: 'Advanced Negotiation Scenarios', lifecycle_state: 'review', verification_state: 'unverified', discovery_tier: 'standard_public', source_type: 'generated_structured', prompt_item_count: 12, scenario_count: 4, created_at: isoDate(5), updated_at: isoDate(3), latest_reviewed_at: null, latest_reviewer_user_id: null, latest_note: null },
  { collection_id: 'col-vq-002', author_user_id: 'usr-006', title: 'Customer Feedback Workshop', lifecycle_state: 'published_private', verification_state: 'unverified', discovery_tier: 'private', source_type: 'manual', prompt_item_count: 8, scenario_count: 2, created_at: isoDate(10), updated_at: isoDate(7), latest_reviewed_at: isoDate(2), latest_reviewer_user_id: 'usr-001', latest_note: 'Looking good, needs more varied scenarios.' },
  { collection_id: 'col-vq-003', author_user_id: 'usr-007', title: 'Team Conflict Resolution', lifecycle_state: 'review', verification_state: 'unverified', discovery_tier: 'org_public', source_type: 'generated_chat', prompt_item_count: 15, scenario_count: 5, created_at: isoDate(3), updated_at: isoDate(1), latest_reviewed_at: null, latest_reviewer_user_id: null, latest_note: null },
  { collection_id: 'col-vq-004', author_user_id: 'usr-002', title: 'Leadership Communication', lifecycle_state: 'published_public', verification_state: 'unverified', discovery_tier: 'global_public', source_type: 'manual', prompt_item_count: 20, scenario_count: 8, created_at: isoDate(14), updated_at: isoDate(14), latest_reviewed_at: null, latest_reviewer_user_id: null, latest_note: null },
];

const SEED_EVAL_SUITES: EvaluationSuiteView[] = [
  { suite_id: 'suite-001', name: 'Quick Practice Assessment', suite_type: 'quick_practice', description: 'Standard quick practice evaluation suite', created_at: '2025-06-01T00:00:00Z', updated_at: '2025-12-01T00:00:00Z' },
  { suite_id: 'suite-002', name: 'Interview Simulation Eval', suite_type: 'interview', description: 'Multi-turn interview evaluation', created_at: '2025-06-15T00:00:00Z', updated_at: '2025-11-20T00:00:00Z' },
  { suite_id: 'suite-003', name: 'Scenario Assessment', suite_type: 'scenario', description: 'Full scenario evaluation with steps', created_at: '2025-07-01T00:00:00Z', updated_at: '2025-10-15T00:00:00Z' },
];

const SEED_EVAL_RUNS: EvaluationRunView[] = [
  { evaluation_run_id: 'run-001', suite_id: 'suite-001', suite_type: 'quick_practice', status: 'completed', passed: true, pass_rate: 0.92, avg_latency_ms: 1240.5, total_tokens: 45230, case_count: 50, model_slugs: ['gpt-4o-mini'], started_at: isoDate(7), completed_at: isoDate(7) },
  { evaluation_run_id: 'run-002', suite_id: 'suite-002', suite_type: 'interview', status: 'completed', passed: true, pass_rate: 0.88, avg_latency_ms: 3420.0, total_tokens: 89234, case_count: 30, model_slugs: ['gpt-4o-mini', 'claude-3-haiku'], started_at: isoDate(6), completed_at: isoDate(6) },
  { evaluation_run_id: 'run-003', suite_id: 'suite-001', suite_type: 'quick_practice', status: 'completed', passed: false, pass_rate: 0.78, avg_latency_ms: 1380.2, total_tokens: 48120, case_count: 50, model_slugs: ['gpt-4o-mini'], started_at: isoDate(5), completed_at: isoDate(5) },
  { evaluation_run_id: 'run-004', suite_id: 'suite-003', suite_type: 'scenario', status: 'completed', passed: true, pass_rate: 0.95, avg_latency_ms: 5680.0, total_tokens: 156780, case_count: 20, model_slugs: ['gpt-4o-mini'], started_at: isoDate(4), completed_at: isoDate(4) },
  { evaluation_run_id: 'run-005', suite_id: 'suite-001', suite_type: 'quick_practice', status: 'completed', passed: true, pass_rate: 0.90, avg_latency_ms: 1190.8, total_tokens: 43890, case_count: 50, model_slugs: ['gpt-4o-mini'], started_at: isoDate(3), completed_at: isoDate(3) },
  { evaluation_run_id: 'run-006', suite_id: 'suite-002', suite_type: 'interview', status: 'failed', passed: false, pass_rate: 0.65, avg_latency_ms: 4210.5, total_tokens: 91234, case_count: 30, model_slugs: ['claude-3-haiku'], started_at: isoDate(2), completed_at: isoDate(2) },
  { evaluation_run_id: 'run-007', suite_id: 'suite-001', suite_type: 'quick_practice', status: 'completed', passed: true, pass_rate: 0.94, avg_latency_ms: 1210.3, total_tokens: 46234, case_count: 50, model_slugs: ['gpt-4o-mini'], started_at: isoDate(1), completed_at: isoDate(1) },
];

const SEED_PROMPTS: PromptSummaryView[] = [
  { name: 'quick_practice_prompt', prompt_type: 'quick_practice_prompt', latest_version: 'v1.2.0', status: 'published', created_at: '2025-01-10T00:00:00Z' },
  { name: 'interview_turn_prompt', prompt_type: 'interview_prompt', latest_version: 'v2.0.0', status: 'published', created_at: '2025-02-15T00:00:00Z' },
  { name: 'scenario_step_prompt', prompt_type: 'scenario_step', latest_version: 'v1.1.0', status: 'published', created_at: '2025-03-01T00:00:00Z' },
  { name: 'assessment_summary_prompt', prompt_type: 'assessment_summary', latest_version: 'v1.0.0', status: 'draft', created_at: '2025-06-01T00:00:00Z' },
  { name: 'feedback_generation_prompt', prompt_type: 'feedback_generation', latest_version: 'v1.3.0', status: 'archived', created_at: '2025-04-01T00:00:00Z' },
];

const SEED_PROMPT_VERSIONS: Record<string, PromptVersionView[]> = {
  'quick_practice_prompt': [
    { id: 1, name: 'quick_practice_prompt', version: 'v1.0.0', prompt_type: 'quick_practice_prompt', template: 'You are a practice session assistant. Present the following scenario to the learner...', variables_schema: { type: 'object', properties: { scenario_text: { type: 'string' } } }, output_schema: null, status: 'archived', parent_version_id: null, created_at: '2025-01-10T00:00:00Z', updated_at: '2025-02-01T00:00:00Z' },
    { id: 2, name: 'quick_practice_prompt', version: 'v1.1.0', prompt_type: 'quick_practice_prompt', template: 'You are a professional practice coach. Guide the learner through the scenario...', variables_schema: { type: 'object', properties: { scenario_text: { type: 'string' }, difficulty: { type: 'string' } } }, output_schema: null, status: 'archived', parent_version_id: 1, created_at: '2025-02-01T00:00:00Z', updated_at: '2025-03-15T00:00:00Z' },
    { id: 3, name: 'quick_practice_prompt', version: 'v1.2.0', prompt_type: 'quick_practice_prompt', template: 'You are an expert soft skills coach. Engage the learner with: {{scenario_text}}. Difficulty: {{difficulty}}. Focus on: {{skill_focus}}', variables_schema: { type: 'object', properties: { scenario_text: { type: 'string' }, difficulty: { type: 'string' }, skill_focus: { type: 'string' } } }, output_schema: { type: 'object', properties: { response: { type: 'string' } } }, status: 'published', parent_version_id: 2, created_at: '2025-03-15T00:00:00Z', updated_at: '2025-06-01T00:00:00Z' },
  ],
  'interview_turn_prompt': [
    { id: 10, name: 'interview_turn_prompt', version: 'v1.0.0', prompt_type: 'interview_prompt', template: 'Present an interview question based on: {{topic}}', variables_schema: { type: 'object', properties: { topic: { type: 'string' } } }, output_schema: null, status: 'archived', parent_version_id: null, created_at: '2025-02-15T00:00:00Z', updated_at: '2025-04-01T00:00:00Z' },
    { id: 11, name: 'interview_turn_prompt', version: 'v2.0.0', prompt_type: 'interview_prompt', template: 'You are conducting a structured interview. Ask a question about {{topic}} that assesses {{skill}}. Follow up naturally on the response.', variables_schema: { type: 'object', properties: { topic: { type: 'string' }, skill: { type: 'string' } } }, output_schema: { type: 'object', properties: { question: { type: 'string' }, follow_up: { type: 'string' } } }, status: 'published', parent_version_id: 10, created_at: '2025-04-01T00:00:00Z', updated_at: '2025-08-01T00:00:00Z' },
  ],
  'scenario_step_prompt': [
    { id: 20, name: 'scenario_step_prompt', version: 'v1.0.0', prompt_type: 'scenario_step', template: 'Set up the scenario: {{scenario_context}}', variables_schema: { type: 'object', properties: { scenario_context: { type: 'string' } } }, output_schema: null, status: 'archived', parent_version_id: null, created_at: '2025-03-01T00:00:00Z', updated_at: '2025-05-01T00:00:00Z' },
    { id: 21, name: 'scenario_step_prompt', version: 'v1.1.0', prompt_type: 'scenario_step', template: 'Present the scenario step: {{step_description}}. Stakeholder: {{stakeholder_name}}, Role: {{stakeholder_role}}. Guide the learner through this step.', variables_schema: { type: 'object', properties: { step_description: { type: 'string' }, stakeholder_name: { type: 'string' }, stakeholder_role: { type: 'string' } } }, output_schema: { type: 'object', properties: { prompt: { type: 'string' } } }, status: 'published', parent_version_id: 20, created_at: '2025-05-01T00:00:00Z', updated_at: '2025-07-01T00:00:00Z' },
  ],
};

const SEED_PIPELINES: PipelineDefinitionView[] = [
  { pipeline_name: 'assistant_turn', topology: 'assistant_turn', description: 'Single assistant turn through input guard to runtime', stage_count: 6, created_at: '2025-01-01T00:00:00Z', updated_at: '2025-06-01T00:00:00Z' },
  { pipeline_name: 'assessment_flow', topology: 'assessment_flow', description: 'Full assessment pipeline from submission to scoring', stage_count: 8, created_at: '2025-02-01T00:00:00Z', updated_at: '2025-07-01T00:00:00Z' },
  { pipeline_name: 'collection_generation', topology: 'collection_generation', description: 'AI-powered collection creation pipeline', stage_count: 10, created_at: '2025-03-01T00:00:00Z', updated_at: '2025-08-01T00:00:00Z' },
];

const SEED_PIPELINE_DAGS: Record<string, PipelineDAGView> = {
  'assistant_turn': {
    pipeline_name: 'assistant_turn',
    topology: 'assistant_turn',
    description: 'Single assistant turn through input guard to runtime',
    stages: [
      { name: 'input_guard', kind: 'GUARD', dependencies: [], runner_class: 'InputGuardStage', description: 'Turn status check, cancellation handling' },
      { name: 'history_enrich', kind: 'ENRICH', dependencies: ['input_guard'], runner_class: 'HistoryEnrichStage', description: 'Conversation history loading' },
      { name: 'profile_enrich', kind: 'ENRICH', dependencies: ['input_guard'], runner_class: 'ProfileEnrichStage', description: 'Learner profile loading' },
      { name: 'progress_enrich', kind: 'ENRICH', dependencies: ['input_guard'], runner_class: 'ProgressEnrichStage', description: 'Progression dashboard loading' },
      { name: 'attempts_enrich', kind: 'ENRICH', dependencies: ['input_guard'], runner_class: 'AttemptsEnrichStage', description: 'Recent attempts loading' },
      { name: 'assistant_runtime', kind: 'AGENT', dependencies: ['history_enrich', 'profile_enrich', 'progress_enrich', 'attempts_enrich'], runner_class: 'AssistantRuntimeStage', description: 'Main LLM orchestrator with tool execution' },
    ],
  },
  'assessment_flow': {
    pipeline_name: 'assessment_flow',
    topology: 'assessment_flow',
    description: 'Full assessment pipeline from submission to scoring',
    stages: [
      { name: 'submission_guard', kind: 'GUARD', dependencies: [], runner_class: 'SubmissionGuardStage', description: 'Validates submission payload' },
      { name: 'prompt_retrieval', kind: 'TRANSFORM', dependencies: ['submission_guard'], runner_class: 'PromptRetrievalStage', description: 'Loads prompt template and variables' },
      { name: 'llm_evaluation', kind: 'WORK', dependencies: ['prompt_retrieval'], runner_class: 'LLMEvaluationStage', description: 'Calls LLM to evaluate response' },
      { name: 'score_aggregation', kind: 'TRANSFORM', dependencies: ['llm_evaluation'], runner_class: 'ScoreAggregationStage', description: 'Aggregates scores across criteria' },
      { name: 'validation_check', kind: 'GUARD', dependencies: ['score_aggregation'], runner_class: 'ValidationCheckStage', description: 'Validates assessment against rubric' },
      { name: 'result_persistence', kind: 'WORK', dependencies: ['validation_check'], runner_class: 'ResultPersistenceStage', description: 'Stores assessment result' },
      { name: 'notification_dispatch', kind: 'WORK', dependencies: ['result_persistence'], runner_class: 'NotificationDispatchStage', description: 'Sends notification to learner' },
      { name: 'metrics_emission', kind: 'WORK', dependencies: ['result_persistence'], runner_class: 'MetricsEmissionStage', description: 'Emits usage metrics' },
    ],
  },
  'collection_generation': {
    pipeline_name: 'collection_generation',
    topology: 'collection_generation',
    description: 'AI-powered collection creation pipeline',
    stages: [
      { name: 'input_guard', kind: 'GUARD', dependencies: [], runner_class: 'GenerationInputGuardStage', description: 'Validates generation request' },
      { name: 'blueprint_transform', kind: 'TRANSFORM', dependencies: ['input_guard'], runner_class: 'BlueprintTransformStage', description: 'Generates collection blueprint' },
      { name: 'blueprint_guard', kind: 'GUARD', dependencies: ['blueprint_transform'], runner_class: 'BlueprintGuardStage', description: 'Validates blueprint quality' },
      { name: 'prompt_items_work', kind: 'WORK', dependencies: ['blueprint_guard'], runner_class: 'PromptItemsWorkStage', description: 'Generates prompt items' },
      { name: 'scenarios_work', kind: 'WORK', dependencies: ['blueprint_guard'], runner_class: 'ScenariosWorkStage', description: 'Generates scenario content' },
      { name: 'assemble_transform', kind: 'TRANSFORM', dependencies: ['prompt_items_work', 'scenarios_work'], runner_class: 'AssembleTransformStage', description: 'Assembles final collection' },
      { name: 'output_guard', kind: 'GUARD', dependencies: ['assemble_transform'], runner_class: 'OutputGuardStage', description: 'Validates assembled collection' },
      { name: 'persistence_work', kind: 'WORK', dependencies: ['output_guard'], runner_class: 'PersistenceWorkStage', description: 'Persists collection to database' },
      { name: 'indexing_transform', kind: 'TRANSFORM', dependencies: ['persistence_work'], runner_class: 'IndexingTransformStage', description: 'Updates search indexes' },
      { name: 'completion_work', kind: 'WORK', dependencies: ['indexing_transform'], runner_class: 'CompletionWorkStage', description: 'Marks generation complete' },
    ],
  },
};

const SEED_PIPELINE_RUNS: Record<string, PipelineRunSummaryView[]> = {
  'assistant_turn': [
    { pipeline_run_id: 'pr-001', pipeline_name: 'assistant_turn', status: 'completed', execution_mode: 'async', user_id: 'usr-002', request_id: 'req-001', trace_id: 'trace-001', error: null, failed_stage: null, started_at: isoDate(1), finished_at: isoDate(1), duration_ms: 1250 },
    { pipeline_run_id: 'pr-002', pipeline_name: 'assistant_turn', status: 'completed', execution_mode: 'async', user_id: 'usr-003', request_id: 'req-002', trace_id: 'trace-002', error: null, failed_stage: null, started_at: isoDate(1), finished_at: isoDate(1), duration_ms: 1380 },
    { pipeline_run_id: 'pr-003', pipeline_name: 'assistant_turn', status: 'failed', execution_mode: 'async', user_id: 'usr-004', request_id: 'req-003', trace_id: 'trace-003', error: 'LLM timeout after 30s', failed_stage: 'assistant_runtime', started_at: isoDate(2), finished_at: isoDate(2), duration_ms: 30200 },
    { pipeline_run_id: 'pr-004', pipeline_name: 'assistant_turn', status: 'completed', execution_mode: 'async', user_id: 'usr-005', request_id: 'req-004', trace_id: 'trace-004', error: null, failed_stage: null, started_at: isoDate(3), finished_at: isoDate(3), duration_ms: 1120 },
    { pipeline_run_id: 'pr-005', pipeline_name: 'assistant_turn', status: 'completed', execution_mode: 'async', user_id: 'usr-006', request_id: 'req-005', trace_id: 'trace-005', error: null, failed_stage: null, started_at: isoDate(4), finished_at: isoDate(4), duration_ms: 1450 },
  ],
  'assessment_flow': [
    { pipeline_run_id: 'pr-010', pipeline_name: 'assessment_flow', status: 'completed', execution_mode: 'async', user_id: 'usr-002', request_id: 'req-010', trace_id: 'trace-010', error: null, failed_stage: null, started_at: isoDate(1), finished_at: isoDate(1), duration_ms: 3420 },
    { pipeline_run_id: 'pr-011', pipeline_name: 'assessment_flow', status: 'completed', execution_mode: 'async', user_id: 'usr-003', request_id: 'req-011', trace_id: 'trace-011', error: null, failed_stage: null, started_at: isoDate(2), finished_at: isoDate(2), duration_ms: 3680 },
    { pipeline_run_id: 'pr-012', pipeline_name: 'assessment_flow', status: 'failed', execution_mode: 'async', user_id: 'usr-004', request_id: 'req-012', trace_id: 'trace-012', error: 'Validation failed: score below threshold', failed_stage: 'validation_check', started_at: isoDate(3), finished_at: isoDate(3), duration_ms: 2890 },
  ],
};

const SEED_PIPELINE_TRACES: Record<string, PipelineTraceView> = {
  'pr-001': {
    pipeline_run_id: 'pr-001',
    pipeline_name: 'assistant_turn',
    execution_sequence: [
      { stage_name: 'input_guard', event_type: 'STARTED', timestamp: isoDate(1), duration_ms: 12, status: 'OK', error: null },
      { stage_name: 'history_enrich', event_type: 'STARTED', timestamp: isoDate(1), duration_ms: 85, status: 'OK', error: null },
      { stage_name: 'profile_enrich', event_type: 'STARTED', timestamp: isoDate(1), duration_ms: 92, status: 'OK', error: null },
      { stage_name: 'progress_enrich', event_type: 'STARTED', timestamp: isoDate(1), duration_ms: 78, status: 'OK', error: null },
      { stage_name: 'attempts_enrich', event_type: 'STARTED', timestamp: isoDate(1), duration_ms: 65, status: 'OK', error: null },
      { stage_name: 'assistant_runtime', event_type: 'STARTED', timestamp: isoDate(1), duration_ms: 918, status: 'OK', error: null },
    ],
    total_duration_ms: 1250,
    started_at: isoDate(1),
    completed_at: isoDate(1),
  },
  'pr-003': {
    pipeline_run_id: 'pr-003',
    pipeline_name: 'assistant_turn',
    execution_sequence: [
      { stage_name: 'input_guard', event_type: 'STARTED', timestamp: isoDate(2), duration_ms: 15, status: 'OK', error: null },
      { stage_name: 'history_enrich', event_type: 'STARTED', timestamp: isoDate(2), duration_ms: 102, status: 'OK', error: null },
      { stage_name: 'profile_enrich', event_type: 'STARTED', timestamp: isoDate(2), duration_ms: 95, status: 'OK', error: null },
      { stage_name: 'progress_enrich', event_type: 'STARTED', timestamp: isoDate(2), duration_ms: 88, status: 'OK', error: null },
      { stage_name: 'attempts_enrich', event_type: 'STARTED', timestamp: isoDate(2), duration_ms: 72, status: 'OK', error: null },
      { stage_name: 'assistant_runtime', event_type: 'STARTED', timestamp: isoDate(2), duration_ms: null, status: 'FAIL', error: 'LLM timeout after 30s' },
    ],
    total_duration_ms: 30200,
    started_at: isoDate(2),
    completed_at: isoDate(2),
  },
};

const SEED_PIPELINE_METRICS: Record<string, PipelineMetricsView> = {
  'assistant_turn': {
    pipeline_name: 'assistant_turn',
    total_runs: 1247,
    success_count: 1198,
    failure_count: 34,
    cancel_count: 15,
    success_rate: 1198 / 1247,
    avg_duration_ms: 920.5,
    p95_duration_ms: 1250,
    stage_metrics: [
      { stage_name: 'input_guard', invocation_count: 1247, success_count: 1247, failure_count: 0, skip_count: 0, cancel_count: 15, retry_count: 0, avg_duration_ms: 12.4, p50_duration_ms: 11, p95_duration_ms: 18, p99_duration_ms: 25 },
      { stage_name: 'history_enrich', invocation_count: 1232, success_count: 1230, failure_count: 2, skip_count: 0, cancel_count: 15, retry_count: 5, avg_duration_ms: 89.2, p50_duration_ms: 85, p95_duration_ms: 120, p99_duration_ms: 180 },
      { stage_name: 'profile_enrich', invocation_count: 1232, success_count: 1231, failure_count: 1, skip_count: 0, cancel_count: 15, retry_count: 3, avg_duration_ms: 94.5, p50_duration_ms: 90, p95_duration_ms: 130, p99_duration_ms: 195 },
      { stage_name: 'progress_enrich', invocation_count: 1232, success_count: 1232, failure_count: 0, skip_count: 0, cancel_count: 15, retry_count: 0, avg_duration_ms: 78.3, p50_duration_ms: 75, p95_duration_ms: 110, p99_duration_ms: 160 },
      { stage_name: 'attempts_enrich', invocation_count: 1232, success_count: 1232, failure_count: 0, skip_count: 0, cancel_count: 15, retry_count: 0, avg_duration_ms: 67.8, p50_duration_ms: 65, p95_duration_ms: 95, p99_duration_ms: 140 },
      { stage_name: 'assistant_runtime', invocation_count: 1232, success_count: 1198, failure_count: 34, skip_count: 0, cancel_count: 15, retry_count: 45, avg_duration_ms: 920.5, p50_duration_ms: 890, p95_duration_ms: 1250, p99_duration_ms: 2500 },
    ],
  },
  'assessment_flow': {
    pipeline_name: 'assessment_flow',
    total_runs: 856,
    success_count: 812,
    failure_count: 28,
    cancel_count: 16,
    success_rate: 812 / 856,
    avg_duration_ms: 1850.0,
    p95_duration_ms: 2400,
    stage_metrics: [
      { stage_name: 'submission_guard', invocation_count: 856, success_count: 856, failure_count: 0, skip_count: 0, cancel_count: 16, retry_count: 0, avg_duration_ms: 8.2, p50_duration_ms: 8, p95_duration_ms: 12, p99_duration_ms: 18 },
      { stage_name: 'prompt_retrieval', invocation_count: 840, success_count: 840, failure_count: 0, skip_count: 0, cancel_count: 16, retry_count: 0, avg_duration_ms: 45.6, p50_duration_ms: 42, p95_duration_ms: 68, p99_duration_ms: 95 },
      { stage_name: 'llm_evaluation', invocation_count: 840, success_count: 825, failure_count: 15, skip_count: 0, cancel_count: 16, retry_count: 25, avg_duration_ms: 1850.0, p50_duration_ms: 1800, p95_duration_ms: 2400, p99_duration_ms: 3200 },
      { stage_name: 'score_aggregation', invocation_count: 825, success_count: 823, failure_count: 2, skip_count: 0, cancel_count: 16, retry_count: 4, avg_duration_ms: 125.3, p50_duration_ms: 120, p95_duration_ms: 180, p99_duration_ms: 250 },
      { stage_name: 'validation_check', invocation_count: 823, success_count: 815, failure_count: 8, skip_count: 0, cancel_count: 16, retry_count: 10, avg_duration_ms: 56.8, p50_duration_ms: 54, p95_duration_ms: 85, p99_duration_ms: 120 },
      { stage_name: 'result_persistence', invocation_count: 815, success_count: 815, failure_count: 0, skip_count: 0, cancel_count: 16, retry_count: 0, avg_duration_ms: 234.5, p50_duration_ms: 220, p95_duration_ms: 340, p99_duration_ms: 480 },
      { stage_name: 'notification_dispatch', invocation_count: 815, success_count: 812, failure_count: 3, skip_count: 0, cancel_count: 16, retry_count: 8, avg_duration_ms: 89.2, p50_duration_ms: 85, p95_duration_ms: 130, p99_duration_ms: 180 },
      { stage_name: 'metrics_emission', invocation_count: 815, success_count: 812, failure_count: 0, skip_count: 3, cancel_count: 16, retry_count: 0, avg_duration_ms: 34.5, p50_duration_ms: 32, p95_duration_ms: 52, p99_duration_ms: 75 },
    ],
  },
};

const SEED_RUBRICS_ADMIN: RubricAdminView[] = [
  {
    rubric_id: 'quick_practice_text@v1',
    family: 'quick_practice_text',
    version: 'v1',
    content_type: 'quick_practice',
    schema_version: '1.0',
    name: 'Quick Practice Text Rubric',
    criteria: [
      { criterion_ref: 'clarity', skill_slug: 'communication', title: 'Clarity', description: 'How clearly does the response convey the main point?', weight: 0.3, required: true, position: 1, levels: [{ level: 1, description: 'Vague or confusing', examples: ['Uses filler words excessively'] }, { level: 2, description: 'Somewhat clear', examples: ['Main point is identifiable'] }, { level: 3, description: 'Clear and direct', examples: ['Main point is clear and well-stated'] }, { level: 4, description: 'Very clear and impactful', examples: ['Message is compelling and memorable'] }, { level: 5, description: 'Exceptional clarity', examples: ['Perfectly articulated with strong impact'] }] },
      { criterion_ref: 'relevance', skill_slug: 'active-listening', title: 'Relevance', description: 'How well does the response address the scenario?', weight: 0.25, required: true, position: 2, levels: [{ level: 1, description: 'Off-topic', examples: ['Does not address the prompt'] }, { level: 2, description: 'Partially relevant', examples: ['Addresses some aspects'] }, { level: 3, description: 'Mostly relevant', examples: ['Addresses most aspects'] }, { level: 4, description: 'Highly relevant', examples: ['Fully addresses the prompt'] }, { level: 5, description: 'Perfectly tailored', examples: ['Exceeds expectations'] }] },
      { criterion_ref: 'structure', skill_slug: 'critical-thinking', title: 'Structure', description: 'How well-organized is the response?', weight: 0.2, required: false, position: 3, levels: [{ level: 1, description: 'Disorganized', examples: ['No logical flow'] }, { level: 2, description: 'Somewhat organized', examples: ['Basic structure present'] }, { level: 3, description: 'Well-organized', examples: ['Clear beginning, middle, end'] }, { level: 4, description: 'Very well-organized', examples: ['Excellent flow and transitions'] }, { level: 5, description: 'Expertly structured', examples: ['Textbook example of structure'] }] },
    ],
  },
  {
    rubric_id: 'interview_scenario@v2',
    family: 'interview_scenario',
    version: 'v2',
    content_type: 'interview',
    schema_version: '2.0',
    name: 'Interview Scenario Rubric v2',
    criteria: [
      { criterion_ref: 'situation-awareness', skill_slug: 'situational-awareness', title: 'Situation Awareness', description: 'Demonstrates understanding of the scenario context', weight: 0.35, required: true, position: 1, levels: [{ level: 1, description: 'No awareness', examples: ['Ignores context entirely'] }, { level: 2, description: 'Limited awareness', examples: ['Shows basic understanding'] }, { level: 3, description: 'Good awareness', examples: ['Demonstrates solid context understanding'] }, { level: 4, description: 'Strong awareness', examples: ['Shows deep context appreciation'] }, { level: 5, description: 'Exceptional awareness', examples: ['Demonstrates expert-level understanding'] }] },
      { criterion_ref: 'stakeholder-handling', skill_slug: 'conflict-resolution', title: 'Stakeholder Handling', description: 'How well are stakeholder concerns addressed?', weight: 0.35, required: true, position: 2, levels: [{ level: 1, description: 'Ignores stakeholders', examples: ['No stakeholder consideration'] }, { level: 2, description: 'Addresses some', examples: ['Mentions some stakeholder concerns'] }, { level: 3, description: 'Balances interests', examples: ['Considers multiple perspectives'] }, { level: 4, description: 'Strong stakeholder focus', examples: ['Prioritizes stakeholder needs effectively'] }, { level: 5, description: 'Expert stakeholder management', examples: ['Demonstrates masterful stakeholder navigation'] }] },
      { criterion_ref: 'actionability', skill_slug: 'problem-solving', title: 'Actionability', description: 'Does the response provide actionable next steps?', weight: 0.3, required: true, position: 3, levels: [{ level: 1, description: 'No actions', examples: ['Vague or no next steps'] }, { level: 2, description: 'Generic actions', examples: ['Generic next steps provided'] }, { level: 3, description: 'Specific actions', examples: ['Clear, specific next steps'] }, { level: 4, description: 'Detailed actions', examples: ['Comprehensive action plan'] }, { level: 5, description: 'Exceptional plan', examples: ['Detailed, prioritized action plan with contingencies'] }] },
    ],
  },
  {
    rubric_id: 'scenario_assessment@v1',
    family: 'scenario_assessment',
    version: 'v1',
    content_type: 'scenario',
    schema_version: '1.0',
    name: 'Scenario Assessment Rubric',
    criteria: [
      { criterion_ref: 'rapport-building', skill_slug: 'empathy', title: 'Rapport Building', description: 'Establishes rapport with stakeholders', weight: 0.25, required: true, position: 1, levels: [{ level: 1, description: 'No rapport', examples: ['Cold or dismissive'] }, { level: 2, description: 'Minimal rapport', examples: ['Basic politeness'] }, { level: 3, description: 'Good rapport', examples: ['Friendly and professional'] }, { level: 4, description: 'Strong rapport', examples: ['Builds genuine connection'] }, { level: 5, description: 'Exceptional rapport', examples: ['Natural rapport that puts others at ease'] }] },
      { criterion_ref: 'problem-resolution', skill_slug: 'problem-solving', title: 'Problem Resolution', description: 'Effectively resolves the presented problem', weight: 0.4, required: true, position: 2, levels: [{ level: 1, description: 'No resolution', examples: ['Problem remains unaddressed'] }, { level: 2, description: 'Partial resolution', examples: ['Addresses some aspects'] }, { level: 3, description: 'Good resolution', examples: ['Resolves most aspects'] }, { level: 4, description: 'Strong resolution', examples: ['Fully resolves the problem'] }, { level: 5, description: 'Exceptional resolution', examples: ['Exceeds expectations with creative solution'] }] },
      { criterion_ref: 'follow-through', skill_slug: 'accountability', title: 'Follow Through', description: 'Commits to and communicates follow-up actions', weight: 0.35, required: true, position: 3, levels: [{ level: 1, description: 'No follow-through', examples: ['No commitment to next steps'] }, { level: 2, description: 'Vague commitment', examples: ['Generic follow-up mentioned'] }, { level: 3, description: 'Clear commitment', examples: ['Specific follow-up with timeline'] }, { level: 4, description: 'Strong commitment', examples: ['Detailed follow-up with ownership'] }, { level: 5, description: 'Exceptional follow-through', examples: ['Comprehensive plan with accountability measures'] }] },
    ],
  },
];

const SEED_WORKFLOW_EVENTS: WorkflowEventView[] = [
  { event_id: 'evt-001', event_type: 'attempt.submitted', request_id: 'req-001', trace_id: 'trace-001', workflow_id: 'wf-001', error_code: null, payload: { attempt_id: 'att-001', user_id: 'usr-002' }, occurred_at: isoDate(1) },
  { event_id: 'evt-002', event_type: 'assessment.validated', request_id: 'req-002', trace_id: 'trace-002', workflow_id: 'wf-002', error_code: null, payload: { attempt_id: 'att-002', score: 4 }, occurred_at: isoDate(1) },
  { event_id: 'evt-003', event_type: 'assessment.rejected', request_id: 'req-003', trace_id: 'trace-003', workflow_id: 'wf-003', error_code: 'SS-ASSESSMENT-001', payload: { attempt_id: 'att-003', rejection_reason: 'Score below minimum threshold' }, occurred_at: isoDate(2) },
  { event_id: 'evt-004', event_type: 'pipeline.failed', request_id: 'req-004', trace_id: 'trace-004', workflow_id: 'wf-004', error_code: 'SS-PIPELINE-002', payload: { pipeline_name: 'assistant_turn', failed_stage: 'assistant_runtime', error: 'LLM timeout' }, occurred_at: isoDate(2) },
  { event_id: 'evt-005', event_type: 'session.started', request_id: 'req-005', trace_id: 'trace-005', workflow_id: 'wf-005', error_code: null, payload: { session_id: 'sess-001', practice_type: 'quick_practice' }, occurred_at: isoDate(3) },
  { event_id: 'evt-006', event_type: 'collection.created', request_id: 'req-006', trace_id: 'trace-006', workflow_id: 'wf-006', error_code: null, payload: { collection_id: 'col-001', author_user_id: 'usr-003' }, occurred_at: isoDate(4) },
  { event_id: 'evt-007', event_type: 'user.login', request_id: 'req-007', trace_id: 'trace-007', workflow_id: null, error_code: null, payload: { user_id: 'usr-002', auth_provider: 'google' }, occurred_at: isoDate(1) },
  { event_id: 'evt-008', event_type: 'eval_run.completed', request_id: 'req-008', trace_id: 'trace-008', workflow_id: null, error_code: null, payload: { run_id: 'run-001', suite_id: 'suite-001', passed: true, pass_rate: 0.92 }, occurred_at: isoDate(7) },
];

let _adminUsers = [...SEED_ADMIN_USERS];
let _learnerRelationships = new Map<string, AdminLearnerRelationshipView>();
let _rubricsAdmin: RubricAdminView[] = [...SEED_RUBRICS_ADMIN];
let _workflowEvents = [...SEED_WORKFLOW_EVENTS];

const SEED_ORG_SKILLS: OrgSkillView[] = [
  { slug: 'effective-communication', name: 'Effective Communication', description: 'Conveys ideas clearly and persuasively in verbal and written form', organisation_id: 'org-001' },
  { slug: 'team-collaboration', name: 'Team Collaboration', description: 'Works effectively with others to achieve shared goals', organisation_id: 'org-001' },
  { slug: 'problem-solving', name: 'Problem Solving', description: 'Identifies issues and develops practical solutions', organisation_id: 'org-001' },
  { slug: 'leadership', name: 'Leadership', description: 'Guides and motivates others toward achieving objectives', organisation_id: 'org-001' },
  { slug: 'adaptability', name: 'Adaptability', description: 'Adjusts approach and mindset to changing circumstances', organisation_id: 'org-001' },
  { slug: 'time-management', name: 'Time Management', description: 'Prioritizes tasks and manages time efficiently', organisation_id: 'org-001' },
  { slug: 'critical-thinking', name: 'Critical Thinking', description: 'Analyzes information to form well-reasoned judgments', organisation_id: 'org-001' },
  { slug: 'conflict-resolution', name: 'Conflict Resolution', description: 'Mediates disputes and finds mutually acceptable solutions', organisation_id: 'org-001' },
];

const SEED_ORG_COMPETENCIES: OrgCompetencyView[] = [
  { slug: 'communication-expertise', name: 'Communication Expertise', description: 'Mastery of effective communication across various contexts', skill_slugs: ['effective-communication', 'active-listening'], organisation_id: 'org-001' },
  { slug: 'teamwork-excellence', name: 'Teamwork Excellence', description: 'Demonstrates exceptional collaboration and team synergy', skill_slugs: ['team-collaboration', 'conflict-resolution'], organisation_id: 'org-001' },
  { slug: 'analytical-prowess', name: 'Analytical Prowess', description: 'Strong analytical and critical thinking capabilities', skill_slugs: ['problem-solving', 'critical-thinking'], organisation_id: 'org-001' },
  { slug: 'leadership-ability', name: 'Leadership Ability', description: 'Capable of guiding teams and making decisions', skill_slugs: ['leadership', 'effective-communication'], organisation_id: 'org-001' },
  { slug: 'agile-adaptation', name: 'Agile Adaptation', description: 'Thrives in changing environments with flexibility', skill_slugs: ['adaptability', 'time-management'], organisation_id: 'org-001' },
];

const SEED_ORG_RUBRICS: OrgRubricView[] = [
  { rubric_id: 'org-rubric-001', family: 'org_communication', version: 'v1', content_type: 'interview', schema_version: '1.0', name: 'Org Communication Rubric', criteria: ['clarity', 'relevance', 'engagement'], organisation_id: 'org-001' },
  { rubric_id: 'org-rubric-002', family: 'org_leadership', version: 'v1', content_type: 'scenario', schema_version: '1.0', name: 'Org Leadership Rubric', criteria: ['decision-making', 'delegation', 'accountability'], organisation_id: 'org-001' },
  { rubric_id: 'org-rubric-003', family: 'org_problem_solving', version: 'v1', content_type: 'quick_practice', schema_version: '1.0', name: 'Org Problem Solving Rubric', criteria: ['analysis', 'creativity', 'implementation'], organisation_id: 'org-001' },
];

const SEED_ORG_PROMPT_ITEMS: PromptItemView[] = [
  { id: 'org-prompt-001', prompt_type: 'interview_prompt', title: 'Team Conflict Scenario', prompt_text: 'Describe how you would handle a conflict within your team', difficulty: 'intermediate', lifecycle_state: 'published_private', target_skill_slugs: ['conflict-resolution', 'communication'], rubric_id: 'org-rubric-001', organisation_id: 'org-001' },
  { id: 'org-prompt-002', prompt_type: 'quick_practice_prompt', title: 'Project Kickoff Briefing', prompt_text: 'Lead a project kickoff meeting with stakeholders', difficulty: 'advanced', lifecycle_state: 'published_private', target_skill_slugs: ['leadership', 'communication'], rubric_id: 'org-rubric-001', organisation_id: 'org-001' },
  { id: 'org-prompt-003', prompt_type: 'interview_prompt', title: 'Performance Review Delivery', prompt_text: 'Deliver constructive feedback during a performance review', difficulty: 'advanced', lifecycle_state: 'published_private', target_skill_slugs: ['communication', 'leadership'], rubric_id: 'org-rubric-002', organisation_id: 'org-001' },
  { id: 'org-prompt-004', prompt_type: 'quick_practice_prompt', title: 'Stakeholder Update', prompt_text: 'Present a project status update to executive stakeholders', difficulty: 'intermediate', lifecycle_state: 'draft', target_skill_slugs: ['communication'], rubric_id: 'org-rubric-001', organisation_id: 'org-001' },
];

const SEED_ORG_SCENARIOS: ScenarioView[] = [
  { id: 'org-scenario-001', title: 'Budget Presentation', business_context: 'Present a budget proposal to senior leadership', learner_objective: 'Develop executive presence and financial communication skills', constraints: ['Time limit of 15 minutes', 'Must address all stakeholder concerns'], stakeholder_tensions: ['Cost vs. quality', 'Short-term vs. long-term priorities'], lifecycle_state: 'published_private', target_skill_slugs: ['communication', 'leadership'], rubric_id: 'org-rubric-002', mock_company: null, mock_people: [], organisation_id: 'org-001' },
  { id: 'org-scenario-002', title: 'New Hire Onboarding', business_context: 'Onboard a new team member with company processes', learner_objective: 'Master onboarding best practices and team integration', constraints: ['Must complete within 30 minutes', 'Cover all mandatory topics'], stakeholder_tensions: ['Thoroughness vs. efficiency', 'Standard process vs. personalized approach'], lifecycle_state: 'published_private', target_skill_slugs: ['leadership', 'communication'], rubric_id: 'org-rubric-002', mock_company: null, mock_people: [], organisation_id: 'org-001' },
  { id: 'org-scenario-003', title: 'Crisis Communication', business_context: 'Handle internal communication during a company crisis', learner_objective: 'Practice crisis communication and stakeholder management', constraints: ['Must address employee concerns within 24 hours', 'All communications must be approved by legal'], stakeholder_tensions: ['Transparency vs. legal risk', 'Employee concerns vs. business continuity'], lifecycle_state: 'published_private', target_skill_slugs: ['communication', 'problem-solving'], rubric_id: 'org-rubric-003', mock_company: null, mock_people: [], organisation_id: 'org-001' },
  { id: 'org-scenario-004', title: 'Cross-functional Collaboration', business_context: 'Coordinate a project across multiple departments', learner_objective: 'Improve cross-departmental collaboration skills', constraints: ['Limited budget', 'Tight timeline'], stakeholder_tensions: ['Different departmental priorities', 'Resource allocation conflicts'], lifecycle_state: 'draft', target_skill_slugs: ['team-collaboration', 'problem-solving'], rubric_id: 'org-rubric-003', mock_company: null, mock_people: [], organisation_id: 'org-001' },
];

let _orgSkills = [...SEED_ORG_SKILLS];
let _orgCompetencies = [...SEED_ORG_COMPETENCIES];
let _orgRubrics = [...SEED_ORG_RUBRICS];
let _orgPromptItems = [...SEED_ORG_PROMPT_ITEMS];
let _orgScenarios = [...SEED_ORG_SCENARIOS];

// Helper function to simulate tool flow based on keywords in chat messages
async function simulateToolFlow(
  sessionId: string,
  turnId: string,
  message: string,
  userMessage: AssistantMessageView,
  isGenerate: boolean,
  isPractice: boolean,
): Promise<void> {
  const session = SEED_ASSISTANT_SESSIONS.find(s => s.id === sessionId);
  if (!session) return;

  const turnIndex = SEED_TURNS.findIndex(t => t.id === turnId);
  if (turnIndex === -1) return;

  let toolCall: AssistantToolCallView;
  let assistantContent: string;

  if (isGenerate) {
    // --- GENERATION FLOW ---
    toolCall = {
      id: `tc-${uid()}`,
      turn_id: turnId,
      tool_name: 'generate_collection',
      status: 'running',
      args: { prompt: message, difficulty: 'intermediate' },
      result: null,
      error_code: null,
      error_message: null,
      child_run_id: null,
      started_at: new Date().toISOString(),
      completed_at: null,
    };

    // Simulate generation progress
    await delay(500);
    
    // Update with blueprint
    toolCall = {
      ...toolCall,
      result: {
        blueprint: {
          title: 'Generated: ' + message.slice(0, 30),
          summary: 'AI-generated practice content based on your request.',
          prompt_items_count: 3,
          scenarios_count: 1,
          model_slug: 'gpt-4',
        },
        progress_percent: 40,
        current_stage: 'blueprint_transform',
      },
    };

    await delay(800);

    // Update with prompt items
    toolCall = {
      ...toolCall,
      result: {
        ...toolCall.result,
        prompt_items: [
          { title: 'Quick Practice: Communication Skills', prompt_type: 'quick_practice_prompt', difficulty: 'intermediate' },
          { title: 'Interview: Leadership Scenario', prompt_type: 'interview_prompt', difficulty: 'advanced' },
          { title: 'Practice: Active Listening', prompt_type: 'quick_practice_prompt', difficulty: 'introductory' },
        ],
        progress_percent: 70,
        current_stage: 'prompt_items_work',
      },
    };

    await delay(800);

    // Complete
    toolCall = {
      ...toolCall,
      status: 'completed',
      result: {
        ...toolCall.result,
        collection_id: `col-${uid()}`,
        progress_percent: 100,
        current_stage: 'completed',
      },
      completed_at: new Date().toISOString(),
      child_run_id: `run-${uid()}`,
    };

    assistantContent = `I've generated a new collection based on your request: "${message}". The collection includes 3 practice prompts and 1 scenario covering communication, leadership, and active listening skills. You can find it in your Collections page!`;

  } else if (isPractice) {
    // --- PRACTICE FLOW ---
    toolCall = {
      id: `tc-${uid()}`,
      turn_id: turnId,
      tool_name: 'start_collection_practice',
      status: 'running',
      args: { collection_id: SEED_COLLECTIONS[0]?.id },
      result: null,
      error_code: null,
      error_message: null,
      child_run_id: null,
      started_at: new Date().toISOString(),
      completed_at: null,
    };

    await delay(600);

    // Update with practice session info
    toolCall = {
      ...toolCall,
      status: 'completed',
      result: {
        practice: {
          session_id: `practice-${uid()}`,
          collection_title: SEED_COLLECTIONS[0]?.title ?? 'Practice Collection',
          session_type: 'quick_practice',
          status: 'responding',
          current_step: 1,
          total_steps: 3,
          current_prompt_title: 'Tell me about a time you handled conflict',
        },
      },
      completed_at: new Date().toISOString(),
      child_run_id: `run-${uid()}`,
    };

    assistantContent = `I've started a practice session for you from the "${SEED_COLLECTIONS[0]?.title ?? 'Collection'}" collection. You're on step 1 of 3. The current prompt is: "Tell me about a time you handled conflict". Take your time and respond when ready!`;

  } else {
    // --- NORMAL FLOW (list_collections) ---
    toolCall = {
      id: `tc-${uid()}`,
      turn_id: turnId,
      tool_name: 'list_collections',
      status: 'running',
      args: {},
      result: null,
      error_code: null,
      error_message: null,
      child_run_id: null,
      started_at: new Date().toISOString(),
      completed_at: null,
    };

    await delay(400);

    // Complete with collection list
    toolCall = {
      ...toolCall,
      status: 'completed',
      result: {
        collections: SEED_COLLECTIONS.slice(0, 3).map(c => ({
          id: c.id,
          title: c.title,
          item_count: c.prompt_items.length + c.scenarios.length,
        })),
      },
      completed_at: new Date().toISOString(),
      child_run_id: `run-${uid()}`,
    };

    assistantContent = `I found ${SEED_COLLECTIONS.length} collections in your library. Based on your message "${message}", I'd recommend checking out "${SEED_COLLECTIONS[0]?.title}". Let me know if you'd like to practice with any of these!`;
  }

  // Update turn with completed tool call
  const assistantMessage: AssistantMessageView = {
    id: `msg-${uid()}`,
    turn_id: turnId,
    role: 'assistant',
    content: assistantContent,
    metadata: {},
    created_at: new Date().toISOString(),
  };

  const baseTurn = SEED_TURNS[turnIndex];
  if (!baseTurn) {
    return;
  }

  const completedTurn: AssistantTurnView = {
    ...baseTurn,
    status: 'completed',
    assistant_message_id: assistantMessage.id,
    completed_at: new Date().toISOString(),
    messages: [...baseTurn.messages, assistantMessage],
    tool_calls: [toolCall],
  };
  SEED_TURNS[turnIndex] = completedTurn;

  // Update session
  const updatedSession: AssistantSessionView = {
    ...session,
    messages: [...session.messages, userMessage, assistantMessage],
    turns: [...session.turns, completedTurn],
    updated_at: new Date().toISOString(),
  };

  const sessionIndex = SEED_ASSISTANT_SESSIONS.findIndex(s => s.id === sessionId);
  if (sessionIndex !== -1) {
    SEED_ASSISTANT_SESSIONS[sessionIndex] = updatedSession;
  }
}

export const mockDataProvider: DataProvider = {
  // --- Auth / Identity -----------------------------------------------------
  async getAuthSession(): Promise<AuthSessionView> {
    await delay(100);
    return syncMockUserFromSession();
  },

  async setActiveOrganisation(organisationId: string | null): Promise<AuthSessionView> {
    await delay(80);
    const session = requireAuthenticatedSession();
    if (organisationId === null) {
      setStoredActiveOrgId(null);
      return syncMockUserFromSession();
    }
    if (session.platform_role !== 'superadmin' && !getMembership(session, organisationId)) {
      throw new Error(`Organisation ${organisationId} is not available for this actor`);
    }
    setStoredActiveOrgId(organisationId);
    return syncMockUserFromSession();
  },

  async listAuthProfiles(): Promise<AuthProfileView[]> {
    await delay(60);
    return MOCK_AUTH_PROFILES.map((profile) => ({
      ...profile,
      session: {
        ...profile.session,
        actor: profile.session.actor ? { ...profile.session.actor } : null,
        org_memberships: profile.session.org_memberships.map((membership) => ({ ...membership })),
        capabilities: [...profile.session.capabilities],
      },
    }));
  },

  async switchAuthProfile(profileId: string): Promise<AuthSessionView> {
    await delay(80);
    const profile = getProfileDefinition(profileId);
    setStoredProfileId(profile.id);
    setStoredActiveOrgId(profile.session.active_organisation_id);
    return syncMockUserFromSession();
  },

  async login(cmd: LoginUserCommand): Promise<UserView> {
    await delay();
    const profile = MOCK_AUTH_PROFILES.find((candidate) => candidate.session.actor?.email === cmd.email);
    if (!profile) {
      throw new Error('Invalid email or password');
    }
    setStoredProfileId(profile.id);
    setStoredActiveOrgId(profile.session.active_organisation_id);
    return syncMockUserFromSession().actor as UserView;
  },

  async register(cmd: RegisterUserCommand): Promise<UserView> {
    await delay();
    const user: UserView = {
      id: uid(),
      email: cmd.email,
      display_name: cmd.display_name,
      role: cmd.role ?? 'standard_user',
      auth_provider: 'local',
      created_at: new Date().toISOString(),
      profile: {
        target_role: cmd.target_role ?? null,
        goals: cmd.goals ?? [],
        practice_preferences: cmd.practice_preferences ?? {},
      },
      org_memberships: [],
    };
    _user = user;
    return user;
  },

  async getMe(): Promise<UserView> {
    await delay(150);
    syncMockUserFromSession();
    return _user;
  },

  async updateProfile(cmd: UpdateProfileCommand): Promise<UserView> {
    await delay();
    _user = {
      ..._user,
      profile: {
        target_role: cmd.target_role !== undefined ? cmd.target_role : _user.profile.target_role,
        goals: cmd.goals !== undefined ? cmd.goals ?? [] : _user.profile.goals,
        practice_preferences: cmd.practice_preferences !== undefined
          ? cmd.practice_preferences ?? {}
          : _user.profile.practice_preferences,
      },
    };
    return _user;
  },

  async deleteMe(): Promise<DeleteAccountResult> {
    await delay();
    const userId = syncMockUserFromSession().actor?.id ?? _user.id;
    setStoredProfileId('learner-alex');
    setStoredActiveOrgId('org-001');
    return { deleted_user_id: userId, status: 'deleted' };
  },

  // --- Organisations -------------------------------------------------------

  async createOrganisation(cmd: CreateOrganisationCommand): Promise<OrganisationView> {
    await delay();
    const session = syncMockUserFromSession();
    const actorId = session.actor?.id;
    if (!actorId) {
      throw new Error('Authentication required');
    }
    const existingSlug = _createdOrganisations.find((o) => o.slug === cmd.slug);
    if (existingSlug) {
      throw new Error('An organisation with this slug already exists');
    }
    const newOrg: OrganisationView = {
      id: `org-${uid()}`,
      name: cmd.name,
      slug: cmd.slug,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    _createdOrganisations.push(newOrg);
    const membership: OrganisationMembershipView = {
      organisation_id: newOrg.id,
      organisation_name: newOrg.name,
      role: 'org_admin',
      permissions: DEFAULT_ORG_ADMIN_PERMISSIONS,
    };
    _createdMemberships.push(membership);
    setStoredActiveOrgId(newOrg.id);
    return newOrg;
  },

  async listOrganisations(): Promise<OrganisationListView[]> {
    await delay();
    const session = syncMockUserFromSession();
    const actorId = session.actor?.id;
    if (!actorId) {
      return [];
    }
    const memberships = _createdMemberships.filter(
      (m) => m.organisation_id !== undefined,
    );
    return memberships
      .map((m) => {
        const org = _createdOrganisations.find((o) => o.id === m.organisation_id);
        if (!org) return null;
        return {
          id: org.id,
          name: org.name,
          slug: org.slug,
          member_count: 1,
        };
      })
      .filter((org): org is OrganisationListView => org !== null);
  },

  // --- Taxonomy ------------------------------------------------------------

  async getTaxonomy(): Promise<TaxonomySnapshot> {
    await delay(150);
    return {
      skills: SEED_SKILLS,
      competencies: SEED_COMPETENCIES,
      rubrics: SEED_RUBRICS,
      rubric_criteria: SEED_RUBRIC_CRITERIA,
    };
  },

  // --- Catalog -------------------------------------------------------------

  async listCollections(filters?: CollectionListFilters): Promise<CollectionView[]> {
    await delay();
    let result = _collections;
    if (filters?.difficulty) {
      result = result.filter((c) => c.difficulty === filters.difficulty);
    }
    if (filters?.skill_slug) {
      result = result.filter((c) => c.target_skill_slugs.includes(filters.skill_slug!));
    }
    if (filters?.competency_slug) {
      result = result.filter((c) => c.target_competency_slugs.includes(filters.competency_slug!));
    }
    if (filters?.discovery_tier) {
      result = result.filter((c) => c.discovery_tier === filters.discovery_tier);
    }
    if (filters?.author_user_id) {
      result = result.filter((c) => c.author_user_id === filters.author_user_id);
    }
    if (filters?.organisation_id) {
      result = result.filter((c) => c.organisation_id === filters.organisation_id);
    }
    if (!filters?.include_private) {
      result = result.filter((c) => c.discovery_tier === 'global_public');
    }
    if (filters?.saved_only) {
      const userSaves = _saves.get(_user.id);
      if (userSaves) {
        result = result.filter((c) => userSaves.has(c.id));
      } else {
        result = [];
      }
    }
    return result.map((c) => ({
      ...c,
      saved_by_actor: _saves.get(_user.id)?.has(c.id) ?? false,
      rated_by_actor: _ratings.get(c.id)?.get(_user.id) ?? null,
    }));
  },

  async getCollection(id: string): Promise<CollectionView> {
    await delay(200);
    const col = _collections.find((c) => c.id === id);
    if (!col) throw new Error(`Collection ${id} not found`);
    return {
      ...col,
      saved_by_actor: _saves.get(_user.id)?.has(id) ?? false,
      rated_by_actor: _ratings.get(id)?.get(_user.id) ?? null,
    };
  },

  async createCollection(cmd: CollectionCreateCommand): Promise<CollectionView> {
    await delay();
    const now = new Date().toISOString();
    const col: CollectionView = {
      id: `col-${uid()}`,
      author_user_id: _user.id,
      organisation_id: cmd.organisation_id ?? null,
      title: cmd.title,
      summary: cmd.summary,
      target_audience: cmd.target_audience,
      difficulty: cmd.difficulty,
      lifecycle_state: 'draft',
      verification_state: 'unverified',
      discovery_tier: 'private',
      source_type: 'manual',
      content_format_mix: cmd.content_format_mix ?? [],
      target_skill_slugs: cmd.target_skill_slugs,
      target_competency_slugs: cmd.target_competency_slugs,
      rubric_ids: cmd.rubric_ids,
      save_count: 0,
      saved_by_actor: false,
      avg_rating: null,
      rating_count: 0,
      rated_by_actor: null,
      featured: false,
      last_generation_artifact_id: null,
      created_at: now,
      updated_at: now,
      prompt_items: [],
      scenarios: [],
    };
    _collections = [..._collections, col];
    return col;
  },

  async addPromptItem(collectionId: string, cmd: PromptItemCreateCommand): Promise<CollectionView> {
    await delay();
    const colIdx = _collections.findIndex((c) => c.id === collectionId);
    if (colIdx === -1) throw new Error(`Collection ${collectionId} not found`);

    const newItem = {
      id: `pi-${uid()}`,
      prompt_type: cmd.prompt_type,
      title: cmd.title,
      prompt_text: cmd.prompt_text,
      difficulty: cmd.difficulty,
      lifecycle_state: 'draft' as const,
      target_skill_slugs: cmd.target_skill_slugs,
      rubric_id: cmd.rubric_id,
    };

    const updated = {
      ..._collections[colIdx]!,
      prompt_items: [..._collections[colIdx]!.prompt_items, newItem],
    };
    _collections = _collections.map((c, i) => (i === colIdx ? updated : c));
    return updated;
  },

  async addScenario(collectionId: string, cmd: ScenarioCreateCommand): Promise<CollectionView> {
    await delay();
    const colIdx = _collections.findIndex((c) => c.id === collectionId);
    if (colIdx === -1) throw new Error(`Collection ${collectionId} not found`);

    const newScenario = {
      id: `sc-${uid()}`,
      title: cmd.title,
      business_context: cmd.business_context,
      learner_objective: cmd.learner_objective,
      constraints: cmd.constraints ?? [],
      stakeholder_tensions: cmd.stakeholder_tensions ?? [],
      lifecycle_state: 'draft' as const,
      target_skill_slugs: cmd.target_skill_slugs,
      rubric_id: cmd.rubric_id,
      mock_company: cmd.mock_company
        ? { id: `mc-${uid()}`, ...cmd.mock_company }
        : null,
      mock_people: (cmd.mock_people ?? []).map((p) => ({
        id: `mp-${uid()}`,
        name: p.name,
        role: p.role,
        goals: p.goals ?? [],
        communication_style: p.communication_style,
        relationship_to_scenario: p.relationship_to_scenario,
      })),
    };

    const updated = {
      ..._collections[colIdx]!,
      scenarios: [..._collections[colIdx]!.scenarios, newScenario],
    };
    _collections = _collections.map((c, i) => (i === colIdx ? updated : c));
    return updated;
  },

  // --- Content Generation --------------------------------------------------

  async generateStructuredCollection(
    cmd: StructuredCollectionGenerationCommand,
  ): Promise<CollectionGenerationView> {
    await delay(2500); // simulate LLM generation latency
    const collectionId = `col-${uid()}`;
    const artifactId = `gen-${uid()}`;

    const promptItems: PromptItemView[] = [];
    const totalPrompts = (cmd.counts.quick_practice_prompt_count ?? 0) + (cmd.counts.interview_prompt_count ?? 0);
    const skillLabel = cmd.target_skill_slugs[0]?.replace(/-/g, ' ') ?? 'skill';

    for (let i = 0; i < totalPrompts; i++) {
      const promptType = i < (cmd.counts.quick_practice_prompt_count ?? 0) ? 'quick_practice_prompt' : 'interview_prompt';
      const typeLabel = promptType === 'quick_practice_prompt' ? 'quick practice' : 'interview';
      promptItems.push({
        id: `pi-${uid()}`,
        prompt_type: promptType,
        title: `${cmd.title_hint ?? 'Generated'} - ${typeLabel} ${i + 1}`,
        prompt_text: `Given the ${cmd.domain.toLowerCase()} context where ${cmd.workplace_context.toLowerCase()}, demonstrate your ability to ${skillLabel} when facing ${cmd.scenario_theme.toLowerCase()}.`,
        difficulty: cmd.difficulty,
        lifecycle_state: 'draft',
        target_skill_slugs: cmd.target_skill_slugs,
        rubric_id: cmd.rubric_ids[0] ?? 'default',
      });
    }

    const scenarios: ScenarioView[] = [];
    for (let i = 0; i < (cmd.counts.scenario_count ?? 0); i++) {
      scenarios.push({
        id: `sc-${uid()}`,
        title: `${cmd.title_hint ?? 'Generated Scenario'} ${i + 1}`,
        business_context: cmd.workplace_context,
        learner_objective: `Navigate ${cmd.scenario_theme.toLowerCase()} using ${cmd.target_skill_slugs.map((s) => s.replace(/-/g, ' ')).join(', ')}.`,
        constraints: ['Time-sensitive decision required', 'Multiple stakeholder perspectives to consider'],
        stakeholder_tensions: [cmd.scenario_theme],
        lifecycle_state: 'draft',
        target_skill_slugs: cmd.target_skill_slugs,
        rubric_id: cmd.rubric_ids[0] ?? 'default',
        mock_company: {
          id: `mc-${uid()}`,
          name: 'Acme Corp',
          industry: cmd.domain,
          operating_context: cmd.workplace_context,
        },
        mock_people: [
          {
            id: `mp-${uid()}`,
            name: 'Alex Rivera',
            role: 'Senior Manager',
            goals: ['Keep the project on track', 'Satisfy all stakeholders'],
            communication_style: 'Direct and pragmatic',
            relationship_to_scenario: 'Project sponsor managing competing priorities',
          },
          {
            id: `mp-${uid()}`,
            name: 'Jordan Lee',
            role: 'Technical Lead',
            goals: ['Ensure quality', 'Meet technical constraints'],
            communication_style: 'Analytical and thorough',
            relationship_to_scenario: 'Constraints owner providing technical perspective',
          },
        ],
      });
    }

    const col: CollectionView = {
      id: collectionId,
      author_user_id: _user.id,
      organisation_id: null,
      title: cmd.title_hint ?? `Generated Collection - ${new Date().toLocaleDateString()}`,
      summary: `AI-generated ${cmd.target_audience} content for ${cmd.target_skill_slugs.map((s) => s.replace(/-/g, ' ')).join(', ')} practice.`,
      target_audience: cmd.target_audience,
      difficulty: cmd.difficulty,
      lifecycle_state: 'draft',
      verification_state: 'unverified',
      discovery_tier: 'private',
      source_type: 'generated_structured',
      content_format_mix: cmd.content_format_mix,
      target_skill_slugs: cmd.target_skill_slugs,
      target_competency_slugs: cmd.target_competency_slugs,
      rubric_ids: cmd.rubric_ids,
      save_count: 0,
      saved_by_actor: false,
      avg_rating: null,
      rating_count: 0,
      rated_by_actor: null,
      featured: false,
      last_generation_artifact_id: artifactId,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      prompt_items: promptItems,
      scenarios,
    };

    _collections = [..._collections, col];

    return {
      collection: col,
      generation_artifact_id: artifactId,
      generation_mode: 'structured',
      prompt_version: 'creator.structured-draft.v1',
      provider: 'mock',
      model_slug: 'mock-v1',
    };
  },

  async generateChatCollection(cmd: ChatCollectionGenerationCommand): Promise<CollectionGenerationView> {
    await delay(2500); // simulate LLM generation latency
    const collectionId = `col-${uid()}`;
    const artifactId = `gen-${uid()}`;

    const promptItems: PromptItemView[] = [];
    const totalPrompts = (cmd.counts.quick_practice_prompt_count ?? 0) + (cmd.counts.interview_prompt_count ?? 0);

    for (let i = 0; i < totalPrompts; i++) {
      const promptType = i < (cmd.counts.quick_practice_prompt_count ?? 0) ? 'quick_practice_prompt' : 'interview_prompt';
      const typeLabel = promptType === 'quick_practice_prompt' ? 'practice' : 'interview';
      promptItems.push({
        id: `pi-${uid()}`,
        prompt_type: promptType,
        title: `AI Generated ${typeLabel} ${i + 1}`,
        prompt_text: cmd.prompt,
        difficulty: cmd.difficulty,
        lifecycle_state: 'draft',
        target_skill_slugs: cmd.target_skill_slugs,
        rubric_id: cmd.rubric_ids[0] ?? 'default',
      });
    }

    const scenarios: ScenarioView[] = [];
    for (let i = 0; i < (cmd.counts.scenario_count ?? 0); i++) {
      scenarios.push({
        id: `sc-${uid()}`,
        title: `AI Generated Scenario ${i + 1}`,
        business_context: `Based on your prompt about: ${cmd.prompt.slice(0, 100)}...`,
        learner_objective: `Address the scenario using ${cmd.target_skill_slugs.map((s) => s.replace(/-/g, ' ')).join(', ')}.`,
        constraints: ['Multiple perspectives to balance', 'Decision required'],
        stakeholder_tensions: ['Competing priorities'],
        lifecycle_state: 'draft',
        target_skill_slugs: cmd.target_skill_slugs,
        rubric_id: cmd.rubric_ids[0] ?? 'default',
        mock_company: {
          id: `mc-${uid()}`,
          name: 'Nexus Industries',
          industry: 'Professional Services',
          operating_context: 'Dynamic environment requiring rapid decision-making',
        },
        mock_people: [
          {
            id: `mp-${uid()}`,
            name: 'Sam Torres',
            role: 'Director',
            goals: ['Drive resolution', 'Maintain relationships'],
            communication_style: 'Collaborative and diplomatic',
            relationship_to_scenario: 'Decision facilitator balancing multiple interests',
          },
        ],
      });
    }

    const col: CollectionView = {
      id: collectionId,
      author_user_id: _user.id,
      organisation_id: null,
      title: `Generated from prompt - ${new Date().toLocaleDateString()}`,
      summary: `AI-generated content based on your input: "${cmd.prompt.slice(0, 80)}..."`,
      target_audience: cmd.target_audience,
      difficulty: cmd.difficulty,
      lifecycle_state: 'draft',
      verification_state: 'unverified',
      discovery_tier: 'private',
      source_type: 'generated_chat',
      content_format_mix: cmd.content_format_mix,
      target_skill_slugs: cmd.target_skill_slugs,
      target_competency_slugs: cmd.target_competency_slugs,
      rubric_ids: cmd.rubric_ids,
      save_count: 0,
      saved_by_actor: false,
      avg_rating: null,
      rating_count: 0,
      rated_by_actor: null,
      featured: false,
      last_generation_artifact_id: artifactId,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      prompt_items: promptItems,
      scenarios,
    };

    _collections = [..._collections, col];

    return {
      collection: col,
      generation_artifact_id: artifactId,
      generation_mode: 'chat',
      prompt_version: 'creator.chat-draft.v1',
      provider: 'mock',
      model_slug: 'mock-v1',
    };
  },

  // --- Practice ------------------------------------------------------------

  async startQuickPracticeSession(cmd: StartQuickPracticeSessionCommand): Promise<QuickPracticeSessionView> {
    await delay(200);
    const item = _collections
      .flatMap((c) => c.prompt_items)
      .find((p) => p.id === cmd.prompt_item_id);

    if (!item) throw new Error(`Prompt item ${cmd.prompt_item_id} not found`);

    const sessionId = `sess-${uid()}`;
    const attemptId = `att-${uid()}`;

    return {
      session_id: sessionId,
      attempt_id: attemptId,
      workflow_id: `wf-${uid()}`,
      status: 'active',
      prompt: {
        content_item_id: item.id,
        prompt_type: item.prompt_type,
        title: item.title,
        prompt_text: item.prompt_text,
        difficulty: item.difficulty,
        delivery_version: 'quick-practice.delivery.v1',
        target_skill_slugs: item.target_skill_slugs,
        rubric_id: item.rubric_id,
        rubric_version: 'v1',
      },
      started_at: new Date().toISOString(),
      trace_id: `trace-${uid()}`,
    };
  },

  async submitAttempt(attemptId: string, cmd: SubmitAttemptCommand): Promise<AttemptView> {
    await delay(1500); // simulate LLM scoring latency

    // find a random prompt to build assessment against
    const promptItem = _collections.flatMap((c) => c.prompt_items)[0]!;
    const score = Math.floor(Math.random() * 3) + 3; // 3-5

    const prompt = {
      content_item_id: promptItem.id,
      prompt_type: promptItem.prompt_type,
      title: promptItem.title,
      prompt_text: promptItem.prompt_text,
      difficulty: promptItem.difficulty,
      delivery_version: 'quick-practice.delivery.v1',
      target_skill_slugs: promptItem.target_skill_slugs,
      rubric_id: `${promptItem.rubric_id}@v1`,
      rubric_version: 'v1',
    };

    const per_skill_assessments: PerSkillAssessment[] = promptItem.target_skill_slugs.map((slug) => {
      const skillScore = Math.max(1, Math.min(5, score + (Math.random() > 0.5 ? 0 : -1)));
      const evidence: EvidenceItem[] = [{
        quote: cmd.response_text.slice(0, 80),
        explanation: `This excerpt demonstrates ${slug.replace(/-/g, ' ')} through the learner's approach.`,
      }];
      return {
        skill_slug: slug,
        score: skillScore,
        rationale: `Demonstrated ${score >= 3 ? 'solid' : 'developing'} ${slug.replace(/-/g, ' ')}.`,
        evidence,
      };
    });

    const attempt: AttemptView = {
      id: attemptId,
      session_id: `sess-${uid()}`,
      workflow_id: `wf-${uid()}`,
      status: 'assessed',
      response_mode: 'text',
      response_text: cmd.response_text,
      last_error_code: null,
      submitted_at: new Date().toISOString(),
      assessed_at: new Date().toISOString(),
      prompt,
      assessment: {
        assessment_id: `assess-${uid()}`,
        attempt_id: attemptId,
        session_id: `sess-${uid()}`,
        validation_status: 'validated',
        prompt_version: 'assessment.quick-practice.v1',
        rubric_id: `${promptItem.rubric_id}@v1`,
        rubric_version: 'v1',
        schema_version: 'quick-practice-assessment-output.v1',
        config_version: 'quick-practice-marking-config.v1',
        provider: 'mock',
        model_slug: 'mock-v1',
        overall_score: score,
        per_skill_assessments,
        summary: score >= 4
          ? 'The response effectively addresses the prompt with clear reasoning and structure.'
          : 'The response partially addresses the prompt with a reasonable approach that could be more detailed.',
        strengths: score >= 3 ? ['Clear communication', 'Relevant context'] : ['Attempted to address the prompt'],
        weaknesses: score < 4 ? ['Add more specific examples', 'Strengthen the conclusion'] : ['Minor refinements possible'],
        next_actions: ['Practice under time pressure', 'Review the relevant framework'],
        trace_id: `trace-${uid()}`,
        pipeline_run_id: `run-${uid()}`,
        rejection_code: null,
        created_at: new Date().toISOString(),
        raw_payload: {},
      },
    };

    _attempts = [
      {
        id: attemptId,
        session_id: attempt.session_id,
        title: prompt.title,
        practice_type: 'quick_practice',
        score,
        skill_slugs: prompt.target_skill_slugs,
        created_at: attempt.assessed_at!,
        status: 'assessed',
      },
      ..._attempts,
    ];

    return attempt;
  },

  async getAttempt(attemptId: string): Promise<AttemptView> {
    await delay(200);
    const historyItem = _attempts.find((a) => a.id === attemptId);
    if (!historyItem) throw new Error(`Attempt ${attemptId} not found`);

    const promptItem = _collections.flatMap((c) => c.prompt_items).find(
      (p) => p.title === historyItem.title,
    ) ?? _collections.flatMap((c) => c.prompt_items)[0]!;

    return {
      id: historyItem.id,
      session_id: historyItem.session_id,
      workflow_id: `wf-${historyItem.id}`,
      status: historyItem.status,
      response_mode: 'text',
      response_text: 'This is a saved response for review.',
      last_error_code: null,
      submitted_at: historyItem.created_at,
      assessed_at: historyItem.created_at,
      prompt: {
        content_item_id: promptItem.id,
        prompt_type: promptItem.prompt_type,
        title: promptItem.title,
        prompt_text: promptItem.prompt_text,
        difficulty: promptItem.difficulty,
        delivery_version: 'quick-practice.delivery.v1',
        target_skill_slugs: promptItem.target_skill_slugs,
        rubric_id: `${promptItem.rubric_id}@v1`,
        rubric_version: 'v1',
      },
      assessment: {
        assessment_id: `assess-${historyItem.id}`,
        attempt_id: historyItem.id,
        session_id: historyItem.session_id,
        validation_status: 'validated',
        prompt_version: 'assessment.quick-practice.v1',
        rubric_id: `${promptItem.rubric_id}@v1`,
        rubric_version: 'v1',
        schema_version: 'quick-practice-assessment-output.v1',
        config_version: 'quick-practice-marking-config.v1',
        provider: 'mock',
        model_slug: 'mock-v1',
        overall_score: historyItem.score,
        per_skill_assessments: historyItem.skill_slugs.map((slug) => ({
          skill_slug: slug,
          score: historyItem.score,
          rationale: `Consistent ${slug.replace(/-/g, ' ')} performance.`,
          evidence: [{
            quote: 'Relevant excerpt from the stored response.',
            explanation: `Demonstrates ${slug.replace(/-/g, ' ')}.`,
          }],
        })),
        summary: `Score of ${historyItem.score}/5 based on rubric criteria.`,
        strengths: ['Structured approach', 'Clear reasoning'],
        weaknesses: historyItem.score < 4 ? ['Could be more specific'] : [],
        next_actions: ['Continue practicing similar prompts'],
        trace_id: `trace-${historyItem.id}`,
        pipeline_run_id: `run-${historyItem.id}`,
        rejection_code: null,
        created_at: historyItem.created_at,
        raw_payload: {},
      },
    };
  },

  // --- Interview -----------------------------------------------------------

  async startInterviewSession(promptItemId: string): Promise<InterviewSessionView> {
    await delay(200);
    const item = _collections
      .flatMap((c) => c.prompt_items)
      .find((p) => p.id === promptItemId);
    if (!item) throw new Error(`Prompt item ${promptItemId} not found`);

    const sessionId = `sess-${uid()}`;
    const attemptId = `att-${uid()}`;
    _interviewSessions.set(sessionId, {
      session_id: sessionId,
      attempt_id: attemptId,
      status: 'active',
      total_turns: 3,
      current_turn: 1,
      current_question: item.prompt_text,
      competency_context: `This question assesses your ${item.target_skill_slugs.map((s) => s.replace(/-/g, ' ')).join(', ')} skills.`,
      history: [],
      target_skill_slugs: item.target_skill_slugs,
      difficulty: item.difficulty,
      started_at: new Date().toISOString(),
    });
    return _interviewSessions.get(sessionId)!;
  },

  async submitInterviewTurn(sessionId: string, cmd: SubmitAttemptCommand): Promise<InterviewSessionView> {
    await delay(800);
    const session = _interviewSessions.get(sessionId);
    if (!session) throw new Error(`Interview session ${sessionId} not found`);

    const newHistory = [
      ...session.history,
      { turn_number: session.current_turn, question: session.current_question, response: cmd.response_text },
    ];

    const isComplete = session.current_turn >= session.total_turns;
    const followUps = [
      'Can you tell me more about how you handled the outcome of that situation?',
      'What would you do differently if you faced this situation again?',
      'How did the other stakeholders respond to your approach?',
    ];

    const updated: InterviewSessionView = {
      ...session,
      history: newHistory,
      current_turn: isComplete ? session.current_turn : session.current_turn + 1,
      current_question: isComplete ? session.current_question : followUps[session.current_turn - 1] ?? followUps[0]!,
      competency_context: isComplete
        ? 'Interview complete — generating your assessment.'
        : `Follow-up ${session.current_turn} of ${session.total_turns - 1}: probing deeper into your response.`,
      status: isComplete ? 'completed' : 'active',
    };

    _interviewSessions.set(sessionId, updated);

    if (isComplete) {
      _attempts = [
        {
          id: session.attempt_id,
          session_id: sessionId,
          title: session.current_question.slice(0, 50),
          practice_type: 'quick_practice',
          score: Math.floor(Math.random() * 2) + 3,
          skill_slugs: session.target_skill_slugs,
          created_at: new Date().toISOString(),
          status: 'assessed',
        },
        ..._attempts,
      ];
    }

    return updated;
  },

  // --- Scenario ------------------------------------------------------------

  async startScenarioSession(scenarioId: string): Promise<ScenarioSessionView> {
    await delay(200);
    const scenario = _collections
      .flatMap((c) => c.scenarios)
      .find((s) => s.id === scenarioId);
    if (!scenario) throw new Error(`Scenario ${scenarioId} not found`);

    const sessionId = `sess-${uid()}`;
    const attemptId = `att-${uid()}`;

    const stepPrompts = [
      `You've just entered the meeting room. ${scenario.mock_people[0]?.name ?? 'The stakeholder'} is visibly frustrated. How do you open the conversation?`,
      `${scenario.mock_people[0]?.name ?? 'The stakeholder'} has raised concerns about the timeline. Present your recovery plan while addressing their specific worries.`,
      `The meeting is wrapping up. Summarize the agreed-upon next steps and set clear expectations for the follow-up.`,
    ];

    _scenarioSessions.set(sessionId, {
      session_id: sessionId,
      attempt_id: attemptId,
      status: 'active',
      scenario,
      total_steps: stepPrompts.length,
      current_step: 1,
      current_prompt_text: stepPrompts[0]!,
      history: [],
      started_at: new Date().toISOString(),
    });

    return _scenarioSessions.get(sessionId)!;
  },

  async submitScenarioStep(sessionId: string, cmd: SubmitAttemptCommand): Promise<ScenarioSessionView> {
    await delay(800);
    const session = _scenarioSessions.get(sessionId);
    if (!session) throw new Error(`Scenario session ${sessionId} not found`);

    const newHistory = [
      ...session.history,
      { step_number: session.current_step, prompt: session.current_prompt_text, response: cmd.response_text },
    ];

    const isComplete = session.current_step >= session.total_steps;

    const stepPrompts = [
      '',
      `${session.scenario.mock_people[0]?.name ?? 'The stakeholder'} has raised concerns about the timeline. Present your recovery plan while addressing their specific worries.`,
      `The meeting is wrapping up. Summarize the agreed-upon next steps and set clear expectations for the follow-up.`,
    ];

    const updated: ScenarioSessionView = {
      ...session,
      history: newHistory,
      current_step: isComplete ? session.current_step : session.current_step + 1,
      current_prompt_text: isComplete ? session.current_prompt_text : stepPrompts[session.current_step] ?? '',
      status: isComplete ? 'completed' : 'active',
    };

    _scenarioSessions.set(sessionId, updated);

    if (isComplete) {
      _attempts = [
        {
          id: session.attempt_id,
          session_id: sessionId,
          title: session.scenario.title,
          practice_type: 'quick_practice',
          score: Math.floor(Math.random() * 2) + 3,
          skill_slugs: session.scenario.target_skill_slugs,
          created_at: new Date().toISOString(),
          status: 'assessed',
        },
        ..._attempts,
      ];
    }

    return updated;
  },

  // --- Progress ------------------------------------------------------------

  async getCompetencyProgress(_userId: string): Promise<CompetencyProgressView[]> {
    await delay(200);
    return SEED_COMPETENCY_PROGRESS;
  },

  async getAttemptHistory(_userId: string): Promise<AttemptHistoryItem[]> {
    await delay(150);
    return _attempts;
  },

  // --- Practice Runs (Aggregate) ---------------------------------------------

  async createPracticeRun(cmd: StartPracticeRunCommand): Promise<PracticeRunView> {
    await delay(300);
    const runId = `run-${uid()}`;
    const now = new Date().toISOString();

    const items: PracticeRunItemSummary[] = cmd.selected_items.map((sel, idx) => {
      let title = '';
      let difficulty: 'introductory' | 'intermediate' | 'advanced' = 'intermediate';
      let skillSlugs: string[] = [];

      if (sel.item_type === 'prompt_item') {
        const item = _collections.flatMap((c) => c.prompt_items).find((p) => p.id === sel.item_id);
        if (item) {
          title = item.title;
          difficulty = item.difficulty;
          skillSlugs = item.target_skill_slugs;
        }
      } else {
        const scenario = _collections.flatMap((c) => c.scenarios).find((s) => s.id === sel.item_id);
        if (scenario) {
          title = scenario.title;
          difficulty = 'intermediate';
          skillSlugs = scenario.target_skill_slugs;
        }
      }

      return {
        id: sel.item_id,
        item_type: sel.item_type,
        title: title || `Item ${idx + 1}`,
        difficulty,
        target_skill_slugs: skillSlugs,
        status: 'pending' as const,
      };
    });

    items.forEach((item, idx) => {
      const sessionId = `ps-${uid()}`;
      const attemptId = `att-${uid()}`;
      _practiceSessions.set(sessionId, {
        id: sessionId,
        practice_run_id: runId,
        sequence_index: idx,
        content_item_id: item.id,
        content_item_type: item.item_type,
        attempt_id: attemptId,
        status: 'active',
        score: null,
        started_at: now,
        completed_at: null,
      });
    });

    const run: PracticeRunView = {
      id: runId,
      user_id: _user.id,
      title: cmd.title,
      status: 'active',
      items,
      summary: {
        total_items: items.length,
        completed_items: 0,
        overall_score: null,
        score_distribution: {},
        skill_breakdown: {},
        practice_type_breakdown: {},
      },
      created_at: now,
      updated_at: now,
      completed_at: null,
    };

    _practiceRuns.set(runId, run);
    return run;
  },

  async listPracticeRuns(): Promise<PracticeRunView[]> {
    await delay(150);
    return Array.from(_practiceRuns.values()).sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    );
  },

  async getPracticeRun(runId: string): Promise<PracticeRunView> {
    await delay(150);
    const run = _practiceRuns.get(runId);
    if (!run) throw new Error(`Practice run ${runId} not found`);
    return run;
  },

  async getPracticeSessions(runId: string): Promise<PracticeSessionView[]> {
    await delay(150);
    return Array.from(_practiceSessions.values())
      .filter((s) => s.practice_run_id === runId)
      .sort((a, b) => a.sequence_index - b.sequence_index);
  },

  // --- Admin: Users & User Management ----------------------------------------

  async listAdminUsers(params?: {
    offset?: number;
    limit?: number;
    search?: string;
    role?: string;
    is_active?: boolean;
  }): Promise<AdminUserListView> {
    await delay(200);
    const session = requireAdminSession();
    let filtered = [..._adminUsers];
    const scopedOrganisationId = getScopedAdminOrganisationId(session);
    if (scopedOrganisationId) {
      filtered = filtered.filter((user) => user.organisation_id === scopedOrganisationId);
    }
    if (params?.search) {
      const q = params.search.toLowerCase();
      filtered = filtered.filter(
        (u) => u.email.toLowerCase().includes(q) || u.display_name.toLowerCase().includes(q),
      );
    }
    if (params?.role) {
      filtered = filtered.filter((u) => u.organisation_role === params.role);
    }
    if (params?.is_active !== undefined) {
      filtered = filtered.filter((u) => u.is_active === params.is_active);
    }
    const offset = params?.offset ?? 0;
    const limit = params?.limit ?? 50;
    const paginated = filtered.slice(offset, offset + limit);
    return {
      users: paginated,
      total: filtered.length,
      offset,
      limit,
    };
  },

  async getAdminUser(userId: string): Promise<AdminUserView | null> {
    await delay(150);
    const session = requireAdminSession();
    const user = _adminUsers.find((u) => u.user_id === userId) ?? null;
    if (!user) return null;
    const scopedOrganisationId = getScopedAdminOrganisationId(session);
    if (scopedOrganisationId && user.organisation_id !== scopedOrganisationId) {
      throw new Error(`User ${userId} is outside the active organisation scope`);
    }
    return user;
  },

  async updateAdminUserRole(userId: string, role: string): Promise<AdminUserView> {
    await delay(200);
    const existingUser = await this.getAdminUser(userId);
    if (!existingUser) throw new Error(`User ${userId} not found`);
    const idx = _adminUsers.findIndex((u) => u.user_id === userId);
    if (idx === -1) throw new Error(`User ${userId} not found`);
    _adminUsers = _adminUsers.map((u, i) =>
      i === idx ? { ...u, organisation_role: role } : u,
    );
    return _adminUsers[idx]!;
  },

  async updateAdminUserStatus(userId: string, isActive: boolean): Promise<AdminUserView> {
    await delay(200);
    const existingUser = await this.getAdminUser(userId);
    if (!existingUser) throw new Error(`User ${userId} not found`);
    const idx = _adminUsers.findIndex((u) => u.user_id === userId);
    if (idx === -1) throw new Error(`User ${userId} not found`);
    _adminUsers = _adminUsers.map((u, i) =>
      i === idx ? { ...u, is_active: isActive } : u,
    );
    return _adminUsers[idx]!;
  },

  async createAdminUser(cmd: { email: string; role: string }): Promise<AdminUserView> {
    await delay(300);
    const session = requireAdminSession();
    const organisationId = getScopedAdminOrganisationId(session);
    if (!organisationId) {
      throw new Error('No active organisation selected');
    }
    const newUser: AdminUserView = {
      user_id: `usr-${uid()}`,
      email: cmd.email,
      display_name: cmd.email.split('@')[0]!,
      auth_provider: 'google',
      is_active: true,
      organisation_id: organisationId,
      organisation_role: cmd.role,
      created_at: new Date().toISOString(),
    };
    _adminUsers = [..._adminUsers, newUser];
    return newUser;
  },

  async bulkAdminUserOperation(cmd: {
    user_ids: string[];
    operation: string;
    payload?: { role?: string };
  }): Promise<BulkOperationResultView> {
    await delay(400);
    let successCount = 0;
    const failedIds: string[] = [];
    for (const userId of cmd.user_ids) {
      try {
        if (cmd.operation === 'suspend') {
          await this.updateAdminUserStatus(userId, false);
        } else if (cmd.operation === 'activate') {
          await this.updateAdminUserStatus(userId, true);
        } else if (cmd.operation === 'change_role' && cmd.payload?.role) {
          await this.updateAdminUserRole(userId, cmd.payload.role);
        }
        successCount++;
      } catch {
        failedIds.push(userId);
      }
    }
    return {
      operation: cmd.operation,
      requested_count: cmd.user_ids.length,
      success_count: successCount,
      failure_count: failedIds.length,
      failed_user_ids: failedIds,
    };
  },

  async getUserActivity(userId: string): Promise<UserActivityView> {
    await delay(250);
    const user = await this.getAdminUser(userId);
    if (!user) throw new Error(`User ${userId} not found`);
    return {
      user_id: user.user_id,
      email: user.email,
      display_name: user.display_name,
      organisation_id: user.organisation_id,
      organisation_role: user.organisation_role,
      total_sessions: Math.floor(Math.random() * 50) + 10,
      total_attempts: Math.floor(Math.random() * 150) + 30,
      recent_sessions: [
        { session_id: `sess-${uid()}`, practice_type: 'quick_practice', content_item_id: `pi-${uid()}`, status: 'completed', created_at: isoDate(1), completed_at: isoDate(1) },
        { session_id: `sess-${uid()}`, practice_type: 'quick_practice', content_item_id: `pi-${uid()}`, status: 'completed', created_at: isoDate(2), completed_at: isoDate(2) },
        { session_id: `sess-${uid()}`, practice_type: 'quick_practice', content_item_id: `pi-${uid()}`, status: 'completed', created_at: isoDate(3), completed_at: isoDate(3) },
      ],
      recent_attempts: [
        { attempt_id: `att-${uid()}`, session_id: `sess-${uid()}`, practice_type: 'quick_practice', content_item_id: `pi-${uid()}`, content_item_type: 'prompt_item', status: 'assessed', overall_score: 4, submitted_at: isoDate(1), assessed_at: isoDate(1) },
        { attempt_id: `att-${uid()}`, session_id: `sess-${uid()}`, practice_type: 'quick_practice', content_item_id: `pi-${uid()}`, content_item_type: 'prompt_item', status: 'assessed', overall_score: 3, submitted_at: isoDate(2), assessed_at: isoDate(2) },
        { attempt_id: `att-${uid()}`, session_id: `sess-${uid()}`, practice_type: 'quick_practice', content_item_id: `pi-${uid()}`, content_item_type: 'prompt_item', status: 'assessed', overall_score: 5, submitted_at: isoDate(3), assessed_at: isoDate(3) },
      ],
      recent_logins: [
        { event_type: 'user.login', occurred_at: isoDate(1), trace_id: `trace-${uid()}` },
        { event_type: 'user.login', occurred_at: isoDate(2), trace_id: `trace-${uid()}` },
        { event_type: 'user.login', occurred_at: isoDate(4), trace_id: `trace-${uid()}` },
      ],
    };
  },

  // --- Admin: Learners & Relationships ---------------------------------------

  async getLearnerAnalytics(
    learnerId: string,
    _params?: { from_date?: string; to_date?: string },
  ): Promise<LearnerAnalyticsView> {
    await delay(300);
    return (
      SEED_LEARNER_ANALYTICS[learnerId] ?? {
        learner_id: learnerId,
        target_role: 'member',
        latest_progress_snapshot_id: `snap-${uid()}`,
        latest_recommendation_id: `rec-${uid()}`,
        weak_skill_slugs: ['active-listening'],
        stagnating_skill_slugs: [],
        coverage_gap_skill_slugs: ['negotiation'],
        usage: {
          total_sessions: Math.floor(Math.random() * 100) + 20,
          total_attempts: Math.floor(Math.random() * 200) + 50,
          submitted_attempts: Math.floor(Math.random() * 180) + 45,
          assessed_attempts: Math.floor(Math.random() * 160) + 40,
          validated_assessments: Math.floor(Math.random() * 140) + 35,
          rejected_assessments: Math.floor(Math.random() * 20) + 5,
          workflow_event_count: Math.floor(Math.random() * 500) + 100,
          pipeline_run_count: Math.floor(Math.random() * 200) + 50,
          provider_call_count: Math.floor(Math.random() * 1000) + 200,
          avg_validated_score: Math.round((3 + Math.random() * 2) * 10) / 10,
          last_activity_at: isoDate(Math.floor(Math.random() * 5)),
        },
        recent_attempts: [
          { attempt_id: `att-${uid()}`, session_id: `sess-${uid()}`, practice_type: 'quick_practice', content_item_id: `pi-${uid()}`, content_item_type: 'prompt_item', status: 'assessed', overall_score: Math.floor(Math.random() * 3) + 3, submitted_at: isoDate(1), assessed_at: isoDate(1) },
        ],
        usage_trend: [
          { bucket_date: '2026-03-01', sessions_started: Math.floor(Math.random() * 20) + 5, attempts_submitted: Math.floor(Math.random() * 10) + 3, assessments_validated: Math.floor(Math.random() * 8) + 2, assessments_rejected: Math.floor(Math.random() * 2) },
          { bucket_date: '2026-03-02', sessions_started: Math.floor(Math.random() * 20) + 5, attempts_submitted: Math.floor(Math.random() * 10) + 3, assessments_validated: Math.floor(Math.random() * 8) + 2, assessments_rejected: Math.floor(Math.random() * 2) },
        ] as UsageTrendPointView[],
        provider_summary: [
          { provider: 'openrouter', model_slug: 'gpt-4o-mini', call_count: Math.floor(Math.random() * 1000) + 200, success_count: Math.floor(Math.random() * 950) + 190, failure_count: Math.floor(Math.random() * 20) + 5, avg_latency_ms: Math.round((600 + Math.random() * 400) * 10) / 10 },
        ] as ProviderUsageView[],
      }
    );
  },

  async getLearnerRelationship(learnerId: string): Promise<AdminLearnerRelationshipView | null> {
    await delay(150);
    return _learnerRelationships.get(learnerId) ?? null;
  },

  async upsertLearnerRelationship(
    learnerId: string,
    relationshipType: string,
  ): Promise<AdminLearnerRelationshipView> {
    await delay(200);
    const now = new Date().toISOString();
    const existing = _learnerRelationships.get(learnerId);
    const rel: AdminLearnerRelationshipView = {
      learner_user_id: learnerId,
      admin_user_id: existing?.admin_user_id ?? _adminUsers[0]!.user_id,
      relationship_type: relationshipType,
      created_at: existing?.created_at ?? now,
      updated_at: now,
    };
    _learnerRelationships.set(learnerId, rel);
    return rel;
  },

  async deleteLearnerRelationship(learnerId: string): Promise<{ status: string }> {
    await delay(150);
    _learnerRelationships.delete(learnerId);
    return { status: 'deleted' };
  },

  // --- Admin: Analytics Overview ---------------------------------------------

  async getAnalyticsOverview(_params?: { from_date?: string; to_date?: string }): Promise<AnalyticsOverviewView> {
    await delay(300);
    return { ...SEED_ANALYTICS_OVERVIEW };
  },

  async getCohortAnalytics(params?: {
    target_role?: string;
    from_date?: string;
    to_date?: string;
  }): Promise<CohortAnalyticsView> {
    await delay(300);
    const key = params?.target_role ?? 'sales-team';
    return SEED_COHORT_ANALYTICS[key] ?? {
      cohort_key: key,
      learner_count: Math.floor(Math.random() * 100) + 20,
      usage: {
        total_sessions: Math.floor(Math.random() * 500) + 100,
        total_attempts: Math.floor(Math.random() * 200) + 50,
        submitted_attempts: Math.floor(Math.random() * 180) + 45,
        assessed_attempts: Math.floor(Math.random() * 160) + 40,
        validated_assessments: Math.floor(Math.random() * 140) + 35,
        rejected_assessments: Math.floor(Math.random() * 20) + 5,
        workflow_event_count: Math.floor(Math.random() * 500) + 100,
        pipeline_run_count: Math.floor(Math.random() * 200) + 50,
        provider_call_count: Math.floor(Math.random() * 2000) + 500,
        avg_validated_score: Math.round((3 + Math.random() * 2) * 10) / 10,
        last_activity_at: isoDate(1),
      },
      weak_skill_clusters: [
        { skill_slug: 'active-listening', learner_count: Math.floor(Math.random() * 50) + 10 },
      ] as SkillClusterView[],
      average_skill_scores: [
        { skill_slug: 'active-listening', avg_score: Math.round((3 + Math.random() * 2) * 10) / 10, learner_count: Math.floor(Math.random() * 50) + 10 },
      ] as SkillAverageView[],
      usage_trend: [
        { bucket_date: '2026-03-01', sessions_started: Math.floor(Math.random() * 20) + 5, attempts_submitted: Math.floor(Math.random() * 10) + 3, assessments_validated: Math.floor(Math.random() * 8) + 2, assessments_rejected: Math.floor(Math.random() * 2) },
      ] as UsageTrendPointView[],
      provider_summary: [
        { provider: 'openrouter', model_slug: 'gpt-4o-mini', call_count: Math.floor(Math.random() * 5000) + 1000, success_count: Math.floor(Math.random() * 4900) + 950, failure_count: Math.floor(Math.random() * 100) + 20, avg_latency_ms: Math.round((700 + Math.random() * 300) * 10) / 10 },
      ] as ProviderUsageView[],
    };
  },

  async getCohortsComparison(params: {
    cohort_keys: string;
    from_date?: string;
    to_date?: string;
  }): Promise<CohortComparisonView> {
    await delay(350);
    const keys = params.cohort_keys.split(',').map((k) => k.trim());
    const cohorts = keys.map((key) => {
      const base = SEED_COHORT_ANALYTICS[key];
      if (base) return base;
      return {
        cohort_key: key,
        learner_count: Math.floor(Math.random() * 100) + 20,
        usage: {
          total_sessions: Math.floor(Math.random() * 500) + 100,
          total_attempts: Math.floor(Math.random() * 200) + 50,
          submitted_attempts: Math.floor(Math.random() * 180) + 45,
          assessed_attempts: Math.floor(Math.random() * 160) + 40,
          validated_assessments: Math.floor(Math.random() * 140) + 35,
          rejected_assessments: Math.floor(Math.random() * 20) + 5,
          workflow_event_count: Math.floor(Math.random() * 500) + 100,
          pipeline_run_count: Math.floor(Math.random() * 200) + 50,
          provider_call_count: Math.floor(Math.random() * 2000) + 500,
          avg_validated_score: Math.round((3 + Math.random() * 2) * 10) / 10,
          last_activity_at: isoDate(1),
        },
        weak_skill_clusters: [
          { skill_slug: 'active-listening', learner_count: Math.floor(Math.random() * 50) + 10 },
        ] as SkillClusterView[],
        average_skill_scores: [
          { skill_slug: 'active-listening', avg_score: Math.round((3 + Math.random() * 2) * 10) / 10, learner_count: Math.floor(Math.random() * 50) + 10 },
        ] as SkillAverageView[],
        usage_trend: [
          { bucket_date: '2026-03-01', sessions_started: Math.floor(Math.random() * 20) + 5, attempts_submitted: Math.floor(Math.random() * 10) + 3, assessments_validated: Math.floor(Math.random() * 8) + 2, assessments_rejected: Math.floor(Math.random() * 2) },
        ] as UsageTrendPointView[],
        provider_summary: [
          { provider: 'openrouter', model_slug: 'gpt-4o-mini', call_count: Math.floor(Math.random() * 5000) + 1000, success_count: Math.floor(Math.random() * 4900) + 950, failure_count: Math.floor(Math.random() * 100) + 20, avg_latency_ms: Math.round((700 + Math.random() * 300) * 10) / 10 },
        ] as ProviderUsageView[],
      } as CohortAnalyticsView;
    });
    return { cohorts, run_count: cohorts.length };
  },

  // --- Admin: Collections & Verification ------------------------------------

  async getVerificationQueue(): Promise<CollectionVerificationQueueItemView[]> {
    await delay(250);
    return [...SEED_VERIFICATION_QUEUE];
  },

  async getCollectionVerification(collectionId: string): Promise<CollectionVerificationAuditView> {
    await delay(200);
    const col = _collections.find((c) => c.id === collectionId) ?? _collections[0]!;
    const queueItem = SEED_VERIFICATION_QUEUE.find((q) => q.collection_id === collectionId);
    return {
      collection: col,
      latest_review: queueItem?.latest_note
        ? {
            reviewer_user_id: queueItem.latest_reviewer_user_id ?? 'usr-001',
            verification_state: queueItem.verification_state,
            note: queueItem.latest_note,
            reviewed_at: queueItem.latest_reviewed_at ?? isoDate(2),
          }
        : null,
      history: queueItem?.latest_note
        ? [
            {
              reviewer_user_id: queueItem.latest_reviewer_user_id ?? 'usr-001',
              verification_state: 'in_review',
              note: 'Initial review started.',
              reviewed_at: isoDate(5),
            },
            {
              reviewer_user_id: queueItem.latest_reviewer_user_id ?? 'usr-001',
              verification_state: queueItem.verification_state,
              note: queueItem.latest_note,
              reviewed_at: queueItem.latest_reviewed_at ?? isoDate(2),
            },
          ]
        : [],
    };
  },

  async updateCollectionVerification(
    collectionId: string,
    cmd: { verification_state: string; note?: string },
  ): Promise<CollectionVerificationAuditView> {
    await delay(300);
    const queueIdx = SEED_VERIFICATION_QUEUE.findIndex((q) => q.collection_id === collectionId);
    if (queueIdx !== -1) {
      SEED_VERIFICATION_QUEUE[queueIdx] = {
        ...SEED_VERIFICATION_QUEUE[queueIdx]!,
        verification_state: cmd.verification_state,
        latest_reviewed_at: new Date().toISOString(),
        latest_reviewer_user_id: _adminUsers[0]!.user_id,
        latest_note: cmd.note ?? null,
      };
    }
    return this.getCollectionVerification(collectionId);
  },

  async updateCollectionFeature(collectionId: string, featured: boolean): Promise<CollectionView> {
    await delay(200);
    const colIdx = _collections.findIndex((c) => c.id === collectionId);
    if (colIdx === -1) throw new Error(`Collection ${collectionId} not found`);
    const updated = { ..._collections[colIdx]!, featured };
    _collections = _collections.map((c, i) => (i === colIdx ? updated : c));
    return updated;
  },

  // --- Admin: Evaluation Dashboard -------------------------------------------

  async listEvalSuites(): Promise<EvaluationSuiteView[]> {
    await delay(200);
    return [...SEED_EVAL_SUITES];
  },

  async listEvalRuns(params?: { limit?: number }): Promise<EvaluationRunView[]> {
    await delay(200);
    const runs = [...SEED_EVAL_RUNS];
    return runs.slice(0, params?.limit ?? 20);
  },

  async getEvalRun(runId: string): Promise<EvaluationRunView> {
    await delay(200);
    const run = SEED_EVAL_RUNS.find((r) => r.evaluation_run_id === runId);
    if (!run) throw new Error(`Eval run ${runId} not found`);
    return run;
  },

  async triggerEvalRun(cmd: { suite_id: string }): Promise<EvaluationRunView> {
    await delay(500);
    const suite = SEED_EVAL_SUITES.find((s) => s.suite_id === cmd.suite_id) ?? SEED_EVAL_SUITES[0]!;
    const newRun: EvaluationRunView = {
      evaluation_run_id: `run-${uid()}`,
      suite_id: suite.suite_id,
      suite_type: suite.suite_type,
      status: 'completed',
      passed: Math.random() > 0.2,
      pass_rate: Math.round((0.75 + Math.random() * 0.25) * 100) / 100,
      avg_latency_ms: Math.round((1000 + Math.random() * 2000) * 100) / 100,
      total_tokens: Math.floor(Math.random() * 50000) + 10000,
      case_count: Math.floor(Math.random() * 30) + 10,
      model_slugs: ['gpt-4o-mini'],
      started_at: new Date().toISOString(),
      completed_at: new Date().toISOString(),
    };
    SEED_EVAL_RUNS.unshift(newRun);
    return newRun;
  },

  async getEvalDashboard(_params?: { from_date?: string; to_date?: string }): Promise<EvaluationDashboardView> {
    await delay(300);
    const runs = SEED_EVAL_RUNS;
    const passed = runs.filter((r) => r.passed).length;
    const failed = runs.filter((r) => !r.passed).length;
    const passRate = runs.length > 0 ? passed / runs.length : 0;
    return {
      total_runs: runs.length,
      pass_fail: { passed, failed, pass_rate: Math.round(passRate * 100) / 100 },
      latency_percentiles: { p50_ms: 1240.5, p95_ms: 2800.0, p99_ms: 4200.0 },
      error_breakdown: [
        { error_code: 'LLM_TIMEOUT', count: 12, percentage: 0.3 },
        { error_code: 'INVALID_OUTPUT', count: 8, percentage: 0.2 },
        { error_code: 'RUBRIC_MISMATCH', count: 5, percentage: 0.125 },
      ],
      total_cases: runs.reduce((sum, r) => sum + r.case_count, 0),
      total_tokens: runs.reduce((sum, r) => sum + r.total_tokens, 0),
      estimated_cost_usd: Math.round(runs.reduce((sum, r) => sum + r.total_tokens * 0.00001, 0) * 100) / 100,
      suite_breakdown: {
        'suite-001': { passed: 4, failed: 1, pass_rate: 0.8 },
        'suite-002': { passed: 1, failed: 1, pass_rate: 0.5 },
        'suite-003': { passed: 1, failed: 0, pass_rate: 1.0 },
      },
      from_date: null,
      to_date: null,
    };
  },

  async getEvalRunsComparison(params: {
    run_ids: string;
    from_date?: string;
    to_date?: string;
  }): Promise<EvaluationComparisonView> {
    await delay(350);
    const ids = params.run_ids.split(',').map((id) => id.trim());
    const runs = SEED_EVAL_RUNS.filter((r) => ids.includes(r.evaluation_run_id));
    const avgPassRate = runs.length > 0 ? runs.reduce((sum, r) => sum + (r.pass_rate ?? 0), 0) / runs.length : null;
    const avgLatency = runs.length > 0 ? runs.reduce((sum, r) => sum + (r.avg_latency_ms ?? 0), 0) / runs.length : null;
    return {
      runs: runs.map((r) => ({
        evaluation_run_id: r.evaluation_run_id,
        suite_id: r.suite_id,
        suite_type: r.suite_type,
        passed: r.passed,
        pass_rate: r.pass_rate,
        avg_latency_ms: r.avg_latency_ms,
        total_tokens: r.total_tokens,
        case_count: r.case_count,
        model_slugs: r.model_slugs,
        started_at: r.started_at,
      })),
      run_count: runs.length,
      total_cases: runs.reduce((sum, r) => sum + r.case_count, 0),
      avg_pass_rate: avgPassRate !== null ? Math.round(avgPassRate * 100) / 100 : null,
      avg_latency_ms: avgLatency !== null ? Math.round(avgLatency * 100) / 100 : null,
    };
  },

  async getEvalBenchmark(_params?: { from_date?: string; to_date?: string }): Promise<BenchmarkDashboardView> {
    await delay(300);
    return {
      models: [
        { model_slug: 'gpt-4o-mini', provider: 'openrouter', run_count: 5, passed_count: 4, failed_count: 1, pass_rate: 0.8, avg_latency_ms: 1240.5, total_prompt_tokens: 120000, total_completion_tokens: 80000, total_tokens: 200000, estimated_cost_usd: 2.0 },
        { model_slug: 'claude-3-haiku', provider: 'openrouter', run_count: 2, passed_count: 1, failed_count: 1, pass_rate: 0.5, avg_latency_ms: 820.3, total_prompt_tokens: 48000, total_completion_tokens: 32000, total_tokens: 80000, estimated_cost_usd: 0.4 },
      ],
      total_runs: 7,
      total_cases: 230,
      from_date: null,
      to_date: null,
    };
  },

  async getEvalCaseDetail(caseId: string): Promise<EvaluationCaseDetailView> {
    await delay(200);
    return {
      case_id: caseId,
      case_label: `Case ${caseId.slice(-4)}`,
      status: 'completed',
      error_code: null,
      suite_id: 'suite-001',
      suite_type: 'quick_practice',
      suite_version: 'v1.0.0',
      evaluation_run_id: 'run-001',
      passed: true,
      metrics: { accuracy: 0.92, latency_ms: 1150, tokens: 450 },
      detail_payload: { input: 'Sample input', expected_output: 'Sample output', actual_output: 'Sample output' },
      started_at: isoDate(7),
      completed_at: isoDate(7),
    };
  },

  // --- Admin: Providers --------------------------------------------------------
  async listOpenRouterModels(): Promise<ProviderModel[]> {
    await delay(200);
    return [
      { id: 'openai/gpt-4o', name: 'GPT-4o', provider: 'openrouter' },
      { id: 'openai/gpt-4o-mini', name: 'GPT-4o Mini', provider: 'openrouter' },
      { id: 'anthropic/claude-3.5-sonnet', name: 'Claude 3.5 Sonnet', provider: 'openrouter' },
      { id: 'anthropic/claude-3-haiku', name: 'Claude 3 Haiku', provider: 'openrouter' },
      { id: 'google/gemini-2.0-flash', name: 'Gemini 2.0 Flash', provider: 'openrouter' },
      { id: 'meta-llama/llama-3.1-70b-instruct', name: 'Llama 3.1 70B', provider: 'openrouter' },
    ];
  },

  // --- Admin: Prompts --------------------------------------------------------

  async listPrompts(): Promise<PromptSummaryView[]> {
    await delay(200);
    return [...SEED_PROMPTS];
  },

  async listPromptVersions(name: string): Promise<PromptVersionView[]> {
    await delay(200);
    return SEED_PROMPT_VERSIONS[name] ?? [];
  },

  async getPromptVersion(name: string, version: string): Promise<PromptVersionView> {
    await delay(200);
    const versions = SEED_PROMPT_VERSIONS[name] ?? [];
    const found = versions.find((v) => v.version === version);
    if (!found) throw new Error(`Prompt ${name} version ${version} not found`);
    return found;
  },

  async createPrompt(cmd: {
    name: string;
    version: string;
    prompt_type: string;
    template: string;
    variables_schema: Record<string, unknown>;
    output_schema?: Record<string, unknown> | null;
    parent_version_id?: number | null;
  }): Promise<PromptVersionView> {
    await delay(300);
    const newVersion: PromptVersionView = {
      id: Math.floor(Math.random() * 10000) + 100,
      name: cmd.name,
      version: cmd.version,
      prompt_type: cmd.prompt_type,
      template: cmd.template,
      variables_schema: cmd.variables_schema,
      output_schema: cmd.output_schema ?? null,
      status: 'draft',
      parent_version_id: cmd.parent_version_id ?? null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    if (!SEED_PROMPT_VERSIONS[cmd.name]) {
      SEED_PROMPT_VERSIONS[cmd.name] = [];
    }
    SEED_PROMPT_VERSIONS[cmd.name]!.push(newVersion);
    SEED_PROMPTS.push({ name: cmd.name, prompt_type: cmd.prompt_type, latest_version: cmd.version, status: 'draft', created_at: new Date().toISOString() });
    return newVersion;
  },

  async updatePrompt(
    name: string,
    version: string,
    cmd: {
      template?: string;
      variables_schema?: Record<string, unknown>;
      output_schema?: Record<string, unknown> | null;
    },
  ): Promise<PromptVersionView> {
    await delay(250);
    const versions = SEED_PROMPT_VERSIONS[name] ?? [];
    const idx = versions.findIndex((v) => v.version === version);
    if (idx === -1) throw new Error(`Prompt ${name} version ${version} not found`);
    const updated: PromptVersionView = {
      ...versions[idx]!,
      template: cmd.template ?? versions[idx]!.template,
      variables_schema: cmd.variables_schema ?? versions[idx]!.variables_schema,
      output_schema: cmd.output_schema !== undefined ? cmd.output_schema : versions[idx]!.output_schema,
      updated_at: new Date().toISOString(),
    };
    SEED_PROMPT_VERSIONS[name]![idx] = updated;
    return updated;
  },

  async publishPrompt(name: string, version: string): Promise<PromptVersionView> {
    await delay(200);
    const versions = SEED_PROMPT_VERSIONS[name] ?? [];
    const idx = versions.findIndex((v) => v.version === version);
    if (idx === -1) throw new Error(`Prompt ${name} version ${version} not found`);
    const updated: PromptVersionView = { ...versions[idx]!, status: 'published', updated_at: new Date().toISOString() };
    SEED_PROMPT_VERSIONS[name]![idx] = updated;
    const promptIdx = SEED_PROMPTS.findIndex((p) => p.name === name);
    if (promptIdx !== -1) {
      SEED_PROMPTS[promptIdx] = { ...SEED_PROMPTS[promptIdx]!, latest_version: version, status: 'published' };
    }
    return updated;
  },

  async archivePrompt(name: string, version: string): Promise<PromptVersionView> {
    await delay(200);
    const versions = SEED_PROMPT_VERSIONS[name] ?? [];
    const idx = versions.findIndex((v) => v.version === version);
    if (idx === -1) throw new Error(`Prompt ${name} version ${version} not found`);
    const updated: PromptVersionView = { ...versions[idx]!, status: 'archived', updated_at: new Date().toISOString() };
    SEED_PROMPT_VERSIONS[name]![idx] = updated;
    return updated;
  },

  async getPromptAnalytics(name: string, version: string): Promise<PromptAnalyticsView> {
    await delay(200);
    const versions = SEED_PROMPT_VERSIONS[name] ?? [];
    const found = versions.find((v) => v.version === version);
    return {
      prompt_version_id: found?.id ?? Math.floor(Math.random() * 10000) + 100,
      name,
      version,
      render_count: Math.floor(Math.random() * 5000) + 500,
      success_count: Math.floor(Math.random() * 4900) + 480,
      failure_count: Math.floor(Math.random() * 50) + 5,
      avg_latency_ms: Math.round((600 + Math.random() * 600) * 100) / 100,
      total_tokens: Math.floor(Math.random() * 1000000) + 100000,
      last_rendered_at: isoDate(Math.floor(Math.random() * 3)),
    };
  },

  async comparePrompts(cmd: { name: string; version_a: string; version_b: string }): Promise<PromptCompareView> {
    await delay(400);
    const versions = SEED_PROMPT_VERSIONS[cmd.name] ?? [];
    const verA = versions.find((v) => v.version === cmd.version_a);
    const verB = versions.find((v) => v.version === cmd.version_b);
    return {
      name: cmd.name,
      version_a: verA ?? { id: 0, name: cmd.name, version: cmd.version_a, prompt_type: 'quick_practice_prompt', template: 'Template not found', variables_schema: {}, output_schema: null, status: 'archived', parent_version_id: null, created_at: '', updated_at: '' },
      version_b: verB ?? { id: 0, name: cmd.name, version: cmd.version_b, prompt_type: 'quick_practice_prompt', template: 'Template not found', variables_schema: {}, output_schema: null, status: 'archived', parent_version_id: null, created_at: '', updated_at: '' },
      diff_summary: verA && verB ? `Comparing v${verA.version} to v${verB.version}` : null,
    };
  },

  // --- Admin: Pipelines ------------------------------------------------------

  async listPipelines(): Promise<PipelineDefinitionView[]> {
    await delay(200);
    return [...SEED_PIPELINES];
  },

  async getPipelineDAG(pipelineName: string): Promise<PipelineDAGView> {
    await delay(200);
    const dag = SEED_PIPELINE_DAGS[pipelineName];
    if (!dag) throw new Error(`Pipeline ${pipelineName} not found`);
    return dag;
  },

  async listPipelineRuns(
    pipelineName: string,
    params?: { offset?: number; limit?: number },
  ): Promise<PipelineRunSummaryView[]> {
    await delay(200);
    const runs = SEED_PIPELINE_RUNS[pipelineName] ?? [];
    const offset = params?.offset ?? 0;
    const limit = params?.limit ?? 50;
    return runs.slice(offset, offset + limit);
  },

  async getPipelineTrace(pipelineName: string, pipelineRunId: string): Promise<PipelineTraceView> {
    await delay(250);
    const trace = SEED_PIPELINE_TRACES[pipelineRunId];
    if (!trace || trace.pipeline_name !== pipelineName) {
      return {
        pipeline_run_id: pipelineRunId,
        pipeline_name: pipelineName,
        execution_sequence: [
          { stage_name: 'start', event_type: 'STARTED', timestamp: isoDate(1), duration_ms: 10, status: 'OK', error: null },
          { stage_name: 'process', event_type: 'STARTED', timestamp: isoDate(1), duration_ms: 500, status: 'OK', error: null },
          { stage_name: 'end', event_type: 'COMPLETED', timestamp: isoDate(1), duration_ms: 5, status: 'OK', error: null },
        ],
        total_duration_ms: 515,
        started_at: isoDate(1),
        completed_at: isoDate(1),
      };
    }
    return trace;
  },

  async getPipelineMetrics(pipelineName: string): Promise<PipelineMetricsView> {
    await delay(250);
    const metrics = SEED_PIPELINE_METRICS[pipelineName];
    if (!metrics) {
      const totalRuns = Math.floor(Math.random() * 500) + 100;
      const successCount = Math.floor(Math.random() * 450) + 90;
      const failureCount = Math.floor(Math.random() * 20) + 5;
      const cancelCount = Math.floor(Math.random() * 10) + 2;
      return {
        pipeline_name: pipelineName,
        total_runs: totalRuns,
        success_count: successCount,
        failure_count: failureCount,
        cancel_count: cancelCount,
        success_rate: successCount / totalRuns,
        avg_duration_ms: 500,
        p95_duration_ms: 1200,
        stage_metrics: [
          { stage_name: 'stage_1', invocation_count: 100, success_count: 98, failure_count: 2, skip_count: 0, cancel_count: 2, retry_count: 5, avg_duration_ms: 120.5, p50_duration_ms: 115, p95_duration_ms: 180, p99_duration_ms: 250 },
        ],
      };
    }
    return metrics;
  },

  // --- Admin: Rubrics --------------------------------------------------------

  async listRubrics(): Promise<RubricView[]> {
    await delay(200);
    return [..._rubricsAdmin];
  },

  async getRubric(rubricId: string): Promise<RubricView> {
    await delay(200);
    const rubric = _rubricsAdmin.find((r) => r.rubric_id === rubricId);
    if (!rubric) throw new Error(`Rubric ${rubricId} not found`);
    return rubric;
  },

  async createRubric(cmd: {
    rubric_id: string;
    family: string;
    version: string;
    content_type: string;
    schema_version: string;
    name: string;
    criteria?: RubricCriterionInput[];
  }): Promise<RubricView> {
    await delay(300);
    const rubric: RubricView = {
      rubric_id: cmd.rubric_id,
      family: cmd.family,
      version: cmd.version,
      content_type: cmd.content_type,
      schema_version: cmd.schema_version,
      name: cmd.name,
    };
    _rubricsAdmin.push(rubric as RubricAdminView);
    return rubric;
  },

  async updateRubric(
    rubricId: string,
    cmd: { family?: string; version?: string; name?: string },
  ): Promise<RubricView> {
    await delay(200);
    const idx = _rubricsAdmin.findIndex((r) => r.rubric_id === rubricId);
    if (idx === -1) throw new Error(`Rubric ${rubricId} not found`);
    const updated: RubricView = {
      ..._rubricsAdmin[idx]!,
      family: cmd.family ?? _rubricsAdmin[idx]!.family,
      version: cmd.version ?? _rubricsAdmin[idx]!.version,
      name: cmd.name ?? _rubricsAdmin[idx]!.name,
    };
    _rubricsAdmin[idx] = updated as RubricAdminView;
    return updated;
  },

  async deleteRubric(rubricId: string): Promise<{ status: string }> {
    await delay(200);
    const idx = _rubricsAdmin.findIndex((r) => r.rubric_id === rubricId);
    if (idx !== -1) {
      _rubricsAdmin = _rubricsAdmin.filter((r) => r.rubric_id !== rubricId);
    }
    return { status: 'deleted' };
  },

  async addRubricCriterion(rubricId: string, criterion: RubricCriterionInput): Promise<RubricView> {
    await delay(250);
    const idx = _rubricsAdmin.findIndex((r) => r.rubric_id === rubricId);
    if (idx === -1) throw new Error(`Rubric ${rubricId} not found`);
    const newCriterion: RubricCriterionAdminView = {
      criterion_ref: criterion.criterion_ref,
      skill_slug: criterion.skill_slug,
      title: criterion.title,
      description: criterion.description,
      weight: criterion.weight,
      required: criterion.required,
      position: criterion.position,
      levels: criterion.levels,
    };
    const existing = _rubricsAdmin[idx]!;
    const updated: RubricAdminView = {
      ...existing,
      criteria: [...(existing.criteria ?? []), newCriterion],
    };
    _rubricsAdmin[idx] = updated;
    return updated;
  },

  async updateRubricCriterion(
    rubricId: string,
    criterionRef: string,
    criterion: Partial<RubricCriterionInput>,
  ): Promise<RubricView> {
    await delay(250);
    const idx = _rubricsAdmin.findIndex((r) => r.rubric_id === rubricId);
    if (idx === -1) throw new Error(`Rubric ${rubricId} not found`);
    const existing = _rubricsAdmin[idx]!;
    const criteriaIdx = existing.criteria?.findIndex((c) => c.criterion_ref === criterionRef) ?? -1;
    if (criteriaIdx === -1) throw new Error(`Criterion ${criterionRef} not found`);
    const updatedCriteria = (existing.criteria ?? []).map((c, i) =>
      i === criteriaIdx ? { ...c, ...criterion } : c,
    );
    const updated: RubricAdminView = { ...existing, criteria: updatedCriteria };
    _rubricsAdmin[idx] = updated;
    return updated;
  },

  async deleteRubricCriterion(rubricId: string, criterionRef: string): Promise<RubricView> {
    await delay(250);
    const idx = _rubricsAdmin.findIndex((r) => r.rubric_id === rubricId);
    if (idx === -1) throw new Error(`Rubric ${rubricId} not found`);
    const existing = _rubricsAdmin[idx]!;
    const updated: RubricAdminView = {
      ...existing,
      criteria: (existing.criteria ?? []).filter((c) => c.criterion_ref !== criterionRef),
    };
    _rubricsAdmin[idx] = updated;
    return updated;
  },

  // --- Admin: Audit & Events -------------------------------------------------

  async listWorkflowEvents(params?: {
    event_type?: string;
    trace_id?: string;
    workflow_id?: string;
    request_id?: string;
    error_code?: string;
    offset?: number;
    limit?: number;
  }): Promise<PaginatedWorkflowEventsView> {
    await delay(200);
    let filtered = [..._workflowEvents];
    if (params?.event_type) {
      filtered = filtered.filter((e) => e.event_type === params.event_type);
    }
    if (params?.error_code) {
      filtered = filtered.filter((e) => e.error_code === params.error_code);
    }
    if (params?.trace_id) {
      filtered = filtered.filter((e) => e.trace_id === params.trace_id);
    }
    if (params?.workflow_id) {
      filtered = filtered.filter((e) => e.workflow_id === params.workflow_id);
    }
    const offset = params?.offset ?? 0;
    const limit = params?.limit ?? 50;
    return {
      items: filtered.slice(offset, offset + limit),
      total: filtered.length,
      offset,
      limit,
    };
  },

  async getWorkflowEvent(eventId: string): Promise<WorkflowEventView> {
    await delay(150);
    const event = _workflowEvents.find((e) => e.event_id === eventId);
    if (!event) throw new Error(`Event ${eventId} not found`);
    return event;
  },

  async updateWorkflowEvent(
    eventId: string,
    cmd: { error_code?: string; payload?: Record<string, unknown> },
  ): Promise<WorkflowEventView> {
    await delay(200);
    const idx = _workflowEvents.findIndex((e) => e.event_id === eventId);
    if (idx === -1) throw new Error(`Event ${eventId} not found`);
    const updated: WorkflowEventView = {
      ..._workflowEvents[idx]!,
      error_code: cmd.error_code ?? _workflowEvents[idx]!.error_code,
      payload: cmd.payload ?? _workflowEvents[idx]!.payload,
    };
    _workflowEvents[idx] = updated;
    return updated;
  },

  async deleteWorkflowEvent(eventId: string): Promise<{ status: string }> {
    await delay(200);
    _workflowEvents = _workflowEvents.filter((e) => e.event_id !== eventId);
    return { status: 'deleted' };
  },

  async getAttemptAudit(attemptId: string): Promise<AttemptAuditView> {
    await delay(300);
    return {
      attempt: {
        attempt_id: attemptId,
        session_id: `sess-${uid()}`,
        practice_type: 'quick_practice',
        content_item_id: `pi-${uid()}`,
        content_item_type: 'prompt_item',
        status: 'assessed',
        overall_score: Math.floor(Math.random() * 2) + 3,
        submitted_at: isoDate(2),
        assessed_at: isoDate(2),
      },
      response_visibility: 'visible_to_learner',
      access_relationship: null,
      prompt: {
        prompt_version: 'quick_practice_prompt@v1.2.0',
        template: 'You are a professional practice coach...',
      },
      response_text: 'This is a sample learner response for the attempt audit trail.',
      assessment: {
        assessment_id: `assess-${uid()}`,
        validation_status: 'validated',
        prompt_version: 'assessment.quick-practice.v1',
        rubric_id: 'quick_practice_text@v1',
        rubric_version: 'v1',
        schema_version: '1.0',
        config_version: '1.0',
        provider: 'openrouter',
        model_slug: 'gpt-4o-mini',
        overall_score: 4,
        rejection_code: null,
        trace_id: `trace-${uid()}`,
        pipeline_run_id: `run-${uid()}`,
        evidence_count: 2,
        strengths_count: 3,
        weaknesses_count: 2,
        next_actions_count: 3,
        evidence_quotes: ['Sample evidence quote 1', 'Sample evidence quote 2'],
        strengths: ['Clear communication', 'Good structure', 'Relevant examples'],
        weaknesses: ['Could add more detail', 'Timing could be improved'],
        next_actions: ['Practice with more scenarios', 'Focus on active listening', 'Review feedback'],
        skill_scores: [
          { skill_slug: 'communication', score: 4, rationale: 'Clear and well-structured response' },
          { skill_slug: 'active-listening', score: 4, rationale: 'Demonstrated good understanding of context' },
        ],
        created_at: isoDate(2),
      },
      latest_progress_snapshot_id: `snap-${uid()}`,
      latest_recommendation_id: `rec-${uid()}`,
      workflow_events: [
        { event_id: `evt-${uid()}`, event_type: 'attempt.submitted', occurred_at: isoDate(2), payload: { attempt_id: attemptId } },
        { event_id: `evt-${uid()}`, event_type: 'assessment.started', occurred_at: isoDate(2), payload: { attempt_id: attemptId } },
        { event_id: `evt-${uid()}`, event_type: 'assessment.validated', occurred_at: isoDate(2), payload: { attempt_id: attemptId, score: 4 } },
      ],
      pipeline_runs: [
        { pipeline_run_id: `pr-${uid()}`, pipeline_name: 'assessment_flow', status: 'completed', started_at: isoDate(2), completed_at: isoDate(2) },
      ],
      provider_calls: [
        { call_id: `call-${uid()}`, provider: 'openrouter', model_slug: 'gpt-4o-mini', operation: 'chat.complete', latency_ms: 850, success: true, error_code: null, trace_id: `trace-${uid()}` },
      ],
    };
  },

  // --- Assistant ------------------------------------------------------------
  async createAssistantSession(cmd?: CreateAssistantSessionCommand): Promise<AssistantSessionView> {
    await delay(200);
    const newSession: AssistantSessionView = {
      id: `session-${uid()}`,
      user_id: SEED_CURRENT_USER.id,
      title: cmd?.title || 'New Chat Session',
      status: 'active',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      turns: [],
      messages: [],
    };
    SEED_ASSISTANT_SESSIONS.unshift(newSession);
    return newSession;
  },

  async listAssistantSessions(): Promise<AssistantSessionView[]> {
    await delay(150);
    return SEED_ASSISTANT_SESSIONS.filter(session => session.user_id === SEED_CURRENT_USER.id);
  },

  async getAssistantSession(sessionId: string): Promise<AssistantSessionView> {
    await delay(100);
    const session = SEED_ASSISTANT_SESSIONS.find(s => s.id === sessionId);
    if (!session) {
      throw new Error(`Session ${sessionId} not found`);
    }
    return session;
  },

  async createAssistantTurn(sessionId: string, cmd: CreateAssistantTurnCommand): Promise<AssistantTurnView> {
    await delay(300);
    
    const session = SEED_ASSISTANT_SESSIONS.find(s => s.id === sessionId);
    if (!session) {
      throw new Error(`Session ${sessionId} not found`);
    }

    const userMessage: AssistantMessageView = {
      id: `msg-${uid()}`,
      turn_id: `turn-${uid()}`,
      role: 'user',
      content: cmd.message,
      metadata: {},
      created_at: new Date().toISOString(),
    };

    const turnId = `turn-${uid()}`;
    const streamToken = `st-${uid()}`;

    // Determine which tool to call based on message content
    const messageLower = cmd.message.toLowerCase();
    const isGenerate = messageLower.includes('generate');
    const isPractice = messageLower.includes('practice');

    const newTurn: AssistantTurnView = {
      id: turnId,
      session_id: sessionId,
      workflow_id: `wf-${uid()}`,
      request_id: `req-${uid()}`,
      trace_id: `trace-${uid()}`,
      pipeline_run_id: `pr-${uid()}`,
      status: 'running',
      stream_token: streamToken,
      last_error_code: null,
      cancel_reason: null,
      created_at: new Date().toISOString(),
      started_at: new Date().toISOString(),
      completed_at: null,
      cancelled_at: null,
      user_message_id: userMessage.id,
      assistant_message_id: null,
      messages: [userMessage],
      tool_calls: [],
    };

    // Store turn for later retrieval
    SEED_TURNS.push(newTurn);

    // Start the async tool flow
    simulateToolFlow(sessionId, turnId, cmd.message, userMessage, isGenerate, isPractice);

    return newTurn;
  },

  async getAssistantTurn(turnId: string): Promise<AssistantTurnView> {
    await delay(100);
    const turn = SEED_TURNS.find(t => t.id === turnId);
    if (!turn) {
      throw new Error(`Turn ${turnId} not found`);
    }
    return turn;
  },

  async cancelAssistantTurn(turnId: string, cmd?: CancelAssistantTurnCommand): Promise<AssistantTurnView> {
    await delay(200);
    const turnIndex = SEED_TURNS.findIndex(t => t.id === turnId);
    if (turnIndex === -1) {
      throw new Error(`Turn ${turnId} not found`);
    }
    
    const turn = SEED_TURNS[turnIndex];
    if (!turn) {
      throw new Error(`Turn ${turnId} not found`);
    }
    
    if (turn.status === 'running') {
      const cancelledTurn: AssistantTurnView = {
        id: turn.id,
        session_id: turn.session_id,
        workflow_id: turn.workflow_id,
        request_id: turn.request_id,
        trace_id: turn.trace_id,
        pipeline_run_id: turn.pipeline_run_id,
        status: 'cancelled',
        stream_token: turn.stream_token,
        last_error_code: turn.last_error_code,
        cancel_reason: cmd?.reason || 'user_requested',
        created_at: turn.created_at,
        started_at: turn.started_at,
        completed_at: new Date().toISOString(),
        cancelled_at: new Date().toISOString(),
        user_message_id: turn.user_message_id,
        assistant_message_id: turn.assistant_message_id,
        messages: turn.messages,
        tool_calls: turn.tool_calls,
      };
      SEED_TURNS[turnIndex] = cancelledTurn;
      return cancelledTurn;
    }
    
    return turn;
  },

  streamAssistantTurn(streamToken: string, callbacks: AssistantStreamCallbacks): () => void {
    const turn = SEED_TURNS.find((item) => item.stream_token === streamToken);
    if (!turn) {
      callbacks.onError?.(`Stream ${streamToken} not found`);
      callbacks.onClose?.();
      return () => {};
    }

    const message = turn.messages.find((item) => item.role === 'user')?.content.toLowerCase() ?? '';
    const isGenerate = message.includes('generate');
    const isPractice = message.includes('practice');

    const runningTool: AssistantToolCallView = {
      id: `tc-${uid()}`,
      turn_id: turn.id,
      tool_name: isGenerate
        ? 'generate_collection'
        : isPractice
          ? 'start_collection_practice'
          : 'list_collections',
      status: 'running',
      args: isGenerate
        ? { prompt: message, difficulty: 'intermediate' }
        : isPractice
          ? { collection_id: SEED_COLLECTIONS[0]?.id }
          : {},
      result: null,
      error_code: null,
      error_message: null,
      child_run_id: null,
      started_at: new Date().toISOString(),
      completed_at: null,
    };

    callbacks.onToolStarted?.(runningTool);

    const completionDelay = isGenerate ? 2300 : isPractice ? 800 : 600;
    const timeoutId = setTimeout(() => {
      const latestTurn = SEED_TURNS.find((item) => item.stream_token === streamToken);
      if (!latestTurn) {
        callbacks.onError?.(`Completed turn for stream ${streamToken} not found`);
        callbacks.onClose?.();
        return;
      }

      const completedTool = latestTurn.tool_calls[0] ?? {
        ...runningTool,
        status: 'completed' as const,
        completed_at: new Date().toISOString(),
      };

      if (completedTool.status === 'failed') {
        callbacks.onToolFailed?.(completedTool);
      } else {
        callbacks.onToolCompleted?.(completedTool);
      }

      callbacks.onTurnCompleted?.();
      callbacks.onClose?.();
    }, completionDelay);

    return () => {
      clearTimeout(timeoutId);
      callbacks.onClose?.();
    };
  },

  // --- Admin: Telemetry & Monitoring -----------------------------------------

  async getTelemetryOverview(_params?: {
    organisation_id?: string;
    from_date?: string;
    to_date?: string;
  }): Promise<TelemetryOverviewView> {
    await delay(300);
    return {
      organisation_id: null,
      from_date: null,
      to_date: null,
      total_provider_calls: 15420,
      provider_call_success_rate: 0.967,
      avg_provider_latency_ms: 342,
      total_pipeline_runs: 11160,
      pipeline_success_rate: 0.94,
      total_workflow_events: 45230,
      total_errors: 512,
      error_rate: 0.011,
      latency_distribution: [
        { bucket_ms: 100, count: 2100, percentage: 13.6 },
        { bucket_ms: 200, count: 4500, percentage: 29.2 },
        { bucket_ms: 300, count: 3800, percentage: 24.6 },
        { bucket_ms: 500, count: 2400, percentage: 15.6 },
        { bucket_ms: 1000, count: 1800, percentage: 11.7 },
        { bucket_ms: 2000, count: 620, percentage: 4.0 },
        { bucket_ms: 5000, count: 200, percentage: 1.3 },
      ],
      pipeline_health: [
        { pipeline_name: 'assessment-pipeline', total_runs: 3420, success_count: 3249, failure_count: 137, cancel_count: 34, success_rate: 0.95, avg_duration_ms: 1200, error_rate: 0.04, last_run_at: isoDate(0) },
        { pipeline_name: 'generation-pipeline', total_runs: 1250, success_count: 1150, failure_count: 75, cancel_count: 25, success_rate: 0.92, avg_duration_ms: 2800, error_rate: 0.06, last_run_at: isoDate(1) },
        { pipeline_name: 'feedback-pipeline', total_runs: 5100, success_count: 4998, failure_count: 71, cancel_count: 31, success_rate: 0.98, avg_duration_ms: 800, error_rate: 0.014, last_run_at: isoDate(0) },
        { pipeline_name: 'interview-pipeline', total_runs: 890, success_count: 792, failure_count: 74, cancel_count: 24, success_rate: 0.89, avg_duration_ms: 3500, error_rate: 0.083, last_run_at: isoDate(2) },
      ],
      provider_metrics: [
        { provider: 'openai', model_slug: 'gpt-4o-mini', operation: 'chat.completion', call_count: 8500, success_count: 8245, failure_count: 255, success_rate: 0.97, avg_latency_ms: 380, p50_latency_ms: 350, p95_latency_ms: 850, p99_latency_ms: 1200, total_tokens: 45600000 },
        { provider: 'openai', model_slug: 'text-embedding-3-small', operation: 'embedding', call_count: 3200, success_count: 3168, failure_count: 32, success_rate: 0.99, avg_latency_ms: 120, p50_latency_ms: 110, p95_latency_ms: 250, p99_latency_ms: 400, total_tokens: 8500000 },
        { provider: 'anthropic', model_slug: 'claude-3-haiku', operation: 'chat.completion', call_count: 2800, success_count: 2688, failure_count: 112, success_rate: 0.96, avg_latency_ms: 420, p50_latency_ms: 390, p95_latency_ms: 920, p99_latency_ms: 1400, total_tokens: 28900000 },
        { provider: 'google', model_slug: 'gemini-pro', operation: 'chat.completion', call_count: 920, success_count: 864, failure_count: 56, success_rate: 0.94, avg_latency_ms: 510, p50_latency_ms: 480, p95_latency_ms: 1100, p99_latency_ms: 1600, total_tokens: 12300000 },
      ],
      error_breakdown: [
        { error_code: 'RATE_LIMIT', error_type: 'RateLimitError', count: 245, percentage: 47.8, examples: ['Rate limit exceeded for openai', 'Too many requests to anthropic'] },
        { error_code: 'TIMEOUT', error_type: 'TimeoutError', count: 128, percentage: 25.0, examples: ['Request timed out after 30s', 'LLM response timeout'] },
        { error_code: 'INVALID_INPUT', error_type: 'ValidationError', count: 89, percentage: 17.4, examples: ['Invalid prompt template', 'Missing required fields'] },
        { error_code: 'INTERNAL', error_type: 'ServerError', count: 50, percentage: 9.8, examples: ['Internal server error', 'Database connection failed'] },
      ],
    };
  },

  async listTelemetryTraces(params?: {
    organisation_id?: string;
    from_date?: string;
    to_date?: string;
    limit?: number;
    offset?: number;
  }): Promise<TelemetryTraceListView> {
    await delay(250);
    const limit = params?.limit ?? 20;
    const traces: TelemetryTraceListItemView[] = [
      { trace_id: 'trace-001-abc123', organisation_id: null, operation_name: 'AssessAttempt', service_name: 'assessment-service', duration_ms: 1250, span_count: 8, error_count: 0, started_at: new Date(Date.now() - 60000).toISOString() },
      { trace_id: 'trace-002-def456', organisation_id: null, operation_name: 'GenerateCollection', service_name: 'generation-service', duration_ms: 3420, span_count: 12, error_count: 0, started_at: new Date(Date.now() - 120000).toISOString() },
      { trace_id: 'trace-003-ghi789', organisation_id: null, operation_name: 'ProcessFeedback', service_name: 'feedback-service', duration_ms: 890, span_count: 5, error_count: 0, started_at: new Date(Date.now() - 180000).toISOString() },
      { trace_id: 'trace-004-jkl012', organisation_id: null, operation_name: 'AssessAttempt', service_name: 'assessment-service', duration_ms: 2100, span_count: 8, error_count: 1, started_at: new Date(Date.now() - 240000).toISOString() },
      { trace_id: 'trace-005-mno345', organisation_id: null, operation_name: 'RunInterview', service_name: 'interview-service', duration_ms: 4500, span_count: 15, error_count: 0, started_at: new Date(Date.now() - 300000).toISOString() },
      { trace_id: 'trace-006-pqr678', organisation_id: null, operation_name: 'GeneratePrompts', service_name: 'generation-service', duration_ms: 2800, span_count: 10, error_count: 0, started_at: new Date(Date.now() - 360000).toISOString() },
      { trace_id: 'trace-007-stu901', organisation_id: null, operation_name: 'AssessAttempt', service_name: 'assessment-service', duration_ms: 1100, span_count: 7, error_count: 0, started_at: new Date(Date.now() - 420000).toISOString() },
      { trace_id: 'trace-008-vwx234', organisation_id: null, operation_name: 'ProcessFeedback', service_name: 'feedback-service', duration_ms: 750, span_count: 4, error_count: 0, started_at: new Date(Date.now() - 480000).toISOString() },
      { trace_id: 'trace-009-yza567', organisation_id: null, operation_name: 'GenerateCollection', service_name: 'generation-service', duration_ms: 5200, span_count: 14, error_count: 2, started_at: new Date(Date.now() - 540000).toISOString() },
      { trace_id: 'trace-010-bcd890', organisation_id: null, operation_name: 'AssessAttempt', service_name: 'assessment-service', duration_ms: 980, span_count: 6, error_count: 0, started_at: new Date(Date.now() - 600000).toISOString() },
    ];
    return {
      traces: traces.slice(0, limit),
      total: 1250,
      offset: params?.offset ?? 0,
      limit,
    };
  },

  async getTelemetryTrace(traceId: string): Promise<TelemetryTraceView> {
    await delay(200);
    const startTime = new Date(Date.now() - 60000);
    const endTime = new Date(Date.now() - 58750);
    return {
      trace_id: traceId,
      organisation_id: null,
      spans: [
        { span_id: 'span-001', parent_span_id: null, operation_name: 'AssessAttempt', service_name: 'assessment-service', start_time: startTime.toISOString(), end_time: endTime.toISOString(), duration_ms: 1250, status_code: 'ok', error: null, attributes: { attempt_id: 'att-123' } },
        { span_id: 'span-002', parent_span_id: 'span-001', operation_name: 'LoadRubric', service_name: 'assessment-service', start_time: new Date(Date.now() - 59950).toISOString(), end_time: new Date(Date.now() - 59900).toISOString(), duration_ms: 50, status_code: 'ok', error: null, attributes: {} },
        { span_id: 'span-003', parent_span_id: 'span-001', operation_name: 'CallLLM', service_name: 'llm-gateway', start_time: new Date(Date.now() - 59900).toISOString(), end_time: new Date(Date.now() - 58920).toISOString(), duration_ms: 980, status_code: 'ok', error: null, attributes: { provider: 'openai', model: 'gpt-4' } },
        { span_id: 'span-004', parent_span_id: 'span-001', operation_name: 'SaveAssessment', service_name: 'assessment-service', start_time: new Date(Date.now() - 58920).toISOString(), end_time: endTime.toISOString(), duration_ms: 120, status_code: 'ok', error: null, attributes: {} },
      ],
      total_duration_ms: 1250,
      started_at: startTime.toISOString(),
      completed_at: endTime.toISOString(),
      error_count: 0,
      span_count: 4,
    };
  },

  // --- Admin: Org-scoped Skills ---------------------------------------------
  async listOrgSkills(orgId: string): Promise<OrgSkillView[]> {
    await delay(200);
    requireOrgAccess(orgId, 'org:read');
    return _orgSkills.filter((s) => s.organisation_id === orgId);
  },

  async getOrgSkill(orgId: string, skillSlug: string): Promise<OrgSkillView> {
    await delay(200);
    requireOrgAccess(orgId, 'org:read');
    const skill = _orgSkills.find((s) => s.organisation_id === orgId && s.slug === skillSlug);
    if (!skill) throw new Error(`Skill ${skillSlug} not found`);
    return skill;
  },

  async createOrgSkill(orgId: string, cmd: { slug: string; name: string; description: string }): Promise<OrgSkillView> {
    await delay(300);
    requireOrgAccess(orgId, 'org:write');
    const skill: OrgSkillView = {
      slug: cmd.slug,
      name: cmd.name,
      description: cmd.description ?? '',
      organisation_id: orgId,
    };
    _orgSkills.push(skill);
    return skill;
  },

  async updateOrgSkill(orgId: string, skillSlug: string, cmd: { name?: string; description?: string }): Promise<OrgSkillView> {
    await delay(200);
    requireOrgAccess(orgId, 'org:write');
    const idx = _orgSkills.findIndex((s) => s.organisation_id === orgId && s.slug === skillSlug);
    if (idx === -1) throw new Error(`Skill ${skillSlug} not found`);
    const updated: OrgSkillView = {
      ..._orgSkills[idx]!,
      name: cmd.name ?? _orgSkills[idx]!.name,
      description: cmd.description ?? _orgSkills[idx]!.description,
    };
    _orgSkills[idx] = updated;
    return updated;
  },

  async deleteOrgSkill(orgId: string, skillSlug: string): Promise<{ status: string }> {
    await delay(200);
    requireOrgAccess(orgId, 'org:write');
    _orgSkills = _orgSkills.filter((s) => !(s.organisation_id === orgId && s.slug === skillSlug));
    return { status: 'deleted' };
  },

  // --- Admin: Org-scoped Competencies ---------------------------------------
  async listOrgCompetencies(orgId: string): Promise<OrgCompetencyView[]> {
    await delay(200);
    requireOrgAccess(orgId, 'org:read');
    return _orgCompetencies.filter((c) => c.organisation_id === orgId);
  },

  async getOrgCompetency(orgId: string, competencySlug: string): Promise<OrgCompetencyView> {
    await delay(200);
    requireOrgAccess(orgId, 'org:read');
    const competency = _orgCompetencies.find((c) => c.organisation_id === orgId && c.slug === competencySlug);
    if (!competency) throw new Error(`Competency ${competencySlug} not found`);
    return competency;
  },

  async createOrgCompetency(orgId: string, cmd: { slug: string; name: string; description: string; skill_slugs?: string[] }): Promise<OrgCompetencyView> {
    await delay(300);
    requireOrgAccess(orgId, 'org:write');
    const competency: OrgCompetencyView = {
      slug: cmd.slug,
      name: cmd.name,
      description: cmd.description ?? '',
      skill_slugs: cmd.skill_slugs ?? [],
      organisation_id: orgId,
    };
    _orgCompetencies.push(competency);
    return competency;
  },

  async updateOrgCompetency(orgId: string, competencySlug: string, cmd: { name?: string; description?: string; skill_slugs?: string[] }): Promise<OrgCompetencyView> {
    await delay(200);
    requireOrgAccess(orgId, 'org:write');
    const idx = _orgCompetencies.findIndex((c) => c.organisation_id === orgId && c.slug === competencySlug);
    if (idx === -1) throw new Error(`Competency ${competencySlug} not found`);
    const updated: OrgCompetencyView = {
      ..._orgCompetencies[idx]!,
      name: cmd.name ?? _orgCompetencies[idx]!.name,
      description: cmd.description ?? _orgCompetencies[idx]!.description,
      skill_slugs: cmd.skill_slugs ?? _orgCompetencies[idx]!.skill_slugs,
    };
    _orgCompetencies[idx] = updated;
    return updated;
  },

  async deleteOrgCompetency(orgId: string, competencySlug: string): Promise<{ status: string }> {
    await delay(200);
    requireOrgAccess(orgId, 'org:write');
    _orgCompetencies = _orgCompetencies.filter((c) => !(c.organisation_id === orgId && c.slug === competencySlug));
    return { status: 'deleted' };
  },

  // --- Admin: Org-scoped Rubrics --------------------------------------------
  async listOrgRubrics(orgId: string): Promise<OrgRubricView[]> {
    await delay(200);
    requireOrgAccess(orgId, 'org:read');
    return _orgRubrics.filter((r) => r.organisation_id === orgId);
  },

  async getOrgRubric(orgId: string, rubricId: string): Promise<OrgRubricView> {
    await delay(200);
    requireOrgAccess(orgId, 'org:read');
    const rubric = _orgRubrics.find((r) => r.organisation_id === orgId && r.rubric_id === rubricId);
    if (!rubric) throw new Error(`Rubric ${rubricId} not found`);
    return rubric;
  },

  async createOrgRubric(orgId: string, cmd: {
    rubric_id: string;
    family: string;
    version: string;
    content_type: string;
    schema_version: string;
    name: string;
    criteria?: string[];
  }): Promise<OrgRubricView> {
    await delay(300);
    requireOrgAccess(orgId, 'org:write');
    const rubric: OrgRubricView = {
      rubric_id: cmd.rubric_id,
      family: cmd.family,
      version: cmd.version,
      content_type: cmd.content_type,
      schema_version: cmd.schema_version,
      name: cmd.name,
      criteria: cmd.criteria ?? [],
      organisation_id: orgId,
    };
    _orgRubrics.push(rubric);
    return rubric;
  },

  async updateOrgRubric(orgId: string, rubricId: string, cmd: { name?: string; criteria?: string[] }): Promise<OrgRubricView> {
    await delay(200);
    requireOrgAccess(orgId, 'org:write');
    const idx = _orgRubrics.findIndex((r) => r.organisation_id === orgId && r.rubric_id === rubricId);
    if (idx === -1) throw new Error(`Rubric ${rubricId} not found`);
    const updated: OrgRubricView = {
      ..._orgRubrics[idx]!,
      name: cmd.name ?? _orgRubrics[idx]!.name,
      criteria: cmd.criteria ?? _orgRubrics[idx]!.criteria,
    };
    _orgRubrics[idx] = updated;
    return updated;
  },

  async deleteOrgRubric(orgId: string, rubricId: string): Promise<{ status: string }> {
    await delay(200);
    requireOrgAccess(orgId, 'org:write');
    _orgRubrics = _orgRubrics.filter((r) => !(r.organisation_id === orgId && r.rubric_id === rubricId));
    return { status: 'deleted' };
  },

  // --- Admin: Org-scoped Prompt Items ---------------------------------------
  async listOrgPromptItems(orgId: string): Promise<PromptItemView[]> {
    await delay(200);
    requireOrgAccess(orgId, 'org:read');
    return _orgPromptItems.filter((p) => p.organisation_id === orgId);
  },

  async getOrgPromptItem(orgId: string, promptItemId: string): Promise<PromptItemView> {
    await delay(200);
    requireOrgAccess(orgId, 'org:read');
    const item = _orgPromptItems.find((p) => p.organisation_id === orgId && p.id === promptItemId);
    if (!item) throw new Error(`Prompt item ${promptItemId} not found`);
    return item;
  },

  async createOrgPromptItem(orgId: string, cmd: PromptItemCreateCommand): Promise<PromptItemView> {
    await delay(300);
    requireOrgAccess(orgId, 'org:write');
    const item: PromptItemView = {
      id: `org-prompt-${uid()}`,
      prompt_type: cmd.prompt_type,
      title: cmd.title,
      prompt_text: cmd.prompt_text,
      difficulty: cmd.difficulty,
      lifecycle_state: 'draft',
      target_skill_slugs: cmd.target_skill_slugs,
      rubric_id: cmd.rubric_id,
      organisation_id: orgId,
    };
    _orgPromptItems.push(item);
    return item;
  },

  async updateOrgPromptItem(orgId: string, promptItemId: string, cmd: Partial<PromptItemCreateCommand>): Promise<PromptItemView> {
    await delay(200);
    requireOrgAccess(orgId, 'org:write');
    const idx = _orgPromptItems.findIndex((p) => p.organisation_id === orgId && p.id === promptItemId);
    if (idx === -1) throw new Error(`Prompt item ${promptItemId} not found`);
    const updated: PromptItemView = {
      ..._orgPromptItems[idx]!,
      title: cmd.title ?? _orgPromptItems[idx]!.title,
      prompt_text: cmd.prompt_text ?? _orgPromptItems[idx]!.prompt_text,
      difficulty: cmd.difficulty ?? _orgPromptItems[idx]!.difficulty,
      target_skill_slugs: cmd.target_skill_slugs ?? _orgPromptItems[idx]!.target_skill_slugs,
      rubric_id: cmd.rubric_id ?? _orgPromptItems[idx]!.rubric_id,
    };
    _orgPromptItems[idx] = updated;
    return updated;
  },

  async deleteOrgPromptItem(orgId: string, promptItemId: string): Promise<{ status: string }> {
    await delay(200);
    requireOrgAccess(orgId, 'org:write');
    _orgPromptItems = _orgPromptItems.filter((p) => !(p.organisation_id === orgId && p.id === promptItemId));
    return { status: 'deleted' };
  },

  // --- Admin: Org-scoped Scenarios ------------------------------------------
  async listOrgScenarios(orgId: string): Promise<ScenarioView[]> {
    await delay(200);
    requireOrgAccess(orgId, 'org:read');
    return _orgScenarios.filter((s) => s.organisation_id === orgId);
  },

  async getOrgScenario(orgId: string, scenarioId: string): Promise<ScenarioView> {
    await delay(200);
    requireOrgAccess(orgId, 'org:read');
    const scenario = _orgScenarios.find((s) => s.organisation_id === orgId && s.id === scenarioId);
    if (!scenario) throw new Error(`Scenario ${scenarioId} not found`);
    return scenario;
  },

  async createOrgScenario(orgId: string, cmd: ScenarioCreateCommand): Promise<ScenarioView> {
    await delay(300);
    requireOrgAccess(orgId, 'org:write');
    const mockCompanyView: MockCompanyView | null = cmd.mock_company ? { ...cmd.mock_company, id: `company-${uid()}` } : null;
    const mockPeopleViews: MockPersonView[] = (cmd.mock_people ?? []).map((p, i) => ({ ...p, id: `person-${uid()}-${i}`, goals: p.goals ?? [] }));
    const scenario: ScenarioView = {
      id: `org-scenario-${uid()}`,
      title: cmd.title,
      business_context: cmd.business_context,
      learner_objective: cmd.learner_objective,
      constraints: cmd.constraints ?? [],
      stakeholder_tensions: cmd.stakeholder_tensions ?? [],
      lifecycle_state: 'draft',
      target_skill_slugs: cmd.target_skill_slugs,
      rubric_id: cmd.rubric_id,
      mock_company: mockCompanyView,
      mock_people: mockPeopleViews,
      organisation_id: orgId,
    };
    _orgScenarios.push(scenario);
    return scenario;
  },

  async updateOrgScenario(orgId: string, scenarioId: string, cmd: Partial<ScenarioCreateCommand>): Promise<ScenarioView> {
    await delay(200);
    requireOrgAccess(orgId, 'org:write');
    const idx = _orgScenarios.findIndex((s) => s.organisation_id === orgId && s.id === scenarioId);
    if (idx === -1) throw new Error(`Scenario ${scenarioId} not found`);
    const existing = _orgScenarios[idx]!;
    const mockCompanyView: MockCompanyView | null = cmd.mock_company !== undefined 
      ? (cmd.mock_company ? { ...cmd.mock_company, id: existing.mock_company?.id ?? `company-${uid()}` } : null)
      : existing.mock_company;
    const mockPeopleViews: MockPersonView[] = cmd.mock_people !== undefined
      ? cmd.mock_people.map((p, i) => ({ ...p, id: existing.mock_people[i]?.id ?? `person-${uid()}-${i}`, goals: p.goals ?? [] }))
      : existing.mock_people;
    const updated: ScenarioView = {
      ...existing,
      title: cmd.title ?? existing.title,
      business_context: cmd.business_context ?? existing.business_context,
      learner_objective: cmd.learner_objective ?? existing.learner_objective,
      constraints: cmd.constraints ?? existing.constraints,
      stakeholder_tensions: cmd.stakeholder_tensions ?? existing.stakeholder_tensions,
      target_skill_slugs: cmd.target_skill_slugs ?? existing.target_skill_slugs,
      rubric_id: cmd.rubric_id ?? existing.rubric_id,
      mock_company: mockCompanyView,
      mock_people: mockPeopleViews,
    };
    _orgScenarios[idx] = updated;
    return updated;
  },

  async deleteOrgScenario(orgId: string, scenarioId: string): Promise<{ status: string }> {
    await delay(200);
    requireOrgAccess(orgId, 'org:write');
    _orgScenarios = _orgScenarios.filter((s) => !(s.organisation_id === orgId && s.id === scenarioId));
    return { status: 'deleted' };
  },
};
