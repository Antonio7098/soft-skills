import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';

export function MainLayout() {
  return (
    <div className="flex min-h-screen w-full bg-surface-primary">
      <div className="noise-overlay" />
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 relative z-0">
        <TopBar />
        <main className="flex-1 overflow-x-hidden p-8">
          <div className="max-w-6xl mx-auto w-full">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
