import { type JSX } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useTheme } from '../../theme';
import { NavItem } from './Sidebar';

const navItems = [
  { label: 'Dashboard', path: '/dashboard' },
  { label: 'Practice', path: '/practice' },
  { label: 'Collections', path: '/collections' },
  { label: 'Progress', path: '/progress' },
  { label: 'Settings', path: '/settings' },
];

export function AppLayout(): JSX.Element {
  const { activeTheme, cycleTheme } = useTheme();
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <div
      style={{
        display: 'flex',
        minHeight: '100vh',
        backgroundColor: activeTheme.colors.background,
        color: activeTheme.colors.text,
        fontFamily: activeTheme.typography.fontBody,
      }}
    >
      <aside
        style={{
          width: '280px',
          minHeight: '100vh',
          backgroundColor: activeTheme.colors.surface,
          borderRight: `1px solid ${activeTheme.colors.border}`,
          display: 'flex',
          flexDirection: 'column',
          flexShrink: 0,
        }}
      >
        <nav
          style={{
            display: 'flex',
            flexDirection: 'column',
            height: '100%',
            width: '100%',
            padding: activeTheme.spacing.space4,
            gap: activeTheme.spacing.space1,
            boxSizing: 'border-box',
          }}
        >
          <div
            style={{
              fontFamily: activeTheme.typography.fontDisplay,
              fontSize: activeTheme.typography.size2xl,
              fontWeight: activeTheme.typography.weightBold,
              color: activeTheme.colors.text,
              padding: activeTheme.spacing.space4,
              marginBottom: activeTheme.spacing.space4,
            }}
          >
            SoftSkills
          </div>
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: activeTheme.spacing.space1,
              flex: 1,
              width: '100%',
              boxSizing: 'border-box',
            }}
          >
            {navItems.map((item) => (
              <NavItem
                key={item.path}
                label={item.label}
                isActive={location.pathname === item.path}
                onClick={() => navigate(item.path)}
              />
            ))}
          </div>
        </nav>
      </aside>

      <main
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          position: 'relative',
        }}
      >
        <header
          style={{
            height: '64px',
            backgroundColor: activeTheme.colors.surface,
            borderBottom: `1px solid ${activeTheme.colors.border}`,
            display: 'flex',
            alignItems: 'center',
            padding: `0 ${activeTheme.spacing.space6}`,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              width: '100%',
            }}
          >
            <span
              style={{
                fontFamily: activeTheme.typography.fontBody,
                fontSize: activeTheme.typography.sizeSm,
                color: activeTheme.colors.textMuted,
              }}
            >
              Practice Mode
            </span>
            <div style={{ display: 'flex', alignItems: 'center', gap: activeTheme.spacing.space4 }}>
              <button
                onClick={cycleTheme}
                style={{
                  background: 'none',
                  border: `1px solid ${activeTheme.colors.border}`,
                  borderRadius: activeTheme.borderRadius.md,
                  padding: `${activeTheme.spacing.space2} ${activeTheme.spacing.space4}`,
                  color: activeTheme.colors.text,
                  fontFamily: activeTheme.typography.fontBody,
                  fontSize: activeTheme.typography.sizeSm,
                  cursor: 'pointer',
                }}
              >
                {activeTheme.name} Theme
              </button>
            </div>
          </div>
        </header>
        <div
          style={{
            flex: 1,
            padding: activeTheme.spacing.space6,
            overflowY: 'auto',
          }}
        >
          <Outlet />
        </div>
      </main>
    </div>
  );
}
