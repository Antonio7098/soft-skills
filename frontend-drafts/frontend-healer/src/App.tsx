import { useState, type ReactNode } from 'react';
import { ThemeProvider } from './design-system';
import { AppShell } from './components/AppShell/AppShell';
import { Dashboard } from './features/dashboard/Dashboard';
import { Practice } from './features/practice/Practice';
import { Collections } from './features/content/Collections';
import { ProgressPage } from './features/progress/ProgressPage';
import { CreatePage } from './features/content/CreatePage';

function PageRouter({ currentPath }: { currentPath: string }): ReactNode {
  switch (currentPath) {
    case 'dashboard':
      return <Dashboard />;
    case 'practice':
      return <Practice />;
    case 'collections':
      return <Collections />;
    case 'progress':
      return <ProgressPage />;
    case 'create':
      return <CreatePage />;
    default:
      return <Dashboard />;
  }
}

function AppContent() {
  const [currentPath, setCurrentPath] = useState('dashboard');

  return (
    <AppShell currentPath={currentPath} onNavigate={setCurrentPath}>
      <PageRouter currentPath={currentPath} />
    </AppShell>
  );
}

function App() {
  return (
    <ThemeProvider defaultTheme="concrete">
      <AppContent />
    </ThemeProvider>
  );
}

export default App;
