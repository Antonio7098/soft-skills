import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createMockSession, createMockDataProvider, mockAuthProfiles } from '@/test/test-utils';
import type { DataProvider } from '@/data/provider';

describe('Mock Data Provider', () => {
  let dataProvider: DataProvider;

  beforeEach(() => {
    vi.clearAllMocks();
    dataProvider = createMockDataProvider();
  });

  describe('Auth Methods', () => {
    it('getAuthSession returns a valid session', async () => {
      const session = await dataProvider.getAuthSession();
      expect(session).toBeDefined();
      expect(session.status).toBe('authenticated');
    });

    it('listAuthProfiles returns mock profiles', async () => {
      const profiles = await dataProvider.listAuthProfiles();
      expect(profiles).toHaveLength(3);
      expect(profiles[0]?.id).toBe('learner-alex');
      expect(profiles[1]?.id).toBe('org-admin-alex');
      expect(profiles[2]?.id).toBe('superadmin-henry');
    });

    it('switchAuthProfile switches to learner profile', async () => {
      const session = await dataProvider.switchAuthProfile('learner-alex');
      expect(session.platform_role).toBe('learner');
    });

    it('switchAuthProfile switches to org-admin profile', async () => {
      const session = await dataProvider.switchAuthProfile('org-admin-alex');
      expect(session.platform_role).toBe('admin');
      expect(session.capabilities).toContain('admin:access');
    });

    it('switchAuthProfile switches to superadmin profile', async () => {
      const session = await dataProvider.switchAuthProfile('superadmin-henry');
      expect(session.platform_role).toBe('superadmin');
      expect(session.capabilities).toContain('platform:superadmin');
    });

    it('switchAuthProfile falls back to org-admin for unknown profile', async () => {
      const session = await dataProvider.switchAuthProfile('unknown-profile');
      expect(session.platform_role).toBe('admin');
    });
  });

  describe('Taxonomy Methods', () => {
    it('getTaxonomy returns seed data', async () => {
      const taxonomy = await dataProvider.getTaxonomy();
      expect(taxonomy).toBeDefined();
      expect(Array.isArray(taxonomy.skills)).toBe(true);
    });
  });

  describe('Admin Collections Methods', () => {
    it('getVerificationQueue returns queue items', async () => {
      const queue = await dataProvider.getVerificationQueue();
      expect(Array.isArray(queue)).toBe(true);
    });
  });

  describe('Admin Evaluations Methods', () => {
    it('listEvalSuites returns evaluation suites', async () => {
      const suites = await dataProvider.listEvalSuites();
      expect(Array.isArray(suites)).toBe(true);
    });

    it('listEvalRuns returns evaluation runs', async () => {
      const runs = await dataProvider.listEvalRuns({ limit: 10 });
      expect(Array.isArray(runs)).toBe(true);
    });
  });

  describe('Admin Prompts Methods', () => {
    it('listPrompts returns prompt list', async () => {
      const prompts = await dataProvider.listPrompts();
      expect(Array.isArray(prompts)).toBe(true);
    });

    it('listPromptVersions returns versions for a prompt', async () => {
      const versions = await dataProvider.listPromptVersions('quick_practice_prompt');
      expect(Array.isArray(versions)).toBe(true);
    });
  });

  describe('Admin Pipelines Methods', () => {
    it('listPipelines returns pipeline list', async () => {
      const pipelines = await dataProvider.listPipelines();
      expect(Array.isArray(pipelines)).toBe(true);
    });
  });

  describe('Org-scoped Methods', () => {
    it('listOrgSkills returns skills for org', async () => {
      const skills = await dataProvider.listOrgSkills('org-001');
      expect(Array.isArray(skills)).toBe(true);
    });

    it('listOrgCompetencies returns competencies for org', async () => {
      const competencies = await dataProvider.listOrgCompetencies('org-001');
      expect(Array.isArray(competencies)).toBe(true);
    });

    it('listOrgRubrics returns rubrics for org', async () => {
      const rubrics = await dataProvider.listOrgRubrics('org-001');
      expect(Array.isArray(rubrics)).toBe(true);
    });

    it('listOrgPromptItems returns prompt items for org', async () => {
      const items = await dataProvider.listOrgPromptItems('org-001');
      expect(Array.isArray(items)).toBe(true);
    });

    it('listOrgScenarios returns scenarios for org', async () => {
      const scenarios = await dataProvider.listOrgScenarios('org-001');
      expect(Array.isArray(scenarios)).toBe(true);
    });
  });

  describe('Progress Methods', () => {
    it('getAttemptHistory returns history for user', async () => {
      const history = await dataProvider.getAttemptHistory('user-001');
      expect(Array.isArray(history)).toBe(true);
    });

    it('getCompetencyProgress returns progress for user', async () => {
      const progress = await dataProvider.getCompetencyProgress('user-001');
      expect(Array.isArray(progress)).toBe(true);
    });
  });

  describe('Assistant Methods', () => {
    it('listAssistantSessions returns sessions', async () => {
      const sessions = await dataProvider.listAssistantSessions();
      expect(Array.isArray(sessions)).toBe(true);
    });

    it('createAssistantSession creates new session', async () => {
      const session = await dataProvider.createAssistantSession();
      expect(session).toBeDefined();
    });
  });
});

describe('Auth Session Mock Data', () => {
  it('mockAuthProfiles contains learner profile', () => {
    const learnerProfile = mockAuthProfiles.find(p => p.id === 'learner-alex');
    expect(learnerProfile).toBeDefined();
    expect(learnerProfile?.session.platform_role).toBe('learner');
  });

  it('mockAuthProfiles contains org-admin profile', () => {
    const adminProfile = mockAuthProfiles.find(p => p.id === 'org-admin-alex');
    expect(adminProfile).toBeDefined();
    expect(adminProfile?.session.capabilities).toContain('admin:access');
  });

  it('mockAuthProfiles contains superadmin profile', () => {
    const superadminProfile = mockAuthProfiles.find(p => p.id === 'superadmin-henry');
    expect(superadminProfile).toBeDefined();
    expect(superadminProfile?.session.capabilities).toContain('platform:superadmin');
  });

  it('superadmin has multiple org memberships', () => {
    const superadminProfile = mockAuthProfiles.find(p => p.id === 'superadmin-henry');
    expect(superadminProfile?.session.org_memberships).toHaveLength(2);
  });
});

describe('Session Factory', () => {
  it('createMockSession creates valid session', () => {
    const session = createMockSession();
    expect(session.status).toBe('authenticated');
    expect(session.actor).toBeDefined();
    expect(session.actor?.email).toBe('test@example.com');
  });

  it('createMockSession allows overrides', () => {
    const session = createMockSession({
      platform_role: 'superadmin',
      active_organisation_id: 'org-999',
    });
    expect(session.platform_role).toBe('superadmin');
    expect(session.active_organisation_id).toBe('org-999');
  });

  it('createMockSession with multiple org memberships', () => {
    const session = createMockSession({
      org_memberships: [
        { organisation_id: 'org-001', organisation_name: 'Org 1', role: 'org_admin', permissions: ['org:read'] },
        { organisation_id: 'org-002', organisation_name: 'Org 2', role: 'member', permissions: [] },
      ],
    });
    expect(session.org_memberships).toHaveLength(2);
  });
});

describe('Mock Data Provider Methods', () => {
  let dataProvider: DataProvider;

  beforeEach(() => {
    vi.clearAllMocks();
    dataProvider = createMockDataProvider();
  });

  it('switchAuthProfile is called with correct profile id', async () => {
    await dataProvider.switchAuthProfile('learner-alex');
    expect(dataProvider.switchAuthProfile).toHaveBeenCalledWith('learner-alex');
  });

  it('listAuthProfiles is called and returns profiles', async () => {
    const profiles = await dataProvider.listAuthProfiles();
    expect(dataProvider.listAuthProfiles).toHaveBeenCalled();
    expect(profiles.length).toBeGreaterThan(0);
  });

  it('getAuthSession returns authenticated session', async () => {
    const session = await dataProvider.getAuthSession();
    expect(session.status).toBe('authenticated');
  });

  it('createAdminUser is mockable', async () => {
    const mockDataProvider = createMockDataProvider({
      createAdminUser: vi.fn().mockResolvedValue({
        user_id: 'usr-new',
        email: 'new@user.com',
        display_name: 'New User',
        is_active: true,
        organisation_role: 'learner',
      }),
    });

    const user = await mockDataProvider.createAdminUser({ email: 'new@user.com', role: 'learner' });
    expect(user.email).toBe('new@user.com');
  });

  it('bulkAdminUserOperation is mockable', async () => {
    const mockDataProvider = createMockDataProvider({
      bulkAdminUserOperation: vi.fn().mockResolvedValue({
        processed: 2,
        succeeded: 2,
        failed: 0,
      }),
    });

    const result = await mockDataProvider.bulkAdminUserOperation({
      user_ids: ['usr-001', 'usr-002'],
      operation: 'deactivate',
    });
    expect(result.processed).toBe(2);
  });

  it('updateAdminUserRole is mockable', async () => {
    const mockDataProvider = createMockDataProvider({
      updateAdminUserRole: vi.fn().mockResolvedValue({
        user_id: 'usr-001',
        email: 'alice@acme.com',
        display_name: 'Alice Chen',
        is_active: true,
        organisation_role: 'admin',
      }),
    });

    const user = await mockDataProvider.updateAdminUserRole('usr-001', 'admin');
    expect(user.organisation_role).toBe('admin');
  });

  it('updateAdminUserStatus is mockable', async () => {
    const mockDataProvider = createMockDataProvider({
      updateAdminUserStatus: vi.fn().mockResolvedValue({
        user_id: 'usr-001',
        email: 'alice@acme.com',
        display_name: 'Alice Chen',
        is_active: false,
        organisation_role: 'admin',
      }),
    });

    const user = await mockDataProvider.updateAdminUserStatus('usr-001', false);
    expect(user.is_active).toBe(false);
  });

  it('getAnalyticsOverview is mockable with full data', async () => {
    const mockDataProvider = createMockDataProvider({
      getAnalyticsOverview: vi.fn().mockResolvedValue({
        total_learners: 1247,
        active_learners_30d: 834,
        total_sessions: 18932,
        avg_validated_score: 72.4,
        overall_usage_trend: [],
      }),
    });

    const overview = await mockDataProvider.getAnalyticsOverview();
    expect(overview.total_learners).toBe(1247);
  });

  it('getLearnerAnalytics is mockable with full data', async () => {
    const mockDataProvider = createMockDataProvider({
      getLearnerAnalytics: vi.fn().mockResolvedValue({
        learner_id: 'usr-002',
        usage: { total_sessions: 45 },
        weak_skill_slugs: ['conflict-resolution'],
      }),
    });

    const analytics = await mockDataProvider.getLearnerAnalytics('usr-002');
    expect(analytics.learner_id).toBe('usr-002');
  });

  it('getPipelineDAG is mockable with full data', async () => {
    const mockDataProvider = createMockDataProvider({
      getPipelineDAG: vi.fn().mockResolvedValue({
        pipeline_name: 'assistant_turn',
        stages: [
          { name: 'input_guard', kind: 'GUARD', dependencies: [] },
        ],
      }),
    });

    const dag = await mockDataProvider.getPipelineDAG('assistant_turn');
    expect(dag.pipeline_name).toBe('assistant_turn');
    expect(dag.stages.length).toBe(1);
  });

  it('getPipelineMetrics is mockable with full data', async () => {
    const mockDataProvider = createMockDataProvider({
      getPipelineMetrics: vi.fn().mockResolvedValue({
        total_runs: 1247,
        success_count: 1198,
        failure_count: 34,
      }),
    });

    const metrics = await mockDataProvider.getPipelineMetrics('assistant_turn');
    expect(metrics.total_runs).toBe(1247);
  });

  it('triggerEvalRun is mockable', async () => {
    const mockDataProvider = createMockDataProvider({
      triggerEvalRun: vi.fn().mockResolvedValue({
        evaluation_run_id: 'run-001',
        suite_id: 'suite-001',
        status: 'completed',
      }),
    });

    const run = await mockDataProvider.triggerEvalRun({ suite_id: 'suite-001' });
    expect(run.suite_id).toBe('suite-001');
  });

  it('setActiveOrganisation is mockable', async () => {
    const updatedSession = createMockSession({ active_organisation_id: 'org-002' });
    const mockDataProvider = createMockDataProvider({
      setActiveOrganisation: vi.fn().mockResolvedValue(updatedSession),
    });

    const session = await mockDataProvider.setActiveOrganisation('org-002');
    expect(session.active_organisation_id).toBe('org-002');
  });

  it('createOrganisation is mockable', async () => {
    const mockDataProvider = createMockDataProvider({
      createOrganisation: vi.fn().mockResolvedValue({
        id: 'org-new',
        name: 'New Org',
        slug: 'new-org',
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      }),
    });

    const org = await mockDataProvider.createOrganisation({ name: 'New Org', slug: 'new-org' });
    expect(org.name).toBe('New Org');
    expect(org.slug).toBe('new-org');
    expect(mockDataProvider.createOrganisation).toHaveBeenCalledWith({ name: 'New Org', slug: 'new-org' });
  });

  it('listOrganisations is mockable', async () => {
    const mockDataProvider = createMockDataProvider({
      listOrganisations: vi.fn().mockResolvedValue([
        { id: 'org-001', name: 'Acme Sales', slug: 'acme-sales', member_count: 3 },
        { id: 'org-002', name: 'Acme Support', slug: 'acme-support', member_count: 5 },
      ]),
    });

    const orgs = await mockDataProvider.listOrganisations();
    expect(orgs).toHaveLength(2);
    expect(orgs[0].name).toBe('Acme Sales');
    expect(orgs[1].member_count).toBe(5);
  });
});
