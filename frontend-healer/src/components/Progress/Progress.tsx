import { forwardRef, type HTMLAttributes } from 'react';

type ProgressSize = 'sm' | 'md' | 'lg';
type ProgressVariant = 'default' | 'success' | 'warning' | 'error' | 'accent';

interface ProgressProps extends HTMLAttributes<HTMLDivElement> {
  /** Progress value 0-100 */
  value: number;
  /** Max value (default 100) */
  max?: number;
  /** Bar height */
  size?: ProgressSize;
  /** Color variant */
  variant?: ProgressVariant;
  /** Show percentage label */
  showLabel?: boolean;
  /** Animated on mount */
  animated?: boolean;
}

const sizeStyles: Record<ProgressSize, string> = {
  sm: '4px',
  md: '8px',
  lg: '12px',
};

const variantColors: Record<ProgressVariant, string> = {
  default: 'var(--color-interactive-default)',
  success: 'var(--color-status-success)',
  warning: 'var(--color-status-warning)',
  error: 'var(--color-status-error)',
  accent: 'var(--color-accent-primary)',
};

/**
 * Progress - Visual progress indicator.
 * Shows completion percentage with configurable variants.
 */
export const Progress = forwardRef<HTMLDivElement, ProgressProps>(
  (
    {
      value,
      max = 100,
      size = 'md',
      variant = 'default',
      showLabel = false,
      animated = true,
      style,
      className,
      ...props
    },
    ref
  ) => {
    const percentage = Math.min(Math.max((value / max) * 100, 0), 100);
    const barHeight = sizeStyles[size];
    const barColor = variantColors[variant];

    return (
      <div
        ref={ref}
        className={className}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--space-3)',
          width: '100%',
          ...style,
        }}
        {...props}
      >
        <div style={{
          flex: 1,
          height: barHeight,
          backgroundColor: 'var(--color-bg-muted)',
          borderRadius: 'var(--radius-full)',
          overflow: 'hidden',
          position: 'relative',
        }}>
          <div
            role="progressbar"
            aria-valuenow={value}
            aria-valuemin={0}
            aria-valuemax={max}
            style={{
              height: '100%',
              width: `${percentage}%`,
              backgroundColor: barColor,
              borderRadius: 'var(--radius-full)',
              transition: animated
                ? 'width var(--duration-slow) var(--easing-out)'
                : 'none',
              transformOrigin: 'left',
            }}
          />
        </div>
        {showLabel && (
          <span style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 'var(--font-size-small)',
            color: 'var(--color-fg-secondary)',
            minWidth: '3ch',
            textAlign: 'right',
          }}>
            {Math.round(percentage)}%
          </span>
        )}
      </div>
    );
  }
);

Progress.displayName = 'Progress';
