import { PageShell } from '@/design-system/patterns/PageShell';
import { Card } from '@/design-system/primitives/Card';
import { Badge } from '@/design-system/primitives/Badge';
import { Button } from '@/design-system/primitives/Button';
import { Avatar } from '@/design-system/primitives/Avatar';
import { ProgressBar } from '@/design-system/primitives/ProgressBar';
import { Clock, Users, Target, Mic, MessageSquare, Brain, Briefcase, TrendingUp } from 'lucide-react';

const PRACTICE_MODES = [
  {
    id: 'interview',
    title: 'Interview Simulation',
    description: 'Full behavioral interview practice with real-time feedback and scoring',
    icon: <Briefcase className="w-6 h-6" />,
    duration: '30-45 min',
    difficulty: 'Intermediate',
    color: 'accent',
    features: ['Live scoring', 'Follow-up questions', 'Competency mapping'],
  },
  {
    id: 'scenario',
    title: 'Scenario Practice',
    description: 'Navigate realistic workplace situations with complex stakeholder dynamics',
    icon: <Target className="w-6 h-6" />,
    duration: '15-30 min',
    difficulty: 'Advanced',
    color: 'info',
    features: ['Multi-step scenarios', 'Stakeholder management', 'Decision trees'],
  },
  {
    id: 'quick',
    title: 'Quick Practice',
    description: 'Focused skill drills for rapid improvement in specific areas',
    icon: <Brain className="w-6 h-6" />,
    duration: '5-10 min',
    difficulty: 'Beginner',
    color: 'success',
    features: ['Targeted skills', 'Instant feedback', 'High repetition'],
  },
  {
    id: 'speech',
    title: 'Speech Exercises',
    description: 'Practice concise, impactful verbal communication and presentation',
    icon: <Mic className="w-6 h-6" />,
    duration: '10-15 min',
    difficulty: 'Intermediate',
    color: 'warning',
    features: ['Voice analysis', 'Clarity scoring', 'Pace guidance'],
  },
];

const RECENT_SESSIONS = [
  {
    id: 1,
    type: 'Interview',
    title: 'Tech Lead Position at DataCorp',
    date: '2 hours ago',
    score: 87,
    duration: '42 min',
    skills: ['Technical Leadership', 'Communication', 'Problem Solving'],
    status: 'completed',
  },
  {
    id: 2,
    type: 'Scenario',
    title: 'The Unhappy Sponsor',
    date: 'Yesterday',
    score: 78,
    duration: '28 min',
    skills: ['Stakeholder Management', 'Negotiation', 'Conflict Resolution'],
    status: 'completed',
  },
  {
    id: 3,
    type: 'Quick Practice',
    title: 'Executive Summary Drill',
    date: '2 days ago',
    score: 92,
    duration: '8 min',
    skills: ['Concise Communication', 'Executive Presence'],
    status: 'completed',
  },
  {
    id: 4,
    type: 'Interview',
    title: 'AI Consultant Role Interview',
    date: '3 days ago',
    score: 81,
    duration: '38 min',
    skills: ['AI Knowledge', 'Client Communication', 'Solution Design'],
    status: 'completed',
  },
];

const RECOMMENDED_PRACTICE = [
  {
    id: 1,
    title: 'Prioritization Under Pressure',
    description: 'Practice making tough choices when everything seems urgent',
    type: 'Scenario',
    duration: '25 min',
    difficulty: 'Advanced',
    reason: 'Based on your recent stakeholder scenarios',
    skills: ['Prioritization', 'Decision Making', 'Stakeholder Management'],
  },
  {
    id: 2,
    title: 'Saying No Gracefully',
    description: 'Learn to decline requests while maintaining relationships',
    type: 'Quick Practice',
    duration: '12 min',
    difficulty: 'Intermediate',
    reason: 'Improve boundary-setting skills',
    skills: ['Communication', 'Professionalism', 'Negotiation'],
  },
  {
    id: 3,
    title: 'Executive Presentation',
    description: 'Deliver complex information to senior leadership',
    type: 'Speech Exercise',
    duration: '18 min',
    difficulty: 'Advanced',
    reason: 'Prepare for client presentations',
    skills: ['Executive Presence', 'Communication', 'Clarity'],
  },
];

function getSessionTypeColor(type: string) {
  switch (type) {
    case 'Interview':
      return 'accent';
    case 'Scenario':
      return 'info';
    case 'Quick Practice':
      return 'success';
    case 'Speech Exercise':
      return 'warning';
    default:
      return 'default';
  }
}

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

export function Practice() {
  return (
    <PageShell
      title="Practice Hub"
      subtitle="Choose a practice mode to improve your consultancy skills."
    >
      <div className="flex flex-col gap-8">
        {/* Practice Modes */}
        <section className="flex flex-col gap-6">
          <h3 className="font-display text-display-xs text-content-primary">Practice Modes</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {PRACTICE_MODES.map((mode) => (
              <Card key={mode.id} interactive className="flex flex-col gap-4 p-6 text-center">
                <div className={`w-12 h-12 rounded-full bg-${mode.color}/10 flex items-center justify-center mx-auto text-${mode.color}`}>
                  {mode.icon}
                </div>
                <div className="flex flex-col gap-2">
                  <h4 className="font-display text-display-sm text-content-primary">{mode.title}</h4>
                  <p className="text-body-sm text-content-secondary line-clamp-3">{mode.description}</p>
                </div>
                <div className="flex flex-col gap-2 text-body-xs text-content-tertiary">
                  <div className="flex items-center justify-center gap-1">
                    <Clock className="w-3 h-3" />
                    <span>{mode.duration}</span>
                  </div>
                  <Badge variant={getDifficultyColor(mode.difficulty)} size="sm">
                    {mode.difficulty}
                  </Badge>
                </div>
                <div className="flex flex-wrap gap-1 justify-center">
                  {mode.features.map((feature) => (
                    <Badge key={feature} variant="default" size="sm">
                      {feature}
                    </Badge>
                  ))}
                </div>
                <Button className="w-full mt-2">Start Practice</Button>
              </Card>
            ))}
          </div>
        </section>

        {/* Recommended Practice */}
        <section className="flex flex-col gap-6">
          <div className="flex items-center justify-between">
            <h3 className="font-display text-display-xs text-content-primary">Recommended for You</h3>
            <Button variant="ghost" size="sm">View All</Button>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {RECOMMENDED_PRACTICE.map((practice) => (
              <Card key={practice.id} className="flex flex-col gap-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 flex flex-col gap-2">
                    <Badge variant={getSessionTypeColor(practice.type)} size="sm">
                      {practice.type}
                    </Badge>
                    <h4 className="font-display text-display-sm text-content-primary line-clamp-2">
                      {practice.title}
                    </h4>
                    <p className="text-body-sm text-content-secondary line-clamp-2">
                      {practice.description}
                    </p>
                  </div>
                </div>
                
                <div className="flex flex-col gap-3">
                  <div className="flex items-center gap-3 text-body-xs text-content-tertiary">
                    <div className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5" />
                      <span>{practice.duration}</span>
                    </div>
                    <Badge variant={getDifficultyColor(practice.difficulty)} size="sm">
                      {practice.difficulty}
                    </Badge>
                  </div>
                  
                  <div className="flex flex-col gap-1">
                    <p className="text-body-xs text-content-tertiary italic">"{practice.reason}"</p>
                    <div className="flex flex-wrap gap-1">
                      {practice.skills.map((skill) => (
                        <Badge key={skill} variant="default" size="sm">
                          {skill}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  
                  <Button className="w-full">Start Practice</Button>
                </div>
              </Card>
            ))}
          </div>
        </section>

        {/* Recent Sessions */}
        <section className="flex flex-col gap-6">
          <div className="flex items-center justify-between">
            <h3 className="font-display text-display-xs text-content-primary">Recent Sessions</h3>
            <Button variant="ghost" size="sm">View History</Button>
          </div>
          <div className="flex flex-col gap-3">
            {RECENT_SESSIONS.map((session) => (
              <Card key={session.id} variant="elevated" className="flex items-center justify-between p-4">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-full bg-surface-secondary flex items-center justify-center font-display text-body-lg text-content-primary">
                    {session.score}
                  </div>
                  <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-2">
                      <Badge variant={getSessionTypeColor(session.type)} size="sm">
                        {session.type}
                      </Badge>
                      <h4 className="text-body-sm font-medium text-content-primary">{session.title}</h4>
                    </div>
                    <div className="flex items-center gap-3 text-body-xs text-content-tertiary">
                      <span>{session.date}</span>
                      <div className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        <span>{session.duration}</span>
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {session.skills.map((skill) => (
                        <Badge key={skill} variant="default" size="sm">
                          {skill}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex flex-col items-end gap-1">
                    <ProgressBar value={session.score} showValue size="sm" />
                    <span className="text-body-xs text-content-tertiary">Score</span>
                  </div>
                  <Button variant="secondary" size="sm">Review</Button>
                </div>
              </Card>
            ))}
          </div>
        </section>

        {/* Skill Focus Areas */}
        <section className="flex flex-col gap-6">
          <h3 className="font-display text-display-xs text-content-primary">Your Skill Focus Areas</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[
              { skill: 'Stakeholder Management', level: 65, focus: 'High', trend: 'up' },
              { skill: 'Communication', level: 82, focus: 'Medium', trend: 'up' },
              { skill: 'Prioritization', level: 45, focus: 'High', trend: 'down' },
              { skill: 'Executive Presence', level: 71, focus: 'Medium', trend: 'up' },
              { skill: 'Conflict Resolution', level: 58, focus: 'High', trend: 'stable' },
              { skill: 'Technical Leadership', level: 88, focus: 'Low', trend: 'up' },
            ].map((skill) => (
              <Card key={skill.skill} className="flex flex-col gap-3 p-4">
                <div className="flex items-center justify-between">
                  <h4 className="text-body-sm font-medium text-content-primary">{skill.skill}</h4>
                  <div className="flex items-center gap-2">
                    <Badge 
                      variant={skill.focus === 'High' ? 'error' : skill.focus === 'Medium' ? 'warning' : 'success'} 
                      size="sm"
                    >
                      {skill.focus} Focus
                    </Badge>
                    {skill.trend === 'up' && <TrendingUp className="w-4 h-4 text-status-success" />}
                    {skill.trend === 'down' && <TrendingUp className="w-4 h-4 text-status-error rotate-180" />}
                  </div>
                </div>
                <ProgressBar value={skill.level} label="Current Level" showValue />
                <Button variant="ghost" size="sm" className="w-full">
                  Practice {skill.skill}
                </Button>
              </Card>
            ))}
          </div>
        </section>
      </div>
    </PageShell>
  );
}
