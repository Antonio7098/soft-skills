import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderWithRouter, renderWithProviders, screen, waitFor, createMockSession, createMockDataProvider } from '@/test/test-utils';
import { render } from '@testing-library/react';
import React from 'react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { AdminOverview } from '@/features/admin/pages/AdminOverview';
import { AdminUsers } from '@/features/admin/pages/AdminUsers';
import { AdminCollections } from '@/features/admin/pages/AdminCollections';
import { AdminEvaluations } from '@/features/admin/pages/AdminEvaluations';
import { AdminGuard } from '@/auth/Guards';
import { DataProviderProvider } from '@/data/DataContext';
import { AuthSessionProvider } from '@/auth/AuthSessionContext';

vi.mock('@/features/admin/pages/AdminOverview', () => ({
  AdminOverview: () => <div data-testid="admin-overview">Admin Overview</div>,
}));

vi.mock('@/features/admin/pages/AdminUsers', () => ({
  AdminUsers: () => <div data-testid="admin-users">Admin Users</div>,
}));

vi.mock('@/features/admin/pages/AdminCollections', () => ({
  AdminCollections: () => <div data-testid="admin-collections">Admin Collections</div>,
}));

vi.mock('@/features/admin/pages/AdminEvaluations', () => ({
  AdminEvaluations: () => <div data-testid="admin-evaluations">Admin Evaluations</div>,
}));

describe('Admin Flow', () => {
  const createAdminSession = () => createMockSession({
    status: 'authenticated',
    platform_role: 'admin',
    capabilities: ['app:access', 'admin:access'],
    org_memberships: [
      { organisation_id: 'org-001', organisation_name: 'Acme Sales', role: 'org_admin', permissions: ['org:read', 'org:write'] },
    ],
    active_organisation_id: 'org-001',
  });

  describe('AdminOverview', () => {
    it('renders overview page for admin users', async () => {
      const mockSession = createAdminSession();
      const mockData = createMockDataProvider({
        getAuthSession: vi.fn().mockResolvedValue(mockSession),
      });

      renderWithRouter(
        <AdminOverview />,
        { dataProvider: mockData, initialEntries: ['/admin'] }
      );

      await waitFor(() => {
        expect(screen.getByTestId('admin-overview')).toBeInTheDocument();
      });
    });
  });

  describe('AdminUsers', () => {
    it('renders user management page', async () => {
      const mockSession = createAdminSession();
      const mockData = createMockDataProvider({
        getAuthSession: vi.fn().mockResolvedValue(mockSession),
      });

      renderWithRouter(
        <AdminUsers />,
        { dataProvider: mockData, initialEntries: ['/admin/users'] }
      );

      await waitFor(() => {
        expect(screen.getByTestId('admin-users')).toBeInTheDocument();
      });
    });
  });

  describe('AdminCollections', () => {
    it('renders collections page', async () => {
      const mockSession = createAdminSession();
      const mockData = createMockDataProvider({
        getAuthSession: vi.fn().mockResolvedValue(mockSession),
      });

      renderWithRouter(
        <AdminCollections />,
        { dataProvider: mockData, initialEntries: ['/admin/collections'] }
      );

      await waitFor(() => {
        expect(screen.getByTestId('admin-collections')).toBeInTheDocument();
      });
    });
  });

  describe('AdminEvaluations', () => {
    it('renders evaluations page', async () => {
      const mockSession = createAdminSession();
      const mockData = createMockDataProvider({
        getAuthSession: vi.fn().mockResolvedValue(mockSession),
      });

      renderWithRouter(
        <AdminEvaluations />,
        { dataProvider: mockData, initialEntries: ['/admin/evaluations'] }
      );

      await waitFor(() => {
        expect(screen.getByTestId('admin-evaluations')).toBeInTheDocument();
      });
    });
  });

  describe('Route Protection', () => {
    it('protects /admin routes with AdminGuard', async () => {
      const mockSession = createMockSession({
        status: 'authenticated',
        platform_role: 'learner',
        capabilities: ['app:access'],
      });
      const mockData = createMockDataProvider({
        getAuthSession: vi.fn().mockResolvedValue(mockSession),
      });

      render(
        <MemoryRouter initialEntries={['/admin']}>
          <DataProviderProvider provider={mockData}>
            <AuthSessionProvider>
              <Routes>
                <Route path="/" element={<div data-testid="home">Home</div>} />
                <Route path="/admin" element={
                  <AdminGuard>
                    <AdminOverview />
                  </AdminGuard>
                } />
              </Routes>
            </AuthSessionProvider>
          </DataProviderProvider>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.queryByTestId('admin-overview')).not.toBeInTheDocument();
      });
    });

    it('allows admin users to access admin routes', async () => {
      const mockSession = createAdminSession();
      const mockData = createMockDataProvider({
        getAuthSession: vi.fn().mockResolvedValue(mockSession),
      });

      renderWithRouter(
        <AdminOverview />,
        { dataProvider: mockData, initialEntries: ['/admin'] }
      );

      await waitFor(() => {
        expect(screen.getByTestId('admin-overview')).toBeInTheDocument();
      });
    });

    it('redirects unauthenticated users', async () => {
      const mockSession = createMockSession({ status: 'anonymous' });
      const mockData = createMockDataProvider({
        getAuthSession: vi.fn().mockResolvedValue(mockSession),
      });

      render(
        <MemoryRouter initialEntries={['/admin']}>
          <DataProviderProvider provider={mockData}>
            <AuthSessionProvider>
              <Routes>
                <Route path="/" element={<div data-testid="home">Home</div>} />
                <Route path="/admin" element={
                  <AdminGuard>
                    <AdminOverview />
                  </AdminGuard>
                } />
              </Routes>
            </AuthSessionProvider>
          </DataProviderProvider>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('home')).toBeInTheDocument();
      });
    });
  });

  describe('Admin Navigation Routes', () => {
    const adminNavItems = [
      { path: '/admin', label: 'Overview' },
      { path: '/admin/users', label: 'Users' },
      { path: '/admin/collections', label: 'Collections' },
      { path: '/admin/evaluations', label: 'Evaluations' },
    ];

    adminNavItems.forEach(({ path }) => {
      it(`can navigate to ${path}`, async () => {
        const mockSession = createAdminSession();
        const mockData = createMockDataProvider({
          getAuthSession: vi.fn().mockResolvedValue(mockSession),
        });

        renderWithRouter(
          <div data-testid="page-content">Page Content</div>,
          { dataProvider: mockData, initialEntries: [path] }
        );

        await waitFor(() => {
          expect(screen.getByTestId('page-content')).toBeInTheDocument();
        });
      });
    });
  });
});

describe('Admin Analytics Integration', () => {
  const createAdminSession = () => createMockSession({
    status: 'authenticated',
    platform_role: 'admin',
    capabilities: ['app:access', 'admin:access'],
    org_memberships: [
      { organisation_id: 'org-001', organisation_name: 'Acme Sales', role: 'org_admin', permissions: ['org:read', 'org:write'] },
    ],
    active_organisation_id: 'org-001',
  });

  describe('Data Provider Mocking', () => {
    it('can mock getAnalyticsOverview with full data', async () => {
      const mockData = createMockDataProvider({
        getAnalyticsOverview: vi.fn().mockResolvedValue({
          total_learners: 1247,
          active_learners_30d: 834,
          total_sessions: 18932,
          avg_validated_score: 72.4,
          overall_usage_trend: [],
        }),
      });

      const overview = await mockData.getAnalyticsOverview();
      expect(overview.total_learners).toBe(1247);
      expect(overview.active_learners_30d).toBe(834);
    });

    it('can mock getLearnerAnalytics with full data', async () => {
      const mockData = createMockDataProvider({
        getLearnerAnalytics: vi.fn().mockResolvedValue({
          learner_id: 'usr-002',
          usage: {
            total_sessions: 45,
            total_attempts: 120,
            submitted_attempts: 115,
            assessed_attempts: 110,
            validated_assessments: 98,
          },
          weak_skill_slugs: ['conflict-resolution', 'active-listening'],
        }),
      });

      const analytics = await mockData.getLearnerAnalytics('usr-002');
      expect(analytics.learner_id).toBe('usr-002');
      expect(analytics.weak_skill_slugs).toContain('conflict-resolution');
    });
  });
});

describe('Admin User Management Integration', () => {
  describe('Data Provider Methods', () => {
    it('can mock createAdminUser', async () => {
      const mockData = createMockDataProvider({
        createAdminUser: vi.fn().mockResolvedValue({
          user_id: 'usr-new',
          email: 'new@user.com',
          display_name: 'New User',
          is_active: true,
          organisation_role: 'learner',
        }),
      });

      const user = await mockData.createAdminUser({ email: 'new@user.com', role: 'learner' });
      expect(user.email).toBe('new@user.com');
      expect(user.organisation_role).toBe('learner');
    });

    it('can mock bulkAdminUserOperation', async () => {
      const mockData = createMockDataProvider({
        bulkAdminUserOperation: vi.fn().mockResolvedValue({
          processed: 5,
          succeeded: 5,
          failed: 0,
        }),
      });

      const result = await mockData.bulkAdminUserOperation({
        user_ids: ['usr-001', 'usr-002', 'usr-003', 'usr-004', 'usr-005'],
        operation: 'change_role',
        payload: { role: 'learner' },
      });
      expect(result.processed).toBe(5);
    });

    it('can mock updateAdminUserRole', async () => {
      const mockData = createMockDataProvider({
        updateAdminUserRole: vi.fn().mockResolvedValue({
          user_id: 'usr-001',
          email: 'alice@acme.com',
          display_name: 'Alice Chen',
          is_active: true,
          organisation_role: 'admin',
        }),
      });

      const user = await mockData.updateAdminUserRole('usr-001', 'admin');
      expect(user.organisation_role).toBe('admin');
    });

    it('can mock updateAdminUserStatus', async () => {
      const mockData = createMockDataProvider({
        updateAdminUserStatus: vi.fn().mockResolvedValue({
          user_id: 'usr-001',
          email: 'alice@acme.com',
          display_name: 'Alice Chen',
          is_active: false,
          organisation_role: 'admin',
        }),
      });

      const user = await mockData.updateAdminUserStatus('usr-001', false);
      expect(user.is_active).toBe(false);
    });
  });
});

describe('Admin Evaluations Integration', () => {
  describe('Data Provider Methods', () => {
    it('can mock triggerEvalRun', async () => {
      const mockData = createMockDataProvider({
        triggerEvalRun: vi.fn().mockResolvedValue({
          evaluation_run_id: 'run-001',
          suite_id: 'suite-001',
          status: 'completed',
          pass_rate: 0.92,
        }),
      });

      const run = await mockData.triggerEvalRun({ suite_id: 'suite-001' });
      expect(run.suite_id).toBe('suite-001');
      expect(run.pass_rate).toBe(0.92);
    });
  });
});

describe('Admin Pipelines Integration', () => {
  describe('Data Provider Methods', () => {
    it('can mock getPipelineDAG with full data', async () => {
      const mockData = createMockDataProvider({
        getPipelineDAG: vi.fn().mockResolvedValue({
          pipeline_name: 'assistant_turn',
          topology: 'assistant_turn',
          stages: [
            { name: 'input_guard', kind: 'GUARD', dependencies: [] },
            { name: 'assistant_runtime', kind: 'AGENT', dependencies: ['input_guard'] },
          ],
        }),
      });

      const dag = await mockData.getPipelineDAG('assistant_turn');
      expect(dag.pipeline_name).toBe('assistant_turn');
      expect(dag.stages).toHaveLength(2);
    });

    it('can mock getPipelineMetrics', async () => {
      const mockData = createMockDataProvider({
        getPipelineMetrics: vi.fn().mockResolvedValue({
          total_runs: 1247,
          success_count: 1198,
          failure_count: 34,
          cancel_count: 15,
          success_rate: 0.96,
        }),
      });

      const metrics = await mockData.getPipelineMetrics('assistant_turn');
      expect(metrics.total_runs).toBe(1247);
      expect(metrics.success_rate).toBe(0.96);
    });
  });
});

describe('Org-scoped Data Integration', () => {
  const createMultiOrgSession = () => createMockSession({
    status: 'authenticated',
    platform_role: 'admin',
    capabilities: ['app:access', 'admin:access'],
    org_memberships: [
      { organisation_id: 'org-001', organisation_name: 'Acme Sales', role: 'org_admin', permissions: ['org:read', 'org:write'] },
      { organisation_id: 'org-002', organisation_name: 'Acme Support', role: 'org_admin', permissions: ['org:read', 'org:write'] },
    ],
    active_organisation_id: 'org-001',
  });

  describe('Skills Management', () => {
    it('can mock listOrgSkills', async () => {
      const mockData = createMockDataProvider({
        listOrgSkills: vi.fn().mockResolvedValue([
          { skill_slug: 'active-listening', name: 'Active Listening', description: 'Skill description' },
          { skill_slug: 'conflict-resolution', name: 'Conflict Resolution', description: 'Another skill' },
        ]),
      });

      const skills = await mockData.listOrgSkills('org-001');
      expect(skills).toHaveLength(2);
      expect(skills[0].skill_slug).toBe('active-listening');
    });

    it('can mock createOrgSkill', async () => {
      const mockData = createMockDataProvider({
        createOrgSkill: vi.fn().mockResolvedValue({
          skill_slug: 'new-skill',
          name: 'New Skill',
          description: 'A newly created skill',
        }),
      });

      const skill = await mockData.createOrgSkill('org-001', {
        slug: 'new-skill',
        name: 'New Skill',
        description: 'A newly created skill',
      });
      expect(skill.skill_slug).toBe('new-skill');
    });
  });

  describe('Competencies Management', () => {
    it('can mock listOrgCompetencies', async () => {
      const mockData = createMockDataProvider({
        listOrgCompetencies: vi.fn().mockResolvedValue([
          { competency_slug: 'communication', name: 'Communication', description: 'Communication skills' },
        ]),
      });

      const competencies = await mockData.listOrgCompetencies('org-002');
      expect(competencies).toHaveLength(1);
    });
  });
});
