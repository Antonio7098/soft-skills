import type { DataProvider } from './provider';
import { mockDataProvider } from './mock-provider';
import { apiDataProvider } from './api-provider';

const API_BASE = import.meta.env.VITE_API_BASE ?? '/api';

let _userId: string | null = null;

export function setCurrentUserId(userId: string | null): void {
  _userId = userId;
}

export function getCurrentUserId(): string | null {
  return _userId;
}

async function isApiReachable(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/health/readiness`, {
      method: 'GET',
      signal: AbortSignal.timeout(3000),
    });
    return res.ok;
  } catch {
    return false;
  }
}

class SwitchingDataProvider implements DataProvider {
  private _useApi: boolean = false;
  private _apiChecked: boolean = false;

  private async ensureApi(): Promise<void> {
    if (this._apiChecked) return;
    this._apiChecked = true;
    this._useApi = await isApiReachable();
  }

  private async withFallback<T>(apiFn: () => Promise<T>, mockFn: () => Promise<T>): Promise<T> {
    await this.ensureApi();
    if (!this._useApi) return mockFn();

    try {
      return await apiFn();
    } catch (err) {
      console.warn('[SwitchingProvider] API call failed, falling back to mock:', err);
      return mockFn();
    }
  }

  isUsingApi(): boolean {
    return this._useApi;
  }

  // --- Auth / Identity -----------------------------------------------------
  register(cmd) {
    return this.withFallback(
      () => apiDataProvider.register(cmd),
      () => mockDataProvider.register(cmd),
    );
  }

  getMe() {
    return this.withFallback(
      () => apiDataProvider.getMe(),
      () => mockDataProvider.getMe(),
    );
  }

  updateProfile(cmd) {
    return this.withFallback(
      () => apiDataProvider.updateProfile(cmd),
      () => mockDataProvider.updateProfile(cmd),
    );
  }

  // --- Taxonomy ------------------------------------------------------------
  getTaxonomy() {
    return this.withFallback(
      () => apiDataProvider.getTaxonomy(),
      () => mockDataProvider.getTaxonomy(),
    );
  }

  // --- Catalog -------------------------------------------------------------
  listCollections(filters) {
    return this.withFallback(
      () => apiDataProvider.listCollections(filters),
      () => mockDataProvider.listCollections(filters),
    );
  }

  getCollection(id) {
    return this.withFallback(
      () => apiDataProvider.getCollection(id),
      () => mockDataProvider.getCollection(id),
    );
  }

  createCollection(cmd) {
    return this.withFallback(
      () => apiDataProvider.createCollection(cmd),
      () => mockDataProvider.createCollection(cmd),
    );
  }

  addPromptItem(collectionId, cmd) {
    return this.withFallback(
      () => apiDataProvider.addPromptItem(collectionId, cmd),
      () => mockDataProvider.addPromptItem(collectionId, cmd),
    );
  }

  addScenario(collectionId, cmd) {
    return this.withFallback(
      () => apiDataProvider.addScenario(collectionId, cmd),
      () => mockDataProvider.addScenario(collectionId, cmd),
    );
  }

  // --- Content Generation --------------------------------------------------
  generateStructuredCollection(cmd) {
    return this.withFallback(
      () => apiDataProvider.generateStructuredCollection(cmd),
      () => mockDataProvider.generateStructuredCollection(cmd),
    );
  }

  generateChatCollection(cmd) {
    return this.withFallback(
      () => apiDataProvider.generateChatCollection(cmd),
      () => mockDataProvider.generateChatCollection(cmd),
    );
  }

  // --- Practice ------------------------------------------------------------
  startQuickPracticeSession(cmd) {
    return this.withFallback(
      () => apiDataProvider.startQuickPracticeSession(cmd),
      () => mockDataProvider.startQuickPracticeSession(cmd),
    );
  }

  submitAttempt(attemptId, cmd) {
    return this.withFallback(
      () => apiDataProvider.submitAttempt(attemptId, cmd),
      () => mockDataProvider.submitAttempt(attemptId, cmd),
    );
  }

  getAttempt(attemptId) {
    return this.withFallback(
      () => apiDataProvider.getAttempt(attemptId),
      () => mockDataProvider.getAttempt(attemptId),
    );
  }

  // --- Interview -----------------------------------------------------------
  startInterviewSession(promptItemId) {
    return this.withFallback(
      () => apiDataProvider.startInterviewSession(promptItemId),
      () => mockDataProvider.startInterviewSession(promptItemId),
    );
  }

  submitInterviewTurn(sessionId, cmd) {
    return this.withFallback(
      () => apiDataProvider.submitInterviewTurn(sessionId, cmd),
      () => mockDataProvider.submitInterviewTurn(sessionId, cmd),
    );
  }

  // --- Scenario ------------------------------------------------------------
  startScenarioSession(scenarioId) {
    return this.withFallback(
      () => apiDataProvider.startScenarioSession(scenarioId),
      () => mockDataProvider.startScenarioSession(scenarioId),
    );
  }

  submitScenarioStep(sessionId, cmd) {
    return this.withFallback(
      () => apiDataProvider.submitScenarioStep(sessionId, cmd),
      () => mockDataProvider.submitScenarioStep(sessionId, cmd),
    );
  }

  // --- Practice Runs (Aggregate) -------------------------------------------
  createPracticeRun(cmd) {
    return this.withFallback(
      () => apiDataProvider.createPracticeRun(cmd),
      () => mockDataProvider.createPracticeRun(cmd),
    );
  }

  listPracticeRuns() {
    return this.withFallback(
      () => apiDataProvider.listPracticeRuns(),
      () => mockDataProvider.listPracticeRuns(),
    );
  }

  getPracticeRun(runId) {
    return this.withFallback(
      () => apiDataProvider.getPracticeRun(runId),
      () => mockDataProvider.getPracticeRun(runId),
    );
  }

  getPracticeSessions(runId) {
    return this.withFallback(
      () => apiDataProvider.getPracticeSessions(runId),
      () => mockDataProvider.getPracticeSessions(runId),
    );
  }

  // --- Progress -----------------------------------------------------------
  getCompetencyProgress(userId) {
    return this.withFallback(
      () => apiDataProvider.getCompetencyProgress(userId),
      () => mockDataProvider.getCompetencyProgress(userId),
    );
  }

  getAttemptHistory(userId) {
    return this.withFallback(
      () => apiDataProvider.getAttemptHistory(userId),
      () => mockDataProvider.getAttemptHistory(userId),
    );
  }
}

export const switchingDataProvider = new SwitchingDataProvider();