import { forwardRef, type HTMLAttributes } from 'react';

type BadgeVariant = 'default' | 'success' | 'warning' | 'error' | 'info' | 'accent';
type BadgeSize = 'sm' | 'md';

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  size?: BadgeSize;
  /** Dot indicator instead of text color */
  dot?: boolean;
}

const variantStyles: Record<BadgeVariant, { bg: string; color: string; dotColor: string }> = {
  default: {
    bg: 'var(--color-bg-muted)',
    color: 'var(--color-fg-secondary)',
    dotColor: 'var(--color-fg-tertiary)',
  },
  success: {
    bg: 'color-mix(in srgb, var(--color-status-success) 15%, transparent)',
    color: 'var(--color-status-success)',
    dotColor: 'var(--color-status-success)',
  },
  warning: {
    bg: 'color-mix(in srgb, var(--color-status-warning) 15%, transparent)',
    color: 'var(--color-status-warning)',
    dotColor: 'var(--color-status-warning)',
  },
  error: {
    bg: 'color-mix(in srgb, var(--color-status-error) 15%, transparent)',
    color: 'var(--color-status-error)',
    dotColor: 'var(--color-status-error)',
  },
  info: {
    bg: 'color-mix(in srgb, var(--color-status-info) 15%, transparent)',
    color: 'var(--color-status-info)',
    dotColor: 'var(--color-status-info)',
  },
  accent: {
    bg: 'color-mix(in srgb, var(--color-accent-primary) 15%, transparent)',
    color: 'var(--color-accent-primary)',
    dotColor: 'var(--color-accent-primary)',
  },
};

const sizeStyles: Record<BadgeSize, React.CSSProperties> = {
  sm: {
    padding: '0.125rem 0.375rem',
    fontSize: 'var(--font-size-micro)',
    fontWeight: 500,
    lineHeight: '1.2',
  },
  md: {
    padding: '0.25rem 0.5rem',
    fontSize: 'var(--font-size-small)',
    fontWeight: 500,
    lineHeight: '1.4',
  },
};

/**
 * Badge - Status indicator or tag.
 * Displays compact labels for status, categories, or counts.
 */
export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ variant = 'default', size = 'md', dot = false, style, className, children, ...props }, ref) => {
    const colors = variantStyles[variant];

    const badgeStyle: React.CSSProperties = {
      display: 'inline-flex',
      alignItems: 'center',
      gap: dot ? '0.375rem' : 0,
      borderRadius: 'var(--radius-full)',
      fontFamily: 'var(--font-body)',
      backgroundColor: colors.bg,
      color: colors.color,
      whiteSpace: 'nowrap',
      ...sizeStyles[size],
      ...style,
    };

    return (
      <span
        ref={ref}
        className={className}
        style={badgeStyle}
        {...props}
      >
        {dot && (
          <span style={{
            width: '0.375rem',
            height: '0.375rem',
            borderRadius: 'var(--radius-full)',
            backgroundColor: colors.dotColor,
            flexShrink: 0,
          }} />
        )}
        {children}
      </span>
    );
  }
);

Badge.displayName = 'Badge';
