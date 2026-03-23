import React from 'react';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { ThemeProvider } from './providers/ThemeProvider';
import { AppLayout } from './ui/layouts/AppLayout';
import { Dashboard } from './pages/Dashboard';
import { Collections } from './pages/Collections';
import { Scenarios } from './pages/Scenarios';
import { MockPeople } from './pages/MockPeople';
import { Interviews } from './pages/Interviews';
import './index.css';

const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: <Dashboard />,
      },
      {
        path: 'collections',
        element: <Collections />,
      },
      {
        path: 'scenarios',
        element: <Scenarios />,
      },
      {
        path: 'people',
        element: <MockPeople />,
      },
      {
        path: 'interviews',
        element: <Interviews />,
      }
    ],
  },
]);

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ThemeProvider>
      <RouterProvider router={router} />
    </ThemeProvider>
  </StrictMode>
);
