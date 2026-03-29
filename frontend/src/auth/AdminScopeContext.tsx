import { createContext, useContext, useEffect, useMemo, type ReactNode } from 'react';
import { useParams } from 'react-router-dom';
import { useAuthSession } from './AuthSessionContext';
import type { OrganisationMembershipView } from '@/data';

function normalizeOrganisationRouteParam(value: string | undefined): string | null {
  if (!value) return null;
  if (value.startsWith(':')) return null;
  if (value.includes('{') || value.includes('}')) return null;
  return value;
}

interface AdminScopeContextValue {
  readonly activeOrganisation: OrganisationMembershipView | null;
  readonly availableOrganisations: OrganisationMembershipView[];
  readonly organisationId: string | null;
  readonly routeOrganisationId: string | null;
  can(permission: string): boolean;
}

const AdminScopeContext = createContext<AdminScopeContextValue | null>(null);

interface AdminScopeProviderProps {
  readonly children: ReactNode;
}

export function AdminScopeProvider({ children }: AdminScopeProviderProps) {
  const { organisationId: rawOrganisationId } = useParams<{ organisationId: string }>();
  const { session, setActiveOrganisation } = useAuthSession();
  const routeOrganisationId = normalizeOrganisationRouteParam(rawOrganisationId);

  const availableOrganisations = session?.org_memberships ?? [];
  const resolvedOrganisationId = routeOrganisationId
    ?? session?.active_organisation_id
    ?? availableOrganisations[0]?.organisation_id
    ?? null;

  useEffect(() => {
    if (!session || !resolvedOrganisationId || session.active_organisation_id === resolvedOrganisationId) {
      return;
    }
    void setActiveOrganisation(resolvedOrganisationId);
  }, [resolvedOrganisationId, session, setActiveOrganisation]);

  const activeOrganisation = availableOrganisations.find(
    (membership) => membership.organisation_id === resolvedOrganisationId,
  ) ?? null;

  const value = useMemo<AdminScopeContextValue>(() => ({
    activeOrganisation,
    availableOrganisations,
    organisationId: resolvedOrganisationId,
    routeOrganisationId: routeOrganisationId ?? null,
    can(permission: string) {
      if (!session) return false;
      if (session.platform_role === 'superadmin') return true;
      return Boolean(activeOrganisation?.permissions.includes(permission));
    },
  }), [activeOrganisation, availableOrganisations, resolvedOrganisationId, routeOrganisationId, session]);

  return (
    <AdminScopeContext.Provider value={value}>
      {children}
    </AdminScopeContext.Provider>
  );
}

export function useAdminScope(): AdminScopeContextValue {
  const context = useContext(AdminScopeContext);
  if (!context) {
    throw new Error('useAdminScope must be used within AdminScopeProvider');
  }
  return context;
}
