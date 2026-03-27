import { useState } from 'react';
import { PanelLeftClose, PanelLeftOpen } from 'lucide-react';
import { NavItem } from '@/components/navigation/NavItem';
import { ThemeSwitcher } from '@/components/navigation/ThemeSwitcher';
import { NAV_ROUTES } from '@/lib/nav-config';
import { cn } from '@/lib/cn';

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={cn(
        'flex flex-col h-screen bg-sidebar-bg border-r border-line sticky top-0',
        'transition-all duration-300 ease-out shrink-0 z-20',
        collapsed ? 'w-[72px]' : 'w-[260px]',
      )}
    >
      <div
        className={cn(
          'flex items-center border-b border-line h-16 shrink-0',
          collapsed ? 'justify-center px-2' : 'justify-between px-5',
        )}
      >
        {!collapsed && (
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-accent flex items-center justify-center">
              <span className="font-display text-body-lg text-surface-primary font-bold">S</span>
            </div>
            <span className="font-display text-display-sm text-sidebar-text mt-1">SoftSkills</span>
          </div>
        )}
        {collapsed && (
          <div className="w-8 h-8 rounded-lg bg-accent flex items-center justify-center">
            <span className="font-display text-body-lg text-surface-primary font-bold">S</span>
          </div>
        )}
      </div>

      <nav className={cn('flex-1 flex flex-col gap-1 py-4', collapsed ? 'px-2' : 'px-3')}>
        {NAV_ROUTES.map((route) => (
          <NavItem
            key={route.path}
            to={route.path}
            icon={<route.icon className="w-5 h-5" />}
            label={route.label}
            collapsed={collapsed}
          />
        ))}
      </nav>

      <div className={cn('border-t border-line py-4', collapsed ? 'px-2' : 'px-3')}>
        <ThemeSwitcher collapsed={collapsed} />
      </div>

      <div className={cn('border-t border-line py-3', collapsed ? 'px-2' : 'px-3')}>
        <button
          onClick={() => setCollapsed((prev) => !prev)}
          className={cn(
            'flex items-center gap-2 rounded-button transition-all duration-150 w-full',
            'text-sidebar-text-muted hover:text-sidebar-text hover:bg-sidebar-item-hover',
            collapsed ? 'justify-center p-2.5' : 'px-3 py-2',
          )}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? (
            <PanelLeftOpen className="w-5 h-5" />
          ) : (
            <>
              <PanelLeftClose className="w-5 h-5" />
              <span className="text-body-sm font-medium">Collapse</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
}
