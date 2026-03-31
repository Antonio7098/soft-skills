import { motion } from 'framer-motion';
import { User, Bot } from 'lucide-react';
import { Card } from '@/design-system/primitives/Card';
import { cn } from '@/lib/cn';

interface Turn {
  readonly question: string;
  readonly response: string;
}

interface TurnHistoryProps {
  readonly turns: readonly Turn[];
  readonly className?: string;
}

export function TurnHistory({ turns, className }: TurnHistoryProps) {
  if (!turns || turns.length === 0) return null;

  return (
    <div className={cn('flex flex-col gap-4', className)}>
      <span className="text-body-xs font-medium text-content-secondary uppercase tracking-wider">
        Previous Turns
      </span>
      <div className="flex flex-col gap-3">
        {turns.map((turn, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
          >
            <Card variant="outlined" padding="sm" className="flex flex-col gap-3">
              <div className="flex items-start gap-3">
                <div className="w-7 h-7 rounded-full bg-accent-muted flex items-center justify-center shrink-0 mt-0.5">
                  <Bot className="w-3.5 h-3.5 text-accent-text" />
                </div>
                <p className="text-body-sm text-content-primary leading-relaxed">{turn.question}</p>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-7 h-7 rounded-full bg-surface-secondary flex items-center justify-center shrink-0 mt-0.5">
                  <User className="w-3.5 h-3.5 text-content-secondary" />
                </div>
                <p className="text-body-sm text-content-secondary leading-relaxed">{turn.response}</p>
              </div>
            </Card>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
