import { useState, useEffect } from 'react';
import { FileText } from 'lucide-react';
import { useData } from '@/data';
import type { PracticeRunView } from '@/data';
import { PageShell } from '@/design-system/patterns/PageShell';
import { LoadingState } from '@/design-system/patterns/LoadingState';
import { EmptyState } from '@/design-system/patterns/EmptyState';
import { PracticeRunListItem } from '@/features/history/PracticeRunListItem';

export function History() {
  const data = useData();
  const [runs, setRuns] = useState<PracticeRunView[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    data.listPracticeRuns()
      .then((r) => { setRuns(r); setLoading(false); })
      .catch(() => setLoading(false));
  }, [data]);

  if (loading) return <LoadingState message="Loading session history..." />;

  return (
    <PageShell
      title="Session History"
      subtitle={`${runs.length} practice sessions completed.`}
    >
      {runs.length === 0 ? (
        <EmptyState
          icon={<FileText className="w-6 h-6" />}
          title="No sessions found"
          description="Complete a practice session to see your history here."
        />
      ) : (
        <div className="flex flex-col gap-3">
          {runs.map((run) => (
            <PracticeRunListItem key={run.run_id} run={run} />
          ))}
        </div>
      )}
    </PageShell>
  );
}
