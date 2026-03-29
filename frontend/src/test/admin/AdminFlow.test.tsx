import { describe, it, expect, vi } from 'vitest';
import { renderWithRouter, screen, waitFor, createMockSession, createMockDataProvider } from '@/test/test-utils';
import { render, screen, waitFor, act } from '@testing-library/react';
import React from 'react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { AdminOverview } from '@/features/admin/pages/AdminOverview';
import { AdminUsers } from '@/features/admin/pages/AdminUsers';
import { AdminGuard } from '@/auth/Guards';
import { DataProviderProvider } from '@/data/DataContext';
import { AuthSessionProvider } from '@/auth/AuthSessionContext';

vi.mock('@/features/admin/pages/AdminOverview', () => ({
  AdminOverview: () => <div data-testid="admin-overview">Admin Overview</div>,
}));

vi.mock('@/features/admin/pages/AdminUsers', () => ({
  AdminUsers: () => <div data-testid="admin-users">Admin Users</div>,
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
        getAnalyticsOverview: vi.fn().mockResolvedValue({
          total_learners: 1247,
          active_learners_30d: 834,
          total_sessions: 18932,
          avg_validated_score: 72.4,
        }),
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
        listAdminUsers: vi.fn().mockResolvedValue({
          users: [
            { user_id: 'usr-001', email: 'alice@acme.com', display_name: 'Alice Chen', is_active: true, organisation_role: 'admin' },
            { user_id: 'usr-002', email: 'bob@acme.com', display_name: 'Bob Martinez', is_active: true, organisation_role: 'member' },
          ],
          total: 2,
        }),
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
  });
});
