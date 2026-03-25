import { useNavigate } from 'react-router-dom';
import { Clock } from 'lucide-react';
import { Card } from '@/design-system/primitives/Card';
import { Badge } from '@/design-system/primitives/Badge';
import { Button } from '@/design-system/primitives/Button';
import { ScoreRing } from '@/design-system/patterns/ScoreRing';
import { getScoreVariant } from '@/lib/variant-helpers';
import type { AttemptHistoryItem } from '@/data';

interface AttemptListItemProps {
  readonly attempt: AttemptHistoryItem;
}

export function AttemptListItem({ attempt }: AttemptListItemProps) {
  const navigate = useNavigate();
  const date = new Date(attempt.created_at);
  const formatted = date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
  const time = date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });

  return (
    <Card interactive padding="md" className="flex items-center gap-4" onClick={() => navigate(`/assessment/${attempt.id}`)}>
      <ScoreRing score={attempt.score} size="sm" />

      <div className="flex-1 min-w-0 flex flex-col gap-1.5">
        <div className="flex items-center gap-2">
          <h4 className="text-body-sm font-medium text-content-primary truncate">{attempt.title}</h4>
          <Badge variant={getScoreVariant(attempt.score)} size="sm">
            {attempt.score}/5
          </Badge>
        </div>
        <div className="flex items-center gap-3 text-body-xs text-content-tertiary">
          <span>{formatted}</span>
          <div className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            <span>{time}</span>
          </div>
          <Badge variant="default" size="sm" className="capitalize">
            {attempt.practice_type.replace(/_/g, ' ')}
          </Badge>
        </div>
        <div className="flex flex-wrap gap-1">
          {attempt.skill_slugs.slice(0, 4).map((slug) => (
            <Badge key={slug} variant="default" size="sm">
              {slug.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
            </Badge>
          ))}
        </div>
      </div>

      <Button variant="secondary" size="sm" onClick={(e) => { e.stopPropagation(); navigate(`/assessment/${attempt.id}`); }}>
        Review
      </Button>
    </Card>
  );
}
