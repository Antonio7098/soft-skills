import { useEffect, useState } from 'react';
import { 
  FlaskConical,
  Play,
  CheckCircle,
  Clock,
  Zap,
} from 'lucide-react';
import { Card } from '@/design-system/primitives/Card';
import { Button } from '@/design-system/primitives/Button';
import { Badge } from '@/design-system/primitives/Badge';
import { LoadingState } from '@/design-system/patterns/LoadingState';
import { useData } from '@/data';
import { AdminPageShell, MetricCard, DataTable, StatusBadge } from '../components';
import type { EvaluationSuiteView, EvaluationRunView, EvaluationDashboardView } from '@/data/types';

export function AdminEvaluations() {
  const dataProvider = useData();
  const [suites, setSuites] = useState<EvaluationSuiteView[]>([]);
  const [runs, setRuns] = useState<EvaluationRunView[]>([]);
  const [dashboard, setDashboard] = useState<EvaluationDashboardView | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      dataProvider.listEvalSuites(),
      dataProvider.listEvalRuns({ limit: 20 }),
      dataProvider.getEvalDashboard(),
    ])
      .then(([suitesData, runsData, dashboardData]) => {
        setSuites(suitesData);
        setRuns(runsData);
        setDashboard(dashboardData);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [dataProvider]);

  const runColumns = [
    {
      key: 'suite_id',
      header: 'Suite',
      render: (run: EvaluationRunView) => (
        <div className="flex flex-col gap-0.5">
          <span className="font-medium">{run.suite_id}</span>
          <span className="text-body-xs text-content-tertiary">{run.suite_type}</span>
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      width: '100px',
      render: (run: EvaluationRunView) => (
        <StatusBadge status={run.passed ? 'passed' : 'failed'} />
      ),
    },
    {
      key: 'pass_rate',
      header: 'Pass Rate',
      width: '100px',
      render: (run: EvaluationRunView) => (
        <span className={run.pass_rate && run.pass_rate > 0.8 ? 'text-status-success' : 'text-status-warning'}>
          {run.pass_rate ? `${(run.pass_rate * 100).toFixed(1)}%` : '—'}
        </span>
      ),
    },
    {
      key: 'case_count',
      header: 'Cases',
      width: '80px',
      render: (run: EvaluationRunView) => (
        <span className="text-content-secondary">{run.case_count}</span>
      ),
    },
    {
      key: 'avg_latency_ms',
      header: 'Latency',
      width: '100px',
      render: (run: EvaluationRunView) => (
        <span className="text-content-secondary">
          {run.avg_latency_ms ? `${run.avg_latency_ms.toFixed(0)}ms` : '—'}
        </span>
      ),
    },
    {
      key: 'started_at',
      header: 'Started',
      width: '140px',
      render: (run: EvaluationRunView) => (
        <span className="text-content-secondary">
          {new Date(run.started_at).toLocaleString()}
        </span>
      ),
    },
  ];

  if (loading) {
    return (
      <AdminPageShell title="Evaluations" subtitle="Model performance and quality metrics">
        <LoadingState message="Loading evaluation data..." />
      </AdminPageShell>
    );
  }

  return (
    <AdminPageShell
      title="Evaluations"
      subtitle="Monitor model performance, run evaluation suites, and track quality metrics"
      actions={
        <Button icon={<Play className="w-4 h-4" />}>
          Run Evaluation
        </Button>
      }
    >
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Total Runs"
          value={dashboard?.total_runs || 0}
          icon={<FlaskConical className="w-4 h-4" />}
        />
        <MetricCard
          label="Pass Rate"
          value={dashboard?.pass_fail?.pass_rate ? `${(dashboard.pass_fail.pass_rate * 100).toFixed(1)}%` : '—'}
          icon={<CheckCircle className="w-4 h-4" />}
          trend={dashboard?.pass_fail?.pass_rate && dashboard.pass_fail.pass_rate > 0.9 ? 'positive' : 'negative'}
        />
        <MetricCard
          label="Total Cases"
          value={dashboard?.total_cases?.toLocaleString() || '0'}
          icon={<Zap className="w-4 h-4" />}
        />
        <MetricCard
          label="Est. Cost"
          value={dashboard?.estimated_cost_usd ? `$${dashboard.estimated_cost_usd.toFixed(2)}` : '—'}
          icon={<Clock className="w-4 h-4" />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h3 className="font-display text-body-md font-semibold text-content-primary">
              Recent Runs
            </h3>
            <Badge variant="default" size="sm">{runs.length} runs</Badge>
          </div>
          <DataTable
            columns={runColumns}
            data={runs.slice(0, 10)}
            keyExtractor={(run) => run.evaluation_run_id}
            emptyMessage="No evaluation runs yet"
          />
        </Card>

        <Card className="flex flex-col gap-4">
          <h3 className="font-display text-body-md font-semibold text-content-primary">
            Evaluation Suites
          </h3>
          <div className="flex flex-col gap-2">
            {suites.slice(0, 6).map((suite) => (
              <div 
                key={suite.suite_id}
                className="flex items-center gap-3 py-2.5 px-3 rounded-lg hover:bg-surface-secondary/50 transition-colors cursor-pointer"
              >
                <div className="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center">
                  <FlaskConical className="w-4 h-4 text-accent" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-body-sm font-medium text-content-primary truncate">
                    {suite.name}
                  </p>
                  <p className="text-body-xs text-content-tertiary">{suite.suite_type}</p>
                </div>
                <Button variant="ghost" size="sm" icon={<Play className="w-3.5 h-3.5" />}>
                  Run
                </Button>
              </div>
            ))}
            {suites.length === 0 && (
              <p className="text-body-sm text-content-tertiary py-4 text-center">No suites configured</p>
            )}
          </div>
        </Card>
      </div>

      {dashboard?.error_breakdown && dashboard.error_breakdown.length > 0 && (
        <Card className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h3 className="font-display text-body-md font-semibold text-content-primary">
              Error Breakdown
            </h3>
            <Badge variant="error" size="sm">{dashboard.error_breakdown.length} error types</Badge>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {dashboard.error_breakdown.slice(0, 4).map((error) => (
              <div key={error.error_code} className="flex flex-col gap-1 p-3 rounded-lg bg-surface-secondary/50">
                <span className="text-body-xs text-content-tertiary">{error.error_code}</span>
                <span className="text-body-md font-semibold text-content-primary">{error.count}</span>
                <span className="text-body-xs text-status-error">{error.percentage.toFixed(1)}%</span>
              </div>
            ))}
          </div>
        </Card>
      )}
    </AdminPageShell>
  );
}
