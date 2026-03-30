import { useState } from 'react';
import { LogOut, Mail, User } from 'lucide-react';
import { useAuthSession } from '@/auth';
import { clearUserId, useData } from '@/data';
import { Card } from '@/design-system/primitives/Card';
import { Button } from '@/design-system/primitives/Button';
import { Avatar } from '@/design-system/primitives/Avatar';

export function ProfileCard() {
  const { session, isMockMode, activeOrganisation } = useAuthSession();
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const data = useData();

  const displayName = session?.actor?.display_name ?? 'User';
  const email = session?.actor?.email ?? '';
  const role = session?.platform_role ?? 'learner';

  const handleLogout = async () => {
    setIsLoggingOut(true);
    clearUserId();
    window.location.href = '/login';
  };

  const handleDeleteAccount = async () => {
    setIsDeleting(true);
    try {
      await data.deleteMe();
      clearUserId();
      window.location.href = '/login';
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <Card className="flex flex-col gap-6">
      <div className="flex flex-col gap-1">
        <h3 className="font-display text-display-xs text-content-primary">Profile</h3>
        <p className="text-body-sm text-content-secondary">Your account information and session details.</p>
      </div>

      <div className="flex flex-col gap-5">
        <div className="flex items-center gap-4 p-4 rounded-xl bg-surface-secondary/50 border border-line">
          <Avatar fallback={displayName} size="lg" />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <p className="font-body font-semibold text-body-md text-content-primary truncate">
                {displayName}
              </p>
              <span className="inline-flex items-center px-2 py-0.5 rounded-badge text-body-xs font-medium bg-accent/10 text-accent">
                {role}
              </span>
            </div>
            {activeOrganisation && (
              <p className="text-body-xs text-content-tertiary mt-0.5">
                {activeOrganisation.organisation_name}
              </p>
            )}
          </div>
        </div>

        <div className="flex flex-col gap-3">
          {email && (
            <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-surface-secondary/30">
              <div className="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center shrink-0">
                <Mail className="w-4 h-4 text-accent" />
              </div>
              <div className="min-w-0">
                <p className="text-body-xs text-content-tertiary uppercase tracking-wider font-medium">Email</p>
                <p className="text-body-sm text-content-primary truncate">{email}</p>
              </div>
            </div>
          )}

          <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-surface-secondary/30">
            <div className="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center shrink-0">
              <User className="w-4 h-4 text-accent" />
            </div>
            <div className="min-w-0">
              <p className="text-body-xs text-content-tertiary uppercase tracking-wider font-medium">Session Mode</p>
              <p className="text-body-sm text-content-primary">{isMockMode ? 'Demo (Mock)' : 'API'}</p>
            </div>
          </div>
        </div>

        <div className="pt-2 flex flex-col gap-3">
          <Button
            variant="danger"
            size="md"
            icon={<LogOut className="w-4 h-4" />}
            onClick={handleLogout}
            loading={isLoggingOut}
            className="w-full"
          >
            Sign out
          </Button>
          <Button
            variant="ghost"
            size="md"
            onClick={handleDeleteAccount}
            loading={isDeleting}
            className="w-full"
          >
            Delete account
          </Button>
        </div>
      </div>
    </Card>
  );
}
