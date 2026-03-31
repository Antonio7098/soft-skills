import { motion } from 'framer-motion';
import { AlertTriangle, TrendingDown, Target } from 'lucide-react';
import { cn } from '@/lib/cn';
import { Card } from '@/design-system/primitives/Card';

interface WeakSkillsTrackerProps {
  readonly weakSkills: string[];
  readonly stagnatingSkills: string[];
  readonly coverageGaps: string[];
  readonly className?: string;
}

interface SkillTagProps {
  readonly slug: string;
  readonly variant: 'weak' | 'stagnating' | 'gap';
  readonly index: number;
}

const variantConfig = {
  weak: {
    icon: AlertTriangle,
    color: 'text-status-error',
    bg: 'bg-status-error/10',
    border: 'border-status-error/20',
  },
  stagnating: {
    icon: TrendingDown,
    color: 'text-status-warning',
    bg: 'bg-status-warning/10',
    border: 'border-status-warning/20',
  },
  gap: {
    icon: Target,
    color: 'text-accent',
    bg: 'bg-accent/10',
    border: 'border-accent/20',
  },
};

function formatSkillName(slug: string): string {
  return slug
    .split('-')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
}

function SkillTag({ slug, variant, index }: SkillTagProps) {
  const config = variantConfig[variant];
  const Icon = config.icon;

  return (
    <motion.span
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-body-xs font-medium border',
        config.color,
        config.bg,
        config.border
      )}
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: index * 0.05, duration: 0.2 }}
    >
      <Icon size={12} />
      <span>{formatSkillName(slug)}</span>
    </motion.span>
  );
}

export function WeakSkillsTracker({
  weakSkills,
  stagnatingSkills,
  coverageGaps,
  className,
}: WeakSkillsTrackerProps) {
  const hasAnyIssues = weakSkills.length > 0 || stagnatingSkills.length > 0 || coverageGaps.length > 0;

  if (!hasAnyIssues) {
    return (
      <Card className={cn('text-center py-8', className)}>
        <div className="text-status-success mb-2">
          <Target size={32} className="mx-auto" />
        </div>
        <h3 className="font-display text-display-xs text-content-primary mb-1">All Skills On Track</h3>
        <p className="text-body-sm text-content-secondary">
          No weak, stagnating, or gap skills detected
        </p>
      </Card>
    );
  }

  return (
    <div className={cn('space-y-6', className)}>
      {weakSkills.length > 0 && (
        <Card>
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle size={18} className="text-status-error" />
            <h3 className="font-display text-display-xs text-content-primary">
              Weak Skills
            </h3>
            <span className="ml-auto text-body-xs text-content-tertiary">
              {weakSkills.length} skill{weakSkills.length !== 1 ? 's' : ''}
            </span>
          </div>
          <p className="text-body-sm text-content-secondary mb-4">
            Skills scoring below 40% that need focused practice
          </p>
          <div className="flex flex-wrap gap-2">
            {weakSkills.map((slug, i) => (
              <SkillTag key={slug} slug={slug} variant="weak" index={i} />
            ))}
          </div>
        </Card>
      )}

      {stagnatingSkills.length > 0 && (
        <Card>
          <div className="flex items-center gap-2 mb-3">
            <TrendingDown size={18} className="text-status-warning" />
            <h3 className="font-display text-display-xs text-content-primary">
              Stagnating Skills
            </h3>
            <span className="ml-auto text-body-xs text-content-tertiary">
              {stagnatingSkills.length} skill{stagnatingSkills.length !== 1 ? 's' : ''}
            </span>
          </div>
          <p className="text-body-sm text-content-secondary mb-4">
            Skills showing declining or no improvement recently
          </p>
          <div className="flex flex-wrap gap-2">
            {stagnatingSkills.map((slug, i) => (
              <SkillTag key={slug} slug={slug} variant="stagnating" index={i} />
            ))}
          </div>
        </Card>
      )}

      {coverageGaps.length > 0 && (
        <Card>
          <div className="flex items-center gap-2 mb-3">
            <Target size={18} className="text-accent" />
            <h3 className="font-display text-display-xs text-content-primary">
              Coverage Gaps
            </h3>
            <span className="ml-auto text-body-xs text-content-tertiary">
              {coverageGaps.length} skill{coverageGaps.length !== 1 ? 's' : ''}
            </span>
          </div>
          <p className="text-body-sm text-content-secondary mb-4">
            Skills with insufficient evidence (less than 3 assessments)
          </p>
          <div className="flex flex-wrap gap-2">
            {coverageGaps.map((slug, i) => (
              <SkillTag key={slug} slug={slug} variant="gap" index={i} />
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
