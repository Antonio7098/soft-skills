import { useEffect } from 'react';
import { Navigate, useParams } from 'react-router-dom';
import { useAuthSession } from '@/auth';
import { LoadingState } from '@/design-system/patterns/LoadingState';

function normalizeOrganisationRouteParam(value: string | undefined): string | null {
  if (!value) return null;
  if (value.startsWith(':')) return null;
  if (value.includes('{') || value.includes('}')) return null;
  return value;
}

interface AdminRouteAliasRedirectProps {
  readonly to: string;
}

export function AdminRouteAliasRedirect({ to }: AdminRouteAliasRedirectProps) {
  const { organisationId: rawOrganisationId } = useParams<{ organisationId: string }>();
  const { session, setActiveOrganisation } = useAuthSession();
  const organisationId = normalizeOrganisationRouteParam(rawOrganisationId);

  useEffect(() => {
    if (!organisationId || session?.active_organisation_id === organisationId) {
      return;
    }
    void setActiveOrganisation(organisationId);
  }, [organisationId, session, setActiveOrganisation]);

  if (organisationId && session?.active_organisation_id !== organisationId) {
    return <LoadingState message="Switching organisation scope..." />;
  }

  return <Navigate to={to} replace />;
}
