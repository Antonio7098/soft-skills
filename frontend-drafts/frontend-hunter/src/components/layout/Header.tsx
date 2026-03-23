import { ThemeSwitcher } from "@/components/composed";
import { Avatar } from "@/components/primitives";

export function Header() {
  return (
    <header
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "var(--spacing-4) var(--spacing-8)",
        borderBottom: "1px solid var(--color-border-subtle)",
        backgroundColor: "var(--color-bg-secondary)",
        backdropFilter: "blur(12px)",
        position: "sticky",
        top: 0,
        zIndex: 50,
        minHeight: 64,
      }}
    >
      {/* Search */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "var(--spacing-3)",
          flex: 1,
          maxWidth: 400,
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "var(--spacing-2)",
            padding: "var(--spacing-2) var(--spacing-3)",
            backgroundColor: "var(--color-bg-tertiary)",
            border: "1px solid var(--color-border-subtle)",
            borderRadius: "var(--radius-md)",
            width: "100%",
            color: "var(--color-text-tertiary)",
            fontSize: "var(--font-size-sm)",
          }}
        >
          <SearchIcon />
          <span>Search skills, collections...</span>
          <span
            style={{
              marginLeft: "auto",
              fontSize: "var(--font-size-xs)",
              padding: "2px 6px",
              backgroundColor: "var(--color-bg-secondary)",
              borderRadius: "var(--radius-sm)",
              border: "1px solid var(--color-border-default)",
              fontFamily: "var(--font-mono)",
            }}
          >
            /
          </span>
        </div>
      </div>

      {/* Right actions */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "var(--spacing-5)",
        }}
      >
        <ThemeSwitcher />

        <button
          style={{
            position: "relative",
            color: "var(--color-text-secondary)",
            padding: "var(--spacing-1)",
            cursor: "pointer",
            border: "none",
            background: "none",
            borderRadius: "var(--radius-md)",
            transition: "all var(--transition-normal)",
            display: "flex",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = "var(--color-text-primary)";
            e.currentTarget.style.backgroundColor = "var(--color-surface-hover)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = "var(--color-text-secondary)";
            e.currentTarget.style.backgroundColor = "transparent";
          }}
        >
          <BellIcon />
          <span
            style={{
              position: "absolute",
              top: 2,
              right: 2,
              width: 7,
              height: 7,
              borderRadius: "50%",
              backgroundColor: "var(--color-status-error)",
              border: "1.5px solid var(--color-bg-secondary)",
            }}
          />
        </button>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "var(--spacing-3)",
          }}
        >
          <Avatar name="Alex Morgan" size="sm" status="online" />
          <div style={{ display: "flex", flexDirection: "column" }}>
            <span
              style={{
                fontSize: "var(--font-size-sm)",
                fontWeight: "var(--font-weight-medium)",
                color: "var(--color-text-primary)",
                lineHeight: "var(--line-height-tight)",
              }}
            >
              Alex Morgan
            </span>
            <span
              style={{
                fontSize: "var(--font-size-xs)",
                color: "var(--color-text-tertiary)",
              }}
            >
              Consultant
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}

function SearchIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
  );
}

function BellIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
      <path d="M13.73 21a2 2 0 0 1-3.46 0" />
    </svg>
  );
}
