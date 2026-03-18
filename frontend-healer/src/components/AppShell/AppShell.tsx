import { type ReactNode } from 'react';
import { ThemeToggle } from '../ThemeToggle/ThemeToggle';
import { useTheme } from '../../design-system/context/ThemeContext';

interface AppShellProps {
  children: ReactNode;
  currentPath: string;
  onNavigate: (path: string) => void;
}

const navItems = [
  { id: 'dashboard', label: 'Dashboard', icon: '◈' },
  { id: 'practice', label: 'Practice', icon: '▶' },
  { id: 'collections', label: 'Collections', icon: '▦' },
  { id: 'progress', label: 'Progress', icon: '◉' },
  { id: 'create', label: 'Create', icon: '✦' },
];

/**
 * AppShell - Main application layout.
 * Provides sidebar navigation and header.
 */
export function AppShell({ children, currentPath, onNavigate }: AppShellProps) {
  const { theme } = useTheme();

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '240px 1fr',
      gridTemplateRows: 'auto 1fr',
      minHeight: '100vh',
      backgroundColor: 'var(--color-bg-primary)',
    }}>
      {/* Sidebar */}
      <aside style={{
        gridRow: '1 / -1',
        backgroundColor: 'var(--color-bg-secondary)',
        borderRight: '1px solid var(--color-border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        padding: 'var(--space-6) 0',
      }}>
        {/* Logo */}
        <div style={{
          padding: '0 var(--space-6)',
          marginBottom: 'var(--space-8)',
        }}>
          <div style={{
            fontFamily: 'var(--font-display)',
            fontSize: 'var(--font-size-xl)',
            color: 'var(--color-fg-primary)',
            letterSpacing: '-0.025em',
          }}>
            SoftSkills
          </div>
          <div style={{
            fontFamily: 'var(--font-body)',
            fontSize: 'var(--font-size-micro)',
            color: 'var(--color-fg-tertiary)',
            letterSpacing: '0.1em',
            textTransform: 'uppercase' as const,
            marginTop: 'var(--space-1)',
          }}>
            Practice Platform
          </div>
        </div>

        {/* Navigation */}
        <nav style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-1)',
          padding: '0 var(--space-3)',
        }}>
          {navItems.map((item) => {
            const isActive = currentPath === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onNavigate(item.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 'var(--space-3)',
                  padding: 'var(--space-3) var(--space-4)',
                  fontFamily: 'var(--font-body)',
                  fontSize: 'var(--font-size-base)',
                  fontWeight: isActive ? 500 : 400,
                  color: isActive ? 'var(--color-fg-primary)' : 'var(--color-fg-secondary)',
                  backgroundColor: isActive ? 'var(--color-bg-tertiary)' : 'transparent',
                  border: 'none',
                  borderRadius: 'var(--radius-md)',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all var(--duration-fast) var(--easing-default)',
                }}
              >
                <span style={{
                  fontSize: '1.125rem',
                  width: '1.5rem',
                  textAlign: 'center',
                  color: isActive ? 'var(--color-accent-primary)' : 'var(--color-fg-tertiary)',
                }}>
                  {item.icon}
                </span>
                {item.label}
              </button>
            );
          })}
        </nav>

        {/* Theme toggle at bottom of sidebar */}
        <div style={{
          padding: 'var(--space-4) var(--space-6)',
          borderTop: '1px solid var(--color-border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <span style={{
            fontFamily: 'var(--font-body)',
            fontSize: 'var(--font-size-small)',
            color: 'var(--color-fg-tertiary)',
          }}>
            {theme.name}
          </span>
          <ThemeToggle />
        </div>
      </aside>

      {/* Header */}
      <header style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: 'var(--space-4) var(--space-8)',
        borderBottom: '1px solid var(--color-border-subtle)',
        backgroundColor: 'var(--color-bg-primary)',
      }}>
        <div style={{
          fontFamily: 'var(--font-body)',
          fontSize: 'var(--font-size-small)',
          color: 'var(--color-fg-tertiary)',
        }}>
          {navItems.find(n => n.id === currentPath)?.label || 'SoftSkills'}
        </div>

        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--space-4)',
        }}>
          <div style={{
            width: '2rem',
            height: '2rem',
            borderRadius: 'var(--radius-full)',
            backgroundColor: 'var(--color-bg-muted)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontFamily: 'var(--font-body)',
            fontSize: 'var(--font-size-small)',
            fontWeight: 600,
            color: 'var(--color-fg-secondary)',
          }}>
            A
          </div>
        </div>
      </header>

      {/* Main content */}
      <main style={{
        padding: 'var(--space-8)',
        overflowY: 'auto',
      }}>
        {children}
      </main>
    </div>
  );
}
