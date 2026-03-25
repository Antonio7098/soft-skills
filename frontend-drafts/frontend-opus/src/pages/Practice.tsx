import { useState, useEffect } from 'react';
import { PageShell } from '@/design-system/patterns/PageShell';
import { PracticeModeCard } from '@/features/practice/PracticeModeCard';
import { RecentSessionRow } from '@/features/practice/RecentSessionRow';
import { FocusSkillCard } from '@/features/dashboard/FocusSkillCard';
import { Button } from '@/design-system/primitives/Button';
import { LoadingState } from '@/design-system/patterns/LoadingState';
import { useData } from '@/data';
import type { AttemptHistoryItem, CompetencyProgressView } from '@/data';
import { PRACTICE_MODES } from '@/lib/data/seed';

export function Practice() {
  const data = useData();
  const [history, setHistory] = useState<AttemptHistoryItem[]>([]);
  const [competencies, setCompetencies] = useState<CompetencyProgressView[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      data.getAttemptHistory('current'),
      data.getCompetencyProgress('current'),
    ]).then(([h, c]) => {
      setHistory(h);
      setCompetencies(c);
      setLoading(false);
    });
  }, [data]);

  if (loading) return <LoadingState message="Loading practice hub..." />;

  const recentSessions = history.slice(0, 4).map((a) => ({
    id: parseInt(a.id.replace(/\D/g, ''), 10) || 0,
    type: 'Quick Practice' as const,
    title: a.title,
    date: new Date(a.created_at).toLocaleDateString(),
    score: Math.round(a.score * 20),
    duration: '10 min',
    skills: a.skill_slugs.map((s) => s.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())),
    status: 'completed' as const,
  }));

  const skillFocus = competencies
    .flatMap((c) => c.skills)
    .reduce((acc, skill) => {
      if (!acc.find((s) => s.slug === skill.slug)) acc.push(skill);
      return acc;
    }, [] as typeof competencies[0]['skills'])
    .slice(0, 6)
    .map((s) => ({
      skill: s.name,
      level: s.score,
      focus: (s.score < 50 ? 'High' : s.score < 70 ? 'Medium' : 'Low') as 'High' | 'Medium' | 'Low',
      trend: s.trend,
    }));

  return (
    <PageShell
      title="Practice Hub"
      subtitle="Choose a practice mode to improve your consultancy skills."
    >
      <div className="flex flex-col gap-8">
        <section className="flex flex-col gap-6">
          <h3 className="font-display text-display-xs text-content-primary">Practice Modes</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {PRACTICE_MODES.map((mode) => (
              <PracticeModeCard key={mode.id} mode={mode} />
            ))}
          </div>
        </section>

        <section className="flex flex-col gap-6">
          <div className="flex items-center justify-between">
            <h3 className="font-display text-display-xs text-content-primary">Recent Sessions</h3>
            <Button variant="ghost" size="sm">View History</Button>
          </div>
          <div className="flex flex-col gap-3">
            {recentSessions.map((session) => (
              <RecentSessionRow key={session.id} session={session} />
            ))}
          </div>
        </section>

        <section className="flex flex-col gap-6">
          <h3 className="font-display text-display-xs text-content-primary">Your Skill Focus Areas</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {skillFocus.map((skill) => (
              <FocusSkillCard key={skill.skill} skill={skill} />
            ))}
          </div>
        </section>
      </div>
    </PageShell>
  );
}
