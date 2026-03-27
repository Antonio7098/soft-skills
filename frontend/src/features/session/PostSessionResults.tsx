import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Trophy,
  RotateCcw,
  ArrowRight,
  ClipboardList,
  ChevronDown,
  ChevronUp,
  Quote,
  ThumbsUp,
  AlertCircle,
  Lightbulb,
  Target,
  Clock,
  CheckCircle2,
  Sparkles,
  SkipForward,
  Zap,
  BookOpen,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { ScoreRing } from '@/design-system/patterns/ScoreRing';
import { Card } from '@/design-system/primitives/Card';
import { Badge } from '@/design-system/primitives/Badge';
import { Button } from '@/design-system/primitives/Button';
import { ProgressBar } from '@/design-system/primitives/ProgressBar';
import { useData } from '@/data';
import type { AttemptView, CompetencyView, PerSkillAssessment, RubricCriterionView } from '@/data';
import {
  getRubricType,
  isBinaryRubric,
  getLevelDescription,
  formatScore,
} from '@/data';
import { getScoreVariant, getDomainDifficultyVariant } from '@/lib/variant-helpers';

interface PostSessionResultsProps {
  readonly attempt: AttemptView;
  readonly elapsedSeconds?: number;
  readonly onRetry?: () => void;
  readonly onContinue?: () => void;
  readonly continueLabel?: string;
}

// ---------------------------------------------------------------------------
// Animation variants
// ---------------------------------------------------------------------------

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { duration: 0.4, staggerChildren: 0.1 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.25, 0.1, 0.25, 1] } },
};

const scaleIn = {
  hidden: { opacity: 0, scale: 0.8 },
  visible: { opacity: 1, scale: 1, transition: { duration: 0.5, ease: [0.34, 1.56, 0.64, 1] } },
};

// ---------------------------------------------------------------------------
// Rubric-aware helpers
// ---------------------------------------------------------------------------

function RubricTypeIndicator({ rubricId, rubricCriteria }: { rubricId: string; rubricCriteria: RubricCriterionView[] }) {
  const rubricType = getRubricType(rubricId);
  const binary = isBinaryRubric(rubricId, rubricCriteria);

  return (
    <div className="flex items-center gap-2">
      {rubricType === 'quick_practice' && (
        <Badge variant="accent" size="sm" className="gap-1">
          <Zap className="w-3 h-3" />
          Quick Practice
        </Badge>
      )}
      {rubricType === 'interview' && (
        <Badge variant="default" size="sm" className="gap-1">
          <BookOpen className="w-3 h-3" />
          Interview
        </Badge>
      )}
      {rubricType === 'scenario' && (
        <Badge variant="default" size="sm" className="gap-1">
          <Target className="w-3 h-3" />
          Scenario
        </Badge>
      )}
      {binary && (
        <Badge variant="warning" size="sm">
          Pass/Fail
        </Badge>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function HeroSection({
  score,
  title,
  difficulty,
  elapsedSeconds,
  rubricId,
  rubricCriteria,
}: {
  score: number;
  title: string;
  difficulty: string;
  elapsedSeconds?: number;
  rubricId: string;
  rubricCriteria: RubricCriterionView[];
}) {
  const formattedTime = elapsedSeconds
    ? `${String(Math.floor(elapsedSeconds / 60)).padStart(2, '0')}:${String(elapsedSeconds % 60).padStart(2, '0')}`
    : null;

  const rubricType = getRubricType(rubricId);
  const binary = isBinaryRubric(rubricId, rubricCriteria);
  const maxScore = binary ? 2 : 5;

  const scoreLabel = rubricType === 'quick_practice'
    ? (score >= 2 ? 'Passed' : 'Not Passed')
    : (score >= 4 ? 'Excellent' : score >= 3 ? 'Good' : 'Developing');

  const scoreMessage = rubricType === 'quick_practice'
    ? (score >= 2
        ? 'Great work! You demonstrated the target behaviors.'
        : 'Keep practicing! Focus on the areas identified below.')
    : (score >= 4
        ? 'Outstanding work! You demonstrated strong competency.'
        : score >= 3
          ? 'Solid performance with room to grow.'
          : 'Keep practicing — every attempt builds your skills.');

  return (
    <motion.div variants={itemVariants} className="flex flex-col items-center gap-6 text-center">
      <motion.div variants={scaleIn} className="relative">
        <div className="absolute -inset-4 rounded-full bg-accent/5 blur-xl" />
        <div className="relative">
          <ScoreRing score={score} maxScore={maxScore} size="lg" label={binary ? 'Result' : 'Overall Score'} />
        </div>
      </motion.div>

      <div className="flex flex-col items-center gap-2">
        <div className="flex items-center gap-2">
          <Trophy className="w-5 h-5 text-accent" />
          <h2 className="font-display text-display-md text-content-primary">Session Complete</h2>
        </div>
        <p className="text-body-md text-content-secondary max-w-md">{title}</p>
        <div className="flex items-center gap-2 mt-1">
          <Badge variant={getDomainDifficultyVariant(difficulty)} size="sm">
            {difficulty.charAt(0).toUpperCase() + difficulty.slice(1)}
          </Badge>
          <Badge variant={getScoreVariant(score)} size="sm">
            {scoreLabel} — {formatScore(rubricId, score, rubricCriteria)}
          </Badge>
          {formattedTime && (
            <Badge variant="default" size="sm">
              <Clock className="w-3 h-3 mr-1" />
              {formattedTime}
            </Badge>
          )}
        </div>
      </div>

      <Card padding="md" className="w-full max-w-lg bg-accent-muted/30 border-accent/10">
        <div className="flex items-start gap-3">
          <Sparkles className="w-5 h-5 text-accent shrink-0 mt-0.5" />
          <p className="text-body-sm text-content-primary leading-relaxed">{scoreMessage}</p>
        </div>
      </Card>
    </motion.div>
  );
}

function PerSkillResultCard({
  assessment,
  rubricId,
  rubricCriteria,
  index,
}: {
  assessment: PerSkillAssessment;
  rubricId: string;
  rubricCriteria: RubricCriterionView[];
  index: number;
}) {
  const [expanded, setExpanded] = useState(false);
  const binary = isBinaryRubric(rubricId, rubricCriteria);
  const maxScore = binary ? 2 : 5;
  const levelDescription = getLevelDescription(rubricId, assessment.skill_slug, assessment.score, rubricCriteria);
  const scoreLabel = formatScore(rubricId, assessment.score, rubricCriteria);

  return (
    <motion.div
      variants={itemVariants}
      initial="hidden"
      animate="visible"
      transition={{ delay: 0.1 + index * 0.08 }}
    >
      <Card variant="outlined" padding="md" className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Target className="w-4 h-4 text-accent" />
            <span className="text-body-sm font-medium text-content-primary">
              {assessment.skill_slug.replace(/-/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={getScoreVariant(assessment.score)} size="sm">
              {scoreLabel}
            </Badge>
            {binary && assessment.score >= 2 && (
              <CheckCircle2 className="w-4 h-4 text-status-success" />
            )}
            {binary && assessment.score < 2 && (
              <AlertCircle className="w-4 h-4 text-status-error" />
            )}
          </div>
        </div>

        <ProgressBar
          value={(assessment.score / maxScore) * 100}
          size="sm"
          variant={binary ? (assessment.score >= 2 ? 'success' : 'accent') : (assessment.score >= 4 ? 'success' : 'accent')}
        />

        <p className="text-body-xs text-content-secondary leading-relaxed">
          <span className="font-medium">Level {assessment.score}:</span> {levelDescription}
        </p>

        {assessment.rationale && (
          <p className="text-body-xs text-content-tertiary leading-relaxed italic">
            {assessment.rationale}
          </p>
        )}

        {assessment.evidence.length > 0 && (
          <button
            type="button"
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1 text-body-xs text-accent hover:text-accent/80 transition-colors"
          >
            {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            {expanded ? 'Hide' : 'Show'} evidence ({assessment.evidence.length})
          </button>
        )}

        <AnimatePresence>
          {expanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="overflow-hidden"
            >
              <div className="flex flex-col gap-2 pt-2 border-t border-line">
                {assessment.evidence.map((ev, i) => (
                  <div key={i} className="flex flex-col gap-1">
                    <p className="text-body-xs text-content-primary italic">"{ev.quote}"</p>
                    <p className="text-body-xs text-content-secondary">{ev.explanation}</p>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </Card>
    </motion.div>
  );
}

function SkillScoresSection({
  perSkillAssessments,
  rubricId,
  rubricCriteria,
}: {
  perSkillAssessments: readonly PerSkillAssessment[];
  rubricId: string;
  rubricCriteria: RubricCriterionView[];
}) {
  const rubricType = getRubricType(rubricId);

  return (
    <motion.div variants={itemVariants}>
      <Card padding="lg" className="flex flex-col gap-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Target className="w-4 h-4 text-accent" />
            <span className="text-body-xs font-semibold text-content-secondary uppercase tracking-wider">
              {rubricType === 'quick_practice' ? 'Skill Assessment' : 'Skill Breakdown'}
            </span>
          </div>
          <RubricTypeIndicator rubricId={rubricId} rubricCriteria={rubricCriteria} />
        </div>
        <div className="flex flex-col gap-4">
          {perSkillAssessments.map((ss, i) => (
            <PerSkillResultCard
              key={ss.skill_slug}
              assessment={ss}
              rubricId={rubricId}
              rubricCriteria={rubricCriteria}
              index={i}
            />
          ))}
        </div>
      </Card>
    </motion.div>
  );
}

function CompetencySection({
  perSkillAssessments,
  competencies,
  rubricId,
  rubricCriteria,
}: {
  perSkillAssessments: readonly PerSkillAssessment[];
  competencies: readonly CompetencyView[];
  rubricId: string;
  rubricCriteria: RubricCriterionView[];
}) {
  const skillScoreMap = new Map(perSkillAssessments.map((s) => [s.skill_slug, s.score]));
  const relevant = competencies.filter((c) =>
    c.skill_slugs.some((slug) => skillScoreMap.has(slug)),
  );

  if (relevant.length === 0) return null;

  const binary = isBinaryRubric(rubricId, rubricCriteria);

  return (
    <motion.div variants={itemVariants}>
      <Card padding="lg" className="flex flex-col gap-5">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-status-success" />
          <span className="text-body-xs font-semibold text-content-secondary uppercase tracking-wider">
            Competencies Exercised
          </span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {relevant.map((comp) => {
            const matchedSkills = comp.skill_slugs.filter((s) => skillScoreMap.has(s));
            const avgScore = matchedSkills.length > 0
              ? matchedSkills.reduce((sum, s) => sum + (skillScoreMap.get(s) ?? 0), 0) / matchedSkills.length
              : 0;

            return (
              <Card key={comp.slug} variant="outlined" padding="sm" className="flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <span className="text-body-sm font-semibold text-content-primary">{comp.name}</span>
                  <Badge variant={getScoreVariant(Math.round(avgScore))} size="sm">
                    {binary
                      ? (avgScore >= 2 ? 'Pass' : 'Fail')
                      : `${avgScore.toFixed(1)}/5`}
                  </Badge>
                </div>
                <p className="text-body-xs text-content-tertiary line-clamp-2">{comp.description}</p>
                <div className="flex flex-wrap gap-1">
                  {matchedSkills.map((slug) => (
                    <Badge key={slug} variant="accent" size="sm">
                      {slug.replace(/-/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())}
                    </Badge>
                  ))}
                </div>
              </Card>
            );
          })}
        </div>
      </Card>
    </motion.div>
  );
}

function EvidenceSection({ perSkillAssessments }: { perSkillAssessments: readonly PerSkillAssessment[] }) {
  const allEvidence = perSkillAssessments.flatMap((psa) =>
    psa.evidence.map((e) => ({ ...e, skill_slug: psa.skill_slug })),
  );

  if (allEvidence.length === 0) return null;

  return (
    <motion.div variants={itemVariants}>
      <Card padding="lg" className="flex flex-col gap-5">
        <div className="flex items-center gap-2">
          <Quote className="w-4 h-4 text-accent" />
          <span className="text-body-xs font-semibold text-content-secondary uppercase tracking-wider">
            Evidence from Your Response
          </span>
        </div>
        <div className="flex flex-col gap-3">
          {allEvidence.map((item, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 + i * 0.08 }}
            >
              <Card variant="outlined" padding="md" className="flex flex-col gap-3">
                <div className="flex items-start gap-3">
                  <div className="w-1 h-full min-h-[20px] rounded-full bg-accent shrink-0" />
                  <p className="text-body-sm text-content-primary italic leading-relaxed">
                    &ldquo;{item.quote}&rdquo;
                  </p>
                </div>
                <div className="flex items-start gap-3 pl-4">
                  <p className="text-body-xs text-content-secondary">{item.explanation}</p>
                </div>
                <div className="pl-4">
                  <Badge variant="accent" size="sm">
                    {item.skill_slug.replace(/-/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())}
                  </Badge>
                </div>
              </Card>
            </motion.div>
          ))}
        </div>
      </Card>
    </motion.div>
  );
}

function FeedbackGrid({
  strengths,
  weaknesses,
  nextActions,
}: {
  strengths: readonly string[];
  weaknesses: readonly string[];
  nextActions: readonly string[];
}) {
  return (
    <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {strengths.length > 0 && (
        <Card padding="md" className="flex flex-col gap-3">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-full bg-status-success/10 flex items-center justify-center">
              <ThumbsUp className="w-3.5 h-3.5 text-status-success" />
            </div>
            <span className="text-body-sm font-semibold text-status-success">Strengths</span>
          </div>
          <ul className="flex flex-col gap-2 pl-9">
            {strengths.map((item, i) => (
              <li key={i} className="text-body-sm text-content-primary leading-relaxed list-disc">
                {item}
              </li>
            ))}
          </ul>
        </Card>
      )}

      {weaknesses.length > 0 && (
        <Card padding="md" className="flex flex-col gap-3">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-full bg-status-warning/10 flex items-center justify-center">
              <AlertCircle className="w-3.5 h-3.5 text-status-warning" />
            </div>
            <span className="text-body-sm font-semibold text-status-warning">Areas to Improve</span>
          </div>
          <ul className="flex flex-col gap-2 pl-9">
            {weaknesses.map((item, i) => (
              <li key={i} className="text-body-sm text-content-primary leading-relaxed list-disc">
                {item}
              </li>
            ))}
          </ul>
        </Card>
      )}

      {nextActions.length > 0 && (
        <Card padding="md" className="flex flex-col gap-3">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-full bg-accent-muted flex items-center justify-center">
              <Lightbulb className="w-3.5 h-3.5 text-accent" />
            </div>
            <span className="text-body-sm font-semibold text-accent-text">Next Steps</span>
          </div>
          <ul className="flex flex-col gap-2 pl-9">
            {nextActions.map((item, i) => (
              <li key={i} className="text-body-sm text-content-primary leading-relaxed list-disc">
                {item}
              </li>
            ))}
          </ul>
        </Card>
      )}
    </motion.div>
  );
}

function ResponseCard({ responseText }: { responseText: string }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <motion.div variants={itemVariants}>
      <Card padding="md" className="flex flex-col gap-3">
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          className="flex items-center justify-between w-full text-left"
        >
          <span className="text-body-xs font-semibold text-content-secondary uppercase tracking-wider">
            Your Response
          </span>
          {expanded ? (
            <ChevronUp className="w-4 h-4 text-content-tertiary" />
          ) : (
            <ChevronDown className="w-4 h-4 text-content-tertiary" />
          )}
        </button>
        <AnimatePresence>
          {expanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.25 }}
              className="overflow-hidden"
            >
              <div className="pt-2 border-t border-line">
                <p className="text-body-sm text-content-primary leading-relaxed whitespace-pre-wrap">
                  {responseText}
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </Card>
    </motion.div>
  );
}

function ActionBar({ onRetry, onContinue, continueLabel }: { onRetry?: () => void; onContinue?: () => void; continueLabel?: string }) {
  const navigate = useNavigate();

  return (
    <motion.div variants={itemVariants} className="flex flex-wrap items-center justify-center gap-3 pt-4">
      {onRetry && (
        <Button variant="secondary" icon={<RotateCcw className="w-4 h-4" />} onClick={onRetry}>
          Try Again
        </Button>
      )}
      {onContinue && (
        <Button variant="secondary" icon={<SkipForward className="w-4 h-4" />} onClick={onContinue}>
          {continueLabel ?? 'Next Question'}
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
        onClick={() => navigate('/practice')}
      >
        Practice More
      </Button>
    </motion.div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function PostSessionResults({ attempt, elapsedSeconds, onRetry, onContinue, continueLabel }: PostSessionResultsProps) {
  const data = useData();
  const [competencies, setCompetencies] = useState<CompetencyView[]>([]);
  const [rubricCriteria, setRubricCriteria] = useState<import('@/data').RubricCriterionView[]>([]);

  useEffect(() => {
    data.getTaxonomy().then((t) => {
      setCompetencies(t.competencies);
      setRubricCriteria(t.rubric_criteria);
    });
  }, [data]);

  const assessment = attempt.assessment;
  if (!assessment) return null;

  const rubricId = assessment.rubric_id;

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="flex flex-col gap-8 py-8 max-w-2xl mx-auto w-full"
    >
      <HeroSection
        score={assessment.overall_score ?? 0}
        title={attempt.prompt.title}
        difficulty={attempt.prompt.difficulty}
        elapsedSeconds={elapsedSeconds}
        rubricId={rubricId}
        rubricCriteria={rubricCriteria}
      />

      {assessment.summary && (
        <motion.div variants={itemVariants}>
          <Card padding="md">
            <p className="text-body-md text-content-primary leading-relaxed">{assessment.summary}</p>
          </Card>
        </motion.div>
      )}

      <SkillScoresSection
        perSkillAssessments={assessment.per_skill_assessments}
        rubricId={rubricId}
        rubricCriteria={rubricCriteria}
      />

      <CompetencySection
        perSkillAssessments={assessment.per_skill_assessments}
        competencies={competencies}
        rubricId={rubricId}
        rubricCriteria={rubricCriteria}
      />

      <EvidenceSection perSkillAssessments={assessment.per_skill_assessments} />

      <FeedbackGrid
        strengths={assessment.strengths}
        weaknesses={assessment.weaknesses}
        nextActions={assessment.next_actions}
      />

      {attempt.response_text && <ResponseCard responseText={attempt.response_text} />}

      <ActionBar onRetry={onRetry} onContinue={onContinue} continueLabel={continueLabel} />
    </motion.div>
  );
}
