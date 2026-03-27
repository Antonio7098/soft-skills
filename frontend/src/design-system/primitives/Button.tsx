import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react';
import { cn } from '@/lib/cn';

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  readonly variant?: ButtonVariant;
  readonly size?: ButtonSize;
  readonly icon?: ReactNode;
  readonly iconPosition?: 'left' | 'right';
  readonly loading?: boolean;
  readonly children: ReactNode;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    'bg-accent text-surface-primary hover:bg-accent-hover active:scale-[0.98] shadow-sm',
  secondary:
    'bg-surface-elevated text-content-primary border border-line hover:border-line-hover hover:bg-surface-secondary active:scale-[0.98]',
  ghost:
    'bg-transparent text-content-secondary hover:text-content-primary hover:bg-surface-secondary active:scale-[0.98]',
  danger:
    'bg-status-error/10 text-status-error hover:bg-status-error/20 active:scale-[0.98]',
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: 'h-8 px-3 text-body-sm gap-1.5',
  md: 'h-10 px-4 text-body-md gap-2',
  lg: 'h-12 px-6 text-body-lg gap-2.5',
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      icon,
      iconPosition = 'left',
      loading = false,
      children,
      className,
      disabled,
      ...props
    },
    ref,
  ) => {
    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={cn(
          'inline-flex items-center justify-center font-body font-medium rounded-button',
          'transition-all duration-150 ease-out',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/50 focus-visible:ring-offset-2 focus-visible:ring-offset-surface-primary',
          'disabled:opacity-50 disabled:pointer-events-none',
          variantStyles[variant],
          sizeStyles[size],
          className,
        )}
        {...props}
      >
        {loading ? (
          <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
        ) : icon && iconPosition === 'left' ? (
          <span className="shrink-0">{icon}</span>
        ) : null}
        <span>{children}</span>
        {!loading && icon && iconPosition === 'right' ? (
          <span className="shrink-0">{icon}</span>
        ) : null}
      </button>
    );
  },
);

Button.displayName = 'Button';
