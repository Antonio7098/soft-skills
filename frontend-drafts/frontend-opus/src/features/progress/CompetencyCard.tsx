import { Card } from '@/design-system/primitives/Card';
import { ProgressBar } from '@/design-system/primitives/ProgressBar';
import type { CompetencyProgress } from '@/types';

interface CompetencyCardProps {
  readonly competency: CompetencyProgress;
}

export function CompetencyCard({ competency }: CompetencyCardProps) {
  return (
    <Card className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h3 className="font-display text-display-xs">{competency.name}</h3>
        <p className="text-body-sm text-content-secondary">Level {competency.level} &middot; {competency.label}</p>
      </div>
      <div className="flex flex-col gap-4">
        {competency.skills.map((skill) => (
          <ProgressBar key={skill.name} value={skill.value} label={skill.name} showValue />
        ))}
      </div>
    </Card>
  );
}
