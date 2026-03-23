import { type JSX } from 'react';
import { useTheme } from '../theme';
import { Header, Page, Section, Grid } from '../components/layout';
import {
  Card,
  ThemeSwitcher,
  Badge,
  Button,
  Progress,
  Avatar,
} from '../components';

const collections = [
  {
    title: 'Client Communication Fundamentals',
    description: 'Master the essentials of professional client interaction',
    skills: ['Active Listening', 'Expectation Setting', 'Structured Communication'],
    difficulty: 'Beginner',
    items: 12,
    completion: 75,
    author: 'Platform',
    verified: true,
  },
  {
    title: 'Stakeholder Management Advanced',
    description: 'Navigate complex organizational dynamics with confidence',
    skills: ['Stakeholder Analysis', 'Influence', 'Negotiation', 'Conflict Resolution'],
    difficulty: 'Advanced',
    items: 18,
    completion: 30,
    author: 'Platform',
    verified: true,
  },
  {
    title: 'Interview Preparation: Tech Leadership',
    description: 'Prepare for senior tech roles with realistic interview scenarios',
    skills: ['Decision Justification', 'Team Leadership', 'Strategic Thinking'],
    difficulty: 'Intermediate',
    items: 24,
    completion: 0,
    author: 'Platform',
    verified: true,
  },
  {
    title: 'Conflict Resolution Mastery',
    description: 'Transform workplace conflicts into productive outcomes',
    skills: ['Conflict Handling', 'Empathy', 'Mediation', 'Problem Solving'],
    difficulty: 'Intermediate',
    items: 15,
    completion: 45,
    author: 'Coach Elena M.',
    verified: true,
  },
  {
    title: 'Executive Presence',
    description: 'Develop commanding communication for leadership contexts',
    skills: ['Executive Summary', 'Presentation', 'Concise Communication'],
    difficulty: 'Advanced',
    items: 10,
    completion: 0,
    author: 'Platform',
    verified: true,
  },
  {
    title: 'Quick Skills: Communication',
    description: 'Short exercises for busy professionals',
    skills: ['Concise Speaking', 'Active Listening', 'Clear Writing'],
    difficulty: 'Beginner',
    items: 30,
    completion: 100,
    author: 'Platform',
    verified: true,
  },
];

export function CollectionsPage(): JSX.Element {
  const { activeTheme } = useTheme();

  return (
    <Page maxWidth="1400px">
      <Section gap="lg">
        <Header
          title="Collections"
          subtitle="Curated practice sets for skill development"
          actions={<ThemeSwitcher compact />}
        />

        <div style={{ display: 'flex', gap: activeTheme.spacing.space3 }}>
          <Button variant="primary">All Collections</Button>
          <Button variant="ghost">My Collections</Button>
          <Button variant="ghost">Popular</Button>
          <Button variant="ghost">New</Button>
        </div>

        <Grid columns="repeat(auto-fill, minmax(350px, 1fr))" gap="md">
          {collections.map((collection) => (
            <Card key={collection.title} variant="elevated" padding="lg">
              <div style={{ display: 'flex', flexDirection: 'column', gap: activeTheme.spacing.space4 }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: activeTheme.spacing.space2, marginBottom: activeTheme.spacing.space2 }}>
                    <h3
                      style={{
                        fontFamily: activeTheme.typography.fontDisplay,
                        fontSize: activeTheme.typography.sizeLg,
                        fontWeight: activeTheme.typography.weightBold,
                        color: activeTheme.colors.text,
                      }}
                    >
                      {collection.title}
                    </h3>
                    {collection.verified && (
                      <Badge variant="success" size="sm">✓ Verified</Badge>
                    )}
                  </div>
                  <p
                    style={{
                      fontFamily: activeTheme.typography.fontBody,
                      fontSize: activeTheme.typography.sizeSm,
                      color: activeTheme.colors.textMuted,
                      lineHeight: activeTheme.typography.lineHeightRelaxed,
                    }}
                  >
                    {collection.description}
                  </p>
                </div>

                <div style={{ display: 'flex', gap: activeTheme.spacing.space2, flexWrap: 'wrap' }}>
                  <Badge variant="default" size="sm">{collection.items} items</Badge>
                  <Badge
                    variant={collection.difficulty === 'Advanced' ? 'error' : collection.difficulty === 'Intermediate' ? 'warning' : 'success'}
                    size="sm"
                  >
                    {collection.difficulty}
                  </Badge>
                </div>

                <div>
                  <div style={{ display: 'flex', gap: activeTheme.spacing.space2, flexWrap: 'wrap', marginBottom: activeTheme.spacing.space2 }}>
                    {collection.skills.slice(0, 3).map((skill) => (
                      <Badge key={skill} variant="primary" size="sm">{skill}</Badge>
                    ))}
                    {collection.skills.length > 3 && (
                      <Badge variant="default" size="sm">+{collection.skills.length - 3}</Badge>
                    )}
                  </div>
                </div>

                {collection.completion > 0 && (
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: activeTheme.spacing.space1 }}>
                      <span style={{ fontFamily: activeTheme.typography.fontMono, fontSize: activeTheme.typography.sizeXs, color: activeTheme.colors.textMuted }}>
                        Progress
                      </span>
                      <span style={{ fontFamily: activeTheme.typography.fontMono, fontSize: activeTheme.typography.sizeXs, color: activeTheme.colors.textMuted }}>
                        {collection.completion}%
                      </span>
                    </div>
                    <Progress value={collection.completion} size="sm" />
                  </div>
                )}

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: activeTheme.spacing.space2 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: activeTheme.spacing.space2 }}>
                    <Avatar name={collection.author} size="sm" />
                    <span style={{ fontFamily: activeTheme.typography.fontBody, fontSize: activeTheme.typography.sizeXs, color: activeTheme.colors.textMuted }}>
                      {collection.author}
                    </span>
                  </div>
                  <Button variant={collection.completion > 0 ? 'secondary' : 'primary'} size="sm">
                    {collection.completion > 0 ? 'Continue' : 'Start'}
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </Grid>

        <Card variant="outlined" padding="lg">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h3
                style={{
                  fontFamily: activeTheme.typography.fontDisplay,
                  fontSize: activeTheme.typography.sizeLg,
                  fontWeight: activeTheme.typography.weightBold,
                  color: activeTheme.colors.text,
                }}
              >
                Create Your Own Collection
              </h3>
              <p
                style={{
                  fontFamily: activeTheme.typography.fontBody,
                  fontSize: activeTheme.typography.sizeSm,
                  color: activeTheme.colors.textMuted,
                }}
              >
                Package your expertise into practice sets for others
              </p>
            </div>
            <Button variant="secondary">Start Creating</Button>
          </div>
        </Card>
      </Section>
    </Page>
  );
}
