import { type ReactNode, type CSSProperties, type JSX } from 'react';
import { useTheme } from '../../theme';

interface AppShellProps {
  children: ReactNode;
  sidebar?: ReactNode;
  header?: ReactNode;
  style?: CSSProperties;
}

export function AppShell({
  children,
  sidebar,
  header,
  style,
}: AppShellProps): JSX.Element {
  const { activeTheme: theme } = useTheme();

  const containerStyle: CSSProperties = {
    display: 'flex',
    minHeight: '100vh',
    backgroundColor: theme.colors.background,
    color: theme.colors.text,
    fontFamily: theme.typography.fontBody,
    ...style,
  };

  const mainStyle: CSSProperties = {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
    position: 'relative',
  };

  const contentStyle: CSSProperties = {
    flex: 1,
    padding: theme.spacing.space6,
    overflowY: 'auto',
  };

  return (
    <div style={containerStyle}>
      {sidebar && (
        <aside
          style={{
            width: '280px',
            minHeight: '100vh',
            backgroundColor: theme.colors.surface,
            borderRight: `1px solid ${theme.colors.border}`,
            display: 'flex',
            flexDirection: 'column',
            flexShrink: 0,
            pointerEvents: 'auto',
            position: 'relative',
            zIndex: 1,
            boxSizing: 'border-box',
          }}
        >
          {sidebar}
        </aside>
      )}
      <main style={mainStyle}>
        {header && (
          <header
            style={{
              height: '64px',
              backgroundColor: theme.colors.surface,
              borderBottom: `1px solid ${theme.colors.border}`,
              display: 'flex',
              alignItems: 'center',
              padding: `0 ${theme.spacing.space6}`,
            }}
          >
            {header}
          </header>
        )}
        <div style={contentStyle}>{children}</div>
      </main>
    </div>
  );
}
