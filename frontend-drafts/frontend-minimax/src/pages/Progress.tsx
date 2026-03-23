import { type JSX } from 'react';
import { useTheme } from '../theme';
import { Header, Page, Section, Grid } from '../components/layout';
import {
  Card,
  ThemeSwitcher,
  ProgressRing,
  Progress,
  Badge,
  StatCard,
} from '../components';

const skills = [
  { name: 'Active Listening', level: 78, trend: '+5' },
  { name: 'Structured Communication', level: 65, trend: '+12' },
  { name: 'Conflict Handling', level: 45, trend: '+3' },
  { name: 'Expectation Setting', level: 82, trend: '-2' },
  { name: 'Executive Summaries', level: 71, trend: '+8' },
  { name: 'Stakeholder Management', level: 58, trend: '+15' },
  { name: 'Decision Justification', level: 63, trend: '+7' },
  { name: 'Team Leadership', level: 52, trend: '+10' },
];

const competencies = [
  { name: 'Communication', score: 85, skills: 4 },
  { name: 'Problem Solving', score: 74, skills: 3 },
  { name: 'Leadership', score: 62, skills: 4 },
  { name: 'Stakeholder Management', score: 68, skills: 5 },
];

const progressHistory = [
  { date: 'Mar 2026', sessions: 12, avgScore: 82 },
  { date: 'Feb 2026', sessions: 8, avgScore: 76 },
  { date: 'Jan 2026', sessions: 15, avgScore: 71 },
  { date: 'Dec 2025', sessions: 6, avgScore: 68 },
  { date: 'Nov 2025', sessions: 10, avgScore: 62 },
];

export function ProgressPage(): JSX.Element {
  const { activeTheme } = useTheme();

  return (
    <Page maxWidth="1400px">
      <Section gap="lg">
        <Header
          title="Progress"
          subtitle="Track your competency growth over time"
          actions={<ThemeSwitcher compact />}
        />

        <Grid columns="repeat(4, 1fr)" gap="md">
          <StatCard label="Total Sessions" value={47} change={{ value: 23, type: 'increase' }} />
          <StatCard label="Avg Score" value="79%" change={{ value: 8, type: 'increase' }} />
          <StatCard label="Skills Improving" value="6/8" />
          <StatCard label="Current Streak" value="12 days" />
        </Grid>

        <Grid columns="repeat(2, 1fr)" gap="md">
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
                Skill Breakdown
              </h3>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: activeTheme.spacing.space4 }}>
              {skills.map((skill) => (
                <div key={skill.name}>
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
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
                      {skill.name}
                    </span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: activeTheme.spacing.space2 }}>
                      <span
                        style={{
                          fontFamily: activeTheme.typography.fontMono,
                          fontSize: activeTheme.typography.sizeXs,
                          color: skill.trend.startsWith('+') ? activeTheme.colors.success : skill.trend.startsWith('-') ? activeTheme.colors.error : activeTheme.colors.textMuted,
                        }}
                      >
                        {skill.trend}
                      </span>
                      <span
                        style={{
                          fontFamily: activeTheme.typography.fontMono,
                          fontSize: activeTheme.typography.sizeSm,
                          color: activeTheme.colors.textMuted,
                        }}
                      >
                        {skill.level}%
                      </span>
                    </div>
                  </div>
                  <Progress value={skill.level} size="sm" />
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
                gap: activeTheme.spacing.space8,
                flexWrap: 'wrap',
              }}
            >
              {competencies.map((comp) => (
                <div key={comp.name} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: activeTheme.spacing.space2 }}>
                  <ProgressRing value={comp.score} size={100} label={comp.name} />
                  <Badge variant="default" size="sm">{comp.skills} skills</Badge>
                </div>
              ))}
            </div>
          </Card>
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
              Progress Over Time
            </h3>
          </div>
          <div style={{ display: 'flex', alignItems: 'end', gap: activeTheme.spacing.space4, height: '200px' }}>
            {progressHistory.map((month, idx) => {
              const heightPercent = (month.avgScore / 100) * 180;
              return (
                <div
                  key={month.date}
                  style={{
                    flex: 1,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: activeTheme.spacing.space2,
                    height: '100%',
                  }}
                >
                  <div
                    style={{
                      flex: 1,
                      width: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'flex-end',
                    }}
                  >
                    <div
                      style={{
                        width: '100%',
                        backgroundColor: idx === 0 ? activeTheme.colors.primary : activeTheme.colors.surfaceAlt,
                        borderRadius: activeTheme.borderRadius.md,
                        transition: 'height 0.3s ease',
                        height: `${heightPercent}px`,
                      }}
                    />
                  </div>
                  <div style={{ textAlign: 'center' }}>
                    <div
                      style={{
                        fontFamily: activeTheme.typography.fontMono,
                        fontSize: activeTheme.typography.sizeXs,
                        color: activeTheme.colors.textMuted,
                      }}
                    >
                      {month.avgScore}%
                    </div>
                    <div
                      style={{
                        fontFamily: activeTheme.typography.fontMono,
                        fontSize: activeTheme.typography.sizeXs,
                        color: activeTheme.colors.textMuted,
                      }}
                    >
                      {month.date}
                    </div>
                    <div
                      style={{
                        fontFamily: activeTheme.typography.fontMono,
                        fontSize: activeTheme.typography.sizeXs,
                        color: activeTheme.colors.textMuted,
                      }}
                    >
                      {month.sessions} sessions
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>

        <Grid columns="repeat(3, 1fr)" gap="md">
          <Card variant="outlined" padding="md">
            <div style={{ display: 'flex', flexDirection: 'column', gap: activeTheme.spacing.space3 }}>
              <h4
                style={{
                  fontFamily: activeTheme.typography.fontDisplay,
                  fontSize: activeTheme.typography.sizeLg,
                  fontWeight: activeTheme.typography.weightBold,
                  color: activeTheme.colors.text,
                }}
              >
                Strengths
              </h4>
              {['Expectation Setting (82%)', 'Active Listening (78%)', 'Executive Summaries (71%)'].map((item, idx) => (
                <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: activeTheme.spacing.space2 }}>
                  <span style={{ color: activeTheme.colors.success }}>✓</span>
                  <span style={{ fontFamily: activeTheme.typography.fontBody, fontSize: activeTheme.typography.sizeSm, color: activeTheme.colors.text }}>
                    {item}
                  </span>
                </div>
              ))}
            </div>
          </Card>

          <Card variant="outlined" padding="md">
            <div style={{ display: 'flex', flexDirection: 'column', gap: activeTheme.spacing.space3 }}>
              <h4
                style={{
                  fontFamily: activeTheme.typography.fontDisplay,
                  fontSize: activeTheme.typography.sizeLg,
                  fontWeight: activeTheme.typography.weightBold,
                  color: activeTheme.colors.text,
                }}
              >
                Growth Areas
              </h4>
              {['Conflict Handling (45%)', 'Stakeholder Management (58%)', 'Team Leadership (52%)'].map((item, idx) => (
                <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: activeTheme.spacing.space2 }}>
                  <span style={{ color: activeTheme.colors.warning }}>→</span>
                  <span style={{ fontFamily: activeTheme.typography.fontBody, fontSize: activeTheme.typography.sizeSm, color: activeTheme.colors.text }}>
                    {item}
                  </span>
                </div>
              ))}
            </div>
          </Card>

          <Card variant="outlined" padding="md">
            <div style={{ display: 'flex', flexDirection: 'column', gap: activeTheme.spacing.space3 }}>
              <h4
                style={{
                  fontFamily: activeTheme.typography.fontDisplay,
                  fontSize: activeTheme.typography.sizeLg,
                  fontWeight: activeTheme.typography.weightBold,
                  color: activeTheme.colors.text,
                }}
              >
                Next Steps
              </h4>
              {['Practice Conflict Handling', 'Review Stakeholder Scenarios', 'Schedule Leadership Mock'].map((item, idx) => (
                <Badge key={idx} variant="primary" size="sm">
                  {item}
                </Badge>
              ))}
            </div>
          </Card>
        </Grid>
      </Section>
    </Page>
  );
}
