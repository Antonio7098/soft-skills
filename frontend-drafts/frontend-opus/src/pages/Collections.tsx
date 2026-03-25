import { useState, useEffect } from 'react';
import { Filter, Search } from 'lucide-react';
import { PageShell } from '@/design-system/patterns/PageShell';
import { CollectionFeaturedCard } from '@/features/collections/CollectionFeaturedCard';
import { CollectionCard } from '@/features/collections/CollectionCard';
import { Button } from '@/design-system/primitives/Button';
import { LoadingState } from '@/design-system/patterns/LoadingState';
import { useData } from '@/data';
import type { CollectionView } from '@/data';

export function Collections() {
  const data = useData();
  const [collections, setCollections] = useState<CollectionView[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    data.listCollections().then((c) => {
      setCollections(c);
      setLoading(false);
    });
  }, [data]);

  if (loading) return <LoadingState message="Loading collections..." />;

  const featured = collections.filter((c) => c.verification_state === 'verified').slice(0, 1);
  const regular = collections.filter((c) => !featured.find((f) => f.id === c.id));

  return (
    <PageShell
      title="Collections"
      subtitle="Curated sets of scenarios and questions for specific roles and competencies."
      actions={
        <div className="flex items-center gap-3">
          <Button variant="ghost" icon={<Filter className="w-4 h-4" />}>
            Filter
          </Button>
          <Button icon={<Search className="w-4 h-4" />}>
            Search
          </Button>
        </div>
      }
    >
      <div className="flex flex-col gap-6">
        {featured.map((collection) => (
          <CollectionFeaturedCard
            key={collection.id}
            collection={toViewProps(collection)}
          />
        ))}

        <div className="flex flex-col gap-4">
          <h3 className="font-display text-display-xs text-content-primary">All Collections</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {regular.map((collection) => (
              <CollectionCard
                key={collection.id}
                collection={toViewProps(collection)}
              />
            ))}
          </div>
        </div>
      </div>
    </PageShell>
  );
}

// Adapter: maps backend CollectionView to the shape feature components expect
function toViewProps(c: CollectionView) {
  return {
    id: c.id,
    title: c.title,
    description: c.summary,
    author: c.author_user_id,
    authorAvatar: null,
    items: c.prompt_items.length + c.scenarios.length,
    duration: `${c.prompt_items.length * 10 + c.scenarios.length * 25}m`,
    difficulty: c.difficulty === 'introductory' ? 'Beginner' : c.difficulty === 'advanced' ? 'Advanced' : 'Intermediate',
    rating: 4.5 + Math.random() * 0.5,
    reviews: Math.floor(Math.random() * 200) + 50,
    tags: c.target_skill_slugs.map((s) => s.replace(/-/g, ' ').replace(/\b\w/g, (ch) => ch.toUpperCase())),
    verified: c.verification_state === 'verified',
    featured: false,
  };
}
