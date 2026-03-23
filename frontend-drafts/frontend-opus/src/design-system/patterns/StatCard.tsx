import type { ReactNode } from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { Card } from '@/design-system/primitives/Card';
import { cn } from '@/lib/cn';

interface StatCardProps {
  readonly label: string;
  readonly value: string | number;
  readonly change?: { value: number; direction: 'up' | 'down' };
  readonly icon?: ReactNode;
  readonly className?: string;
}

export function StatCard({ label, value, change, icon, className }: StatCardProps) {
  return (
    <Card variant="default" padding="md" className={cn('flex flex-col gap-3', className)}>
      <div className="flex items-center justify-between">
        <span className="text-body-sm font-medium text-content-secondary">{label}</span>
        {icon && <span className="text-content-tertiary">{icon}</span>}
      </div>
      <div className="flex items-end gap-2">
        <span className="font-display text-display-md text-content-primary">{value}</span>
        {change && (
          <span
            className={cn(
              'flex items-center gap-0.5 text-body-xs font-medium mb-1',
              change.direction === 'up' ? 'text-status-success' : 'text-status-error',
            )}
          >
            {change.direction === 'up' ? (
              <TrendingUp className="w-3.5 h-3.5" />
            ) : (
              <TrendingDown className="w-3.5 h-3.5" />
            )}
            {change.value}%
          </span>
        )}
      </div>
    </Card>
  );
}
