import { Card, Text, Badge, Progress, Stat } from '../../components';

const competencies = [
  {
    name: 'Stakeholder Management',
    level: 72,
    trend: 'up' as const,
    skills: [
      { name: 'Expectation Setting', level: 78 },
      { name: 'Empathy', level: 65 },
      { name: 'Negotiation', level: 52 },
    ],
  },
  {
    name: 'Communication',
    level: 85,
    trend: 'up' as const,
    skills: [
      { name: 'Active Listening', level: 90 },
      { name: 'Concise Speaking', level: 82 },
      { name: 'Structured Communication', level: 88 },
    ],
  },
  {
    name: 'Teamwork',
    level: 68,
    trend: 'neutral' as const,
    skills: [
      { name: 'Conflict Handling', level: 45 },
      { name: 'Decision Justification', level: 75 },
      { name: 'Active Listening', level: 90 },
    ],
  },
  {
    name: 'Prioritization',
    level: 58,
    trend: 'up' as const,
    skills: [
      { name: 'Prioritization Under Pressure', level: 55 },
      { name: 'Executive Summary', level: 91 },
      { name: 'Structured Thinking', level: 62 },
    ],
  },
  {
    name: 'Professionalism',
    level: 82,
    trend: 'up' as const,
    skills: [
      { name: 'Active Listening', level: 90 },
      { name: 'Empathy', level: 65 },
      { name: 'Decision Justification', level: 75 },
    ],
  },
  {
    name: 'Problem Solving',
    level: 75,
    trend: 'up' as const,
    skills: [
      { name: 'Structured Thinking', level: 62 },
      { name: 'Decision Justification', level: 75 },
      { name: 'Active Listening', level: 90 },
    ],
  },
];

const recentScores = [
  { date: 'Mar 18', score: 82 },
  { date: 'Mar 17', score: 75 },
  { date: 'Mar 16', score: 68 },
  { date: 'Mar 15', score: 91 },
  { date: 'Mar 14', score: 73 },
  { date: 'Mar 13', score: 65 },
  { date: 'Mar 12', score: 78 },
  { date: 'Mar 11', score: 85 },
  { date: 'Mar 10', score: 70 },
  { date: 'Mar 9', score: 88 },
];

function getLevelColor(level: number): string {
  if (level >= 80) return 'var(--color-status-success)';
  if (level >= 60) return 'var(--color-status-info)';
  if (level >= 40) return 'var(--color-status-warning)';
  return 'var(--color-status-error)';
}

function getProgressVariant(level: number): 'success' | 'default' | 'warning' | 'error' {
  if (level >= 80) return 'success';
  if (level >= 60) return 'default';
  if (level >= 40) return 'warning';
  return 'error';
}

/**
 * Progress - Skill and competency progression tracking.
 */
export function ProgressPage() {
  return (
    <div>
      <div style={{ marginBottom: 'var(--space-8)' }}>
        <Text variant="display" style={{ marginBottom: 'var(--space-2)' }}>
          Progress
        </Text>
        <Text variant="body" color="secondary">
          Track your skill development over time. Progress reflects demonstrated performance across multiple practice sessions.
        </Text>
      </div>

      {/* Summary stats */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: 'var(--space-6)',
        marginBottom: 'var(--space-8)',
      }}>
        <Card variant="filled" padding="lg">
          <Stat
            label="Overall Level"
            value="Intermediate"
            description="Based on 47 assessments"
          />
        </Card>
        <Card variant="filled" padding="lg">
          <Stat
            label="Strongest Skill"
            value="Active Listening"
            description="Score: 90%"
          />
        </Card>
        <Card variant="filled" padding="lg">
          <Stat
            label="Focus Skill"
            value="Conflict Handling"
            description="Score: 45%"
          />
        </Card>
        <Card variant="filled" padding="lg">
          <Stat
            label="Sessions This Week"
            value={8}
            change={{ value: 14, direction: 'up' }}
            description="vs. last week"
          />
        </Card>
      </div>

      {/* Score trend mini-chart */}
      <Card padding="lg" style={{ marginBottom: 'var(--space-8)' }}>
        <Text variant="subheading" style={{ marginBottom: 'var(--space-6)' }}>
          Score Trend (Last 10 Sessions)
        </Text>
        <div style={{
          display: 'flex',
          alignItems: 'flex-end',
          gap: 'var(--space-2)',
          height: '8rem',
          paddingBottom: 'var(--space-4)',
          borderBottom: '1px solid var(--color-border-subtle)',
        }}>
          {recentScores.map((entry, i) => {
            const height = (entry.score / 100) * 100;
            return (
              <div
                key={i}
                style={{
                  flex: 1,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: 'var(--space-1)',
                }}
              >
                <span style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: 'var(--font-size-micro)',
                  color: 'var(--color-fg-tertiary)',
                }}>
                  {entry.score}
                </span>
                <div style={{
                  width: '100%',
                  maxWidth: '2rem',
                  height: `${height}%`,
                  backgroundColor: getLevelColor(entry.score),
                  borderRadius: 'var(--radius-sm) var(--radius-sm) 0 0',
                  transition: 'height var(--duration-slow) var(--easing-out)',
                  transitionDelay: `${i * 50}ms`,
                }} />
              </div>
            );
          })}
        </div>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginTop: 'var(--space-2)',
        }}>
          {recentScores.map((entry, i) => (
            <span
              key={i}
              style={{
                flex: 1,
                textAlign: 'center',
                fontFamily: 'var(--font-body)',
                fontSize: 'var(--font-size-micro)',
                color: 'var(--color-fg-tertiary)',
              }}
            >
              {entry.date.split(' ')[1]}
            </span>
          ))}
        </div>
      </Card>

      {/* Competency breakdown */}
      <Text variant="subheading" style={{ marginBottom: 'var(--space-4)' }}>
        Competency Progression
      </Text>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(2, 1fr)',
        gap: 'var(--space-5)',
      }}>
        {competencies.map((comp) => (
          <Card key={comp.name} padding="lg">
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: 'var(--space-4)',
            }}>
              <div>
                <Text variant="body" style={{ fontWeight: 600 }}>
                  {comp.name}
                </Text>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 'var(--space-2)',
                  marginTop: 'var(--space-1)',
                }}>
                  <span style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: 'var(--font-size-xl)',
                    color: getLevelColor(comp.level),
                    fontWeight: 600,
                  }}>
                    {comp.level}
                  </span>
                  <Badge
                    variant={comp.trend === 'up' ? 'success' : 'default'}
                    size="sm"
                  >
                    {comp.trend === 'up' ? '↑ Improving' : '→ Stable'}
                  </Badge>
                </div>
              </div>
            </div>

            <Progress value={comp.level} variant={getProgressVariant(comp.level)} showLabel />

            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--space-3)',
              marginTop: 'var(--space-4)',
              paddingTop: 'var(--space-4)',
              borderTop: '1px solid var(--color-border-subtle)',
            }}>
              {comp.skills.map((skill) => (
                <div key={skill.name}>
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    marginBottom: 'var(--space-1)',
                  }}>
                    <Text variant="bodySmall">{skill.name}</Text>
                    <Text
                      variant="mono"
                      style={{
                        fontSize: 'var(--font-size-small)',
                        color: getLevelColor(skill.level),
                      }}
                    >
                      {skill.level}
                    </Text>
                  </div>
                  <Progress value={skill.level} size="sm" variant={getProgressVariant(skill.level)} />
                </div>
              ))}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
