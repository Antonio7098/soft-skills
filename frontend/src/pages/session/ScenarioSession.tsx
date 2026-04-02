import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useData } from '@/data';
import type { ScenarioSessionView, AttemptView } from '@/data';
import { useSessionTimer } from '@/hooks/useSessionTimer';
import { LoadingState } from '@/design-system/patterns/LoadingState';
import { ErrorState } from '@/design-system/patterns/ErrorState';
import { SessionShell } from '@/features/session/SessionShell';
import { PromptDisplay } from '@/features/session/PromptDisplay';
import { ResponseInput } from '@/features/session/ResponseInput';
import { AssessingOverlay } from '@/features/session/AssessingOverlay';
import { PostSessionResults } from '@/features/session/PostSessionResults';
import { ContextPanel } from '@/features/session/ContextPanel';

type Phase = 'loading' | 'responding' | 'submitting' | 'assessing' | 'complete' | 'error';

export function ScenarioSession() {
  const { scenarioId } = useParams<{ scenarioId: string }>();
  const navigate = useNavigate();
  const data = useData();
  const timer = useSessionTimer();

  const [phase, setPhase] = useState<Phase>('loading');
  const [session, setSession] = useState<ScenarioSessionView | null>(null);
  const [result, setResult] = useState<AttemptView | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!scenarioId) { setError('No scenario ID provided'); setPhase('error'); return; }
    data.startScenarioSession(scenarioId)
      .then((s) => { setSession(s); setPhase('responding'); })
      .catch((e) => { setError(e.message); setPhase('error'); });
  }, [scenarioId, data]);

  async function handleSubmit(text: string) {
    if (!session) return;
    setPhase('submitting');
    try {
      const updatedSession = await data.submitScenarioStep(session.session_id, { response_text: text });
      if (updatedSession.status === 'completed') {
        setPhase('assessing');
        timer.pause();
        const attempt = await data.getAttempt(updatedSession.attempt_id);
        setSession(updatedSession);
        setResult(attempt);
        setTimeout(() => setPhase('complete'), 1500);
        return;
      }
      setSession(updatedSession);
      setPhase('responding');
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Submission failed');
      setPhase('error');
    }
  }

  if (phase === 'loading') return <LoadingState message="Setting up the scenario..." />;
  if (phase === 'error') return <ErrorState message={error} onRetry={() => navigate('/practice')} />;

  return (
    <SessionShell
      title={session?.scenario?.title ?? 'Scenario Practice'}
      timer={timer.formatted}
      currentStep={session?.current_step ?? 1}
      totalSteps={session?.total_steps ?? 1}
      stepLabel="Response"
      sidebar={session?.scenario ? <ContextPanel scenario={session.scenario} /> : undefined}
    >
      {(phase === 'responding' || phase === 'submitting') && session && (
        <>
          <PromptDisplay
            title={session.scenario?.title ?? 'Scenario Practice'}
            promptText={session.current_prompt_text}
            skillSlugs={session.scenario?.target_skill_slugs ?? []}
          />
          <ResponseInput
            onSubmit={handleSubmit}
            loading={phase === 'submitting'}
            minLength={10}
            submitLabel={session.current_step >= session.total_steps ? 'Submit Response' : 'Next Question'}
            placeholder="How would you respond in this situation?"
          />
        </>
      )}

      {phase === 'assessing' && <AssessingOverlay message="Evaluating your scenario performance..." />}

      {phase === 'complete' && result?.assessment && (
        <PostSessionResults
          attempt={result}
          elapsedSeconds={timer.elapsed}
          onRetry={() => navigate(`/session/scenario/${scenarioId}`)}
        />
      )}
    </SessionShell>
  );
}
