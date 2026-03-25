import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useData } from '@/data';
import type { QuickPracticeSessionView, AttemptView } from '@/data';
import { useSessionTimer } from '@/hooks/useSessionTimer';
import { LoadingState } from '@/design-system/patterns/LoadingState';
import { ErrorState } from '@/design-system/patterns/ErrorState';
import { SessionShell } from '@/features/session/SessionShell';
import { PromptDisplay } from '@/features/session/PromptDisplay';
import { ResponseInput } from '@/features/session/ResponseInput';
import { AssessingOverlay } from '@/features/session/AssessingOverlay';
import { SessionComplete } from '@/features/session/SessionComplete';

type Phase = 'loading' | 'responding' | 'assessing' | 'complete' | 'error';

export function QuickPracticeSession() {
  const { promptId } = useParams<{ promptId: string }>();
  const navigate = useNavigate();
  const data = useData();
  const timer = useSessionTimer();

  const [phase, setPhase] = useState<Phase>('loading');
  const [session, setSession] = useState<QuickPracticeSessionView | null>(null);
  const [result, setResult] = useState<AttemptView | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!promptId) { setError('No prompt ID provided'); setPhase('error'); return; }
    data.startQuickPracticeSession({ prompt_item_id: promptId })
      .then((s) => { setSession(s); setPhase('responding'); })
      .catch((e) => { setError(e.message); setPhase('error'); });
  }, [promptId, data]);

  async function handleSubmit(text: string) {
    if (!session) return;
    setPhase('assessing');
    timer.pause();
    try {
      const attempt = await data.submitAttempt(session.attempt_id, { response_text: text });
      setResult(attempt);
      setPhase('complete');
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Submission failed');
      setPhase('error');
    }
  }

  if (phase === 'loading') return <LoadingState message="Preparing your practice session..." />;
  if (phase === 'error') return <ErrorState message={error} onRetry={() => navigate('/practice')} />;

  return (
    <SessionShell
      title={session?.prompt.title ?? 'Quick Practice'}
      timer={timer.formatted}
      currentStep={1}
      totalSteps={1}
      stepLabel="Prompt"
    >
      {phase === 'responding' && session && (
        <>
          <PromptDisplay
            title={session.prompt.title}
            promptText={session.prompt.prompt_text}
            difficulty={session.prompt.difficulty}
            skillSlugs={session.prompt.target_skill_slugs}
          />
          <ResponseInput onSubmit={handleSubmit} placeholder="Write your response..." />
        </>
      )}

      {phase === 'assessing' && <AssessingOverlay />}

      {phase === 'complete' && result?.assessment && (
        <SessionComplete
          score={result.assessment.overall_score ?? 0}
          attemptId={result.id}
          title={session?.prompt.title ?? 'Quick Practice'}
          skillSlugs={session?.prompt.target_skill_slugs}
          onRetry={() => navigate(`/session/quick/${promptId}`)}
        />
      )}
    </SessionShell>
  );
}
