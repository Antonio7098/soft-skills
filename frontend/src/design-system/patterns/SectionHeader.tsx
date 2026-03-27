import type { ReactNode } from 'react';
import { cn } from '@/lib/cn';

interface SectionHeaderProps {
  readonly title: string;
  readonly subtitle?: string;
  readonly action?: ReactNode;
  readonly className?: string;
}

export function SectionHeader({ title, subtitle, action, className }: SectionHeaderProps) {
  return (
    <div className={cn('flex items-end justify-between gap-4', className)}>
      <div className="flex flex-col gap-0.5">
        <h3 className="font-display text-display-sm text-content-primary">{title}</h3>
        {subtitle && (
          <p className="text-body-sm text-content-secondary">{subtitle}</p>
        )}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
}
