import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/ui/components/Card';
import { Badge } from '@/ui/components/Badge';
import { Briefcase } from 'lucide-react';

export function MockPeople() {
  const people = [
    {
      id: 1,
      name: 'Sarah Jenkins',
      role: 'Product Owner',
      company: 'HealthAI Corp',
      archetype: 'The Skeptic',
      description: 'Protective of her product vision. Values evidence over promises. Needs to be brought along on the journey.',
      communicationStyle: 'Direct, questioning, low tolerance for jargon',
      traits: ['Detail-oriented', 'Risk-averse', 'Stakeholder-focused']
    },
    {
      id: 2,
      name: 'David Chen',
      role: 'VP of Engineering',
      company: 'FinTech Solutions',
      archetype: 'The Architect',
      description: 'Deeply technical leader who wants to understand the implementation details before committing to a timeline.',
      communicationStyle: 'Technical, analytical, prefers async written updates',
      traits: ['System-thinker', 'Process-driven', 'Direct']
    },
    {
      id: 3,
      name: 'Elena Rodriguez',
      role: 'CMO',
      company: 'RetailPlus',
      archetype: 'The Visionary',
      description: 'Excited by new ideas but often underestimates the complexity of execution. Prone to changing scope.',
      communicationStyle: 'High-energy, fast-paced, visual thinker',
      traits: ['Creative', 'Impatient', 'Big-picture']
    }
  ];

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div>
        <h1 className="text-3xl font-display font-bold tracking-tight">Mock People</h1>
        <p className="text-muted-foreground mt-2">The cast of characters you'll interact with during scenarios.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {people.map(person => (
          <Card key={person.id} className="overflow-hidden">
            <div className="h-24 bg-gradient-to-r from-primary/20 to-accent/20" />
            <CardHeader className="-mt-12">
              <div className="w-20 h-20 rounded-full bg-background border-4 border-background flex items-center justify-center text-2xl font-bold text-primary shadow-sm mb-2">
                {person.name.split(' ').map(n => n[0]).join('')}
              </div>
              <CardTitle className="text-xl">{person.name}</CardTitle>
              <CardDescription className="flex items-center gap-2 mt-1 font-medium text-foreground">
                <Briefcase className="w-4 h-4 text-muted-foreground" />
                {person.role} at {person.company}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">Archetype</h4>
                <Badge variant="secondary">{person.archetype}</Badge>
              </div>
              
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">Profile</h4>
                <p className="text-sm text-foreground/80 leading-relaxed">{person.description}</p>
              </div>

              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">Communication Style</h4>
                <p className="text-sm italic text-foreground/70">"{person.communicationStyle}"</p>
              </div>

              <div className="pt-4 border-t border-border">
                <div className="flex flex-wrap gap-2">
                  {person.traits.map(trait => (
                    <Badge key={trait} variant="outline" className="bg-background/50">
                      {trait}
                    </Badge>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
