import { Award, Clock, Star, Target } from 'lucide-react';
import { PageShell } from '@/design-system/patterns/PageShell';
import { StatCard } from '@/design-system/patterns/StatCard';
import { Card } from '@/design-system/primitives/Card';
import { Button } from '@/design-system/primitives/Button';
import { Badge } from '@/design-system/primitives/Badge';
import { ProgressBar } from '@/design-system/primitives/ProgressBar';

export function Dashboard() {
  return (
    <PageShell
      title="Welcome back, Alex"
      subtitle="You're on a 4-day streak. Keep up the momentum with a quick practice session today."
      actions={
        <Button variant="primary" icon={<Target className="w-4 h-4" />}>
          Start Practice
        </Button>
      }
    >
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Current Streak"
          value="4 Days"
          icon={<Clock className="w-5 h-5 text-accent" />}
          change={{ value: 12, direction: 'up' }}
        />
        <StatCard
          label="Total Scenarios"
          value="24"
          icon={<Target className="w-5 h-5" />}
          change={{ value: 8, direction: 'up' }}
        />
        <StatCard
          label="Avg. Score"
          value="82%"
          icon={<Star className="w-5 h-5 text-status-warning" />}
          change={{ value: 3, direction: 'up' }}
        />
        <StatCard
          label="Competencies"
          value="3/8"
          icon={<Award className="w-5 h-5 text-status-info" />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-2">
        <div className="lg:col-span-2 flex flex-col gap-6">
          <section className="flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h3 className="font-display text-display-xs text-content-primary">Recommended Next</h3>
              <Button variant="ghost" size="sm">View all</Button>
            </div>
            <Card interactive className="flex flex-col sm:flex-row gap-6 items-start sm:items-center">
              <div className="flex-1 flex flex-col gap-2">
                <div className="flex items-center gap-2">
                  <Badge variant="accent">Stakeholder Management</Badge>
                  <span className="text-body-xs text-content-tertiary">15 mins</span>
                </div>
                <h4 className="text-body-lg font-medium text-content-primary">
                  The Unhappy Sponsor
                </h4>
                <p className="text-body-sm text-content-secondary line-clamp-2">
                  A key project sponsor is unhappy with the latest delivery and is threatening to escalate. Navigate the conversation to de-escalate and find a constructive path forward.
                </p>
              </div>
              <Button>Begin Scenario</Button>
            </Card>
          </section>

          <section className="flex flex-col gap-4">
            <h3 className="font-display text-display-xs text-content-primary">Recent Activity</h3>
            <div className="flex flex-col gap-3">
              {[
                { title: 'Tech Lead Interview', score: 85, date: 'Yesterday', type: 'Interview' },
                { title: 'Scope Creep Pushback', score: 78, date: '2 days ago', type: 'Scenario' },
                { title: 'Executive Summary', score: 92, date: '3 days ago', type: 'Quick Practice' },
              ].map((activity, i) => (
                <Card key={i} variant="elevated" padding="sm" className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-full bg-surface-secondary flex items-center justify-center font-display text-content-primary">
                      {activity.score}
                    </div>
                    <div className="flex flex-col">
                      <span className="text-body-sm font-medium text-content-primary">{activity.title}</span>
                      <div className="flex items-center gap-2 text-body-xs text-content-tertiary">
                        <span>{activity.type}</span>
                        <span>•</span>
                        <span>{activity.date}</span>
                      </div>
                    </div>
                  </div>
                  <Button variant="ghost" size="sm">Review</Button>
                </Card>
              ))}
            </div>
          </section>
        </div>

        <div className="flex flex-col gap-6">
          <section className="flex flex-col gap-4">
            <h3 className="font-display text-display-xs text-content-primary">Current Focus</h3>
            <Card className="flex flex-col gap-5">
              <div className="flex flex-col gap-1">
                <span className="text-body-sm font-medium text-content-primary">Prioritization</span>
                <span className="text-body-xs text-content-secondary">Needs work based on recent scenarios</span>
              </div>
              <ProgressBar value={45} label="Level 2 / 5" showValue variant="accent" />
              <div className="flex flex-col gap-2 mt-2">
                <span className="text-body-xs font-medium text-content-secondary uppercase tracking-wider">
                  Key Skills to Practice
                </span>
                <div className="flex flex-wrap gap-2">
                  <Badge variant="default">Trade-off Analysis</Badge>
                  <Badge variant="default">Saying No</Badge>
                  <Badge variant="default">Impact Assessment</Badge>
                </div>
              </div>
              <Button variant="secondary" className="w-full mt-2">Practice Skills</Button>
            </Card>
          </section>
        </div>
      </div>
    </PageShell>
  );
}
