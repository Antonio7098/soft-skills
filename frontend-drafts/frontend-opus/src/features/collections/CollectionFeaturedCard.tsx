import { useNavigate } from 'react-router-dom';
import { BookOpen, Clock, Star, Users } from 'lucide-react';
import { Card } from '@/design-system/primitives/Card';
import { Badge } from '@/design-system/primitives/Badge';
import { Button } from '@/design-system/primitives/Button';
import { Avatar } from '@/design-system/primitives/Avatar';
import { getDifficultyVariant } from '@/lib/variant-helpers';
import type { Collection } from '@/types';

interface CollectionFeaturedCardProps {
  readonly collection: Collection;
}

export function CollectionFeaturedCard({ collection }: CollectionFeaturedCardProps) {
  const navigate = useNavigate();

  return (
    <Card variant="elevated" className="overflow-hidden">
      <div className="flex flex-col lg:flex-row gap-6">
        <div className="flex-1 flex flex-col gap-4">
          <div className="flex items-start justify-between gap-4">
            <div className="flex flex-col gap-2">
              <div className="flex items-center gap-2">
                <h3 className="font-display text-display-md text-content-primary">
                  {collection.title}
                </h3>
                {collection.verified && (
                  <Badge variant="accent" size="sm">Verified</Badge>
                )}
                <Badge variant="success" size="sm">Featured</Badge>
              </div>
              <p className="text-body-md text-content-secondary leading-relaxed">
                {collection.description}
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-4 text-body-sm text-content-tertiary">
            <div className="flex items-center gap-1">
              <BookOpen className="w-4 h-4" />
              <span>{collection.items} items</span>
            </div>
            <div className="flex items-center gap-1">
              <Clock className="w-4 h-4" />
              <span>{collection.duration}</span>
            </div>
            <div className="flex items-center gap-1">
              <Users className="w-4 h-4" />
              <span>{collection.reviews} reviews</span>
            </div>
            <div className="flex items-center gap-1">
              <Star className="w-4 h-4 fill-current" />
              <span>{collection.rating}</span>
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            {collection.tags.map((tag) => (
              <Badge key={tag} variant="default" size="sm">{tag}</Badge>
            ))}
          </div>

          <div className="flex items-center justify-between pt-2">
            <div className="flex items-center gap-3">
              <Avatar fallback={collection.author} size="sm" />
              <div>
                <p className="text-body-sm font-medium text-content-primary">{collection.author}</p>
                <Badge variant={getDifficultyVariant(collection.difficulty)} size="sm">
                  {collection.difficulty}
                </Badge>
              </div>
            </div>
            <Button onClick={() => navigate(`/collections/${collection.id}`)}>View Collection</Button>
          </div>
        </div>
      </div>
    </Card>
  );
}
