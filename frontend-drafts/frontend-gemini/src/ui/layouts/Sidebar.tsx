import { NavLink } from 'react-router-dom';
import { cn } from '@/utils/cn';
import { 
  LayoutDashboard, 
  Layers, 
  MessageSquare, 
  Users,
  Settings,
  Target
} from 'lucide-react';

export function Sidebar() {
  const links = [
    { name: 'Dashboard', href: '/', icon: LayoutDashboard },
    { name: 'Collections', href: '/collections', icon: Layers },
    { name: 'Scenarios', href: '/scenarios', icon: Target },
    { name: 'Interviews', href: '/interviews', icon: MessageSquare },
    { name: 'Mock People', href: '/people', icon: Users },
  ];

  return (
    <aside className="w-64 border-r border-border bg-background flex flex-col h-screen">
      <div className="p-6">
        <h1 className="text-2xl font-display font-bold text-primary tracking-tight">SoftSkills.</h1>
      </div>
      
      <nav className="flex-1 px-4 space-y-2">
        {links.map((link) => (
          <NavLink
            key={link.name}
            to={link.href}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2 rounded-md transition-colors text-sm font-medium',
                isActive 
                  ? 'bg-primary text-primary-foreground' 
                  : 'text-muted-foreground hover:bg-secondary hover:text-secondary-foreground'
              )
            }
          >
            <link.icon className="w-4 h-4" />
            {link.name}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-border">
        <NavLink
          to="/settings"
          className={({ isActive }) =>
            cn(
              'flex items-center gap-3 px-3 py-2 rounded-md transition-colors text-sm font-medium',
              isActive 
                ? 'bg-primary text-primary-foreground' 
                : 'text-muted-foreground hover:bg-secondary hover:text-secondary-foreground'
            )
          }
        >
          <Settings className="w-4 h-4" />
          Settings
        </NavLink>
      </div>
    </aside>
  );
}
