import { describe, it, expect, vi } from 'vitest';
import { screen, waitFor, fireEvent } from '@testing-library/react';
import React from 'react';
import { renderWithRouter, createMockDataProvider, createMockSession } from '@/test/test-utils';
import { AdminAudit } from '@/features/admin/pages/AdminAudit';

vi.mock('@/features/admin/components', () => ({
  AdminPageShell: ({ children, title, subtitle }: { children: React.ReactNode; title: string; subtitle: string }) => (
    <div data-testid="admin-audit-page">
      <h1>{title}</h1>
      <p>{subtitle}</p>
      {children}
    </div>
  ),
  MetricCard: ({ label, value }: { label: string; value: string | number }) => (
    <div data-testid="metric-card">
      <span>{label}</span>
      <span>{value}</span>
    </div>
  ),
  DataTable: ({ data, columns }: { data: any[]; columns: any[] }) => (
    <div data-testid="data-table">
      {data.map((item) => (
        <div key={item.event_id} data-testid="event-row">
          {item.event_type}
        </div>
      ))}
    </div>
  ),
  SearchInput: ({ value, onChange, placeholder, className }: { value: string; onChange: (v: string) => void; placeholder: string; className?: string }) => (
    <input
      data-testid="search-input"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
    />
  ),
  FilterSelect: ({ value, onChange, options, placeholder, className }: { value: string; onChange: (v: string) => void; options: { value: string; label: string }[]; placeholder: string; className?: string }) => (
    <select
      data-testid="filter-select"
      value={value}
      onChange={(e) => onChange(e.target.value)}
    >
      <option value="">{placeholder}</option>
      {options.map((opt) => (
        <option key={opt.value} value={opt.value}>{opt.label}</option>
      ))}
    </select>
  ),
  Pagination: ({ currentPage, totalPages, onPageChange }: { currentPage: number; totalPages: number; onPageChange: (p: number) => void }) => (
    <div data-testid="pagination">
      <span>Page {currentPage} of {totalPages}</span>
      <button onClick={() => onPageChange(currentPage + 1)}>Next</button>
    </div>
  ),
}));

const mockEvents = {
  items: [
    {
      event_id: 'evt-001',
      event_type: 'session.started',
      trace_id: 'trace-aaa',
      workflow_id: 'wf-001',
      error_code: null,
      occurred_at: '2026-03-31T10:00:00Z',
    },
    {
      event_id: 'evt-002',
      event_type: 'attempt.submitted',
      trace_id: 'trace-bbb',
      workflow_id: 'wf-002',
      error_code: 'SS-ERR-001',
      occurred_at: '2026-03-31T11:00:00Z',
    },
    {
      event_id: 'evt-003',
      event_type: 'pipeline.failed',
      trace_id: 'trace-ccc',
      workflow_id: 'wf-003',
      error_code: 'SS-PIPE-002',
      occurred_at: '2026-03-31T12:00:00Z',
    },
  ],
  total: 3,
  offset: 0,
  limit: 20,
};

describe('AdminAudit Filtering', () => {
  const createAdminSession = () => createMockSession({
    status: 'authenticated',
    platform_role: 'admin',
    capabilities: ['app:access', 'admin:access'],
    org_memberships: [
      { organisation_id: 'org-001', organisation_name: 'Acme Sales', role: 'org_admin', permissions: ['org:read', 'org:write'] },
    ],
    active_organisation_id: 'org-001',
  });

  it('renders audit page with filter controls', async () => {
    const mockSession = createAdminSession();
    const mockData = createMockDataProvider({
      getAuthSession: vi.fn().mockResolvedValue(mockSession),
      listWorkflowEvents: vi.fn().mockResolvedValue(mockEvents),
    });

    renderWithRouter(<AdminAudit />, { dataProvider: mockData, initialEntries: ['/admin/audit'] });

    await waitFor(() => {
      expect(screen.getByTestId('admin-audit-page')).toBeInTheDocument();
    });

    expect(screen.getAllByTestId('search-input')).toHaveLength(2);
    expect(screen.getAllByTestId('filter-select')).toHaveLength(2);
  });

  it('calls listWorkflowEvents with search param', async () => {
    const mockSession = createAdminSession();
    const listWorkflowEvents = vi.fn().mockResolvedValue(mockEvents);
    const mockData = createMockDataProvider({
      getAuthSession: vi.fn().mockResolvedValue(mockSession),
      listWorkflowEvents,
    });

    renderWithRouter(<AdminAudit />, { dataProvider: mockData, initialEntries: ['/admin/audit'] });

    await waitFor(() => {
      expect(screen.getAllByTestId('search-input')).toHaveLength(2);
    });

    const searchInputs = screen.getAllByTestId('search-input');
    fireEvent.change(searchInputs[0], { target: { value: 'session' } });

    await waitFor(() => {
      expect(listWorkflowEvents).toHaveBeenCalledWith(
        expect.objectContaining({ search: 'session' })
      );
    });
  });

  it('calls listWorkflowEvents with event_type filter', async () => {
    const mockSession = createAdminSession();
    const listWorkflowEvents = vi.fn().mockResolvedValue(mockEvents);
    const mockData = createMockDataProvider({
      getAuthSession: vi.fn().mockResolvedValue(mockSession),
      listWorkflowEvents,
    });

    renderWithRouter(<AdminAudit />, { dataProvider: mockData, initialEntries: ['/admin/audit'] });

    await waitFor(() => {
      expect(screen.getAllByTestId('filter-select')).toHaveLength(2);
    });

    const filterSelects = screen.getAllByTestId('filter-select');
    fireEvent.change(filterSelects[0], { target: { value: 'session.started' } });

    await waitFor(() => {
      expect(listWorkflowEvents).toHaveBeenCalledWith(
        expect.objectContaining({ event_type: 'session.started' })
      );
    });
  });

  it('calls listWorkflowEvents with sort params', async () => {
    const mockSession = createAdminSession();
    const listWorkflowEvents = vi.fn().mockResolvedValue(mockEvents);
    const mockData = createMockDataProvider({
      getAuthSession: vi.fn().mockResolvedValue(mockSession),
      listWorkflowEvents,
    });

    renderWithRouter(<AdminAudit />, { dataProvider: mockData, initialEntries: ['/admin/audit'] });

    await waitFor(() => {
      expect(listWorkflowEvents).toHaveBeenCalled();
    });

    const lastCall = listWorkflowEvents.mock.calls[listWorkflowEvents.mock.calls.length - 1][0];
    expect(lastCall).toHaveProperty('sort_by');
    expect(lastCall).toHaveProperty('sort_order');
  });

  it('displays events in data table', async () => {
    const mockSession = createAdminSession();
    const mockData = createMockDataProvider({
      getAuthSession: vi.fn().mockResolvedValue(mockSession),
      listWorkflowEvents: vi.fn().mockResolvedValue(mockEvents),
    });

    renderWithRouter(<AdminAudit />, { dataProvider: mockData, initialEntries: ['/admin/audit'] });

    await waitFor(() => {
      expect(screen.getAllByTestId('event-row')).toHaveLength(3);
    });

    expect(screen.getByText('session.started')).toBeInTheDocument();
    expect(screen.getByText('attempt.submitted')).toBeInTheDocument();
    expect(screen.getByText('pipeline.failed')).toBeInTheDocument();
  });

  it('shows error count in metrics', async () => {
    const mockSession = createAdminSession();
    const mockData = createMockDataProvider({
      getAuthSession: vi.fn().mockResolvedValue(mockSession),
      listWorkflowEvents: vi.fn().mockResolvedValue(mockEvents),
    });

    renderWithRouter(<AdminAudit />, { dataProvider: mockData, initialEntries: ['/admin/audit'] });

    await waitFor(() => {
      expect(screen.getAllByTestId('metric-card')).toHaveLength(4);
    });

    const metricCards = screen.getAllByTestId('metric-card');
    const errorCard = metricCards.find((card) => card.textContent?.includes('Errors'));
    expect(errorCard).toBeInTheDocument();
  });
});
