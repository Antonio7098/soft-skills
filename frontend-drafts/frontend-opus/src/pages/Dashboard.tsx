import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Award, Clock, Star, Target } from 'lucide-react';
import { PageShell } from '@/design-system/patterns/PageShell';
import { StatCard } from '@/design-system/patterns/StatCard';
import { Card } from '@/design-system/primitives/Card';
import { Button } from '@/design-system/primitives/Button';
import { Badge } from '@/design-system/primitives/Badge';
import { ProgressBar } from '@/design-system/primitives/ProgressBar';
import { RecentActivityRow } from '@/features/dashboard/RecentActivityRow';
import { LoadingState } from '@/design-system/patterns/LoadingState';
import { useData } from '@/data';
import type { AttemptHistoryItem, CompetencyProgressView } from '@/data';

export function Dashboard() {
  const navigate = useNavigate();
  const data = useData();
  const [user, setUser] = useState<{ display_name: string } | null>(null);
  const [history, setHistory] = useState<AttemptHistoryItem[]>([]);
  const [competencies, setCompetencies] = useState<CompetencyProgressView[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      data.getMe(),
      data.getAttemptHistory('current'),
      data.getCompetencyProgress('current'),
    ]).then(([u, h, c]) => {
      setUser(u);
      setHistory(h);
      setCompetencies(c);
      setLoading(false);
    });
  }, [data]);

  if (loading) return <LoadingState message="Loading dashboard..." />;

  const completedCompetencies = competencies.filter((c) => c.overall_score >= 60).length;
  const topWeak = [...competencies].sort((a, b) => a.overall_score - b.overall_score)[0];
  const recentActivity = history.slice(0, 3).map((a) => ({
    title: a.title,
    score: Math.round(a.score * 20),
    date: new Date(a.created_at).toLocaleDateString(),
    type: 'Quick Practice',
  }));

  return (
    <PageShell
      title={`Welcome back, ${user?.display_name ?? 'Learner'}`}
      subtitle={`You've completed ${history.length} attempts. Keep building your skills.`}
      actions={
        <Button variant="primary" icon={<Target className="w-4 h-4" />} onClick={() => navigate('/practice')}>
          Start Practice
        </Button>
      }
    >
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total Attempts"
          value={history.length}
          icon={<Target className="w-5 h-5" />}
        />
        <StatCard
          label="Avg. Score"
          value={`${history.length > 0 ? Math.round(history.reduce((s, a) => s + a.score, 0) / history.length * 20) : 0}%`}
          icon={<Star className="w-5 h-5 text-status-warning" />}
        />
        <StatCard
          label="Competencies"
          value={`${completedCompetencies}/${competencies.length}`}
          icon={<Award className="w-5 h-5 text-status-info" />}
        />
        <StatCard
          label="Skills Practiced"
          value={new Set(history.flatMap((a) => a.skill_slugs)).size}
          icon={<Clock className="w-5 h-5 text-accent" />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-2">
        <div className="lg:col-span-2 flex flex-col gap-6">
          <section className="flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h3 className="font-display text-display-xs text-content-primary">Recent Activity</h3>
              <Button variant="ghost" size="sm" onClick={() => navigate('/history')}>View History</Button>
            </div>
            <div className="flex flex-col gap-3">
              {recentActivity.map((activity, i) => (
                <RecentActivityRow key={i} activity={activity} />
              ))}
            </div>
          </section>
        </div>

        <div className="flex flex-col gap-6">
          {topWeak && (
            <section className="flex flex-col gap-4">
              <h3 className="font-display text-display-xs text-content-primary">Current Focus</h3>
              <Card className="flex flex-col gap-5">
                <div className="flex flex-col gap-1">
                  <span className="text-body-sm font-medium text-content-primary">{topWeak.name}</span>
                  <span className="text-body-xs text-content-secondary">{topWeak.description}</span>
                </div>
                <ProgressBar value={topWeak.overall_score} label={`Level ${topWeak.confidence}`} showValue variant="accent" />
                <div className="flex flex-col gap-2 mt-2">
                  <span className="text-body-xs font-medium text-content-secondary uppercase tracking-wider">
                    Key Skills to Practice
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {topWeak.skills.slice(0, 3).map((s) => (
                      <Badge key={s.slug} variant="default">{s.name}</Badge>
                    ))}
                  </div>
                </div>
                <Button variant="secondary" className="w-full mt-2" onClick={() => navigate('/practice')}>Practice Skills</Button>
              </Card>
            </section>
          )}
        </div>
      </div>
    </PageShell>
  );
}
