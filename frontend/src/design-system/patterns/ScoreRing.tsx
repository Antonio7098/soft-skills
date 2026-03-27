import { cn } from '@/lib/cn';

interface ScoreRingProps {
  readonly score: number;
  readonly maxScore?: number;
  readonly size?: 'sm' | 'md' | 'lg';
  readonly label?: string;
  readonly className?: string;
}

const sizeConfig = {
  sm: { diameter: 64, stroke: 4, fontSize: 'text-body-lg', labelSize: 'text-body-xs' },
  md: { diameter: 96, stroke: 5, fontSize: 'text-display-md', labelSize: 'text-body-sm' },
  lg: { diameter: 128, stroke: 6, fontSize: 'text-display-lg', labelSize: 'text-body-md' },
} as const;

function getScoreColor(pct: number): string {
  if (pct >= 80) return 'text-status-success';
  if (pct >= 60) return 'text-accent';
  if (pct >= 40) return 'text-status-warning';
  return 'text-status-error';
}

function getStrokeColor(pct: number): string {
  if (pct >= 80) return 'var(--color-status-success)';
  if (pct >= 60) return 'var(--color-accent)';
  if (pct >= 40) return 'var(--color-status-warning)';
  return 'var(--color-status-error)';
}

export function ScoreRing({ score, maxScore = 5, size = 'md', label, className }: ScoreRingProps) {
  const pct = Math.round((score / maxScore) * 100);
  const cfg = sizeConfig[size];
  const radius = (cfg.diameter - cfg.stroke * 2) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (pct / 100) * circumference;

  return (
    <div className={cn('flex flex-col items-center gap-2', className)}>
      <div className="relative" style={{ width: cfg.diameter, height: cfg.diameter }}>
        <svg width={cfg.diameter} height={cfg.diameter} className="-rotate-90">
          <circle
            cx={cfg.diameter / 2}
            cy={cfg.diameter / 2}
            r={radius}
            fill="none"
            stroke="var(--color-surface-secondary)"
            strokeWidth={cfg.stroke}
          />
          <circle
            cx={cfg.diameter / 2}
            cy={cfg.diameter / 2}
            r={radius}
            fill="none"
            stroke={getStrokeColor(pct)}
            strokeWidth={cfg.stroke}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            className="transition-all duration-700 ease-out"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={cn('font-display font-bold', cfg.fontSize, getScoreColor(pct))}>
            {score}
          </span>
          <span className="text-body-xs text-content-tertiary">/{maxScore}</span>
        </div>
      </div>
      {label && (
        <span className={cn('font-medium text-content-secondary', cfg.labelSize)}>{label}</span>
      )}
    </div>
  );
}
