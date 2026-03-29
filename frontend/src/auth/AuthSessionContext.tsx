import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { useData, type AuthProfileView, type AuthSessionView, type OrganisationMembershipView } from '@/data';
import { LoadingState } from '@/design-system/patterns/LoadingState';

interface AuthSessionContextValue {
  readonly session: AuthSessionView | null;
  readonly authProfiles: AuthProfileView[];
  readonly loading: boolean;
  readonly error: string | null;
  readonly isAuthenticated: boolean;
  readonly isAdmin: boolean;
  readonly isMockMode: boolean;
  readonly activeOrganisation: OrganisationMembershipView | null;
  refreshSession(): Promise<void>;
  setActiveOrganisation(organisationId: string | null): Promise<void>;
  switchAuthProfile(profileId: string): Promise<void>;
}

const AuthSessionContext = createContext<AuthSessionContextValue | null>(null);

function getActiveOrganisation(session: AuthSessionView | null): OrganisationMembershipView | null {
  if (!session?.active_organisation_id) return null;
  return session.org_memberships.find(
    (membership) => membership.organisation_id === session.active_organisation_id,
  ) ?? null;
}

interface AuthSessionProviderProps {
  readonly children: ReactNode;
}

export function AuthSessionProvider({ children }: AuthSessionProviderProps) {
  const data = useData();
  const [session, setSession] = useState<AuthSessionView | null>(null);
  const [authProfiles, setAuthProfiles] = useState<AuthProfileView[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadSession = useCallback(async () => {
    setLoading(true);
    try {
      const [nextSession, nextProfiles] = await Promise.all([
        data.getAuthSession(),
        data.listAuthProfiles(),
      ]);
      setSession(nextSession);
      setAuthProfiles(nextProfiles);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load session');
    } finally {
      setLoading(false);
    }
  }, [data]);

  useEffect(() => {
    void loadSession();
  }, [loadSession]);

  const refreshSession = useCallback(async () => {
    await loadSession();
  }, [loadSession]);

  const setActiveOrganisation = useCallback(async (organisationId: string | null) => {
    const nextSession = await data.setActiveOrganisation(organisationId);
    setSession(nextSession);
    setError(null);
  }, [data]);

  const switchAuthProfile = useCallback(async (profileId: string) => {
    const [nextSession, nextProfiles] = await Promise.all([
      data.switchAuthProfile(profileId),
      data.listAuthProfiles(),
    ]);
    setSession(nextSession);
    setAuthProfiles(nextProfiles);
    setError(null);
  }, [data]);

  const value = useMemo<AuthSessionContextValue>(() => ({
    session,
    authProfiles,
    loading,
    error,
    isAuthenticated: session?.status === 'authenticated',
    isAdmin: Boolean(session && session.capabilities.includes('admin:access')),
    isMockMode: session?.data_mode === 'mock',
    activeOrganisation: getActiveOrganisation(session),
    refreshSession,
    setActiveOrganisation,
    switchAuthProfile,
  }), [session, authProfiles, loading, error, refreshSession, setActiveOrganisation, switchAuthProfile]);

  return (
    <AuthSessionContext.Provider value={value}>
      {children}
    </AuthSessionContext.Provider>
  );
}

export function useAuthSession(): AuthSessionContextValue {
  const context = useContext(AuthSessionContext);
  if (!context) {
    throw new Error('useAuthSession must be used within AuthSessionProvider');
  }
  return context;
}

export function AuthBootstrapScreen() {
  return <LoadingState message="Loading your session..." />;
}
