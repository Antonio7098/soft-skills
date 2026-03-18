import { forwardRef, type HTMLAttributes } from 'react';

interface DividerProps extends HTMLAttributes<HTMLHRElement> {
  /** Divider orientation */
  orientation?: 'horizontal' | 'vertical';
  /** Spacing around the divider */
  spacing?: string;
  /** Visual weight */
  variant?: 'default' | 'strong' | 'subtle';
}

const variantColors: Record<string, string> = {
  default: 'var(--color-border-default)',
  strong: 'var(--color-border-strong)',
  subtle: 'var(--color-border-subtle)',
};

/**
 * Divider - Visual separator between content sections.
 */
export const Divider = forwardRef<HTMLHRElement, DividerProps>(
  ({ orientation = 'horizontal', spacing, variant = 'default', style, className, ...props }, ref) => {
    const isHorizontal = orientation === 'horizontal';

    const dividerStyle: React.CSSProperties = {
      border: 'none',
      backgroundColor: variantColors[variant],
      flexShrink: 0,
      ...(isHorizontal
        ? {
            height: '1px',
            width: '100%',
            margin: spacing || 'var(--space-4) 0',
          }
        : {
            width: '1px',
            height: '100%',
            margin: spacing || '0 var(--space-4)',
          }),
      ...style,
    };

    return (
      <hr
        ref={ref}
        className={className}
        style={dividerStyle}
        role="separator"
        {...props}
      />
    );
  }
);

Divider.displayName = 'Divider';
