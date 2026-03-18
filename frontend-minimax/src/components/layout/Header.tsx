import { type ReactNode, type CSSProperties, type JSX } from 'react';
import { useTheme } from '../../theme';

interface HeaderProps {
  title?: string;
  subtitle?: string;
  actions?: ReactNode;
  style?: CSSProperties;
}

export function Header({
  title,
  subtitle,
  actions,
  style,
}: HeaderProps): JSX.Element {
  const { activeTheme: theme } = useTheme();

  const headerStyle: CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    width: '100%',
    ...style,
  };

  const titleGroupStyle: CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    gap: theme.spacing.space1,
  };

  const titleStyle: CSSProperties = {
    fontFamily: theme.typography.fontDisplay,
    fontSize: theme.typography.size2xl,
    fontWeight: theme.typography.weightBold,
    color: theme.colors.text,
    lineHeight: theme.typography.lineHeightTight,
  };

  const subtitleStyle: CSSProperties = {
    fontFamily: theme.typography.fontBody,
    fontSize: theme.typography.sizeSm,
    color: theme.colors.textMuted,
  };

  const actionsStyle: CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: theme.spacing.space3,
  };

  return (
    <header style={headerStyle}>
      <div style={titleGroupStyle}>
        {title && <h1 style={titleStyle}>{title}</h1>}
        {subtitle && <p style={subtitleStyle}>{subtitle}</p>}
      </div>
      {actions && <div style={actionsStyle}>{actions}</div>}
    </header>
  );
}
