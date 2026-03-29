import { describe, it, expect, vi } from 'vitest';
import { renderWithRouter, screen, waitFor, createMockSession, createMockDataProvider } from '@/test/test-utils';
import React from 'react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { AdminScopeProvider, useAdminScope } from '@/auth/AdminScopeContext';
import { AdminGuard } from '@/auth/Guards';

describe('Org Scoping', () => {
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

  describe('AdminScopeProvider resolution', () => {
    it('resolves organisationId from URL param', async () => {
      const mockSession = createMultiOrgSession();
      const mockData = createMockDataProvider({
        getAuthSession: vi.fn().mockResolvedValue(mockSession),
      });

      renderWithRouter(
        <Routes>
          <Route path="/admin/orgs/:organisationId/skills" element={
            <AdminScopeProvider>
              <OrgIdReporter />
            </AdminScopeProvider>
          } />
        </Routes>,
        { dataProvider: mockData, initialEntries: ['/admin/orgs/org-002/skills'] }
      );

      await waitFor(() => {
        expect(screen.getByTestId('org-id')).toHaveTextContent('org-002');
      });
    });

    it('falls back to active organisation when no URL param', async () => {
      const mockSession = createMultiOrgSession();
      const mockData = createMockDataProvider({
        getAuthSession: vi.fn().mockResolvedValue(mockSession),
      });

      renderWithRouter(
        <Routes>
          <Route path="/admin/skills" element={
            <AdminScopeProvider>
              <OrgIdReporter />
            </AdminScopeProvider>
          } />
        </Routes>,
        { dataProvider: mockData, initialEntries: ['/admin/skills'] }
      );

      await waitFor(() => {
        expect(screen.getByTestId('org-id')).toHaveTextContent('org-001');
      });
    });
  });

  describe('Permission enforcement via AdminGuard', () => {
    it('denies access to org user is not member of', async () => {
      const mockSession = createMockSession({
        status: 'authenticated',
        platform_role: 'admin',
        capabilities: ['app:access', 'admin:access'],
        org_memberships: [
          { organisation_id: 'org-001', organisation_name: 'Acme Sales', role: 'org_admin', permissions: ['org:read', 'org:write'] },
        ],
        active_organisation_id: 'org-001',
      });
      const mockData = createMockDataProvider({
        getAuthSession: vi.fn().mockResolvedValue(mockSession),
      });

      renderWithRouter(
        <Routes>
          <Route path="/admin/orgs/:organisationId" element={
            <AdminGuard>
              <div data-testid="should-not-render">Content</div>
            </AdminGuard>
          } />
        </Routes>,
        { dataProvider: mockData, initialEntries: ['/admin/orgs/org-999'] }
      );

      await waitFor(() => {
        expect(screen.getByText('Organisation Access Denied')).toBeInTheDocument();
      });
    });

    it('allows access when user has membership in the org', async () => {
      const mockSession = createMultiOrgSession();
      const mockData = createMockDataProvider({
        getAuthSession: vi.fn().mockResolvedValue(mockSession),
      });

      renderWithRouter(
        <Routes>
          <Route path="/admin/orgs/:organisationId" element={
            <AdminGuard>
              <div data-testid="admin-content">Content</div>
            </AdminGuard>
          } />
        </Routes>,
        { dataProvider: mockData, initialEntries: ['/admin/orgs/org-002'] }
      );

      await waitFor(() => {
        expect(screen.getByTestId('admin-content')).toBeInTheDocument();
      });
    });

    it('superadmin bypasses org membership check', async () => {
      const mockSession = createMockSession({
        status: 'authenticated',
        platform_role: 'superadmin',
        capabilities: ['app:access', 'admin:access', 'platform:superadmin'],
        org_memberships: [
          { organisation_id: 'org-001', organisation_name: 'Acme Sales', role: 'org_admin', permissions: ['org:read', 'org:write'] },
        ],
        active_organisation_id: 'org-001',
      });
      const mockData = createMockDataProvider({
        getAuthSession: vi.fn().mockResolvedValue(mockSession),
      });

      renderWithRouter(
        <Routes>
          <Route path="/admin/orgs/:organisationId" element={
            <AdminGuard>
              <div data-testid="superadmin-content">Content</div>
            </AdminGuard>
          } />
        </Routes>,
        { dataProvider: mockData, initialEntries: ['/admin/orgs/org-001'] }
      );

      await waitFor(() => {
        expect(screen.getByTestId('superadmin-content')).toBeInTheDocument();
      });
    });
  });

  describe('setActiveOrganisation', () => {
    it('calls setActiveOrganisation when route org differs from session', async () => {
      const mockSession = createMultiOrgSession();
      const updatedSession = createMockSession({
        ...mockSession,
        active_organisation_id: 'org-002',
      });
      const mockData = createMockDataProvider({
        getAuthSession: vi.fn().mockResolvedValue(mockSession),
        setActiveOrganisation: vi.fn().mockResolvedValue(updatedSession),
      });

      renderWithRouter(
        <Routes>
          <Route path="/admin/orgs/:organisationId/skills" element={
            <AdminScopeProvider>
              <div>Content</div>
            </AdminScopeProvider>
          } />
        </Routes>,
        { dataProvider: mockData, initialEntries: ['/admin/orgs/org-002/skills'] }
      );

      await waitFor(() => {
        expect(mockData.setActiveOrganisation).toHaveBeenCalledWith('org-002');
      });
    });

    it('does not call setActiveOrganisation when already on same org', async () => {
      const mockSession = createMultiOrgSession();
      const mockData = createMockDataProvider({
        getAuthSession: vi.fn().mockResolvedValue(mockSession),
      });

      renderWithRouter(
        <Routes>
          <Route path="/admin/orgs/:organisationId/skills" element={
            <AdminScopeProvider>
              <div>Content</div>
            </AdminScopeProvider>
          } />
        </Routes>,
        { dataProvider: mockData, initialEntries: ['/admin/orgs/org-001/skills'] }
      );

      await waitFor(() => {
        expect(mockData.setActiveOrganisation).not.toHaveBeenCalled();
      });
    });
  });
});

function OrgIdReporter() {
  const { organisationId } = useAdminScope();
  return <span data-testid="org-id">{organisationId}</span>;
}
