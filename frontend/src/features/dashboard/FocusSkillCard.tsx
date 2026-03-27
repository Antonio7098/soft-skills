import { Card } from '@/design-system/primitives/Card';
import { Button } from '@/design-system/primitives/Button';
import { Badge } from '@/design-system/primitives/Badge';
import { ProgressBar } from '@/design-system/primitives/ProgressBar';
import type { SkillFocus } from '@/types';
import { getFocusVariant } from '@/lib/variant-helpers';
import { TrendingUp } from 'lucide-react';

interface FocusSkillCardProps {
  readonly skill: SkillFocus;
}

export function FocusSkillCard({ skill }: FocusSkillCardProps) {
  return (
    <Card className="flex flex-col gap-3 p-4">
      <div className="flex items-center justify-between">
        <h4 className="text-body-sm font-medium text-content-primary">{skill.skill}</h4>
        <div className="flex items-center gap-2">
          <Badge variant={getFocusVariant(skill.focus)} size="sm">
            {skill.focus} Focus
          </Badge>
          {skill.trend === 'up' && <TrendingUp className="w-4 h-4 text-status-success" />}
          {skill.trend === 'down' && <TrendingUp className="w-4 h-4 text-status-error rotate-180" />}
        </div>
      </div>
      <ProgressBar value={skill.level} label="Current Level" showValue />
      <Button variant="ghost" size="sm" className="w-full">
        Practice {skill.skill}
      </Button>
    </Card>
  );
}
