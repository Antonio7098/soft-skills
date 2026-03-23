import { type ReactNode, type CSSProperties, type JSX } from 'react';
import { useTheme } from '../../theme';

interface CardProps {
  children: ReactNode;
  variant?: 'default' | 'elevated' | 'outlined' | 'accent';
  padding?: 'none' | 'sm' | 'md' | 'lg';
  style?: CSSProperties;
}

export function Card({
  children,
  variant = 'default',
  padding = 'md',
  style,
}: CardProps): JSX.Element {
  const { activeTheme: theme } = useTheme();

  const paddingMap = {
    none: '0',
    sm: theme.spacing.space3,
    md: theme.spacing.space5,
    lg: theme.spacing.space8,
  };

  const variantStyles: Record<string, React.CSSProperties> = {
    default: {
      backgroundColor: theme.colors.surface,
      border: `1px solid ${theme.colors.border}`,
    },
    elevated: {
      backgroundColor: theme.colors.surface,
      boxShadow: theme.shadow.md,
    },
    outlined: {
      backgroundColor: 'transparent',
      border: `2px solid ${theme.colors.border}`,
    },
    accent: {
      backgroundColor: theme.colors.surface,
      border: `1px solid ${theme.colors.primary}`,
      borderLeftWidth: '4px',
    },
  };

  const cardStyle: React.CSSProperties = {
    borderRadius: theme.borderRadius.lg,
    padding: paddingMap[padding],
    transition: `all ${theme.motion.durationNormal} ${theme.motion.easeOut}`,
    ...variantStyles[variant],
    ...style,
  };

  return <div style={cardStyle}>{children}</div>;
}
