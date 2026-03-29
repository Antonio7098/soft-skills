import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Users, 
  GraduationCap, 
  Target, 
  CheckCircle2, 
  AlertTriangle,
  TrendingUp,
  Activity,
  Clock,
} from 'lucide-react';
import { Card } from '@/design-system/primitives/Card';
import { Badge } from '@/design-system/primitives/Badge';
import { LoadingState } from '@/design-system/patterns/LoadingState';
import { useData } from '@/data';
import { AdminPageShell, MetricCard, MiniChart } from '../components';
import type { AnalyticsOverviewView } from '@/data/types';

export function AdminOverview() {
  const navigate = useNavigate();
  const dataProvider = useData();
  const [overview, setOverview] = useState<AnalyticsOverviewView | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    dataProvider.getAnalyticsOverview()
      .then(setOverview)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [dataProvider]);

  if (loading) {
    return (
      <AdminPageShell title="Overview" subtitle="Platform health and key metrics">
        <LoadingState message="Loading dashboard..." />
      </AdminPageShell>
    );
  }

  const trendData = overview?.overall_usage_trend?.slice(-14).map((t) => ({
    label: t.bucket_date,
    value: t.sessions_started + t.attempts_submitted,
  })) || [];


  return (
    <AdminPageShell 
      title="Overview" 
      subtitle="Platform health and key metrics at a glance"
    >
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Total Learners"
          value={overview?.total_learners?.toLocaleString() || '0'}
          icon={<GraduationCap className="w-4 h-4" />}
          subtitle={`${overview?.active_learners_30d || 0} active in last 30 days`}
        />
        <MetricCard
          label="Total Sessions"
          value={overview?.total_sessions?.toLocaleString() || '0'}
          icon={<Target className="w-4 h-4" />}
          change={{ value: 12, direction: 'up' }}
          trend="positive"
        />
        <MetricCard
          label="Validated Assessments"
          value={overview?.validated_assessments?.toLocaleString() || '0'}
          icon={<CheckCircle2 className="w-4 h-4" />}
          subtitle={`${overview?.rejected_assessments || 0} rejected`}
        />
        <MetricCard
          label="Avg Score"
          value={overview?.avg_validated_score?.toFixed(1) || '—'}
          icon={<TrendingUp className="w-4 h-4" />}
          trend="positive"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h3 className="font-display text-body-md font-semibold text-content-primary">Activity Trend</h3>
            <Badge variant="default" size="sm">Last 14 days</Badge>
          </div>
          <MiniChart data={trendData} height={120} color="accent" />
          <div className="flex items-center gap-6 text-body-xs text-content-secondary">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-accent" />
              Sessions & Attempts
            </span>
          </div>
        </Card>

        <Card className="flex flex-col gap-4">
          <h3 className="font-display text-body-md font-semibold text-content-primary">Quick Stats</h3>
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between py-2 border-b border-line">
              <span className="text-body-sm text-content-secondary">Total Attempts</span>
              <span className="text-body-sm font-medium text-content-primary">
                {overview?.total_attempts?.toLocaleString() || '0'}
              </span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-line">
              <span className="text-body-sm text-content-secondary">Submitted</span>
              <span className="text-body-sm font-medium text-content-primary">
                {overview?.submitted_attempts?.toLocaleString() || '0'}
              </span>
            </div>
            <div className="flex items-center justify-between py-2">
              <span className="text-body-sm text-content-secondary">Validation Rate</span>
              <span className="text-body-sm font-medium text-status-success">
                {overview?.validated_assessments && overview?.submitted_attempts
                  ? ((overview.validated_assessments / overview.submitted_attempts) * 100).toFixed(1)
                  : '0'}%
              </span>
            </div>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h3 className="font-display text-body-md font-semibold text-content-primary">Top Weak Skills</h3>
            <button 
              onClick={() => navigate('/admin/learners')}
              className="text-body-xs text-accent hover:underline"
            >
              View all
            </button>
          </div>
          <div className="flex flex-col gap-2">
            {overview?.top_weak_skills?.slice(0, 5).map((skill, idx) => (
              <div key={skill.skill_slug} className="flex items-center gap-3 py-2">
                <span className="w-5 h-5 rounded-full bg-surface-secondary flex items-center justify-center text-body-xs font-medium text-content-secondary">
                  {idx + 1}
                </span>
                <span className="flex-1 text-body-sm text-content-primary">{skill.skill_slug}</span>
                <Badge variant="warning" size="sm">{skill.learner_count} learners</Badge>
              </div>
            )) || (
              <p className="text-body-sm text-content-tertiary py-4 text-center">No data available</p>
            )}
          </div>
        </Card>

        <Card className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h3 className="font-display text-body-md font-semibold text-content-primary">Provider Performance</h3>
            <button 
              onClick={() => navigate('/admin/telemetry')}
              className="text-body-xs text-accent hover:underline"
            >
              View details
            </button>
          </div>
          <div className="flex flex-col gap-2">
            {overview?.provider_summary?.slice(0, 4).map((provider) => (
              <div key={`${provider.provider}-${provider.model_slug}`} className="flex items-center gap-3 py-2">
                <Activity className="w-4 h-4 text-content-tertiary" />
                <div className="flex-1 min-w-0">
                  <p className="text-body-sm text-content-primary truncate">
                    {provider.provider} {provider.model_slug && `/ ${provider.model_slug}`}
                  </p>
                  <p className="text-body-xs text-content-tertiary">
                    {provider.call_count} calls · {provider.avg_latency_ms?.toFixed(0) || '—'}ms avg
                  </p>
                </div>
                <Badge 
                  variant={provider.success_count / provider.call_count > 0.95 ? 'success' : 'warning'} 
                  size="sm"
                >
                  {((provider.success_count / provider.call_count) * 100).toFixed(1)}%
                </Badge>
              </div>
            )) || (
              <p className="text-body-sm text-content-tertiary py-4 text-center">No data available</p>
            )}
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card 
          interactive 
          onClick={() => navigate('/admin/users')}
          className="flex items-center gap-4 cursor-pointer"
        >
          <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center">
            <Users className="w-5 h-5 text-accent" />
          </div>
          <div className="flex-1">
            <p className="text-body-sm font-medium text-content-primary">User Management</p>
            <p className="text-body-xs text-content-tertiary">Manage users and permissions</p>
          </div>
        </Card>

        <Card 
          interactive 
          onClick={() => navigate('/admin/collections')}
          className="flex items-center gap-4 cursor-pointer"
        >
          <div className="w-10 h-10 rounded-lg bg-status-warning/10 flex items-center justify-center">
            <AlertTriangle className="w-5 h-5 text-status-warning" />
          </div>
          <div className="flex-1">
            <p className="text-body-sm font-medium text-content-primary">Verification Queue</p>
            <p className="text-body-xs text-content-tertiary">Review pending content</p>
          </div>
        </Card>

        <Card 
          interactive 
          onClick={() => navigate('/admin/evaluations')}
          className="flex items-center gap-4 cursor-pointer"
        >
          <div className="w-10 h-10 rounded-lg bg-status-success/10 flex items-center justify-center">
            <Clock className="w-5 h-5 text-status-success" />
          </div>
          <div className="flex-1">
            <p className="text-body-sm font-medium text-content-primary">Evaluations</p>
            <p className="text-body-xs text-content-tertiary">Monitor model performance</p>
          </div>
        </Card>
      </div>
    </AdminPageShell>
  );
}
