import { Outlet } from 'react-router-dom';

export function SessionLayout() {
  return (
    <div className="flex min-h-screen w-full bg-surface-primary">
      <div className="noise-overlay" />
      <main className="flex-1 relative z-0">
        <Outlet />
      </main>
    </div>
  );
}
