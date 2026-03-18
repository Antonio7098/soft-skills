import { forwardRef, type HTMLAttributes, type ReactNode } from 'react';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  /** Card variant */
  variant?: 'default' | 'elevated' | 'outlined' | 'filled';
  /** Padding size */
  padding?: 'none' | 'sm' | 'md' | 'lg';
  /** Interactive hover state */
  interactive?: boolean;
  /** Header content */
  header?: ReactNode;
  /** Footer content */
  footer?: ReactNode;
}

const paddingStyles: Record<string, React.CSSProperties> = {
  none: { padding: 0 },
  sm: { padding: 'var(--space-3)' },
  md: { padding: 'var(--space-5)' },
  lg: { padding: 'var(--space-8)' },
};

const variantStyles: Record<string, React.CSSProperties> = {
  default: {
    backgroundColor: 'var(--color-bg-secondary)',
    border: '1px solid var(--color-border-subtle)',
  },
  elevated: {
    backgroundColor: 'var(--color-bg-secondary)',
    border: 'none',
    boxShadow: 'var(--shadow-lg)',
  },
  outlined: {
    backgroundColor: 'transparent',
    border: '1px solid var(--color-border-default)',
  },
  filled: {
    backgroundColor: 'var(--color-bg-tertiary)',
    border: 'none',
  },
};

/**
 * Card - Flexible container for grouping content.
 * Supports variants, padding, and interactive states.
 */
export const Card = forwardRef<HTMLDivElement, CardProps>(
  (
    {
      variant = 'default',
      padding = 'md',
      interactive = false,
      header,
      footer,
      style,
      className,
      children,
      ...props
    },
    ref
  ) => {
    const cardStyle: React.CSSProperties = {
      borderRadius: 'var(--radius-lg)',
      overflow: 'hidden',
      transition: interactive
        ? 'all var(--duration-fast) var(--easing-default)'
        : 'none',
      cursor: interactive ? 'pointer' : 'default',
      ...variantStyles[variant],
      ...style,
    };

    return (
      <div
        ref={ref}
        className={className}
        style={cardStyle}
        {...props}
      >
        {header && (
          <div style={{
            ...paddingStyles[padding],
            borderBottom: '1px solid var(--color-border-subtle)',
          }}>
            {header}
          </div>
        )}
        <div style={paddingStyles[padding]}>
          {children}
        </div>
        {footer && (
          <div style={{
            ...paddingStyles[padding],
            borderTop: '1px solid var(--color-border-subtle)',
          }}>
            {footer}
          </div>
        )}
      </div>
    );
  }
);

Card.displayName = 'Card';
