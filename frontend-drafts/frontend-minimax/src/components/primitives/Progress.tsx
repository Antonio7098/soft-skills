import { type CSSProperties, type JSX } from 'react';
import { useTheme } from '../../theme';

interface ProgressProps {
  value: number;
  max?: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  variant?: 'default' | 'success' | 'warning' | 'error';
  style?: CSSProperties;
}

export function Progress({
  value,
  max = 100,
  size = 'md',
  showLabel = false,
  variant = 'default',
  style,
}: ProgressProps): JSX.Element {
  const { activeTheme: theme } = useTheme();

  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  const variantColors = {
    default: theme.colors.primary,
    success: theme.colors.success,
    warning: theme.colors.warning,
    error: theme.colors.error,
  };

  const sizeMap = {
    sm: '0.25rem',
    md: '0.5rem',
    lg: '0.75rem',
  };

  const trackStyle: CSSProperties = {
    width: '100%',
    height: sizeMap[size],
    backgroundColor: theme.colors.surfaceAlt,
    borderRadius: theme.borderRadius.full,
    overflow: 'hidden',
  };

  const fillStyle: CSSProperties = {
    height: '100%',
    width: `${percentage}%`,
    backgroundColor: variantColors[variant],
    borderRadius: theme.borderRadius.full,
    transition: `width ${theme.motion.durationSlow} ${theme.motion.easeOut}`,
  };

  const labelStyle: CSSProperties = {
    fontFamily: theme.typography.fontMono,
    fontSize: theme.typography.sizeXs,
    color: theme.colors.textMuted,
    marginTop: theme.spacing.space1,
  };

  return (
    <div style={{ width: '100%', ...style }}>
      <div style={trackStyle}>
        <div style={fillStyle} />
      </div>
      {showLabel && (
        <div style={labelStyle}>{Math.round(percentage)}%</div>
      )}
    </div>
  );
}
