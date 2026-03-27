import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useData } from '@/data';
import type { QuickPracticeSessionView, AttemptView, CollectionView } from '@/data';
import { useSessionTimer } from '@/hooks/useSessionTimer';
import { LoadingState } from '@/design-system/patterns/LoadingState';
import { ErrorState } from '@/design-system/patterns/ErrorState';
import { SessionShell } from '@/features/session/SessionShell';
import { PromptDisplay } from '@/features/session/PromptDisplay';
import { ResponseInput } from '@/features/session/ResponseInput';
import { AssessingOverlay } from '@/features/session/AssessingOverlay';
import { PostSessionResults } from '@/features/session/PostSessionResults';

type Phase = 'loading' | 'responding' | 'assessing' | 'complete' | 'error';

export function QuickPracticeSession() {
  const { promptId } = useParams<{ promptId: string }>();
  const navigate = useNavigate();
  const data = useData();
  const timer = useSessionTimer();

  const [phase, setPhase] = useState<Phase>('loading');
  const [session, setSession] = useState<QuickPracticeSessionView | null>(null);
  const [result, setResult] = useState<AttemptView | null>(null);
  const [collections, setCollections] = useState<CollectionView[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!promptId) { setError('No prompt ID provided'); setPhase('error'); return; }
    Promise.all([
      data.startQuickPracticeSession({ prompt_item_id: promptId }),
      data.listCollections(),
    ])
      .then(([s, cols]) => { setSession(s); setCollections(cols); setPhase('responding'); })
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

  function handleContinue() {
    // Find another prompt from the same collection
    const allPrompts = collections.flatMap((c) => c.prompt_items);
    const currentIdx = allPrompts.findIndex((p) => p.id === promptId);
    const nextPrompt = allPrompts[currentIdx + 1] ?? allPrompts[0];
    if (nextPrompt && nextPrompt.id !== promptId) {
      navigate(`/session/quick/${nextPrompt.id}`, { replace: true });
      window.location.reload(); // Full reset for clean state
    } else {
      navigate('/practice');
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
          <ResponseInput onSubmit={handleSubmit} minLength={10} placeholder="Write your response... (min 10 characters)" />
        </>
      )}

      {phase === 'assessing' && <AssessingOverlay />}

      {phase === 'complete' && result?.assessment && (
        <PostSessionResults
          attempt={result}
          elapsedSeconds={timer.elapsed}
          onRetry={() => navigate(`/session/quick/${promptId}`)}
          onContinue={handleContinue}
          continueLabel="Next Question"
        />
      )}
    </SessionShell>
  );
}
