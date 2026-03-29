import { Outlet } from 'react-router-dom';
import { AdminSidebar } from './AdminSidebar';
import { AdminHeader } from './AdminHeader';

export function AdminLayout() {
  return (
    <div className="flex min-h-screen w-full bg-surface-primary">
      <div className="noise-overlay" />
      <AdminSidebar />
      <div className="flex-1 flex flex-col min-w-0 relative z-0">
        <AdminHeader />
        <main className="flex-1 overflow-x-hidden p-6">
          <div className="max-w-7xl mx-auto w-full">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
