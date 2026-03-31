import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Minus, ArrowUp, ArrowDown } from 'lucide-react';
import { cn } from '@/lib/cn';

type TrendDirection = 'improving' | 'declining' | 'stable' | 'up' | 'down';

interface TrendBadgeProps {
  readonly trend: TrendDirection;
  readonly size?: 'sm' | 'md';
  readonly className?: string;
}

interface DeltaIndicatorProps {
  readonly delta: number;
  readonly showIcon?: boolean;
  readonly size?: 'sm' | 'md';
  readonly className?: string;
}

const trendConfig: Record<
  TrendDirection,
  { icon: typeof TrendingUp; color: string; bg: string; label: string }
> = {
  improving: {
    icon: TrendingUp,
    color: 'text-status-success',
    bg: 'bg-status-success/10',
    label: 'Improving',
  },
  up: {
    icon: TrendingUp,
    color: 'text-status-success',
    bg: 'bg-status-success/10',
    label: 'Up',
  },
  declining: {
    icon: TrendingDown,
    color: 'text-status-error',
    bg: 'bg-status-error/10',
    label: 'Declining',
  },
  down: {
    icon: TrendingDown,
    color: 'text-status-error',
    bg: 'bg-status-error/10',
    label: 'Down',
  },
  stable: {
    icon: Minus,
    color: 'text-content-secondary',
    bg: 'bg-surface-secondary',
    label: 'Stable',
  },
};

const sizeStyles = {
  sm: 'px-1.5 py-0.5 text-body-xs gap-1',
  md: 'px-2 py-1 text-body-sm gap-1.5',
};

const iconSizes = {
  sm: 12,
  md: 14,
};

export function TrendBadge({ trend, size = 'sm', className }: TrendBadgeProps) {
  const config = trendConfig[trend];
  const Icon = config.icon;

  return (
    <motion.span
      className={cn(
        'inline-flex items-center rounded-full font-medium',
        config.color,
        config.bg,
        sizeStyles[size],
        className
      )}
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ duration: 0.2 }}
    >
      <Icon size={iconSizes[size]} />
      <span>{config.label}</span>
    </motion.span>
  );
}

export function DeltaIndicator({
  delta,
  showIcon = true,
  size = 'sm',
  className,
}: DeltaIndicatorProps) {
  const isPositive = delta > 0;
  const isNeutral = delta === 0;
  const Icon = isPositive ? ArrowUp : ArrowDown;

  const colorClass = isNeutral
    ? 'text-content-tertiary'
    : isPositive
      ? 'text-status-success'
      : 'text-status-error';

  const formattedDelta = isNeutral
    ? '0%'
    : `${isPositive ? '+' : ''}${Math.round(delta * 100)}%`;

  return (
    <motion.span
      className={cn(
        'inline-flex items-center font-medium',
        colorClass,
        size === 'sm' ? 'text-body-xs gap-0.5' : 'text-body-sm gap-1',
        className
      )}
      initial={{ y: isPositive ? 5 : -5, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      {showIcon && !isNeutral && <Icon size={iconSizes[size]} />}
      <span>{formattedDelta}</span>
    </motion.span>
  );
}
