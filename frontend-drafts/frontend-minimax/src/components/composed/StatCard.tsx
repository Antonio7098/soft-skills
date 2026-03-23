import { type CSSProperties, type JSX } from 'react';
import { useTheme } from '../../theme';
import { Card } from '../primitives';

interface StatCardProps {
  label: string;
  value: string | number;
  change?: {
    value: number;
    type: 'increase' | 'decrease';
  };
  icon?: JSX.Element;
  style?: CSSProperties;
}

export function StatCard({
  label,
  value,
  change,
  icon,
  style,
}: StatCardProps): JSX.Element {
  const { activeTheme: theme } = useTheme();

  const containerStyle: CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    gap: theme.spacing.space2,
    ...style,
  };

  const headerStyle: CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  };

  const labelStyle: CSSProperties = {
    fontFamily: theme.typography.fontBody,
    fontSize: theme.typography.sizeSm,
    color: theme.colors.textMuted,
    textTransform: 'uppercase',
    letterSpacing: theme.typography.letterSpacingWide,
  };

  const valueStyle: CSSProperties = {
    fontFamily: theme.typography.fontDisplay,
    fontSize: theme.typography.size4xl,
    fontWeight: theme.typography.weightBold,
    color: theme.colors.text,
    lineHeight: theme.typography.lineHeightTight,
  };

  const changeStyle: CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: theme.spacing.space1,
    fontFamily: theme.typography.fontMono,
    fontSize: theme.typography.sizeSm,
    color: change?.type === 'increase' ? theme.colors.success : theme.colors.error,
  };

  return (
    <Card variant="elevated" padding="lg" style={containerStyle}>
      <div style={headerStyle}>
        <span style={labelStyle}>{label}</span>
        {icon && <span style={{ color: theme.colors.textMuted }}>{icon}</span>}
      </div>
      <span style={valueStyle}>{value}</span>
      {change && (
        <div style={changeStyle}>
          <span>{change.type === 'increase' ? '↑' : '↓'}</span>
          <span>{Math.abs(change.value)}%</span>
        </div>
      )}
    </Card>
  );
}
