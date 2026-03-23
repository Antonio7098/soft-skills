import type { ReactNode } from 'react';
import { NavLink } from 'react-router-dom';
import { cn } from '@/lib/cn';

interface NavItemProps {
  readonly to: string;
  readonly icon: ReactNode;
  readonly label: string;
  readonly collapsed?: boolean;
}

export function NavItem({ to, icon, label, collapsed = false }: NavItemProps) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        cn(
          'group flex items-center gap-3 rounded-button transition-all duration-150',
          'text-sidebar-text-muted hover:text-sidebar-text hover:bg-sidebar-item-hover',
          collapsed ? 'justify-center p-2.5' : 'px-3 py-2.5',
          isActive && 'bg-sidebar-item-active text-sidebar-text font-medium',
        )
      }
    >
      <span className="shrink-0 w-5 h-5">{icon}</span>
      {!collapsed && (
        <span className="text-body-sm truncate">{label}</span>
      )}
    </NavLink>
  );
}
