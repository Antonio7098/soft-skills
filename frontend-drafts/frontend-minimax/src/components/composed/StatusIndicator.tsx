import { type JSX } from 'react';
import { useTheme } from '../../theme';

type AttemptStatus = 'started' | 'submitted' | 'pending' | 'assessed' | 'failed';

interface StatusIndicatorProps {
  status: AttemptStatus;
  showLabel?: boolean;
}

const statusConfig: Record<
  AttemptStatus,
  { label: string; variant: 'default' | 'warning' | 'primary' | 'success' | 'error' }
> = {
  started: { label: 'In Progress', variant: 'primary' },
  submitted: { label: 'Submitted', variant: 'primary' },
  pending: { label: 'Pending Review', variant: 'warning' },
  assessed: { label: 'Assessed', variant: 'success' },
  failed: { label: 'Failed', variant: 'error' },
};

export function StatusIndicator({
  status,
  showLabel = true,
}: StatusIndicatorProps): JSX.Element {
  const { activeTheme: theme } = useTheme();
  const config = statusConfig[status];

  const dotStyle = {
    width: '0.5rem',
    height: '0.5rem',
    borderRadius: theme.borderRadius.full,
    backgroundColor:
      config.variant === 'success'
        ? theme.colors.success
        : config.variant === 'warning'
        ? theme.colors.warning
        : config.variant === 'error'
        ? theme.colors.error
        : theme.colors.primary,
    boxShadow:
      config.variant === 'success'
        ? `0 0 8px ${theme.colors.success}`
        : config.variant === 'warning'
        ? `0 0 8px ${theme.colors.warning}`
        : config.variant === 'error'
        ? `0 0 8px ${theme.colors.error}`
        : `0 0 8px ${theme.colors.primary}`,
  };

  if (!showLabel) {
    return <span style={dotStyle} />;
  }

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: theme.spacing.space2 }}>
      <span style={dotStyle} />
      <span
        style={{
          fontFamily: theme.typography.fontBody,
          fontSize: theme.typography.sizeSm,
          color: theme.colors.textMuted,
        }}
      >
        {config.label}
      </span>
    </div>
  );
}
