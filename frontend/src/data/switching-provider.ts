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
    if (!res.ok) {
      return false;
    }

    const contentType = res.headers.get('content-type') ?? '';
    if (!contentType.includes('application/json')) {
      return false;
    }

    const payload = await res.json() as { status?: string; ok?: boolean };
    return payload.status === 'ok' || payload.ok === true;
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
    } catch {
      this._useApi = false;
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

  // --- Assistant ------------------------------------------------------------
  createAssistantSession(cmd) {
    return this.withFallback(
      () => apiDataProvider.createAssistantSession(cmd),
      () => mockDataProvider.createAssistantSession(cmd),
    );
  }

  listAssistantSessions() {
    return this.withFallback(
      () => apiDataProvider.listAssistantSessions(),
      () => mockDataProvider.listAssistantSessions(),
    );
  }

  getAssistantSession(sessionId) {
    return this.withFallback(
      () => apiDataProvider.getAssistantSession(sessionId),
      () => mockDataProvider.getAssistantSession(sessionId),
    );
  }

  createAssistantTurn(sessionId, cmd) {
    return this.withFallback(
      () => apiDataProvider.createAssistantTurn(sessionId, cmd),
      () => mockDataProvider.createAssistantTurn(sessionId, cmd),
    );
  }

  getAssistantTurn(turnId) {
    return this.withFallback(
      () => apiDataProvider.getAssistantTurn(turnId),
      () => mockDataProvider.getAssistantTurn(turnId),
    );
  }

  cancelAssistantTurn(turnId, cmd) {
    return this.withFallback(
      () => apiDataProvider.cancelAssistantTurn(turnId, cmd),
      () => mockDataProvider.cancelAssistantTurn(turnId, cmd),
    );
  }

  streamAssistantTurn(streamToken, callbacks) {
    if (!this._useApi) {
      return mockDataProvider.streamAssistantTurn(streamToken, callbacks);
    }

    let mockCleanup: (() => void) | null = null;
    let hasFallenBack = false;

    const apiCleanup = apiDataProvider.streamAssistantTurn(streamToken, {
      ...callbacks,
      onError: (error) => {
        if (hasFallenBack) {
          callbacks.onError?.(error);
          return;
        }

        hasFallenBack = true;
        this._useApi = false;

        try {
          mockCleanup = mockDataProvider.streamAssistantTurn(streamToken, callbacks);
        } catch {
          callbacks.onError?.(error);
        }
      },
    });

    return () => {
      apiCleanup();
      mockCleanup?.();
    };
  }

  // --- Admin: Users & User Management ----------------------------------------
  listAdminUsers(params) {
    return this.withFallback(
      () => apiDataProvider.listAdminUsers(params),
      () => mockDataProvider.listAdminUsers(params),
    );
  }

  getAdminUser(userId) {
    return this.withFallback(
      () => apiDataProvider.getAdminUser(userId),
      () => mockDataProvider.getAdminUser(userId),
    );
  }

  updateAdminUserRole(userId, role) {
    return this.withFallback(
      () => apiDataProvider.updateAdminUserRole(userId, role),
      () => mockDataProvider.updateAdminUserRole(userId, role),
    );
  }

  updateAdminUserStatus(userId, isActive) {
    return this.withFallback(
      () => apiDataProvider.updateAdminUserStatus(userId, isActive),
      () => mockDataProvider.updateAdminUserStatus(userId, isActive),
    );
  }

  createAdminUser(cmd) {
    return this.withFallback(
      () => apiDataProvider.createAdminUser(cmd),
      () => mockDataProvider.createAdminUser(cmd),
    );
  }

  bulkAdminUserOperation(cmd) {
    return this.withFallback(
      () => apiDataProvider.bulkAdminUserOperation(cmd),
      () => mockDataProvider.bulkAdminUserOperation(cmd),
    );
  }

  getUserActivity(userId) {
    return this.withFallback(
      () => apiDataProvider.getUserActivity(userId),
      () => mockDataProvider.getUserActivity(userId),
    );
  }

  // --- Admin: Learners & Relationships --------------------------------------
  getLearnerAnalytics(learnerId, params) {
    return this.withFallback(
      () => apiDataProvider.getLearnerAnalytics(learnerId, params),
      () => mockDataProvider.getLearnerAnalytics(learnerId, params),
    );
  }

  getLearnerRelationship(learnerId) {
    return this.withFallback(
      () => apiDataProvider.getLearnerRelationship(learnerId),
      () => mockDataProvider.getLearnerRelationship(learnerId),
    );
  }

  upsertLearnerRelationship(learnerId, relationshipType) {
    return this.withFallback(
      () => apiDataProvider.upsertLearnerRelationship(learnerId, relationshipType),
      () => mockDataProvider.upsertLearnerRelationship(learnerId, relationshipType),
    );
  }

  deleteLearnerRelationship(learnerId) {
    return this.withFallback(
      () => apiDataProvider.deleteLearnerRelationship(learnerId),
      () => mockDataProvider.deleteLearnerRelationship(learnerId),
    );
  }

  // --- Admin: Analytics Overview ---------------------------------------------
  getAnalyticsOverview(params) {
    return this.withFallback(
      () => apiDataProvider.getAnalyticsOverview(params),
      () => mockDataProvider.getAnalyticsOverview(params),
    );
  }

  getCohortAnalytics(params) {
    return this.withFallback(
      () => apiDataProvider.getCohortAnalytics(params),
      () => mockDataProvider.getCohortAnalytics(params),
    );
  }

  getCohortsComparison(params) {
    return this.withFallback(
      () => apiDataProvider.getCohortsComparison(params),
      () => mockDataProvider.getCohortsComparison(params),
    );
  }

  // --- Admin: Collections & Verification -----------------------------------
  getVerificationQueue() {
    return this.withFallback(
      () => apiDataProvider.getVerificationQueue(),
      () => mockDataProvider.getVerificationQueue(),
    );
  }

  getCollectionVerification(collectionId) {
    return this.withFallback(
      () => apiDataProvider.getCollectionVerification(collectionId),
      () => mockDataProvider.getCollectionVerification(collectionId),
    );
  }

  updateCollectionVerification(collectionId, cmd) {
    return this.withFallback(
      () => apiDataProvider.updateCollectionVerification(collectionId, cmd),
      () => mockDataProvider.updateCollectionVerification(collectionId, cmd),
    );
  }

  updateCollectionFeature(collectionId, featured) {
    return this.withFallback(
      () => apiDataProvider.updateCollectionFeature(collectionId, featured),
      () => mockDataProvider.updateCollectionFeature(collectionId, featured),
    );
  }

  // --- Admin: Evaluation Dashboard -------------------------------------------
  listEvalSuites() {
    return this.withFallback(
      () => apiDataProvider.listEvalSuites(),
      () => mockDataProvider.listEvalSuites(),
    );
  }

  listEvalRuns(params) {
    return this.withFallback(
      () => apiDataProvider.listEvalRuns(params),
      () => mockDataProvider.listEvalRuns(params),
    );
  }

  getEvalRun(runId) {
    return this.withFallback(
      () => apiDataProvider.getEvalRun(runId),
      () => mockDataProvider.getEvalRun(runId),
    );
  }

  triggerEvalRun(cmd) {
    return this.withFallback(
      () => apiDataProvider.triggerEvalRun(cmd),
      () => mockDataProvider.triggerEvalRun(cmd),
    );
  }

  getEvalDashboard(params) {
    return this.withFallback(
      () => apiDataProvider.getEvalDashboard(params),
      () => mockDataProvider.getEvalDashboard(params),
    );
  }

  getEvalRunsComparison(params) {
    return this.withFallback(
      () => apiDataProvider.getEvalRunsComparison(params),
      () => mockDataProvider.getEvalRunsComparison(params),
    );
  }

  getEvalBenchmark(params) {
    return this.withFallback(
      () => apiDataProvider.getEvalBenchmark(params),
      () => mockDataProvider.getEvalBenchmark(params),
    );
  }

  getEvalCaseDetail(caseId) {
    return this.withFallback(
      () => apiDataProvider.getEvalCaseDetail(caseId),
      () => mockDataProvider.getEvalCaseDetail(caseId),
    );
  }

  // --- Admin: Prompts --------------------------------------------------------
  listPrompts() {
    return this.withFallback(
      () => apiDataProvider.listPrompts(),
      () => mockDataProvider.listPrompts(),
    );
  }

  listPromptVersions(name) {
    return this.withFallback(
      () => apiDataProvider.listPromptVersions(name),
      () => mockDataProvider.listPromptVersions(name),
    );
  }

  getPromptVersion(name, version) {
    return this.withFallback(
      () => apiDataProvider.getPromptVersion(name, version),
      () => mockDataProvider.getPromptVersion(name, version),
    );
  }

  createPrompt(cmd) {
    return this.withFallback(
      () => apiDataProvider.createPrompt(cmd),
      () => mockDataProvider.createPrompt(cmd),
    );
  }

  updatePrompt(name, version, cmd) {
    return this.withFallback(
      () => apiDataProvider.updatePrompt(name, version, cmd),
      () => mockDataProvider.updatePrompt(name, version, cmd),
    );
  }

  publishPrompt(name, version) {
    return this.withFallback(
      () => apiDataProvider.publishPrompt(name, version),
      () => mockDataProvider.publishPrompt(name, version),
    );
  }

  archivePrompt(name, version) {
    return this.withFallback(
      () => apiDataProvider.archivePrompt(name, version),
      () => mockDataProvider.archivePrompt(name, version),
    );
  }

  getPromptAnalytics(name, version) {
    return this.withFallback(
      () => apiDataProvider.getPromptAnalytics(name, version),
      () => mockDataProvider.getPromptAnalytics(name, version),
    );
  }

  comparePrompts(cmd) {
    return this.withFallback(
      () => apiDataProvider.comparePrompts(cmd),
      () => mockDataProvider.comparePrompts(cmd),
    );
  }

  // --- Admin: Pipelines ------------------------------------------------------
  listPipelines() {
    return this.withFallback(
      () => apiDataProvider.listPipelines(),
      () => mockDataProvider.listPipelines(),
    );
  }

  getPipelineDAG(pipelineName) {
    return this.withFallback(
      () => apiDataProvider.getPipelineDAG(pipelineName),
      () => mockDataProvider.getPipelineDAG(pipelineName),
    );
  }

  listPipelineRuns(pipelineName, params) {
    return this.withFallback(
      () => apiDataProvider.listPipelineRuns(pipelineName, params),
      () => mockDataProvider.listPipelineRuns(pipelineName, params),
    );
  }

  getPipelineTrace(pipelineName, pipelineRunId) {
    return this.withFallback(
      () => apiDataProvider.getPipelineTrace(pipelineName, pipelineRunId),
      () => mockDataProvider.getPipelineTrace(pipelineName, pipelineRunId),
    );
  }

  getPipelineMetrics(pipelineName) {
    return this.withFallback(
      () => apiDataProvider.getPipelineMetrics(pipelineName),
      () => mockDataProvider.getPipelineMetrics(pipelineName),
    );
  }

  // --- Admin: Rubrics --------------------------------------------------------
  listRubrics() {
    return this.withFallback(
      () => apiDataProvider.listRubrics(),
      () => mockDataProvider.listRubrics(),
    );
  }

  getRubric(rubricId) {
    return this.withFallback(
      () => apiDataProvider.getRubric(rubricId),
      () => mockDataProvider.getRubric(rubricId),
    );
  }

  createRubric(cmd) {
    return this.withFallback(
      () => apiDataProvider.createRubric(cmd),
      () => mockDataProvider.createRubric(cmd),
    );
  }

  updateRubric(rubricId, cmd) {
    return this.withFallback(
      () => apiDataProvider.updateRubric(rubricId, cmd),
      () => mockDataProvider.updateRubric(rubricId, cmd),
    );
  }

  deleteRubric(rubricId) {
    return this.withFallback(
      () => apiDataProvider.deleteRubric(rubricId),
      () => mockDataProvider.deleteRubric(rubricId),
    );
  }

  addRubricCriterion(rubricId, criterion) {
    return this.withFallback(
      () => apiDataProvider.addRubricCriterion(rubricId, criterion),
      () => mockDataProvider.addRubricCriterion(rubricId, criterion),
    );
  }

  updateRubricCriterion(rubricId, criterionRef, criterion) {
    return this.withFallback(
      () => apiDataProvider.updateRubricCriterion(rubricId, criterionRef, criterion),
      () => mockDataProvider.updateRubricCriterion(rubricId, criterionRef, criterion),
    );
  }

  deleteRubricCriterion(rubricId, criterionRef) {
    return this.withFallback(
      () => apiDataProvider.deleteRubricCriterion(rubricId, criterionRef),
      () => mockDataProvider.deleteRubricCriterion(rubricId, criterionRef),
    );
  }

  // --- Admin: Audit & Events -------------------------------------------------
  listWorkflowEvents(params) {
    return this.withFallback(
      () => apiDataProvider.listWorkflowEvents(params),
      () => mockDataProvider.listWorkflowEvents(params),
    );
  }

  getWorkflowEvent(eventId) {
    return this.withFallback(
      () => apiDataProvider.getWorkflowEvent(eventId),
      () => mockDataProvider.getWorkflowEvent(eventId),
    );
  }

  updateWorkflowEvent(eventId, cmd) {
    return this.withFallback(
      () => apiDataProvider.updateWorkflowEvent(eventId, cmd),
      () => mockDataProvider.updateWorkflowEvent(eventId, cmd),
    );
  }

  deleteWorkflowEvent(eventId) {
    return this.withFallback(
      () => apiDataProvider.deleteWorkflowEvent(eventId),
      () => mockDataProvider.deleteWorkflowEvent(eventId),
    );
  }

  getAttemptAudit(attemptId) {
    return this.withFallback(
      () => apiDataProvider.getAttemptAudit(attemptId),
      () => mockDataProvider.getAttemptAudit(attemptId),
    );
  }

  // --- Admin: Telemetry & Monitoring -----------------------------------------
  getTelemetryOverview(params) {
    return this.withFallback(
      () => apiDataProvider.getTelemetryOverview(params),
      () => mockDataProvider.getTelemetryOverview(params),
    );
  }

  listTelemetryTraces(params) {
    return this.withFallback(
      () => apiDataProvider.listTelemetryTraces(params),
      () => mockDataProvider.listTelemetryTraces(params),
    );
  }

  getTelemetryTrace(traceId) {
    return this.withFallback(
      () => apiDataProvider.getTelemetryTrace(traceId),
      () => mockDataProvider.getTelemetryTrace(traceId),
    );
  }

  // --- Admin: Org-scoped Skills ---------------------------------------------
  listOrgSkills(orgId) {
    return this.withFallback(
      () => apiDataProvider.listOrgSkills(orgId),
      () => mockDataProvider.listOrgSkills(orgId),
    );
  }

  getOrgSkill(orgId, skillId) {
    return this.withFallback(
      () => apiDataProvider.getOrgSkill(orgId, skillId),
      () => mockDataProvider.getOrgSkill(orgId, skillId),
    );
  }

  createOrgSkill(orgId, cmd) {
    return this.withFallback(
      () => apiDataProvider.createOrgSkill(orgId, cmd),
      () => mockDataProvider.createOrgSkill(orgId, cmd),
    );
  }

  updateOrgSkill(orgId, skillId, cmd) {
    return this.withFallback(
      () => apiDataProvider.updateOrgSkill(orgId, skillId, cmd),
      () => mockDataProvider.updateOrgSkill(orgId, skillId, cmd),
    );
  }

  deleteOrgSkill(orgId, skillId) {
    return this.withFallback(
      () => apiDataProvider.deleteOrgSkill(orgId, skillId),
      () => mockDataProvider.deleteOrgSkill(orgId, skillId),
    );
  }

  // --- Admin: Org-scoped Competencies ---------------------------------------
  listOrgCompetencies(orgId) {
    return this.withFallback(
      () => apiDataProvider.listOrgCompetencies(orgId),
      () => mockDataProvider.listOrgCompetencies(orgId),
    );
  }

  getOrgCompetency(orgId, competencyId) {
    return this.withFallback(
      () => apiDataProvider.getOrgCompetency(orgId, competencyId),
      () => mockDataProvider.getOrgCompetency(orgId, competencyId),
    );
  }

  createOrgCompetency(orgId, cmd) {
    return this.withFallback(
      () => apiDataProvider.createOrgCompetency(orgId, cmd),
      () => mockDataProvider.createOrgCompetency(orgId, cmd),
    );
  }

  updateOrgCompetency(orgId, competencyId, cmd) {
    return this.withFallback(
      () => apiDataProvider.updateOrgCompetency(orgId, competencyId, cmd),
      () => mockDataProvider.updateOrgCompetency(orgId, competencyId, cmd),
    );
  }

  deleteOrgCompetency(orgId, competencyId) {
    return this.withFallback(
      () => apiDataProvider.deleteOrgCompetency(orgId, competencyId),
      () => mockDataProvider.deleteOrgCompetency(orgId, competencyId),
    );
  }

  // --- Admin: Org-scoped Rubrics --------------------------------------------
  listOrgRubrics(orgId) {
    return this.withFallback(
      () => apiDataProvider.listOrgRubrics(orgId),
      () => mockDataProvider.listOrgRubrics(orgId),
    );
  }

  getOrgRubric(orgId, rubricId) {
    return this.withFallback(
      () => apiDataProvider.getOrgRubric(orgId, rubricId),
      () => mockDataProvider.getOrgRubric(orgId, rubricId),
    );
  }

  createOrgRubric(orgId, cmd) {
    return this.withFallback(
      () => apiDataProvider.createOrgRubric(orgId, cmd),
      () => mockDataProvider.createOrgRubric(orgId, cmd),
    );
  }

  updateOrgRubric(orgId, rubricId, cmd) {
    return this.withFallback(
      () => apiDataProvider.updateOrgRubric(orgId, rubricId, cmd),
      () => mockDataProvider.updateOrgRubric(orgId, rubricId, cmd),
    );
  }

  deleteOrgRubric(orgId, rubricId) {
    return this.withFallback(
      () => apiDataProvider.deleteOrgRubric(orgId, rubricId),
      () => mockDataProvider.deleteOrgRubric(orgId, rubricId),
    );
  }

  // --- Admin: Org-scoped Prompt Items ---------------------------------------
  listOrgPromptItems(orgId) {
    return this.withFallback(
      () => apiDataProvider.listOrgPromptItems(orgId),
      () => mockDataProvider.listOrgPromptItems(orgId),
    );
  }

  getOrgPromptItem(orgId, promptItemId) {
    return this.withFallback(
      () => apiDataProvider.getOrgPromptItem(orgId, promptItemId),
      () => mockDataProvider.getOrgPromptItem(orgId, promptItemId),
    );
  }

  createOrgPromptItem(orgId, cmd) {
    return this.withFallback(
      () => apiDataProvider.createOrgPromptItem(orgId, cmd),
      () => mockDataProvider.createOrgPromptItem(orgId, cmd),
    );
  }

  updateOrgPromptItem(orgId, promptItemId, cmd) {
    return this.withFallback(
      () => apiDataProvider.updateOrgPromptItem(orgId, promptItemId, cmd),
      () => mockDataProvider.updateOrgPromptItem(orgId, promptItemId, cmd),
    );
  }

  deleteOrgPromptItem(orgId, promptItemId) {
    return this.withFallback(
      () => apiDataProvider.deleteOrgPromptItem(orgId, promptItemId),
      () => mockDataProvider.deleteOrgPromptItem(orgId, promptItemId),
    );
  }

  // --- Admin: Org-scoped Scenarios ------------------------------------------
  listOrgScenarios(orgId) {
    return this.withFallback(
      () => apiDataProvider.listOrgScenarios(orgId),
      () => mockDataProvider.listOrgScenarios(orgId),
    );
  }

  getOrgScenario(orgId, scenarioId) {
    return this.withFallback(
      () => apiDataProvider.getOrgScenario(orgId, scenarioId),
      () => mockDataProvider.getOrgScenario(orgId, scenarioId),
    );
  }

  createOrgScenario(orgId, cmd) {
    return this.withFallback(
      () => apiDataProvider.createOrgScenario(orgId, cmd),
      () => mockDataProvider.createOrgScenario(orgId, cmd),
    );
  }

  updateOrgScenario(orgId, scenarioId, cmd) {
    return this.withFallback(
      () => apiDataProvider.updateOrgScenario(orgId, scenarioId, cmd),
      () => mockDataProvider.updateOrgScenario(orgId, scenarioId, cmd),
    );
  }

  deleteOrgScenario(orgId, scenarioId) {
    return this.withFallback(
      () => apiDataProvider.deleteOrgScenario(orgId, scenarioId),
      () => mockDataProvider.deleteOrgScenario(orgId, scenarioId),
    );
  }
}

export const switchingDataProvider = new SwitchingDataProvider();