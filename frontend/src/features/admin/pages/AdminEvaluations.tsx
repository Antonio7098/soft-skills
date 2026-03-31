import { useEffect, useState, useMemo } from 'react';
import {
  FlaskConical,
  Play,
  CheckCircle,
  Clock,
  Zap,
  X,
  GitCompare,
} from 'lucide-react';
import { Card } from '@/design-system/primitives/Card';
import { Button } from '@/design-system/primitives/Button';
import { Badge } from '@/design-system/primitives/Badge';
import { LoadingState } from '@/design-system/patterns/LoadingState';
import { FilterSelect } from '../components/FilterSelect';
import { useData } from '@/data';
import { AdminPageShell, MetricCard, DataTable, StatusBadge } from '../components';
import type { EvaluationSuiteView, EvaluationRunView, EvaluationDashboardView, ProviderModel } from '@/data/types';

type GroupByOption = 'none' | 'model' | 'run';

interface RunEvaluationModalProps {
  suite: EvaluationSuiteView;
  models: ProviderModel[];
  onRun: (suiteId: string, provider: string, modelSlugs: string[]) => void;
  onClose: () => void;
}

const AVAILABLE_PROVIDERS = [
  { id: 'openrouter', name: 'OpenRouter' },
];

function RunEvaluationModal({ suite, models, onRun, onClose }: RunEvaluationModalProps) {
  const [selectedProvider, setSelectedProvider] = useState<string>('openrouter');
  const [selectedModels, setSelectedModels] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const filteredModels = models.filter(m => m.provider === selectedProvider);

  const handleSubmit = async () => {
    if (selectedModels.length === 0) return;
    setIsSubmitting(true);
    await onRun(suite.suite_id, selectedProvider, selectedModels);
    setIsSubmitting(false);
    onClose();
  };

  const toggleModel = (modelId: string) => {
    setSelectedModels(prev => 
      prev.includes(modelId) 
        ? prev.filter(m => m !== modelId)
        : [...prev, modelId]
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-surface-primary border border-line rounded-xl p-6 w-full max-w-md shadow-xl">
        <button 
          onClick={onClose}
          className="absolute top-4 right-4 p-1 rounded-lg hover:bg-surface-secondary/50 transition-colors"
        >
          <X className="w-5 h-5 text-content-tertiary" />
        </button>
        
        <h2 className="text-lg font-semibold text-content-primary mb-1">
          Run Evaluation
        </h2>
        <p className="text-body-sm text-content-secondary mb-6">
          Select provider and models to evaluate with {suite.name}
        </p>

        <div className="mb-4">
          <label className="block text-body-sm font-medium text-content-primary mb-2">
            Provider
          </label>
          <select
            value={selectedProvider}
            onChange={(e) => {
              setSelectedProvider(e.target.value);
              setSelectedModels([]);
            }}
            className="w-full h-9 pl-3 pr-8 rounded-lg bg-surface-secondary/50 border border-line text-body-sm text-content-primary focus:outline-none focus:ring-2 focus:ring-accent/30"
          >
            {AVAILABLE_PROVIDERS.map(p => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
        </div>

        <div className="mb-6">
          <label className="block text-body-sm font-medium text-content-primary mb-2">
            Select Models
          </label>
          <div className="max-h-60 overflow-y-auto border border-line rounded-lg divide-y divide-line">
            {filteredModels.map(model => (
              <label 
                key={model.id}
                className="flex items-center gap-3 p-3 cursor-pointer hover:bg-surface-secondary/30 transition-colors"
              >
                <input 
                  type="checkbox"
                  checked={selectedModels.includes(model.id)}
                  onChange={() => toggleModel(model.id)}
                  className="w-4 h-4 rounded border-line text-accent focus:ring-accent/30"
                />
                <div className="flex-1 min-w-0">
                  <p className="text-body-sm font-medium text-content-primary truncate">
                    {model.name}
                  </p>
                  <p className="text-body-xs text-content-tertiary truncate">
                    {model.id}
                  </p>
                </div>
              </label>
            ))}
            {filteredModels.length === 0 && (
              <p className="p-4 text-body-sm text-content-tertiary text-center">
                No models available for {AVAILABLE_PROVIDERS.find(p => p.id === selectedProvider)?.name}.
              </p>
            )}
          </div>
        </div>

        <div className="flex gap-3 justify-end">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button 
            onClick={handleSubmit}
            disabled={selectedModels.length === 0}
            loading={isSubmitting}
          >
            Run with {selectedModels.length} model{selectedModels.length !== 1 ? 's' : ''}
          </Button>
        </div>
      </div>
    </div>
  );
}

interface ComparisonModalProps {
  runs: EvaluationRunView[];
  onClose: () => void;
}

function RunDetailModal({ run, onClose }: { run: EvaluationRunView; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-surface-primary border border-line rounded-xl p-6 w-full max-w-2xl shadow-xl">
        <button 
          onClick={onClose}
          className="absolute top-4 right-4 p-1 rounded-lg hover:bg-surface-secondary/50 transition-colors"
        >
          <X className="w-5 h-5 text-content-tertiary" />
        </button>
        
        <h2 className="text-lg font-semibold text-content-primary mb-6">
          Evaluation Run Details
        </h2>

        <div className="grid grid-cols-2 gap-6 mb-6">
          <div>
            <p className="text-body-xs text-content-tertiary mb-1">Run ID</p>
            <p className="text-body-sm font-mono text-content-primary">{run.evaluation_run_id}</p>
          </div>
          <div>
            <p className="text-body-xs text-content-tertiary mb-1">Status</p>
            <StatusBadge status={run.passed ? 'passed' : 'failed'} />
          </div>
          <div>
            <p className="text-body-xs text-content-tertiary mb-1">Suite</p>
            <p className="text-body-sm text-content-primary">{run.suite_id}</p>
          </div>
          <div>
            <p className="text-body-xs text-content-tertiary mb-1">Suite Type</p>
            <p className="text-body-sm text-content-primary">{run.suite_type}</p>
          </div>
          <div>
            <p className="text-body-xs text-content-tertiary mb-1">Pass Rate</p>
            <p className={`text-body-sm font-medium ${run.pass_rate && run.pass_rate > 0.8 ? 'text-status-success' : 'text-status-warning'}`}>
              {run.pass_rate ? `${(run.pass_rate * 100).toFixed(1)}%` : '—'}
            </p>
          </div>
          <div>
            <p className="text-body-xs text-content-tertiary mb-1">Case Count</p>
            <p className="text-body-sm text-content-primary">{run.case_count}</p>
          </div>
        </div>

        <div className="mb-6">
          <p className="text-body-xs text-content-tertiary mb-2">Models</p>
          <div className="flex flex-wrap gap-2">
            {run.model_slugs.map((model, i) => (
              <Badge key={i} variant="default" size="sm">{model}</Badge>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4 mb-6 p-4 bg-surface-secondary/30 rounded-lg">
          <div>
            <p className="text-body-xs text-content-tertiary">Avg Latency</p>
            <p className="text-body-md font-medium text-content-primary">
              {run.avg_latency_ms ? `${run.avg_latency_ms.toFixed(0)}ms` : '—'}
            </p>
          </div>
          <div>
            <p className="text-body-xs text-content-tertiary">Total Tokens</p>
            <p className="text-body-md font-medium text-content-primary">{run.total_tokens.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-body-xs text-content-tertiary">Est. Cost</p>
            <p className="text-body-md font-medium text-content-primary">—</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-body-xs text-content-tertiary mb-1">Started</p>
            <p className="text-body-sm text-content-primary">{new Date(run.started_at).toLocaleString()}</p>
          </div>
          <div>
            <p className="text-body-xs text-content-tertiary mb-1">Completed</p>
            <p className="text-body-sm text-content-primary">
              {run.completed_at ? new Date(run.completed_at).toLocaleString() : '—'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function ComparisonModal({ runs, onClose }: ComparisonModalProps) {
  const [groupBy, setGroupBy] = useState<GroupByOption>('model');

  const groupedData = useMemo(() => {
    if (groupBy === 'none') {
      return { 'All Runs': runs };
    }
    
    const groups: Record<string, EvaluationRunView[]> = {};
    
    for (const run of runs) {
      let key: string;
      if (groupBy === 'model') {
        key = run.model_slugs.join(', ') || 'unknown';
      } else {
        key = run.evaluation_run_id;
      }
      
      if (!groups[key]) {
        groups[key] = [];
      }
      groups[key]!.push(run);
    }
    
    return groups;
  }, [runs, groupBy]);

  const groupEntries = Object.entries(groupedData);

  const summaryMetrics = useMemo(() => {
    if (groupBy === 'model') {
      const modelMetrics: Record<string, { runs: number; passed: number; cases: number; totalTokens: number; avgLatency: number }> = {};
      for (const run of runs) {
        const key = run.model_slugs.join(', ') || 'unknown';
        if (!modelMetrics[key]) {
          modelMetrics[key] = { runs: 0, passed: 0, cases: 0, totalTokens: 0, avgLatency: 0 };
        }
        modelMetrics[key].runs += 1;
        if (run.passed) modelMetrics[key].passed += 1;
        modelMetrics[key].cases += run.case_count;
        modelMetrics[key].totalTokens += run.total_tokens;
        modelMetrics[key].avgLatency += run.avg_latency_ms || 0;
      }
      return Object.entries(modelMetrics).map(([model, m]) => ({
        model,
        runs: m.runs,
        passRate: m.runs > 0 ? m.passed / m.runs : 0,
        avgLatency: m.runs > 0 ? m.avgLatency / m.runs : 0,
        totalCases: m.cases,
        totalTokens: m.totalTokens,
      }));
    }
    return [];
  }, [runs, groupBy]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-surface-primary border border-line rounded-xl p-6 w-full max-w-4xl max-h-[80vh] overflow-hidden shadow-xl flex flex-col">
        <button 
          onClick={onClose}
          className="absolute top-4 right-4 p-1 rounded-lg hover:bg-surface-secondary/50 transition-colors"
        >
          <X className="w-5 h-5 text-content-tertiary" />
        </button>
        
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-lg font-semibold text-content-primary">
              Compare Runs
            </h2>
            <p className="text-body-sm text-content-secondary">
              {runs.length} evaluation runs
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-body-sm text-content-secondary">Group by:</span>
            <FilterSelect
              value={groupBy}
              onChange={(v) => setGroupBy(v as GroupByOption)}
              options={[
                { value: 'none', label: 'No grouping' },
                { value: 'model', label: 'Model' },
                { value: 'run', label: 'Run' },
              ]}
              className="w-32"
            />
          </div>
        </div>

        {groupBy === 'model' && summaryMetrics.length > 0 && (
          <div className="mb-6 p-4 bg-surface-secondary/30 rounded-lg">
            <h4 className="text-body-sm font-medium text-content-primary mb-3">Summary by Model</h4>
            <div className="grid grid-cols-5 gap-4 text-body-xs text-content-secondary border-b border-line pb-2 mb-2">
              <span>Model</span>
              <span>Runs</span>
              <span>Pass Rate</span>
              <span>Avg Latency</span>
              <span>Total Cases</span>
            </div>
            {summaryMetrics.map((m) => (
              <div key={m.model} className="grid grid-cols-5 gap-4 text-body-sm py-2 border-b border-line/50">
                <span className="font-medium text-content-primary truncate">{m.model}</span>
                <span>{m.runs}</span>
                <span className={m.passRate >= 0.8 ? 'text-status-success' : 'text-status-warning'}>
                  {(m.passRate * 100).toFixed(1)}%
                </span>
                <span>{m.avgLatency.toFixed(0)}ms</span>
                <span>{m.totalCases}</span>
              </div>
            ))}
          </div>
        )}

        <div className="flex-1 overflow-y-auto">
          {groupEntries.map(([groupName, groupRuns]) => (
            <div key={groupName} className="mb-6">
              <h4 className="text-body-sm font-medium text-content-primary mb-3 sticky top-0 bg-surface-primary py-2 border-b border-line">
                {groupName} ({groupRuns.length} runs)
              </h4>
              <table className="w-full text-body-sm">
                <thead>
                  <tr className="text-left text-content-tertiary border-b border-line">
                    <th className="pb-2 font-medium">Run ID</th>
                    <th className="pb-2 font-medium">Suite</th>
                    <th className="pb-2 font-medium">Status</th>
                    <th className="pb-2 font-medium">Pass Rate</th>
                    <th className="pb-2 font-medium">Cases</th>
                    <th className="pb-2 font-medium">Latency</th>
                    <th className="pb-2 font-medium">Tokens</th>
                    <th className="pb-2 font-medium">Started</th>
                  </tr>
                </thead>
                <tbody>
                  {groupRuns.map((run) => (
                    <tr key={run.evaluation_run_id} className="border-b border-line/50 hover:bg-surface-secondary/30">
                      <td className="py-2 font-mono text-xs">{run.evaluation_run_id.slice(0, 12)}</td>
                      <td className="py-2">{run.suite_id}</td>
                      <td className="py-2">
                        <StatusBadge status={run.passed ? 'passed' : 'failed'} />
                      </td>
                      <td className="py-2">
                        <span className={run.pass_rate && run.pass_rate > 0.8 ? 'text-status-success' : 'text-status-warning'}>
                          {run.pass_rate ? `${(run.pass_rate * 100).toFixed(1)}%` : '—'}
                        </span>
                      </td>
                      <td className="py-2">{run.case_count}</td>
                      <td className="py-2">{run.avg_latency_ms ? `${run.avg_latency_ms.toFixed(0)}ms` : '—'}</td>
                      <td className="py-2">{run.total_tokens.toLocaleString()}</td>
                      <td className="py-2 text-content-tertiary">{new Date(run.started_at).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export function AdminEvaluations() {
  const dataProvider = useData();
  const [suites, setSuites] = useState<EvaluationSuiteView[]>([]);
  const [runs, setRuns] = useState<EvaluationRunView[]>([]);
  const [dashboard, setDashboard] = useState<EvaluationDashboardView | null>(null);
  const [models, setModels] = useState<ProviderModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [runningEval, setRunningEval] = useState<string | null>(null);
  const [showRunModal, setShowRunModal] = useState(false);
  const [selectedSuite, setSelectedSuite] = useState<EvaluationSuiteView | null>(null);
  const [groupBy, setGroupBy] = useState<GroupByOption>('none');
  const [showCompare, setShowCompare] = useState(false);
  const [selectedRun, setSelectedRun] = useState<EvaluationRunView | null>(null);

  const refreshData = () => {
    setLoading(true);
    Promise.all([
      dataProvider.listEvalSuites(),
      dataProvider.listEvalRuns({ limit: 20 }),
      dataProvider.getEvalDashboard(),
      dataProvider.listOpenRouterModels(),
    ])
      .then(([suitesData, runsData, dashboardData, modelsData]) => {
        setSuites(suitesData);
        setRuns(runsData);
        setDashboard(dashboardData);
        setModels(modelsData);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    refreshData();
  }, [dataProvider]);

  const handleRunEvaluation = async (suiteId: string, provider: string, modelSlugs: string[]) => {
    setRunningEval(suiteId);
    try {
      await dataProvider.triggerEvalRun({ 
        suite_id: suiteId, 
        model_slugs: modelSlugs.map(m => `${provider}/${m}`) 
      });
      refreshData();
    } catch (error) {
      console.error('Failed to run evaluation:', error);
    } finally {
      setRunningEval(null);
    }
  };

  const openRunModal = (suite: EvaluationSuiteView) => {
    setSelectedSuite(suite);
    setShowRunModal(true);
  };

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
      key: 'model_slugs',
      header: 'Model',
      render: (run: EvaluationRunView) => (
        <div className="flex flex-col gap-0.5 max-w-32">
          {run.model_slugs.slice(0, 2).map((model, i) => (
            <span key={i} className="text-body-xs text-content-secondary truncate" title={model}>
              {model.split('/').pop()}
            </span>
          ))}
          {run.model_slugs.length > 2 && (
            <span className="text-body-xs text-content-tertiary">+{run.model_slugs.length - 2} more</span>
          )}
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
        <Button 
          icon={<Play className="w-4 h-4" />} 
          onClick={() => suites[0] && openRunModal(suites[0])}
          loading={runningEval !== null}
        >
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
            <div className="flex items-center gap-2">
              <Button 
                variant="ghost" 
                size="sm"
                icon={<GitCompare className="w-4 h-4" />}
                onClick={() => setShowCompare(true)}
              >
                Compare
              </Button>
              <FilterSelect
                value={groupBy}
                onChange={(v) => setGroupBy(v as GroupByOption)}
                options={[
                  { value: 'none', label: 'No grouping' },
                  { value: 'model', label: 'Group by model' },
                  { value: 'run', label: 'Group by run' },
                ]}
                className="w-36"
              />
              <Badge variant="default" size="sm">{runs.length} runs</Badge>
            </div>
          </div>
          <DataTable
            columns={runColumns}
            data={runs.slice(0, 10)}
            keyExtractor={(run) => run.evaluation_run_id}
            onRowClick={(run) => setSelectedRun(run)}
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
                <Button 
                  variant="ghost" 
                  size="sm" 
                  icon={<Play className="w-3.5 h-3.5" />}
                  onClick={() => openRunModal(suite)}
                  loading={runningEval === suite.suite_id}
                >
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

      {showRunModal && selectedSuite && (
        <RunEvaluationModal
          suite={selectedSuite}
          models={models}
          onRun={handleRunEvaluation}
          onClose={() => setShowRunModal(false)}
        />
      )}

      {showCompare && runs.length > 0 && (
        <ComparisonModal
          runs={runs}
          onClose={() => setShowCompare(false)}
        />
      )}

      {selectedRun && (
        <RunDetailModal
          run={selectedRun}
          onClose={() => setSelectedRun(null)}
        />
      )}
    </AdminPageShell>
  );
}
