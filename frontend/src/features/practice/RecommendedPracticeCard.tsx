import { Clock } from 'lucide-react';
import { Card } from '@/design-system/primitives/Card';
import { Badge } from '@/design-system/primitives/Badge';
import { Button } from '@/design-system/primitives/Button';
import { getSessionTypeVariant, getDifficultyVariant } from '@/lib/variant-helpers';
import type { RecommendedPractice } from '@/types';

interface RecommendedPracticeCardProps {
  readonly practice: RecommendedPractice;
}

export function RecommendedPracticeCard({ practice }: RecommendedPracticeCardProps) {
  return (
    <Card className="flex flex-col gap-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 flex flex-col gap-2">
          <Badge variant={getSessionTypeVariant(practice.type)} size="sm">
            {practice.type}
          </Badge>
          <h4 className="font-display text-display-sm text-content-primary line-clamp-2">
            {practice.title}
          </h4>
          <p className="text-body-sm text-content-secondary line-clamp-2">
            {practice.description}
          </p>
        </div>
      </div>

      <div className="flex flex-col gap-3">
        <div className="flex items-center gap-3 text-body-xs text-content-tertiary">
          <div className="flex items-center gap-1">
            <Clock className="w-3.5 h-3.5" />
            <span>{practice.duration}</span>
          </div>
          <Badge variant={getDifficultyVariant(practice.difficulty)} size="sm">
            {practice.difficulty}
          </Badge>
        </div>

        <div className="flex flex-col gap-1">
          <p className="text-body-xs text-content-tertiary italic">&ldquo;{practice.reason}&rdquo;</p>
          <div className="flex flex-wrap gap-1">
            {practice.skills.map((skill) => (
              <Badge key={skill} variant="default" size="sm">
                {skill}
              </Badge>
            ))}
          </div>
        </div>

        <Button className="w-full">Start Practice</Button>
      </div>
    </Card>
  );
}
