import { Card, CardContent } from '@/ui/components/Card';
import { Badge } from '@/ui/components/Badge';
import { MessageSquare, Calendar, CheckCircle2, Clock, XCircle } from 'lucide-react';

export function Interviews() {
  const attempts = [
    {
      id: 1,
      title: 'Senior Consultant Behavioural',
      date: '2026-03-18',
      status: 'Assessed',
      score: 85,
      competencies: ['Leadership', 'Problem Solving'],
      duration: '45m'
    },
    {
      id: 2,
      title: 'Handling Difficult Clients',
      date: '2026-03-15',
      status: 'Assessed',
      score: 92,
      competencies: ['Communication', 'Stakeholder Management'],
      duration: '30m'
    },
    {
      id: 3,
      title: 'AI Project Delivery',
      date: '2026-03-10',
      status: 'Assessment Failed',
      score: null,
      competencies: ['Technical Communication'],
      duration: '25m'
    }
  ];

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-display font-bold tracking-tight">Interview Attempts</h1>
          <p className="text-muted-foreground mt-2">Review your past performance and AI assessments.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {attempts.map(attempt => (
          <Card key={attempt.id} className="hover:border-primary/50 transition-colors cursor-pointer">
            <CardContent className="p-6">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="flex items-start gap-4">
                  <div className="p-3 bg-secondary rounded-lg text-secondary-foreground">
                    <MessageSquare className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg">{attempt.title}</h3>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground mt-1">
                      <span className="flex items-center gap-1">
                        <Calendar className="w-4 h-4" /> {attempt.date}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-4 h-4" /> {attempt.duration}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-6">
                  <div className="flex flex-col items-end gap-2">
                    <div className="flex gap-2">
                      {attempt.competencies.map(comp => (
                        <Badge key={comp} variant="outline">{comp}</Badge>
                      ))}
                    </div>
                    {attempt.status === 'Assessed' ? (
                      <Badge variant="success" className="gap-1">
                        <CheckCircle2 className="w-3 h-3" /> {attempt.score}% Score
                      </Badge>
                    ) : (
                      <Badge variant="destructive" className="gap-1">
                        <XCircle className="w-3 h-3" /> Error in Assessment
                      </Badge>
                    )}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
