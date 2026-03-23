import { type CSSProperties, type JSX } from 'react';
import { useTheme } from '../../theme';

interface ProgressRingProps {
  value: number;
  max?: number;
  size?: number;
  strokeWidth?: number;
  variant?: 'default' | 'success' | 'warning' | 'error';
  showValue?: boolean;
  label?: string;
  style?: CSSProperties;
}

export function ProgressRing({
  value,
  max = 100,
  size = 80,
  strokeWidth = 6,
  variant = 'default',
  showValue = true,
  label,
  style,
}: ProgressRingProps): JSX.Element {
  const { activeTheme: theme } = useTheme();

  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percentage / 100) * circumference;

  const variantColors = {
    default: theme.colors.primary,
    success: theme.colors.success,
    warning: theme.colors.warning,
    error: theme.colors.error,
  };

  const containerStyle: CSSProperties = {
    position: 'relative',
    display: 'inline-flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: theme.spacing.space1,
    ...style,
  };

  const svgStyle: CSSProperties = {
    transform: 'rotate(-90deg)',
  };

  const trackStyle: CSSProperties = {
    fill: 'none',
    stroke: theme.colors.surfaceAlt,
    strokeWidth,
  };

  const progressStyle: CSSProperties = {
    fill: 'none',
    stroke: variantColors[variant],
    strokeWidth,
    strokeLinecap: 'round',
    strokeDasharray: circumference,
    strokeDashoffset: offset,
    transition: `stroke-dashoffset ${theme.motion.durationSlow} ${theme.motion.easeOut}`,
  };

  const valueStyle: CSSProperties = {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    fontFamily: theme.typography.fontMono,
    fontSize: theme.typography.sizeLg,
    fontWeight: theme.typography.weightBold,
    color: theme.colors.text,
  };

  const labelStyle: CSSProperties = {
    fontFamily: theme.typography.fontBody,
    fontSize: theme.typography.sizeXs,
    color: theme.colors.textMuted,
    textTransform: 'uppercase',
    letterSpacing: theme.typography.letterSpacingWide,
  };

  return (
    <div style={containerStyle}>
      <svg width={size} height={size} style={svgStyle}>
        <circle cx={size / 2} cy={size / 2} r={radius} style={trackStyle} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          style={progressStyle}
        />
      </svg>
      {showValue && (
        <span style={valueStyle}>{Math.round(percentage)}</span>
      )}
      {label && <span style={labelStyle}>{label}</span>}
    </div>
  );
}
