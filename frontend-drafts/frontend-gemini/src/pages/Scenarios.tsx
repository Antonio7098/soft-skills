import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/ui/components/Card';
import { Badge } from '@/ui/components/Badge';
import { Users, Building2, Briefcase } from 'lucide-react';

export function Scenarios() {
  const scenarios = [
    {
      id: 1,
      title: 'The Scope Creep Client',
      company: 'FinTech Solutions',
      role: 'Lead Consultant',
      description: 'The client is asking for three additional features that were not in the original SOW, but the deadline remains the same.',
      difficulty: 'Hard',
      competency: 'Stakeholder Management',
    },
    {
      id: 2,
      title: 'Failing Model Performance',
      company: 'HealthAI Corp',
      role: 'AI Engineer',
      description: 'The latest model iteration has regressed in performance on minority demographics. You need to explain this to the non-technical product owner.',
      difficulty: 'Medium',
      competency: 'Communication',
    },
    {
      id: 3,
      title: 'Misaligned Team Priorities',
      company: 'Internal Project',
      role: 'Project Manager',
      description: 'Two senior engineers are arguing over architectural decisions, threatening the sprint delivery.',
      difficulty: 'Medium',
      competency: 'Teamwork',
    }
  ];

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div>
        <h1 className="text-3xl font-display font-bold tracking-tight">Scenarios</h1>
        <p className="text-muted-foreground mt-2">Realistic workplace situations to test your judgement and skills.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {scenarios.map(scenario => (
          <Card key={scenario.id} className="hover:shadow-md transition-shadow cursor-pointer">
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-xl">{scenario.title}</CardTitle>
                  <CardDescription className="flex items-center gap-2 mt-2">
                    <Building2 className="w-4 h-4" /> {scenario.company}
                  </CardDescription>
                </div>
                <Badge variant={scenario.difficulty === 'Hard' ? 'destructive' : 'secondary'}>
                  {scenario.difficulty}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-2 text-sm font-medium text-foreground">
                <Briefcase className="w-4 h-4 text-muted-foreground" />
                Playing as: {scenario.role}
              </div>
              <p className="text-muted-foreground text-sm leading-relaxed">
                {scenario.description}
              </p>
              <div className="pt-4 flex items-center justify-between border-t border-border">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Users className="w-4 h-4" />
                  3 Mock People
                </div>
                <Badge variant="outline">{scenario.competency}</Badge>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
