import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Building2, Plus, Loader2, ChevronRight } from 'lucide-react';
import { Card } from '@/design-system/primitives/Card';
import { Button } from '@/design-system/primitives/Button';
import { Badge } from '@/design-system/primitives/Badge';
import { EmptyState } from '@/design-system/patterns/EmptyState';
import { useAuthSession } from '@/auth';

interface OrganisationListProps {
  readonly onCreateClick: () => void;
}

export function OrganisationList({ onCreateClick }: OrganisationListProps) {
  const navigate = useNavigate();
  const { session, setActiveOrganisation, activeOrganisation } = useAuthSession();
  const [switchingOrgId, setSwitchingOrgId] = useState<string | null>(null);

  const memberships = session?.org_memberships ?? [];

  const handleSwitchOrg = async (orgId: string) => {
    setSwitchingOrgId(orgId);
    try {
      await setActiveOrganisation(orgId);
      navigate('/admin');
    } finally {
      setSwitchingOrgId(null);
    }
  };

  if (memberships.length === 0) {
    return (
      <Card className="flex flex-col gap-4">
        <EmptyState
          icon={<Building2 className="w-6 h-6" />}
          title="No organisations yet"
          description="Create your first organisation to start collaborating with your team."
          action={
            <Button
              variant="primary"
              size="md"
              icon={<Plus className="w-4 h-4" />}
              onClick={onCreateClick}
            >
              Create Organisation
            </Button>
          }
        />
      </Card>
    );
  }

  return (
    <Card className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div className="flex flex-col gap-1">
          <h3 className="font-display text-display-xs text-content-primary">Organisations</h3>
          <p className="text-body-sm text-content-secondary">Manage your organisation memberships.</p>
        </div>
        <Button
          variant="secondary"
          size="sm"
          icon={<Plus className="w-4 h-4" />}
          onClick={onCreateClick}
        >
          New
        </Button>
      </div>

      <div className="flex flex-col gap-2">
        {memberships.map((membership) => {
          const isActive = activeOrganisation?.organisation_id === membership.organisation_id;
          const isSwitching = switchingOrgId === membership.organisation_id;
          return (
            <div
              key={membership.organisation_id}
              className="flex items-center gap-3 p-4 rounded-xl bg-surface-secondary/30 border border-line hover:border-line-strong transition-colors"
            >
              <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center shrink-0">
                <Building2 className="w-5 h-5 text-accent" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="font-body font-semibold text-body-md text-content-primary truncate">
                    {membership.organisation_name}
                  </p>
                  {isActive && (
                    <Badge variant="accent" size="sm">
                      Active
                    </Badge>
                  )}
                </div>
                <div className="flex items-center gap-2 mt-0.5">
                  <Badge
                    variant={membership.role === 'org_admin' ? 'default' : 'default'}
                    size="sm"
                  >
                    {membership.role === 'org_admin' ? 'Admin' : 'Member'}
                  </Badge>
                </div>
              </div>
              {!isActive && (
                <Button
                  variant="ghost"
                  size="sm"
                  icon={isSwitching ? <Loader2 className="w-4 h-4 animate-spin" /> : <ChevronRight className="w-4 h-4" />}
                  onClick={() => handleSwitchOrg(membership.organisation_id)}
                  disabled={isSwitching}
                >
                  {isSwitching ? 'Switching...' : 'Switch'}
                </Button>
              )}
            </div>
          );
        })}
      </div>
    </Card>
  );
}
