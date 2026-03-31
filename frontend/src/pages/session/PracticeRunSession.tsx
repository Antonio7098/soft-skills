import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Trophy,
  RotateCcw,
  ArrowRight,
  CheckCircle2,
  SkipForward,
  Brain,
  Target,
} from 'lucide-react';
import { Card } from '@/design-system/primitives/Card';
import { Badge } from '@/design-system/primitives/Badge';
import { Button } from '@/design-system/primitives/Button';
import { LoadingState } from '@/design-system/patterns/LoadingState';
import { ErrorState } from '@/design-system/patterns/ErrorState';
import { SessionShell } from '@/features/session/SessionShell';
import { PromptDisplay } from '@/features/session/PromptDisplay';
import { ResponseInput } from '@/features/session/ResponseInput';
import { AssessingOverlay } from '@/features/session/AssessingOverlay';
import { ContextPanel } from '@/features/session/ContextPanel';
import { useData } from '@/data';
import { useSessionTimer } from '@/hooks/useSessionTimer';
import type {
  PracticeRunView,
  PracticeSessionView,
  AttemptView,
  ScenarioView,
} from '@/data';
import { getDomainDifficultyVariant } from '@/lib/variant-helpers';
import { cn } from '@/lib/cn';

type Phase = 'loading' | 'practicing' | 'assessing' | 'complete' | 'error';

function extractScenarioQuestion(promptText: string): string {
  const lines = promptText.split('\n').map(l => l.trim()).filter(Boolean);
  if (lines.length === 0) return promptText;
  const firstLine = lines[0]!;
  const lastLine = lines[lines.length - 1]!;
  if (firstLine !== lastLine) {
    return `${firstLine}\n\n${lastLine}`;
  }
  return lastLine;
}

function RunProgressSidebar({ run, currentIndex }: { run: PracticeRunView; currentIndex: number }) {
  return (
    <div className="flex flex-col gap-4">
      <div>
        <h4 className="font-display text-display-xs text-content-primary mb-2">Session Progress</h4>
        <p className="text-body-xs text-content-secondary">
          {currentIndex} of {run.items.length} completed
        </p>
      </div>
      <div className="flex flex-col gap-1.5">
        {run.items.map((item, idx) => (
          <div
            key={`${item.item_type}-${item.id}`}
            className={cn(
              'flex items-center gap-2 p-2 rounded-button transition-colors',
              idx < currentIndex
                ? 'bg-status-success/10'
                : idx === currentIndex
                  ? 'bg-accent/10'
                  : 'bg-surface-secondary',
            )}
          >
            <div className={cn(
              'w-6 h-6 rounded-full flex items-center justify-center text-xs shrink-0',
              idx < currentIndex
                ? 'bg-status-success/20 text-status-success'
                : idx === currentIndex
                  ? 'bg-accent/20 text-accent'
                  : 'bg-surface-secondary text-content-tertiary',
            )}>
              {idx < currentIndex ? (
                <CheckCircle2 className="w-3.5 h-3.5" />
              ) : item.item_type === 'prompt_item' ? (
                <Brain className="w-3.5 h-3.5" />
              ) : (
                <Target className="w-3.5 h-3.5" />
              )}
            </div>
            <span className={cn(
              'text-body-xs truncate',
              idx === currentIndex ? 'text-content-primary font-medium' : 'text-content-secondary',
            )}>
              {item.title}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function ItemResultCard({ attempt, onNext, isLast }: {
  attempt: AttemptView;
  onNext: () => void;
  isLast: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-4"
    >
      <Card variant="default" padding="lg" className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-status-success" />
            <span className="text-body-md font-medium text-content-primary">Response Submitted</span>
          </div>
          <Badge variant="success" size="sm">
            Score: {Math.round(attempt.assessment?.overall_score ?? 0)}%
          </Badge>
        </div>

        {attempt.assessment && (
          <>
            {attempt.assessment.strengths.length > 0 && (
              <div className="flex flex-col gap-2">
                <span className="text-body-xs font-semibold text-content-secondary uppercase tracking-wider">Strengths</span>
                <ul className="flex flex-col gap-1 pl-5">
                  {attempt.assessment.strengths.map((s, i) => (
                    <li key={i} className="text-body-sm text-content-primary list-disc">{s}</li>
                  ))}
                </ul>
              </div>
            )}

            {attempt.assessment.weaknesses.length > 0 && (
              <div className="flex flex-col gap-2">
                <span className="text-body-xs font-semibold text-content-secondary uppercase tracking-wider">Areas to Improve</span>
                <ul className="flex flex-col gap-1 pl-5">
                  {attempt.assessment.weaknesses.map((w, i) => (
                    <li key={i} className="text-body-sm text-content-primary list-disc">{w}</li>
                  ))}
                </ul>
              </div>
            )}
          </>
        )}

        <div className="flex items-center gap-3 pt-4 border-t border-line">
          {isLast ? (
            <Button variant="primary" icon={<Trophy className="w-4 h-4" />} onClick={onNext}>
              View Summary
            </Button>
          ) : (
            <Button variant="primary" icon={<ArrowRight className="w-4 h-4" />} iconPosition="right" onClick={onNext}>
              Next Question
            </Button>
          )}
          <Button variant="secondary" icon={<SkipForward className="w-4 h-4" />} onClick={onNext}>
            Skip
          </Button>
        </div>
      </Card>
    </motion.div>
  );
}

function RunResultsBreakdown({ run, attempts }: { run: PracticeRunView; attempts: AttemptView[] }) {
  const score = run.summary.overall_score;

  return (
    <motion.div
      variants={{
        hidden: { opacity: 0 },
        visible: { opacity: 1, transition: { duration: 0.4, staggerChildren: 0.1 } },
      }}
      initial="hidden"
      animate="visible"
      className="flex flex-col gap-6"
    >
      <motion.div
        variants={{
          hidden: { opacity: 0, y: 16 },
          visible: { opacity: 1, y: 0, transition: { duration: 0.4 } },
        }}
        className="flex flex-col items-center gap-4 text-center"
      >
        <div className="relative">
          <div className="absolute -inset-4 rounded-full bg-accent/5 blur-xl" />
          <div className="relative w-24 h-24 rounded-full bg-accent/10 flex items-center justify-center">
            <Trophy className="w-12 h-12 text-accent" />
          </div>
        </div>
        <div className="flex flex-col gap-1">
          <h2 className="font-display text-display-md text-content-primary">Session Complete</h2>
          <p className="text-body-md text-content-secondary">{run.title}</p>
        </div>
        {score !== null && (
          <Badge variant="success" size="md">
            Overall Score: {Math.round(score)}%
          </Badge>
        )}
      </motion.div>

      <Card variant="default" padding="lg" className="flex flex-col gap-4">
        <h3 className="text-body-sm font-semibold text-content-secondary uppercase tracking-wider">
          Per-Question Results
        </h3>
        <div className="flex flex-col gap-4">
          {run.items.map((item, idx) => {
            const attempt = attempts.find(a => a.prompt.title === item.title);
            const itemScore = attempt?.assessment?.overall_score;
            const rubricId = attempt?.assessment?.rubric_id ?? '';
            const binary = rubricId.includes('quick_practice');

            return (
              <Card key={`${item.item_type}-${item.id}`} variant="outlined" padding="md" className="flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className={cn(
                      'w-6 h-6 rounded-full flex items-center justify-center text-xs',
                      item.status === 'completed' ? 'bg-status-success/20 text-status-success' : 'bg-surface-secondary text-content-tertiary',
                    )}>
                      {item.status === 'completed' ? <CheckCircle2 className="w-3.5 h-3.5" /> : idx + 1}
                    </div>
                    <div className="flex flex-col">
                      <span className="text-body-sm font-medium text-content-primary">{item.title}</span>
                      <div className="flex items-center gap-2">
                        <Badge variant={getDomainDifficultyVariant(item.difficulty)} size="sm">
                          {item.difficulty}
                        </Badge>
                        <Badge variant="default" size="sm">
                          {item.item_type === 'prompt_item' ? 'Question' : 'Scenario'}
                        </Badge>
                        {binary && <Badge variant="warning" size="sm">Pass/Fail</Badge>}
                        {!binary && <Badge variant="accent" size="sm">1-5 Scale</Badge>}
                      </div>
                    </div>
                  </div>
                  {itemScore !== undefined && itemScore !== null && (
                    <Badge variant={itemScore >= (binary ? 2 : 4) ? 'success' : itemScore >= (binary ? 1 : 3) ? 'warning' : 'error'} size="md">
                      {binary
                        ? (itemScore >= 2 ? 'Pass' : 'Fail')
                        : `${Math.round(itemScore)}/5`}
                    </Badge>
                  )}
                </div>

                {attempt?.assessment && (
                  <div className="flex flex-col gap-2 pt-2 border-t border-line">
                    <div className="flex flex-wrap gap-1">
                      {attempt.assessment.per_skill_assessments.map(psa => (
                        <Badge key={psa.skill_slug} variant="accent" size="sm">
                          {psa.skill_slug.replace(/-/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())}: {binary ? (psa.score >= 2 ? 'Pass' : 'Fail') : `${psa.score}/5`}
                        </Badge>
                      ))}
                    </div>
                    {attempt.assessment.summary && (
                      <p className="text-body-xs text-content-secondary">{attempt.assessment.summary}</p>
                    )}
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      </Card>
    </motion.div>
  );
}

export function PracticeRunSession() {
  const { runId } = useParams<{ runId: string }>();
  const navigate = useNavigate();
  const data = useData();
  const timer = useSessionTimer();

  const [phase, setPhase] = useState<Phase>('loading');
  const [run, setRun] = useState<PracticeRunView | null>(null);
  const [sessions, setSessions] = useState<PracticeSessionView[]>([]);
  const [currentSessionIndex, setCurrentSessionIndex] = useState(0);
  const [currentAttempt, setCurrentAttempt] = useState<AttemptView | null>(null);
  const [allAttempts, setAllAttempts] = useState<AttemptView[]>([]);
  const [error, setError] = useState('');
  const [currentScenario, setCurrentScenario] = useState<ScenarioView | null>(null);

  const loadSession = useCallback(() => {
    if (!runId) {
      setError('No run ID provided');
      setPhase('error');
      return;
    }

    setPhase('loading');
    Promise.all([
      data.getPracticeRun(runId),
      data.getPracticeSessions(runId),
    ])
      .then(([r, sess]) => {
        setRun(r);
        setSessions(sess);
        setPhase(r.status === 'completed' ? 'complete' : 'practicing');
      })
      .catch((e) => {
        setError(e.message);
        setPhase('error');
      });
  }, [runId, data]);

  useEffect(() => {
    loadSession();
    timer.reset();
  }, [loadSession]);

  useEffect(() => {
    if (!run || sessions.length === 0) {
      setCurrentScenario(null);
      return;
    }

    const item = run.items[currentSessionIndex];
    if (!item || item.item_type !== 'scenario') {
      setCurrentScenario(null);
      return;
    }

    data.listCollections()
      .then(cols => {
        const scenario = cols.flatMap(c => c.scenarios).find(s => s.id === item.id);
        setCurrentScenario(scenario ?? null);
      });
  }, [run, sessions, currentSessionIndex, data]);

  async function handleSubmit(text: string) {
    const currentSession = sessions[currentSessionIndex];
    if (!run || !currentSession) {
      console.error('[PracticeRunSession] Submit blocked: run or session missing', { run: !!run, session: !!currentSession, sessionsLen: sessions.length });
      return;
    }

    setPhase('assessing');
    timer.pause();

    try {
      const attempt = await data.submitAttempt(currentSession.attempt_id, { response_text: text });
      setCurrentAttempt(attempt);
      setAllAttempts(prev => [...prev, attempt]);

      setSessions(prev => prev.map((s, idx) =>
        idx === currentSessionIndex
          ? { ...s, status: 'completed' as const, score: attempt.assessment?.overall_score ?? null, completed_at: new Date().toISOString() }
          : s
      ));

      setRun(prev => prev ? {
        ...prev,
        items: prev.items.map((item, idx) =>
          idx === currentSessionIndex ? { ...item, status: 'completed' as const } : item
        ),
      } : null);

      setPhase('complete');
    } catch (e) {
      console.error('[PracticeRunSession] Submit error:', e);
      setError(e instanceof Error ? e.message : 'Submission failed');
      setPhase('error');
    }
  }

  const handleNext = useCallback(() => {
    if (!run) return;

    const nextIndex = currentSessionIndex + 1;
    if (nextIndex >= sessions.length) {
      setRun(prev => prev ? { ...prev, status: 'completed' } : null);
      setPhase('complete');
    } else {
      setCurrentSessionIndex(nextIndex);
      setCurrentAttempt(null);
      setPhase('practicing');
      timer.resume();
    }
  }, [run, currentSessionIndex, sessions.length, timer]);

  const handleEnd = useCallback(() => {
    navigate('/practice');
  }, [navigate]);

  const handleRetry = useCallback(() => {
    setCurrentAttempt(null);
    setPhase('practicing');
    timer.reset();
  }, [timer]);

  if (phase === 'loading' || phase === 'practicing' && (!run || sessions.length === 0)) {
    return <LoadingState message="Loading your practice session..." />;
  }

  if (phase === 'error') {
    return <ErrorState message={error || 'Failed to load practice run'} onRetry={loadSession} />;
  }

  if (!run || sessions.length === 0) {
    return <ErrorState message="No sessions found" onRetry={loadSession} />;
  }

  const currentItem = run.items[currentSessionIndex];
  const isLastItem = currentSessionIndex >= sessions.length - 1;
  const isScenario = currentItem?.item_type === 'scenario' && currentScenario;

  const scenarioPromptText = isScenario
    ? extractScenarioQuestion(currentItem.prompt_text ?? '')
    : currentItem.prompt_text ?? '';

  if (phase === 'complete' && isLastItem) {
    return (
      <div className="min-h-screen bg-surface-primary flex items-center justify-center p-6">
        <div className="max-w-2xl w-full">
          <RunResultsBreakdown run={run} attempts={allAttempts} />
          <div className="flex items-center justify-center gap-3 mt-8">
            <Button variant="secondary" icon={<RotateCcw className="w-4 h-4" />} onClick={handleRetry}>
              Practice Again
            </Button>
            <Button variant="primary" icon={<ArrowRight className="w-4 h-4" />} iconPosition="right" onClick={() => navigate('/practice')}>
              Back to Practice
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <SessionShell
      title={run.title ?? ''}
      timer={timer.formatted}
      currentStep={currentSessionIndex + 1}
      totalSteps={sessions.length}
      stepLabel="Item"
      sidebar={<RunProgressSidebar run={run} currentIndex={currentSessionIndex} />}
      onEnd={handleEnd}
      wide={!!isScenario}
    >
      {phase === 'practicing' && currentItem && (
        <>
          {currentItem.item_type === 'scenario' && currentScenario ? (
            <div className="flex gap-6">
              <div className="w-80 shrink-0">
                <ContextPanel scenario={currentScenario} />
              </div>
              <div className="flex-1 flex justify-center">
                <div className="w-full max-w-2xl flex flex-col gap-6">
                  <PromptDisplay
                    title={currentItem.title}
                    promptText={scenarioPromptText ?? ''}
                    difficulty={currentItem.difficulty}
                    skillSlugs={currentItem.target_skill_slugs}
                  />
                  <ResponseInput
                    onSubmit={handleSubmit}
                    placeholder="Write your response here..."
                    submitLabel="Submit Response"
                    minLength={10}
                  />
                </div>
              </div>
            </div>
          ) : (
            <div className="flex flex-col gap-6">
              <PromptDisplay
                title={currentItem.title}
                promptText={currentItem.prompt_text ?? ''}
                difficulty={currentItem.difficulty}
                skillSlugs={currentItem.target_skill_slugs}
              />
              <ResponseInput
                onSubmit={handleSubmit}
                placeholder="Write your response here..."
                submitLabel="Submit Response"
                minLength={10}
              />
            </div>
          )}
        </>
      )}

      {phase === 'assessing' && <AssessingOverlay />}

      {phase === 'complete' && currentAttempt?.assessment && (
        <ItemResultCard
          attempt={currentAttempt}
          onNext={handleNext}
          isLast={isLastItem}
        />
      )}
    </SessionShell>
  );
}
