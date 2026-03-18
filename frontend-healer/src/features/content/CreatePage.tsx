import { Card, Text, Button, Badge, Tag, Stack } from '../../components';

const creationMethods = [
  {
    id: 'form',
    title: 'Structured Form',
    description: 'Create content step by step with guided fields and AI suggestions.',
    icon: '⊞',
    recommended: true,
  },
  {
    id: 'chat',
    title: 'Chat Generation',
    description: 'Describe what you want in natural language and let AI generate a draft.',
    icon: '◉',
    recommended: false,
  },
  {
    id: 'manual',
    title: 'Manual Creation',
    description: 'Build content from scratch with full control over every detail.',
    icon: '✎',
    recommended: false,
  },
];

const recentDrafts = [
  {
    title: 'AI Ethics Dilemma Collection',
    status: 'draft',
    items: 5,
    lastEdited: '2 hours ago',
    skills: ['Professionalism', 'Decision Justification'],
  },
  {
    title: 'Startup Pivot Scenarios',
    status: 'review',
    items: 8,
    lastEdited: 'Yesterday',
    skills: ['Adaptability', 'Prioritization', 'Communication'],
  },
  {
    title: 'Enterprise Client Walkthrough',
    status: 'draft',
    items: 3,
    lastEdited: '3 days ago',
    skills: ['Stakeholder Management', 'Executive Summary'],
  },
];

const statusColors: Record<string, 'default' | 'warning' | 'success'> = {
  draft: 'default',
  review: 'warning',
  published: 'success',
};

/**
 * Create - Content authoring page.
 */
export function CreatePage() {
  return (
    <div>
      <div style={{ marginBottom: 'var(--space-8)' }}>
        <Text variant="display" style={{ marginBottom: 'var(--space-2)' }}>
          Create Content
        </Text>
        <Text variant="body" color="secondary">
          Build practice collections, scenarios, and interview questions. Use AI assistance or create manually.
        </Text>
      </div>

      {/* Creation methods */}
      <div style={{ marginBottom: 'var(--space-10)' }}>
        <Text variant="subheading" style={{ marginBottom: 'var(--space-4)' }}>
          How would you like to create?
        </Text>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: 'var(--space-4)',
        }}>
          {creationMethods.map((method) => (
            <Card
              key={method.id}
              variant={method.recommended ? 'elevated' : 'default'}
              padding="lg"
              interactive
            >
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}>
                  <span style={{
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
                    {method.icon}
                  </span>
                  {method.recommended && (
                    <Badge variant="accent" size="sm">Recommended</Badge>
                  )}
                </div>
                <div>
                  <Text variant="body" style={{ fontWeight: 600, marginBottom: 'var(--space-1)' }}>
                    {method.title}
                  </Text>
                  <Text variant="bodySmall" color="secondary">
                    {method.description}
                  </Text>
                </div>
                <Button variant="secondary" size="sm">
                  Start Creating
                </Button>
              </div>
            </Card>
          ))}
        </div>
      </div>

      {/* Recent drafts */}
      <div>
        <Text variant="subheading" style={{ marginBottom: 'var(--space-4)' }}>
          Recent Drafts
        </Text>
        <Stack gap="var(--space-3)">
          {recentDrafts.map((draft, i) => (
            <Card key={i} variant="default" padding="md" interactive>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--space-4)',
              }}>
                <div style={{ flex: 1 }}>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 'var(--space-2)',
                    marginBottom: 'var(--space-1)',
                  }}>
                    <Text variant="body" style={{ fontWeight: 600 }}>
                      {draft.title}
                    </Text>
                    <Badge variant={statusColors[draft.status]} size="sm">
                      {draft.status}
                    </Badge>
                  </div>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 'var(--space-4)',
                  }}>
                    <Text variant="caption" color="tertiary">
                      {draft.items} items
                    </Text>
                    <Text variant="caption" color="tertiary">
                      Edited {draft.lastEdited}
                    </Text>
                    <div style={{ display: 'flex', gap: 'var(--space-1)' }}>
                      {draft.skills.map((skill) => (
                        <Tag key={skill} size="sm">{skill}</Tag>
                      ))}
                    </div>
                  </div>
                </div>
                <Button size="sm" variant="ghost">
                  Continue
                </Button>
              </div>
            </Card>
          ))}
        </Stack>
      </div>
    </div>
  );
}
