import { motion } from 'framer-motion';
import { Quote } from 'lucide-react';
import { Card } from '@/design-system/primitives/Card';
import { Badge } from '@/design-system/primitives/Badge';
import type { EvidenceItem } from '@/data';

interface EvidenceListProps {
  readonly evidence: readonly EvidenceItem[];
}

export function EvidenceList({ evidence }: EvidenceListProps) {
  if (evidence.length === 0) return null;

  return (
    <div className="flex flex-col gap-4">
      <span className="text-body-xs font-medium text-content-secondary uppercase tracking-wider">
        Evidence from Your Response
      </span>
      <div className="flex flex-col gap-3">
        {evidence.map((item, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.06 }}
          >
            <Card variant="outlined" padding="md" className="flex flex-col gap-3">
              <div className="flex items-start gap-3">
                <Quote className="w-4 h-4 text-accent shrink-0 mt-0.5" />
                <p className="text-body-sm text-content-primary italic leading-relaxed">
                  "{item.quote}"
                </p>
              </div>
              <div className="flex items-start gap-3 pl-7">
                <p className="text-body-xs text-content-secondary">{item.explanation}</p>
              </div>
              <div className="pl-7">
                <Badge variant="accent" size="sm">
                  {item.skill_slug.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                </Badge>
              </div>
            </Card>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
