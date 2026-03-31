import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useData } from '@/data';
import type { AttemptView, ScenarioView } from '@/data';
import { useSessionTimer } from '@/hooks/useSessionTimer';
import { LoadingState } from '@/design-system/patterns/LoadingState';
import { ErrorState } from '@/design-system/patterns/ErrorState';
import { SessionShell } from '@/features/session/SessionShell';
import { PromptDisplay } from '@/features/session/PromptDisplay';
import { ResponseInput } from '@/features/session/ResponseInput';
import { AssessingOverlay } from '@/features/session/AssessingOverlay';
import { PostSessionResults } from '@/features/session/PostSessionResults';
import { ContextPanel } from '@/features/session/ContextPanel';

type Phase = 'loading' | 'responding' | 'assessing' | 'complete' | 'error';

export function ScenarioSession() {
  const { scenarioId } = useParams<{ scenarioId: string }>();
  const navigate = useNavigate();
  const data = useData();
  const timer = useSessionTimer();
  const { pause, resume, reset } = timer;

  const [phase, setPhase] = useState<Phase>('loading');
  const [scenario, setScenario] = useState<ScenarioView | null>(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [attempts, setAttempts] = useState<AttemptView[]>([]);
  const [result, setResult] = useState<AttemptView | null>(null);
  const [error, setError] = useState('');

  const loadScenario = useCallback(() => {
    if (!scenarioId) { setError('No scenario ID provided'); setPhase('error'); return; }
    data.listCollections()
      .then(cols => {
        const found = cols.flatMap(c => c.scenarios).find(s => s.id === scenarioId);
        if (!found) {
          setError('Scenario not found');
          setPhase('error');
          return;
        }
        if (found.questions.length === 0) {
          setError('This scenario has no authored questions. Use the practice run flow instead.');
          setPhase('error');
          return;
        }
        setScenario(found);
        setCurrentQuestionIndex(0);
        setAttempts([]);
        setResult(null);
        setPhase('responding');
        reset();
      })
      .catch((e) => {
        setError(e.message);
        setPhase('error');
      });
  }, [scenarioId, data, reset]);

  useEffect(() => {
    loadScenario();
  }, [loadScenario]);

  async function handleSubmit(text: string) {
    if (!scenario) return;
    setPhase('assessing');
    pause();
    try {
      const sessionResponse = await data.startScenarioSession(scenarioId!);
      const attempt = await data.submitAttempt(sessionResponse.attempt_id, { response_text: text });
      const nextAttempts = [...attempts, attempt];
      setAttempts(nextAttempts);

      const nextIndex = currentQuestionIndex + 1;
      if (nextIndex >= scenario.questions.length) {
        setResult(attempt);
        setPhase('complete');
      } else {
        setCurrentQuestionIndex(nextIndex);
        setPhase('responding');
        resume();
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Submission failed');
      setPhase('error');
    }
  }

  const handleEnd = useCallback(() => {
    navigate('/practice');
  }, [navigate]);

  if (phase === 'loading') return <LoadingState message="Setting up the scenario..." />;
  if (phase === 'error') return <ErrorState message={error} onRetry={() => navigate('/practice')} />;
  if (!scenario) return <ErrorState message="Scenario not found" onRetry={() => navigate('/practice')} />;

  const questionCount = scenario.questions.length;
  const isLastQuestion = currentQuestionIndex >= questionCount - 1;
  const currentQuestion = scenario.questions[currentQuestionIndex];

  if (phase === 'complete' && result?.assessment) {
    const completedAttempts = attempts.length > 0 ? attempts : [result];
    const totalScore = completedAttempts.reduce((sum, a) => sum + (a.assessment?.overall_score ?? 0), 0);
    const avgScore = completedAttempts.length > 0 ? totalScore / completedAttempts.length : 0;

    const summaryAttempt: AttemptView = {
      attempt_id: result.attempt_id,
      session_id: result.session_id,
      status: 'completed',
      prompt: result.prompt,
      response_text: completedAttempts.map(a => a.response_text).join('\n\n'),
      assessment: {
        ...result.assessment,
        overall_score: avgScore,
        summary: `Completed ${questionCount} scenario questions.`,
      },
      submitted_at: result.submitted_at,
      assessed_at: result.assessed_at,
    };

    return (
      <SessionShell
        title={scenario.title}
        timer={timer.formatted}
        currentStep={questionCount}
        totalSteps={questionCount}
        stepLabel="Question"
        sidebar={<ContextPanel scenario={scenario} />}
        onEnd={handleEnd}
        wide
      >
        <PostSessionResults
          attempt={summaryAttempt}
          elapsedSeconds={timer.elapsed}
          onRetry={() => navigate(`/session/scenario/${scenarioId}`)}
        />
      </SessionShell>
    );
  }

  return (
    <SessionShell
      title={scenario.title}
      timer={timer.formatted}
      currentStep={currentQuestionIndex + 1}
      totalSteps={questionCount}
      stepLabel="Question"
      sidebar={<ContextPanel scenario={scenario} />}
      onEnd={handleEnd}
      wide
    >
      {(phase === 'responding' || phase === 'assessing') && (
        <>
          <PromptDisplay
            key={`prompt-${currentQuestionIndex}`}
            title={`Question ${currentQuestionIndex + 1} of ${questionCount}`}
            promptText={`Question: ${currentQuestion}`}
            difficulty="intermediate"
            skillSlugs={scenario.target_skill_slugs}
          />
          <ResponseInput
            key={`response-${currentQuestionIndex}`}
            onSubmit={handleSubmit}
            loading={phase === 'assessing'}
            minLength={10}
            submitLabel={isLastQuestion ? 'Complete Scenario' : 'Submit & Continue'}
            placeholder="How would you respond in this situation?"
          />
        </>
      )}

      {phase === 'assessing' && <AssessingOverlay message="Evaluating your response..." />}
    </SessionShell>
  );
}
