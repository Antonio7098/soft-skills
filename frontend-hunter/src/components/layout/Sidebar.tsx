import { useLocation, useNavigate } from "react-router-dom";

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

interface NavItem {
  label: string;
  path: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  {
    label: "Dashboard",
    path: "/",
    icon: <DashboardIcon />,
  },
  {
    label: "Collections",
    path: "/collections",
    icon: <CollectionsIcon />,
  },
  {
    label: "Practice",
    path: "/practice",
    icon: <PracticeIcon />,
  },
  {
    label: "Progress",
    path: "/progress",
    icon: <ProgressIcon />,
  },
  {
    label: "Feedback",
    path: "/feedback",
    icon: <FeedbackIcon />,
  },
];

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <aside
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        height: "100vh",
        width: collapsed ? 64 : 240,
        backgroundColor: "var(--color-bg-secondary)",
        borderRight: "1px solid var(--color-border-subtle)",
        display: "flex",
        flexDirection: "column",
        transition: "width var(--transition-slow)",
        zIndex: 100,
        overflow: "hidden",
      }}
    >
      {/* Brand */}
      <div
        style={{
          padding: collapsed ? "var(--spacing-4)" : "var(--spacing-5) var(--spacing-5)",
          borderBottom: "1px solid var(--color-border-subtle)",
          display: "flex",
          alignItems: "center",
          gap: "var(--spacing-3)",
          minHeight: 64,
        }}
      >
        <div
          style={{
            width: 28,
            height: 28,
            borderRadius: "var(--radius-md)",
            backgroundColor: "var(--color-accent-primary)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
          }}
        >
          <span
            style={{
              fontFamily: "var(--font-display)",
              fontSize: 16,
              color: "#fff",
              fontWeight: "var(--font-weight-regular)",
            }}
          >
            S
          </span>
        </div>
        {!collapsed && (
          <span
            style={{
              fontFamily: "var(--font-display)",
              fontSize: "var(--font-size-xl)",
              color: "var(--color-text-primary)",
              whiteSpace: "nowrap",
              animation: "fadeIn var(--transition-normal) both",
            }}
          >
            SoftSkills
          </span>
        )}
      </div>

      {/* Nav */}
      <nav
        style={{
          flex: 1,
          padding: "var(--spacing-3)",
          display: "flex",
          flexDirection: "column",
          gap: "var(--spacing-1)",
          overflowY: "auto",
        }}
      >
        {navItems.map((item) => {
          const isActive =
            item.path === "/"
              ? location.pathname === "/"
              : location.pathname.startsWith(item.path);

          return (
            <button
              key={item.path}
              onClick={() => navigate(item.path)}
              title={collapsed ? item.label : undefined}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "var(--spacing-3)",
                padding: collapsed
                  ? "var(--spacing-2)"
                  : "var(--spacing-2) var(--spacing-3)",
                borderRadius: "var(--radius-md)",
                color: isActive
                  ? "var(--color-accent-primary)"
                  : "var(--color-text-secondary)",
                backgroundColor: isActive
                  ? "var(--color-accent-muted)"
                  : "transparent",
                fontSize: "var(--font-size-sm)",
                fontWeight: isActive
                  ? "var(--font-weight-semibold)"
                  : "var(--font-weight-medium)",
                transition: "all var(--transition-normal)",
                justifyContent: collapsed ? "center" : "flex-start",
                whiteSpace: "nowrap",
                border: "none",
                cursor: "pointer",
                fontFamily: "var(--font-body)",
              }}
              onMouseEnter={(e) => {
                if (!isActive) {
                  e.currentTarget.style.backgroundColor =
                    "var(--color-surface-hover)";
                  e.currentTarget.style.color = "var(--color-text-primary)";
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive) {
                  e.currentTarget.style.backgroundColor = "transparent";
                  e.currentTarget.style.color = "var(--color-text-secondary)";
                }
              }}
            >
              <span style={{ display: "flex", alignItems: "center", flexShrink: 0 }}>
                {item.icon}
              </span>
              {!collapsed && <span>{item.label}</span>}
            </button>
          );
        })}
      </nav>

      {/* Collapse toggle */}
      <div
        style={{
          padding: "var(--spacing-3)",
          borderTop: "1px solid var(--color-border-subtle)",
        }}
      >
        <button
          onClick={onToggle}
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            width: "100%",
            padding: "var(--spacing-2)",
            borderRadius: "var(--radius-md)",
            color: "var(--color-text-tertiary)",
            transition: "all var(--transition-normal)",
            cursor: "pointer",
            border: "none",
            backgroundColor: "transparent",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = "var(--color-surface-hover)";
            e.currentTarget.style.color = "var(--color-text-primary)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = "transparent";
            e.currentTarget.style.color = "var(--color-text-tertiary)";
          }}
        >
          <CollapseIcon collapsed={collapsed} />
        </button>
      </div>
    </aside>
  );
}

/* --- Icons --- */

function DashboardIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
      <rect x="14" y="14" width="7" height="7" rx="1" />
    </svg>
  );
}

function CollectionsIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
      <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
    </svg>
  );
}

function PracticeIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="5 3 19 12 5 21 5 3" />
    </svg>
  );
}

function ProgressIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <line x1="12" y1="20" x2="12" y2="10" />
      <line x1="18" y1="20" x2="18" y2="4" />
      <line x1="6" y1="20" x2="6" y2="16" />
    </svg>
  );
}

function FeedbackIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  );
}

function CollapseIcon({ collapsed }: { collapsed: boolean }) {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      style={{
        transform: collapsed ? "rotate(180deg)" : "rotate(0deg)",
        transition: "transform var(--transition-normal)",
      }}
    >
      <polyline points="15 18 9 12 15 6" />
    </svg>
  );
}
