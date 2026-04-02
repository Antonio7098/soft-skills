import { StrictMode, Suspense, lazy, type ComponentType, type ReactNode } from 'react';
import { createRoot } from 'react-dom/client';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import { AuthSessionProvider, AdminGuard, UserAppGuard } from './auth';
import { DataProviderProvider } from './data';
import { LoadingState } from './design-system/patterns/LoadingState';
import './index.css';

function lazyPage<TModule, TExport extends keyof TModule>(
  loader: () => Promise<TModule>,
  exportName: TExport,
) {
  return lazy(async () => {
    const module = await loader();
    return {
      default: module[exportName] as ComponentType<any>,
    };
  });
}

function withSuspense(element: ReactNode) {
  return (
    <Suspense fallback={<LoadingState message="Loading page..." />}>
      {element}
    </Suspense>
  );
}

const MainLayout = lazyPage(() => import('./components/layout/MainLayout'), 'MainLayout');
const SessionLayout = lazyPage(() => import('./components/layout/SessionLayout'), 'SessionLayout');
const Dashboard = lazyPage(() => import('./pages/Dashboard'), 'Dashboard');
const Practice = lazyPage(() => import('./pages/Practice'), 'Practice');
const Generate = lazyPage(() => import('./pages/Generate'), 'Generate');
const Collections = lazyPage(() => import('./pages/Collections'), 'Collections');
const HubBrowse = lazyPage(() => import('./pages/HubBrowse'), 'HubBrowse');
const Progress = lazyPage(() => import('./pages/Progress'), 'Progress');
const Settings = lazyPage(() => import('./pages/Settings'), 'Settings');
const Assessment = lazyPage(() => import('./pages/Assessment'), 'Assessment');
const History = lazyPage(() => import('./pages/History'), 'History');
const CollectionDetail = lazyPage(() => import('./pages/CollectionDetail'), 'CollectionDetail');
const ScenarioDetail = lazyPage(() => import('./pages/ScenarioDetail'), 'ScenarioDetail');
const Chat = lazyPage(() => import('./pages/Chat'), 'Chat');
const Login = lazyPage(() => import('./pages/Login'), 'Login');
const QuickPracticeSession = lazyPage(() => import('./pages/session/QuickPracticeSession'), 'QuickPracticeSession');
const InterviewSession = lazyPage(() => import('./pages/session/InterviewSession'), 'InterviewSession');
const ScenarioSession = lazyPage(() => import('./pages/session/ScenarioSession'), 'ScenarioSession');
const PracticeRunSession = lazyPage(() => import('./pages/session/PracticeRunSession'), 'PracticeRunSession');
const AdminLayout = lazyPage(() => import('./features/admin'), 'AdminLayout');
const AdminOverview = lazyPage(() => import('./features/admin'), 'AdminOverview');
const AdminUsers = lazyPage(() => import('./features/admin'), 'AdminUsers');
const AdminLearners = lazyPage(() => import('./features/admin'), 'AdminLearners');
const AdminCollections = lazyPage(() => import('./features/admin'), 'AdminCollections');
const AdminEvaluations = lazyPage(() => import('./features/admin'), 'AdminEvaluations');
const AdminPrompts = lazyPage(() => import('./features/admin'), 'AdminPrompts');
const AdminPipelines = lazyPage(() => import('./features/admin'), 'AdminPipelines');
const AdminRubrics = lazyPage(() => import('./features/admin'), 'AdminRubrics');
const AdminAudit = lazyPage(() => import('./features/admin'), 'AdminAudit');
const AdminTelemetry = lazyPage(() => import('./features/admin'), 'AdminTelemetry');
const AdminOrgSkills = lazyPage(() => import('./features/admin'), 'AdminOrgSkills');
const AdminOrgCompetencies = lazyPage(() => import('./features/admin'), 'AdminOrgCompetencies');
const AdminOrgRubrics = lazyPage(() => import('./features/admin'), 'AdminOrgRubrics');
const AdminOrgPromptItems = lazyPage(() => import('./features/admin'), 'AdminOrgPromptItems');
const AdminOrgScenarios = lazyPage(() => import('./features/admin'), 'AdminOrgScenarios');
const AdminRouteAliasRedirect = lazyPage(() => import('./features/admin'), 'AdminRouteAliasRedirect');

const router = createBrowserRouter([
  {
    path: '/login',
    element: withSuspense(<Login />),
  },
  {
    path: '/',
    element: <UserAppGuard>{withSuspense(<MainLayout />)}</UserAppGuard>,
    children: [
      { index: true, element: withSuspense(<Dashboard />) },
      { path: 'practice', element: withSuspense(<Practice />) },
      { path: 'generate', element: withSuspense(<Generate />) },
      { path: 'collections', element: withSuspense(<Collections />) },
      { path: 'collections/hub/:hubType', element: withSuspense(<HubBrowse />) },
      { path: 'collections/:collectionId', element: withSuspense(<CollectionDetail />) },
      { path: 'collections/:collectionId/scenario/:scenarioId', element: withSuspense(<ScenarioDetail />) },
      { path: 'progress', element: withSuspense(<Progress />) },
      { path: 'settings', element: withSuspense(<Settings />) },
      { path: 'assessment/:attemptId', element: withSuspense(<Assessment />) },
      { path: 'history', element: withSuspense(<History />) },
      { path: 'chat', element: withSuspense(<Chat />) },
      { path: 'chat/:sessionId', element: withSuspense(<Chat />) },
    ],
  },
  {
    path: '/session',
    element: <UserAppGuard>{withSuspense(<SessionLayout />)}</UserAppGuard>,
    children: [
      { path: 'quick/:promptId', element: withSuspense(<QuickPracticeSession />) },
      { path: 'interview/:promptId', element: withSuspense(<InterviewSession />) },
      { path: 'scenario/:scenarioId', element: withSuspense(<ScenarioSession />) },
      { path: 'practice-run/:runId', element: withSuspense(<PracticeRunSession />) },
    ],
  },
  {
    path: '/admin',
    element: <AdminGuard>{withSuspense(<AdminLayout />)}</AdminGuard>,
    children: [
      { index: true, element: withSuspense(<AdminOverview />) },
      { path: 'users', element: withSuspense(<AdminUsers />) },
      { path: 'learners', element: withSuspense(<AdminLearners />) },
      { path: 'collections', element: withSuspense(<AdminCollections />) },
      { path: 'evaluations', element: withSuspense(<AdminEvaluations />) },
      { path: 'prompts', element: withSuspense(<AdminPrompts />) },
      { path: 'pipelines', element: withSuspense(<AdminPipelines />) },
      { path: 'rubrics', element: withSuspense(<AdminRubrics />) },
      { path: 'audit', element: withSuspense(<AdminAudit />) },
      { path: 'telemetry', element: withSuspense(<AdminTelemetry />) },
      { path: 'skills', element: withSuspense(<AdminOrgSkills />) },
      { path: 'competencies', element: withSuspense(<AdminOrgCompetencies />) },
      { path: 'org-rubrics', element: withSuspense(<AdminOrgRubrics />) },
      { path: 'prompt-items', element: withSuspense(<AdminOrgPromptItems />) },
      { path: 'scenarios', element: withSuspense(<AdminOrgScenarios />) },
      { path: 'orgs/:organisationId/skills', element: withSuspense(<AdminRouteAliasRedirect to="/admin/skills" />) },
      { path: 'orgs/:organisationId/competencies', element: withSuspense(<AdminRouteAliasRedirect to="/admin/competencies" />) },
      { path: 'orgs/:organisationId/rubrics', element: withSuspense(<AdminRouteAliasRedirect to="/admin/org-rubrics" />) },
      { path: 'orgs/:organisationId/prompt-items', element: withSuspense(<AdminRouteAliasRedirect to="/admin/prompt-items" />) },
      { path: 'orgs/:organisationId/scenarios', element: withSuspense(<AdminRouteAliasRedirect to="/admin/scenarios" />) },
    ],
  },
]);

const root = document.getElementById('root');
if (root) {
  createRoot(root).render(
    <StrictMode>
      <ThemeProvider>
        <DataProviderProvider>
          <AuthSessionProvider>
            <RouterProvider router={router} future={{ v7_startTransition: true }} />
          </AuthSessionProvider>
        </DataProviderProvider>
      </ThemeProvider>
    </StrictMode>,
  );
}
