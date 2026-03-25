import { Card } from '@/design-system/primitives/Card';
import { Button } from '@/design-system/primitives/Button';
import type { RecentActivity } from '@/types';

interface RecentActivityRowProps {
  readonly activity: RecentActivity;
}

export function RecentActivityRow({ activity }: RecentActivityRowProps) {
  return (
    <Card variant="elevated" padding="sm" className="flex items-center justify-between">
      <div className="flex items-center gap-4">
        <div className="w-10 h-10 rounded-full bg-surface-secondary flex items-center justify-center font-display text-content-primary">
          {activity.score}
        </div>
        <div className="flex flex-col">
          <span className="text-body-sm font-medium text-content-primary">{activity.title}</span>
          <div className="flex items-center gap-2 text-body-xs text-content-tertiary">
            <span>{activity.type}</span>
            <span>&middot;</span>
            <span>{activity.date}</span>
          </div>
        </div>
      </div>
      <Button variant="ghost" size="sm">Review</Button>
    </Card>
  );
}
