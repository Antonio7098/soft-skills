import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import { DataProviderProvider } from './data';
import { MainLayout } from './components/layout/MainLayout';
import { SessionLayout } from './components/layout/SessionLayout';
import { Dashboard } from './pages/Dashboard';
import { Practice } from './pages/Practice';
import { Collections } from './pages/Collections';
import { Progress } from './pages/Progress';
import { Settings } from './pages/Settings';
import { Assessment } from './pages/Assessment';
import { History } from './pages/History';
import { CollectionDetail } from './pages/CollectionDetail';
import { ScenarioDetail } from './pages/ScenarioDetail';
import { QuickPracticeSession } from './pages/session/QuickPracticeSession';
import { InterviewSession } from './pages/session/InterviewSession';
import { ScenarioSession } from './pages/session/ScenarioSession';
import { PracticeRunSession } from './pages/session/PracticeRunSession';
import './index.css';

const router = createBrowserRouter([
  {
    path: '/',
    element: <MainLayout />,
    children: [
      { index: true, element: <Dashboard /> },
      { path: 'practice', element: <Practice /> },
      { path: 'collections', element: <Collections /> },
      { path: 'collections/:collectionId', element: <CollectionDetail /> },
      { path: 'collections/:collectionId/scenario/:scenarioId', element: <ScenarioDetail /> },
      { path: 'progress', element: <Progress /> },
      { path: 'settings', element: <Settings /> },
      { path: 'assessment/:attemptId', element: <Assessment /> },
      { path: 'history', element: <History /> },
    ],
  },
  {
    path: '/session',
    element: <SessionLayout />,
    children: [
      { path: 'quick/:promptId', element: <QuickPracticeSession /> },
      { path: 'interview/:promptId', element: <InterviewSession /> },
      { path: 'scenario/:scenarioId', element: <ScenarioSession /> },
      { path: 'practice-run/:runId', element: <PracticeRunSession /> },
    ],
  },
]);

const root = document.getElementById('root');
if (root) {
  createRoot(root).render(
    <StrictMode>
      <ThemeProvider>
        <DataProviderProvider>
          <RouterProvider router={router} />
        </DataProviderProvider>
      </ThemeProvider>
    </StrictMode>,
  );
}
