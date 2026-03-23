import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/ui/components/Card';
import { Badge } from '@/ui/components/Badge';
import { Layers, Star } from 'lucide-react';

export function Collections() {
  const collections = [
    {
      id: 1,
      title: 'Consultancy Fundamentals',
      description: 'Core skills for new consultants, focusing on stakeholder communication and basic problem solving.',
      skills: ['Active Listening', 'Structured Communication'],
      level: 'Beginner',
      verified: true,
    },
    {
      id: 2,
      title: 'AI Delivery Under Pressure',
      description: 'Scenarios dealing with AI project risks, misaligned expectations, and difficult client conversations.',
      skills: ['Expectation Setting', 'Conflict Handling', 'Negotiation'],
      level: 'Advanced',
      verified: true,
    },
    {
      id: 3,
      title: 'Behavioural Interview Prep',
      description: 'Common behavioural questions for senior tech roles and consulting positions.',
      skills: ['Executive Summary', 'Decision Justification'],
      level: 'Intermediate',
      verified: false,
    }
  ];

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-display font-bold tracking-tight">Collections</h1>
          <p className="text-muted-foreground mt-2">Curated practice paths to build specific competencies.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {collections.map(collection => (
          <Card key={collection.id} className="flex flex-col group hover:border-primary/50 transition-colors cursor-pointer">
            <CardHeader>
              <div className="flex justify-between items-start mb-2">
                <div className="p-2 bg-primary/10 rounded-lg text-primary">
                  <Layers className="w-5 h-5" />
                </div>
                {collection.verified && (
                  <Badge variant="secondary" className="gap-1 bg-yellow-500/10 text-yellow-700 hover:bg-yellow-500/20">
                    <Star className="w-3 h-3 fill-current" /> Verified
                  </Badge>
                )}
              </div>
              <CardTitle className="group-hover:text-primary transition-colors">{collection.title}</CardTitle>
              <CardDescription className="line-clamp-2">{collection.description}</CardDescription>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col justify-end gap-4">
              <div className="flex flex-wrap gap-2">
                {collection.skills.map(skill => (
                  <Badge key={skill} variant="outline" className="bg-background">
                    {skill}
                  </Badge>
                ))}
              </div>
              <div className="flex items-center justify-between text-sm text-muted-foreground border-t border-border pt-4 mt-2">
                <span>{collection.level}</span>
                <span>12 items</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
