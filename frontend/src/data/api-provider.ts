import type { DataProvider } from './provider';
import type {
  UserView,
  TaxonomySnapshot,
  CollectionView,
  CollectionListFilters,
  QuickPracticeSessionView,
  AttemptView,
  InterviewSessionView,
  ScenarioSessionView,
  PracticeRunView,
  PracticeSessionView,
  CollectionGenerationView,
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
  AssistantSessionView,
  AssistantTurnView,
  CreateAssistantSessionCommand,
  CreateAssistantTurnCommand,
  CancelAssistantTurnCommand,
  AssistantStreamCallbacks,
} from './types';

const API_BASE = import.meta.env.VITE_API_BASE ?? '/api';

function getAuthHeaders(): Record<string, string> {
  const userId = sessionStorage.getItem('ss_user_id');
  if (!userId) return {};
  return { 'X-User-ID': userId };
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = {
    'Content-Type': 'application/json',
    ...getAuthHeaders(),
    ...init?.headers,
  };

  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.error?.message ?? `API error ${res.status}`);
  }

  const envelope = await res.json();
  return envelope.data as T;
}

export function setUserId(userId: string): void {
  sessionStorage.setItem('ss_user_id', userId);
}

export function clearUserId(): void {
  sessionStorage.removeItem('ss_user_id');
}

export function getUserId(): string | null {
  return sessionStorage.getItem('ss_user_id');
}

export const apiDataProvider: DataProvider = {
  // --- Auth / Identity -----------------------------------------------------
  register: (cmd) => {
    const result = request<UserView>('/auth/register', { method: 'POST', body: JSON.stringify(cmd) });
    result.then((user) => setUserId(user.id)).catch(() => {});
    return result;
  },
  getMe: () => request<UserView>('/users/me'),
  updateProfile: (cmd) => request<UserView>('/users/me/profile', { method: 'PATCH', body: JSON.stringify(cmd) }),

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
    request<CollectionGenerationView>('/collections/generate/structured', { method: 'POST', body: JSON.stringify(cmd) }),
  generateChatCollection: (cmd) =>
    request<CollectionGenerationView>('/collections/generate/chat', { method: 'POST', body: JSON.stringify(cmd) }),

  // --- Practice ------------------------------------------------------------
  startQuickPracticeSession: (cmd) =>
    request<QuickPracticeSessionView>('/attempts/quick-practice/sessions', { method: 'POST', body: JSON.stringify(cmd) }),
  submitAttempt: (attemptId, cmd) =>
    request<AttemptView>(`/attempts/${attemptId}/submit`, { method: 'POST', body: JSON.stringify(cmd) }),
  getAttempt: (attemptId) => request<AttemptView>(`/attempts/${attemptId}`),

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
      items: cmd.selected_items.map((item) => ({
        ...item,
        practice_type: item.item_type === 'prompt_item' ? 'quick_practice' : item.item_type,
      })),
    };
    return request<PracticeRunView>('/practice-runs', { method: 'POST', body: JSON.stringify(adapted) });
  },
  listPracticeRuns: () =>
    request<PracticeRunView[]>('/practice-runs'),
  getPracticeRun: (runId) =>
    request<PracticeRunView>(`/practice-runs/${runId}`),
  getPracticeSessions: (runId) =>
    request<PracticeSessionView[]>(`/practice-runs/${runId}/sessions`),

  // --- Progress -----------------------------------------------------------
  getCompetencyProgress: async () => {
    throw new Error('Progress API not yet implemented - use mock provider');
  },
  getAttemptHistory: async () => {
    throw new Error('Attempt history API not yet implemented - use mock provider');
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
    const wsUrl = `${API_BASE.replace('http', 'ws')}/assistant/streams/${encodeURIComponent(streamToken)}`;
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
        } else if (data.type === 'turn.completed' && callbacks.onTurnCompleted) {
          callbacks.onTurnCompleted(data.payload);
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

    // Handle control messages (like cancellation)
    const sendControlMessage = (type: string, reason?: string) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type, reason }));
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