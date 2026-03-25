import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import { DataProviderProvider } from './data';
import { MainLayout } from './components/layout/MainLayout';
import { Dashboard } from './pages/Dashboard';
import { Practice } from './pages/Practice';
import { Collections } from './pages/Collections';
import { Progress } from './pages/Progress';
import { Settings } from './pages/Settings';
import './index.css';

const router = createBrowserRouter([
  {
    path: '/',
    element: <MainLayout />,
    children: [
      { index: true, element: <Dashboard /> },
      { path: 'practice', element: <Practice /> },
      { path: 'collections', element: <Collections /> },
      { path: 'progress', element: <Progress /> },
      { path: 'settings', element: <Settings /> },
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
