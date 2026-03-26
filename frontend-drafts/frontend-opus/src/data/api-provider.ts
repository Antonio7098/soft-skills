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
} from './types';

// ---------------------------------------------------------------------------
// ApiDataProvider — thin wrapper over the real backend REST API.
// All methods mirror the backend FastAPI routes.
// ---------------------------------------------------------------------------

const API_BASE = import.meta.env.VITE_API_BASE ?? '/api';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...init?.headers,
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.error?.message ?? `API error ${res.status}`);
  }

  const envelope = await res.json();
  return envelope.data as T;
}

export const apiDataProvider: DataProvider = {
  // --- Auth / Identity -----------------------------------------------------
  register: (cmd) => request<UserView>('/auth/register', { method: 'POST', body: JSON.stringify(cmd) }),
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
    const qs = params.toString();
    return request<CollectionView[]>(`/collections${qs ? `?${qs}` : ''}`);
  },
  getCollection: (id) => request<CollectionView>(`/collections/${id}`),
  createCollection: (cmd) => request<CollectionView>('/collections', { method: 'POST', body: JSON.stringify(cmd) }),
  addPromptItem: (collectionId, cmd) =>
    request<CollectionView>(`/collections/${collectionId}/prompt-items`, { method: 'POST', body: JSON.stringify(cmd) }),
  addScenario: (collectionId, cmd) =>
    request<CollectionView>(`/collections/${collectionId}/scenarios`, { method: 'POST', body: JSON.stringify(cmd) }),

  // --- Practice ------------------------------------------------------------
  startQuickPracticeSession: (cmd) =>
    request<QuickPracticeSessionView>('/attempts/quick-practice/sessions', { method: 'POST', body: JSON.stringify(cmd) }),
  submitAttempt: (attemptId, cmd) =>
    request<AttemptView>(`/attempts/${attemptId}/submit`, { method: 'POST', body: JSON.stringify(cmd) }),
  getAttempt: (attemptId) => request<AttemptView>(`/attempts/${attemptId}`),

  // --- Interview -----------------------------------------------------------
  startInterviewSession: (promptItemId) =>
    request<InterviewSessionView>('/attempts/interview/sessions', { method: 'POST', body: JSON.stringify({ prompt_item_id: promptItemId }) }),
  submitInterviewTurn: (sessionId, cmd) =>
    request<InterviewSessionView>(`/attempts/interview/sessions/${sessionId}/turns`, { method: 'POST', body: JSON.stringify(cmd) }),

  // --- Scenario ------------------------------------------------------------
  startScenarioSession: (scenarioId) =>
    request<ScenarioSessionView>('/attempts/scenario/sessions', { method: 'POST', body: JSON.stringify({ scenario_id: scenarioId }) }),
  submitScenarioStep: (sessionId, cmd) =>
    request<ScenarioSessionView>(`/attempts/scenario/sessions/${sessionId}/steps`, { method: 'POST', body: JSON.stringify(cmd) }),

  // --- Practice Runs (Aggregate) ---------------------------------------------
  createPracticeRun: (cmd) =>
    request<PracticeRunView>('/practice-runs', { method: 'POST', body: JSON.stringify(cmd) }),
  listPracticeRuns: () =>
    request<PracticeRunView[]>('/practice-runs'),
  getPracticeRun: (runId) =>
    request<PracticeRunView>(`/practice-runs/${runId}`),
  getPracticeSessions: (runId) =>
    request<PracticeSessionView[]>(`/practice-runs/${runId}/sessions`),

  // --- Progress (no backend endpoint yet — stub) ---------------------------
  getCompetencyProgress: async () => {
    throw new Error('Progress API not yet implemented');
  },
  getAttemptHistory: async () => {
    throw new Error('Attempt history API not yet implemented');
  },
};
