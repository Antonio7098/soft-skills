import { type ReactNode, type JSX } from 'react';
import { useTheme } from '../../theme';

type BadgeVariant = 'default' | 'success' | 'warning' | 'error' | 'primary';
type BadgeSize = 'sm' | 'md';

export interface BadgeProps {
  children: ReactNode;
  variant?: BadgeVariant;
  size?: BadgeSize;
}

export function Badge({
  children,
  variant = 'default',
  size = 'md',
}: BadgeProps): JSX.Element {
  const { activeTheme: theme } = useTheme();

  const variantStyles = {
    default: {
      backgroundColor: theme.colors.surfaceAlt,
      color: theme.colors.text,
    },
    success: {
      backgroundColor: `${theme.colors.success}20`,
      color: theme.colors.success,
    },
    warning: {
      backgroundColor: `${theme.colors.warning}20`,
      color: theme.colors.warning,
    },
    error: {
      backgroundColor: `${theme.colors.error}20`,
      color: theme.colors.error,
    },
    primary: {
      backgroundColor: theme.colors.primaryMuted,
      color: theme.colors.primary,
    },
  };

  const sizeStyles = {
    sm: {
      padding: `${theme.spacing.space1} ${theme.spacing.space2}`,
      fontSize: theme.typography.sizeXs,
    },
    md: {
      padding: `${theme.spacing.space1} ${theme.spacing.space3}`,
      fontSize: theme.typography.sizeSm,
    },
  };

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        fontFamily: theme.typography.fontBody,
        fontWeight: theme.typography.weightMedium,
        letterSpacing: theme.typography.letterSpacingWide,
        textTransform: 'uppercase',
        borderRadius: theme.borderRadius.sm,
        ...variantStyles[variant],
        ...sizeStyles[size],
      }}
    >
      {children}
    </span>
  );
}
