import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useData } from '@/data';
import type { CollectionView } from '@/data';
import { LoadingState } from '@/design-system/patterns/LoadingState';
import { ErrorState } from '@/design-system/patterns/ErrorState';
import { CollectionHeader } from '@/features/collections/CollectionHeader';
import { CollectionContentTabs } from '@/features/collections/CollectionContentTabs';

export function CollectionDetail() {
  const { collectionId } = useParams<{ collectionId: string }>();
  const navigate = useNavigate();
  const data = useData();

  const [collection, setCollection] = useState<CollectionView | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!collectionId) {
      setError('No collection ID provided');
      setLoading(false);
      return;
    }
    data.getCollection(collectionId)
      .then((c) => { setCollection(c); setLoading(false); })
      .catch((e) => { setError(e.message); setLoading(false); });
  }, [collectionId, data]);

  if (loading) return <LoadingState message="Loading collection..." />;
  if (error || !collection) return <ErrorState message={error || 'Collection not found'} onRetry={() => navigate('/collections')} />;

  function handleStartFirst() {
    if (!collection) return;
    if (collection.scenarios.length > 0) {
      navigate(`/session/scenario/${collection.scenarios[0]!.id}`);
    } else if (collection.prompt_items.length > 0) {
      const first = collection.prompt_items[0]!;
      const prefix = first.prompt_type === 'interview_prompt' ? '/session/interview' : '/session/quick';
      navigate(`${prefix}/${first.id}`);
    }
  }

  return (
    <div className="flex flex-col gap-8 max-w-5xl mx-auto">
      <CollectionHeader collection={collection} onStartFirst={handleStartFirst} />
      <CollectionContentTabs collection={collection} />
    </div>
  );
}
