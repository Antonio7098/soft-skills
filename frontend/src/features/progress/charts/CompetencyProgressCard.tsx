import { motion } from 'framer-motion';
import { cn } from '@/lib/cn';
import { Card } from '@/design-system/primitives/Card';
import { ProgressBar } from '@/design-system/primitives/ProgressBar';
import { DeltaIndicator } from './TrendBadge';
import type { CompetencyHistoryPoint } from '@/data';

interface CompetencyProgressCardProps {
  readonly competency: CompetencyHistoryPoint;
  readonly competencyName?: string;
  readonly competencyDescription?: string;
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

export function CompetencyProgressCard({
  competency,
  competencyName,
  competencyDescription,
  onClick,
  className,
}: CompetencyProgressCardProps) {
  const displayName =
    competencyName ??
    competency.competency_slug
      .split('-')
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(' ');

  const scorePercent = Math.round(competency.score * 100);
  const trend = competency.delta > 0.02 ? 'improving' : competency.delta < -0.02 ? 'declining' : 'stable';

  const trendConfig = {
    improving: {
      color: 'bg-status-success/10 text-status-success border-status-success/20',
      label: 'Improving',
    },
    declining: {
      color: 'bg-status-error/10 text-status-error border-status-error/20',
      label: 'Needs Focus',
    },
    stable: {
      color: 'bg-surface-secondary text-content-secondary border-line',
      label: 'Stable',
    },
  };

  const trendStyle = trendConfig[trend];

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card
        interactive={!!onClick}
        onClick={onClick}
        className={cn('flex flex-col gap-4', className)}
      >
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <h4 className="font-display text-body-lg font-semibold text-content-primary truncate">
              {displayName}
            </h4>
            {competencyDescription && (
              <p className="text-body-xs text-content-secondary mt-1 line-clamp-2">
                {competencyDescription}
              </p>
            )}
          </div>
          <div className="flex flex-col items-end gap-1 ml-4">
            <span className="text-display-md font-display font-bold text-content-primary">
              {scorePercent}%
            </span>
            <DeltaIndicator delta={competency.delta} size="sm" />
          </div>
        </div>

        {/* Progress Bar */}
        <ProgressBar
          value={scorePercent}
          variant={scorePercent >= 70 ? 'success' : 'accent'}
          size="md"
        />

        {/* Footer */}
        <div className="flex items-center justify-between">
          <span
            className={cn(
              'px-2 py-0.5 rounded-full text-body-xs font-medium border',
              trendStyle.color
            )}
          >
            {trendStyle.label}
          </span>
          <div className="flex items-center gap-2 text-body-xs text-content-tertiary">
            <span className={cn('font-medium', getConfidenceBandColor(competency.confidence_band))}>
              {competency.confidence_band} confidence
            </span>
            <span>•</span>
            <span>{Math.round(competency.confidence * 100)}%</span>
          </div>
        </div>
      </Card>
    </motion.div>
  );
}
