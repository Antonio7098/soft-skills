import { Card, Stack, Text, Badge, Progress, Stat, Tag } from '../../components';

/**
 * Dashboard - Main user landing page.
 * Shows overview stats, recent activity, and recommended practice.
 */
export function Dashboard() {
  return (
    <div>
      {/* Welcome header */}
      <div style={{ marginBottom: 'var(--space-8)' }}>
        <Text variant="display" style={{ marginBottom: 'var(--space-2)' }}>
          Welcome back, Alex
        </Text>
        <Text variant="body" color="secondary">
          Continue building your consultancy skills. You have 3 weak skills to focus on.
        </Text>
      </div>

      {/* Stats row */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: 'var(--space-6)',
        marginBottom: 'var(--space-8)',
      }}>
        <Card variant="filled" padding="lg">
          <Stat
            label="Practice Sessions"
            value={47}
            change={{ value: 12, direction: 'up' }}
            description="This month"
          />
        </Card>
        <Card variant="filled" padding="lg">
          <Stat
            label="Avg. Score"
            value="78%"
            change={{ value: 5, direction: 'up' }}
            description="Across all skills"
          />
        </Card>
        <Card variant="filled" padding="lg">
          <Stat
            label="Skills Improved"
            value={6}
            change={{ value: 2, direction: 'up' }}
            description="Out of 10 tracked"
          />
        </Card>
        <Card variant="filled" padding="lg">
          <Stat
            label="Current Streak"
            value="14"
            description="Days in a row"
          />
        </Card>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 380px',
        gap: 'var(--space-6)',
      }}>
        {/* Recent activity */}
        <Card padding="lg" header={
          <Text variant="subheading">Recent Activity</Text>
        }>
          <Stack gap="var(--space-4)">
            {[
              { skill: 'Stakeholder Management', score: 82, mode: 'Scenario', time: '2 hours ago', competency: 'Communication' },
              { skill: 'Conflict Handling', score: 65, mode: 'Interview', time: 'Yesterday', competency: 'Teamwork' },
              { skill: 'Executive Summary', score: 91, mode: 'Quick Practice', time: '2 days ago', competency: 'Communication' },
              { skill: 'Prioritization', score: 73, mode: 'Scenario', time: '3 days ago', competency: 'Leadership' },
            ].map((item, i) => (
              <div key={i} style={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--space-4)',
                padding: 'var(--space-3) 0',
                borderBottom: i < 3 ? '1px solid var(--color-border-subtle)' : 'none',
              }}>
                <div style={{
                  width: '3rem',
                  height: '3rem',
                  borderRadius: 'var(--radius-lg)',
                  backgroundColor: 'var(--color-bg-muted)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontFamily: 'var(--font-mono)',
                  fontSize: 'var(--font-size-base)',
                  fontWeight: 600,
                  color: item.score >= 80 ? 'var(--color-status-success)' : item.score >= 60 ? 'var(--color-status-warning)' : 'var(--color-status-error)',
                  flexShrink: 0,
                }}>
                  {item.score}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <Text variant="body" style={{ fontWeight: 500 }}>{item.skill}</Text>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 'var(--space-2)',
                    marginTop: 'var(--space-1)',
                  }}>
                    <Badge size="sm">{item.mode}</Badge>
                    <Text variant="caption" color="tertiary">{item.time}</Text>
                  </div>
                </div>
                <Tag size="sm">{item.competency}</Tag>
              </div>
            ))}
          </Stack>
        </Card>

        {/* Sidebar column */}
        <Stack gap="var(--space-6)">
          {/* Recommended practice */}
          <Card variant="elevated" padding="lg">
            <Text variant="subheading" style={{ marginBottom: 'var(--space-4)' }}>
              Recommended Next
            </Text>
            <Stack gap="var(--space-3)">
              {[
                { title: 'Managing Difficult Clients', type: 'Scenario', skill: 'Conflict Handling', duration: '15 min' },
                { title: 'Deadline Negotiation', type: 'Interview', skill: 'Prioritization', duration: '10 min' },
                { title: 'Team Misalignment', type: 'Scenario', skill: 'Teamwork', duration: '20 min' },
              ].map((item, i) => (
                <div key={i} style={{
                  padding: 'var(--space-3)',
                  backgroundColor: 'var(--color-bg-tertiary)',
                  borderRadius: 'var(--radius-md)',
                  cursor: 'pointer',
                  transition: 'all var(--duration-fast) var(--easing-default)',
                }}>
                  <Text variant="body" style={{ fontWeight: 500, marginBottom: 'var(--space-1)' }}>
                    {item.title}
                  </Text>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 'var(--space-2)',
                  }}>
                    <Badge size="sm" variant="accent">{item.type}</Badge>
                    <Text variant="caption" color="tertiary">{item.duration}</Text>
                  </div>
                </div>
              ))}
            </Stack>
          </Card>

          {/* Weak skills */}
          <Card padding="lg">
            <Text variant="subheading" style={{ marginBottom: 'var(--space-4)' }}>
              Focus Areas
            </Text>
            <Stack gap="var(--space-4)">
              {[
                { skill: 'Conflict Handling', level: 45, target: 70 },
                { skill: 'Negotiation', level: 52, target: 70 },
                { skill: 'Expectation Setting', level: 58, target: 75 },
              ].map((item, i) => (
                <div key={i}>
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    marginBottom: 'var(--space-2)',
                  }}>
                    <Text variant="bodySmall">{item.skill}</Text>
                    <Text variant="mono" color="tertiary">{item.level}%</Text>
                  </div>
                  <Progress
                    value={item.level}
                    size="sm"
                    variant={item.level < 50 ? 'warning' : 'default'}
                  />
                </div>
              ))}
            </Stack>
          </Card>
        </Stack>
      </div>
    </div>
  );
}
