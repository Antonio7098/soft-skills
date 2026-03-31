import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { RotateCcw, ArrowLeft, History } from 'lucide-react';
import { useData } from '@/data';
import type { AttemptView } from '@/data';
import { PageShell } from '@/design-system/patterns/PageShell';
import { LoadingState } from '@/design-system/patterns/LoadingState';
import { ErrorState } from '@/design-system/patterns/ErrorState';
import { Button } from '@/design-system/primitives/Button';
import { ScoreBreakdown } from '@/features/assessment/ScoreBreakdown';
import { EvidenceList } from '@/features/assessment/EvidenceList';
import { FeedbackSection } from '@/features/assessment/FeedbackSection';

export function Assessment() {
  const { attemptId } = useParams<{ attemptId: string }>();
  const navigate = useNavigate();
  const data = useData();

  const [attempt, setAttempt] = useState<AttemptView | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

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

  return (
    <PageShell
      title="Assessment Results"
      subtitle={attempt.prompt.title}
      actions={
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" icon={<ArrowLeft className="w-4 h-4" />} onClick={() => navigate(-1)}>
            Back
          </Button>
          <Button variant="secondary" size="sm" icon={<History className="w-4 h-4" />} onClick={() => navigate('/history')}>
            History
          </Button>
          <Button variant="primary" size="sm" icon={<RotateCcw className="w-4 h-4" />} onClick={() => navigate('/practice')}>
            Practice Again
          </Button>
        </div>
      }
    >
      <ScoreBreakdown
        overallScore={assessment.overall_score ?? 0}
        perSkillAssessments={assessment.per_skill_assessments}
        rationale={assessment.summary}
      />

      <EvidenceList perSkillAssessments={assessment.per_skill_assessments} />

      <FeedbackSection
        strengths={assessment.strengths}
        weaknesses={assessment.weaknesses}
        nextActions={assessment.next_actions}
      />
    </PageShell>
  );
}
