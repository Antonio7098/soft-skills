import { motion } from 'framer-motion';
import { ArrowRight, RotateCcw, ClipboardList } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { ScoreRing } from '@/design-system/patterns/ScoreRing';
import { Button } from '@/design-system/primitives/Button';
import { Card } from '@/design-system/primitives/Card';
import { Badge } from '@/design-system/primitives/Badge';

interface SessionCompleteProps {
  readonly score: number;
  readonly maxScore?: number;
  readonly attemptId: string;
  readonly title: string;
  readonly skillSlugs?: readonly string[];
  readonly onRetry?: () => void;
}

export function SessionComplete({ score, maxScore = 5, attemptId, title, skillSlugs, onRetry }: SessionCompleteProps) {
  const navigate = useNavigate();

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4, ease: [0.25, 0.1, 0.25, 1] }}
      className="flex flex-col items-center gap-8 py-12"
    >
      <div className="flex flex-col items-center gap-3">
        <h2 className="font-display text-display-md text-content-primary">Session Complete</h2>
        <p className="text-body-md text-content-secondary">{title}</p>
      </div>

      <ScoreRing score={score} maxScore={maxScore} size="lg" label="Overall Score" />

      {skillSlugs && skillSlugs.length > 0 && (
        <Card padding="md" className="w-full max-w-sm">
          <div className="flex flex-col gap-2">
            <span className="text-body-xs font-medium text-content-secondary uppercase tracking-wider">Skills Assessed</span>
            <div className="flex flex-wrap gap-1.5">
              {skillSlugs.map((slug) => (
                <Badge key={slug} variant="accent" size="sm">
                  {slug.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                </Badge>
              ))}
            </div>
          </div>
        </Card>
      )}

      <div className="flex items-center gap-3">
        {onRetry && (
          <Button variant="secondary" icon={<RotateCcw className="w-4 h-4" />} onClick={onRetry}>
            Try Again
          </Button>
        )}
        <Button
          variant="secondary"
          icon={<ClipboardList className="w-4 h-4" />}
          onClick={() => navigate('/history')}
        >
          View History
        </Button>
        <Button
          variant="primary"
          icon={<ArrowRight className="w-4 h-4" />}
          iconPosition="right"
          onClick={() => navigate(`/assessment/${attemptId}`)}
        >
          View Full Feedback
        </Button>
      </div>
    </motion.div>
  );
}
