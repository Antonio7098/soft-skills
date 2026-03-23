import { forwardRef, type HTMLAttributes } from 'react';

interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  /** Width (CSS value) */
  width?: string | number;
  /** Height (CSS value) */
  height?: string | number;
  /** Shape preset */
  variant?: 'text' | 'circular' | 'rectangular';
  /** Animation type */
  animation?: 'pulse' | 'shimmer' | 'none';
}

/**
 * Skeleton - Loading placeholder.
 * Provides visual feedback during async operations.
 * Follows CL-012: no blank loading screens.
 */
export const Skeleton = forwardRef<HTMLDivElement, SkeletonProps>(
  (
    {
      width,
      height,
      variant = 'text',
      animation = 'shimmer',
      style,
      className,
      ...props
    },
    ref
  ) => {
    const baseStyle: React.CSSProperties = {
      backgroundColor: 'var(--color-bg-muted)',
      borderRadius: variant === 'circular'
        ? 'var(--radius-full)'
        : variant === 'text'
          ? 'var(--radius-sm)'
          : 'var(--radius-md)',
      width: width ?? (variant === 'text' ? '100%' : '2rem'),
      height: height ?? (variant === 'text' ? '1em' : variant === 'circular' ? width : '2rem'),
      animation: animation === 'pulse'
        ? 'pulse 1.5s ease-in-out infinite'
        : animation === 'shimmer'
          ? 'shimmer 2s ease-in-out infinite'
          : 'none',
      ...(animation === 'shimmer' ? {
        background: 'linear-gradient(90deg, var(--color-bg-muted) 25%, var(--color-bg-tertiary) 50%, var(--color-bg-muted) 75%)',
        backgroundSize: '200% 100%',
      } : {}),
      ...style,
    };

    return (
      <div
        ref={ref}
        className={className}
        style={baseStyle}
        aria-hidden="true"
        {...props}
      />
    );
  }
);

Skeleton.displayName = 'Skeleton';

/**
 * SkeletonGroup - Multiple skeleton items with staggered animation.
 */
interface SkeletonGroupProps {
  count?: number;
  height?: string | number;
  spacing?: string;
}

export function SkeletonGroup({ count = 3, height = '1rem', spacing = 'var(--space-3)' }: SkeletonGroupProps) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: spacing }}>
      {Array.from({ length: count }).map((_, i) => (
        <Skeleton
          key={i}
          height={height}
          style={{
            animationDelay: `${i * 100}ms`,
          }}
        />
      ))}
    </div>
  );
}
