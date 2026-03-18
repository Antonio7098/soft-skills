import { Card, Stack, Text, Badge, Button, Avatar, Tag } from '../../components';

const practiceModes = [
  {
    id: 'interview',
    title: 'Interview Simulation',
    description: 'Practice behavioural interviews with AI-driven follow-up probing and competency-focused scoring.',
    icon: '▶',
    duration: '15-30 min',
    skills: ['Communication', 'Problem Solving', 'Professionalism'],
    color: 'accent',
  },
  {
    id: 'scenario',
    title: 'Scenario Practice',
    description: 'Navigate realistic workplace situations: unhappy stakeholders, conflicting deadlines, scope changes.',
    icon: '◆',
    duration: '10-20 min',
    skills: ['Stakeholder Management', 'Prioritization', 'Adaptability'],
    color: 'info',
  },
  {
    id: 'quick',
    title: 'Quick Practice',
    description: 'Short, focused prompts targeting a single skill or compact scenario. Perfect for daily practice.',
    icon: '●',
    duration: '2-5 min',
    skills: ['Active Listening', 'Concise Speaking', 'Empathy'],
    color: 'success',
  },
  {
    id: 'speech',
    title: 'Speech Exercises',
    description: 'Practice concise speaking tasks: executive summaries, difficult conversations, client explanations.',
    icon: '◎',
    duration: '5-10 min',
    skills: ['Executive Summary', 'Concise Speaking', 'Decision Justification'],
    color: 'warning',
  },
];

const mockScenarios = [
  {
    title: 'The Unhappy Client',
    company: 'Meridian Consulting',
    description: 'Your client is dissatisfied with the project timeline. Schedule a call to address concerns.',
    difficulty: 'Intermediate',
    skills: ['Conflict Handling', 'Expectation Setting', 'Empathy'],
    estimatedTime: '15 min',
    persona: {
      name: 'Sarah Chen',
      role: 'VP of Operations',
      avatar: 'SC',
    },
  },
  {
    title: 'Team Misalignment',
    company: 'TechForward Inc.',
    description: 'Two senior engineers disagree on the technical approach. Facilitate a resolution.',
    difficulty: 'Advanced',
    skills: ['Teamwork', 'Negotiation', 'Decision Justification'],
    estimatedTime: '20 min',
    persona: {
      name: 'James Wright',
      role: 'Engineering Manager',
      avatar: 'JW',
    },
  },
  {
    title: 'Scope Creep Negotiation',
    company: 'Nova Digital',
    description: 'The client wants to add features beyond the agreed scope. Negotiate a path forward.',
    difficulty: 'Advanced',
    skills: ['Prioritization', 'Negotiation', 'Stakeholder Management'],
    estimatedTime: '18 min',
    persona: {
      name: 'Maria Santos',
      role: 'Product Director',
      avatar: 'MS',
    },
  },
];

/**
 * Practice - Practice mode selection and scenario browser.
 */
export function Practice() {
  return (
    <div>
      <div style={{ marginBottom: 'var(--space-8)' }}>
        <Text variant="display" style={{ marginBottom: 'var(--space-2)' }}>
          Practice
        </Text>
        <Text variant="body" color="secondary">
          Choose a practice mode or browse scenarios to start a session.
        </Text>
      </div>

      {/* Practice modes */}
      <div style={{ marginBottom: 'var(--space-10)' }}>
        <Text variant="subheading" style={{ marginBottom: 'var(--space-4)' }}>
          Practice Modes
        </Text>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: 'var(--space-4)',
        }}>
          {practiceModes.map((mode) => (
            <Card
              key={mode.id}
              variant="default"
              padding="lg"
              interactive
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--space-3)',
              }}
            >
              <div style={{
                width: '3rem',
                height: '3rem',
                borderRadius: 'var(--radius-lg)',
                backgroundColor: 'color-mix(in srgb, var(--color-accent-primary) 12%, transparent)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.25rem',
                color: 'var(--color-accent-primary)',
              }}>
                {mode.icon}
              </div>
              <div>
                <Text variant="body" style={{ fontWeight: 600, marginBottom: 'var(--space-1)' }}>
                  {mode.title}
                </Text>
                <Text variant="bodySmall" color="secondary" lineClamp={3}>
                  {mode.description}
                </Text>
              </div>
              <div style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: 'var(--space-1)',
                marginTop: 'auto',
                paddingTop: 'var(--space-3)',
              }}>
                {mode.skills.map((skill) => (
                  <Tag key={skill} size="sm">{skill}</Tag>
                ))}
              </div>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                paddingTop: 'var(--space-3)',
                borderTop: '1px solid var(--color-border-subtle)',
              }}>
                <Text variant="caption" color="tertiary">{mode.duration}</Text>
                <Button size="sm" variant="secondary">Start</Button>
              </div>
            </Card>
          ))}
        </div>
      </div>

      {/* Featured scenarios */}
      <div>
        <Text variant="subheading" style={{ marginBottom: 'var(--space-4)' }}>
          Featured Scenarios
        </Text>
        <Stack gap="var(--space-4)">
          {mockScenarios.map((scenario, i) => (
            <Card key={i} variant="default" padding="lg" interactive>
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'auto 1fr auto',
                gap: 'var(--space-6)',
                alignItems: 'center',
              }}>
                {/* Persona avatar */}
                <Avatar name={scenario.persona.name} size="lg" />

                {/* Content */}
                <div>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 'var(--space-2)',
                    marginBottom: 'var(--space-2)',
                  }}>
                    <Text variant="subheading">{scenario.title}</Text>
                    <Badge
                      variant={scenario.difficulty === 'Advanced' ? 'warning' : 'info'}
                      size="sm"
                    >
                      {scenario.difficulty}
                    </Badge>
                  </div>
                  <Text variant="body" color="secondary" style={{ marginBottom: 'var(--space-3)' }}>
                    {scenario.description}
                  </Text>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 'var(--space-4)',
                  }}>
                    <Text variant="caption" color="tertiary">
                      {scenario.company}
                    </Text>
                    <Text variant="caption" color="tertiary">
                      {scenario.estimatedTime}
                    </Text>
                    <div style={{ display: 'flex', gap: 'var(--space-1)' }}>
                      {scenario.skills.map((skill) => (
                        <Tag key={skill} size="sm">{skill}</Tag>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Action */}
                <Button>Begin Scenario</Button>
              </div>
            </Card>
          ))}
        </Stack>
      </div>
    </div>
  );
}
