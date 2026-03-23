import { PageShell } from '@/design-system/patterns/PageShell';
import { Card } from '@/design-system/primitives/Card';
import { ProgressBar } from '@/design-system/primitives/ProgressBar';

export function Progress() {
  return (
    <PageShell
      title="Skill Progression"
      subtitle="Track your demonstrated performance across core competencies."
    >
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card title="Communication" className="flex flex-col gap-6">
          <div className="flex flex-col gap-2">
            <h3 className="font-display text-display-xs">Communication</h3>
            <p className="text-body-sm text-content-secondary">Level 3 • Competent</p>
          </div>
          <div className="flex flex-col gap-4">
            <ProgressBar value={85} label="Active Listening" showValue />
            <ProgressBar value={72} label="Concise Explanation" showValue />
            <ProgressBar value={60} label="Structured Communication" showValue />
          </div>
        </Card>
        
        <Card title="Stakeholder Management" className="flex flex-col gap-6">
          <div className="flex flex-col gap-2">
            <h3 className="font-display text-display-xs">Stakeholder Management</h3>
            <p className="text-body-sm text-content-secondary">Level 2 • Developing</p>
          </div>
          <div className="flex flex-col gap-4">
            <ProgressBar value={65} label="Empathy" showValue />
            <ProgressBar value={45} label="Expectation Setting" showValue />
            <ProgressBar value={30} label="Conflict Handling" showValue />
          </div>
        </Card>
      </div>
    </PageShell>
  );
}
