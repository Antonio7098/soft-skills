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
};