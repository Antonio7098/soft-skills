import { useNavigate } from 'react-router-dom';
import { Shield } from 'lucide-react';
import { useAuthSession } from '@/auth';
import { PageShell } from '@/design-system/patterns/PageShell';
import { Card } from '@/design-system/primitives/Card';
import { Button } from '@/design-system/primitives/Button';
import { ThemeSwitcher } from '@/components/navigation/ThemeSwitcher';

export function Settings() {
  const navigate = useNavigate();
  const { isAdmin, session, activeOrganisation } = useAuthSession();

  return (
    <PageShell
      title="Settings"
      subtitle="Manage your account preferences and application settings."
    >
      <div className="max-w-2xl flex flex-col gap-6">
        <Card className="flex flex-col gap-6">
          <div className="flex flex-col gap-1">
            <h3 className="font-display text-display-xs text-content-primary">Appearance</h3>
            <p className="text-body-sm text-content-secondary">Customize the look and feel of the application.</p>
          </div>

          <div className="p-4 rounded-xl bg-surface-secondary/50 border border-line">
            <ThemeSwitcher />
          </div>
        </Card>

        <Card className="flex flex-col gap-6">
          <div className="flex flex-col gap-1">
            <h3 className="font-display text-display-xs text-content-primary">Administration</h3>
            <p className="text-body-sm text-content-secondary">
              {isAdmin
                ? 'Access administrative tools for your current organisation scope.'
                : 'Your current session does not include admin access.'}
            </p>
          </div>

          <div className="flex items-center justify-between p-4 rounded-xl bg-accent/5 border border-accent/20">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center">
                <Shield className="w-5 h-5 text-accent" />
              </div>
              <div>
                <p className="text-body-sm font-medium text-content-primary">Admin Dashboard</p>
                <p className="text-body-xs text-content-tertiary">
                  {isAdmin
                    ? `Manage users, content, and system settings${activeOrganisation ? ` for ${activeOrganisation.organisation_name}` : ''}`
                    : `Signed in as ${session?.actor?.display_name ?? 'User'}`}
                </p>
              </div>
            </div>
            <Button 
              variant="primary" 
              size="sm"
              onClick={() => navigate('/admin')}
              disabled={!isAdmin}
            >
              {isAdmin ? 'Go to Admin Dashboard' : 'Admin Access Required'}
            </Button>
          </div>
        </Card>
      </div>
    </PageShell>
  );
}
