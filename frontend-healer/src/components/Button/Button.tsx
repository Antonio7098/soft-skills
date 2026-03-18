import { forwardRef, type ButtonHTMLAttributes } from 'react';

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** Visual variant */
  variant?: ButtonVariant;
  /** Size preset */
  size?: ButtonSize;
  /** Full width */
  fullWidth?: boolean;
  /** Loading state */
  loading?: boolean;
  /** Icon (left) */
  icon?: React.ReactNode;
}

const variantStyles: Record<ButtonVariant, React.CSSProperties> = {
  primary: {
    backgroundColor: 'var(--color-interactive-default)',
    color: 'var(--color-fg-inverse)',
    border: 'none',
    fontWeight: 500,
  },
  secondary: {
    backgroundColor: 'transparent',
    color: 'var(--color-interactive-default)',
    border: '1px solid var(--color-border-strong)',
    fontWeight: 500,
  },
  ghost: {
    backgroundColor: 'transparent',
    color: 'var(--color-fg-secondary)',
    border: 'none',
    fontWeight: 400,
  },
  danger: {
    backgroundColor: 'var(--color-status-error)',
    color: 'var(--color-fg-inverse)',
    border: 'none',
    fontWeight: 500,
  },
};

const sizeStyles: Record<ButtonSize, React.CSSProperties> = {
  sm: {
    height: '2rem',
    padding: '0 0.75rem',
    fontSize: 'var(--font-size-small)',
    borderRadius: 'var(--radius-md)',
  },
  md: {
    height: '2.5rem',
    padding: '0 1rem',
    fontSize: 'var(--font-size-base)',
    borderRadius: 'var(--radius-md)',
  },
  lg: {
    height: '3rem',
    padding: '0 1.5rem',
    fontSize: 'var(--font-size-medium)',
    borderRadius: 'var(--radius-lg)',
  },
};

/**
 * Button - Interactive element with variants and sizes.
 * Uses design system tokens for consistent styling.
 */
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      fullWidth = false,
      loading = false,
      icon,
      disabled,
      style,
      className,
      children,
      ...props
    },
    ref
  ) => {
    const baseStyle: React.CSSProperties = {
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '0.5rem',
      fontFamily: 'var(--font-body)',
      cursor: disabled || loading ? 'not-allowed' : 'pointer',
      opacity: disabled ? 0.5 : 1,
      width: fullWidth ? '100%' : 'auto',
      transition: 'all var(--duration-fast) var(--easing-default)',
      ...variantStyles[variant],
      ...sizeStyles[size],
      ...style,
    };

    return (
      <button
        ref={ref}
        className={className}
        style={baseStyle}
        disabled={disabled || loading}
        {...props}
      >
        {loading ? (
          <span style={{
            width: '1em',
            height: '1em',
            border: '2px solid currentColor',
            borderTopColor: 'transparent',
            borderRadius: '50%',
            animation: 'spin 0.6s linear infinite',
          }} />
        ) : (
          icon
        )}
        {children}
        <style>{`
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        `}</style>
      </button>
    );
  }
);

Button.displayName = 'Button';
