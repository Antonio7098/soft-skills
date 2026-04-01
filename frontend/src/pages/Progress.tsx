import { useState } from 'react';
import { FlaskConical } from 'lucide-react';
import { PageShell } from '@/design-system/patterns/PageShell';
import { Button } from '@/design-system/primitives/Button';
import { ProgressDashboard } from '@/features/progress/ProgressDashboard';
import { DataProviderProvider } from '@/data/DataContext';
import { mockDataProvider } from '@/data/mock-provider';

export function Progress() {
  const [useMockData, setUseMockData] = useState(false);

  const dashboard = <ProgressDashboard />;

  return (
    <PageShell
      title="Skill Progression"
      subtitle="Track your demonstrated performance across core competencies with detailed visualizations."
      actions={
        <Button
          variant={useMockData ? 'primary' : 'secondary'}
          size="sm"
          icon={<FlaskConical size={16} />}
          onClick={() => setUseMockData(prev => !prev)}
        >
          {useMockData ? 'Using Mock Data' : 'Use Mock Data'}
        </Button>
      }
    >
      {useMockData ? (
        <DataProviderProvider provider={mockDataProvider}>
          {dashboard}
        </DataProviderProvider>
      ) : (
        dashboard
      )}
    </PageShell>
  );
}
