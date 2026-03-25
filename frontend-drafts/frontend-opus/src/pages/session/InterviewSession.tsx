import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useData, buildMockAttemptView } from '@/data';
import type { InterviewSessionView, AttemptView } from '@/data';
import { useSessionTimer } from '@/hooks/useSessionTimer';
import { LoadingState } from '@/design-system/patterns/LoadingState';
import { ErrorState } from '@/design-system/patterns/ErrorState';
import { SessionShell } from '@/features/session/SessionShell';
import { PromptDisplay } from '@/features/session/PromptDisplay';
import { ResponseInput } from '@/features/session/ResponseInput';
import { AssessingOverlay } from '@/features/session/AssessingOverlay';
import { PostSessionResults } from '@/features/session/PostSessionResults';
import { TurnHistory } from '@/features/session/TurnHistory';

type Phase = 'loading' | 'responding' | 'submitting' | 'assessing' | 'complete' | 'error';

export function InterviewSession() {
  const { promptId } = useParams<{ promptId: string }>();
  const navigate = useNavigate();
  const data = useData();
  const timer = useSessionTimer();

  const [phase, setPhase] = useState<Phase>('loading');
  const [session, setSession] = useState<InterviewSessionView | null>(null);
  const [result, setResult] = useState<AttemptView | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!promptId) { setError('No prompt ID provided'); setPhase('error'); return; }
    data.startInterviewSession(promptId)
      .then((s) => { setSession(s); setPhase('responding'); })
      .catch((e) => { setError(e.message); setPhase('error'); });
  }, [promptId, data]);

  async function handleSubmit(text: string) {
    if (!session) return;
    setPhase('submitting');
    try {
      const updated = await data.submitInterviewTurn(session.session_id, { response_text: text });
      setSession(updated);
      if (updated.status === 'completed') {
        setPhase('assessing');
        timer.pause();
        const allResponses = updated.history.map((t) => t.response).join('\n\n');
        const mockResult = buildMockAttemptView({
          attemptId: updated.attempt_id,
          sessionId: updated.session_id,
          title: 'Interview Simulation',
          promptText: updated.history[0]?.question ?? updated.current_question,
          difficulty: updated.difficulty,
          skillSlugs: updated.target_skill_slugs,
          responseText: allResponses,
        });
        setResult(mockResult);
        setTimeout(() => setPhase('complete'), 1500);
      } else {
        setPhase('responding');
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Submission failed');
      setPhase('error');
    }
  }

  if (phase === 'loading') return <LoadingState message="Preparing your interview..." />;
  if (phase === 'error') return <ErrorState message={error} onRetry={() => navigate('/practice')} />;

  return (
    <SessionShell
      title="Interview Simulation"
      timer={timer.formatted}
      currentStep={session?.current_turn ?? 1}
      totalSteps={session?.total_turns ?? 3}
      stepLabel="Turn"
    >
      {(phase === 'responding' || phase === 'submitting') && session && (
        <>
          <TurnHistory turns={session.history} />
          <PromptDisplay
            promptText={session.current_question}
            context={session.competency_context}
            difficulty={session.difficulty}
            skillSlugs={session.target_skill_slugs}
          />
          <ResponseInput
            onSubmit={handleSubmit}
            loading={phase === 'submitting'}
            minLength={10}
            submitLabel={session.current_turn >= session.total_turns ? 'Submit Final Answer' : 'Submit Answer'}
            placeholder="Share your experience using the STAR method (Situation, Task, Action, Result)..."
          />
        </>
      )}

      {phase === 'assessing' && <AssessingOverlay message="Compiling your interview assessment..." />}

      {phase === 'complete' && result?.assessment && (
        <PostSessionResults
          attempt={result}
          elapsedSeconds={timer.elapsed}
          onRetry={() => navigate(`/session/interview/${promptId}`)}
        />
      )}
    </SessionShell>
  );
}
