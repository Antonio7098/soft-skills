import { type JSX } from 'react';
import { useTheme } from '../theme';
import { Header, Page, Section, Grid } from '../components/layout';
import {
  Card,
  ThemeSwitcher,
  ProgressRing,
  Badge,
  Button,
  StatusIndicator,
} from '../components';

const practiceModes = [
  {
    title: 'Interview Simulation',
    description: 'Practice realistic interview scenarios with AI-powered feedback',
    icon: '🎯',
    scenarios: 24,
    difficulty: 'Intermediate',
  },
  {
    title: 'Scenario Practice',
    description: 'Work through realistic workplace situations with stakeholders',
    icon: '💼',
    scenarios: 18,
    difficulty: 'Advanced',
  },
  {
    title: 'Quick Practice',
    description: 'Short, focused exercises on specific skills',
    icon: '⚡',
    scenarios: 42,
    difficulty: 'All Levels',
  },
];

const recentSessions = [
  { title: 'Stakeholder Management Interview', type: 'interview', status: 'assessed' as const, score: 85, time: '2h ago' },
  { title: 'Conflict Resolution Scenario', type: 'scenario', status: 'pending' as const, score: null, time: '5h ago' },
  { title: 'Executive Summary Quick Practice', type: 'quick', status: 'assessed' as const, score: 92, time: '1d ago' },
  { title: 'Leadership Interview Questions', type: 'interview', status: 'assessed' as const, score: 78, time: '2d ago' },
];

export function PracticePage(): JSX.Element {
  const { activeTheme } = useTheme();

  return (
    <Page maxWidth="1400px">
      <Section gap="lg">
        <Header
          title="Practice"
          subtitle="Choose your practice mode"
          actions={<ThemeSwitcher compact />}
        />

        <Grid columns="repeat(3, 1fr)" gap="md">
          {practiceModes.map((mode) => (
            <Card key={mode.title} variant="elevated" padding="lg">
              <div style={{ display: 'flex', flexDirection: 'column', gap: activeTheme.spacing.space4 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: activeTheme.spacing.space3 }}>
                  <span style={{ fontSize: '2rem' }}>{mode.icon}</span>
                  <div>
                    <h3
                      style={{
                        fontFamily: activeTheme.typography.fontDisplay,
                        fontSize: activeTheme.typography.sizeLg,
                        fontWeight: activeTheme.typography.weightBold,
                        color: activeTheme.colors.text,
                      }}
                    >
                      {mode.title}
                    </h3>
                    <Badge
                      variant={mode.difficulty === 'Advanced' ? 'error' : mode.difficulty === 'Intermediate' ? 'warning' : 'success'}
                      size="sm"
                    >
                      {mode.difficulty}
                    </Badge>
                  </div>
                </div>
                <p
                  style={{
                    fontFamily: activeTheme.typography.fontBody,
                    fontSize: activeTheme.typography.sizeSm,
                    color: activeTheme.colors.textMuted,
                    lineHeight: activeTheme.typography.lineHeightRelaxed,
                  }}
                >
                  {mode.description}
                </p>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span
                    style={{
                      fontFamily: activeTheme.typography.fontMono,
                      fontSize: activeTheme.typography.sizeXs,
                      color: activeTheme.colors.textMuted,
                    }}
                  >
                    {mode.scenarios} scenarios
                  </span>
                  <Button variant="primary" size="sm">
                    Start
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </Grid>

        <Card variant="default" padding="lg">
          <div style={{ marginBottom: activeTheme.spacing.space4 }}>
            <h3
              style={{
                fontFamily: activeTheme.typography.fontDisplay,
                fontSize: activeTheme.typography.sizeXl,
                fontWeight: activeTheme.typography.weightBold,
                color: activeTheme.colors.text,
              }}
            >
              Continue Practice
            </h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: activeTheme.spacing.space3 }}>
            {recentSessions.map((session, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: activeTheme.spacing.space4,
                  backgroundColor: activeTheme.colors.surfaceAlt,
                  borderRadius: activeTheme.borderRadius.md,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: activeTheme.spacing.space4 }}>
                  <StatusIndicator status={session.status} showLabel={false} />
                  <div>
                    <h4
                      style={{
                        fontFamily: activeTheme.typography.fontBody,
                        fontSize: activeTheme.typography.sizeBase,
                        fontWeight: activeTheme.typography.weightMedium,
                        color: activeTheme.colors.text,
                      }}
                    >
                      {session.title}
                    </h4>
                    <div style={{ display: 'flex', gap: activeTheme.spacing.space2, marginTop: activeTheme.spacing.space1 }}>
                      <Badge variant="default" size="sm">
                        {session.type}
                      </Badge>
                      {session.score && (
                        <Badge variant="success" size="sm">
                          Score: {session.score}%
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: activeTheme.spacing.space4 }}>
                  <span
                    style={{
                      fontFamily: activeTheme.typography.fontMono,
                      fontSize: activeTheme.typography.sizeXs,
                      color: activeTheme.colors.textMuted,
                    }}
                  >
                    {session.time}
                  </span>
                  <Button variant="secondary" size="sm">
                    {session.status === 'pending' ? 'Continue' : 'Review'}
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card variant="outlined" padding="lg">
          <div style={{ marginBottom: activeTheme.spacing.space4 }}>
            <h3
              style={{
                fontFamily: activeTheme.typography.fontDisplay,
                fontSize: activeTheme.typography.sizeXl,
                fontWeight: activeTheme.typography.weightBold,
                color: activeTheme.colors.text,
              }}
            >
              Recommended For You
            </h3>
          </div>
          <Grid columns="repeat(2, 1fr)" gap="md">
            {[
              { skill: 'Conflict Handling', match: 94, reason: 'Based on your recent assessment' },
              { skill: 'Expectation Setting', match: 87, reason: 'Identified as a growth area' },
              { skill: 'Executive Summaries', match: 82, reason: 'Strengthen your communication' },
              { skill: 'Stakeholder Management', match: 76, reason: 'Building on your progress' },
            ].map((rec) => (
              <div
                key={rec.skill}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: activeTheme.spacing.space4,
                  backgroundColor: activeTheme.colors.surfaceAlt,
                  borderRadius: activeTheme.borderRadius.md,
                }}
              >
                <div>
                  <h4
                    style={{
                      fontFamily: activeTheme.typography.fontBody,
                      fontSize: activeTheme.typography.sizeBase,
                      fontWeight: activeTheme.typography.weightMedium,
                      color: activeTheme.colors.text,
                    }}
                  >
                    {rec.skill}
                  </h4>
                  <p
                    style={{
                      fontFamily: activeTheme.typography.fontBody,
                      fontSize: activeTheme.typography.sizeXs,
                      color: activeTheme.colors.textMuted,
                    }}
                  >
                    {rec.reason}
                  </p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: activeTheme.spacing.space3 }}>
                  <ProgressRing value={rec.match} size={50} showValue={false} />
                  <Button variant="ghost" size="sm">
                    Start
                  </Button>
                </div>
              </div>
            ))}
          </Grid>
        </Card>
      </Section>
    </Page>
  );
}
