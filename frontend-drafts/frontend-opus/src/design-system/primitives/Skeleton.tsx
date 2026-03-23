import { cn } from '@/lib/cn';

type SkeletonVariant = 'text' | 'circular' | 'rectangular';

interface SkeletonProps {
  readonly variant?: SkeletonVariant;
  readonly width?: string;
  readonly height?: string;
  readonly className?: string;
}

export function Skeleton({
  variant = 'text',
  width,
  height,
  className,
}: SkeletonProps) {
  return (
    <div
      className={cn(
        'bg-surface-secondary animate-skeleton-pulse',
        variant === 'text' && 'h-4 rounded-md',
        variant === 'circular' && 'rounded-full',
        variant === 'rectangular' && 'rounded-card',
        className,
      )}
      style={{ width, height }}
      aria-hidden="true"
    />
  );
}
