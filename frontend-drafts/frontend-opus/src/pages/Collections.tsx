import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Globe, Building2, Bookmark, Clock, Star, BookOpen } from 'lucide-react';
import { PageShell } from '@/design-system/patterns/PageShell';
import { Card } from '@/design-system/primitives/Card';
import { Button } from '@/design-system/primitives/Button';
import { Badge } from '@/design-system/primitives/Badge';
import { LoadingState } from '@/design-system/patterns/LoadingState';
import { useData } from '@/data';
import type { CollectionView } from '@/data';
import { cn } from '@/lib/cn';

interface HubCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  collectionCount: number;
  onClick: () => void;
}

function HubCard({ icon, title, description, collectionCount, onClick }: HubCardProps) {
  return (
    <Card
      interactive
      variant="elevated"
      className="flex-1 min-w-[280px] cursor-pointer group"
      onClick={onClick}
    >
      <div className="flex flex-col gap-4">
        <div className="flex items-start justify-between">
          <div className="p-3 rounded-lg bg-accent/10 text-accent group-hover:bg-accent group-hover:text-white transition-colors">
            {icon}
          </div>
          <span className="text-body-xs text-content-tertiary font-medium">{collectionCount} collections</span>
        </div>
        <div className="flex flex-col gap-1">
          <h3 className="font-display text-display-sm text-content-primary">{title}</h3>
          <p className="text-body-sm text-content-secondary">{description}</p>
        </div>
        <Button variant="secondary" className="w-full mt-auto">Browse Hub</Button>
      </div>
    </Card>
  );
}

function CollectionBrowseCard({ collection, onSaveToggle }: { collection: CollectionView; onSaveToggle?: (id: string, saved: boolean) => void }) {
  return (
    <Card interactive className="flex flex-col gap-3" onClick={() => window.location.href = `/collections/${collection.id}`}>
      <div className="flex items-start justify-between gap-2">
        <h4 className="font-display text-display-sm text-content-primary line-clamp-2 flex-1">{collection.title}</h4>
        <div className="flex items-center gap-1.5 shrink-0">
          {collection.verification_state === 'verified' && (
            <Badge variant="accent" size="sm">Verified</Badge>
          )}
          <button
            onClick={(e) => {
              e.stopPropagation();
              onSaveToggle?.(collection.id, !collection.saved_by_actor);
            }}
            className={cn(
              'p-1.5 rounded-button transition-colors',
              collection.saved_by_actor
                ? 'text-accent hover:text-accent-hover'
                : 'text-content-tertiary hover:text-content-primary hover:bg-surface-secondary',
            )}
          >
            <Bookmark className={cn('w-4 h-4', collection.saved_by_actor && 'fill-current')} />
          </button>
        </div>
      </div>
      <p className="text-body-sm text-content-secondary line-clamp-2">{collection.summary}</p>

      <div className="flex flex-wrap gap-1">
        {collection.target_skill_slugs.slice(0, 2).map((s) => (
          <Badge key={s} variant="default" size="sm">{s.replace(/-/g, ' ')}</Badge>
        ))}
        {collection.target_skill_slugs.length > 2 && (
          <Badge variant="default" size="sm">+{collection.target_skill_slugs.length - 2}</Badge>
        )}
      </div>

      <div className="flex items-center gap-3 text-body-xs text-content-tertiary">
        <div className="flex items-center gap-1">
          <Bookmark className="w-3.5 h-3.5" />
          <span>{collection.save_count}</span>
        </div>
        {collection.avg_rating && (
          <div className="flex items-center gap-1">
            <Star className="w-3.5 h-3.5 fill-current" />
            <span>{collection.avg_rating.toFixed(1)}</span>
          </div>
        )}
        <div className="flex items-center gap-1">
          <BookOpen className="w-3.5 h-3.5" />
          <span>{collection.prompt_items.length + collection.scenarios.length}</span>
        </div>
        <Badge variant="default" size="sm" className="ml-auto capitalize">
          {collection.difficulty}
        </Badge>
      </div>
    </Card>
  );
}

interface CollectionRowProps {
  collection: CollectionView;
  onSaveToggle?: (id: string, saved: boolean) => void;
}

function CollectionRow({ collection, onSaveToggle }: CollectionRowProps) {
  return (
    <Card interactive className="flex items-center gap-4" onClick={() => window.location.href = `/collections/${collection.id}`}>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <h4 className="font-display text-display-sm text-content-primary truncate">{collection.title}</h4>
          {collection.verification_state === 'verified' && (
            <Badge variant="accent" size="sm">Verified</Badge>
          )}
          {collection.featured && (
            <Badge variant="success" size="sm">Featured</Badge>
          )}
        </div>
        <p className="text-body-sm text-content-secondary line-clamp-1">{collection.summary}</p>
        <div className="flex items-center gap-3 mt-2 text-body-xs text-content-tertiary">
          <div className="flex items-center gap-1">
            <Bookmark className="w-3.5 h-3.5" />
            <span>{collection.save_count}</span>
          </div>
          {collection.avg_rating && (
            <div className="flex items-center gap-1">
              <Star className="w-3.5 h-3.5 fill-current" />
              <span>{collection.avg_rating.toFixed(1)} ({collection.rating_count})</span>
            </div>
          )}
          <div className="flex items-center gap-1">
            <BookOpen className="w-3.5 h-3.5" />
            <span>{collection.prompt_items.length + collection.scenarios.length} items</span>
          </div>
          <Badge variant="default" size="sm" className="capitalize">{collection.difficulty}</Badge>
        </div>
      </div>
      <Button
        variant={collection.saved_by_actor ? 'primary' : 'secondary'}
        size="sm"
        icon={<Bookmark className={cn('w-4 h-4', collection.saved_by_actor && 'fill-current')} />}
        onClick={(e) => {
          e.stopPropagation();
          onSaveToggle?.(collection.id, !collection.saved_by_actor);
        }}
      >
        {collection.saved_by_actor ? 'Saved' : 'Save'}
      </Button>
    </Card>
  );
}

interface SectionHeaderProps {
  title: string;
  action?: { label: string; onClick: () => void };
}

function SectionHeader({ title, action }: SectionHeaderProps) {
  return (
    <div className="flex items-center justify-between">
      <h2 className="font-display text-display-xs text-content-primary">{title}</h2>
      {action && (
        <Button variant="ghost" size="sm" onClick={action.onClick}>
          {action.label}
        </Button>
      )}
    </div>
  );
}

export function Collections() {
  const navigate = useNavigate();
  const data = useData();
  const [collections, setCollections] = useState<CollectionView[]>([]);
  const [user, setUser] = useState<{ id: string; display_name: string } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      data.getMe(),
      data.listCollections({ include_private: true }),
    ]).then(([u, c]) => {
      setUser(u);
      setCollections(c);
      setLoading(false);
    });
  }, [data]);

  const globalCollections = useMemo(() => collections.filter((c) => c.discovery_tier === 'global_public'), [collections]);
  const orgCollections = useMemo(() => collections.filter((c) => c.discovery_tier === 'org_public'), [collections]);
  const myCollections = useMemo(() => collections.filter((c) => c.author_user_id === user?.id), [collections, user]);
  const savedCollections = useMemo(() => collections.filter((c) => c.saved_by_actor), [collections]);
  const featuredCollection = useMemo(() => myCollections.find((c) => c.featured) ?? globalCollections.find((c) => c.verification_state === 'verified'), [myCollections, globalCollections]);

  const handleSaveToggle = (id: string, saved: boolean) => {
    setCollections((prev) =>
      prev.map((c) =>
        c.id === id ? { ...c, saved_by_actor: saved, save_count: saved ? c.save_count + 1 : c.save_count - 1 } : c,
      ),
    );
  };

  if (loading) return <LoadingState message="Loading collections..." />;

  return (
    <PageShell
      title="Collections"
      subtitle="Curated sets of scenarios and questions for specific roles and competencies."
    >
      <div className="flex flex-col gap-8">
        <section className="flex flex-col gap-4">
          <SectionHeader title="Browse Collections" />
          <div className="flex gap-4 flex-wrap">
            <HubCard
              icon={<Globe className="w-6 h-6" />}
              title="Global Hub"
              description="Public collections available to all users"
              collectionCount={globalCollections.length}
              onClick={() => navigate('/collections/hub/global')}
            />
            <HubCard
              icon={<Building2 className="w-6 h-6" />}
              title="Org Hub"
              description="Collections shared within your organization"
              collectionCount={orgCollections.length}
              onClick={() => navigate('/collections/hub/org')}
            />
          </div>
        </section>

        {featuredCollection && (
          <section className="flex flex-col gap-4">
            <SectionHeader
              title="Featured Collection"
              action={{ label: 'View All', onClick: () => window.location.href = `/collections/${featuredCollection.id}` }}
            />
            <FeaturedCollectionCard collection={featuredCollection} onSaveToggle={handleSaveToggle} />
          </section>
        )}

        {savedCollections.length > 0 && (
          <section className="flex flex-col gap-4">
            <SectionHeader title="Your Collections" />
            <div className="flex flex-col gap-3">
              {savedCollections.slice(0, 3).map((c) => (
                <CollectionRow key={c.id} collection={c} onSaveToggle={handleSaveToggle} />
              ))}
            </div>
          </section>
        )}

        {myCollections.length > 0 && (
          <section className="flex flex-col gap-4">
            <SectionHeader
              title="Created by You"
              action={{ label: 'View All', onClick: () => {} }}
            />
            <div className="flex flex-col gap-3">
              {myCollections.slice(0, 3).map((c) => (
                <CollectionRow key={c.id} collection={c} onSaveToggle={handleSaveToggle} />
              ))}
            </div>
          </section>
        )}

        {globalCollections.length > 0 && (
          <section className="flex flex-col gap-4">
            <SectionHeader
              title="Popular in Global Hub"
              action={{ label: 'Browse All', onClick: () => navigate('/collections/hub/global') }}
            />
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {globalCollections.slice(0, 6).map((c) => (
                <CollectionBrowseCard key={c.id} collection={c} onSaveToggle={handleSaveToggle} />
              ))}
            </div>
          </section>
        )}
      </div>
    </PageShell>
  );
}

function FeaturedCollectionCard({ collection, onSaveToggle }: { collection: CollectionView; onSaveToggle?: (id: string, saved: boolean) => void }) {
  return (
    <Card variant="elevated" className="overflow-hidden">
      <div className="flex flex-col lg:flex-row gap-6">
        <div className="flex-1 flex flex-col gap-4">
          <div className="flex items-start justify-between gap-4">
            <div className="flex flex-col gap-2">
              <div className="flex items-center gap-2">
                <h3 className="font-display text-display-md text-content-primary">{collection.title}</h3>
                {collection.verification_state === 'verified' && (
                  <Badge variant="accent" size="sm">Verified</Badge>
                )}
                <Badge variant="success" size="sm">Featured</Badge>
              </div>
              <p className="text-body-md text-content-secondary leading-relaxed">{collection.summary}</p>
            </div>
            <button
              onClick={() => onSaveToggle?.(collection.id, !collection.saved_by_actor)}
              className={cn(
                'p-2 rounded-button transition-colors shrink-0',
                collection.saved_by_actor
                  ? 'text-accent hover:text-accent-hover'
                  : 'text-content-tertiary hover:text-content-primary hover:bg-surface-secondary',
              )}
            >
              <Bookmark className={cn('w-5 h-5', collection.saved_by_actor && 'fill-current')} />
            </button>
          </div>

          <div className="flex flex-wrap items-center gap-4 text-body-sm text-content-tertiary">
            <div className="flex items-center gap-1">
              <BookOpen className="w-4 h-4" />
              <span>{collection.prompt_items.length + collection.scenarios.length} items</span>
            </div>
            <div className="flex items-center gap-1">
              <Clock className="w-4 h-4" />
              <span>~{collection.prompt_items.length * 10 + collection.scenarios.length * 25} min</span>
            </div>
            {collection.avg_rating && (
              <div className="flex items-center gap-1">
                <Star className="w-4 h-4 fill-current" />
                <span>{collection.avg_rating.toFixed(1)} ({collection.rating_count})</span>
              </div>
            )}
            <div className="flex items-center gap-1">
              <Bookmark className="w-4 h-4" />
              <span>{collection.save_count} saves</span>
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            {collection.target_skill_slugs.map((s) => (
              <Badge key={s} variant="default" size="sm">{s.replace(/-/g, ' ')}</Badge>
            ))}
          </div>

          <div className="flex items-center justify-between pt-2">
            <Badge variant="default" size="sm" className="capitalize">{collection.difficulty}</Badge>
            <Button onClick={() => window.location.href = `/collections/${collection.id}`}>View Collection</Button>
          </div>
        </div>
      </div>
    </Card>
  );
}