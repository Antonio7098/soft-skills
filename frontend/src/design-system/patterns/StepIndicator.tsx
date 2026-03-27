import { cn } from '@/lib/cn';

interface StepIndicatorProps {
  readonly current: number;
  readonly total: number;
  readonly label?: string;
  readonly className?: string;
}

export function StepIndicator({ current, total, label, className }: StepIndicatorProps) {
  return (
    <div className={cn('flex items-center gap-3', className)}>
      {label && (
        <span className="text-body-sm font-medium text-content-secondary">{label}</span>
      )}
      <div className="flex items-center gap-1.5">
        {Array.from({ length: total }, (_, i) => {
          const step = i + 1;
          const isActive = step === current;
          const isComplete = step < current;

          return (
            <div
              key={step}
              className={cn(
                'rounded-full transition-all duration-300',
                isActive
                  ? 'w-8 h-2 bg-accent'
                  : isComplete
                    ? 'w-2 h-2 bg-accent/60'
                    : 'w-2 h-2 bg-surface-secondary',
              )}
            />
          );
        })}
      </div>
      <span className="text-body-xs text-content-tertiary">
        {current}/{total}
      </span>
    </div>
  );
}
