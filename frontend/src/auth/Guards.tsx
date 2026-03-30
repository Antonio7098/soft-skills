import { Navigate } from 'react-router-dom';
import type { ReactNode } from 'react';
import { Card } from '@/design-system/primitives/Card';
import { Button } from '@/design-system/primitives/Button';
import { AuthBootstrapScreen, useAuthSession } from './AuthSessionContext';
import { AdminScopeProvider, useAdminScope } from './AdminScopeContext';

interface GuardProps {
  readonly children: ReactNode;
}

function AuthStateCard(props: {
  readonly title: string;
  readonly message: string;
  readonly actionLabel?: string;
  readonly onAction?: () => void;
}) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-primary px-6">
      <Card className="w-full max-w-lg flex flex-col gap-4">
        <h1 className="font-display text-display-xs text-content-primary">{props.title}</h1>
        <p className="text-body-sm text-content-secondary">{props.message}</p>
        {props.actionLabel && props.onAction && (
          <div>
            <Button onClick={props.onAction}>{props.actionLabel}</Button>
          </div>
        )}
      </Card>
    </div>
  );
}

export function UserAppGuard({ children }: GuardProps) {
  const { loading, error, isAuthenticated, refreshSession } = useAuthSession();

  if (loading) {
    return <AuthBootstrapScreen />;
  }
  if (error) {
    return <AuthStateCard title="Session Unavailable" message={error} actionLabel="Retry" onAction={() => void refreshSession()} />;
  }
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

function AdminScopeGuard({ children }: GuardProps) {
  const { session, refreshSession } = useAuthSession();
  const { routeOrganisationId, activeOrganisation, can } = useAdminScope();

  if (!session) {
    return <AuthBootstrapScreen />;
  }
  if (!session.capabilities.includes('admin:access')) {
    return <Navigate to="/" replace />;
  }
  if (routeOrganisationId && (!activeOrganisation || !can('org:read'))) {
    return (
      <AuthStateCard
        title="Organisation Access Denied"
        message={`You do not have access to organisation ${routeOrganisationId}.`}
        actionLabel="Refresh Session"
        onAction={() => void refreshSession()}
      />
    );
  }
  return <>{children}</>;
}

export function AdminGuard({ children }: GuardProps) {
  const { loading, error, session, refreshSession } = useAuthSession();

  if (loading) {
    return <AuthBootstrapScreen />;
  }
  if (error) {
    return <AuthStateCard title="Admin Session Unavailable" message={error} actionLabel="Retry" onAction={() => void refreshSession()} />;
  }
  if (!session?.capabilities.includes('admin:access')) {
    return <Navigate to="/" replace />;
  }

  return (
    <AdminScopeProvider>
      <AdminScopeGuard>{children}</AdminScopeGuard>
    </AdminScopeProvider>
  );
}
