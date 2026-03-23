import { forwardRef, type HTMLAttributes, type ReactNode } from 'react';
import { cn } from '@/lib/cn';

type CardVariant = 'default' | 'elevated' | 'outlined' | 'ghost';
type CardPadding = 'none' | 'sm' | 'md' | 'lg';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  readonly variant?: CardVariant;
  readonly padding?: CardPadding;
  readonly interactive?: boolean;
  readonly children: ReactNode;
}

const variantStyles: Record<CardVariant, string> = {
  default: 'bg-surface-elevated shadow-card border border-line',
  elevated: 'bg-surface-elevated shadow-elevated border border-line',
  outlined: 'bg-transparent border border-line',
  ghost: 'bg-transparent',
};

const paddingStyles: Record<CardPadding, string> = {
  none: '',
  sm: 'p-3',
  md: 'p-5',
  lg: 'p-7',
};

export const Card = forwardRef<HTMLDivElement, CardProps>(
  (
    {
      variant = 'default',
      padding = 'md',
      interactive = false,
      children,
      className,
      ...props
    },
    ref,
  ) => {
    return (
      <div
        ref={ref}
        className={cn(
          'rounded-card',
          variantStyles[variant],
          paddingStyles[padding],
          interactive && 'cursor-pointer hover:shadow-card-hover hover:border-line-hover transition-all duration-200',
          className,
        )}
        {...props}
      >
        {children}
      </div>
    );
  },
);

Card.displayName = 'Card';
