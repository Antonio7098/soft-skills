import { useLocation } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';

const ROUTE_TITLES: Record<string, string> = {
  '/admin': 'Overview',
  '/admin/users': 'Users',
  '/admin/learners': 'Learners',
  '/admin/collections': 'Collections',
  '/admin/evaluations': 'Evaluations',
  '/admin/prompts': 'Prompts',
  '/admin/pipelines': 'Pipelines',
  '/admin/rubrics': 'Rubrics',
  '/admin/audit': 'Audit Logs',
  '/admin/telemetry': 'Telemetry',
};

export function AdminHeader() {
  const location = useLocation();
  const currentTitle = ROUTE_TITLES[location.pathname] || 'Admin';

  return (
    <header className="h-14 border-b border-line bg-surface-primary/80 backdrop-blur-sm sticky top-0 z-10">
      <div className="h-full px-6 flex items-center justify-between">
        <div className="flex items-center gap-2 text-body-sm">
          <span className="text-content-tertiary">Admin</span>
          <ChevronRight className="w-3.5 h-3.5 text-content-tertiary" />
          <span className="text-content-primary font-medium">{currentTitle}</span>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-accent/10 border border-accent/20 flex items-center justify-center">
              <span className="text-body-xs font-semibold text-accent">AD</span>
            </div>
            <div className="flex flex-col">
              <span className="text-body-xs font-medium text-content-primary">Admin User</span>
              <span className="text-body-xs text-content-tertiary">Administrator</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
