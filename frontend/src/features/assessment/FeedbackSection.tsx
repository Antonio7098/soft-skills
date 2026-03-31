import { motion } from 'framer-motion';
import { ThumbsUp, AlertCircle, Lightbulb } from 'lucide-react';
import { Card } from '@/design-system/primitives/Card';
import { cn } from '@/lib/cn';

interface FeedbackSectionProps {
  readonly strengths: readonly string[];
  readonly weaknesses: readonly string[];
  readonly nextActions: readonly string[];
}

interface FeedbackBlockProps {
  readonly title: string;
  readonly icon: React.ReactNode;
  readonly items: readonly string[];
  readonly accentClass: string;
  readonly iconBgClass: string;
}

function FeedbackBlock({ title, icon, items, accentClass, iconBgClass }: FeedbackBlockProps) {
  if (items.length === 0) return null;

  return (
    <Card padding="md" className="flex flex-col gap-3">
      <div className="flex items-center gap-2">
        <div className={cn('w-7 h-7 rounded-full flex items-center justify-center', iconBgClass)}>
          {icon}
        </div>
        <span className={cn('text-body-sm font-semibold', accentClass)}>{title}</span>
      </div>
      <ul className="flex flex-col gap-2 pl-9">
        {items.map((item, i) => (
          <li key={i} className="text-body-sm text-content-primary leading-relaxed list-disc">
            {item}
          </li>
        ))}
      </ul>
    </Card>
  );
}

export function FeedbackSection({ strengths, weaknesses, nextActions }: FeedbackSectionProps) {
  if (!strengths || !weaknesses || !nextActions) return null;
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: 0.1 }}
      className="grid grid-cols-1 md:grid-cols-3 gap-4"
    >
      <FeedbackBlock
        title="Strengths"
        icon={<ThumbsUp className="w-3.5 h-3.5 text-status-success" />}
        items={strengths}
        accentClass="text-status-success"
        iconBgClass="bg-status-success/10"
      />
      <FeedbackBlock
        title="Areas to Improve"
        icon={<AlertCircle className="w-3.5 h-3.5 text-status-warning" />}
        items={weaknesses}
        accentClass="text-status-warning"
        iconBgClass="bg-status-warning/10"
      />
      <FeedbackBlock
        title="Suggested Next Steps"
        icon={<Lightbulb className="w-3.5 h-3.5 text-accent" />}
        items={nextActions}
        accentClass="text-accent-text"
        iconBgClass="bg-accent-muted"
      />
    </motion.div>
  );
}
