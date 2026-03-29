import { useEffect, useState } from 'react';
import { 
  Activity,
  Zap,
  AlertTriangle,
  Clock,
  Server,
  ChevronRight,
} from 'lucide-react';
import { Card } from '@/design-system/primitives/Card';
import { Badge } from '@/design-system/primitives/Badge';
import { LoadingState } from '@/design-system/patterns/LoadingState';
import { useData } from '@/data';
import { AdminPageShell, MetricCard, DataTable, MiniChart } from '../components';
import type { TelemetryOverviewView, TelemetryTraceListView, TelemetryTraceListItemView } from '@/data/types';

export function AdminTelemetry() {
  const dataProvider = useData();
  const [overview, setOverview] = useState<TelemetryOverviewView | null>(null);
  const [traces, setTraces] = useState<TelemetryTraceListView | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      dataProvider.getTelemetryOverview(),
      dataProvider.listTelemetryTraces({ limit: 20 }),
    ])
      .then(([overviewData, tracesData]) => {
        setOverview(overviewData);
        setTraces(tracesData);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [dataProvider]);

  const traceColumns = [
    {
      key: 'operation_name',
      header: 'Operation',
      render: (trace: TelemetryTraceListItemView) => (
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${trace.error_count > 0 ? 'bg-status-error' : 'bg-status-success'}`} />
          <span className="font-medium">{trace.operation_name || 'Unknown'}</span>
        </div>
      ),
    },
    {
      key: 'service_name',
      header: 'Service',
      width: '120px',
      render: (trace: TelemetryTraceListItemView) => (
        <Badge variant="default" size="sm">{trace.service_name || '—'}</Badge>
      ),
    },
    {
      key: 'duration_ms',
      header: 'Duration',
      width: '100px',
      render: (trace: TelemetryTraceListItemView) => (
        <span className={trace.duration_ms && trace.duration_ms > 1000 ? 'text-status-warning' : 'text-content-secondary'}>
          {trace.duration_ms ? `${trace.duration_ms.toFixed(0)}ms` : '—'}
        </span>
      ),
    },
    {
      key: 'span_count',
      header: 'Spans',
      width: '80px',
      render: (trace: TelemetryTraceListItemView) => (
        <span className="text-content-secondary">{trace.span_count}</span>
      ),
    },
    {
      key: 'started_at',
      header: 'Time',
      width: '140px',
      render: (trace: TelemetryTraceListItemView) => (
        <span className="text-content-secondary">
          {trace.started_at ? new Date(trace.started_at).toLocaleString() : '—'}
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

  const latencyData = overview?.latency_distribution?.map((bucket) => ({
    label: `${bucket.bucket_ms}ms`,
    value: bucket.count,
  })) || [];

  if (loading) {
    return (
      <AdminPageShell title="Telemetry" subtitle="Distributed tracing and performance">
        <LoadingState message="Loading telemetry data..." />
      </AdminPageShell>
    );
  }

  return (
    <AdminPageShell
      title="Telemetry"
      subtitle="Monitor distributed traces, provider performance, and system health"
    >
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Provider Calls"
          value={overview?.total_provider_calls?.toLocaleString() || '0'}
          icon={<Zap className="w-4 h-4" />}
        />
        <MetricCard
          label="Success Rate"
          value={overview?.provider_call_success_rate ? `${(overview.provider_call_success_rate * 100).toFixed(1)}%` : '—'}
          icon={<Activity className="w-4 h-4" />}
          trend={overview?.provider_call_success_rate && overview.provider_call_success_rate > 0.95 ? 'positive' : 'negative'}
        />
        <MetricCard
          label="Avg Latency"
          value={overview?.avg_provider_latency_ms ? `${overview.avg_provider_latency_ms.toFixed(0)}ms` : '—'}
          icon={<Clock className="w-4 h-4" />}
        />
        <MetricCard
          label="Total Errors"
          value={overview?.total_errors || 0}
          icon={<AlertTriangle className="w-4 h-4" />}
          trend={overview?.total_errors && overview.total_errors > 0 ? 'negative' : 'positive'}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h3 className="font-display text-body-md font-semibold text-content-primary">
              Recent Traces
            </h3>
            <Badge variant="default" size="sm">{traces?.total || 0} total</Badge>
          </div>
          <DataTable
            columns={traceColumns}
            data={traces?.traces || []}
            keyExtractor={(trace) => trace.trace_id}
            emptyMessage="No traces found"
          />
        </Card>

        <div className="flex flex-col gap-4">
          <Card className="flex flex-col gap-4">
            <h3 className="font-display text-body-md font-semibold text-content-primary">
              Latency Distribution
            </h3>
            {latencyData.length > 0 ? (
              <MiniChart data={latencyData} height={80} color="accent" />
            ) : (
              <p className="text-body-sm text-content-tertiary py-4 text-center">No data</p>
            )}
          </Card>

          <Card className="flex flex-col gap-4">
            <h3 className="font-display text-body-md font-semibold text-content-primary">
              Pipeline Health
            </h3>
            <div className="flex flex-col gap-2">
              {overview?.pipeline_health?.slice(0, 4).map((pipeline) => (
                <div 
                  key={pipeline.pipeline_name}
                  className="flex items-center gap-3 py-2 px-3 rounded-lg bg-surface-secondary/50"
                >
                  <Server className="w-4 h-4 text-content-tertiary" />
                  <div className="flex-1 min-w-0">
                    <p className="text-body-sm font-medium text-content-primary truncate">
                      {pipeline.pipeline_name}
                    </p>
                  </div>
                  <Badge 
                    variant={pipeline.success_rate && pipeline.success_rate > 0.9 ? 'success' : 'warning'} 
                    size="sm"
                  >
                    {pipeline.success_rate ? `${(pipeline.success_rate * 100).toFixed(0)}%` : '—'}
                  </Badge>
                </div>
              ))}
              {(!overview?.pipeline_health || overview.pipeline_health.length === 0) && (
                <p className="text-body-sm text-content-tertiary py-4 text-center">No pipelines</p>
              )}
            </div>
          </Card>
        </div>
      </div>

      {overview?.provider_metrics && overview.provider_metrics.length > 0 && (
        <Card className="flex flex-col gap-4">
          <h3 className="font-display text-body-md font-semibold text-content-primary">
            Provider Metrics
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {overview.provider_metrics.slice(0, 6).map((metric) => (
              <div 
                key={`${metric.provider}-${metric.operation}`}
                className="p-4 rounded-lg bg-surface-secondary/50 border border-line"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-body-sm font-medium text-content-primary">
                    {metric.provider}
                  </span>
                  <Badge 
                    variant={metric.success_rate && metric.success_rate > 0.95 ? 'success' : 'warning'} 
                    size="sm"
                  >
                    {metric.success_rate ? `${(metric.success_rate * 100).toFixed(1)}%` : '—'}
                  </Badge>
                </div>
                <p className="text-body-xs text-content-tertiary mb-3">{metric.operation}</p>
                <div className="grid grid-cols-2 gap-2 text-body-xs">
                  <div>
                    <span className="text-content-tertiary">Calls</span>
                    <p className="font-medium text-content-primary">{metric.call_count}</p>
                  </div>
                  <div>
                    <span className="text-content-tertiary">Avg Latency</span>
                    <p className="font-medium text-content-primary">
                      {metric.avg_latency_ms ? `${metric.avg_latency_ms.toFixed(0)}ms` : '—'}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {overview?.error_breakdown && overview.error_breakdown.length > 0 && (
        <Card className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h3 className="font-display text-body-md font-semibold text-content-primary">
              Error Breakdown
            </h3>
            <Badge variant="error" size="sm">{overview.error_breakdown.length} types</Badge>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {overview.error_breakdown.slice(0, 4).map((error) => (
              <div 
                key={error.error_type}
                className="p-3 rounded-lg bg-status-error/5 border border-status-error/20"
              >
                <p className="text-body-sm font-medium text-content-primary">{error.error_type}</p>
                <p className="text-body-xs text-content-tertiary">{error.error_code || 'No code'}</p>
                <div className="flex items-center justify-between mt-2">
                  <span className="text-body-md font-semibold text-status-error">{error.count}</span>
                  <span className="text-body-xs text-content-tertiary">{error.percentage.toFixed(1)}%</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </AdminPageShell>
  );
}
