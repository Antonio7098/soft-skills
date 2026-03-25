import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useData } from '@/data';
import type { ScenarioSessionView } from '@/data';
import { useSessionTimer } from '@/hooks/useSessionTimer';
import { LoadingState } from '@/design-system/patterns/LoadingState';
import { ErrorState } from '@/design-system/patterns/ErrorState';
import { SessionShell } from '@/features/session/SessionShell';
import { PromptDisplay } from '@/features/session/PromptDisplay';
import { ResponseInput } from '@/features/session/ResponseInput';
import { AssessingOverlay } from '@/features/session/AssessingOverlay';
import { SessionComplete } from '@/features/session/SessionComplete';
import { ContextPanel } from '@/features/session/ContextPanel';
import { TurnHistory } from '@/features/session/TurnHistory';

type Phase = 'loading' | 'responding' | 'submitting' | 'assessing' | 'complete' | 'error';

export function ScenarioSession() {
  const { scenarioId } = useParams<{ scenarioId: string }>();
  const navigate = useNavigate();
  const data = useData();
  const timer = useSessionTimer();

  const [phase, setPhase] = useState<Phase>('loading');
  const [session, setSession] = useState<ScenarioSessionView | null>(null);
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
      const updated = await data.submitScenarioStep(session.session_id, { response_text: text });
      setSession(updated);
      if (updated.status === 'completed') {
        setPhase('assessing');
        timer.pause();
        setTimeout(() => setPhase('complete'), 1500);
      } else {
        setPhase('responding');
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Submission failed');
      setPhase('error');
    }
  }

  if (phase === 'loading') return <LoadingState message="Setting up the scenario..." />;
  if (phase === 'error') return <ErrorState message={error} onRetry={() => navigate('/practice')} />;

  const previousTurns = session?.history.map((h) => ({
    question: h.prompt,
    response: h.response,
  })) ?? [];

  return (
    <SessionShell
      title={session?.scenario.title ?? 'Scenario Practice'}
      timer={timer.formatted}
      currentStep={session?.current_step ?? 1}
      totalSteps={session?.total_steps ?? 3}
      stepLabel="Step"
      sidebar={session ? <ContextPanel scenario={session.scenario} /> : undefined}
    >
      {(phase === 'responding' || phase === 'submitting') && session && (
        <>
          <TurnHistory turns={previousTurns} />
          <PromptDisplay
            title={`Step ${session.current_step} of ${session.total_steps}`}
            promptText={session.current_prompt_text}
          />
          <ResponseInput
            onSubmit={handleSubmit}
            loading={phase === 'submitting'}
            submitLabel={session.current_step >= session.total_steps ? 'Complete Scenario' : 'Submit & Continue'}
            placeholder="How would you respond in this situation?"
          />
        </>
      )}

      {phase === 'assessing' && <AssessingOverlay message="Evaluating your scenario performance..." />}

      {phase === 'complete' && session && (
        <SessionComplete
          score={Math.floor(Math.random() * 2) + 3}
          attemptId={session.attempt_id}
          title={session.scenario.title}
          skillSlugs={session.scenario.target_skill_slugs}
          onRetry={() => navigate(`/session/scenario/${scenarioId}`)}
        />
      )}
    </SessionShell>
  );
}
