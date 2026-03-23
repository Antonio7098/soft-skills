import type { ReactNode } from 'react';
import { cn } from '@/lib/cn';

interface EmptyStateProps {
  readonly icon: ReactNode;
  readonly title: string;
  readonly description: string;
  readonly action?: ReactNode;
  readonly className?: string;
}

export function EmptyState({ icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center gap-4 py-16 px-6 text-center',
        className,
      )}
    >
      <div className="w-12 h-12 rounded-full bg-surface-secondary flex items-center justify-center text-content-tertiary">
        {icon}
      </div>
      <div className="flex flex-col gap-1.5 max-w-sm">
        <h3 className="font-display text-display-sm text-content-primary">{title}</h3>
        <p className="text-body-sm text-content-secondary">{description}</p>
      </div>
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}
