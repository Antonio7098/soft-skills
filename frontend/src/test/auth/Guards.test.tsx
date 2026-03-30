import { describe, it, expect, vi } from 'vitest';
import { renderWithRouter, renderWithProviders, screen, waitFor, createMockSession, createMockDataProvider } from '@/test/test-utils';
import { UserAppGuard, AdminGuard } from '@/auth/Guards';
import { render, screen, waitFor, act } from '@testing-library/react';
import React from 'react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { DataProviderProvider } from '@/data/DataContext';
import { AuthSessionProvider } from '@/auth/AuthSessionContext';
import { AdminScopeProvider, useAdminScope } from '@/auth/AdminScopeContext';

describe('UserAppGuard', () => {
  it('shows loading state while session is loading', async () => {
    const mockData = createMockDataProvider({
      getAuthSession: vi.fn().mockImplementation(() => new Promise(() => {})),
    });

    renderWithProviders(
      <UserAppGuard>
        <ProtectedContent />
      </UserAppGuard>,
      { dataProvider: mockData }
    );

    expect(screen.getByText('Loading your session...')).toBeInTheDocument();
  });

  it('renders children when authenticated', async () => {
    const mockSession = createMockSession({ status: 'authenticated' });
    const mockData = createMockDataProvider({
      getAuthSession: vi.fn().mockResolvedValue(mockSession),
    });

    renderWithProviders(
      <UserAppGuard>
        <ProtectedContent />
      </UserAppGuard>,
      { dataProvider: mockData }
    );

    await waitFor(() => {
      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });
  });

  it('shows error state when session load fails', async () => {
    const mockData = createMockDataProvider({
      getAuthSession: vi.fn().mockRejectedValue(new Error('Failed to load')),
    });

    renderWithProviders(
      <UserAppGuard>
        <ProtectedContent />
      </UserAppGuard>,
      { dataProvider: mockData }
    );

    await waitFor(() => {
      expect(screen.getByText('Session Unavailable')).toBeInTheDocument();
      expect(screen.getByText('Failed to load')).toBeInTheDocument();
    });
  });

  it('shows sign-in required when not authenticated', async () => {
    const mockSession = createMockSession({ status: 'anonymous' });
    const mockData = createMockDataProvider({
      getAuthSession: vi.fn().mockResolvedValue(mockSession),
    });

    render(
      <MemoryRouter initialEntries={['/']}>
        <DataProviderProvider provider={mockData}>
          <AuthSessionProvider>
            <Routes>
              <Route path="/login" element={<div data-testid="login-page">Login</div>} />
              <Route
                path="/"
                element={(
                  <UserAppGuard>
                    <ProtectedContent />
                  </UserAppGuard>
                )}
              />
            </Routes>
          </AuthSessionProvider>
        </DataProviderProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('login-page')).toBeInTheDocument();
    });
  });

  it('has retry button on error that reloads session', async () => {
    const mockData = createMockDataProvider({
      getAuthSession: vi.fn()
        .mockRejectedValueOnce(new Error('Failed to load'))
        .mockResolvedValue(createMockSession({ status: 'authenticated' })),
    });

    renderWithProviders(
      <UserAppGuard>
        <ProtectedContent />
      </UserAppGuard>,
      { dataProvider: mockData }
    );

    await waitFor(() => {
      expect(screen.getByText('Session Unavailable')).toBeInTheDocument();
    });

    await act(async () => {
      screen.getByText('Retry').click();
    });

    await waitFor(() => {
      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });
  });
});

describe('AdminGuard', () => {
  it('shows loading state while session is loading', async () => {
    const mockData = createMockDataProvider({
      getAuthSession: vi.fn().mockImplementation(() => new Promise(() => {})),
    });

    renderWithProviders(
      <AdminGuard>
        <AdminContent />
      </AdminGuard>,
      { dataProvider: mockData }
    );

    expect(screen.getByText('Loading your session...')).toBeInTheDocument();
  });

  it('renders children wrapped in AdminScopeProvider when admin', async () => {
    const mockSession = createMockSession({
      status: 'authenticated',
      platform_role: 'admin',
      capabilities: ['app:access', 'admin:access'],
    });
    const mockData = createMockDataProvider({
      getAuthSession: vi.fn().mockResolvedValue(mockSession),
    });

    renderWithRouter(
      <AdminGuard>
        <AdminContent />
      </AdminGuard>,
      { dataProvider: mockData, initialEntries: ['/admin'] }
    );

    await waitFor(() => {
      expect(screen.getByTestId('admin-content')).toBeInTheDocument();
      expect(screen.getByTestId('admin-scope-available')).toHaveTextContent('true');
    });
  });

  it('redirects non-admin users to home', async () => {
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
              <Route path="/" element={<HomePage />} />
              <Route path="/admin" element={
                <AdminGuard>
                  <AdminContent />
                </AdminGuard>
              } />
            </Routes>
          </AuthSessionProvider>
        </DataProviderProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('home-page')).toBeInTheDocument();
    });
  });

  it('shows error state when session load fails', async () => {
    const mockData = createMockDataProvider({
      getAuthSession: vi.fn().mockRejectedValue(new Error('Admin session unavailable')),
    });

    renderWithProviders(
      <AdminGuard>
        <AdminContent />
      </AdminGuard>,
      { dataProvider: mockData }
    );

    await waitFor(() => {
      expect(screen.getByText('Admin Session Unavailable')).toBeInTheDocument();
    });
  });

  it('superadmin can access admin area', async () => {
    const mockSession = createMockSession({
      status: 'authenticated',
      platform_role: 'superadmin',
      capabilities: ['app:access', 'admin:access', 'platform:superadmin'],
    });
    const mockData = createMockDataProvider({
      getAuthSession: vi.fn().mockResolvedValue(mockSession),
    });

    renderWithRouter(
      <AdminGuard>
        <AdminContent />
      </AdminGuard>,
      { dataProvider: mockData, initialEntries: ['/admin'] }
    );

    await waitFor(() => {
      expect(screen.getByTestId('admin-content')).toBeInTheDocument();
    });
  });
});

describe('AdminScopeGuard', () => {
  it('shows organisation access denied when user lacks org:read', async () => {
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
            <AdminContent />
          </AdminGuard>
        } />
      </Routes>,
      { dataProvider: mockData, initialEntries: ['/admin/orgs/org-999'] }
    );

    await waitFor(() => {
      expect(screen.getByText('Organisation Access Denied')).toBeInTheDocument();
    });
  });

  it('allows access when user has org:read for the organisation', async () => {
    const mockSession = createMockSession({
      status: 'authenticated',
      platform_role: 'admin',
      capabilities: ['app:access', 'admin:access'],
      org_memberships: [
        { organisation_id: 'org-001', organisation_name: 'Acme Sales', role: 'org_admin', permissions: ['org:read', 'org:write'] },
        { organisation_id: 'org-002', organisation_name: 'Acme Support', role: 'org_admin', permissions: ['org:read', 'org:write'] },
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
            <AdminContent />
          </AdminGuard>
        } />
      </Routes>,
      { dataProvider: mockData, initialEntries: ['/admin/orgs/org-002'] }
    );

    await waitFor(() => {
      expect(screen.getByTestId('admin-content')).toBeInTheDocument();
    });
  });

  it('superadmin bypasses org:read check', async () => {
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
            <AdminContent />
          </AdminGuard>
        } />
      </Routes>,
      { dataProvider: mockData, initialEntries: ['/admin/orgs/org-001'] }
    );

    await waitFor(() => {
      expect(screen.getByTestId('admin-content')).toBeInTheDocument();
    });
  });
});

function ProtectedContent() {
  return <div data-testid="protected-content">Protected Content</div>;
}

function AdminContent() {
  const { activeOrganisation } = useAdminScopeStrict();
  return (
    <div>
      <div data-testid="admin-content">Admin Content</div>
      <div data-testid="admin-scope-available">{String(activeOrganisation !== null)}</div>
    </div>
  );
}

function HomePage() {
  return <div data-testid="home-page">Home</div>;
}

function useAdminScopeStrict() {
  const context = useAdminScope();
  if (!context) {
    throw new Error('useAdminScope must be used within AdminScopeProvider');
  }
  return context;
}
