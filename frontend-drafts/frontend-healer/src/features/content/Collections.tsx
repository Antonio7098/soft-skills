import { Card, Text, Badge, Tag, Progress, Button } from '../../components';

const collections = [
  {
    id: '1',
    title: 'Consultancy Fundamentals',
    description: 'Core skills every consultant needs: stakeholder communication, structured thinking, and managing expectations.',
    itemCount: 12,
    difficulty: 'Beginner',
    skills: ['Communication', 'Stakeholder Management', 'Structured Thinking'],
    estimatedTime: '2 hours',
    progress: 65,
    verified: true,
  },
  {
    id: '2',
    title: 'Behavioural Interview Prep',
    description: 'STAR method practice for common behavioural questions. Covers leadership, teamwork, and conflict scenarios.',
    itemCount: 18,
    difficulty: 'Intermediate',
    skills: ['Professionalism', 'Problem Solving', 'Decision Justification'],
    estimatedTime: '3 hours',
    progress: 30,
    verified: true,
  },
  {
    id: '3',
    title: 'AI Delivery Under Pressure',
    description: 'High-stakes scenarios for AI and digital transformation projects. Navigate technical ambiguity and client expectations.',
    itemCount: 10,
    difficulty: 'Advanced',
    skills: ['Managing Ambiguity', 'Prioritization', 'Adaptability'],
    estimatedTime: '2.5 hours',
    progress: 0,
    verified: true,
  },
  {
    id: '4',
    title: 'Client Communication Mastery',
    description: 'From executive briefings to difficult conversations. Master the art of client-facing communication.',
    itemCount: 15,
    difficulty: 'Intermediate',
    skills: ['Concise Speaking', 'Empathy', 'Expectation Setting'],
    estimatedTime: '2.5 hours',
    progress: 45,
    verified: false,
  },
  {
    id: '5',
    title: 'Team Leadership Scenarios',
    description: 'Navigate team dynamics, facilitate decisions, and handle interpersonal challenges in technical teams.',
    itemCount: 8,
    difficulty: 'Advanced',
    skills: ['Leadership', 'Teamwork', 'Conflict Handling'],
    estimatedTime: '1.5 hours',
    progress: 0,
    verified: false,
  },
  {
    id: '6',
    title: 'Quick Wins: Daily Practice',
    description: 'Short, focused exercises for building consistent habits. Each session takes under 5 minutes.',
    itemCount: 20,
    difficulty: 'Beginner',
    skills: ['Active Listening', 'Concise Speaking', 'Structured Thinking'],
    estimatedTime: '1.5 hours',
    progress: 80,
    verified: true,
  },
];

const difficultyColor: Record<string, 'success' | 'info' | 'warning'> = {
  Beginner: 'success',
  Intermediate: 'info',
  Advanced: 'warning',
};

/**
 * Collections - Browse and discover practice collections.
 */
export function Collections() {
  return (
    <div>
      <div style={{ marginBottom: 'var(--space-8)' }}>
        <Text variant="display" style={{ marginBottom: 'var(--space-2)' }}>
          Collections
        </Text>
        <Text variant="body" color="secondary">
          Curated practice content organized by theme, skill level, and learning objectives.
        </Text>
      </div>

      {/* Filter bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--space-3)',
        marginBottom: 'var(--space-6)',
        paddingBottom: 'var(--space-4)',
        borderBottom: '1px solid var(--color-border-subtle)',
      }}>
        <Text variant="caption" color="tertiary" style={{ marginRight: 'var(--space-2)' }}>
          Filter:
        </Text>
        {['All', 'Beginner', 'Intermediate', 'Advanced'].map((filter, i) => (
          <button
            key={filter}
            style={{
              fontFamily: 'var(--font-body)',
              fontSize: 'var(--font-size-small)',
              fontWeight: i === 0 ? 500 : 400,
              color: i === 0 ? 'var(--color-fg-primary)' : 'var(--color-fg-secondary)',
              backgroundColor: i === 0 ? 'var(--color-bg-tertiary)' : 'transparent',
              border: 'none',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--space-2) var(--space-3)',
              cursor: 'pointer',
            }}
          >
            {filter}
          </button>
        ))}
      </div>

      {/* Collections grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: 'var(--space-5)',
      }}>
        {collections.map((collection) => (
          <Card key={collection.id} variant="default" padding="lg" interactive>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
              {/* Header */}
              <div style={{
                display: 'flex',
                alignItems: 'flex-start',
                justifyContent: 'space-between',
              }}>
                <Badge variant={difficultyColor[collection.difficulty]} size="sm">
                  {collection.difficulty}
                </Badge>
                {collection.verified && (
                  <Badge variant="success" size="sm" dot>
                    Verified
                  </Badge>
                )}
              </div>

              {/* Content */}
              <div>
                <Text variant="subheading" style={{ marginBottom: 'var(--space-2)' }}>
                  {collection.title}
                </Text>
                <Text variant="bodySmall" color="secondary" lineClamp={3}>
                  {collection.description}
                </Text>
              </div>

              {/* Meta */}
              <div style={{
                display: 'flex',
                gap: 'var(--space-4)',
                paddingTop: 'var(--space-2)',
              }}>
                <Text variant="caption" color="tertiary">
                  {collection.itemCount} items
                </Text>
                <Text variant="caption" color="tertiary">
                  {collection.estimatedTime}
                </Text>
              </div>

              {/* Skills */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-1)' }}>
                {collection.skills.map((skill) => (
                  <Tag key={skill} size="sm">{skill}</Tag>
                ))}
              </div>

              {/* Progress */}
              {collection.progress > 0 && (
                <div style={{ paddingTop: 'var(--space-2)' }}>
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    marginBottom: 'var(--space-2)',
                  }}>
                    <Text variant="caption" color="tertiary">Progress</Text>
                    <Text variant="mono" color="tertiary" style={{ fontSize: 'var(--font-size-small)' }}>
                      {collection.progress}%
                    </Text>
                  </div>
                  <Progress value={collection.progress} size="sm" />
                </div>
              )}

              {/* Action */}
              <Button
                variant="secondary"
                fullWidth
                style={{ marginTop: 'var(--space-2)' }}
              >
                {collection.progress > 0 ? 'Continue' : 'Start Collection'}
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
