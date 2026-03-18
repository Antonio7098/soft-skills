import { forwardRef, type HTMLAttributes } from 'react';

type TextVariant = 'display' | 'heading' | 'subheading' | 'body' | 'bodySmall' | 'caption' | 'mono';
type TextColor = 'primary' | 'secondary' | 'tertiary' | 'inverse' | 'accent' | 'success' | 'warning' | 'error';
type TextElement = 'p' | 'span' | 'label' | 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6' | 'small' | 'strong' | 'em';

interface TextProps extends Omit<HTMLAttributes<HTMLElement>, 'color'> {
  /** Typography variant */
  variant?: TextVariant;
  /** Semantic color token */
  color?: TextColor;
  /** HTML element to render */
  as?: TextElement;
  /** Truncate with ellipsis */
  truncate?: boolean;
  /** Number of lines to show before truncating */
  lineClamp?: number;
}

const variantStyles: Record<TextVariant, React.CSSProperties> = {
  display: {
    fontFamily: 'var(--font-display)',
    fontSize: 'var(--font-size-5xl)',
    fontWeight: 400,
    lineHeight: 1.1,
    letterSpacing: '-0.025em',
  },
  heading: {
    fontFamily: 'var(--font-display)',
    fontSize: 'var(--font-size-3xl)',
    fontWeight: 400,
    lineHeight: 1.1,
    letterSpacing: '-0.025em',
  },
  subheading: {
    fontFamily: 'var(--font-display)',
    fontSize: 'var(--font-size-xl)',
    fontWeight: 400,
    lineHeight: 1.2,
    letterSpacing: '-0.015em',
  },
  body: {
    fontFamily: 'var(--font-body)',
    fontSize: 'var(--font-size-base)',
    fontWeight: 400,
    lineHeight: 1.75,
  },
  bodySmall: {
    fontFamily: 'var(--font-body)',
    fontSize: 'var(--font-size-small)',
    fontWeight: 400,
    lineHeight: 1.6,
  },
  caption: {
    fontFamily: 'var(--font-body)',
    fontSize: 'var(--font-size-micro)',
    fontWeight: 500,
    lineHeight: 1.4,
    letterSpacing: '0.05em',
    textTransform: 'uppercase' as const,
  },
  mono: {
    fontFamily: 'var(--font-mono)',
    fontSize: 'var(--font-size-small)',
    fontWeight: 400,
    lineHeight: 1.5,
  },
};

const colorStyles: Record<TextColor, React.CSSProperties> = {
  primary: { color: 'var(--color-fg-primary)' },
  secondary: { color: 'var(--color-fg-secondary)' },
  tertiary: { color: 'var(--color-fg-tertiary)' },
  inverse: { color: 'var(--color-fg-inverse)' },
  accent: { color: 'var(--color-fg-accent)' },
  success: { color: 'var(--color-status-success)' },
  warning: { color: 'var(--color-status-warning)' },
  error: { color: 'var(--color-status-error)' },
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnyRef = any;

/**
 * Text - Typography primitive with semantic variants.
 * Uses design system tokens for all styling.
 */
export const Text = forwardRef<HTMLElement, TextProps>(
  (
    {
      variant = 'body',
      color = 'primary',
      as: Component = 'p',
      truncate = false,
      lineClamp,
      style,
      className,
      children,
      ...props
    },
    ref
  ) => {
    const combinedStyle: React.CSSProperties = {
      ...variantStyles[variant],
      ...colorStyles[color],
      ...(truncate ? { overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' } : {}),
      ...(lineClamp ? { display: '-webkit-box', WebkitLineClamp: lineClamp, WebkitBoxOrient: 'vertical' as const, overflow: 'hidden' } : {}),
      ...style,
    };

    return (
      <Component
        ref={ref as AnyRef}
        className={className}
        style={combinedStyle}
        {...props}
      >
        {children}
      </Component>
    );
  }
);

Text.displayName = 'Text';
