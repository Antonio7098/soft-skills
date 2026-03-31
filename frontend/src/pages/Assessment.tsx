import { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { RotateCcw, ArrowLeft, History, MessageSquare } from 'lucide-react';
import { useData } from '@/data';
import type { AttemptView } from '@/data';
import { PageShell } from '@/design-system/patterns/PageShell';
import { LoadingState } from '@/design-system/patterns/LoadingState';
import { ErrorState } from '@/design-system/patterns/ErrorState';
import { Button } from '@/design-system/primitives/Button';
import { Badge } from '@/design-system/primitives/Badge';
import { ScoreBreakdown } from '@/features/assessment/ScoreBreakdown';
import { EvidenceList } from '@/features/assessment/EvidenceList';
import { FeedbackSection } from '@/features/assessment/FeedbackSection';

export function Assessment() {
  const { attemptId } = useParams<{ attemptId: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const data = useData();

  const [attempt, setAttempt] = useState<AttemptView | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const questionIndex = searchParams.get('questionIndex');
  const selectedQuestionIndex = questionIndex !== null ? parseInt(questionIndex, 10) : null;

  useEffect(() => {
    if (!attemptId) { setError('No attempt ID'); setLoading(false); return; }
    data.getAttempt(attemptId)
      .then((a) => { setAttempt(a); setLoading(false); })
      .catch((e) => { setError(e.message); setLoading(false); });
  }, [attemptId, data]);

  if (loading) return <LoadingState message="Loading assessment..." />;
  if (error || !attempt) return <ErrorState message={error || 'Attempt not found'} onRetry={() => navigate('/history')} />;

  const assessment = attempt.assessment;
  if (!assessment) return <ErrorState message="No assessment data available for this attempt." onRetry={() => navigate('/history')} />;

  const perSkillAssessments = assessment.per_skill_assessments ?? [];

  const isSingleQuestion = selectedQuestionIndex !== null;
  const questionAssessment = isSingleQuestion 
    ? perSkillAssessments.filter((_, idx) => idx === selectedQuestionIndex)
    : perSkillAssessments;

  const pageTitle = isSingleQuestion 
    ? `Question ${selectedQuestionIndex + 1} Assessment` 
    : 'Assessment Results';

  return (
    <PageShell
      title={pageTitle}
      subtitle={attempt.prompt.title}
      actions={
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" icon={<ArrowLeft className="w-4 h-4" />} onClick={() => navigate(-1)}>
            Back
          </Button>
          <Button variant="secondary" size="sm" icon={<History className="w-4 h-4" />} onClick={() => navigate('/history')}>
            History
          </Button>
          {isSingleQuestion && (
            <Button variant="secondary" size="sm" icon={<MessageSquare className="w-4 h-4" />} onClick={() => navigate(`/assessment/${attemptId}`)}>
              Full Assessment
            </Button>
          )}
          <Button variant="primary" size="sm" icon={<RotateCcw className="w-4 h-4" />} onClick={() => navigate('/practice')}>
            Practice Again
          </Button>
        </div>
      }
    >
      {isSingleQuestion && (
        <div className="mb-4 p-4 bg-surface-secondary rounded-lg border border-line">
          <p className="text-body-md text-content-primary">{attempt.prompt.prompt_text}</p>
        </div>
      )}

      <ScoreBreakdown
        overallScore={assessment.overall_score ?? 0}
        perSkillAssessments={questionAssessment}
        rationale={isSingleQuestion ? undefined : assessment.summary}
      />

      {isSingleQuestion && assessment.strengths && assessment.strengths.length > 0 && (
        <div className="mb-4">
          <Badge variant="success" size="md">Strengths demonstrated in this response</Badge>
          <ul className="mt-2 flex flex-col gap-1">
            {assessment.strengths.map((s, i) => (
              <li key={i} className="text-body-sm text-content-secondary">• {s}</li>
            ))}
          </ul>
        </div>
      )}

      {isSingleQuestion && assessment.weaknesses && assessment.weaknesses.length > 0 && (
        <div className="mb-4">
          <Badge variant="warning" size="md">Areas to improve in this response</Badge>
          <ul className="mt-2 flex flex-col gap-1">
            {assessment.weaknesses.map((w, i) => (
              <li key={i} className="text-body-sm text-content-secondary">• {w}</li>
            ))}
          </ul>
        </div>
      )}

      {!isSingleQuestion && (
        <>
          <EvidenceList perSkillAssessments={perSkillAssessments} />
          <FeedbackSection
            strengths={assessment.strengths}
            weaknesses={assessment.weaknesses}
            nextActions={assessment.next_actions}
          />
        </>
      )}
    </PageShell>
  );
}
