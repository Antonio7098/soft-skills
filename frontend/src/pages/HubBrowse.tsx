import { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Globe, Building2, Bookmark, Star, BookOpen, Filter, ArrowLeft } from 'lucide-react';
import { PageShell } from '@/design-system/patterns/PageShell';
import { Card } from '@/design-system/primitives/Card';
import { Button } from '@/design-system/primitives/Button';
import { Badge } from '@/design-system/primitives/Badge';
import { Input } from '@/design-system/primitives/Input';
import { LoadingState } from '@/design-system/patterns/LoadingState';
import { useData } from '@/data';
import type { CollectionView, DiscoveryTier, Difficulty } from '@/data';
import { cn } from '@/lib/cn';

type SortOption = 'popularity' | 'rating' | 'recent' | 'name';

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

export function HubBrowse() {
  const { hubType } = useParams<{ hubType: string }>();
  const navigate = useNavigate();
  const data = useData();
  const [collections, setCollections] = useState<CollectionView[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState<SortOption>('popularity');
  const [difficultyFilter, setDifficultyFilter] = useState<Difficulty | 'all'>('all');
  const [skillFilter, setSkillFilter] = useState<string>('all');

  const handleSaveToggle = (id: string, saved: boolean) => {
    setCollections((prev) =>
      prev.map((c) =>
        c.id === id ? { ...c, saved_by_actor: saved, save_count: saved ? c.save_count + 1 : c.save_count - 1 } : c,
      ),
    );
  };

  const hubConfig = useMemo(() => {
    if (hubType === 'global') {
      return {
        tier: 'global_public' as DiscoveryTier,
        title: 'Global Hub',
        description: 'Public collections available to all users',
        icon: <Globe className="w-6 h-6" />,
      };
    }
    return {
      tier: 'org_public' as DiscoveryTier,
      title: 'Org Hub',
      description: 'Collections shared within your organization',
      icon: <Building2 className="w-6 h-6" />,
    };
  }, [hubType]);

  useEffect(() => {
    setLoading(true);
    data.listCollections({ discovery_tier: hubConfig.tier, include_private: false }).then((c) => {
      setCollections(c);
      setLoading(false);
    });
  }, [data, hubConfig.tier]);

  const allSkills = useMemo(() => {
    const skills = new Set<string>();
    collections.forEach((c) => c.target_skill_slugs.forEach((s) => skills.add(s)));
    return Array.from(skills).sort();
  }, [collections]);

  const filteredAndSorted = useMemo(() => {
    let result = [...collections];

    if (search) {
      const q = search.toLowerCase();
      result = result.filter(
        (c) =>
          c.title.toLowerCase().includes(q) ||
          c.summary.toLowerCase().includes(q) ||
          c.target_skill_slugs.some((s) => s.replace(/-/g, ' ').includes(q)),
      );
    }

    if (difficultyFilter !== 'all') {
      result = result.filter((c) => c.difficulty === difficultyFilter);
    }

    if (skillFilter !== 'all') {
      result = result.filter((c) => c.target_skill_slugs.includes(skillFilter));
    }

    const verified = result.filter((c) => c.verification_state === 'verified');
    const unverified = result.filter((c) => c.verification_state !== 'verified');
    result = [...verified, ...unverified];

    switch (sortBy) {
      case 'popularity':
        result.sort((a, b) => b.save_count - a.save_count);
        break;
      case 'rating':
        result.sort((a, b) => (b.avg_rating ?? 0) - (a.avg_rating ?? 0));
        break;
      case 'recent':
        result.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
        break;
      case 'name':
        result.sort((a, b) => a.title.localeCompare(b.title));
        break;
    }

    return result;
  }, [collections, search, difficultyFilter, skillFilter, sortBy]);

  return (
    <PageShell
      title={hubConfig.title}
      subtitle={hubConfig.description}
      actions={
        <Button variant="ghost" icon={<ArrowLeft className="w-4 h-4" />} onClick={() => navigate('/collections')}>
          Back to Collections
        </Button>
      }
    >
      <div className="flex flex-col gap-6">
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex-1 min-w-[200px]">
              <Input
                placeholder="Search collections..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                icon={<Filter className="w-4 h-4" />}
              />
            </div>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortOption)}
              className="h-10 px-3 rounded-input font-body text-body-md bg-surface-elevated text-content-primary border border-line focus:outline-none focus:ring-2 focus:ring-accent/30"
            >
              <option value="popularity">Most Popular</option>
              <option value="rating">Highest Rated</option>
              <option value="recent">Most Recent</option>
              <option value="name">Name A-Z</option>
            </select>
            <select
              value={difficultyFilter}
              onChange={(e) => setDifficultyFilter(e.target.value as Difficulty | 'all')}
              className="h-10 px-3 rounded-input font-body text-body-md bg-surface-elevated text-content-primary border border-line focus:outline-none focus:ring-2 focus:ring-accent/30"
            >
              <option value="all">All Difficulties</option>
              <option value="introductory">Introductory</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
            </select>
            <select
              value={skillFilter}
              onChange={(e) => setSkillFilter(e.target.value)}
              className="h-10 px-3 rounded-input font-body text-body-md bg-surface-elevated text-content-primary border border-line focus:outline-none focus:ring-2 focus:ring-accent/30"
            >
              <option value="all">All Skills</option>
              {allSkills.map((s) => (
                <option key={s} value={s}>{s.replace(/-/g, ' ')}</option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-2 text-body-xs text-content-tertiary">
            <span>{filteredAndSorted.length} collections</span>
            <span>·</span>
            <span>Verified shown first</span>
          </div>
        </div>

        {loading ? (
          <LoadingState message="Loading collections..." />
        ) : filteredAndSorted.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-content-tertiary">
            <BookOpen className="w-12 h-12 mb-4" />
            <p>No collections found</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredAndSorted.map((collection) => (
              <CollectionBrowseCard key={collection.id} collection={collection} onSaveToggle={handleSaveToggle} />
            ))}
          </div>
        )}
      </div>
    </PageShell>
  );
}