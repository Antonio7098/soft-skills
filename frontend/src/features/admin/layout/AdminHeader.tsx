import { useLocation } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';
import { useAuthSession, useAdminScope } from '@/auth';

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
  '/admin/skills': 'Skills',
  '/admin/competencies': 'Competencies',
  '/admin/org-rubrics': 'Org Rubrics',
  '/admin/prompt-items': 'Prompt Items',
  '/admin/scenarios': 'Scenarios',
};

export function AdminHeader() {
  const location = useLocation();
  const currentTitle = ROUTE_TITLES[location.pathname]
    || (location.pathname.includes('/orgs/') && location.pathname.endsWith('/skills') ? 'Skills' : null)
    || (location.pathname.includes('/orgs/') && location.pathname.endsWith('/competencies') ? 'Competencies' : null)
    || (location.pathname.includes('/orgs/') && location.pathname.endsWith('/rubrics') ? 'Org Rubrics' : null)
    || (location.pathname.includes('/orgs/') && location.pathname.endsWith('/prompt-items') ? 'Prompt Items' : null)
    || (location.pathname.includes('/orgs/') && location.pathname.endsWith('/scenarios') ? 'Scenarios' : null)
    || 'Admin';
  const { session } = useAuthSession();
  const { activeOrganisation } = useAdminScope();
  const initials = session?.actor?.display_name
    ?.split(' ')
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase() ?? 'AD';

  return (
    <header className="h-14 border-b border-line bg-surface-primary/80 backdrop-blur-sm sticky top-0 z-10">
      <div className="h-full px-6 flex items-center justify-between">
        <div className="flex items-center gap-2 text-body-sm">
          <span className="text-content-tertiary">Admin</span>
          <ChevronRight className="w-3.5 h-3.5 text-content-tertiary" />
          <span className="text-content-primary font-medium">{currentTitle}</span>
          {activeOrganisation && (
            <>
              <ChevronRight className="w-3.5 h-3.5 text-content-tertiary" />
              <span className="text-content-secondary">{activeOrganisation.organisation_name}</span>
            </>
          )}
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-accent/10 border border-accent/20 flex items-center justify-center">
              <span className="text-body-xs font-semibold text-accent">{initials}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-body-xs font-medium text-content-primary">{session?.actor?.display_name ?? 'Admin User'}</span>
              <span className="text-body-xs text-content-tertiary">
                {session?.platform_role === 'superadmin' ? 'Superadmin' : activeOrganisation?.role === 'org_admin' ? 'Organisation Admin' : 'Administrator'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
