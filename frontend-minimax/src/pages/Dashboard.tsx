import { type JSX } from 'react';
import { useTheme } from '../theme';
import { Header, Page, Section, Grid } from '../components/layout';
import { Card, StatCard, ThemeSwitcher, ProgressRing, StatusIndicator, Badge, Button, Progress } from '../components';

export function DashboardPage(): JSX.Element {
  const { activeTheme } = useTheme();

  return (
    <Page maxWidth="1400px">
      <Section gap="lg">
        <Header
          title="Dashboard"
          subtitle="Track your professional skills growth"
          actions={<ThemeSwitcher compact />}
        />

        <Grid columns="repeat(4, 1fr)" gap="md">
          <StatCard label="Practice Sessions" value={24} change={{ value: 12, type: 'increase' }} />
          <StatCard label="Skills Assessed" value={8} />
          <StatCard label="Avg Score" value="87%" change={{ value: 5, type: 'increase' }} />
          <StatCard label="Streak" value="7 days" />
        </Grid>

        <Grid columns="repeat(3, 1fr)" gap="md">
          <Card variant="elevated" padding="lg">
            <div style={{ marginBottom: activeTheme.spacing.space4 }}>
              <h3
                style={{
                  fontFamily: activeTheme.typography.fontDisplay,
                  fontSize: activeTheme.typography.sizeXl,
                  fontWeight: activeTheme.typography.weightBold,
                  color: activeTheme.colors.text,
                }}
              >
                Skill Progress
              </h3>
            </div>
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: activeTheme.spacing.space4,
              }}
            >
              {[
                { skill: 'Active Listening', level: 78 },
                { skill: 'Structured Communication', level: 65 },
                { skill: 'Conflict Handling', level: 45 },
                { skill: 'Expectation Setting', level: 82 },
              ].map((item) => (
                <div key={item.skill}>
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      marginBottom: activeTheme.spacing.space1,
                    }}
                  >
                    <span
                      style={{
                        fontFamily: activeTheme.typography.fontBody,
                        fontSize: activeTheme.typography.sizeSm,
                        color: activeTheme.colors.text,
                      }}
                    >
                      {item.skill}
                    </span>
                    <span
                      style={{
                        fontFamily: activeTheme.typography.fontMono,
                        fontSize: activeTheme.typography.sizeSm,
                        color: activeTheme.colors.textMuted,
                      }}
                    >
                      {item.level}%
                    </span>
                  </div>
                  <Progress value={item.level} size="sm" />
                </div>
              ))}
            </div>
          </Card>

          <Card variant="accent" padding="lg">
            <div style={{ marginBottom: activeTheme.spacing.space4 }}>
              <h3
                style={{
                  fontFamily: activeTheme.typography.fontDisplay,
                  fontSize: activeTheme.typography.sizeXl,
                  fontWeight: activeTheme.typography.weightBold,
                  color: activeTheme.colors.text,
                }}
              >
                Competency Overview
              </h3>
            </div>
            <div
              style={{
                display: 'flex',
                justifyContent: 'center',
                gap: activeTheme.spacing.space6,
                flexWrap: 'wrap',
              }}
            >
              {[
                { label: 'Communication', value: 85 },
                { label: 'Leadership', value: 62 },
                { label: 'Problem Solving', value: 74 },
              ].map((comp) => (
                <ProgressRing
                  key={comp.label}
                  value={comp.value}
                  size={100}
                  label={comp.label}
                />
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
                Recent Activity
              </h3>
            </div>
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: activeTheme.spacing.space3,
              }}
            >
              {[
                { type: 'assessed', title: 'Stakeholder Management Scenario', time: '2h ago' },
                { type: 'pending', title: 'Conflict Resolution Interview', time: '5h ago' },
                { type: 'assessed', title: 'Executive Summary Exercise', time: '1d ago' },
              ].map((item, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: activeTheme.spacing.space3,
                    backgroundColor: activeTheme.colors.surfaceAlt,
                    borderRadius: activeTheme.borderRadius.md,
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: activeTheme.spacing.space3 }}>
                    <StatusIndicator status={item.type as 'assessed' | 'pending'} showLabel={false} />
                    <span
                      style={{
                        fontFamily: activeTheme.typography.fontBody,
                        fontSize: activeTheme.typography.sizeSm,
                        color: activeTheme.colors.text,
                      }}
                    >
                      {item.title}
                    </span>
                  </div>
                  <span
                    style={{
                      fontFamily: activeTheme.typography.fontMono,
                      fontSize: activeTheme.typography.sizeXs,
                      color: activeTheme.colors.textMuted,
                    }}
                  >
                    {item.time}
                  </span>
                </div>
              ))}
            </div>
          </Card>
        </Grid>

        <Card variant="elevated" padding="lg">
          <div style={{ marginBottom: activeTheme.spacing.space4 }}>
            <h3
              style={{
                fontFamily: activeTheme.typography.fontDisplay,
                fontSize: activeTheme.typography.sizeXl,
                fontWeight: activeTheme.typography.weightBold,
                color: activeTheme.colors.text,
              }}
            >
              Practice Collection
            </h3>
          </div>
          <Grid columns="repeat(auto-fill, minmax(280px, 1fr))" gap="md">
            {[
              { title: 'Client Communication Fundamentals', skills: 4, difficulty: 'Beginner' },
              { title: 'Stakeholder Management Advanced', skills: 6, difficulty: 'Advanced' },
              { title: 'Conflict Resolution Scenarios', skills: 5, difficulty: 'Intermediate' },
              { title: 'Executive Presence Practice', skills: 3, difficulty: 'Intermediate' },
            ].map((collection) => (
              <Card key={collection.title} variant="default" padding="md">
                <div style={{ display: 'flex', flexDirection: 'column', gap: activeTheme.spacing.space3 }}>
                  <div>
                    <h4
                      style={{
                        fontFamily: activeTheme.typography.fontBody,
                        fontSize: activeTheme.typography.sizeBase,
                        fontWeight: activeTheme.typography.weightMedium,
                        color: activeTheme.colors.text,
                        marginBottom: activeTheme.spacing.space2,
                      }}
                    >
                      {collection.title}
                    </h4>
                    <div style={{ display: 'flex', gap: activeTheme.spacing.space2, flexWrap: 'wrap' }}>
                      <Badge variant="primary" size="sm">{collection.skills} skills</Badge>
                      <Badge variant={collection.difficulty === 'Beginner' ? 'success' : collection.difficulty === 'Advanced' ? 'error' : 'warning'} size="sm">
                        {collection.difficulty}
                      </Badge>
                    </div>
                  </div>
                  <Button variant="secondary" size="sm">Start Practice</Button>
                </div>
              </Card>
            ))}
          </Grid>
        </Card>
      </Section>
    </Page>
  );
}
