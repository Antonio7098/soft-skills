import { type JSX } from 'react';
import { Badge, type BadgeProps } from '../primitives';

type SkillLevel = 'beginner' | 'intermediate' | 'advanced' | 'expert';

interface SkillBadgeProps {
  name: string;
  level?: SkillLevel;
  variant?: BadgeProps['variant'];
}

const levelVariants: Record<SkillLevel, BadgeProps['variant']> = {
  beginner: 'default',
  intermediate: 'primary',
  advanced: 'warning',
  expert: 'success',
};

export function SkillBadge({
  name,
  level = 'beginner',
  variant,
}: SkillBadgeProps): JSX.Element {
  return (
    <Badge variant={variant ?? levelVariants[level]} size="sm">
      {name}
    </Badge>
  );
}
