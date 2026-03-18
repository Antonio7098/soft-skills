import { useTheme } from '../../design-system';

/**
 * ThemeToggle - Switches between available themes.
 * Animated toggle with sun/moon iconography.
 */
export function ThemeToggle() {
  const { themeId, toggleTheme } = useTheme();

  const isObsidian = themeId === 'obsidian';

  return (
    <button
      onClick={toggleTheme}
      aria-label={`Switch to ${isObsidian ? 'light' : 'dark'} theme`}
      title={`Switch to ${isObsidian ? 'light' : 'dark'} theme`}
      style={{
        position: 'relative',
        width: '3.5rem',
        height: '2rem',
        borderRadius: 'var(--radius-full)',
        border: '1px solid var(--color-border-strong)',
        backgroundColor: 'var(--color-bg-tertiary)',
        cursor: 'pointer',
        padding: 0,
        overflow: 'hidden',
        transition: 'all var(--duration-normal) var(--easing-default)',
      }}
    >
      {/* Track icons */}
      <div style={{
        position: 'absolute',
        inset: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 0.375rem',
        pointerEvents: 'none',
      }}>
        {/* Sun icon */}
        <svg
          width="12"
          height="12"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{
            color: isObsidian ? 'var(--color-fg-tertiary)' : 'var(--color-accent-primary)',
            transition: 'color var(--duration-normal) var(--easing-default)',
          }}
        >
          <circle cx="12" cy="12" r="5" />
          <line x1="12" y1="1" x2="12" y2="3" />
          <line x1="12" y1="21" x2="12" y2="23" />
          <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
          <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
          <line x1="1" y1="12" x2="3" y2="12" />
          <line x1="21" y1="12" x2="23" y2="12" />
          <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
          <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
        </svg>

        {/* Moon icon */}
        <svg
          width="12"
          height="12"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{
            color: isObsidian ? 'var(--color-accent-primary)' : 'var(--color-fg-tertiary)',
            transition: 'color var(--duration-normal) var(--easing-default)',
          }}
        >
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
        </svg>
      </div>

      {/* Sliding thumb */}
      <span
        aria-hidden="true"
        style={{
          position: 'absolute',
          top: '2px',
          left: isObsidian ? 'calc(100% - 1.625rem)' : '2px',
          width: '1.5rem',
          height: '1.5rem',
          borderRadius: 'var(--radius-full)',
          backgroundColor: 'var(--color-interactive-default)',
          transition: 'left var(--duration-normal) var(--easing-bounce)',
          boxShadow: 'var(--shadow-md)',
        }}
      />
    </button>
  );
}
