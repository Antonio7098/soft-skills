import { useEffect, useState } from 'react';
import { 
  GraduationCap,
  TrendingDown,
  BarChart3,
  ChevronRight,
} from 'lucide-react';
import { Card } from '@/design-system/primitives/Card';
import { Badge } from '@/design-system/primitives/Badge';
import { LoadingState } from '@/design-system/patterns/LoadingState';
import { useData } from '@/data';
import { AdminPageShell, MetricCard, SearchInput, FilterSelect } from '../components';
import type { AnalyticsOverviewView, CohortAnalyticsView } from '@/data/types';

const COHORT_OPTIONS = [
  { value: 'software_engineer', label: 'Software Engineer' },
  { value: 'product_manager', label: 'Product Manager' },
  { value: 'designer', label: 'Designer' },
  { value: 'data_scientist', label: 'Data Scientist' },
];

export function AdminLearners() {
  const dataProvider = useData();
  const [overview, setOverview] = useState<AnalyticsOverviewView | null>(null);
  const [cohort, setCohort] = useState<CohortAnalyticsView | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [cohortFilter, setCohortFilter] = useState('');

  useEffect(() => {
    setLoading(true);
    Promise.all([
      dataProvider.getAnalyticsOverview(),
      cohortFilter ? dataProvider.getCohortAnalytics({ target_role: cohortFilter }) : Promise.resolve(null),
    ])
      .then(([overviewData, cohortData]) => {
        setOverview(overviewData);
        setCohort(cohortData);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [dataProvider, cohortFilter]);

  if (loading) {
    return (
      <AdminPageShell title="Learners" subtitle="Learner analytics and progress tracking">
        <LoadingState message="Loading learner data..." />
      </AdminPageShell>
    );
  }

  return (
    <AdminPageShell
      title="Learners"
      subtitle="Monitor learner progress, identify skill gaps, and track cohort performance"
    >
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Total Learners"
          value={overview?.total_learners?.toLocaleString() || '0'}
          icon={<GraduationCap className="w-4 h-4" />}
        />
        <MetricCard
          label="Active (30d)"
          value={overview?.active_learners_30d?.toLocaleString() || '0'}
          icon={<BarChart3 className="w-4 h-4" />}
          change={{ value: 8, direction: 'up' }}
          trend="positive"
        />
        <MetricCard
          label="Avg Score"
          value={overview?.avg_validated_score?.toFixed(1) || '—'}
          trend="positive"
        />
        <MetricCard
          label="Validation Rate"
          value={
            overview?.validated_assessments && overview?.submitted_attempts
              ? `${((overview.validated_assessments / overview.submitted_attempts) * 100).toFixed(0)}%`
              : '—'
          }
          trend="positive"
        />
      </div>

      <Card className="flex flex-col gap-4">
        <div className="flex items-center gap-3">
          <SearchInput
            value={search}
            onChange={setSearch}
            placeholder="Search learners..."
            className="w-64"
          />
          <FilterSelect
            value={cohortFilter}
            onChange={setCohortFilter}
            options={COHORT_OPTIONS}
            placeholder="All cohorts"
            className="w-48"
          />
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h3 className="font-display text-body-md font-semibold text-content-primary">
              Top Weak Skills
            </h3>
            <Badge variant="warning" size="sm">Needs attention</Badge>
          </div>
          <div className="flex flex-col gap-2">
            {overview?.top_weak_skills?.slice(0, 6).map((skill) => (
              <div 
                key={skill.skill_slug} 
                className="flex items-center gap-3 py-2.5 px-3 rounded-lg hover:bg-surface-secondary/50 transition-colors cursor-pointer"
              >
                <div className="w-6 h-6 rounded-full bg-status-warning/10 flex items-center justify-center">
                  <TrendingDown className="w-3.5 h-3.5 text-status-warning" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-body-sm font-medium text-content-primary truncate">
                    {skill.skill_slug.replace(/_/g, ' ')}
                  </p>
                </div>
                <Badge variant="default" size="sm">{skill.learner_count} learners</Badge>
                <ChevronRight className="w-4 h-4 text-content-tertiary" />
              </div>
            )) || (
              <p className="text-body-sm text-content-tertiary py-4 text-center">No data available</p>
            )}
          </div>
        </Card>

        <Card className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h3 className="font-display text-body-md font-semibold text-content-primary">
              Cohort Breakdown
            </h3>
          </div>
          <div className="flex flex-col gap-2">
            {overview?.cohort_breakdown?.slice(0, 6).map((cohortItem) => (
              <div 
                key={cohortItem.cohort_key} 
                onClick={() => setCohortFilter(cohortItem.cohort_key)}
                className={`flex items-center gap-3 py-2.5 px-3 rounded-lg hover:bg-surface-secondary/50 transition-colors cursor-pointer ${
                  cohortFilter === cohortItem.cohort_key ? 'bg-accent/10 border border-accent/20' : ''
                }`}
              >
                <div className="w-6 h-6 rounded-full bg-accent/10 flex items-center justify-center">
                  <GraduationCap className="w-3.5 h-3.5 text-accent" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-body-sm font-medium text-content-primary truncate">
                    {cohortItem.cohort_key.replace(/_/g, ' ')}
                  </p>
                </div>
                <Badge variant="accent" size="sm">{cohortItem.learner_count} learners</Badge>
                <ChevronRight className="w-4 h-4 text-content-tertiary" />
              </div>
            )) || (
              <p className="text-body-sm text-content-tertiary py-4 text-center">No cohorts found</p>
            )}
          </div>
        </Card>
      </div>

      {cohort && (
        <Card className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h3 className="font-display text-body-md font-semibold text-content-primary">
              {cohortFilter.replace(/_/g, ' ')} Cohort Details
            </h3>
            <Badge variant="info" size="sm">{cohort.learner_count} learners</Badge>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="flex flex-col gap-1">
              <span className="text-body-xs text-content-tertiary">Sessions</span>
              <span className="text-body-md font-semibold text-content-primary">
                {cohort.usage?.total_sessions?.toLocaleString() || '0'}
              </span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-body-xs text-content-tertiary">Attempts</span>
              <span className="text-body-md font-semibold text-content-primary">
                {cohort.usage?.total_attempts?.toLocaleString() || '0'}
              </span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-body-xs text-content-tertiary">Validated</span>
              <span className="text-body-md font-semibold text-status-success">
                {cohort.usage?.validated_assessments?.toLocaleString() || '0'}
              </span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-body-xs text-content-tertiary">Avg Score</span>
              <span className="text-body-md font-semibold text-content-primary">
                {cohort.usage?.avg_validated_score?.toFixed(1) || '—'}
              </span>
            </div>
          </div>
        </Card>
      )}
    </AdminPageShell>
  );
}
