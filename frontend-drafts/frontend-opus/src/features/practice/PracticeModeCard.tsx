import { Clock } from 'lucide-react';
import { Card } from '@/design-system/primitives/Card';
import { Badge } from '@/design-system/primitives/Badge';
import { Button } from '@/design-system/primitives/Button';
import { getDifficultyVariant } from '@/lib/variant-helpers';
import type { PracticeMode } from '@/types';

interface PracticeModeCardProps {
  readonly mode: PracticeMode;
}

export function PracticeModeCard({ mode }: PracticeModeCardProps) {
  return (
    <Card interactive className="flex flex-col gap-4 p-6 text-center">
      <div className={`w-12 h-12 rounded-full bg-${mode.color}/10 flex items-center justify-center mx-auto text-${mode.color}`}>
        {mode.icon}
      </div>
      <div className="flex flex-col gap-2">
        <h4 className="font-display text-display-sm text-content-primary">{mode.title}</h4>
        <p className="text-body-sm text-content-secondary line-clamp-3">{mode.description}</p>
      </div>
      <div className="flex flex-col gap-2 text-body-xs text-content-tertiary">
        <div className="flex items-center justify-center gap-1">
          <Clock className="w-3 h-3" />
          <span>{mode.duration}</span>
        </div>
        <Badge variant={getDifficultyVariant(mode.difficulty)} size="sm">
          {mode.difficulty}
        </Badge>
      </div>
      <div className="flex flex-wrap gap-1 justify-center">
        {mode.features.map((feature) => (
          <Badge key={feature} variant="default" size="sm">
            {feature}
          </Badge>
        ))}
      </div>
      <Button className="w-full mt-2">Start Practice</Button>
    </Card>
  );
}
