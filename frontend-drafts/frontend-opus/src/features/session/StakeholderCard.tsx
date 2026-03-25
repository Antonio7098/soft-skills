import { Avatar } from '@/design-system/primitives/Avatar';
import { Card } from '@/design-system/primitives/Card';
import { Badge } from '@/design-system/primitives/Badge';
import type { MockPersonView } from '@/data';

interface StakeholderCardProps {
  readonly person: MockPersonView;
}

export function StakeholderCard({ person }: StakeholderCardProps) {
  return (
    <Card padding="md" className="flex flex-col gap-3">
      <div className="flex items-center gap-3">
        <Avatar fallback={person.name} size="sm" />
        <div className="flex flex-col">
          <span className="text-body-sm font-medium text-content-primary">{person.name}</span>
          <span className="text-body-xs text-content-secondary">{person.role}</span>
        </div>
      </div>
      <p className="text-body-xs text-content-secondary italic">{person.relationship_to_scenario}</p>
      <div className="flex flex-col gap-1.5">
        <span className="text-body-xs font-medium text-content-tertiary">Communication style</span>
        <span className="text-body-sm text-content-primary">{person.communication_style}</span>
      </div>
      {person.goals.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {person.goals.map((g, i) => (
            <Badge key={i} variant="default" size="sm">{g}</Badge>
          ))}
        </div>
      )}
    </Card>
  );
}
