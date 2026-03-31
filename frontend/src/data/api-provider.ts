import type { DataProvider } from './provider';
import type {
  UserView,
  AuthSessionView,
  LoginUserCommand,
  TaxonomySnapshot,
  CollectionView,
  CollectionListFilters,
  QuickPracticeSessionView,
  AttemptView,
  AttemptHistoryItem,
  InterviewSessionView,
  ScenarioSessionView,
  PracticeRunView,
  CompetencyProgressView,
  GenerationStartedView,
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
  WorkflowEventView,
  PaginatedWorkflowEventsView,
  AttemptAuditView,
  TelemetryOverviewView,
  TelemetryTraceListView,
  TelemetryTraceView,
  AssistantSessionView,
  AssistantTurnView,
  OrgSkillView,
  OrgCompetencyView,
  OrgRubricView,
  PromptItemView,
  ScenarioView,
  DeleteAccountResult,
} from './types';

const API_BASE = import.meta.env.VITE_API_BASE ?? '/api';
const USER_ID_STORAGE_KEY = 'ss_user_id';
const ACTIVE_ORG_STORAGE_KEY = 'ss_active_organisation_id';

export class ApiRequestError extends Error {
  readonly status: number | null;
  readonly isNetworkError: boolean;

  constructor(message: string, opts?: { status?: number | null; isNetworkError?: boolean }) {
    super(message);
    this.name = 'ApiRequestError';
    this.status = opts?.status ?? null;
    this.isNetworkError = opts?.isNetworkError ?? false;
  }
}

function getAuthHeaders(): Record<string, string> {
  const headers: Record<string, string> = {};
  const userId = sessionStorage.getItem(USER_ID_STORAGE_KEY);
  if (userId) {
    headers['X-User-ID'] = userId;
  }
  const activeOrganisationId = getStoredActiveOrganisation();
  if (activeOrganisationId) {
    headers['X-Organisation-ID'] = activeOrganisationId;
  }
  return headers;
}

function getStoredActiveOrganisation(): string | null {
  return sessionStorage.getItem(ACTIVE_ORG_STORAGE_KEY);
}

export function getStoredActiveOrganisationId(): string | null {
  return getStoredActiveOrganisation();
}

function setStoredActiveOrganisationId(organisationId: string | null): void {
  if (organisationId) {
    sessionStorage.setItem(ACTIVE_ORG_STORAGE_KEY, organisationId);
    return;
  }
  sessionStorage.removeItem(ACTIVE_ORG_STORAGE_KEY);
}

function clearStoredSession(): void {
  clearUserId();
  setStoredActiveOrganisationId(null);
}

function isUnauthorizedError(error: unknown): error is ApiRequestError {
  return error instanceof ApiRequestError && error.status === 401;
}

function buildAnonymousSession(): AuthSessionView {
  return {
    status: 'anonymous',
    actor: null,
    platform_role: 'anonymous',
    org_memberships: [],
    active_organisation_id: null,
    capabilities: [],
    data_mode: 'api',
  };
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = {
    'Content-Type': 'application/json',
    ...getAuthHeaders(),
    ...init?.headers,
  };

  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Network request failed';
    throw new ApiRequestError(message, { isNetworkError: true });
  }

  if (!res.ok) {
    if (res.status === 401) {
      const body = await res.json().catch(() => ({}));
      const isAuthAction = path === '/auth/login';
      const isLoginPage = window.location.pathname === '/login';
      if (!isLoginPage && !isAuthAction) {
        window.location.href = '/login';
      }
      throw new ApiRequestError(body?.error?.message ?? 'Session expired', { status: 401 });
    }
    const body = await res.json().catch(() => ({}));
    const details = body?.error?.details;
    const validationErrors = Array.isArray(details?.errors) ? details.errors : null;
    const firstValidationError = validationErrors?.[0];
    const validationSuffix =
      firstValidationError && typeof firstValidationError === 'object'
        ? ` (${String(firstValidationError.loc?.join?.('.') ?? 'request')}: ${String(firstValidationError.msg ?? 'invalid value')})`
        : '';
    throw new ApiRequestError(
      `${body?.error?.message ?? `API error ${res.status}`}${validationSuffix}`,
      { status: res.status }
    );
  }

  const envelope = await res.json();
  if (envelope.error) {
    const errorMessage = envelope.error?.message ?? envelope.error?.code ?? JSON.stringify(envelope.error);
    throw new ApiRequestError(errorMessage, { status: res.status });
  }
  if (envelope.status === 'error' || envelope.status === 'failed') {
    const errorMessage = envelope.errors?.[0]?.message ?? envelope.message ?? JSON.stringify(envelope);
    throw new ApiRequestError(errorMessage, { status: res.status });
  }
  return envelope.data as T;
}

export function setUserId(userId: string): void {
  sessionStorage.setItem(USER_ID_STORAGE_KEY, userId);
}

export function clearUserId(): void {
  sessionStorage.removeItem(USER_ID_STORAGE_KEY);
}

export function getUserId(): string | null {
  return sessionStorage.getItem(USER_ID_STORAGE_KEY);
}

function buildWebSocketUrl(path: string): string {
  if (API_BASE.startsWith('http://') || API_BASE.startsWith('https://')) {
    const base = new URL(API_BASE);
    base.protocol = base.protocol === 'https:' ? 'wss:' : 'ws:';
    base.pathname = `${base.pathname.replace(/\/$/, '')}${path}`;
    base.search = '';
    base.hash = '';
    return base.toString();
  }

  const url = new URL(`${API_BASE}${path}`, window.location.origin);
  url.protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return url.toString();
}

function deriveSessionFromUser(user: UserView): AuthSessionView {
  const storedActiveOrgId = getStoredActiveOrganisation();
  const platformRole = user.role === 'superadmin'
    ? 'superadmin'
    : user.role === 'admin'
      ? 'admin'
      : 'learner';
  const orgMemberships = user.org_memberships ?? [];
  const activeOrganisationId = storedActiveOrgId ?? orgMemberships[0]?.organisation_id ?? null;
  const hasOrgAdmin = orgMemberships.some((m) => m.role === 'admin');
  const capabilities: AuthSessionView['capabilities'] =
    platformRole === 'learner' && !hasOrgAdmin
      ? ['app:access']
      : ['app:access', 'admin:access'];

  return {
    status: 'authenticated',
    actor: user,
    platform_role: platformRole,
    org_memberships: orgMemberships,
    active_organisation_id: activeOrganisationId,
    capabilities,
    data_mode: 'api',
  };
}

type ProgressDashboardApiView = {
  snapshot: {
    competency_states: Array<{
      competency_slug: string;
      score: number;
      confidence_band: string;
    }>;
    skill_states: Array<{
      skill_slug: string;
      score: number;
      evidence_count: number;
      delta: number;
    }>;
  };
};

function mapConfidenceBand(value: string): 'low' | 'medium' | 'high' {
  if (value === 'high' || value === 'medium' || value === 'low') {
    return value;
  }
  return 'low';
}

function mapTrend(delta: number): 'up' | 'down' | 'stable' {
  if (delta > 0) return 'up';
  if (delta < 0) return 'down';
  return 'stable';
}

function mapCompetencyProgress(
  dashboard: ProgressDashboardApiView,
  taxonomy: TaxonomySnapshot,
): CompetencyProgressView[] {
  return dashboard.snapshot.competency_states.map((competencyState) => {
    const competency = taxonomy.competencies.find(
      (item) => item.slug === competencyState.competency_slug,
    );
    const skillViews = dashboard.snapshot.skill_states
      .filter((skillState) => {
        const linkedCompetency = taxonomy.competencies.find(
          (item) => item.slug === competencyState.competency_slug,
        );
        return linkedCompetency?.skills?.some((skill) => skill.slug === skillState.skill_slug) ?? false;
      })
      .map((skillState) => {
        const skill = taxonomy.skills.find((item) => item.slug === skillState.skill_slug);
        return {
          slug: skillState.skill_slug,
          name: skill?.name ?? skillState.skill_slug,
          score: Math.round(skillState.score),
          evidence_count: skillState.evidence_count,
          trend: mapTrend(skillState.delta),
        };
      });

    return {
      slug: competencyState.competency_slug,
      name: competency?.name ?? competencyState.competency_slug,
      description: competency?.description ?? '',
      skills: skillViews,
      overall_score: Math.round(competencyState.score),
      confidence: mapConfidenceBand(competencyState.confidence_band),
    };
  });
}

export const apiDataProvider: DataProvider = {
  // --- Auth / Identity -----------------------------------------------------
  getAuthSession: async () => {
    try {
      return deriveSessionFromUser(await request<UserView>('/users/me'));
    } catch (error) {
      if (isUnauthorizedError(error)) {
        clearStoredSession();
        return buildAnonymousSession();
      }
      throw error;
    }
  },
  setActiveOrganisation: async (organisationId) => {
    setStoredActiveOrganisationId(organisationId);
    try {
      return deriveSessionFromUser(await request<UserView>('/users/me'));
    } catch (error) {
      if (isUnauthorizedError(error)) {
        clearStoredSession();
        return buildAnonymousSession();
      }
      throw error;
    }
  },
  listAuthProfiles: async () => [],
  switchAuthProfile: async (_profileId) => {
    throw new ApiRequestError('Auth profile switching is only available in mock mode');
  },
  login: (cmd: LoginUserCommand) => {
    const result = request<UserView>('/auth/login', { method: 'POST', body: JSON.stringify(cmd) });
    result.then((user) => setUserId(user.id)).catch(() => {});
    return result;
  },
  register: (cmd) => {
    const result = request<UserView>('/auth/register', { method: 'POST', body: JSON.stringify(cmd) });
    result.then((user) => setUserId(user.id)).catch(() => {});
    return result;
  },
  getMe: () => request<UserView>('/users/me'),
  updateProfile: (cmd) => request<UserView>('/users/me/profile', { method: 'PATCH', body: JSON.stringify(cmd) }),
  deleteMe: () => {
    const result = request<DeleteAccountResult>('/users/me', { method: 'DELETE' });
    result.then(() => clearStoredSession()).catch(() => {});
    return result;
  },

  // --- Organisations --------------------------------------------------------
  createOrganisation: (cmd) =>
    request<import('./types').OrganisationView>('/organisations', { method: 'POST', body: JSON.stringify(cmd) }),
  listOrganisations: () =>
    request<import('./types').OrganisationListView[]>('/organisations'),

  // --- Taxonomy ------------------------------------------------------------
  getTaxonomy: () => request<TaxonomySnapshot>('/skills/catalog'),

  // --- Catalog -------------------------------------------------------------
  listCollections: (filters?: CollectionListFilters) => {
    const params = new URLSearchParams();
    if (filters?.difficulty) params.set('difficulty', filters.difficulty);
    if (filters?.skill_slug) params.set('skill_slug', filters.skill_slug);
    if (filters?.competency_slug) params.set('competency_slug', filters.competency_slug);
    if (filters?.include_private !== undefined) params.set('include_private', String(filters.include_private));
    if (filters?.saved_only) params.set('saved_only', 'true');
    if (filters?.discovery_tier) params.set('discovery_tier', filters.discovery_tier);
    if (filters?.author_user_id) params.set('author_user_id', filters.author_user_id);
    if (filters?.organisation_id) params.set('organisation_id', filters.organisation_id);
    const qs = params.toString();
    return request<CollectionView[]>(`/collections${qs ? `?${qs}` : ''}`);
  },
  getCollection: (id) => request<CollectionView>(`/collections/${id}`),
  createCollection: (cmd) => request<CollectionView>('/collections', { method: 'POST', body: JSON.stringify(cmd) }),
  addPromptItem: (collectionId, cmd) =>
    request<CollectionView>(`/collections/${collectionId}/prompt-items`, { method: 'POST', body: JSON.stringify(cmd) }),
  addScenario: (collectionId, cmd) =>
    request<CollectionView>(`/collections/${collectionId}/scenarios`, { method: 'POST', body: JSON.stringify(cmd) }),

  // --- Content Generation --------------------------------------------------
  generateStructuredCollection: (cmd) =>
    request<GenerationStartedView>('/collections/generate/structured', { method: 'POST', body: JSON.stringify(cmd) }),
  generateChatCollection: (cmd) =>
    request<GenerationStartedView>('/collections/generate/chat', { method: 'POST', body: JSON.stringify(cmd) }),
  streamGeneration: (streamToken, callbacks) => {
    const wsUrl = buildWebSocketUrl(`/ws/generation/${encodeURIComponent(streamToken)}`);
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'pong') {
          return;
        }
        callbacks.onEvent?.(data);
        if (data.type === 'completed') {
          callbacks.onCompleted?.(data.payload ?? {});
        } else if (data.type === 'failed' || data.type === 'cancelled') {
          callbacks.onFailed?.(data.payload ?? {});
        }
      } catch (error) {
        callbacks.onError?.(error instanceof Error ? error.message : 'Failed to parse generation stream message');
      }
    };

    ws.onerror = () => {
      callbacks.onError?.('Generation websocket error');
    };

    ws.onclose = () => {
      callbacks.onClose?.();
    };

    return () => {
      ws.close();
    };
  },

  // --- Practice ------------------------------------------------------------
  startQuickPracticeSession: (cmd) =>
    request<QuickPracticeSessionView>('/attempts/quick-practice/sessions', { method: 'POST', body: JSON.stringify(cmd) }),
  submitAttempt: (attemptId, cmd) =>
    request<AttemptView>(`/attempts/${attemptId}/submit`, { method: 'POST', body: JSON.stringify(cmd) }),
  getAttempt: (attemptId) => request<any>(`/attempts/${attemptId}`).then((raw) => {
    const attempt = raw.data ?? raw;
    if (attempt.assessment) {
      // Map backend rationale to frontend summary
      if (attempt.assessment.rationale !== undefined && attempt.assessment.summary === undefined) {
        attempt.assessment.summary = attempt.assessment.rationale;
      }
      // Ensure per_skill_assessments is an array
      if (!attempt.assessment.per_skill_assessments) {
        attempt.assessment.per_skill_assessments = [];
      }
    }
    return attempt as AttemptView;
  }),

  // --- Interview (maps to same backend endpoint, returns PracticeSessionView) ---
  startInterviewSession: (promptItemId) =>
    request<InterviewSessionView>('/attempts/interview/sessions', { method: 'POST', body: JSON.stringify({ prompt_item_id: promptItemId }) }),
  submitInterviewTurn: (_sessionId, _cmd) => {
    throw new Error('submitInterviewTurn not yet implemented in backend - use mock provider');
  },

  // --- Scenario (maps to same backend endpoint, returns PracticeSessionView) ---
  startScenarioSession: (scenarioId) =>
    request<ScenarioSessionView>('/attempts/scenario/sessions', { method: 'POST', body: JSON.stringify({ scenario_id: scenarioId }) }),
  submitScenarioStep: (_sessionId, _cmd) => {
    throw new Error('submitScenarioStep not yet implemented in backend - use mock provider');
  },

  // --- Practice Runs (Aggregate) -------------------------------------------
  createPracticeRun: (cmd) => {
    const adapted = {
      items: cmd.selected_items.map((item) => {
        if (item.item_type === 'scenario') {
          return { practice_type: 'scenario', scenario_id: item.item_id };
        }
        if (item.item_type === 'prompt_item' && item.prompt_type) {
          const practiceType = item.prompt_type === 'interview_prompt' ? 'interview' : 'quick_practice';
          return { practice_type: practiceType, prompt_item_id: item.item_id };
        }
        return { practice_type: 'quick_practice', prompt_item_id: item.item_id };
      }),
    };
    return request<PracticeRunView>('/practice-runs', { method: 'POST', body: JSON.stringify(adapted) });
  },
  listPracticeRuns: () =>
    request<any[]>('/practice-runs').then((runs) =>
      runs.map((raw) => ({
        run_id: raw.run_id,
        workflow_id: raw.workflow_id,
        status: raw.status,
        total_items: raw.total_items,
        completed_items: raw.completed_items,
        validated_items: raw.validated_items,
        failed_items: raw.failed_items,
        current_attempt_id: null,
        started_at: raw.started_at,
        completed_at: raw.completed_at,
        overall_score: raw.overall_score_average ?? null,
        items: [], // Items loaded separately via getPracticeRun
        summary: {
          total_items: raw.total_items,
          completed_items: raw.completed_items,
          overall_score: raw.overall_score_average ?? null,
          score_distribution: {},
          skill_breakdown: {},
          practice_type_breakdown: {},
        },
      })) as PracticeRunView[]
    ),
  getPracticeRun: (runId) =>
    request<any>(`/practice-runs/${runId}`).then((raw) => {
      return {
        run_id: raw.run_id,
        workflow_id: raw.workflow_id,
        status: raw.status,
        total_items: raw.total_items,
        completed_items: raw.completed_items,
        validated_items: raw.validated_items,
        failed_items: raw.failed_items,
        current_attempt_id: raw.current_attempt_id,
        started_at: raw.started_at,
        completed_at: raw.completed_at,
        items: (raw.items ?? []).map((item: any) => ({
          id: item.attempt?.id ?? item.attempt?.prompt?.content_item_id ?? '',
          item_type: item.attempt?.prompt?.content_item_type === 'quick_practice_prompt' || item.attempt?.prompt?.content_item_type === 'interview_prompt' ? 'prompt_item' : 'scenario',
          title: item.attempt?.prompt?.title ?? '',
          prompt_text: item.attempt?.prompt?.prompt_text ?? '',
          difficulty: item.attempt?.prompt?.difficulty ?? 'intermediate',
          target_skill_slugs: item.attempt?.prompt?.target_skill_slugs ?? [],
          status: item.attempt?.status ?? 'pending',
        })),
        summary: {
          total_items: raw.total_items,
          completed_items: raw.completed_items,
          overall_score: raw.summary?.overall_score_average ?? null,
          score_distribution: raw.summary?.score_distribution ?? {},
          skill_breakdown: raw.summary?.skill_breakdown ?? {},
          practice_type_breakdown: raw.summary?.practice_type_breakdown ?? {},
        },
      } as PracticeRunView;
    }),
  getPracticeSessions: (runId) =>
    request<any[]>(`/practice-runs/${runId}/sessions`).then((raw) =>
      raw.map((s: any) => ({
        id: s.id,
        practice_run_id: s.practice_run_id,
        sequence_index: s.sequence_index,
        content_item_id: s.content_item_id,
        content_item_type: s.content_item_type === 'scenario_step' ? 'scenario' : 'prompt_item',
        attempt_id: s.last_attempt_id,
        status: s.status,
        score: null,
        started_at: s.created_at,
        completed_at: s.completed_at,
      })),
    ),

  // --- Progress -----------------------------------------------------------
  getCompetencyProgress: async () => {
    const [dashboard, taxonomy] = await Promise.all([
      request<ProgressDashboardApiView>('/progress/me'),
      request<TaxonomySnapshot>('/skills/catalog'),
    ]);
    return mapCompetencyProgress(dashboard, taxonomy);
  },
  getAttemptHistory: () => request<AttemptHistoryItem[]>('/attempts/history'),
  getProgressHistory: (params) => {
    const searchParams = new URLSearchParams();
    if (params?.from_date) searchParams.set('from_date', params.from_date);
    if (params?.to_date) searchParams.set('to_date', params.to_date);
    if (params?.limit !== undefined) searchParams.set('limit', String(params.limit));
    const qs = searchParams.toString();
    return request<import('./types').ProgressHistory>(`/progress/me/history${qs ? `?${qs}` : ''}`);
  },
  getSkillTimeline: (skillSlug, params) => {
    const searchParams = new URLSearchParams();
    if (params?.from_date) searchParams.set('from_date', params.from_date);
    if (params?.to_date) searchParams.set('to_date', params.to_date);
    if (params?.limit !== undefined) searchParams.set('limit', String(params.limit));
    const qs = searchParams.toString();
    return request<import('./types').SkillTimeline>(`/progress/me/timeline/${encodeURIComponent(skillSlug)}${qs ? `?${qs}` : ''}`);
  },

  // --- Admin: Users & User Management ----------------------------------------
  listAdminUsers: (params) => {
    const searchParams = new URLSearchParams();
    if (params?.offset !== undefined) searchParams.set('offset', String(params.offset));
    if (params?.limit !== undefined) searchParams.set('limit', String(params.limit));
    if (params?.search) searchParams.set('search', params.search);
    if (params?.role) searchParams.set('role', params.role);
    if (params?.is_active !== undefined) searchParams.set('is_active', String(params.is_active));
    const qs = searchParams.toString();
    return request<AdminUserListView>(`/admin/users${qs ? `?${qs}` : ''}`);
  },
  getAdminUser: (userId) => request<AdminUserView | null>(`/admin/users/${userId}`),
  updateAdminUserRole: (userId, role) =>
    request<AdminUserView>(`/admin/users/${userId}/role`, { method: 'PUT', body: JSON.stringify({ role }) }),
  updateAdminUserStatus: (userId, isActive) =>
    request<AdminUserView>(`/admin/users/${userId}/status`, { method: 'PATCH', body: JSON.stringify({ is_active: isActive }) }),
  createAdminUser: (cmd) => request<AdminUserView>('/admin/users', { method: 'POST', body: JSON.stringify(cmd) }),
  bulkAdminUserOperation: (cmd) =>
    request<BulkOperationResultView>('/admin/users/bulk', { method: 'POST', body: JSON.stringify(cmd) }),
  getUserActivity: (userId) => request<UserActivityView>(`/admin/users/${userId}/activity`),

  // --- Admin: Learners & Relationships --------------------------------------
  getLearnerAnalytics: (learnerId, params) => {
    const searchParams = new URLSearchParams();
    if (params?.from_date) searchParams.set('from_date', params.from_date);
    if (params?.to_date) searchParams.set('to_date', params.to_date);
    const qs = searchParams.toString();
    return request<LearnerAnalyticsView>(`/admin/learners/${learnerId}/analytics${qs ? `?${qs}` : ''}`);
  },
  getLearnerRelationship: (learnerId) =>
    request<AdminLearnerRelationshipView | null>(`/admin/learners/${learnerId}/relationship`),
  upsertLearnerRelationship: (learnerId, relationshipType) =>
    request<AdminLearnerRelationshipView>(`/admin/learners/${learnerId}/relationship`, {
      method: 'PUT',
      body: JSON.stringify({ relationship_type: relationshipType }),
    }),
  deleteLearnerRelationship: (learnerId) =>
    request<{ status: string }>(`/admin/learners/${learnerId}/relationship`, { method: 'DELETE' }),

  // --- Admin: Analytics Overview ---------------------------------------------
  getAnalyticsOverview: (params) => {
    const searchParams = new URLSearchParams();
    if (params?.from_date) searchParams.set('from_date', params.from_date);
    if (params?.to_date) searchParams.set('to_date', params.to_date);
    const qs = searchParams.toString();
    return request<AnalyticsOverviewView>(`/admin/analytics/overview${qs ? `?${qs}` : ''}`);
  },
  getCohortAnalytics: (params) => {
    const searchParams = new URLSearchParams();
    if (params?.target_role) searchParams.set('target_role', params.target_role);
    if (params?.from_date) searchParams.set('from_date', params.from_date);
    if (params?.to_date) searchParams.set('to_date', params.to_date);
    const qs = searchParams.toString();
    return request<CohortAnalyticsView>(`/admin/cohorts/analytics${qs ? `?${qs}` : ''}`);
  },
  getCohortsComparison: (params) => {
    const searchParams = new URLSearchParams();
    if (params.cohort_keys) searchParams.set('cohort_keys', params.cohort_keys);
    if (params?.from_date) searchParams.set('from_date', params.from_date);
    if (params?.to_date) searchParams.set('to_date', params.to_date);
    const qs = searchParams.toString();
    return request<CohortComparisonView>(`/admin/cohorts/comparison${qs ? `?${qs}` : ''}`);
  },

  // --- Admin: Collections & Verification -----------------------------------
  getVerificationQueue: () => request<CollectionVerificationQueueItemView[]>('/admin/collections/verification-queue'),
  getCollectionVerification: (collectionId) =>
    request<CollectionVerificationAuditView>(`/admin/collections/${collectionId}/verification`),
  updateCollectionVerification: (collectionId, cmd) =>
    request<CollectionVerificationAuditView>(`/admin/collections/${collectionId}/verification`, {
      method: 'POST',
      body: JSON.stringify(cmd),
    }),
  updateCollectionFeature: (collectionId, featured) =>
    request<CollectionView>(`/admin/collections/${collectionId}/feature`, {
      method: 'PATCH',
      body: JSON.stringify({ featured }),
    }),

  // --- Admin: Evaluation Dashboard -------------------------------------------
  listEvalSuites: () => request<EvaluationSuiteView[]>('/admin/evaluations/suites'),
  listEvalRuns: (params) => {
    const searchParams = new URLSearchParams();
    if (params?.limit !== undefined) searchParams.set('limit', String(params.limit));
    const qs = searchParams.toString();
    return request<EvaluationRunView[]>(`/admin/evaluations/runs${qs ? `?${qs}` : ''}`);
  },
  getEvalRun: (runId) => request<EvaluationRunView>(`/admin/evaluations/runs/${runId}`),
  triggerEvalRun: (cmd) =>
    request<EvaluationRunView>('/admin/evaluations/runs', { method: 'POST', body: JSON.stringify(cmd) }),
  getEvalDashboard: (params) => {
    const searchParams = new URLSearchParams();
    if (params?.from_date) searchParams.set('from_date', params.from_date);
    if (params?.to_date) searchParams.set('to_date', params.to_date);
    const qs = searchParams.toString();
    return request<EvaluationDashboardView>(`/admin/evaluations/dashboard${qs ? `?${qs}` : ''}`);
  },
  getEvalRunsComparison: (params) => {
    const searchParams = new URLSearchParams();
    if (params.run_ids) searchParams.set('run_ids', params.run_ids);
    if (params?.from_date) searchParams.set('from_date', params.from_date);
    if (params?.to_date) searchParams.set('to_date', params.to_date);
    const qs = searchParams.toString();
    return request<EvaluationComparisonView>(`/admin/evaluations/runs/compare${qs ? `?${qs}` : ''}`);
  },
  getEvalBenchmark: (params) => {
    const searchParams = new URLSearchParams();
    if (params?.from_date) searchParams.set('from_date', params.from_date);
    if (params?.to_date) searchParams.set('to_date', params.to_date);
    const qs = searchParams.toString();
    return request<BenchmarkDashboardView>(`/admin/evaluations/benchmark${qs ? `?${qs}` : ''}`);
  },
  getEvalCaseDetail: (caseId) => request<EvaluationCaseDetailView>(`/admin/evaluations/cases/${caseId}`),

  // --- Admin: Providers --------------------------------------------------------
  listOpenRouterModels: () => request<ProviderModel[]>('/providers/openrouter/models'),

  // --- Admin: Prompts --------------------------------------------------------
  listPrompts: () => request<PromptSummaryView[]>('/admin/prompts'),
  listPromptVersions: (name) => request<PromptVersionView[]>(`/admin/prompts/${encodeURIComponent(name)}/versions`),
  getPromptVersion: (name, version) =>
    request<PromptVersionView>(`/admin/prompts/${encodeURIComponent(name)}/versions/${encodeURIComponent(version)}`),
  createPrompt: (cmd) => request<PromptVersionView>('/admin/prompts', { method: 'POST', body: JSON.stringify(cmd) }),
  updatePrompt: (name, version, cmd) =>
    request<PromptVersionView>(`/admin/prompts/${encodeURIComponent(name)}/versions/${encodeURIComponent(version)}`, {
      method: 'PUT',
      body: JSON.stringify(cmd),
    }),
  publishPrompt: (name, version) =>
    request<PromptVersionView>(`/admin/prompts/${encodeURIComponent(name)}/versions/${encodeURIComponent(version)}/publish`, {
      method: 'POST',
      body: JSON.stringify({}),
    }),
  archivePrompt: (name, version) =>
    request<PromptVersionView>(`/admin/prompts/${encodeURIComponent(name)}/versions/${encodeURIComponent(version)}/archive`, {
      method: 'POST',
      body: JSON.stringify({}),
    }),
  getPromptAnalytics: (name, version) =>
    request<PromptAnalyticsView>(`/admin/prompts/${encodeURIComponent(name)}/versions/${encodeURIComponent(version)}/analytics`),
  comparePrompts: (cmd) => request<PromptCompareView>('/admin/prompts/compare', { method: 'POST', body: JSON.stringify(cmd) }),

  // --- Admin: Pipelines ------------------------------------------------------
  listPipelines: () => request<PipelineDefinitionView[]>('/admin/pipelines'),
  getPipelineDAG: (pipelineName) => request<PipelineDAGView>(`/admin/pipelines/${encodeURIComponent(pipelineName)}`),
  listPipelineRuns: (pipelineName, params) => {
    const searchParams = new URLSearchParams();
    if (params?.offset !== undefined) searchParams.set('offset', String(params.offset));
    if (params?.limit !== undefined) searchParams.set('limit', String(params.limit));
    const qs = searchParams.toString();
    return request<PipelineRunSummaryView[]>(`/admin/pipelines/${encodeURIComponent(pipelineName)}/runs${qs ? `?${qs}` : ''}`);
  },
  getPipelineTrace: (pipelineName, pipelineRunId) =>
    request<PipelineTraceView>(`/admin/pipelines/${encodeURIComponent(pipelineName)}/runs/${encodeURIComponent(pipelineRunId)}/trace`),
  getPipelineMetrics: (pipelineName) =>
    request<PipelineMetricsView>(`/admin/pipelines/${encodeURIComponent(pipelineName)}/metrics`),

  // --- Admin: Rubrics --------------------------------------------------------
  listRubrics: () => request<RubricView[]>('/admin/rubrics'),
  getRubric: (rubricId) => request<RubricView>(`/admin/rubrics/${encodeURIComponent(rubricId)}`),
  createRubric: (cmd) => request<RubricView>('/admin/rubrics', { method: 'POST', body: JSON.stringify(cmd) }),
  updateRubric: (rubricId, cmd) =>
    request<RubricView>(`/admin/rubrics/${encodeURIComponent(rubricId)}`, { method: 'PATCH', body: JSON.stringify(cmd) }),
  deleteRubric: (rubricId) =>
    request<{ status: string }>(`/admin/rubrics/${encodeURIComponent(rubricId)}`, { method: 'DELETE' }),
  addRubricCriterion: (rubricId, criterion) =>
    request<RubricView>(`/admin/rubrics/${encodeURIComponent(rubricId)}/criteria`, {
      method: 'POST',
      body: JSON.stringify(criterion),
    }),
  updateRubricCriterion: (rubricId, criterionRef, criterion) =>
    request<RubricView>(`/admin/rubrics/${encodeURIComponent(rubricId)}/criteria/${encodeURIComponent(criterionRef)}`, {
      method: 'PATCH',
      body: JSON.stringify(criterion),
    }),
  deleteRubricCriterion: (rubricId, criterionRef) =>
    request<RubricView>(`/admin/rubrics/${encodeURIComponent(rubricId)}/criteria/${encodeURIComponent(criterionRef)}`, {
      method: 'DELETE',
    }),

  // --- Admin: Org-scoped Skills ------------------------------------------------
  listOrgSkills: (orgId) =>
    request<OrgSkillView[]>(`/organisations/${encodeURIComponent(orgId)}/skills`),
  getOrgSkill: (orgId, skillSlug) =>
    request<OrgSkillView>(`/organisations/${encodeURIComponent(orgId)}/skills/${encodeURIComponent(skillSlug)}`),
  createOrgSkill: (orgId, cmd) =>
    request<OrgSkillView>(`/organisations/${encodeURIComponent(orgId)}/skills`, { method: 'POST', body: JSON.stringify(cmd) }),
  updateOrgSkill: (orgId, skillSlug, cmd) =>
    request<OrgSkillView>(`/organisations/${encodeURIComponent(orgId)}/skills/${encodeURIComponent(skillSlug)}`, { method: 'PATCH', body: JSON.stringify(cmd) }),
  deleteOrgSkill: (orgId, skillSlug) =>
    request<{ status: string }>(`/organisations/${encodeURIComponent(orgId)}/skills/${encodeURIComponent(skillSlug)}`, { method: 'DELETE' }),

  // --- Admin: Org-scoped Competencies -----------------------------------------
  listOrgCompetencies: (orgId) =>
    request<OrgCompetencyView[]>(`/organisations/${encodeURIComponent(orgId)}/competencies`),
  getOrgCompetency: (orgId, competencySlug) =>
    request<OrgCompetencyView>(`/organisations/${encodeURIComponent(orgId)}/competencies/${encodeURIComponent(competencySlug)}`),
  createOrgCompetency: (orgId, cmd) =>
    request<OrgCompetencyView>(`/organisations/${encodeURIComponent(orgId)}/competencies`, { method: 'POST', body: JSON.stringify(cmd) }),
  updateOrgCompetency: (orgId, competencySlug, cmd) =>
    request<OrgCompetencyView>(`/organisations/${encodeURIComponent(orgId)}/competencies/${encodeURIComponent(competencySlug)}`, { method: 'PATCH', body: JSON.stringify(cmd) }),
  deleteOrgCompetency: (orgId, competencySlug) =>
    request<{ status: string }>(`/organisations/${encodeURIComponent(orgId)}/competencies/${encodeURIComponent(competencySlug)}`, { method: 'DELETE' }),

  // --- Admin: Org-scoped Rubrics ----------------------------------------------
  listOrgRubrics: (orgId) =>
    request<OrgRubricView[]>(`/organisations/${encodeURIComponent(orgId)}/rubrics`),
  getOrgRubric: (orgId, rubricId) =>
    request<OrgRubricView>(`/organisations/${encodeURIComponent(orgId)}/rubrics/${encodeURIComponent(rubricId)}`),
  createOrgRubric: (orgId, cmd) =>
    request<OrgRubricView>(`/organisations/${encodeURIComponent(orgId)}/rubrics`, { method: 'POST', body: JSON.stringify(cmd) }),
  updateOrgRubric: (orgId, rubricId, cmd) =>
    request<OrgRubricView>(`/organisations/${encodeURIComponent(orgId)}/rubrics/${encodeURIComponent(rubricId)}`, { method: 'PATCH', body: JSON.stringify(cmd) }),
  deleteOrgRubric: (orgId, rubricId) =>
    request<{ status: string }>(`/organisations/${encodeURIComponent(orgId)}/rubrics/${encodeURIComponent(rubricId)}`, { method: 'DELETE' }),

  // --- Admin: Org-scoped Prompt Items -----------------------------------------
  listOrgPromptItems: (orgId) =>
    request<PromptItemView[]>(`/organisations/${encodeURIComponent(orgId)}/prompt-items`),
  getOrgPromptItem: (orgId, promptItemId) =>
    request<PromptItemView>(`/organisations/${encodeURIComponent(orgId)}/prompt-items/${encodeURIComponent(promptItemId)}`),
  createOrgPromptItem: (orgId, cmd) =>
    request<PromptItemView>(`/organisations/${encodeURIComponent(orgId)}/prompt-items`, { method: 'POST', body: JSON.stringify(cmd) }),
  updateOrgPromptItem: (orgId, promptItemId, cmd) =>
    request<PromptItemView>(`/organisations/${encodeURIComponent(orgId)}/prompt-items/${encodeURIComponent(promptItemId)}`, { method: 'PATCH', body: JSON.stringify(cmd) }),
  deleteOrgPromptItem: (orgId, promptItemId) =>
    request<{ status: string }>(`/organisations/${encodeURIComponent(orgId)}/prompt-items/${encodeURIComponent(promptItemId)}`, { method: 'DELETE' }),

  // --- Admin: Org-scoped Scenarios -------------------------------------------
  listOrgScenarios: (orgId) =>
    request<ScenarioView[]>(`/organisations/${encodeURIComponent(orgId)}/scenarios`),
  getOrgScenario: (orgId, scenarioId) =>
    request<ScenarioView>(`/organisations/${encodeURIComponent(orgId)}/scenarios/${encodeURIComponent(scenarioId)}`),
  createOrgScenario: (orgId, cmd) =>
    request<ScenarioView>(`/organisations/${encodeURIComponent(orgId)}/scenarios`, { method: 'POST', body: JSON.stringify(cmd) }),
  updateOrgScenario: (orgId, scenarioId, cmd) =>
    request<ScenarioView>(`/organisations/${encodeURIComponent(orgId)}/scenarios/${encodeURIComponent(scenarioId)}`, { method: 'PATCH', body: JSON.stringify(cmd) }),
  deleteOrgScenario: (orgId, scenarioId) =>
    request<{ status: string }>(`/organisations/${encodeURIComponent(orgId)}/scenarios/${encodeURIComponent(scenarioId)}`, { method: 'DELETE' }),

  // --- Admin: Audit & Events -------------------------------------------------
  listWorkflowEvents: (params) => {
    const searchParams = new URLSearchParams();
    if (params?.event_type) searchParams.set('event_type', params.event_type);
    if (params?.trace_id) searchParams.set('trace_id', params.trace_id);
    if (params?.workflow_id) searchParams.set('workflow_id', params.workflow_id);
    if (params?.request_id) searchParams.set('request_id', params.request_id);
    if (params?.error_code) searchParams.set('error_code', params.error_code);
    if (params?.offset !== undefined) searchParams.set('offset', String(params.offset));
    if (params?.limit !== undefined) searchParams.set('limit', String(params.limit));
    const qs = searchParams.toString();
    return request<PaginatedWorkflowEventsView>(`/events${qs ? `?${qs}` : ''}`);
  },
  getWorkflowEvent: (eventId) => request<WorkflowEventView>(`/events/${encodeURIComponent(eventId)}`),
  updateWorkflowEvent: (eventId, cmd) =>
    request<WorkflowEventView>(`/events/${encodeURIComponent(eventId)}`, { method: 'PATCH', body: JSON.stringify(cmd) }),
  deleteWorkflowEvent: (eventId) =>
    request<{ status: string }>(`/events/${encodeURIComponent(eventId)}`, { method: 'DELETE' }),
  getAttemptAudit: (attemptId) => request<AttemptAuditView>(`/admin/attempts/${attemptId}/audit`),

  // --- Admin: Telemetry & Monitoring -----------------------------------------
  getTelemetryOverview: (params) => {
    const searchParams = new URLSearchParams();
    if (params?.organisation_id) searchParams.set('organisation_id', params.organisation_id);
    if (params?.from_date) searchParams.set('from_date', params.from_date);
    if (params?.to_date) searchParams.set('to_date', params.to_date);
    const qs = searchParams.toString();
    return request<TelemetryOverviewView>(`/admin/telemetry/overview${qs ? `?${qs}` : ''}`);
  },
  listTelemetryTraces: (params) => {
    const searchParams = new URLSearchParams();
    if (params?.organisation_id) searchParams.set('organisation_id', params.organisation_id);
    if (params?.from_date) searchParams.set('from_date', params.from_date);
    if (params?.to_date) searchParams.set('to_date', params.to_date);
    if (params?.offset !== undefined) searchParams.set('offset', String(params.offset));
    if (params?.limit !== undefined) searchParams.set('limit', String(params.limit));
    const qs = searchParams.toString();
    return request<TelemetryTraceListView>(`/admin/telemetry/traces${qs ? `?${qs}` : ''}`);
  },
  getTelemetryTrace: (traceId) => request<TelemetryTraceView | null>(`/admin/telemetry/traces/${encodeURIComponent(traceId)}`),

  // --- Assistant ------------------------------------------------------------
  createAssistantSession: (cmd) =>
    request<AssistantSessionView>('/assistant/sessions', {
      method: 'POST',
      body: JSON.stringify(cmd || {}),
    }),

  listAssistantSessions: () =>
    request<AssistantSessionView[]>('/assistant/sessions'),

  getAssistantSession: (sessionId) =>
    request<AssistantSessionView>(`/assistant/sessions/${encodeURIComponent(sessionId)}`),

  createAssistantTurn: (sessionId, cmd) =>
    request<AssistantTurnView>(`/assistant/sessions/${encodeURIComponent(sessionId)}/turns`, {
      method: 'POST',
      body: JSON.stringify(cmd),
    }),

  getAssistantTurn: (turnId) =>
    request<AssistantTurnView>(`/assistant/turns/${encodeURIComponent(turnId)}`),

  cancelAssistantTurn: (turnId, cmd) =>
    request<AssistantTurnView>(`/assistant/turns/${encodeURIComponent(turnId)}/cancel`, {
      method: 'POST',
      body: JSON.stringify(cmd || { reason: 'user_requested' }),
    }),

  streamAssistantTurn: (streamToken, callbacks) => {
    const wsUrl = buildWebSocketUrl(`/assistant/streams/${encodeURIComponent(streamToken)}`);
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('Assistant stream connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'tool.started' && callbacks.onToolStarted) {
          callbacks.onToolStarted(data.payload);
        } else if (data.type === 'tool.completed' && callbacks.onToolCompleted) {
          callbacks.onToolCompleted(data.payload);
        } else if (data.type === 'tool.failed' && callbacks.onToolFailed) {
          callbacks.onToolFailed(data.payload);
        } else if (data.type === 'turn.failed' && callbacks.onTurnFailed) {
          callbacks.onTurnFailed(data.payload);
        } else if (data.type === 'turn.completed' && callbacks.onTurnCompleted) {
          callbacks.onTurnCompleted();
        }
      } catch (error) {
        console.error('Error parsing assistant stream message:', error);
        if (callbacks.onError) {
          callbacks.onError('Failed to parse stream message');
        }
      }
    };

    ws.onerror = (error) => {
      console.error('Assistant stream error:', error);
      if (callbacks.onError) {
        callbacks.onError('WebSocket connection error');
      }
    };

    ws.onclose = () => {
      console.log('Assistant stream closed');
      if (callbacks.onClose) {
        callbacks.onClose();
      }
    };
    // Return cleanup function
    return () => {
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
    };
  },
};
