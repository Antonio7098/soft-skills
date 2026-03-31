import { motion } from 'framer-motion';
import { cn } from '@/lib/cn';
import { Card } from '@/design-system/primitives/Card';
import { ProgressBar } from '@/design-system/primitives/ProgressBar';
import { TrendBadge, DeltaIndicator } from './TrendBadge';
import type { SkillHistoryPoint } from '@/data';

interface SkillProgressCardProps {
  readonly skill: SkillHistoryPoint;
  readonly skillName?: string;
  readonly onClick?: () => void;
  readonly className?: string;
}

function getConfidenceBandColor(band: 'low' | 'medium' | 'high'): string {
  switch (band) {
    case 'high':
      return 'text-status-success';
    case 'medium':
      return 'text-accent';
    default:
      return 'text-status-warning';
  }
}

export function SkillProgressCard({
  skill,
  skillName,
  onClick,
  className,
}: SkillProgressCardProps) {
  const displayName =
    skillName ??
    skill.skill_slug
      .split('-')
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(' ');

  const scorePercent = Math.round(skill.score * 100);
  const trend = skill.delta > 0.02 ? 'up' : skill.delta < -0.02 ? 'down' : 'stable';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card
        interactive={!!onClick}
        onClick={onClick}
        className={cn('flex flex-col gap-3', className)}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <h4 className="font-medium text-content-primary truncate">{displayName}</h4>
            <div className="flex items-center gap-2 mt-1">
              <span className={cn('text-body-xs font-medium', getConfidenceBandColor(skill.confidence_band))}>
                {skill.confidence_band} confidence
              </span>
              <span className="text-body-xs text-content-tertiary">
                • {skill.evidence_count} evidence{skill.evidence_count !== 1 ? 's' : ''}
              </span>
            </div>
          </div>
          <div className="flex flex-col items-end gap-1">
            <span className="text-display-sm font-display font-bold text-content-primary">
              {scorePercent}%
            </span>
            <DeltaIndicator delta={skill.delta} size="sm" />
          </div>
        </div>

        <ProgressBar
          value={scorePercent}
          variant={scorePercent >= 70 ? 'success' : 'accent'}
          size="sm"
        />

        <div className="flex items-center justify-between">
          <TrendBadge trend={trend} size="sm" />
          <span className="text-body-xs text-content-tertiary">
            {Math.round(skill.confidence * 100)}% confidence
          </span>
        </div>
      </Card>
    </motion.div>
  );
}
