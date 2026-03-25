import { Clock } from 'lucide-react';
import { Card } from '@/design-system/primitives/Card';
import { Badge } from '@/design-system/primitives/Badge';
import { Button } from '@/design-system/primitives/Button';
import { ProgressBar } from '@/design-system/primitives/ProgressBar';
import { getSessionTypeVariant } from '@/lib/variant-helpers';
import type { RecentSession } from '@/types';

interface RecentSessionRowProps {
  readonly session: RecentSession;
}

export function RecentSessionRow({ session }: RecentSessionRowProps) {
  return (
    <Card variant="elevated" className="flex items-center justify-between p-4">
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 rounded-full bg-surface-secondary flex items-center justify-center font-display text-body-lg text-content-primary">
          {session.score}
        </div>
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <Badge variant={getSessionTypeVariant(session.type)} size="sm">
              {session.type}
            </Badge>
            <h4 className="text-body-sm font-medium text-content-primary">{session.title}</h4>
          </div>
          <div className="flex items-center gap-3 text-body-xs text-content-tertiary">
            <span>{session.date}</span>
            <div className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              <span>{session.duration}</span>
            </div>
          </div>
          <div className="flex flex-wrap gap-1">
            {session.skills.map((skill) => (
              <Badge key={skill} variant="default" size="sm">
                {skill}
              </Badge>
            ))}
          </div>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <div className="flex flex-col items-end gap-1">
          <ProgressBar value={session.score} showValue size="sm" />
          <span className="text-body-xs text-content-tertiary">Score</span>
        </div>
        <Button variant="secondary" size="sm">Review</Button>
      </div>
    </Card>
  );
}
