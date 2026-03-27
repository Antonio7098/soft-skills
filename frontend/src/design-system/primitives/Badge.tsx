import type { ReactNode } from 'react';
import { cn } from '@/lib/cn';

export type BadgeVariant = 'default' | 'accent' | 'success' | 'warning' | 'error' | 'info';
type BadgeSize = 'sm' | 'md';

interface BadgeProps {
  readonly variant?: BadgeVariant;
  readonly size?: BadgeSize;
  readonly children: ReactNode;
  readonly className?: string;
}

const variantStyles: Record<BadgeVariant, string> = {
  default: 'bg-surface-secondary text-content-secondary border-line',
  accent: 'bg-accent-muted text-accent-text border-accent/20',
  success: 'bg-status-success/10 text-status-success border-status-success/20',
  warning: 'bg-status-warning/10 text-status-warning border-status-warning/20',
  error: 'bg-status-error/10 text-status-error border-status-error/20',
  info: 'bg-status-info/10 text-status-info border-status-info/20',
};

const sizeStyles: Record<BadgeSize, string> = {
  sm: 'px-1.5 py-0.5 text-body-xs',
  md: 'px-2.5 py-1 text-body-sm',
};

export function Badge({ variant = 'default', size = 'sm', children, className }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center font-body font-medium rounded-badge border',
        variantStyles[variant],
        sizeStyles[size],
        className,
      )}
    >
      {children}
    </span>
  );
}
