import { useTheme } from "@/theme";

export function ThemeSwitcher() {
  const { mode, toggleTheme } = useTheme();
  const isDark = mode === "dark";

  return (
    <button
      onClick={toggleTheme}
      aria-label={`Switch to ${isDark ? "light" : "dark"} theme`}
      style={{
        position: "relative",
        width: 56,
        height: 28,
        borderRadius: "var(--radius-full)",
        backgroundColor: "var(--color-bg-tertiary)",
        border: "1px solid var(--color-border-default)",
        cursor: "pointer",
        transition: "all var(--transition-normal)",
        display: "flex",
        alignItems: "center",
        padding: "0 3px",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = "var(--color-accent-primary)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = "var(--color-border-default)";
      }}
    >
      <span
        style={{
          position: "absolute",
          left: 3,
          fontSize: 13,
          lineHeight: 1,
          opacity: isDark ? 0.8 : 0.3,
          transition: "opacity var(--transition-normal)",
        }}
      >
        <MoonIcon />
      </span>
      <span
        style={{
          position: "absolute",
          right: 3,
          fontSize: 13,
          lineHeight: 1,
          opacity: isDark ? 0.3 : 0.8,
          transition: "opacity var(--transition-normal)",
        }}
      >
        <SunIcon />
      </span>
      <span
        style={{
          width: 20,
          height: 20,
          borderRadius: "50%",
          backgroundColor: "var(--color-accent-primary)",
          transform: isDark ? "translateX(0)" : "translateX(26px)",
          transition: "transform var(--transition-slow)",
          boxShadow: "var(--shadow-sm)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <span style={{ fontSize: 10, lineHeight: 1, color: "#fff" }}>
          {isDark ? <MoonIcon /> : <SunIcon />}
        </span>
      </span>
    </button>
  );
}

function SunIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2" />
      <path d="M12 20v2" />
      <path d="m4.93 4.93 1.41 1.41" />
      <path d="m17.66 17.66 1.41 1.41" />
      <path d="M2 12h2" />
      <path d="M20 12h2" />
      <path d="m6.34 17.66-1.41 1.41" />
      <path d="m19.07 4.93-1.41 1.41" />
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" />
    </svg>
  );
}
