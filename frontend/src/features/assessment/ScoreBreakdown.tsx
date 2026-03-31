import { motion } from 'framer-motion';
import { ScoreRing } from '@/design-system/patterns/ScoreRing';
import { Card } from '@/design-system/primitives/Card';
import { ProgressBar } from '@/design-system/primitives/ProgressBar';
import { Badge } from '@/design-system/primitives/Badge';
import { getScoreVariant } from '@/lib/variant-helpers';
import type { PerSkillAssessment } from '@/data';

interface ScoreBreakdownProps {
  readonly overallScore: number;
  readonly maxScore?: number;
  readonly perSkillAssessments: readonly PerSkillAssessment[];
  readonly rationale?: string | null;
}

export function ScoreBreakdown({ overallScore, maxScore = 5, perSkillAssessments, rationale }: ScoreBreakdownProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="flex flex-col gap-6"
    >
      <div className="flex flex-col sm:flex-row items-center gap-8">
        <ScoreRing score={overallScore} maxScore={maxScore} size="lg" label="Overall Score" />
        {rationale && (
          <Card padding="md" className="flex-1">
            <p className="text-body-md text-content-primary leading-relaxed">{rationale}</p>
          </Card>
        )}
      </div>

      <Card padding="md" className="flex flex-col gap-4">
        <span className="text-body-xs font-medium text-content-secondary uppercase tracking-wider">
          Skill Scores
        </span>
        <div className="flex flex-col gap-3">
          {perSkillAssessments.map((ss, i) => (
            <motion.div
              key={ss.skill_slug}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.06 }}
              className="flex flex-col gap-1.5"
            >
              <div className="flex items-center justify-between">
                <span className="text-body-sm font-medium text-content-primary">
                  {ss.skill_slug.replace(/-/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())}
                </span>
                <Badge variant={getScoreVariant(ss.score)} size="sm">
                  {ss.score}/{maxScore}
                </Badge>
              </div>
              <ProgressBar value={(ss.score / maxScore) * 100} size="sm" variant={ss.score >= 4 ? 'success' : 'accent'} />
              {ss.rationale && (
                <p className="text-body-xs text-content-secondary">{ss.rationale}</p>
              )}
            </motion.div>
          ))}
        </div>
      </Card>
    </motion.div>
  );
}
