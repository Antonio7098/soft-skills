import { useState, useEffect } from 'react';
import { PageShell } from '@/design-system/patterns/PageShell';
import { CompetencyCard } from '@/features/progress/CompetencyCard';
import { LoadingState } from '@/design-system/patterns/LoadingState';
import { useData } from '@/data';
import type { CompetencyProgressView } from '@/data';

export function Progress() {
  const data = useData();
  const [competencies, setCompetencies] = useState<CompetencyProgressView[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    data.getCompetencyProgress('current').then((c) => {
      setCompetencies(c);
      setLoading(false);
    });
  }, [data]);

  if (loading) return <LoadingState message="Loading progress..." />;

  return (
    <PageShell
      title="Skill Progression"
      subtitle="Track your demonstrated performance across core competencies."
    >
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {competencies.map((comp) => (
          <CompetencyCard
            key={comp.slug}
            competency={{
              name: comp.name,
              level: comp.confidence === 'high' ? '3' : comp.confidence === 'medium' ? '2' : '1',
              label: comp.overall_score >= 70 ? 'Competent' : comp.overall_score >= 40 ? 'Developing' : 'Beginning',
              skills: comp.skills.map((s) => ({ name: s.name, value: s.score })),
            }}
          />
        ))}
      </div>
    </PageShell>
  );
}
