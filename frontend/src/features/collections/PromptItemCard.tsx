import { useNavigate } from 'react-router-dom';
import { Brain, Briefcase, Play } from 'lucide-react';
import { Card } from '@/design-system/primitives/Card';
import { Badge } from '@/design-system/primitives/Badge';
import { Button } from '@/design-system/primitives/Button';
import { getDomainDifficultyVariant } from '@/lib/variant-helpers';
import type { PromptItemView } from '@/data';
import { cn } from '@/lib/cn';

interface PromptItemCardProps {
  readonly item: PromptItemView;
}

const typeConfig = {
  quick_practice_prompt: {
    label: 'Quick Practice',
    icon: Brain,
    badgeVariant: 'success' as const,
    sessionPrefix: '/session/quick',
  },
  interview_prompt: {
    label: 'Interview',
    icon: Briefcase,
    badgeVariant: 'accent' as const,
    sessionPrefix: '/session/interview',
  },
  scenario_step: {
    label: 'Scenario Step',
    icon: Brain,
    badgeVariant: 'info' as const,
    sessionPrefix: '/session/quick',
  },
} as const;

export function PromptItemCard({ item }: PromptItemCardProps) {
  const navigate = useNavigate();
  const config = typeConfig[item.prompt_type];
  const Icon = config.icon;

  return (
    <Card interactive padding="md" className="flex items-start gap-4" onClick={() => navigate(`${config.sessionPrefix}/${item.id}`)}>
      <div className={cn(
        'w-10 h-10 rounded-xl flex items-center justify-center shrink-0',
        item.prompt_type === 'quick_practice_prompt' && 'bg-status-success/10 text-status-success',
        item.prompt_type === 'interview_prompt' && 'bg-accent-muted text-accent-text',
        item.prompt_type === 'scenario_step' && 'bg-status-info/10 text-status-info',
      )}>
        <Icon className="w-5 h-5" />
      </div>
      <div className="flex-1 min-w-0 flex flex-col gap-2">
        <div className="flex items-start justify-between gap-3">
          <h4 className="text-body-sm font-medium text-content-primary line-clamp-1">{item.title}</h4>
          <div className="flex items-center gap-2 shrink-0">
            <Badge variant={config.badgeVariant} size="sm">{config.label}</Badge>
            <Badge variant={getDomainDifficultyVariant(item.difficulty)} size="sm" className="capitalize">{item.difficulty}</Badge>
          </div>
        </div>
        <p className="text-body-xs text-content-secondary line-clamp-2 leading-relaxed">{item.prompt_text}</p>
        <div className="flex flex-wrap gap-1 pt-1">
          {item.target_skill_slugs.slice(0, 3).map((slug) => (
            <Badge key={slug} variant="default" size="sm">
              {slug.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
            </Badge>
          ))}
          {item.target_skill_slugs.length > 3 && (
            <Badge variant="default" size="sm">+{item.target_skill_slugs.length - 3}</Badge>
          )}
        </div>
      </div>
      <Button variant="ghost" size="sm" icon={<Play className="w-3.5 h-3.5" />} className="shrink-0 mt-1" onClick={(e) => { e.stopPropagation(); navigate(`${config.sessionPrefix}/${item.id}`); }}>
        Start
      </Button>
    </Card>
  );
}
