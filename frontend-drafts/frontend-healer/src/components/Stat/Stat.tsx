import { forwardRef, type HTMLAttributes } from 'react';

interface StatProps extends HTMLAttributes<HTMLDivElement> {
  /** Stat label */
  label: string;
  /** Stat value */
  value: string | number;
  /** Optional change indicator */
  change?: {
    value: number;
    direction: 'up' | 'down' | 'neutral';
  };
  /** Optional description */
  description?: string;
}

/**
 * Stat - Statistics display card.
 * Shows key metrics with optional trend indicators.
 */
export const Stat = forwardRef<HTMLDivElement, StatProps>(
  ({ label, value, change, description, style, className, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={className}
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-1)',
          ...style,
        }}
        {...props}
      >
        <span style={{
          fontFamily: 'var(--font-body)',
          fontSize: 'var(--font-size-small)',
          fontWeight: 500,
          color: 'var(--color-fg-tertiary)',
          letterSpacing: '0.05em',
          textTransform: 'uppercase' as const,
        }}>
          {label}
        </span>
        <div style={{
          display: 'flex',
          alignItems: 'baseline',
          gap: 'var(--space-2)',
        }}>
          <span style={{
            fontFamily: 'var(--font-display)',
            fontSize: 'var(--font-size-4xl)',
            fontWeight: 400,
            color: 'var(--color-fg-primary)',
            lineHeight: 1.1,
          }}>
            {value}
          </span>
          {change && (
            <span style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 'var(--font-size-small)',
              fontWeight: 500,
              color: change.direction === 'up'
                ? 'var(--color-status-success)'
                : change.direction === 'down'
                  ? 'var(--color-status-error)'
                  : 'var(--color-fg-tertiary)',
            }}>
              {change.direction === 'up' ? '+' : change.direction === 'down' ? '-' : ''}
              {Math.abs(change.value)}%
            </span>
          )}
        </div>
        {description && (
          <span style={{
            fontFamily: 'var(--font-body)',
            fontSize: 'var(--font-size-small)',
            color: 'var(--color-fg-tertiary)',
          }}>
            {description}
          </span>
        )}
      </div>
    );
  }
);

Stat.displayName = 'Stat';
