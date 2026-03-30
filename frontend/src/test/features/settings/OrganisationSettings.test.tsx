import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderWithRouter, screen, waitFor, createMockSession, createMockDataProvider } from '@/test/test-utils';
import { Route, Routes } from 'react-router-dom';
import React from 'react';
import { OrganisationModal } from '@/features/settings/OrganisationModal';
import { OrganisationList } from '@/features/settings/OrganisationList';

describe('OrganisationModal', () => {
  const mockOnClose = vi.fn();
  const mockOnSuccess = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders modal when isOpen is true', () => {
    const session = createMockSession({ platform_role: 'admin', capabilities: ['app:access', 'admin:access'] });
    const mockData = createMockDataProvider({
      getAuthSession: vi.fn().mockResolvedValue(session),
      createOrganisation: vi.fn().mockResolvedValue({
        id: 'org-new',
        name: 'Test Org',
        slug: 'test-org',
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      }),
    });
    renderWithRouter(
      <Routes>
        <Route path="/settings" element={<OrganisationModal isOpen={true} onClose={mockOnClose} onSuccess={mockOnSuccess} />} />
      </Routes>,
      { dataProvider: mockData, initialEntries: ['/settings'] },
    );
    expect(screen.getByRole('heading', { name: /create organisation/i })).toBeInTheDocument();
    expect(screen.getByLabelText('Organisation Name')).toBeInTheDocument();
    expect(screen.getByLabelText('URL Slug')).toBeInTheDocument();
  });

  it('does not render modal when isOpen is false', () => {
    const session = createMockSession({ platform_role: 'admin', capabilities: ['app:access', 'admin:access'] });
    const mockData = createMockDataProvider({
      getAuthSession: vi.fn().mockResolvedValue(session),
    });
    renderWithRouter(
      <Routes>
        <Route path="/settings" element={<OrganisationModal isOpen={false} onClose={mockOnClose} onSuccess={mockOnSuccess} />} />
      </Routes>,
      { dataProvider: mockData, initialEntries: ['/settings'] },
    );
    expect(screen.queryByLabelText('Organisation Name')).not.toBeInTheDocument();
  });

  it('shows error when createOrganisation fails', async () => {
    const session = createMockSession({ platform_role: 'admin', capabilities: ['app:access', 'admin:access'] });
    const mockData = createMockDataProvider({
      getAuthSession: vi.fn().mockResolvedValue(session),
      createOrganisation: vi.fn().mockRejectedValue(new Error('An organisation with this slug already exists')),
    });
    renderWithRouter(
      <Routes>
        <Route path="/settings" element={<OrganisationModal isOpen={true} onClose={mockOnClose} onSuccess={mockOnSuccess} />} />
      </Routes>,
      { dataProvider: mockData, initialEntries: ['/settings'] },
    );
    const user = require('@testing-library/user-event').userEvent;
    await user.type(screen.getByLabelText('Organisation Name'), 'Dup Org');
    await user.click(screen.getByRole('button', { name: /create organisation/i }));
    await waitFor(() => {
      expect(screen.getByText('An organisation with this slug already exists')).toBeInTheDocument();
    });
  });
});

describe('OrganisationList', () => {
  const mockOnCreateClick = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows empty state when no memberships', () => {
    const session = createMockSession({
      org_memberships: [],
      active_organisation_id: null,
      capabilities: ['app:access'],
    });
    const mockData = createMockDataProvider({
      getAuthSession: vi.fn().mockResolvedValue(session),
    });
    renderWithRouter(
      <Routes>
        <Route path="/settings" element={<OrganisationList onCreateClick={mockOnCreateClick} />} />
      </Routes>,
      { dataProvider: mockData, initialEntries: ['/settings'] },
    );
    expect(screen.getByText('No organisations yet')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create organisation/i })).toBeInTheDocument();
  });

  it('shows organisations when memberships exist', async () => {
    const session = createMockSession({
      platform_role: 'admin',
      capabilities: ['app:access', 'admin:access'],
      org_memberships: [
        { organisation_id: 'org-001', organisation_name: 'Acme Sales', role: 'org_admin', permissions: ['admin:access', 'org:read', 'org:write'] },
        { organisation_id: 'org-002', organisation_name: 'Acme Support', role: 'member', permissions: ['collections:read', 'practice:run'] },
      ],
      active_organisation_id: 'org-001',
    });
    const mockData = createMockDataProvider({
      getAuthSession: vi.fn().mockResolvedValue(session),
    });
    renderWithRouter(
      <Routes>
        <Route path="/settings" element={<OrganisationList onCreateClick={mockOnCreateClick} />} />
      </Routes>,
      { dataProvider: mockData, initialEntries: ['/settings'] },
    );
    await waitFor(() => {
      expect(screen.getByText('Acme Sales')).toBeInTheDocument();
    });
    expect(screen.getByText('Acme Support')).toBeInTheDocument();
  });

  it('shows active badge on active organisation', async () => {
    const session = createMockSession({
      platform_role: 'admin',
      capabilities: ['app:access', 'admin:access'],
      org_memberships: [
        { organisation_id: 'org-001', organisation_name: 'Acme Sales', role: 'org_admin', permissions: ['admin:access', 'org:read', 'org:write'] },
      ],
      active_organisation_id: 'org-001',
    });
    const mockData = createMockDataProvider({
      getAuthSession: vi.fn().mockResolvedValue(session),
    });
    renderWithRouter(
      <Routes>
        <Route path="/settings" element={<OrganisationList onCreateClick={mockOnCreateClick} />} />
      </Routes>,
      { dataProvider: mockData, initialEntries: ['/settings'] },
    );
    await waitFor(() => {
      expect(screen.getByText('Active')).toBeInTheDocument();
    });
  });

  it('calls onCreateClick when New button is clicked', async () => {
    const session = createMockSession({
      platform_role: 'admin',
      capabilities: ['app:access', 'admin:access'],
      org_memberships: [
        { organisation_id: 'org-001', organisation_name: 'Acme Sales', role: 'org_admin', permissions: ['admin:access', 'org:read', 'org:write'] },
      ],
      active_organisation_id: 'org-001',
    });
    const mockData = createMockDataProvider({
      getAuthSession: vi.fn().mockResolvedValue(session),
    });
    renderWithRouter(
      <Routes>
        <Route path="/settings" element={<OrganisationList onCreateClick={mockOnCreateClick} />} />
      </Routes>,
      { dataProvider: mockData, initialEntries: ['/settings'] },
    );
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'New' })).toBeInTheDocument();
    });
    await require('@testing-library/user-event').userEvent.click(screen.getByRole('button', { name: 'New' }));
    expect(mockOnCreateClick).toHaveBeenCalled();
  });

  it('shows switch button for non-active organisations', async () => {
    const session = createMockSession({
      platform_role: 'admin',
      capabilities: ['app:access', 'admin:access'],
      org_memberships: [
        { organisation_id: 'org-001', organisation_name: 'Acme Sales', role: 'org_admin', permissions: ['admin:access', 'org:read', 'org:write'] },
        { organisation_id: 'org-002', organisation_name: 'Acme Support', role: 'org_admin', permissions: ['admin:access', 'org:read', 'org:write'] },
      ],
      active_organisation_id: 'org-001',
    });
    const mockData = createMockDataProvider({
      getAuthSession: vi.fn().mockResolvedValue(session),
    });
    renderWithRouter(
      <Routes>
        <Route path="/settings" element={<OrganisationList onCreateClick={mockOnCreateClick} />} />
      </Routes>,
      { dataProvider: mockData, initialEntries: ['/settings'] },
    );
    await waitFor(() => {
      expect(screen.getAllByRole('button', { name: /switch/i })).toHaveLength(1);
    });
  });
});
