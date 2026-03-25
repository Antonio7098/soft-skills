import { Building2, AlertTriangle, Target } from 'lucide-react';
import { Card } from '@/design-system/primitives/Card';
import { Badge } from '@/design-system/primitives/Badge';
import { SectionHeader } from '@/design-system/patterns/SectionHeader';
import { StakeholderCard } from './StakeholderCard';
import type { ScenarioView } from '@/data';

interface ContextPanelProps {
  readonly scenario: ScenarioView;
}

export function ContextPanel({ scenario }: ContextPanelProps) {
  return (
    <div className="flex flex-col gap-6">
      {scenario.mock_company && (
        <Card padding="md" className="flex flex-col gap-3">
          <div className="flex items-center gap-2 text-content-secondary">
            <Building2 className="w-4 h-4" />
            <span className="text-body-xs font-medium uppercase tracking-wider">Company</span>
          </div>
          <div className="flex flex-col gap-1">
            <h4 className="font-display text-display-sm text-content-primary">{scenario.mock_company.name}</h4>
            <Badge variant="default" size="sm">{scenario.mock_company.industry}</Badge>
          </div>
          <p className="text-body-sm text-content-secondary leading-relaxed">
            {scenario.mock_company.operating_context}
          </p>
        </Card>
      )}

      <div className="flex flex-col gap-3">
        <SectionHeader title="Objective" />
        <Card padding="md" className="flex items-start gap-3">
          <Target className="w-4 h-4 text-accent mt-0.5 shrink-0" />
          <p className="text-body-sm text-content-primary leading-relaxed">{scenario.learner_objective}</p>
        </Card>
      </div>

      {scenario.constraints.length > 0 && (
        <div className="flex flex-col gap-3">
          <SectionHeader title="Constraints" />
          <div className="flex flex-col gap-2">
            {scenario.constraints.map((c, i) => (
              <Card key={i} padding="sm" variant="outlined" className="flex items-start gap-2">
                <AlertTriangle className="w-3.5 h-3.5 text-status-warning mt-0.5 shrink-0" />
                <span className="text-body-sm text-content-primary">{c}</span>
              </Card>
            ))}
          </div>
        </div>
      )}

      {scenario.mock_people.length > 0 && (
        <div className="flex flex-col gap-3">
          <SectionHeader title="Stakeholders" />
          <div className="flex flex-col gap-3">
            {scenario.mock_people.map((person) => (
              <StakeholderCard key={person.id} person={person} />
            ))}
          </div>
        </div>
      )}

      {scenario.stakeholder_tensions.length > 0 && (
        <div className="flex flex-col gap-3">
          <SectionHeader title="Tensions" />
          <div className="flex flex-col gap-2">
            {scenario.stakeholder_tensions.map((t, i) => (
              <div key={i} className="flex items-start gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-status-error mt-2 shrink-0" />
                <span className="text-body-sm text-content-secondary">{t}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
