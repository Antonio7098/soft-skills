import { PageShell } from '@/design-system/patterns/PageShell';
import { Card } from '@/design-system/primitives/Card';
import { Badge } from '@/design-system/primitives/Badge';
import { Button } from '@/design-system/primitives/Button';
import { Avatar } from '@/design-system/primitives/Avatar';
import { Clock, Users, Star, BookOpen, Filter, Search } from 'lucide-react';

const COLLECTIONS = [
  {
    id: 1,
    title: 'Consultancy Fundamentals',
    description: 'Core scenarios for building foundational consultancy skills',
    author: 'Sarah Chen',
    authorAvatar: null,
    items: 24,
    duration: '3h 20m',
    difficulty: 'Beginner',
    rating: 4.8,
    reviews: 156,
    tags: ['Communication', 'Stakeholder Management', 'Problem Solving'],
    verified: true,
    featured: true,
  },
  {
    id: 2,
    title: 'AI Delivery Under Pressure',
    description: 'High-stakes AI project scenarios with tight deadlines and difficult stakeholders',
    author: 'Marcus Rodriguez',
    authorAvatar: null,
    items: 18,
    duration: '2h 45m',
    difficulty: 'Advanced',
    rating: 4.9,
    reviews: 89,
    tags: ['AI Projects', 'Pressure Handling', 'Technical Leadership'],
    verified: true,
    featured: false,
  },
  {
    id: 3,
    title: 'Stakeholder Navigation',
    description: 'Master the art of managing complex stakeholder relationships and expectations',
    author: 'Dr. Emily Watson',
    authorAvatar: null,
    items: 32,
    duration: '4h 15m',
    difficulty: 'Intermediate',
    rating: 4.7,
    reviews: 203,
    tags: ['Stakeholder Management', 'Communication', 'Negotiation'],
    verified: true,
    featured: false,
  },
  {
    id: 4,
    title: 'Executive Communication',
    description: 'Practice delivering clear, impactful messages to senior leadership',
    author: 'James Park',
    authorAvatar: null,
    items: 15,
    duration: '2h 00m',
    difficulty: 'Intermediate',
    rating: 4.6,
    reviews: 127,
    tags: ['Executive Presence', 'Communication', 'Presentation Skills'],
    verified: false,
    featured: false,
  },
  {
    id: 5,
    title: 'Crisis Management Scenarios',
    description: 'Navigate high-pressure situations with confidence and clarity',
    author: 'Alex Thompson',
    authorAvatar: null,
    items: 21,
    duration: '3h 30m',
    difficulty: 'Advanced',
    rating: 4.8,
    reviews: 94,
    tags: ['Crisis Response', 'Pressure Handling', 'Decision Making'],
    verified: true,
    featured: false,
  },
  {
    id: 6,
    title: 'Client Relationship Building',
    description: 'Develop lasting client relationships through effective communication and trust',
    author: 'Nina Patel',
    authorAvatar: null,
    items: 28,
    duration: '3h 45m',
    difficulty: 'Beginner',
    rating: 4.5,
    reviews: 178,
    tags: ['Client Management', 'Trust Building', 'Communication'],
    verified: false,
    featured: false,
  },
];

function getDifficultyColor(difficulty: string) {
  switch (difficulty) {
    case 'Beginner':
      return 'status-success';
    case 'Intermediate':
      return 'status-warning';
    case 'Advanced':
      return 'status-error';
    default:
      return 'default';
  }
}

export function Collections() {
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
        {COLLECTIONS.filter((c) => c.featured).map((collection) => (
          <Card key={collection.id} variant="elevated" className="overflow-hidden">
            <div className="flex flex-col lg:flex-row gap-6">
              <div className="flex-1 flex flex-col gap-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex flex-col gap-2">
                    <div className="flex items-center gap-2">
                      <h3 className="font-display text-display-md text-content-primary">
                        {collection.title}
                      </h3>
                      {collection.verified && (
                        <Badge variant="accent" size="sm">
                          Verified
                        </Badge>
                      )}
                      <Badge variant="success" size="sm">
                        Featured
                      </Badge>
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
                    <Badge key={tag} variant="default" size="sm">
                      {tag}
                    </Badge>
                  ))}
                </div>

                <div className="flex items-center justify-between pt-2">
                  <div className="flex items-center gap-3">
                    <Avatar fallback={collection.author} size="sm" />
                    <div>
                      <p className="text-body-sm font-medium text-content-primary">
                        {collection.author}
                      </p>
                      <Badge variant={getDifficultyColor(collection.difficulty)} size="sm">
                        {collection.difficulty}
                      </Badge>
                    </div>
                  </div>
                  <Button>Start Collection</Button>
                </div>
              </div>
            </div>
          </Card>
        ))}

        <div className="flex flex-col gap-4">
          <h3 className="font-display text-display-xs text-content-primary">All Collections</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {COLLECTIONS.filter((c) => !c.featured).map((collection) => (
              <Card key={collection.id} interactive className="flex flex-col gap-4">
                <div className="flex flex-col gap-3">
                  <div className="flex items-start justify-between gap-2">
                    <h4 className="font-display text-display-sm text-content-primary line-clamp-2">
                      {collection.title}
                    </h4>
                    {collection.verified && (
                      <Badge variant="accent" size="sm">
                        Verified
                      </Badge>
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
                      <Badge key={tag} variant="default" size="sm">
                        {tag}
                      </Badge>
                    ))}
                    {collection.tags.length > 2 && (
                      <Badge variant="default" size="sm">
                        +{collection.tags.length - 2}
                      </Badge>
                    )}
                  </div>

                  <div className="flex items-center justify-between pt-1">
                    <div className="flex items-center gap-2">
                      <Avatar fallback={collection.author} size="sm" />
                      <Badge variant={getDifficultyColor(collection.difficulty)} size="sm">
                        {collection.difficulty}
                      </Badge>
                    </div>
                    <Button variant="secondary" size="sm">
                      Start
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </PageShell>
  );
}
