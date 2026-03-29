import { describe, it, expect, vi } from 'vitest';
import { renderWithRouter, renderWithProviders, screen, waitFor, createMockSession, createMockDataProvider } from '@/test/test-utils';
import { AdminScopeProvider, useAdminScope } from '@/auth/AdminScopeContext';
import { AuthSessionProvider, useAuthSession } from '@/auth/AuthSessionContext';
import { render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';

describe('AdminScopeContext', () => {
  describe('initialization', () => {
    it('provides available organisations from session', async () => {
      const mockSession = createMockSession({
        org_memberships: [
          { organisation_id: 'org-001', organisation_name: 'Acme Sales', role: 'org_admin', permissions: ['org:read', 'org:write'] },
          { organisation_id: 'org-002', organisation_name: 'Acme Support', role: 'member', permissions: ['org:read'] },
        ],
        active_organisation_id: 'org-001',
      });
      const mockData = createMockDataProvider({
        getAuthSession: vi.fn().mockResolvedValue(mockSession),
      });

      renderWithProviders(
        <AdminScopeProvider>
          <AvailableOrgsComponent />
        </AdminScopeProvider>,
        { dataProvider: mockData }
      );

      await waitFor(() => {
        const count = screen.getByTestId('available-orgs-count');
        expect(count).toHaveTextContent('2');
      });
    });

    it('resolves organisationId from route param first', async () => {
      const mockSession = createMockSession({
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
          <Route path="/admin/orgs/:organisationId/*" element={
            <AdminScopeProvider>
              <OrgIdComponent />
            </AdminScopeProvider>
          } />
        </Routes>,
        { dataProvider: mockData, initialEntries: ['/admin/orgs/org-002/users'] }
      );

      await waitFor(() => {
        expect(screen.getByTestId('org-id')).toHaveTextContent('org-002');
        expect(screen.getByTestId('route-org-id')).toHaveTextContent('org-002');
      });
    });

    it('falls back to session active_organisation_id when no route param', async () => {
      const mockSession = createMockSession({
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
          <Route path="/admin" element={
            <AdminScopeProvider>
              <OrgIdComponent />
            </AdminScopeProvider>
          } />
        </Routes>,
        { dataProvider: mockData, initialEntries: ['/admin'] }
      );

      await waitFor(() => {
        expect(screen.getByTestId('org-id')).toHaveTextContent('org-001');
      });
    });

    it('falls back to first org membership when no active org is set', async () => {
      const mockSession = createMockSession({
        org_memberships: [
          { organisation_id: 'org-001', organisation_name: 'Acme Sales', role: 'member', permissions: ['org:read'] },
        ],
        active_organisation_id: null,
      });
      const mockData = createMockDataProvider({
        getAuthSession: vi.fn().mockResolvedValue(mockSession),
      });

      renderWithProviders(
        <AdminScopeProvider>
          <OrgIdComponent />
        </AdminScopeProvider>,
        { dataProvider: mockData }
      );

      await waitFor(() => {
        expect(screen.getByTestId('org-id')).toHaveTextContent('org-001');
      });
    });
  });

  describe('can() permission check', () => {
    it('returns true when user has the permission', async () => {
      const mockSession = createMockSession({
        org_memberships: [
          { organisation_id: 'org-001', organisation_name: 'Acme Sales', role: 'org_admin', permissions: ['org:read', 'org:write'] },
        ],
        active_organisation_id: 'org-001',
        platform_role: 'admin',
      });
      const mockData = createMockDataProvider({
        getAuthSession: vi.fn().mockResolvedValue(mockSession),
      });

      renderWithProviders(
        <AdminScopeProvider>
          <CanComponent permission="org:read" />
        </AdminScopeProvider>,
        { dataProvider: mockData }
      );

      await waitFor(() => {
        expect(screen.getByTestId('can-result')).toHaveTextContent('true');
      });
    });

    it('returns false when user lacks the permission', async () => {
      const mockSession = createMockSession({
        org_memberships: [
          { organisation_id: 'org-001', organisation_name: 'Acme Sales', role: 'member', permissions: ['org:read'] },
        ],
        active_organisation_id: 'org-001',
        platform_role: 'learner',
      });
      const mockData = createMockDataProvider({
        getAuthSession: vi.fn().mockResolvedValue(mockSession),
      });

      renderWithProviders(
        <AdminScopeProvider>
          <CanComponent permission="org:write" />
        </AdminScopeProvider>,
        { dataProvider: mockData }
      );

      await waitFor(() => {
        expect(screen.getByTestId('can-result')).toHaveTextContent('false');
      });
    });

    it('superadmin bypasses all permission checks', async () => {
      const mockSession = createMockSession({
        platform_role: 'superadmin',
        capabilities: ['app:access', 'admin:access', 'platform:superadmin'],
        org_memberships: [
          { organisation_id: 'org-001', organisation_name: 'Acme Sales', role: 'member', permissions: [] },
        ],
        active_organisation_id: 'org-001',
      });
      const mockData = createMockDataProvider({
        getAuthSession: vi.fn().mockResolvedValue(mockSession),
      });

      renderWithProviders(
        <AdminScopeProvider>
          <CanComponent permission="org:write" />
        </AdminScopeProvider>,
        { dataProvider: mockData }
      );

      await waitFor(() => {
        expect(screen.getByTestId('can-result')).toHaveTextContent('true');
      });
    });

    it('returns false when session is not loaded', async () => {
      const mockData = createMockDataProvider({
        getAuthSession: vi.fn().mockImplementation(() => new Promise(() => {})),
      });

      renderWithProviders(
        <AdminScopeProvider>
          <CanComponent permission="org:read" />
        </AdminScopeProvider>,
        { dataProvider: mockData }
      );

      await waitFor(() => {
        expect(screen.getByTestId('can-result')).toHaveTextContent('false');
      });
    });
  });

  describe('activeOrganisation', () => {
    it('returns the organisation membership for the resolved org', async () => {
      const mockSession = createMockSession({
        org_memberships: [
          { organisation_id: 'org-001', organisation_name: 'Acme Sales', role: 'org_admin', permissions: ['org:read', 'org:write'] },
        ],
        active_organisation_id: 'org-001',
      });
      const mockData = createMockDataProvider({
        getAuthSession: vi.fn().mockResolvedValue(mockSession),
      });

      renderWithProviders(
        <AdminScopeProvider>
          <ActiveOrgInfoComponent />
        </AdminScopeProvider>,
        { dataProvider: mockData }
      );

      await waitFor(() => {
        expect(screen.getByTestId('active-org-info')).toHaveTextContent('Acme Sales');
      });
    });
  });

  describe('routeOrganisationId', () => {
    it('returns null for routes without org param', async () => {
      const mockSession = createMockSession();
      const mockData = createMockDataProvider({
        getAuthSession: vi.fn().mockResolvedValue(mockSession),
      });

      renderWithRouter(
        <Routes>
          <Route path="/admin/users" element={
            <AdminScopeProvider>
              <RouteOrgIdComponent />
            </AdminScopeProvider>
          } />
        </Routes>,
        { dataProvider: mockData, initialEntries: ['/admin/users'] }
      );

      await waitFor(() => {
        expect(screen.getByTestId('route-org-id')).toHaveTextContent('null');
      });
    });

    it('ignores Rails-style :id route params', async () => {
      const mockSession = createMockSession();
      const mockData = createMockDataProvider({
        getAuthSession: vi.fn().mockResolvedValue(mockSession),
      });

      renderWithRouter(
        <Routes>
          <Route path="/admin/orgs/:id/users" element={
            <AdminScopeProvider>
              <RouteOrgIdComponent />
            </AdminScopeProvider>
          } />
        </Routes>,
        { dataProvider: mockData, initialEntries: ['/admin/orgs/:id/users'] }
      );

      await waitFor(() => {
        expect(screen.getByTestId('route-org-id')).toHaveTextContent('null');
      });
    });

    it('ignores route params with braces', async () => {
      const mockSession = createMockSession();
      const mockData = createMockDataProvider({
        getAuthSession: vi.fn().mockResolvedValue(mockSession),
      });

      renderWithRouter(
        <Routes>
          <Route path="/admin/orgs/{id}/users" element={
            <AdminScopeProvider>
              <RouteOrgIdComponent />
            </AdminScopeProvider>
          } />
        </Routes>,
        { dataProvider: mockData, initialEntries: ['/admin/orgs/{id}/users'] }
      );

      await waitFor(() => {
        expect(screen.getByTestId('route-org-id')).toHaveTextContent('null');
      });
    });
  });

  describe('setActiveOrganisation integration', () => {
    it('calls setActiveOrganisation when route org differs from session', async () => {
      const mockSession = createMockSession({
        org_memberships: [
          { organisation_id: 'org-001', organisation_name: 'Acme Sales', role: 'org_admin', permissions: ['org:read', 'org:write'] },
          { organisation_id: 'org-002', organisation_name: 'Acme Support', role: 'org_admin', permissions: ['org:read', 'org:write'] },
        ],
        active_organisation_id: 'org-001',
      });
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
          <Route path="/admin/orgs/:organisationId/*" element={
            <AdminScopeProvider>
              <div>Content</div>
            </AdminScopeProvider>
          } />
        </Routes>,
        { dataProvider: mockData, initialEntries: ['/admin/orgs/org-002/users'] }
      );

      await waitFor(() => {
        expect(mockData.setActiveOrganisation).toHaveBeenCalledWith('org-002');
      });
    });

    it('does not call setActiveOrganisation when already set to same org', async () => {
      const mockSession = createMockSession({
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
          <Route path="/admin/orgs/:organisationId/*" element={
            <AdminScopeProvider>
              <div>Content</div>
            </AdminScopeProvider>
          } />
        </Routes>,
        { dataProvider: mockData, initialEntries: ['/admin/orgs/org-001/users'] }
      );

      await waitFor(() => {
        expect(mockData.setActiveOrganisation).not.toHaveBeenCalled();
      });
    });
  });
});

function AvailableOrgsComponent() {
  const { availableOrganisations } = useAdminScope();
  return <span data-testid="available-orgs-count">{availableOrganisations.length}</span>;
}

function OrgIdComponent() {
  const { organisationId, routeOrganisationId } = useAdminScope();
  return (
    <div>
      <span data-testid="org-id">{organisationId}</span>
      <span data-testid="route-org-id">{routeOrganisationId ?? 'null'}</span>
    </div>
  );
}

function CanComponent({ permission }: { permission: string }) {
  const { can } = useAdminScope();
  return <span data-testid="can-result">{String(can(permission))}</span>;
}

function ActiveOrgInfoComponent() {
  const { activeOrganisation } = useAdminScope();
  return <span data-testid="active-org-info">{activeOrganisation?.organisation_name ?? 'null'}</span>;
}

function RouteOrgIdComponent() {
  const { routeOrganisationId } = useAdminScope();
  return <span data-testid="route-org-id">{routeOrganisationId ?? 'null'}</span>;
}
