import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/ui/components/Card';
import { Badge } from '@/ui/components/Badge';
import { Button } from '@/ui/components/Button';
import { PlayCircle, Users, Clock } from 'lucide-react';

export function Dashboard() {
  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex flex-col gap-2">
        <h1 className="text-4xl font-display font-bold tracking-tight">Welcome back</h1>
        <p className="text-muted-foreground text-lg">Continue your competency growth journey.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="bg-primary/5 border-primary/20">
          <CardHeader>
            <CardTitle>Current Focus</CardTitle>
            <CardDescription>Stakeholder Management</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-display font-bold">Level 2</div>
            <p className="text-sm text-muted-foreground mt-2">Developing</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Practice Sessions</CardTitle>
            <CardDescription>This week</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-display font-bold">4</div>
            <p className="text-sm text-muted-foreground mt-2">+2 from last week</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Assessed Skills</CardTitle>
            <CardDescription>Total calibrated</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-display font-bold">12</div>
            <p className="text-sm text-muted-foreground mt-2">Across 3 competencies</p>
          </CardContent>
        </Card>
      </div>

      <div className="space-y-4">
        <h2 className="text-2xl font-display font-bold">Recommended Next Steps</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="flex flex-col">
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle>Managing Difficult Deadlines</CardTitle>
                  <CardDescription className="mt-1">Scenario Practice</CardDescription>
                </div>
                <Badge>High Priority</Badge>
              </div>
            </CardHeader>
            <CardContent className="flex-1">
              <p className="text-sm text-muted-foreground">
                Practice setting expectations when a key project milestone is at risk due to external dependencies.
              </p>
              <div className="flex gap-4 mt-4 text-sm text-muted-foreground">
                <div className="flex items-center gap-1">
                  <Clock className="w-4 h-4" /> 15 mins
                </div>
                <div className="flex items-center gap-1">
                  <Users className="w-4 h-4" /> 2 Stakeholders
                </div>
              </div>
            </CardContent>
            <CardFooter>
              <Button className="w-full gap-2">
                <PlayCircle className="w-4 h-4" /> Start Scenario
              </Button>
            </CardFooter>
          </Card>

          <Card className="flex flex-col">
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle>Consultancy Fundamentals</CardTitle>
                  <CardDescription className="mt-1">Collection</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="flex-1">
              <p className="text-sm text-muted-foreground">
                Resume your progress on the core consultancy skills collection. Focus on active listening and structured communication.
              </p>
              <div className="mt-4 w-full bg-secondary rounded-full h-2">
                <div className="bg-primary h-2 rounded-full w-[45%]"></div>
              </div>
              <p className="text-xs text-muted-foreground mt-2">45% Complete</p>
            </CardContent>
            <CardFooter>
              <Button variant="secondary" className="w-full">
                Continue Collection
              </Button>
            </CardFooter>
          </Card>
        </div>
      </div>
    </div>
  );
}
