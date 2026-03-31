import { PageShell } from '@/design-system/patterns/PageShell';
import { ProgressDashboard } from '@/features/progress/ProgressDashboard';

export function Progress() {
  return (
    <PageShell
      title="Skill Progression"
      subtitle="Track your demonstrated performance across core competencies with detailed visualizations."
    >
      <ProgressDashboard />
    </PageShell>
  );
}
