import { useNavigate } from 'react-router-dom';
import { Target, Building2, Users, ChevronRight } from 'lucide-react';
import { motion } from 'framer-motion';
import { Card } from '@/design-system/primitives/Card';
import { Badge } from '@/design-system/primitives/Badge';
import { Avatar } from '@/design-system/primitives/Avatar';
import { cn } from '@/lib/cn';
import type { ScenarioView } from '@/data';

interface ScenarioOverviewCardProps {
  readonly scenario: ScenarioView;
  readonly collectionId: string;
}

export function ScenarioOverviewCard({ scenario, collectionId }: ScenarioOverviewCardProps) {
  const navigate = useNavigate();

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
    >
      <Card
        interactive
        padding="lg"
        className="flex flex-col gap-4 group"
        onClick={() => navigate(`/collections/${collectionId}/scenario/${scenario.id}`)}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-xl bg-status-info/10 flex items-center justify-center shrink-0">
              <Target className="w-5 h-5 text-status-info" />
            </div>
            <div className="flex flex-col gap-1">
              <h4 className="font-display text-display-sm text-content-primary">{scenario.title}</h4>
              <p className="text-body-sm text-content-secondary leading-relaxed line-clamp-2">{scenario.business_context}</p>
            </div>
          </div>
          <ChevronRight className="w-5 h-5 text-content-tertiary group-hover:text-accent transition-colors shrink-0 mt-1" />
        </div>

        <div className="flex items-center gap-4 pl-[52px]">
          {scenario.mock_company && (
            <div className="flex items-center gap-1.5 text-body-xs text-content-tertiary">
              <Building2 className="w-3.5 h-3.5" />
              <span>{scenario.mock_company.name}</span>
            </div>
          )}
          {scenario.mock_people.length > 0 && (
            <div className="flex items-center gap-1.5 text-body-xs text-content-tertiary">
              <Users className="w-3.5 h-3.5" />
              <span>{scenario.mock_people.length} stakeholder{scenario.mock_people.length > 1 ? 's' : ''}</span>
            </div>
          )}
        </div>

        <div className="flex items-center justify-between pl-[52px]">
          <div className="flex items-center gap-2">
            {scenario.mock_people.length > 0 && (
              <div className="flex -space-x-2">
                {scenario.mock_people.slice(0, 3).map((p) => (
                  <Avatar key={p.id} fallback={p.name} size="sm" className="ring-2 ring-surface-primary" />
                ))}
              </div>
            )}
            <div className="flex flex-wrap gap-1">
              {scenario.target_skill_slugs.slice(0, 3).map((slug) => (
                <Badge key={slug} variant="default" size="sm">
                  {slug.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                </Badge>
              ))}
            </div>
          </div>
          <Badge variant="info" size="sm">
            {scenario.constraints.length} constraint{scenario.constraints.length !== 1 ? 's' : ''}
          </Badge>
        </div>
      </Card>
    </motion.div>
  );
}
