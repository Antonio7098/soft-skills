import { type JSX } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './theme';
import { useThemeStyles } from './hooks';
import { AppLayout } from './components/layout/AppLayout';
import {
  DashboardPage,
  PracticePage,
  CollectionsPage,
  ProgressPage,
  SettingsPage,
} from './pages';

function ThemeStyles(): null {
  useThemeStyles();
  return null;
}

function App(): JSX.Element {
  return (
    <ThemeProvider>
      <ThemeStyles />
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/practice" element={<PracticePage />} />
            <Route path="/collections" element={<CollectionsPage />} />
            <Route path="/progress" element={<ProgressPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
