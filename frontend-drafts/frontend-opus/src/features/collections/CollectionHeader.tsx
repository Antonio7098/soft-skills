import { useNavigate } from 'react-router-dom';
import { ArrowLeft, BookOpen, Clock, Users, Shield, Play } from 'lucide-react';
import { motion } from 'framer-motion';
import { Badge } from '@/design-system/primitives/Badge';
import { Button } from '@/design-system/primitives/Button';
import { Avatar } from '@/design-system/primitives/Avatar';
import { getDomainDifficultyVariant } from '@/lib/variant-helpers';
import type { CollectionView } from '@/data';

interface CollectionHeaderProps {
  readonly collection: CollectionView;
  readonly onStartFirst?: () => void;
}

export function CollectionHeader({ collection, onStartFirst }: CollectionHeaderProps) {
  const navigate = useNavigate();
  const totalItems = collection.prompt_items.length + collection.scenarios.length;
  const estimatedMinutes = collection.prompt_items.length * 10 + collection.scenarios.length * 25;

  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-6"
    >
      <button
        onClick={() => navigate('/collections')}
        className="flex items-center gap-1.5 text-body-sm text-content-secondary hover:text-content-primary transition-colors w-fit"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Collections
      </button>

      <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-6">
        <div className="flex flex-col gap-4 flex-1 min-w-0">
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="font-display text-display-lg text-content-primary">{collection.title}</h1>
            {collection.verification_state === 'verified' && (
              <Badge variant="accent" size="md">
                <span className="flex items-center gap-1"><Shield className="w-3 h-3" /> Verified</span>
              </Badge>
            )}
            <Badge variant={getDomainDifficultyVariant(collection.difficulty)} size="md" className="capitalize">
              {collection.difficulty}
            </Badge>
          </div>
          <p className="text-body-md text-content-secondary leading-relaxed max-w-2xl">{collection.summary}</p>

          <div className="flex flex-wrap items-center gap-5 text-body-sm text-content-tertiary">
            <div className="flex items-center gap-1.5">
              <BookOpen className="w-4 h-4" />
              <span>{totalItems} item{totalItems !== 1 ? 's' : ''}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Clock className="w-4 h-4" />
              <span>~{estimatedMinutes} min</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Users className="w-4 h-4" />
              <span>{collection.target_audience}</span>
            </div>
          </div>

          <div className="flex flex-wrap gap-1.5 pt-1">
            {collection.target_skill_slugs.map((slug) => (
              <Badge key={slug} variant="default" size="sm">
                {slug.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
              </Badge>
            ))}
          </div>

          <div className="flex items-center gap-3 pt-2">
            <Avatar fallback={collection.author_user_id} size="sm" />
            <span className="text-body-sm text-content-secondary">by <span className="font-medium text-content-primary">{collection.author_user_id}</span></span>
          </div>
        </div>

        <div className="shrink-0">
          <Button
            variant="primary"
            size="md"
            icon={<Play className="w-4 h-4" />}
            onClick={onStartFirst}
          >
            Start Collection
          </Button>
        </div>
      </div>
    </motion.div>
  );
}
