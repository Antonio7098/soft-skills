import React, { type ReactNode } from 'react';
import { render, type RenderOptions } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { DataProviderProvider } from '@/data/DataContext';
import { AuthSessionProvider } from '@/auth/AuthSessionContext';
import type { DataProvider } from '@/data/provider';
import type { AuthSessionView, AuthProfileView } from '@/data';

export const createMockSession = (overrides: Partial<AuthSessionView> = {}): AuthSessionView => ({
  status: 'authenticated',
  actor: {
    id: 'user-001',
    email: 'test@example.com',
    display_name: 'Test User',
    role: 'learner',
    auth_provider: 'google',
    created_at: '2025-01-01T00:00:00Z',
    profile: {
      target_role: 'Sales Representative',
      goals: ['Improve communication'],
      practice_preferences: {},
    },
  },
  platform_role: 'learner',
  org_memberships: [
    {
      organisation_id: 'org-001',
      organisation_name: 'Acme Sales',
      role: 'member',
      permissions: ['collections:read', 'practice:run'],
    },
  ],
  active_organisation_id: 'org-001',
  capabilities: ['app:access'],
  data_mode: 'mock',
  ...overrides,
});

export const mockAuthProfiles: AuthProfileView[] = [
  {
    id: 'learner-alex',
    label: 'Alex Chen',
    description: 'Learner in Acme Sales',
    session: createMockSession({ status: 'authenticated' }),
  },
  {
    id: 'org-admin-alex',
    label: 'Alex Chen (Org Admin)',
    description: 'Org admin for Acme Sales',
    session: createMockSession({
      platform_role: 'admin',
      capabilities: ['app:access', 'admin:access'],
      org_memberships: [
        {
          organisation_id: 'org-001',
          organisation_name: 'Acme Sales',
          role: 'org_admin',
          permissions: ['collections:read', 'practice:run', 'admin:access', 'org:read', 'org:write'],
        },
      ],
    }),
  },
  {
    id: 'superadmin-henry',
    label: 'Henry Patel',
    description: 'Platform admin across multiple organisations',
    session: createMockSession({
      actor: {
        id: 'user-900',
        email: 'henry.patel@acme.com',
        display_name: 'Henry Patel',
        role: 'superadmin',
        auth_provider: 'google',
        created_at: '2026-01-05T10:00:00Z',
        profile: {
          target_role: 'Platform Admin',
          goals: ['Audit org content'],
          practice_preferences: {},
        },
      },
      platform_role: 'superadmin',
      capabilities: ['app:access', 'admin:access', 'platform:superadmin'],
      org_memberships: [
        {
          organisation_id: 'org-001',
          organisation_name: 'Acme Sales',
          role: 'org_admin',
          permissions: ['collections:read', 'practice:run', 'admin:access', 'org:read', 'org:write'],
        },
        {
          organisation_id: 'org-002',
          organisation_name: 'Acme Support',
          role: 'org_admin',
          permissions: ['collections:read', 'practice:run', 'admin:access', 'org:read', 'org:write'],
        },
      ],
      active_organisation_id: 'org-001',
    }),
  },
];

export const createMockDataProvider = (overrides: Partial<DataProvider> = {}): DataProvider => {
  const defaultSession = createMockSession();

  return {
    getAuthSession: vi.fn().mockResolvedValue(defaultSession),
    setActiveOrganisation: vi.fn().mockResolvedValue(defaultSession),
    listAuthProfiles: vi.fn().mockResolvedValue(mockAuthProfiles),
    switchAuthProfile: vi.fn().mockImplementation((profileId: string) => {
      const profile = mockAuthProfiles.find((p) => p.id === profileId) ?? mockAuthProfiles[1]!;
      return Promise.resolve(profile.session);
    }),
    login: vi.fn().mockResolvedValue(defaultSession.actor!),
    register: vi.fn().mockResolvedValue(defaultSession.actor!),
    getMe: vi.fn().mockResolvedValue(defaultSession.actor!),
    updateProfile: vi.fn().mockResolvedValue(defaultSession.actor!),
    deleteMe: vi.fn().mockResolvedValue({ deleted_user_id: defaultSession.actor!.id, status: 'deleted' }),
    getTaxonomy: vi.fn().mockResolvedValue({ skills: [], competencies: [] }),
    listCollections: vi.fn().mockResolvedValue([]),
    getCollection: vi.fn().mockResolvedValue({} as any),
    createCollection: vi.fn().mockResolvedValue({} as any),
    addPromptItem: vi.fn().mockResolvedValue({} as any),
    addScenario: vi.fn().mockResolvedValue({} as any),
    generateStructuredCollection: vi.fn().mockResolvedValue({} as any),
    generateChatCollection: vi.fn().mockResolvedValue({} as any),
    startQuickPracticeSession: vi.fn().mockResolvedValue({} as any),
    submitAttempt: vi.fn().mockResolvedValue({} as any),
    getAttempt: vi.fn().mockResolvedValue({} as any),
    startInterviewSession: vi.fn().mockResolvedValue({} as any),
    submitInterviewTurn: vi.fn().mockResolvedValue({} as any),
    startScenarioSession: vi.fn().mockResolvedValue({} as any),
    submitScenarioStep: vi.fn().mockResolvedValue({} as any),
    createPracticeRun: vi.fn().mockResolvedValue({} as any),
    listPracticeRuns: vi.fn().mockResolvedValue([]),
    getPracticeRun: vi.fn().mockResolvedValue({} as any),
    getPracticeSessions: vi.fn().mockResolvedValue([]),
    getCompetencyProgress: vi.fn().mockResolvedValue([]),
    getAttemptHistory: vi.fn().mockResolvedValue([]),
    listAdminUsers: vi.fn().mockResolvedValue({ users: [], total: 0 }),
    getAdminUser: vi.fn().mockResolvedValue(null),
    updateAdminUserRole: vi.fn().mockResolvedValue({} as any),
    updateAdminUserStatus: vi.fn().mockResolvedValue({} as any),
    createAdminUser: vi.fn().mockResolvedValue({} as any),
    bulkAdminUserOperation: vi.fn().mockResolvedValue({} as any),
    getUserActivity: vi.fn().mockResolvedValue({} as any),
    getLearnerAnalytics: vi.fn().mockResolvedValue({} as any),
    getLearnerRelationship: vi.fn().mockResolvedValue(null),
    upsertLearnerRelationship: vi.fn().mockResolvedValue({} as any),
    deleteLearnerRelationship: vi.fn().mockResolvedValue({ status: 'ok' }),
    getAnalyticsOverview: vi.fn().mockResolvedValue({} as any),
    getCohortAnalytics: vi.fn().mockResolvedValue({} as any),
    getCohortsComparison: vi.fn().mockResolvedValue({} as any),
    getVerificationQueue: vi.fn().mockResolvedValue([]),
    getCollectionVerification: vi.fn().mockResolvedValue({} as any),
    updateCollectionVerification: vi.fn().mockResolvedValue({} as any),
    updateCollectionFeature: vi.fn().mockResolvedValue({} as any),
    listEvalSuites: vi.fn().mockResolvedValue([]),
    listEvalRuns: vi.fn().mockResolvedValue([]),
    getEvalRun: vi.fn().mockResolvedValue({} as any),
    triggerEvalRun: vi.fn().mockResolvedValue({} as any),
    getEvalDashboard: vi.fn().mockResolvedValue({} as any),
    getEvalRunsComparison: vi.fn().mockResolvedValue({} as any),
    getEvalBenchmark: vi.fn().mockResolvedValue({} as any),
    getEvalCaseDetail: vi.fn().mockResolvedValue({} as any),
    listPrompts: vi.fn().mockResolvedValue([]),
    listPromptVersions: vi.fn().mockResolvedValue([]),
    getPromptVersion: vi.fn().mockResolvedValue({} as any),
    createPrompt: vi.fn().mockResolvedValue({} as any),
    updatePrompt: vi.fn().mockResolvedValue({} as any),
    publishPrompt: vi.fn().mockResolvedValue({} as any),
    archivePrompt: vi.fn().mockResolvedValue({} as any),
    getPromptAnalytics: vi.fn().mockResolvedValue({} as any),
    comparePrompts: vi.fn().mockResolvedValue({} as any),
    listPipelines: vi.fn().mockResolvedValue([]),
    getPipelineDAG: vi.fn().mockResolvedValue({} as any),
    listPipelineRuns: vi.fn().mockResolvedValue([]),
    getPipelineTrace: vi.fn().mockResolvedValue({} as any),
    getPipelineMetrics: vi.fn().mockResolvedValue({} as any),
    listRubrics: vi.fn().mockResolvedValue([]),
    getRubric: vi.fn().mockResolvedValue({} as any),
    createRubric: vi.fn().mockResolvedValue({} as any),
    updateRubric: vi.fn().mockResolvedValue({} as any),
    deleteRubric: vi.fn().mockResolvedValue({ status: 'ok' }),
    addRubricCriterion: vi.fn().mockResolvedValue({} as any),
    updateRubricCriterion: vi.fn().mockResolvedValue({} as any),
    deleteRubricCriterion: vi.fn().mockResolvedValue({} as any),
    listOrgSkills: vi.fn().mockResolvedValue([]),
    getOrgSkill: vi.fn().mockResolvedValue({} as any),
    createOrgSkill: vi.fn().mockResolvedValue({} as any),
    updateOrgSkill: vi.fn().mockResolvedValue({} as any),
    deleteOrgSkill: vi.fn().mockResolvedValue({ status: 'ok' }),
    listOrgCompetencies: vi.fn().mockResolvedValue([]),
    getOrgCompetency: vi.fn().mockResolvedValue({} as any),
    createOrgCompetency: vi.fn().mockResolvedValue({} as any),
    updateOrgCompetency: vi.fn().mockResolvedValue({} as any),
    deleteOrgCompetency: vi.fn().mockResolvedValue({ status: 'ok' }),
    listOrgRubrics: vi.fn().mockResolvedValue([]),
    getOrgRubric: vi.fn().mockResolvedValue({} as any),
    createOrgRubric: vi.fn().mockResolvedValue({} as any),
    updateOrgRubric: vi.fn().mockResolvedValue({} as any),
    deleteOrgRubric: vi.fn().mockResolvedValue({ status: 'ok' }),
    listOrgPromptItems: vi.fn().mockResolvedValue([]),
    getOrgPromptItem: vi.fn().mockResolvedValue({} as any),
    createOrgPromptItem: vi.fn().mockResolvedValue({} as any),
    updateOrgPromptItem: vi.fn().mockResolvedValue({} as any),
    deleteOrgPromptItem: vi.fn().mockResolvedValue({ status: 'ok' }),
    listOrgScenarios: vi.fn().mockResolvedValue([]),
    getOrgScenario: vi.fn().mockResolvedValue({} as any),
    createOrgScenario: vi.fn().mockResolvedValue({} as any),
    updateOrgScenario: vi.fn().mockResolvedValue({} as any),
    deleteOrgScenario: vi.fn().mockResolvedValue({ status: 'ok' }),
    listWorkflowEvents: vi.fn().mockResolvedValue({ events: [], total: 0 }),
    getWorkflowEvent: vi.fn().mockResolvedValue({} as any),
    updateWorkflowEvent: vi.fn().mockResolvedValue({} as any),
    deleteWorkflowEvent: vi.fn().mockResolvedValue({ status: 'ok' }),
    getAttemptAudit: vi.fn().mockResolvedValue({} as any),
    getTelemetryOverview: vi.fn().mockResolvedValue({} as any),
    listTelemetryTraces: vi.fn().mockResolvedValue({ traces: [], total: 0 }),
    getTelemetryTrace: vi.fn().mockResolvedValue(null),
    createAssistantSession: vi.fn().mockResolvedValue({} as any),
    listAssistantSessions: vi.fn().mockResolvedValue([]),
    getAssistantSession: vi.fn().mockResolvedValue({} as any),
    createAssistantTurn: vi.fn().mockResolvedValue({} as any),
    getAssistantTurn: vi.fn().mockResolvedValue({} as any),
    cancelAssistantTurn: vi.fn().mockResolvedValue({} as any),
    streamAssistantTurn: vi.fn().mockReturnValue(() => {}),
    ...overrides,
  } as DataProvider;
};

interface TestProvidersProps {
  children: ReactNode;
  dataProvider?: DataProvider;
}

function TestProviders({ children, dataProvider }: TestProvidersProps) {
  const provider = dataProvider ?? createMockDataProvider();

  return (
    <DataProviderProvider provider={provider}>
      <AuthSessionProvider>
        {children}
      </AuthSessionProvider>
    </DataProviderProvider>
  );
}

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  dataProvider?: DataProvider;
}

export function renderWithProviders(
  ui: React.ReactElement,
  { dataProvider, ...renderOptions }: CustomRenderOptions = {},
) {
  return {
    ...render(ui, { wrapper: ({ children }) => (
      <TestProviders dataProvider={dataProvider}>
        {children}
      </TestProviders>
    ), ...renderOptions }),
    dataProvider,
  };
}

export function renderWithRouter(
  ui: React.ReactElement,
  { dataProvider, initialEntries = ['/'], ...renderOptions }: CustomRenderOptions & { initialEntries?: string[] } = {},
) {
  return {
    ...render(
      <MemoryRouter initialEntries={initialEntries}>
        <DataProviderProvider provider={dataProvider ?? createMockDataProvider()}>
          <AuthSessionProvider>
            {ui}
          </AuthSessionProvider>
        </DataProviderProvider>
      </MemoryRouter>,
      renderOptions,
    ),
    dataProvider,
  };
}

export { render, screen, waitFor, act } from '@testing-library/react';
export { userEvent } from '@testing-library/user-event';
