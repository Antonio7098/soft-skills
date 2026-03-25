import { BookOpen, Clock, Star } from 'lucide-react';
import { Card } from '@/design-system/primitives/Card';
import { Badge } from '@/design-system/primitives/Badge';
import { Button } from '@/design-system/primitives/Button';
import { Avatar } from '@/design-system/primitives/Avatar';
import { getDifficultyVariant } from '@/lib/variant-helpers';
import type { Collection } from '@/types';

interface CollectionCardProps {
  readonly collection: Collection;
}

export function CollectionCard({ collection }: CollectionCardProps) {
  return (
    <Card interactive className="flex flex-col gap-4">
      <div className="flex flex-col gap-3">
        <div className="flex items-start justify-between gap-2">
          <h4 className="font-display text-display-sm text-content-primary line-clamp-2">
            {collection.title}
          </h4>
          {collection.verified && (
            <Badge variant="accent" size="sm">Verified</Badge>
          )}
        </div>

        <p className="text-body-sm text-content-secondary line-clamp-3">
          {collection.description}
        </p>

        <div className="flex items-center gap-3 text-body-xs text-content-tertiary">
          <div className="flex items-center gap-1">
            <BookOpen className="w-3.5 h-3.5" />
            <span>{collection.items}</span>
          </div>
          <div className="flex items-center gap-1">
            <Clock className="w-3.5 h-3.5" />
            <span>{collection.duration}</span>
          </div>
          <div className="flex items-center gap-1">
            <Star className="w-3.5 h-3.5 fill-current" />
            <span>{collection.rating}</span>
          </div>
        </div>

        <div className="flex flex-wrap gap-1">
          {collection.tags.slice(0, 2).map((tag) => (
            <Badge key={tag} variant="default" size="sm">{tag}</Badge>
          ))}
          {collection.tags.length > 2 && (
            <Badge variant="default" size="sm">+{collection.tags.length - 2}</Badge>
          )}
        </div>

        <div className="flex items-center justify-between pt-1">
          <div className="flex items-center gap-2">
            <Avatar fallback={collection.author} size="sm" />
            <Badge variant={getDifficultyVariant(collection.difficulty)} size="sm">
              {collection.difficulty}
            </Badge>
          </div>
          <Button variant="secondary" size="sm">Start</Button>
        </div>
      </div>
    </Card>
  );
}
