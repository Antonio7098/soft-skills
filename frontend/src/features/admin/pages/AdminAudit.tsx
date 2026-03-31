import { useEffect, useState } from 'react';
import { 
  ScrollText,
  Filter,
  AlertTriangle,
  Clock,
  ChevronRight,
  X,
} from 'lucide-react';
import { Card } from '@/design-system/primitives/Card';
import { Button } from '@/design-system/primitives/Button';
import { Badge } from '@/design-system/primitives/Badge';
import { LoadingState } from '@/design-system/patterns/LoadingState';
import { useData } from '@/data';
import { AdminPageShell, MetricCard, DataTable, SearchInput, FilterSelect, Pagination } from '../components';
import type { WorkflowEventView, PaginatedWorkflowEventsView } from '@/data/types';

const EVENT_TYPE_OPTIONS = [
  { value: 'session.started', label: 'Session Started' },
  { value: 'attempt.submitted', label: 'Attempt Submitted' },
  { value: 'assessment.completed', label: 'Assessment Completed' },
  { value: 'pipeline.failed', label: 'Pipeline Failed' },
];

export function AdminAudit() {
  const dataProvider = useData();
  const [events, setEvents] = useState<PaginatedWorkflowEventsView | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [eventTypeFilter, setEventTypeFilter] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 20;
  const [selectedEvent, setSelectedEvent] = useState<WorkflowEventView | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);

  useEffect(() => {
    setLoading(true);
    dataProvider.listWorkflowEvents({
      offset: (page - 1) * pageSize,
      limit: pageSize,
      event_type: eventTypeFilter || undefined,
      trace_id: search || undefined,
    })
      .then((result) => {
        console.log('[AdminAudit] Received events:', result);
        setEvents(result);
      })
      .catch((error) => console.error('[AdminAudit] Error loading events:', error))
      .finally(() => setLoading(false));
  }, [dataProvider, page, eventTypeFilter, search]);

  const columns = [
    {
      key: 'event_type',
      header: 'Event',
      render: (event: WorkflowEventView) => (
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${event.error_code ? 'bg-status-error' : 'bg-status-success'}`} />
          <span className="font-medium">{event.event_type}</span>
        </div>
      ),
    },
    {
      key: 'trace_id',
      header: 'Trace ID',
      width: '140px',
      render: (event: WorkflowEventView) => (
        <span className="font-mono text-body-xs text-content-secondary">
          {event.trace_id?.slice(0, 12) || '—'}...
        </span>
      ),
    },
    {
      key: 'workflow_id',
      header: 'Workflow',
      width: '140px',
      render: (event: WorkflowEventView) => (
        <span className="font-mono text-body-xs text-content-secondary">
          {event.workflow_id?.slice(0, 12) || '—'}...
        </span>
      ),
    },
    {
      key: 'error_code',
      header: 'Error',
      width: '100px',
      render: (event: WorkflowEventView) => (
        event.error_code ? (
          <Badge variant="error" size="sm">{event.error_code}</Badge>
        ) : (
          <span className="text-content-tertiary">—</span>
        )
      ),
    },
    {
      key: 'occurred_at',
      header: 'Time',
      width: '160px',
      render: (event: WorkflowEventView) => (
        <span className="text-content-secondary">
          {new Date(event.occurred_at).toLocaleString()}
        </span>
      ),
    },
    {
      key: 'actions',
      header: '',
      width: '48px',
      render: (event: WorkflowEventView) => (
        <button 
          onClick={() => { setSelectedEvent(event); setShowDetailModal(true); }}
          className="p-1 rounded hover:bg-surface-secondary"
        >
          <ChevronRight className="w-4 h-4 text-content-tertiary" />
        </button>
      ),
    },
  ];

  const totalPages = events ? Math.ceil(events.total / pageSize) : 1;
  const errorCount = events?.items.filter((e) => e.error_code).length || 0;

  if (loading && !events) {
    return (
      <AdminPageShell title="Audit Logs" subtitle="System event tracking">
        <LoadingState message="Loading audit logs..." />
      </AdminPageShell>
    );
  }

  return (
    <AdminPageShell
      title="Audit Logs"
      subtitle="Track workflow events, errors, and system activity"
    >
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Total Events"
          value={events?.total?.toLocaleString() || '0'}
          icon={<ScrollText className="w-4 h-4" />}
        />
        <MetricCard
          label="This Page"
          value={events?.items.length || 0}
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
          value={events?.items[0] ? new Date(events.items[0].occurred_at).toLocaleTimeString() : '—'}
          icon={<Clock className="w-4 h-4" />}
        />
      </div>

      <Card className="flex flex-col gap-4">
        <div className="flex items-center gap-3">
          <SearchInput
            value={search}
            onChange={setSearch}
            placeholder="Search by trace ID..."
            className="w-64"
          />
          <FilterSelect
            value={eventTypeFilter}
            onChange={setEventTypeFilter}
            options={EVENT_TYPE_OPTIONS}
            placeholder="All event types"
            className="w-48"
          />
          <div className="flex-1" />
          <span className="text-body-xs text-content-tertiary">
            {events?.total || 0} total events
          </span>
        </div>
      </Card>

      <DataTable
        columns={columns}
        data={events?.items || []}
        keyExtractor={(event) => event.event_id}
        emptyMessage="No events found"
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
              <h3 className="font-display text-display-xs text-content-primary">Event Details</h3>
              <button onClick={() => { setShowDetailModal(false); setSelectedEvent(null); }} className="p-1 rounded hover:bg-surface-secondary">
                <X className="w-5 h-5 text-content-tertiary" />
              </button>
            </div>
            
            <div className="flex flex-col gap-3">
              <div className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${selectedEvent.error_code ? 'bg-status-error' : 'bg-status-success'}`} />
                <span className="text-body-md font-semibold text-content-primary">{selectedEvent.event_type}</span>
              </div>
              
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-lg bg-surface-secondary/50">
                  <p className="text-body-xs text-content-tertiary">Event ID</p>
                  <p className="text-body-sm font-mono text-content-primary truncate">{selectedEvent.event_id}</p>
                </div>
                <div className="p-3 rounded-lg bg-surface-secondary/50">
                  <p className="text-body-xs text-content-tertiary">Occurred At</p>
                  <p className="text-body-sm text-content-primary">{new Date(selectedEvent.occurred_at).toLocaleString()}</p>
                </div>
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
                  <pre className="p-3 rounded-lg bg-surface-secondary/50 text-body-xs font-mono text-content-primary overflow-auto max-h-40">
                    {JSON.stringify(selectedEvent.payload, null, 2)}
                  </pre>
                </div>
              )}

              <div className="flex flex-col gap-2">
                <p className="text-body-sm font-medium text-content-secondary">Raw Event JSON</p>
                <pre className="p-3 rounded-lg bg-surface-secondary/50 text-body-xs font-mono text-content-primary overflow-auto max-h-60">
                  {JSON.stringify(selectedEvent, null, 2)}
                </pre>
              </div>
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
