import type {
  UserView,
  TaxonomySnapshot,
  CollectionView,
  CollectionListFilters,
  CollectionCreateCommand,
  PromptItemCreateCommand,
  ScenarioCreateCommand,
  RegisterUserCommand,
  UpdateProfileCommand,
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
} from './types';

// ---------------------------------------------------------------------------
// DataProvider — single interface the frontend depends on.
// Swap MockDataProvider ↔ ApiDataProvider without touching components.
// ---------------------------------------------------------------------------

export interface DataProvider {
  // --- Auth / Identity -----------------------------------------------------
  register(cmd: RegisterUserCommand): Promise<UserView>;
  getMe(): Promise<UserView>;
  updateProfile(cmd: UpdateProfileCommand): Promise<UserView>;

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
}
