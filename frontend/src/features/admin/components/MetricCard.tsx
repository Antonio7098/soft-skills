import type { ReactNode } from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { Card } from '@/design-system/primitives/Card';
import { cn } from '@/lib/cn';

interface MetricCardProps {
  readonly label: string;
  readonly value: string | number;
  readonly change?: { value: number; direction: 'up' | 'down' };
  readonly trend?: 'positive' | 'negative' | 'neutral';
  readonly icon?: ReactNode;
  readonly subtitle?: string;
  readonly className?: string;
}

export function MetricCard({ 
  label, 
  value, 
  change, 
  trend = 'neutral',
  icon, 
  subtitle,
  className 
}: MetricCardProps) {
  const trendColor = trend === 'positive' 
    ? 'text-status-success' 
    : trend === 'negative' 
      ? 'text-status-error' 
      : 'text-content-secondary';

  return (
    <Card variant="default" padding="md" className={cn('flex flex-col gap-2', className)}>
      <div className="flex items-center justify-between">
        <span className="text-body-xs font-medium text-content-tertiary uppercase tracking-wider">{label}</span>
        {icon && <span className="text-content-tertiary">{icon}</span>}
      </div>
      <div className="flex items-baseline gap-2">
        <span className="font-display text-display-sm text-content-primary">{value}</span>
        {change && (
          <span
            className={cn(
              'flex items-center gap-0.5 text-body-xs font-medium',
              change.direction === 'up' ? trendColor : trendColor,
            )}
          >
            {change.direction === 'up' ? (
              <TrendingUp className="w-3 h-3" />
            ) : (
              <TrendingDown className="w-3 h-3" />
            )}
            {Math.abs(change.value)}%
          </span>
        )}
      </div>
      {subtitle && (
        <span className="text-body-xs text-content-tertiary">{subtitle}</span>
      )}
    </Card>
  );
}
