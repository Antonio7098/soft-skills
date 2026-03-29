import { useEffect, useState } from 'react';
import { 
  ScrollText,
  Filter,
  AlertTriangle,
  Clock,
  ChevronRight,
} from 'lucide-react';
import { Card } from '@/design-system/primitives/Card';
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

  useEffect(() => {
    setLoading(true);
    dataProvider.listWorkflowEvents({
      offset: (page - 1) * pageSize,
      limit: pageSize,
      event_type: eventTypeFilter || undefined,
      trace_id: search || undefined,
    })
      .then(setEvents)
      .catch(console.error)
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
      render: () => (
        <ChevronRight className="w-4 h-4 text-content-tertiary" />
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
    </AdminPageShell>
  );
}
