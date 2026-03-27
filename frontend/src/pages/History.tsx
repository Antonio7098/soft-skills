import { useState, useEffect, useMemo } from 'react';
import { FileText } from 'lucide-react';
import { useData } from '@/data';
import type { AttemptHistoryItem } from '@/data';
import { PageShell } from '@/design-system/patterns/PageShell';
import { LoadingState } from '@/design-system/patterns/LoadingState';
import { EmptyState } from '@/design-system/patterns/EmptyState';
import { AttemptListItem } from '@/features/history/AttemptListItem';
import { HistoryFilters } from '@/features/history/HistoryFilters';
import type { PracticeTypeFilter } from '@/features/history/HistoryFilters';

export function History() {
  const data = useData();
  const [attempts, setAttempts] = useState<AttemptHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [practiceType, setPracticeType] = useState<PracticeTypeFilter>('all');

  useEffect(() => {
    data.getAttemptHistory('current')
      .then((h) => { setAttempts(h); setLoading(false); })
      .catch(() => setLoading(false));
  }, [data]);

  const filtered = useMemo(() => {
    let result = attempts;
    if (practiceType !== 'all') {
      result = result.filter((a) => a.practice_type === practiceType);
    }
    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter((a) =>
        a.title.toLowerCase().includes(q) ||
        a.skill_slugs.some((s) => s.includes(q)),
      );
    }
    return result;
  }, [attempts, practiceType, search]);

  if (loading) return <LoadingState message="Loading attempt history..." />;

  return (
    <PageShell
      title="Attempt History"
      subtitle={`${attempts.length} total attempts across all practice modes.`}
    >
      <HistoryFilters
        search={search}
        onSearchChange={setSearch}
        practiceType={practiceType}
        onPracticeTypeChange={setPracticeType}
      />

      {filtered.length === 0 ? (
        <EmptyState
          icon={<FileText className="w-6 h-6" />}
          title="No attempts found"
          description={search || practiceType !== 'all'
            ? 'Try adjusting your filters to see more results.'
            : 'Complete a practice session to see your attempts here.'}
        />
      ) : (
        <div className="flex flex-col gap-3">
          {filtered.map((attempt) => (
            <AttemptListItem key={attempt.id} attempt={attempt} />
          ))}
        </div>
      )}
    </PageShell>
  );
}
