import { Bell, Search } from 'lucide-react';
import { useLocation } from 'react-router-dom';
import { Avatar } from '@/design-system/primitives/Avatar';
import { NAV_ROUTES } from '@/lib/nav-config';

function getPageTitle(pathname: string): string {
  const route = NAV_ROUTES.find((r) => r.path === pathname || (r.path !== '/' && pathname.startsWith(r.path)));
  return route ? route.label : 'Dashboard';
}

export function TopBar() {
  const location = useLocation();
  const title = getPageTitle(location.pathname);

  return (
    <header className="h-16 border-b border-line bg-surface-primary/80 backdrop-blur-md sticky top-0 z-10 flex items-center justify-between px-8 shrink-0">
      <div className="flex items-center gap-4">
        <h2 className="font-display text-display-sm text-content-primary mt-1">{title}</h2>
      </div>

      <div className="flex items-center gap-4">
        <div className="relative hidden md:block">
          <Search className="w-4 h-4 text-content-tertiary absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search..."
            className="w-64 h-9 pl-9 pr-4 rounded-full bg-surface-secondary border border-transparent focus:border-line focus:bg-surface-primary focus:outline-none focus:ring-2 focus:ring-accent/20 text-body-sm transition-all duration-200"
          />
        </div>
        
        <button className="relative w-9 h-9 flex items-center justify-center rounded-full text-content-secondary hover:text-content-primary hover:bg-surface-secondary transition-colors">
          <Bell className="w-5 h-5" />
          <span className="absolute top-2 right-2.5 w-1.5 h-1.5 bg-status-error rounded-full ring-2 ring-surface-primary" />
        </button>

        <div className="w-px h-6 bg-line mx-1" />

        <button className="flex items-center gap-2 hover:opacity-80 transition-opacity">
          <Avatar fallback="Alex Chen" size="sm" />
        </button>
      </div>
    </header>
  );
}
