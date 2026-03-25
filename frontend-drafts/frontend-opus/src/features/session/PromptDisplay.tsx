import { motion } from 'framer-motion';
import { Card } from '@/design-system/primitives/Card';
import { Badge } from '@/design-system/primitives/Badge';
import { getDomainDifficultyVariant } from '@/lib/variant-helpers';
import { cn } from '@/lib/cn';

interface PromptDisplayProps {
  readonly title?: string;
  readonly promptText: string;
  readonly difficulty?: string;
  readonly skillSlugs?: readonly string[];
  readonly context?: string;
  readonly className?: string;
}

export function PromptDisplay({ title, promptText, difficulty, skillSlugs, context, className }: PromptDisplayProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
    >
      <Card variant="elevated" padding="lg" className={cn('flex flex-col gap-4', className)}>
        {(title || difficulty) && (
          <div className="flex items-start justify-between gap-3">
            {title && (
              <h3 className="font-display text-display-sm text-content-primary">{title}</h3>
            )}
            {difficulty && (
              <Badge variant={getDomainDifficultyVariant(difficulty)} size="sm" className="shrink-0 capitalize">
                {difficulty}
              </Badge>
            )}
          </div>
        )}

        {context && (
          <p className="text-body-sm text-content-secondary italic border-l-2 border-accent/30 pl-3">
            {context}
          </p>
        )}

        <p className="text-body-md text-content-primary leading-relaxed">{promptText}</p>

        {skillSlugs && skillSlugs.length > 0 && (
          <div className="flex flex-wrap gap-1.5 pt-2 border-t border-line">
            {skillSlugs.map((slug) => (
              <Badge key={slug} variant="default" size="sm">
                {slug.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
              </Badge>
            ))}
          </div>
        )}
      </Card>
    </motion.div>
  );
}
