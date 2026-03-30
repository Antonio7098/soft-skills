import type {
  UserView,
  AuthSessionView,
  AuthProfileView,
  LoginUserCommand,
  TaxonomySnapshot,
  CollectionView,
  CollectionListFilters,
  CollectionCreateCommand,
  PromptItemCreateCommand,
  ScenarioCreateCommand,
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
  PracticeSessionView,
  StartPracticeRunCommand,
  StructuredCollectionGenerationCommand,
  ChatCollectionGenerationCommand,
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
  WorkflowEventView,
  PaginatedWorkflowEventsView,
  AttemptAuditView,
  TelemetryOverviewView,
  TelemetryTraceListView,
  TelemetryTraceView,
  AssistantSessionView,
  AssistantTurnView,
  CreateAssistantSessionCommand,
  CreateAssistantTurnCommand,
  CancelAssistantTurnCommand,
  AssistantStreamCallbacks,
  OrgSkillView,
  OrgCompetencyView,
  OrgRubricView,
  PromptItemView,
  ScenarioView,
} from './types';

// ---------------------------------------------------------------------------
// DataProvider — single interface the frontend depends on.
// Swap MockDataProvider ↔ ApiDataProvider without touching components.
// ---------------------------------------------------------------------------

export interface DataProvider {
  // --- Auth / Identity -----------------------------------------------------
  getAuthSession(): Promise<AuthSessionView>;
  setActiveOrganisation(organisationId: string | null): Promise<AuthSessionView>;
  listAuthProfiles(): Promise<AuthProfileView[]>;
  switchAuthProfile(profileId: string): Promise<AuthSessionView>;
  login(cmd: LoginUserCommand): Promise<UserView>;
  register(cmd: RegisterUserCommand): Promise<UserView>;
  getMe(): Promise<UserView>;
  updateProfile(cmd: UpdateProfileCommand): Promise<UserView>;
  deleteMe(): Promise<DeleteAccountResult>;

  // --- Taxonomy ------------------------------------------------------------
  getTaxonomy(): Promise<TaxonomySnapshot>;

  // --- Catalog -------------------------------------------------------------
  listCollections(filters?: CollectionListFilters): Promise<CollectionView[]>;
  getCollection(id: string): Promise<CollectionView>;
  createCollection(cmd: CollectionCreateCommand): Promise<CollectionView>;
  addPromptItem(collectionId: string, cmd: PromptItemCreateCommand): Promise<CollectionView>;
  addScenario(collectionId: string, cmd: ScenarioCreateCommand): Promise<CollectionView>;

  // --- Content Generation --------------------------------------------------
  generateStructuredCollection(cmd: StructuredCollectionGenerationCommand): Promise<CollectionGenerationView>;
  generateChatCollection(cmd: ChatCollectionGenerationCommand): Promise<CollectionGenerationView>;

  // --- Practice ------------------------------------------------------------
  startQuickPracticeSession(cmd: StartQuickPracticeSessionCommand): Promise<QuickPracticeSessionView>;
  submitAttempt(attemptId: string, cmd: SubmitAttemptCommand): Promise<AttemptView>;
  getAttempt(attemptId: string): Promise<AttemptView>;

  // --- Interview -----------------------------------------------------------
  startInterviewSession(promptItemId: string): Promise<InterviewSessionView>;
  submitInterviewTurn(sessionId: string, cmd: SubmitAttemptCommand): Promise<InterviewSessionView>;

  // --- Scenario ------------------------------------------------------------
  startScenarioSession(scenarioId: string): Promise<ScenarioSessionView>;
  submitScenarioStep(sessionId: string, cmd: SubmitAttemptCommand): Promise<ScenarioSessionView>;

  // --- Practice Runs (Aggregate) -------------------------------------------
  createPracticeRun(cmd: StartPracticeRunCommand): Promise<PracticeRunView>;
  listPracticeRuns(): Promise<PracticeRunView[]>;
  getPracticeRun(runId: string): Promise<PracticeRunView>;
  getPracticeSessions(runId: string): Promise<PracticeSessionView[]>;

  // --- Progress (derived — no backend endpoint yet) ------------------------
  getCompetencyProgress(userId: string): Promise<CompetencyProgressView[]>;
  getAttemptHistory(userId: string): Promise<AttemptHistoryItem[]>;

  // --- Admin: Users & User Management ----------------------------------------
  listAdminUsers(params?: {
    offset?: number;
    limit?: number;
    search?: string;
    role?: string;
    is_active?: boolean;
  }): Promise<AdminUserListView>;
  getAdminUser(userId: string): Promise<AdminUserView | null>;
  updateAdminUserRole(userId: string, role: string): Promise<AdminUserView>;
  updateAdminUserStatus(userId: string, isActive: boolean): Promise<AdminUserView>;
  createAdminUser(cmd: { email: string; role: string }): Promise<AdminUserView>;
  bulkAdminUserOperation(cmd: {
    user_ids: string[];
    operation: string;
    payload?: { role?: string };
  }): Promise<BulkOperationResultView>;
  getUserActivity(userId: string): Promise<UserActivityView>;

  // --- Admin: Learners & Relationships --------------------------------------
  getLearnerAnalytics(
    learnerId: string,
    params?: { from_date?: string; to_date?: string },
  ): Promise<LearnerAnalyticsView>;
  getLearnerRelationship(learnerId: string): Promise<AdminLearnerRelationshipView | null>;
  upsertLearnerRelationship(
    learnerId: string,
    relationshipType: string,
  ): Promise<AdminLearnerRelationshipView>;
  deleteLearnerRelationship(learnerId: string): Promise<{ status: string }>;

  // --- Admin: Analytics Overview --------------------------------------------
  getAnalyticsOverview(params?: {
    from_date?: string;
    to_date?: string;
  }): Promise<AnalyticsOverviewView>;
  getCohortAnalytics(params?: {
    target_role?: string;
    from_date?: string;
    to_date?: string;
  }): Promise<CohortAnalyticsView>;
  getCohortsComparison(params: {
    cohort_keys: string;
    from_date?: string;
    to_date?: string;
  }): Promise<CohortComparisonView>;

  // --- Admin: Collections & Verification -----------------------------------
  getVerificationQueue(): Promise<CollectionVerificationQueueItemView[]>;
  getCollectionVerification(collectionId: string): Promise<CollectionVerificationAuditView>;
  updateCollectionVerification(
    collectionId: string,
    cmd: { verification_state: string; note?: string },
  ): Promise<CollectionVerificationAuditView>;
  updateCollectionFeature(
    collectionId: string,
    featured: boolean,
  ): Promise<CollectionView>;

  // --- Admin: Evaluation Dashboard -------------------------------------------
  listEvalSuites(): Promise<EvaluationSuiteView[]>;
  listEvalRuns(params?: { limit?: number }): Promise<EvaluationRunView[]>;
  getEvalRun(runId: string): Promise<EvaluationRunView>;
  triggerEvalRun(cmd: { suite_id: string; model_slugs?: string[]; case_ids?: string[]; tags?: string[] }): Promise<EvaluationRunView>;
  getEvalDashboard(params?: {
    from_date?: string;
    to_date?: string;
  }): Promise<EvaluationDashboardView>;
  getEvalRunsComparison(params: {
    run_ids: string;
    from_date?: string;
    to_date?: string;
  }): Promise<EvaluationComparisonView>;
  getEvalBenchmark(params?: {
    from_date?: string;
    to_date?: string;
  }): Promise<BenchmarkDashboardView>;
  getEvalCaseDetail(caseId: string): Promise<EvaluationCaseDetailView>;

  // --- Admin: Providers --------------------------------------------------------
  listOpenRouterModels(): Promise<ProviderModel[]>;

  // --- Admin: Prompts --------------------------------------------------------
  listPrompts(): Promise<PromptSummaryView[]>;
  listPromptVersions(name: string): Promise<PromptVersionView[]>;
  getPromptVersion(name: string, version: string): Promise<PromptVersionView>;
  createPrompt(cmd: {
    name: string;
    version: string;
    prompt_type: string;
    template: string;
    variables_schema: Record<string, unknown>;
    output_schema?: Record<string, unknown> | null;
    parent_version_id?: number | null;
  }): Promise<PromptVersionView>;
  updatePrompt(
    name: string,
    version: string,
    cmd: {
      template?: string;
      variables_schema?: Record<string, unknown>;
      output_schema?: Record<string, unknown> | null;
    },
  ): Promise<PromptVersionView>;
  publishPrompt(name: string, version: string): Promise<PromptVersionView>;
  archivePrompt(name: string, version: string): Promise<PromptVersionView>;
  getPromptAnalytics(name: string, version: string): Promise<PromptAnalyticsView>;
  comparePrompts(cmd: {
    name: string;
    version_a: string;
    version_b: string;
  }): Promise<PromptCompareView>;

  // --- Admin: Pipelines ------------------------------------------------------
  listPipelines(): Promise<PipelineDefinitionView[]>;
  getPipelineDAG(pipelineName: string): Promise<PipelineDAGView>;
  listPipelineRuns(
    pipelineName: string,
    params?: { offset?: number; limit?: number },
  ): Promise<PipelineRunSummaryView[]>;
  getPipelineTrace(
    pipelineName: string,
    pipelineRunId: string,
  ): Promise<PipelineTraceView>;
  getPipelineMetrics(pipelineName: string): Promise<PipelineMetricsView>;

  // --- Admin: Rubrics --------------------------------------------------------
  listRubrics(): Promise<RubricView[]>;
  getRubric(rubricId: string): Promise<RubricView>;
  createRubric(cmd: {
    rubric_id: string;
    family: string;
    version: string;
    content_type: string;
    schema_version: string;
    name: string;
    criteria?: RubricCriterionInput[];
  }): Promise<RubricView>;
  updateRubric(
    rubricId: string,
    cmd: { family?: string; version?: string; name?: string },
  ): Promise<RubricView>;
  deleteRubric(rubricId: string): Promise<{ status: string }>;
  addRubricCriterion(
    rubricId: string,
    criterion: RubricCriterionInput,
  ): Promise<RubricView>;
  updateRubricCriterion(
    rubricId: string,
    criterionRef: string,
    criterion: Partial<RubricCriterionInput>,
  ): Promise<RubricView>;
  deleteRubricCriterion(
    rubricId: string,
    criterionRef: string,
  ): Promise<RubricView>;

  // --- Admin: Org-scoped Skills ------------------------------------------------
  listOrgSkills(orgId: string): Promise<OrgSkillView[]>;
  getOrgSkill(orgId: string, skillSlug: string): Promise<OrgSkillView>;
  createOrgSkill(orgId: string, cmd: { slug: string; name: string; description: string }): Promise<OrgSkillView>;
  updateOrgSkill(orgId: string, skillSlug: string, cmd: { name?: string; description?: string }): Promise<OrgSkillView>;
  deleteOrgSkill(orgId: string, skillSlug: string): Promise<{ status: string }>;

  // --- Admin: Org-scoped Competencies -----------------------------------------
  listOrgCompetencies(orgId: string): Promise<OrgCompetencyView[]>;
  getOrgCompetency(orgId: string, competencySlug: string): Promise<OrgCompetencyView>;
  createOrgCompetency(orgId: string, cmd: { slug: string; name: string; description: string; skill_slugs?: string[] }): Promise<OrgCompetencyView>;
  updateOrgCompetency(orgId: string, competencySlug: string, cmd: { name?: string; description?: string; skill_slugs?: string[] }): Promise<OrgCompetencyView>;
  deleteOrgCompetency(orgId: string, competencySlug: string): Promise<{ status: string }>;

  // --- Admin: Org-scoped Rubrics ----------------------------------------------
  listOrgRubrics(orgId: string): Promise<OrgRubricView[]>;
  getOrgRubric(orgId: string, rubricId: string): Promise<OrgRubricView>;
  createOrgRubric(orgId: string, cmd: {
    rubric_id: string;
    family: string;
    version: string;
    content_type: string;
    schema_version: string;
    name: string;
    criteria?: string[];
  }): Promise<OrgRubricView>;
  updateOrgRubric(orgId: string, rubricId: string, cmd: { name?: string; criteria?: string[] }): Promise<OrgRubricView>;
  deleteOrgRubric(orgId: string, rubricId: string): Promise<{ status: string }>;

  // --- Admin: Org-scoped Prompt Items -----------------------------------------
  listOrgPromptItems(orgId: string): Promise<PromptItemView[]>;
  getOrgPromptItem(orgId: string, promptItemId: string): Promise<PromptItemView>;
  createOrgPromptItem(orgId: string, cmd: PromptItemCreateCommand): Promise<PromptItemView>;
  updateOrgPromptItem(orgId: string, promptItemId: string, cmd: Partial<PromptItemCreateCommand>): Promise<PromptItemView>;
  deleteOrgPromptItem(orgId: string, promptItemId: string): Promise<{ status: string }>;

  // --- Admin: Org-scoped Scenarios -------------------------------------------
  listOrgScenarios(orgId: string): Promise<ScenarioView[]>;
  getOrgScenario(orgId: string, scenarioId: string): Promise<ScenarioView>;
  createOrgScenario(orgId: string, cmd: ScenarioCreateCommand): Promise<ScenarioView>;
  updateOrgScenario(orgId: string, scenarioId: string, cmd: Partial<ScenarioCreateCommand>): Promise<ScenarioView>;
  deleteOrgScenario(orgId: string, scenarioId: string): Promise<{ status: string }>;

  // --- Admin: Audit & Events -------------------------------------------------
  listWorkflowEvents(params?: {
    event_type?: string;
    trace_id?: string;
    workflow_id?: string;
    request_id?: string;
    error_code?: string;
    offset?: number;
    limit?: number;
  }): Promise<PaginatedWorkflowEventsView>;
  getWorkflowEvent(eventId: string): Promise<WorkflowEventView>;
  updateWorkflowEvent(
    eventId: string,
    cmd: { error_code?: string; payload?: Record<string, unknown> },
  ): Promise<WorkflowEventView>;
  deleteWorkflowEvent(eventId: string): Promise<{ status: string }>;
  getAttemptAudit(attemptId: string): Promise<AttemptAuditView>;

  // --- Admin: Telemetry & Monitoring -----------------------------------------
  getTelemetryOverview(params?: {
    organisation_id?: string;
    from_date?: string;
    to_date?: string;
  }): Promise<TelemetryOverviewView>;
  listTelemetryTraces(params?: {
    organisation_id?: string;
    from_date?: string;
    to_date?: string;
    offset?: number;
    limit?: number;
  }): Promise<TelemetryTraceListView>;
  getTelemetryTrace(traceId: string): Promise<TelemetryTraceView | null>;

  // --- Assistant ------------------------------------------------------------
  createAssistantSession(cmd?: CreateAssistantSessionCommand): Promise<AssistantSessionView>;
  listAssistantSessions(): Promise<AssistantSessionView[]>;
  getAssistantSession(sessionId: string): Promise<AssistantSessionView>;
  createAssistantTurn(sessionId: string, cmd: CreateAssistantTurnCommand): Promise<AssistantTurnView>;
  getAssistantTurn(turnId: string): Promise<AssistantTurnView>;
  cancelAssistantTurn(turnId: string, cmd?: CancelAssistantTurnCommand): Promise<AssistantTurnView>;
  streamAssistantTurn(streamToken: string, callbacks: AssistantStreamCallbacks): () => void;
}
