// @ts-nocheck
import type { DataProvider } from './provider';
import { mockDataProvider } from './mock-provider';
import { apiDataProvider, ApiRequestError } from './api-provider';

const API_BASE = import.meta.env.VITE_API_BASE ?? '/api';
const DATA_MODE = import.meta.env.VITE_DATA_MODE === 'api'
  ? 'api'
  : import.meta.env.VITE_DATA_MODE === 'mock'
    ? 'mock'
    : 'auto';

export function getDataMode(): 'api' | 'mock' | 'auto' {
  return DATA_MODE;
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

    const envelope = await res.json() as { data?: { status?: string; ok?: boolean }; status?: string; ok?: boolean };
    const payload = envelope.data ?? envelope;
    return payload.status === 'ok' || payload.status === 'ready' || payload.ok === true;
  } catch {
    return false;
  }
}

class SwitchingDataProvider implements DataProvider {
  private _resolvedMode: 'api' | 'mock' | null = DATA_MODE === 'auto' ? null : DATA_MODE;

  private async resolveMode(): Promise<'api' | 'mock'> {
    if (this._resolvedMode) return this._resolvedMode;
    this._resolvedMode = await isApiReachable() ? 'api' : 'mock';
    return this._resolvedMode;
  }

  private shouldFallbackToMock(error: unknown): boolean {
    if (error instanceof Error && error.message.includes('not yet implemented')) {
      return true;
    }
    if (DATA_MODE !== 'auto') return false;
    if (error instanceof ApiRequestError) {
      return error.isNetworkError || error.status === null;
    }
    return false;
  }

  private async withMode<T>(apiFn: () => Promise<T>, mockFn: () => Promise<T>): Promise<T> {
    const mode = await this.resolveMode();
    if (mode === 'mock') return mockFn();

    try {
      return await apiFn();
    } catch (error) {
      if (!this.shouldFallbackToMock(error)) {
        throw error;
      }
      this._resolvedMode = 'mock';
      return mockFn();
    }
  }

  isUsingApi(): boolean {
    return this._resolvedMode === 'api';
  }

  // --- Auth / Identity -----------------------------------------------------
  getAuthSession() {
    return this.withMode(
      () => apiDataProvider.getAuthSession(),
      () => mockDataProvider.getAuthSession(),
    );
  }

  setActiveOrganisation(organisationId) {
    return this.withMode(
      () => apiDataProvider.setActiveOrganisation(organisationId),
      () => mockDataProvider.setActiveOrganisation(organisationId),
    );
  }

  listAuthProfiles() {
    return this.withMode(
      () => apiDataProvider.listAuthProfiles(),
      () => mockDataProvider.listAuthProfiles(),
    );
  }

  switchAuthProfile(profileId) {
    return this.withMode(
      () => apiDataProvider.switchAuthProfile(profileId),
      () => mockDataProvider.switchAuthProfile(profileId),
    );
  }

  login(cmd) {
    return this.withMode(
      () => apiDataProvider.login(cmd),
      () => mockDataProvider.login(cmd),
    );
  }

  register(cmd) {
    return this.withMode(
      () => apiDataProvider.register(cmd),
      () => mockDataProvider.register(cmd),
    );
  }

  getMe() {
    return this.withMode(
      () => apiDataProvider.getMe(),
      () => mockDataProvider.getMe(),
    );
  }

  updateProfile(cmd) {
    return this.withMode(
      () => apiDataProvider.updateProfile(cmd),
      () => mockDataProvider.updateProfile(cmd),
    );
  }

  deleteMe() {
    return this.withMode(
      () => apiDataProvider.deleteMe(),
      () => mockDataProvider.deleteMe(),
    );
  }

  // --- Organisations --------------------------------------------------------
  createOrganisation(cmd) {
    return this.withMode(
      () => apiDataProvider.createOrganisation(cmd),
      () => mockDataProvider.createOrganisation(cmd),
    );
  }

  listOrganisations() {
    return this.withMode(
      () => apiDataProvider.listOrganisations(),
      () => mockDataProvider.listOrganisations(),
    );
  }

  // --- Taxonomy ------------------------------------------------------------
  getTaxonomy() {
    return this.withMode(
      () => apiDataProvider.getTaxonomy(),
      () => mockDataProvider.getTaxonomy(),
    );
  }

  // --- Catalog -------------------------------------------------------------
  listCollections(filters) {
    return this.withMode(
      () => apiDataProvider.listCollections(filters),
      () => mockDataProvider.listCollections(filters),
    );
  }

  getCollection(id) {
    return this.withMode(
      () => apiDataProvider.getCollection(id),
      () => mockDataProvider.getCollection(id),
    );
  }

  createCollection(cmd) {
    return this.withMode(
      () => apiDataProvider.createCollection(cmd),
      () => mockDataProvider.createCollection(cmd),
    );
  }

  addPromptItem(collectionId, cmd) {
    return this.withMode(
      () => apiDataProvider.addPromptItem(collectionId, cmd),
      () => mockDataProvider.addPromptItem(collectionId, cmd),
    );
  }

  addScenario(collectionId, cmd) {
    return this.withMode(
      () => apiDataProvider.addScenario(collectionId, cmd),
      () => mockDataProvider.addScenario(collectionId, cmd),
    );
  }

  // --- Content Generation --------------------------------------------------
  generateStructuredCollection(cmd) {
    return this.withMode(
      () => apiDataProvider.generateStructuredCollection(cmd),
      () => mockDataProvider.generateStructuredCollection(cmd),
    );
  }

  generateChatCollection(cmd) {
    return this.withMode(
      () => apiDataProvider.generateChatCollection(cmd),
      () => mockDataProvider.generateChatCollection(cmd),
    );
  }

  streamGeneration(streamToken, callbacks) {
    if (this._resolvedMode === 'mock') {
      return mockDataProvider.streamGeneration(streamToken, callbacks);
    }
    return apiDataProvider.streamGeneration(streamToken, callbacks);
  }

  // --- Practice ------------------------------------------------------------
  startQuickPracticeSession(cmd) {
    return this.withMode(
      () => apiDataProvider.startQuickPracticeSession(cmd),
      () => mockDataProvider.startQuickPracticeSession(cmd),
    );
  }

  submitAttempt(attemptId, cmd) {
    return this.withMode(
      () => apiDataProvider.submitAttempt(attemptId, cmd),
      () => mockDataProvider.submitAttempt(attemptId, cmd),
    );
  }

  getAttempt(attemptId) {
    return this.withMode(
      () => apiDataProvider.getAttempt(attemptId),
      () => mockDataProvider.getAttempt(attemptId),
    );
  }

  // --- Interview -----------------------------------------------------------
  startInterviewSession(promptItemId) {
    return this.withMode(
      () => apiDataProvider.startInterviewSession(promptItemId),
      () => mockDataProvider.startInterviewSession(promptItemId),
    );
  }

  submitInterviewTurn(sessionId, cmd) {
    return this.withMode(
      () => apiDataProvider.submitInterviewTurn(sessionId, cmd),
      () => mockDataProvider.submitInterviewTurn(sessionId, cmd),
    );
  }

  // --- Scenario ------------------------------------------------------------
  startScenarioSession(scenarioId) {
    return this.withMode(
      () => apiDataProvider.startScenarioSession(scenarioId),
      () => mockDataProvider.startScenarioSession(scenarioId),
    );
  }

  submitScenarioStep(sessionId, cmd) {
    return this.withMode(
      () => apiDataProvider.submitScenarioStep(sessionId, cmd),
      () => mockDataProvider.submitScenarioStep(sessionId, cmd),
    );
  }

  // --- Practice Runs (Aggregate) -------------------------------------------
  createPracticeRun(cmd) {
    return this.withMode(
      () => apiDataProvider.createPracticeRun(cmd),
      () => mockDataProvider.createPracticeRun(cmd),
    );
  }

  listPracticeRuns() {
    return this.withMode(
      () => apiDataProvider.listPracticeRuns(),
      () => mockDataProvider.listPracticeRuns(),
    );
  }

  getPracticeRun(runId) {
    return this.withMode(
      () => apiDataProvider.getPracticeRun(runId),
      () => mockDataProvider.getPracticeRun(runId),
    );
  }

  getPracticeSessions(runId) {
    return this.withMode(
      () => apiDataProvider.getPracticeSessions(runId),
      () => mockDataProvider.getPracticeSessions(runId),
    );
  }

  // --- Progress -----------------------------------------------------------
  getCompetencyProgress(userId) {
    return this.withMode(
      () => apiDataProvider.getCompetencyProgress(userId),
      () => mockDataProvider.getCompetencyProgress(userId),
    );
  }

  getAttemptHistory(userId) {
    return this.withMode(
      () => apiDataProvider.getAttemptHistory(userId),
      () => mockDataProvider.getAttemptHistory(userId),
    );
  }

  // --- Assistant ------------------------------------------------------------
  createAssistantSession(cmd) {
    return this.withMode(
      () => apiDataProvider.createAssistantSession(cmd),
      () => mockDataProvider.createAssistantSession(cmd),
    );
  }

  listAssistantSessions() {
    return this.withMode(
      () => apiDataProvider.listAssistantSessions(),
      () => mockDataProvider.listAssistantSessions(),
    );
  }

  getAssistantSession(sessionId) {
    return this.withMode(
      () => apiDataProvider.getAssistantSession(sessionId),
      () => mockDataProvider.getAssistantSession(sessionId),
    );
  }

  createAssistantTurn(sessionId, cmd) {
    return this.withMode(
      () => apiDataProvider.createAssistantTurn(sessionId, cmd),
      () => mockDataProvider.createAssistantTurn(sessionId, cmd),
    );
  }

  getAssistantTurn(turnId) {
    return this.withMode(
      () => apiDataProvider.getAssistantTurn(turnId),
      () => mockDataProvider.getAssistantTurn(turnId),
    );
  }

  cancelAssistantTurn(turnId, cmd) {
    return this.withMode(
      () => apiDataProvider.cancelAssistantTurn(turnId, cmd),
      () => mockDataProvider.cancelAssistantTurn(turnId, cmd),
    );
  }

  streamAssistantTurn(streamToken, callbacks) {
    if (this._resolvedMode === 'mock') {
      return mockDataProvider.streamAssistantTurn(streamToken, callbacks);
    }
    return apiDataProvider.streamAssistantTurn(streamToken, callbacks);
  }

  // --- Admin: Users & User Management ----------------------------------------
  listAdminUsers(params) {
    return this.withMode(
      () => apiDataProvider.listAdminUsers(params),
      () => mockDataProvider.listAdminUsers(params),
    );
  }

  getAdminUser(userId) {
    return this.withMode(
      () => apiDataProvider.getAdminUser(userId),
      () => mockDataProvider.getAdminUser(userId),
    );
  }

  updateAdminUserRole(userId, role) {
    return this.withMode(
      () => apiDataProvider.updateAdminUserRole(userId, role),
      () => mockDataProvider.updateAdminUserRole(userId, role),
    );
  }

  updateAdminUserStatus(userId, isActive) {
    return this.withMode(
      () => apiDataProvider.updateAdminUserStatus(userId, isActive),
      () => mockDataProvider.updateAdminUserStatus(userId, isActive),
    );
  }

  createAdminUser(cmd) {
    return this.withMode(
      () => apiDataProvider.createAdminUser(cmd),
      () => mockDataProvider.createAdminUser(cmd),
    );
  }

  bulkAdminUserOperation(cmd) {
    return this.withMode(
      () => apiDataProvider.bulkAdminUserOperation(cmd),
      () => mockDataProvider.bulkAdminUserOperation(cmd),
    );
  }

  getUserActivity(userId) {
    return this.withMode(
      () => apiDataProvider.getUserActivity(userId),
      () => mockDataProvider.getUserActivity(userId),
    );
  }

  // --- Admin: Learners & Relationships --------------------------------------
  getLearnerAnalytics(learnerId, params) {
    return this.withMode(
      () => apiDataProvider.getLearnerAnalytics(learnerId, params),
      () => mockDataProvider.getLearnerAnalytics(learnerId, params),
    );
  }

  getLearnerRelationship(learnerId) {
    return this.withMode(
      () => apiDataProvider.getLearnerRelationship(learnerId),
      () => mockDataProvider.getLearnerRelationship(learnerId),
    );
  }

  upsertLearnerRelationship(learnerId, relationshipType) {
    return this.withMode(
      () => apiDataProvider.upsertLearnerRelationship(learnerId, relationshipType),
      () => mockDataProvider.upsertLearnerRelationship(learnerId, relationshipType),
    );
  }

  deleteLearnerRelationship(learnerId) {
    return this.withMode(
      () => apiDataProvider.deleteLearnerRelationship(learnerId),
      () => mockDataProvider.deleteLearnerRelationship(learnerId),
    );
  }

  // --- Admin: Analytics Overview ---------------------------------------------
  getAnalyticsOverview(params) {
    return this.withMode(
      () => apiDataProvider.getAnalyticsOverview(params),
      () => mockDataProvider.getAnalyticsOverview(params),
    );
  }

  getCohortAnalytics(params) {
    return this.withMode(
      () => apiDataProvider.getCohortAnalytics(params),
      () => mockDataProvider.getCohortAnalytics(params),
    );
  }

  getCohortsComparison(params) {
    return this.withMode(
      () => apiDataProvider.getCohortsComparison(params),
      () => mockDataProvider.getCohortsComparison(params),
    );
  }

  // --- Admin: Collections & Verification -----------------------------------
  getVerificationQueue() {
    return this.withMode(
      () => apiDataProvider.getVerificationQueue(),
      () => mockDataProvider.getVerificationQueue(),
    );
  }

  getCollectionVerification(collectionId) {
    return this.withMode(
      () => apiDataProvider.getCollectionVerification(collectionId),
      () => mockDataProvider.getCollectionVerification(collectionId),
    );
  }

  updateCollectionVerification(collectionId, cmd) {
    return this.withMode(
      () => apiDataProvider.updateCollectionVerification(collectionId, cmd),
      () => mockDataProvider.updateCollectionVerification(collectionId, cmd),
    );
  }

  updateCollectionFeature(collectionId, featured) {
    return this.withMode(
      () => apiDataProvider.updateCollectionFeature(collectionId, featured),
      () => mockDataProvider.updateCollectionFeature(collectionId, featured),
    );
  }

  // --- Admin: Evaluation Dashboard -------------------------------------------
  listEvalSuites() {
    return this.withMode(
      () => apiDataProvider.listEvalSuites(),
      () => mockDataProvider.listEvalSuites(),
    );
  }

  listEvalRuns(params) {
    return this.withMode(
      () => apiDataProvider.listEvalRuns(params),
      () => mockDataProvider.listEvalRuns(params),
    );
  }

  getEvalRun(runId) {
    return this.withMode(
      () => apiDataProvider.getEvalRun(runId),
      () => mockDataProvider.getEvalRun(runId),
    );
  }

  triggerEvalRun(cmd) {
    return this.withMode(
      () => apiDataProvider.triggerEvalRun(cmd),
      () => mockDataProvider.triggerEvalRun(cmd),
    );
  }

  getEvalDashboard(params) {
    return this.withMode(
      () => apiDataProvider.getEvalDashboard(params),
      () => mockDataProvider.getEvalDashboard(params),
    );
  }

  getEvalRunsComparison(params) {
    return this.withMode(
      () => apiDataProvider.getEvalRunsComparison(params),
      () => mockDataProvider.getEvalRunsComparison(params),
    );
  }

  getEvalBenchmark(params) {
    return this.withMode(
      () => apiDataProvider.getEvalBenchmark(params),
      () => mockDataProvider.getEvalBenchmark(params),
    );
  }

  getEvalCaseDetail(caseId) {
    return this.withMode(
      () => apiDataProvider.getEvalCaseDetail(caseId),
      () => mockDataProvider.getEvalCaseDetail(caseId),
    );
  }

  // --- Admin: Providers --------------------------------------------------------
  listOpenRouterModels() {
    return this.withMode(
      () => apiDataProvider.listOpenRouterModels(),
      () => mockDataProvider.listOpenRouterModels(),
    );
  }

  // --- Admin: Prompts --------------------------------------------------------
  listPrompts() {
    return this.withMode(
      () => apiDataProvider.listPrompts(),
      () => mockDataProvider.listPrompts(),
    );
  }

  listPromptVersions(name) {
    return this.withMode(
      () => apiDataProvider.listPromptVersions(name),
      () => mockDataProvider.listPromptVersions(name),
    );
  }

  getPromptVersion(name, version) {
    return this.withMode(
      () => apiDataProvider.getPromptVersion(name, version),
      () => mockDataProvider.getPromptVersion(name, version),
    );
  }

  createPrompt(cmd) {
    return this.withMode(
      () => apiDataProvider.createPrompt(cmd),
      () => mockDataProvider.createPrompt(cmd),
    );
  }

  updatePrompt(name, version, cmd) {
    return this.withMode(
      () => apiDataProvider.updatePrompt(name, version, cmd),
      () => mockDataProvider.updatePrompt(name, version, cmd),
    );
  }

  publishPrompt(name, version) {
    return this.withMode(
      () => apiDataProvider.publishPrompt(name, version),
      () => mockDataProvider.publishPrompt(name, version),
    );
  }

  archivePrompt(name, version) {
    return this.withMode(
      () => apiDataProvider.archivePrompt(name, version),
      () => mockDataProvider.archivePrompt(name, version),
    );
  }

  getPromptAnalytics(name, version) {
    return this.withMode(
      () => apiDataProvider.getPromptAnalytics(name, version),
      () => mockDataProvider.getPromptAnalytics(name, version),
    );
  }

  comparePrompts(cmd) {
    return this.withMode(
      () => apiDataProvider.comparePrompts(cmd),
      () => mockDataProvider.comparePrompts(cmd),
    );
  }

  // --- Admin: Pipelines ------------------------------------------------------
  listPipelines() {
    return this.withMode(
      () => apiDataProvider.listPipelines(),
      () => mockDataProvider.listPipelines(),
    );
  }

  getPipelineDAG(pipelineName) {
    return this.withMode(
      () => apiDataProvider.getPipelineDAG(pipelineName),
      () => mockDataProvider.getPipelineDAG(pipelineName),
    );
  }

  listPipelineRuns(pipelineName, params) {
    return this.withMode(
      () => apiDataProvider.listPipelineRuns(pipelineName, params),
      () => mockDataProvider.listPipelineRuns(pipelineName, params),
    );
  }

  getPipelineTrace(pipelineName, pipelineRunId) {
    return this.withMode(
      () => apiDataProvider.getPipelineTrace(pipelineName, pipelineRunId),
      () => mockDataProvider.getPipelineTrace(pipelineName, pipelineRunId),
    );
  }

  getPipelineMetrics(pipelineName) {
    return this.withMode(
      () => apiDataProvider.getPipelineMetrics(pipelineName),
      () => mockDataProvider.getPipelineMetrics(pipelineName),
    );
  }

  // --- Admin: Rubrics --------------------------------------------------------
  listRubrics() {
    return this.withMode(
      () => apiDataProvider.listRubrics(),
      () => mockDataProvider.listRubrics(),
    );
  }

  getRubric(rubricId) {
    return this.withMode(
      () => apiDataProvider.getRubric(rubricId),
      () => mockDataProvider.getRubric(rubricId),
    );
  }

  createRubric(cmd) {
    return this.withMode(
      () => apiDataProvider.createRubric(cmd),
      () => mockDataProvider.createRubric(cmd),
    );
  }

  updateRubric(rubricId, cmd) {
    return this.withMode(
      () => apiDataProvider.updateRubric(rubricId, cmd),
      () => mockDataProvider.updateRubric(rubricId, cmd),
    );
  }

  deleteRubric(rubricId) {
    return this.withMode(
      () => apiDataProvider.deleteRubric(rubricId),
      () => mockDataProvider.deleteRubric(rubricId),
    );
  }

  addRubricCriterion(rubricId, criterion) {
    return this.withMode(
      () => apiDataProvider.addRubricCriterion(rubricId, criterion),
      () => mockDataProvider.addRubricCriterion(rubricId, criterion),
    );
  }

  updateRubricCriterion(rubricId, criterionRef, criterion) {
    return this.withMode(
      () => apiDataProvider.updateRubricCriterion(rubricId, criterionRef, criterion),
      () => mockDataProvider.updateRubricCriterion(rubricId, criterionRef, criterion),
    );
  }

  deleteRubricCriterion(rubricId, criterionRef) {
    return this.withMode(
      () => apiDataProvider.deleteRubricCriterion(rubricId, criterionRef),
      () => mockDataProvider.deleteRubricCriterion(rubricId, criterionRef),
    );
  }

  // --- Admin: Audit & Events -------------------------------------------------
  listWorkflowEvents(params) {
    return this.withMode(
      () => apiDataProvider.listWorkflowEvents(params),
      () => mockDataProvider.listWorkflowEvents(params),
    );
  }

  listUnifiedAuditLog(params) {
    return this.withMode(
      () => apiDataProvider.listUnifiedAuditLog(params),
      () => mockDataProvider.listUnifiedAuditLog(params),
    );
  }

  getWorkflowEvent(eventId) {
    return this.withMode(
      () => apiDataProvider.getWorkflowEvent(eventId),
      () => mockDataProvider.getWorkflowEvent(eventId),
    );
  }

  updateWorkflowEvent(eventId, cmd) {
    return this.withMode(
      () => apiDataProvider.updateWorkflowEvent(eventId, cmd),
      () => mockDataProvider.updateWorkflowEvent(eventId, cmd),
    );
  }

  deleteWorkflowEvent(eventId) {
    return this.withMode(
      () => apiDataProvider.deleteWorkflowEvent(eventId),
      () => mockDataProvider.deleteWorkflowEvent(eventId),
    );
  }

  getAttemptAudit(attemptId) {
    return this.withMode(
      () => apiDataProvider.getAttemptAudit(attemptId),
      () => mockDataProvider.getAttemptAudit(attemptId),
    );
  }

  // --- Admin: Telemetry & Monitoring -----------------------------------------
  getTelemetryOverview(params) {
    return this.withMode(
      () => apiDataProvider.getTelemetryOverview(params),
      () => mockDataProvider.getTelemetryOverview(params),
    );
  }

  listTelemetryTraces(params) {
    return this.withMode(
      () => apiDataProvider.listTelemetryTraces(params),
      () => mockDataProvider.listTelemetryTraces(params),
    );
  }

  getTelemetryTrace(traceId) {
    return this.withMode(
      () => apiDataProvider.getTelemetryTrace(traceId),
      () => mockDataProvider.getTelemetryTrace(traceId),
    );
  }

  // --- Admin: Org-scoped Skills ---------------------------------------------
  listOrgSkills(orgId) {
    return this.withMode(
      () => apiDataProvider.listOrgSkills(orgId),
      () => mockDataProvider.listOrgSkills(orgId),
    );
  }

  getOrgSkill(orgId, skillId) {
    return this.withMode(
      () => apiDataProvider.getOrgSkill(orgId, skillId),
      () => mockDataProvider.getOrgSkill(orgId, skillId),
    );
  }

  createOrgSkill(orgId, cmd) {
    return this.withMode(
      () => apiDataProvider.createOrgSkill(orgId, cmd),
      () => mockDataProvider.createOrgSkill(orgId, cmd),
    );
  }

  updateOrgSkill(orgId, skillId, cmd) {
    return this.withMode(
      () => apiDataProvider.updateOrgSkill(orgId, skillId, cmd),
      () => mockDataProvider.updateOrgSkill(orgId, skillId, cmd),
    );
  }

  deleteOrgSkill(orgId, skillId) {
    return this.withMode(
      () => apiDataProvider.deleteOrgSkill(orgId, skillId),
      () => mockDataProvider.deleteOrgSkill(orgId, skillId),
    );
  }

  // --- Admin: Org-scoped Competencies ---------------------------------------
  listOrgCompetencies(orgId) {
    return this.withMode(
      () => apiDataProvider.listOrgCompetencies(orgId),
      () => mockDataProvider.listOrgCompetencies(orgId),
    );
  }

  getOrgCompetency(orgId, competencyId) {
    return this.withMode(
      () => apiDataProvider.getOrgCompetency(orgId, competencyId),
      () => mockDataProvider.getOrgCompetency(orgId, competencyId),
    );
  }

  createOrgCompetency(orgId, cmd) {
    return this.withMode(
      () => apiDataProvider.createOrgCompetency(orgId, cmd),
      () => mockDataProvider.createOrgCompetency(orgId, cmd),
    );
  }

  updateOrgCompetency(orgId, competencyId, cmd) {
    return this.withMode(
      () => apiDataProvider.updateOrgCompetency(orgId, competencyId, cmd),
      () => mockDataProvider.updateOrgCompetency(orgId, competencyId, cmd),
    );
  }

  deleteOrgCompetency(orgId, competencyId) {
    return this.withMode(
      () => apiDataProvider.deleteOrgCompetency(orgId, competencyId),
      () => mockDataProvider.deleteOrgCompetency(orgId, competencyId),
    );
  }

  // --- Admin: Org-scoped Rubrics --------------------------------------------
  listOrgRubrics(orgId) {
    return this.withMode(
      () => apiDataProvider.listOrgRubrics(orgId),
      () => mockDataProvider.listOrgRubrics(orgId),
    );
  }

  getOrgRubric(orgId, rubricId) {
    return this.withMode(
      () => apiDataProvider.getOrgRubric(orgId, rubricId),
      () => mockDataProvider.getOrgRubric(orgId, rubricId),
    );
  }

  createOrgRubric(orgId, cmd) {
    return this.withMode(
      () => apiDataProvider.createOrgRubric(orgId, cmd),
      () => mockDataProvider.createOrgRubric(orgId, cmd),
    );
  }

  updateOrgRubric(orgId, rubricId, cmd) {
    return this.withMode(
      () => apiDataProvider.updateOrgRubric(orgId, rubricId, cmd),
      () => mockDataProvider.updateOrgRubric(orgId, rubricId, cmd),
    );
  }

  deleteOrgRubric(orgId, rubricId) {
    return this.withMode(
      () => apiDataProvider.deleteOrgRubric(orgId, rubricId),
      () => mockDataProvider.deleteOrgRubric(orgId, rubricId),
    );
  }

  // --- Admin: Org-scoped Prompt Items ---------------------------------------
  listOrgPromptItems(orgId) {
    return this.withMode(
      () => apiDataProvider.listOrgPromptItems(orgId),
      () => mockDataProvider.listOrgPromptItems(orgId),
    );
  }

  getOrgPromptItem(orgId, promptItemId) {
    return this.withMode(
      () => apiDataProvider.getOrgPromptItem(orgId, promptItemId),
      () => mockDataProvider.getOrgPromptItem(orgId, promptItemId),
    );
  }

  createOrgPromptItem(orgId, cmd) {
    return this.withMode(
      () => apiDataProvider.createOrgPromptItem(orgId, cmd),
      () => mockDataProvider.createOrgPromptItem(orgId, cmd),
    );
  }

  updateOrgPromptItem(orgId, promptItemId, cmd) {
    return this.withMode(
      () => apiDataProvider.updateOrgPromptItem(orgId, promptItemId, cmd),
      () => mockDataProvider.updateOrgPromptItem(orgId, promptItemId, cmd),
    );
  }

  deleteOrgPromptItem(orgId, promptItemId) {
    return this.withMode(
      () => apiDataProvider.deleteOrgPromptItem(orgId, promptItemId),
      () => mockDataProvider.deleteOrgPromptItem(orgId, promptItemId),
    );
  }

  // --- Admin: Org-scoped Scenarios ------------------------------------------
  listOrgScenarios(orgId) {
    return this.withMode(
      () => apiDataProvider.listOrgScenarios(orgId),
      () => mockDataProvider.listOrgScenarios(orgId),
    );
  }

  getOrgScenario(orgId, scenarioId) {
    return this.withMode(
      () => apiDataProvider.getOrgScenario(orgId, scenarioId),
      () => mockDataProvider.getOrgScenario(orgId, scenarioId),
    );
  }

  createOrgScenario(orgId, cmd) {
    return this.withMode(
      () => apiDataProvider.createOrgScenario(orgId, cmd),
      () => mockDataProvider.createOrgScenario(orgId, cmd),
    );
  }

  updateOrgScenario(orgId, scenarioId, cmd) {
    return this.withMode(
      () => apiDataProvider.updateOrgScenario(orgId, scenarioId, cmd),
      () => mockDataProvider.updateOrgScenario(orgId, scenarioId, cmd),
    );
  }

  deleteOrgScenario(orgId, scenarioId) {
    return this.withMode(
      () => apiDataProvider.deleteOrgScenario(orgId, scenarioId),
      () => mockDataProvider.deleteOrgScenario(orgId, scenarioId),
    );
  }
}

export const switchingDataProvider = new SwitchingDataProvider();
