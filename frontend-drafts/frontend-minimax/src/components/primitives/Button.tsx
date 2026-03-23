import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react';
import { useTheme } from '../../theme';

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      isLoading = false,
      leftIcon,
      rightIcon,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    const { activeTheme: theme } = useTheme();

    const baseStyles: React.CSSProperties = {
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: theme.spacing.space2,
      fontFamily: theme.typography.fontBody,
      fontWeight: theme.typography.weightMedium,
      borderRadius: theme.borderRadius.md,
      border: 'none',
      cursor: disabled || isLoading ? 'not-allowed' : 'pointer',
      opacity: disabled ? 0.5 : 1,
      transition: `all ${theme.motion.durationNormal} ${theme.motion.easeOut}`,
      whiteSpace: 'nowrap',
    };

    const sizeStyles: Record<ButtonSize, React.CSSProperties> = {
      sm: {
        padding: `${theme.spacing.space1} ${theme.spacing.space3}`,
        fontSize: theme.typography.sizeSm,
        minHeight: '2rem',
      },
      md: {
        padding: `${theme.spacing.space2} ${theme.spacing.space4}`,
        fontSize: theme.typography.sizeBase,
        minHeight: '2.5rem',
      },
      lg: {
        padding: `${theme.spacing.space3} ${theme.spacing.space6}`,
        fontSize: theme.typography.sizeLg,
        minHeight: '3rem',
      },
    };

    const variantStyles: Record<ButtonVariant, React.CSSProperties> = {
      primary: {
        backgroundColor: theme.colors.primary,
        color: theme.colors.textInverse,
      },
      secondary: {
        backgroundColor: theme.colors.surface,
        color: theme.colors.text,
        border: `1px solid ${theme.colors.border}`,
      },
      ghost: {
        backgroundColor: 'transparent',
        color: theme.colors.text,
      },
      danger: {
        backgroundColor: theme.colors.error,
        color: theme.colors.textInverse,
      },
    };

    const style: React.CSSProperties = {
      ...baseStyles,
      ...sizeStyles[size],
      ...variantStyles[variant],
    };

    return (
      <button
        ref={ref}
        style={style}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading ? (
          <span
            style={{
              display: 'inline-block',
              width: '1em',
              height: '1em',
              border: '2px solid currentColor',
              borderTopColor: 'transparent',
              borderRadius: '50%',
              animation: `spin ${theme.motion.durationSlow} linear infinite`,
            }}
          />
        ) : (
          <>
            {leftIcon && <span style={{ display: 'flex' }}>{leftIcon}</span>}
            {children}
            {rightIcon && <span style={{ display: 'flex' }}>{rightIcon}</span>}
          </>
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';
