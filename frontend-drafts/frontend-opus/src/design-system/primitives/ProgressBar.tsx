import { cn } from '@/lib/cn';

type ProgressVariant = 'default' | 'accent' | 'success';
type ProgressSize = 'sm' | 'md';

interface ProgressBarProps {
  readonly value: number;
  readonly label?: string;
  readonly showValue?: boolean;
  readonly variant?: ProgressVariant;
  readonly size?: ProgressSize;
  readonly className?: string;
}

const trackSizeStyles: Record<ProgressSize, string> = {
  sm: 'h-1.5',
  md: 'h-2.5',
};

const fillVariantStyles: Record<ProgressVariant, string> = {
  default: 'bg-content-secondary',
  accent: 'bg-accent',
  success: 'bg-status-success',
};

export function ProgressBar({
  value,
  label,
  showValue = false,
  variant = 'accent',
  size = 'md',
  className,
}: ProgressBarProps) {
  const clamped = Math.max(0, Math.min(100, value));

  return (
    <div className={cn('flex flex-col gap-1.5', className)}>
      {(label || showValue) && (
        <div className="flex items-center justify-between">
          {label && (
            <span className="text-body-sm font-medium text-content-primary">
              {label}
            </span>
          )}
          {showValue && (
            <span className="text-body-xs font-medium text-content-secondary">
              {Math.round(clamped)}%
            </span>
          )}
        </div>
      )}
      <div
        className={cn(
          'w-full rounded-full bg-surface-secondary overflow-hidden',
          trackSizeStyles[size],
        )}
        role="progressbar"
        aria-valuenow={clamped}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={label}
      >
        <div
          className={cn(
            'h-full rounded-full transition-all duration-500 ease-out',
            fillVariantStyles[variant],
          )}
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
}
