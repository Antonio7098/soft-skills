import { useEffect, useState, useCallback } from 'react';
import { 
  ScrollText,
  Filter,
  AlertTriangle,
  Clock,
  ChevronRight,
  X,
  ChevronDown,
  ChevronUp,
  Calendar,
  Regex,
  SlidersHorizontal,
  Server,
  GitBranch,
  User,
} from 'lucide-react';
import { Card } from '@/design-system/primitives/Card';
import { Button } from '@/design-system/primitives/Button';
import { Badge } from '@/design-system/primitives/Badge';
import { LoadingState } from '@/design-system/patterns/LoadingState';
import { useData } from '@/data';
import { AdminPageShell, MetricCard, DataTable, SearchInput, FilterSelect, Pagination } from '../components';
import type { UnifiedAuditEntryView, PaginatedUnifiedAuditView } from '@/data/types';

const SOURCE_OPTIONS = [
  { value: 'workflow_event', label: 'Workflow Events' },
  { value: 'pipeline_run', label: 'Pipeline Runs' },
  { value: 'provider_call', label: 'Provider Calls' },
];

const EVENT_TYPE_OPTIONS = [
  { value: 'session.started', label: 'Session Started' },
  { value: 'attempt.submitted', label: 'Attempt Submitted' },
  { value: 'assessment.completed', label: 'Assessment Completed' },
  { value: 'pipeline.failed', label: 'Pipeline Failed' },
  { value: 'auth.login.success', label: 'Login Success' },
  { value: 'auth.login.failure', label: 'Login Failure' },
  { value: 'verification.submitted', label: 'Verification Submitted' },
  { value: 'verification.approved', label: 'Verification Approved' },
  { value: 'verification.rejected', label: 'Verification Rejected' },
];

const SORT_OPTIONS = [
  { value: 'occurred_at', label: 'Time' },
  { value: 'event_type', label: 'Event Type' },
  { value: 'user_id', label: 'User ID' },
];

const PAGE_SIZE = 20;

function formatDateForApi(dateStr: string): string {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return '';
  return d.toISOString();
}

const SOURCE_ICONS: Record<string, React.ReactNode> = {
  workflow_event: <ScrollText className="w-3.5 h-3.5" />,
  pipeline_run: <GitBranch className="w-3.5 h-3.5" />,
  provider_call: <Server className="w-3.5 h-3.5" />,
};

const SOURCE_COLORS: Record<string, string> = {
  workflow_event: 'bg-accent',
  pipeline_run: 'bg-status-warning',
  provider_call: 'bg-content-tertiary',
};

export function AdminAudit() {
  const dataProvider = useData();
  const [auditData, setAuditData] = useState<PaginatedUnifiedAuditView | null>(null);
  const [loading, setLoading] = useState(true);
  
  // Filters
  const [sourceFilter, setSourceFilter] = useState('');
  const [search, setSearch] = useState('');
  const [eventTypeFilter, setEventTypeFilter] = useState('');
  const [errorCodeFilter, setErrorCodeFilter] = useState('');
  const [userIdFilter, setUserIdFilter] = useState('');
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  
  // Sorting
  const [sortBy, setSortBy] = useState('occurred_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  
  // Pagination
  const [page, setPage] = useState(1);
  
  // UI state
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<UnifiedAuditEntryView | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);

  const loadAuditLog = useCallback(() => {
    setLoading(true);
    const params: Record<string, string | number | undefined> = {
      offset: (page - 1) * PAGE_SIZE,
      limit: PAGE_SIZE,
    };
    if (sourceFilter) params.source = sourceFilter;
    if (eventTypeFilter) params.event_type = eventTypeFilter;
    if (errorCodeFilter) params.error_code = errorCodeFilter;
    if (userIdFilter) params.user_id = userIdFilter;
    if (search) params.search = search;
    if (fromDate) params.from_date = formatDateForApi(fromDate);
    if (toDate) params.to_date = formatDateForApi(toDate);
    if (sortBy) params.sort_by = sortBy;
    if (sortOrder) params.sort_order = sortOrder;

    dataProvider.listUnifiedAuditLog(params)
      .then((result) => {
        setAuditData(result);
      })
      .catch((error) => console.error('[AdminAudit] Error loading audit log:', error))
      .finally(() => setLoading(false));
  }, [dataProvider, page, sourceFilter, eventTypeFilter, errorCodeFilter, userIdFilter, search, fromDate, toDate, sortBy, sortOrder]);

  useEffect(() => {
    loadAuditLog();
  }, [loadAuditLog]);

  const handleSort = (field: string) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
    setPage(1);
  };

  const clearFilters = () => {
    setSourceFilter('');
    setSearch('');
    setEventTypeFilter('');
    setErrorCodeFilter('');
    setUserIdFilter('');
    setFromDate('');
    setToDate('');
    setPage(1);
  };

  const hasActiveFilters = sourceFilter || search || eventTypeFilter || errorCodeFilter || userIdFilter || fromDate || toDate;

  const columns = [
    {
      key: 'source',
      header: 'Source',
      width: '100px',
      sortable: false,
      render: (entry: UnifiedAuditEntryView) => (
        <div className="flex items-center gap-1.5">
          <span className={`w-2 h-2 rounded-full ${SOURCE_COLORS[entry.source] || 'bg-content-tertiary'}`} />
          <span className="text-body-xs text-content-secondary">{entry.source.replace('_', ' ')}</span>
        </div>
      ),
    },
    {
      key: 'event_type',
      header: 'Event',
      width: '200px',
      sortable: true,
      render: (entry: UnifiedAuditEntryView) => (
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${entry.error_code ? 'bg-status-error' : 'bg-status-success'}`} />
          <span className="font-medium text-body-sm">{entry.event_type}</span>
        </div>
      ),
    },
    {
      key: 'user_id',
      header: 'User',
      width: '120px',
      sortable: true,
      render: (entry: UnifiedAuditEntryView) => (
        entry.user_id ? (
          <span className="font-mono text-body-xs text-content-secondary">
            {entry.user_id.slice(0, 12)}...
          </span>
        ) : (
          <span className="text-content-tertiary">—</span>
        )
      ),
    },
    {
      key: 'trace_id',
      header: 'Trace ID',
      width: '120px',
      sortable: false,
      render: (entry: UnifiedAuditEntryView) => (
        <span className="font-mono text-body-xs text-content-secondary">
          {entry.trace_id?.slice(0, 12) || '—'}...
        </span>
      ),
    },
    {
      key: 'error_code',
      header: 'Error',
      width: '120px',
      sortable: false,
      render: (entry: UnifiedAuditEntryView) => (
        entry.error_code ? (
          <Badge variant="error" size="sm">{entry.error_code}</Badge>
        ) : (
          <span className="text-content-tertiary">—</span>
        )
      ),
    },
    {
      key: 'occurred_at',
      header: 'Time',
      width: '180px',
      sortable: true,
      render: (entry: UnifiedAuditEntryView) => (
        <span className="text-content-secondary text-body-sm">
          {new Date(entry.occurred_at).toLocaleString()}
        </span>
      ),
    },
  ];

  const totalPages = auditData ? Math.ceil(auditData.total / PAGE_SIZE) : 1;
  const errorCount = auditData?.items.filter((e) => e.error_code).length || 0;
  const sourceCounts = auditData?.items.reduce((acc, e) => {
    acc[e.source] = (acc[e.source] || 0) + 1;
    return acc;
  }, {} as Record<string, number>) || {};

  const SortIndicator = ({ columnKey }: { columnKey: string }) => {
    if (sortBy !== columnKey) return <span className="w-3 h-3 inline-block" />;
    return sortOrder === 'asc' 
      ? <ChevronUp className="w-3 h-3 inline-block" /> 
      : <ChevronDown className="w-3 h-3 inline-block" />;
  };

  if (loading && !auditData) {
    return (
      <AdminPageShell title="Audit Logs" subtitle="Unified system event tracking">
        <LoadingState message="Loading audit logs..." />
      </AdminPageShell>
    );
  }

  return (
    <AdminPageShell
      title="Audit Logs"
      subtitle="Unified view of workflow events, pipeline runs, and provider calls"
    >
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Total Events"
          value={auditData?.total?.toLocaleString() || '0'}
          icon={<ScrollText className="w-4 h-4" />}
        />
        <MetricCard
          label="This Page"
          value={auditData?.items.length || 0}
          icon={<Filter className="w-4 h-4" />}
        />
        <MetricCard
          label="Errors"
          value={errorCount}
          icon={<AlertTriangle className="w-4 h-4" />}
          trend={errorCount > 0 ? 'negative' : 'positive'}
        />
        <MetricCard
          label="Latest"
          value={auditData?.items[0] ? new Date(auditData.items[0].occurred_at).toLocaleTimeString() : '—'}
          icon={<Clock className="w-4 h-4" />}
        />
      </div>

      {/* Source breakdown */}
      {Object.keys(sourceCounts).length > 0 && (
        <div className="flex items-center gap-3 flex-wrap">
          {Object.entries(sourceCounts).map(([source, count]) => (
            <Badge key={source} variant="default" size="sm" className="flex items-center gap-1.5">
              {SOURCE_ICONS[source]}
              {source.replace('_', ' ')}: {count}
            </Badge>
          ))}
        </div>
      )}

      {/* Primary Filters */}
      <Card className="flex flex-col gap-4">
        <div className="flex items-center gap-3 flex-wrap">
          <FilterSelect
            value={sourceFilter}
            onChange={setSourceFilter}
            options={SOURCE_OPTIONS}
            placeholder="All sources"
            className="w-40"
          />
          <SearchInput
            value={search}
            onChange={setSearch}
            placeholder="Regex search (type, trace, workflow, user...)"
            className="w-72"
          />
          <FilterSelect
            value={eventTypeFilter}
            onChange={setEventTypeFilter}
            options={EVENT_TYPE_OPTIONS}
            placeholder="All event types"
            className="w-48"
          />
          <FilterSelect
            value={errorCodeFilter}
            onChange={setErrorCodeFilter}
            options={[
              { value: 'exists', label: 'Has Error' },
            ]}
            placeholder="Error status"
            className="w-36"
          />
          <SearchInput
            value={userIdFilter}
            onChange={setUserIdFilter}
            placeholder="Filter by user ID..."
            className="w-48"
          />
          <div className="flex-1" />
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
            className="flex items-center gap-1.5"
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
            Advanced
            {showAdvancedFilters ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          </Button>
          {hasActiveFilters && (
            <Button variant="ghost" size="sm" onClick={clearFilters}>
              <X className="w-3.5 h-3.5 mr-1" />
              Clear
            </Button>
          )}
          <span className="text-body-xs text-content-tertiary">
            {auditData?.total || 0} total events
          </span>
        </div>

        {/* Advanced Filters */}
        {showAdvancedFilters && (
          <div className="flex items-center gap-3 pt-3 border-t border-line flex-wrap">
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-content-tertiary" />
              <span className="text-body-xs text-content-secondary">From:</span>
              <input
                type="datetime-local"
                value={fromDate}
                onChange={(e) => { setFromDate(e.target.value); setPage(1); }}
                className="h-8 px-2 rounded-lg bg-surface-secondary/50 border border-line text-body-xs text-content-primary focus:outline-none focus:ring-2 focus:ring-accent/30"
              />
            </div>
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-content-tertiary" />
              <span className="text-body-xs text-content-secondary">To:</span>
              <input
                type="datetime-local"
                value={toDate}
                onChange={(e) => { setToDate(e.target.value); setPage(1); }}
                className="h-8 px-2 rounded-lg bg-surface-secondary/50 border border-line text-body-xs text-content-primary focus:outline-none focus:ring-2 focus:ring-accent/30"
              />
            </div>
            <div className="flex-1" />
            <div className="flex items-center gap-2">
              <span className="text-body-xs text-content-secondary">Sort:</span>
              <FilterSelect
                value={sortBy}
                onChange={(val) => { setSortBy(val); setPage(1); }}
                options={SORT_OPTIONS}
                placeholder="Sort by"
                className="w-32"
              />
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                className="flex items-center gap-1"
              >
                {sortOrder === 'asc' ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                {sortOrder.toUpperCase()}
              </Button>
            </div>
          </div>
        )}
      </Card>

      {/* Active filter badges */}
      {hasActiveFilters && (
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-body-xs text-content-tertiary">Active filters:</span>
          {sourceFilter && (
            <Badge variant="info" size="sm" className="flex items-center gap-1">
              {SOURCE_ICONS[sourceFilter]}
              {SOURCE_OPTIONS.find(o => o.value === sourceFilter)?.label || sourceFilter}
              <button onClick={() => setSourceFilter('')} className="ml-1 hover:text-status-error"><X className="w-3 h-3" /></button>
            </Badge>
          )}
          {search && (
            <Badge variant="info" size="sm" className="flex items-center gap-1">
              <Regex className="w-3 h-3" />
              {search}
              <button onClick={() => setSearch('')} className="ml-1 hover:text-status-error"><X className="w-3 h-3" /></button>
            </Badge>
          )}
          {eventTypeFilter && (
            <Badge variant="info" size="sm" className="flex items-center gap-1">
              Type: {EVENT_TYPE_OPTIONS.find(o => o.value === eventTypeFilter)?.label || eventTypeFilter}
              <button onClick={() => setEventTypeFilter('')} className="ml-1 hover:text-status-error"><X className="w-3 h-3" /></button>
            </Badge>
          )}
          {errorCodeFilter && (
            <Badge variant="error" size="sm" className="flex items-center gap-1">
              Has errors
              <button onClick={() => setErrorCodeFilter('')} className="ml-1 hover:text-status-error"><X className="w-3 h-3" /></button>
            </Badge>
          )}
          {userIdFilter && (
            <Badge variant="info" size="sm" className="flex items-center gap-1">
              <User className="w-3 h-3" />
              {userIdFilter}
              <button onClick={() => setUserIdFilter('')} className="ml-1 hover:text-status-error"><X className="w-3 h-3" /></button>
            </Badge>
          )}
          {fromDate && (
            <Badge variant="info" size="sm" className="flex items-center gap-1">
              From: {new Date(fromDate).toLocaleString()}
              <button onClick={() => setFromDate('')} className="ml-1 hover:text-status-error"><X className="w-3 h-3" /></button>
            </Badge>
          )}
          {toDate && (
            <Badge variant="info" size="sm" className="flex items-center gap-1">
              To: {new Date(toDate).toLocaleString()}
              <button onClick={() => setToDate('')} className="ml-1 hover:text-status-error"><X className="w-3 h-3" /></button>
            </Badge>
          )}
        </div>
      )}

      <DataTable
        columns={columns.map(col => ({
          ...col,
          header: col.sortable ? (
            <button
              onClick={() => handleSort(col.key)}
              className="flex items-center gap-1 hover:text-content-primary transition-colors cursor-pointer"
            >
              {col.header}
              <SortIndicator columnKey={col.key} />
            </button>
          ) : col.header,
        }))}
        data={auditData?.items || []}
        keyExtractor={(entry) => `${entry.source}:${entry.id}`}
        onRowClick={(entry) => { setSelectedEvent(entry); setShowDetailModal(true); }}
        emptyMessage="No audit entries found"
      />

      <Pagination
        currentPage={page}
        totalPages={totalPages}
        onPageChange={setPage}
      />

      {/* Event Detail Modal */}
      {showDetailModal && selectedEvent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <Card className="w-full max-w-2xl flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {SOURCE_ICONS[selectedEvent.source]}
                <h3 className="font-display text-display-xs text-content-primary">
                  {selectedEvent.source.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())} Details
                </h3>
              </div>
              <button onClick={() => { setShowDetailModal(false); setSelectedEvent(null); }} className="p-1 rounded hover:bg-surface-secondary">
                <X className="w-5 h-5 text-content-tertiary" />
              </button>
            </div>
            
            <div className="flex flex-col gap-3">
              <div className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${selectedEvent.error_code ? 'bg-status-error' : 'bg-status-success'}`} />
                <span className="text-body-md font-semibold text-content-primary">{selectedEvent.event_type}</span>
                <Badge variant="default" size="sm">{selectedEvent.source}</Badge>
              </div>
              
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-lg bg-surface-secondary/50">
                  <p className="text-body-xs text-content-tertiary">ID</p>
                  <p className="text-body-sm font-mono text-content-primary truncate">{selectedEvent.id}</p>
                </div>
                <div className="p-3 rounded-lg bg-surface-secondary/50">
                  <p className="text-body-xs text-content-tertiary">Occurred At</p>
                  <p className="text-body-sm text-content-primary">{new Date(selectedEvent.occurred_at).toLocaleString()}</p>
                </div>
                {selectedEvent.user_id && (
                  <div className="p-3 rounded-lg bg-surface-secondary/50">
                    <p className="text-body-xs text-content-tertiary">User ID</p>
                    <p className="text-body-sm font-mono text-content-primary truncate">{selectedEvent.user_id}</p>
                  </div>
                )}
                {selectedEvent.request_id && (
                  <div className="p-3 rounded-lg bg-surface-secondary/50">
                    <p className="text-body-xs text-content-tertiary">Request ID</p>
                    <p className="text-body-sm font-mono text-content-primary truncate">{selectedEvent.request_id}</p>
                  </div>
                )}
                {selectedEvent.trace_id && (
                  <div className="p-3 rounded-lg bg-surface-secondary/50">
                    <p className="text-body-xs text-content-tertiary">Trace ID</p>
                    <p className="text-body-sm font-mono text-content-primary truncate">{selectedEvent.trace_id}</p>
                  </div>
                )}
                {selectedEvent.workflow_id && (
                  <div className="p-3 rounded-lg bg-surface-secondary/50">
                    <p className="text-body-xs text-content-tertiary">Workflow ID</p>
                    <p className="text-body-sm font-mono text-content-primary truncate">{selectedEvent.workflow_id}</p>
                  </div>
                )}
              </div>

              {selectedEvent.error_code && (
                <div className="p-3 rounded-lg bg-status-error/5 border border-status-error/20">
                  <p className="text-body-xs text-content-tertiary mb-1">Error</p>
                  <p className="text-body-sm font-medium text-status-error">{selectedEvent.error_code}</p>
                </div>
              )}

              {selectedEvent.payload && Object.keys(selectedEvent.payload).length > 0 && (
                <div className="flex flex-col gap-2">
                  <p className="text-body-sm font-medium text-content-secondary">Payload</p>
                  <pre className="p-3 rounded-lg bg-surface-secondary/50 text-body-xs font-mono text-content-primary overflow-auto max-h-60">
                    {JSON.stringify(selectedEvent.payload, null, 2)}
                  </pre>
                </div>
              )}
            </div>

            <div className="flex justify-end pt-2 border-t border-line">
              <Button variant="secondary" onClick={() => { setShowDetailModal(false); setSelectedEvent(null); }}>Close</Button>
            </div>
          </Card>
        </div>
      )}
    </AdminPageShell>
  );
}
