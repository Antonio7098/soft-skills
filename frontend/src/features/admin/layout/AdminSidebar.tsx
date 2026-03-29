import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  GraduationCap,
  FolderCheck,
  FlaskConical,
  FileText,
  GitBranch,
  Scale,
  ScrollText,
  Activity,
  PanelLeftClose,
  PanelLeftOpen,
  ArrowLeft,
  Lightbulb,
  Target,
  Map,
} from 'lucide-react';
import { cn } from '@/lib/cn';

interface NavItemProps {
  readonly to: string;
  readonly icon: React.ReactNode;
  readonly label: string;
  readonly collapsed: boolean;
}

function NavItem({ to, icon, label, collapsed }: NavItemProps) {
  return (
    <NavLink
      to={to}
      end={to === '/admin'}
      className={({ isActive }) =>
        cn(
          'flex items-center gap-3 rounded-lg transition-all duration-150',
          collapsed ? 'justify-center p-2.5' : 'px-3 py-2.5',
          isActive
            ? 'bg-accent/10 text-accent border border-accent/20'
            : 'text-sidebar-text-muted hover:text-sidebar-text hover:bg-sidebar-item-hover border border-transparent',
        )
      }
    >
      <span className="shrink-0">{icon}</span>
      {!collapsed && <span className="text-body-sm font-medium">{label}</span>}
    </NavLink>
  );
}

const NAV_SECTIONS = [
  {
    title: 'Overview',
    items: [
      { path: '/admin', label: 'Dashboard', icon: LayoutDashboard },
    ],
  },
  {
    title: 'People',
    items: [
      { path: '/admin/users', label: 'Users', icon: Users },
      { path: '/admin/learners', label: 'Learners', icon: GraduationCap },
    ],
  },
  {
    title: 'Content',
    items: [
      { path: '/admin/collections', label: 'Collections', icon: FolderCheck },
      { path: '/admin/evaluations', label: 'Evaluations', icon: FlaskConical },
      { path: '/admin/prompts', label: 'Prompts', icon: FileText },
    ],
  },
  {
    title: 'System',
    items: [
      { path: '/admin/pipelines', label: 'Pipelines', icon: GitBranch },
      { path: '/admin/rubrics', label: 'Rubrics', icon: Scale },
      { path: '/admin/audit', label: 'Audit Logs', icon: ScrollText },
      { path: '/admin/telemetry', label: 'Telemetry', icon: Activity },
    ],
  },
  {
    title: 'Organisations',
    items: [
      { path: '/admin/skills', label: 'Skills', icon: Lightbulb },
      { path: '/admin/competencies', label: 'Competencies', icon: Target },
      { path: '/admin/org-rubrics', label: 'Org Rubrics', icon: Scale },
      { path: '/admin/prompt-items', label: 'Prompt Items', icon: FileText },
      { path: '/admin/scenarios', label: 'Scenarios', icon: Map },
    ],
  },
];

export function AdminSidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const sections = NAV_SECTIONS;

  return (
    <aside
      className={cn(
        'flex flex-col h-screen bg-sidebar-bg border-r border-line sticky top-0',
        'transition-all duration-300 ease-out shrink-0 z-20',
        collapsed ? 'w-[72px]' : 'w-[240px]',
      )}
    >
      <div
        className={cn(
          'flex items-center border-b border-line h-14 shrink-0',
          collapsed ? 'justify-center px-2' : 'justify-between px-4',
        )}
      >
        {!collapsed && (
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-md bg-accent flex items-center justify-center">
              <span className="font-display text-body-sm text-surface-primary font-bold">A</span>
            </div>
            <span className="font-display text-body-md text-sidebar-text font-semibold">Admin</span>
          </div>
        )}
        {collapsed && (
          <div className="w-7 h-7 rounded-md bg-accent flex items-center justify-center">
            <span className="font-display text-body-sm text-surface-primary font-bold">A</span>
          </div>
        )}
      </div>

      <div className={cn('py-3 border-b border-line', collapsed ? 'px-2' : 'px-3')}>
        <NavLink
          to="/"
          className={cn(
            'flex items-center gap-2 rounded-lg transition-all duration-150',
            collapsed ? 'justify-center p-2.5' : 'px-3 py-2',
            'text-sidebar-text-muted hover:text-sidebar-text hover:bg-sidebar-item-hover',
          )}
        >
          <ArrowLeft className="w-4 h-4" />
          {!collapsed && <span className="text-body-sm font-medium">Back to App</span>}
        </NavLink>
      </div>

      <nav className={cn('flex-1 overflow-y-auto py-4', collapsed ? 'px-2' : 'px-3')}>
        {sections.map((section, idx) => (
          <div key={section.title} className={cn(idx > 0 && 'mt-6')}>
            {!collapsed && (
              <span className="px-3 text-body-xs font-medium text-sidebar-text-muted uppercase tracking-wider">
                {section.title}
              </span>
            )}
            <div className={cn('flex flex-col gap-1', !collapsed && 'mt-2')}>
              {section.items.map((item) => (
                <NavItem
                  key={item.path}
                  to={item.path}
                  icon={<item.icon className="w-[18px] h-[18px]" />}
                  label={item.label}
                  collapsed={collapsed}
                />
              ))}
            </div>
          </div>
        ))}
      </nav>

      <div className={cn('border-t border-line py-3', collapsed ? 'px-2' : 'px-3')}>
        <button
          onClick={() => setCollapsed((prev) => !prev)}
          className={cn(
            'flex items-center gap-2 rounded-lg transition-all duration-150 w-full',
            'text-sidebar-text-muted hover:text-sidebar-text hover:bg-sidebar-item-hover',
            collapsed ? 'justify-center p-2.5' : 'px-3 py-2',
          )}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? (
            <PanelLeftOpen className="w-[18px] h-[18px]" />
          ) : (
            <>
              <PanelLeftClose className="w-[18px] h-[18px]" />
              <span className="text-body-sm font-medium">Collapse</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
}
