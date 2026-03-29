import { useEffect, useState } from 'react';
import { 
  GitBranch,
  Play,
  CheckCircle,
  XCircle,
  ChevronRight,
  X,
  BarChart3,
} from 'lucide-react';
import { Card } from '@/design-system/primitives/Card';
import { Button } from '@/design-system/primitives/Button';
import { LoadingState } from '@/design-system/patterns/LoadingState';
import { useData } from '@/data';
import { AdminPageShell, MetricCard, DataTable, StatusBadge } from '../components';
import type { PipelineDefinitionView, PipelineRunSummaryView, PipelineMetricsView } from '@/data/types';

export function AdminPipelines() {
  const dataProvider = useData();
  const [pipelines, setPipelines] = useState<PipelineDefinitionView[]>([]);
  const [selectedPipeline, setSelectedPipeline] = useState<string | null>(null);
  const [runs, setRuns] = useState<PipelineRunSummaryView[]>([]);
  const [loading, setLoading] = useState(true);
  const [showMetricsModal, setShowMetricsModal] = useState(false);
  const [metrics, setMetrics] = useState<PipelineMetricsView | null>(null);
  const [metricsLoading, setMetricsLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    dataProvider.listPipelines()
      .then(setPipelines)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [dataProvider]);

  useEffect(() => {
    if (selectedPipeline) {
      dataProvider.listPipelineRuns(selectedPipeline, { limit: 20 })
        .then(setRuns)
        .catch(console.error);
    } else {
      setRuns([]);
    }
  }, [dataProvider, selectedPipeline]);

  const handleViewMetrics = async () => {
    if (!selectedPipeline) return;
    setMetricsLoading(true);
    setShowMetricsModal(true);
    try {
      const data = await dataProvider.getPipelineMetrics(selectedPipeline);
      setMetrics(data);
    } catch (error) {
      console.error('Failed to load metrics:', error);
    } finally {
      setMetricsLoading(false);
    }
  };

  const runColumns = [
    {
      key: 'pipeline_run_id',
      header: 'Run ID',
      render: (run: PipelineRunSummaryView) => (
        <span className="font-mono text-body-xs">{run.pipeline_run_id.slice(0, 8)}...</span>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      width: '100px',
      render: (run: PipelineRunSummaryView) => (
        <StatusBadge status={run.status as 'completed' | 'running' | 'failed'} />
      ),
    },
    {
      key: 'duration_ms',
      header: 'Duration',
      width: '100px',
      render: (run: PipelineRunSummaryView) => (
        <span className="text-content-secondary">
          {run.duration_ms ? `${(run.duration_ms / 1000).toFixed(2)}s` : '—'}
        </span>
      ),
    },
    {
      key: 'started_at',
      header: 'Started',
      width: '140px',
      render: (run: PipelineRunSummaryView) => (
        <span className="text-content-secondary">
          {run.started_at ? new Date(run.started_at).toLocaleString() : '—'}
        </span>
      ),
    },
  ];

  if (loading) {
    return (
      <AdminPageShell title="Pipelines" subtitle="Workflow execution monitoring">
        <LoadingState message="Loading pipelines..." />
      </AdminPageShell>
    );
  }

  const totalRuns = runs.length;
  const successRuns = runs.filter((r) => r.status === 'completed').length;
  const failedRuns = runs.filter((r) => r.status === 'failed').length;

  return (
    <AdminPageShell
      title="Pipelines"
      subtitle="Monitor workflow executions, view DAGs, and track performance metrics"
    >
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Total Pipelines"
          value={pipelines.length}
          icon={<GitBranch className="w-4 h-4" />}
        />
        <MetricCard
          label="Recent Runs"
          value={totalRuns}
          icon={<Play className="w-4 h-4" />}
        />
        <MetricCard
          label="Success Rate"
          value={totalRuns > 0 ? `${((successRuns / totalRuns) * 100).toFixed(0)}%` : '—'}
          icon={<CheckCircle className="w-4 h-4" />}
          trend={successRuns / totalRuns > 0.9 ? 'positive' : 'negative'}
        />
        <MetricCard
          label="Failed"
          value={failedRuns}
          icon={<XCircle className="w-4 h-4" />}
          trend={failedRuns > 0 ? 'negative' : 'positive'}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="flex flex-col gap-4">
          <h3 className="font-display text-body-md font-semibold text-content-primary">
            Pipelines
          </h3>
          <div className="flex flex-col gap-2">
            {pipelines.map((pipeline) => (
              <div 
                key={pipeline.pipeline_name}
                onClick={() => setSelectedPipeline(pipeline.pipeline_name)}
                className={`flex items-center gap-3 py-2.5 px-3 rounded-lg transition-colors cursor-pointer ${
                  selectedPipeline === pipeline.pipeline_name 
                    ? 'bg-accent/10 border border-accent/20' 
                    : 'hover:bg-surface-secondary/50'
                }`}
              >
                <div className="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center">
                  <GitBranch className="w-4 h-4 text-accent" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-body-sm font-medium text-content-primary truncate">
                    {pipeline.pipeline_name}
                  </p>
                  <p className="text-body-xs text-content-tertiary">
                    {pipeline.stage_count} stages
                  </p>
                </div>
                <ChevronRight className="w-4 h-4 text-content-tertiary" />
              </div>
            ))}
            {pipelines.length === 0 && (
              <p className="text-body-sm text-content-tertiary py-4 text-center">No pipelines found</p>
            )}
          </div>
        </Card>

        <Card className="lg:col-span-2 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h3 className="font-display text-body-md font-semibold text-content-primary">
              {selectedPipeline ? `${selectedPipeline} Runs` : 'Select a Pipeline'}
            </h3>
            {selectedPipeline && (
              <Button variant="secondary" size="sm" icon={<BarChart3 className="w-4 h-4" />} onClick={handleViewMetrics}>
                View Metrics
              </Button>
            )}
          </div>
          {selectedPipeline && runs.length > 0 ? (
            <DataTable
              columns={runColumns}
              data={runs}
              keyExtractor={(run) => run.pipeline_run_id}
              emptyMessage="No runs found"
            />
          ) : (
            <div className="flex items-center justify-center py-12">
              <p className="text-body-sm text-content-tertiary">
                {selectedPipeline ? 'No runs found for this pipeline' : 'Click a pipeline to view runs'}
              </p>
            </div>
          )}
        </Card>
      </div>

      {/* Metrics Modal */}
      {showMetricsModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-2xl flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h3 className="font-display text-display-xs text-content-primary">
                {selectedPipeline} Metrics
              </h3>
              <button onClick={() => { setShowMetricsModal(false); setMetrics(null); }} className="p-1 rounded hover:bg-surface-secondary">
                <X className="w-5 h-5 text-content-tertiary" />
              </button>
            </div>
            {metricsLoading ? (
              <div className="py-8">
                <LoadingState message="Loading metrics..." />
              </div>
            ) : metrics ? (
              <div className="flex flex-col gap-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-3 rounded-lg bg-surface-secondary/50">
                    <p className="text-body-xs text-content-tertiary">Total Runs</p>
                    <p className="text-body-lg font-semibold text-content-primary">{metrics.total_runs}</p>
                  </div>
                  <div className="p-3 rounded-lg bg-surface-secondary/50">
                    <p className="text-body-xs text-content-tertiary">Success Rate</p>
                    <p className="text-body-lg font-semibold text-status-success">
                      {(metrics.success_rate * 100).toFixed(1)}%
                    </p>
                  </div>
                  <div className="p-3 rounded-lg bg-surface-secondary/50">
                    <p className="text-body-xs text-content-tertiary">Avg Duration</p>
                    <p className="text-body-lg font-semibold text-content-primary">
                      {(metrics.avg_duration_ms / 1000).toFixed(2)}s
                    </p>
                  </div>
                  <div className="p-3 rounded-lg bg-surface-secondary/50">
                    <p className="text-body-xs text-content-tertiary">P95 Duration</p>
                    <p className="text-body-lg font-semibold text-content-primary">
                      {(metrics.p95_duration_ms / 1000).toFixed(2)}s
                    </p>
                  </div>
                </div>
                {metrics.stage_metrics && metrics.stage_metrics.length > 0 && (
                  <div>
                    <h4 className="text-body-sm font-medium text-content-secondary mb-2">Stage Breakdown</h4>
                    <div className="flex flex-col gap-2">
                      {metrics.stage_metrics.map((stage) => (
                        <div key={stage.stage_name} className="flex items-center justify-between p-2 rounded-lg bg-surface-secondary/30">
                          <span className="text-body-sm text-content-primary">{stage.stage_name}</span>
                          <div className="flex items-center gap-4">
                            <span className="text-body-xs text-content-tertiary">
                              Avg: {((stage.avg_duration_ms ?? 0) / 1000).toFixed(2)}s
                            </span>
                            <span className="text-body-xs text-status-success">
                              {((stage.success_count / stage.invocation_count) * 100).toFixed(0)}% success
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-body-sm text-content-tertiary py-8 text-center">No metrics available</p>
            )}
            <div className="flex justify-end pt-2">
              <Button variant="secondary" onClick={() => { setShowMetricsModal(false); setMetrics(null); }}>Close</Button>
            </div>
          </Card>
        </div>
      )}
    </AdminPageShell>
  );
}
