import { useState, type ReactNode } from "react";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <div
      style={{
        display: "flex",
        minHeight: "100vh",
        backgroundColor: "var(--color-bg-primary)",
      }}
    >
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
      />
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          minWidth: 0,
          marginLeft: sidebarCollapsed ? 64 : 240,
          transition: "margin-left var(--transition-slow)",
        }}
      >
        <Header />
        <main
          style={{
            flex: 1,
            padding: "var(--spacing-8)",
            maxWidth: 1200,
            width: "100%",
            margin: "0 auto",
          }}
        >
          {children}
        </main>
      </div>
    </div>
  );
}
