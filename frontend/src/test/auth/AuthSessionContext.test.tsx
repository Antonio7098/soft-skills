import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderWithProviders, screen, waitFor, createMockSession, createMockDataProvider } from '@/test/test-utils';
import { AuthSessionProvider, useAuthSession } from '@/auth/AuthSessionContext';
import { DataProviderProvider } from '@/data/DataContext';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';

describe('AuthSessionContext', () => {
  describe('initialization', () => {
    it('loads session and auth profiles on mount', async () => {
      const mockData = createMockDataProvider();
      renderWithProviders(
        <AuthSessionProvider>
          <TestComponent />
        </AuthSessionProvider>,
        { dataProvider: mockData }
      );

      await waitFor(() => {
        expect(mockData.getAuthSession).toHaveBeenCalled();
        expect(mockData.listAuthProfiles).toHaveBeenCalled();
      });
    });

    it('exposes session, loading, and error state', async () => {
      const mockData = createMockDataProvider();
      renderWithProviders(
        <AuthSessionProvider>
          <TestComponent />
        </AuthSessionProvider>,
        { dataProvider: mockData }
      );

      await waitFor(() => {
        expect(screen.getByTestId('auth-loading')).toHaveTextContent('false');
        expect(screen.getByTestId('auth-session')).toBeInTheDocument();
      });
    });

    it('sets isAuthenticated true when session status is authenticated', async () => {
      const mockSession = createMockSession({ status: 'authenticated' });
      const mockData = createMockDataProvider({
        getAuthSession: vi.fn().mockResolvedValue(mockSession),
      });

      renderWithProviders(
        <AuthSessionProvider>
          <TestComponent />
        </AuthSessionProvider>,
        { dataProvider: mockData }
      );

      await waitFor(() => {
        expect(screen.getByTestId('auth-is-authenticated')).toHaveTextContent('true');
      });
    });

    it('sets isAuthenticated false when session status is anonymous', async () => {
      const mockSession = createMockSession({ status: 'anonymous' });
      const mockData = createMockDataProvider({
        getAuthSession: vi.fn().mockResolvedValue(mockSession),
      });

      renderWithProviders(
        <AuthSessionProvider>
          <TestComponent />
        </AuthSessionProvider>,
        { dataProvider: mockData }
      );

      await waitFor(() => {
        expect(screen.getByTestId('auth-is-authenticated')).toHaveTextContent('false');
      });
    });

    it('sets isAdmin true when session has admin:access capability', async () => {
      const mockSession = createMockSession({
        capabilities: ['app:access', 'admin:access'],
        platform_role: 'admin',
      });
      const mockData = createMockDataProvider({
        getAuthSession: vi.fn().mockResolvedValue(mockSession),
      });

      renderWithProviders(
        <AuthSessionProvider>
          <TestComponent />
        </AuthSessionProvider>,
        { dataProvider: mockData }
      );

      await waitFor(() => {
        expect(screen.getByTestId('auth-is-admin')).toHaveTextContent('true');
      });
    });

    it('sets isAdmin false when session lacks admin:access capability', async () => {
      const mockSession = createMockSession({
        capabilities: ['app:access'],
        platform_role: 'learner',
      });
      const mockData = createMockDataProvider({
        getAuthSession: vi.fn().mockResolvedValue(mockSession),
      });

      renderWithProviders(
        <AuthSessionProvider>
          <TestComponent />
        </AuthSessionProvider>,
        { dataProvider: mockData }
      );

      await waitFor(() => {
        expect(screen.getByTestId('auth-is-admin')).toHaveTextContent('false');
      });
    });

    it('handles session load error', async () => {
      const mockData = createMockDataProvider({
        getAuthSession: vi.fn().mockRejectedValue(new Error('Network error')),
      });

      renderWithProviders(
        <AuthSessionProvider>
          <TestComponent />
        </AuthSessionProvider>,
        { dataProvider: mockData }
      );

      await waitFor(() => {
        expect(screen.getByTestId('auth-error')).toBeInTheDocument();
      });
    });
  });

  describe('setActiveOrganisation', () => {
    it('updates active organisation', async () => {
      const mockSession = createMockSession();
      const updatedSession = createMockSession({
        active_organisation_id: 'org-002',
      });
      const mockData = createMockDataProvider({
        getAuthSession: vi.fn().mockResolvedValue(mockSession),
        setActiveOrganisation: vi.fn().mockResolvedValue(updatedSession),
      });

      renderWithProviders(
        <AuthSessionProvider>
          <SetOrgComponent />
        </AuthSessionProvider>,
        { dataProvider: mockData }
      );

      await waitFor(() => {
        expect(screen.getByTestId('org-ready')).toBeInTheDocument();
      });

      await act(async () => {
        await screen.getByTestId('set-org-btn').click();
      });

      await waitFor(() => {
        expect(mockData.setActiveOrganisation).toHaveBeenCalledWith('org-002');
      });
    });
  });

  describe('switchAuthProfile', () => {
    it('switches to different auth profile', async () => {
      const mockSession = createMockSession();
      const orgAdminSession = createMockSession({
        platform_role: 'admin',
        capabilities: ['app:access', 'admin:access'],
      });
      const mockData = createMockDataProvider({
        getAuthSession: vi.fn().mockResolvedValue(mockSession),
        switchAuthProfile: vi.fn().mockResolvedValue(orgAdminSession),
      });

      renderWithProviders(
        <AuthSessionProvider>
          <SwitchProfileComponent />
        </AuthSessionProvider>,
        { dataProvider: mockData }
      );

      await waitFor(() => {
        expect(screen.getByTestId('profile-ready')).toBeInTheDocument();
      });

      await act(async () => {
        await screen.getByTestId('switch-profile-btn').click();
      });

      await waitFor(() => {
        expect(mockData.switchAuthProfile).toHaveBeenCalledWith('org-admin-alex');
      });
    });
  });

  describe('refreshSession', () => {
    it('reloads the session', async () => {
      const mockSession = createMockSession();
      const mockData = createMockDataProvider({
        getAuthSession: vi.fn().mockResolvedValue(mockSession),
      });

      renderWithProviders(
        <AuthSessionProvider>
          <RefreshComponent />
        </AuthSessionProvider>,
        { dataProvider: mockData }
      );

      await waitFor(() => {
        expect(screen.getByTestId('refresh-ready')).toBeInTheDocument();
      });

      const callCountBefore = mockData.getAuthSession.mock.calls.length;

      await act(async () => {
        await screen.getByTestId('refresh-btn').click();
      });

      expect(mockData.getAuthSession.mock.calls.length).toBeGreaterThan(callCountBefore);
    });
  });

  describe('activeOrganisation', () => {
    it('returns the active organisation from org_memberships', async () => {
      const mockSession = createMockSession({
        active_organisation_id: 'org-001',
        org_memberships: [
          { organisation_id: 'org-001', organisation_name: 'Acme Sales', role: 'member', permissions: [] },
          { organisation_id: 'org-002', organisation_name: 'Acme Support', role: 'member', permissions: [] },
        ],
      });
      const mockData = createMockDataProvider({
        getAuthSession: vi.fn().mockResolvedValue(mockSession),
      });

      renderWithProviders(
        <AuthSessionProvider>
          <ActiveOrgComponent />
        </AuthSessionProvider>,
        { dataProvider: mockData }
      );

      await waitFor(() => {
        expect(screen.getByTestId('active-org-name')).toHaveTextContent('Acme Sales');
      });
    });

    it('returns null when no active organisation is set', async () => {
      const mockSession = createMockSession({
        active_organisation_id: null,
        org_memberships: [],
      });
      const mockData = createMockDataProvider({
        getAuthSession: vi.fn().mockResolvedValue(mockSession),
      });

      renderWithProviders(
        <AuthSessionProvider>
          <ActiveOrgComponent />
        </AuthSessionProvider>,
        { dataProvider: mockData }
      );

      await waitFor(() => {
        expect(screen.getByTestId('active-org-name')).toHaveTextContent('null');
      });
    });
  });
});

function TestComponent() {
  const { session, loading, error, isAuthenticated, isAdmin } = useAuthSession();
  return (
    <div>
      <span data-testid="auth-loading">{String(loading)}</span>
      <span data-testid="auth-error">{error ?? 'no-error'}</span>
      <span data-testid="auth-session">{session ? 'has-session' : 'no-session'}</span>
      <span data-testid="auth-is-authenticated">{String(isAuthenticated)}</span>
      <span data-testid="auth-is-admin">{String(isAdmin)}</span>
    </div>
  );
}

function SetOrgComponent() {
  const { loading, setActiveOrganisation } = useAuthSession();
  if (loading) return <div>Loading...</div>;
  return (
    <div>
      <span data-testid="org-ready">ready</span>
      <button data-testid="set-org-btn" onClick={() => setActiveOrganisation('org-002')}>
        Set Org
      </button>
    </div>
  );
}

function SwitchProfileComponent() {
  const { loading, switchAuthProfile, authProfiles } = useAuthSession();
  if (loading) return <div>Loading...</div>;
  return (
    <div>
      <span data-testid="profile-ready">ready</span>
      <span data-testid="profile-count">{authProfiles.length}</span>
      <button data-testid="switch-profile-btn" onClick={() => switchAuthProfile('org-admin-alex')}>
        Switch Profile
      </button>
    </div>
  );
}

function RefreshComponent() {
  const { loading, refreshSession } = useAuthSession();
  if (loading) return <div>Loading...</div>;
  return (
    <div>
      <span data-testid="refresh-ready">ready</span>
      <button data-testid="refresh-btn" onClick={() => refreshSession()}>
        Refresh
      </button>
    </div>
  );
}

function ActiveOrgComponent() {
  const { loading, activeOrganisation } = useAuthSession();
  if (loading) return <div>Loading...</div>;
  return (
    <div>
      <span data-testid="active-org-name">{activeOrganisation?.organisation_name ?? 'null'}</span>
    </div>
  );
}
