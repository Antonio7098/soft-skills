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
        <div key={`${item.source}:${item.id}`} data-testid="audit-row">
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

const mockAuditData = {
  items: [
    {
      id: 'evt-001',
      source: 'workflow_event' as const,
      event_type: 'session.started',
      user_id: 'user-001',
      trace_id: 'trace-aaa',
      workflow_id: 'wf-001',
      request_id: null,
      error_code: null,
      occurred_at: '2026-03-31T10:00:00Z',
      payload: {},
    },
    {
      id: 'pr-001',
      source: 'pipeline_run' as const,
      event_type: 'assessment_pipeline',
      user_id: 'user-002',
      trace_id: 'trace-bbb',
      workflow_id: null,
      request_id: null,
      error_code: null,
      occurred_at: '2026-03-31T11:00:00Z',
      payload: { status: 'completed' },
    },
    {
      id: 'pc-001',
      source: 'provider_call' as const,
      event_type: 'chat.completion',
      user_id: null,
      trace_id: 'trace-ccc',
      workflow_id: null,
      request_id: null,
      error_code: 'rate_limit',
      occurred_at: '2026-03-31T12:00:00Z',
      payload: { provider: 'openai', model_id: 'gpt-4' },
    },
  ],
  total: 3,
  offset: 0,
  limit: 20,
};

describe('AdminAudit Unified Log', () => {
  const createAdminSession = () => createMockSession({
    status: 'authenticated',
    platform_role: 'admin',
    capabilities: ['app:access', 'admin:access'],
    org_memberships: [
      { organisation_id: 'org-001', organisation_name: 'Acme Sales', role: 'org_admin', permissions: ['org:read', 'org:write'] },
    ],
    active_organisation_id: 'org-001',
  });

  it('renders audit page with source filter and search', async () => {
    const mockSession = createAdminSession();
    const mockData = createMockDataProvider({
      getAuthSession: vi.fn().mockResolvedValue(mockSession),
      listUnifiedAuditLog: vi.fn().mockResolvedValue(mockAuditData),
    });

    renderWithRouter(<AdminAudit />, { dataProvider: mockData, initialEntries: ['/admin/audit'] });

    await waitFor(() => {
      expect(screen.getByTestId('admin-audit-page')).toBeInTheDocument();
    });

    expect(screen.getAllByTestId('search-input')).toHaveLength(2);
    expect(screen.getAllByTestId('filter-select')).toHaveLength(3);
  });

  it('calls listUnifiedAuditLog with source filter', async () => {
    const mockSession = createAdminSession();
    const listUnifiedAuditLog = vi.fn().mockResolvedValue(mockAuditData);
    const mockData = createMockDataProvider({
      getAuthSession: vi.fn().mockResolvedValue(mockSession),
      listUnifiedAuditLog,
    });

    renderWithRouter(<AdminAudit />, { dataProvider: mockData, initialEntries: ['/admin/audit'] });

    await waitFor(() => {
      expect(screen.getAllByTestId('filter-select')).toHaveLength(3);
    });

    const filterSelects = screen.getAllByTestId('filter-select');
    fireEvent.change(filterSelects[0], { target: { value: 'workflow_event' } });

    await waitFor(() => {
      expect(listUnifiedAuditLog).toHaveBeenCalledWith(
        expect.objectContaining({ source: 'workflow_event' })
      );
    });
  });

  it('calls listUnifiedAuditLog with search param', async () => {
    const mockSession = createAdminSession();
    const listUnifiedAuditLog = vi.fn().mockResolvedValue(mockAuditData);
    const mockData = createMockDataProvider({
      getAuthSession: vi.fn().mockResolvedValue(mockSession),
      listUnifiedAuditLog,
    });

    renderWithRouter(<AdminAudit />, { dataProvider: mockData, initialEntries: ['/admin/audit'] });

    await waitFor(() => {
      expect(screen.getAllByTestId('search-input')).toHaveLength(2);
    });

    const searchInputs = screen.getAllByTestId('search-input');
    fireEvent.change(searchInputs[0], { target: { value: 'session' } });

    await waitFor(() => {
      expect(listUnifiedAuditLog).toHaveBeenCalledWith(
        expect.objectContaining({ search: 'session' })
      );
    });
  });

  it('displays entries from multiple sources', async () => {
    const mockSession = createAdminSession();
    const mockData = createMockDataProvider({
      getAuthSession: vi.fn().mockResolvedValue(mockSession),
      listUnifiedAuditLog: vi.fn().mockResolvedValue(mockAuditData),
    });

    renderWithRouter(<AdminAudit />, { dataProvider: mockData, initialEntries: ['/admin/audit'] });

    await waitFor(() => {
      expect(screen.getAllByTestId('audit-row')).toHaveLength(3);
    });

    expect(screen.getByText('session.started')).toBeInTheDocument();
    expect(screen.getByText('assessment_pipeline')).toBeInTheDocument();
    expect(screen.getByText('chat.completion')).toBeInTheDocument();
  });

  it('shows error count in metrics', async () => {
    const mockSession = createAdminSession();
    const mockData = createMockDataProvider({
      getAuthSession: vi.fn().mockResolvedValue(mockSession),
      listUnifiedAuditLog: vi.fn().mockResolvedValue(mockAuditData),
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
