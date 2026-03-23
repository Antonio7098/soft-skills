import { Page } from "@/components/layout";
import {
  StatCard,
  ProgressRing,
  SkillBadge,
  StatusIndicator,
} from "@/components/composed";
import { Card, Badge, Button, Progress } from "@/components/primitives";

const recentActivity = [
  {
    id: "1",
    title: "Stakeholder Negotiation",
    type: "Scenario",
    score: 82,
    time: "2 hours ago",
    status: "success" as const,
  },
  {
    id: "2",
    title: "Active Listening Interview",
    type: "Interview",
    score: 74,
    time: "Yesterday",
    status: "success" as const,
  },
  {
    id: "3",
    title: "Conflict Resolution",
    type: "Quick Practice",
    score: null,
    time: "2 days ago",
    status: "loading" as const,
  },
];

const topSkills = [
  { name: "Active Listening", score: 78, level: "proficient" as const },
  { name: "Stakeholder Management", score: 72, level: "developing" as const },
  { name: "Concise Communication", score: 65, level: "developing" as const },
  { name: "Empathy", score: 81, level: "proficient" as const },
];

const recommendedCollections = [
  {
    id: "1",
    title: "Difficult Conversations",
    skill: "Conflict Handling",
    items: 12,
    difficulty: "Advanced",
  },
  {
    id: "2",
    title: "Client Discovery Calls",
    skill: "Active Listening",
    items: 8,
    difficulty: "Intermediate",
  },
  {
    id: "3",
    title: "Executive Summaries",
    skill: "Concise Communication",
    items: 6,
    difficulty: "Intermediate",
  },
];

export function DashboardPage() {
  return (
    <Page
      title="Dashboard"
      subtitle="Track your competency growth and pick up where you left off."
      actions={
        <Button variant="primary" size="md">
          Start Practice
        </Button>
      }
    >
      {/* Stats row */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: "var(--spacing-4)",
        }}
      >
        <StatCard
          label="Attempts"
          value="47"
          change={{ value: 12, direction: "up" }}
          accent
          className="stagger-1"
        />
        <StatCard
          label="Avg Score"
          value="76"
          change={{ value: 4, direction: "up" }}
          className="stagger-2"
        />
        <StatCard
          label="Skills Practiced"
          value="12"
          className="stagger-3"
        />
        <StatCard
          label="Streak"
          value="5d"
          change={{ value: 0, direction: "neutral" }}
          className="stagger-4"
        />
      </div>

      {/* Main content grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "var(--spacing-6)",
        }}
      >
        {/* Competency overview */}
        <Card variant="default" padding="lg">
          <h2
            style={{
              fontFamily: "var(--font-display)",
              fontSize: "var(--font-size-2xl)",
              marginBottom: "var(--spacing-6)",
              color: "var(--color-text-primary)",
            }}
          >
            Competencies
          </h2>
          <div
            style={{
              display: "flex",
              justifyContent: "space-around",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "var(--spacing-6)",
            }}
          >
            <ProgressRing value={72} size={100} label="Communication" />
            <ProgressRing
              value={65}
              size={100}
              label="Teamwork"
              color="var(--color-status-success)"
            />
            <ProgressRing
              value={58}
              size={100}
              label="Leadership"
              color="var(--color-status-warning)"
            />
          </div>
        </Card>

        {/* Top skills */}
        <Card variant="default" padding="lg">
          <h2
            style={{
              fontFamily: "var(--font-display)",
              fontSize: "var(--font-size-2xl)",
              marginBottom: "var(--spacing-6)",
              color: "var(--color-text-primary)",
            }}
          >
            Top Skills
          </h2>
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "var(--spacing-4)",
            }}
          >
            {topSkills.map((skill, i) => (
              <div
                key={skill.name}
                className={`stagger-${i + 1}`}
                style={{ animation: "fadeInUp var(--transition-slow) both" }}
              >
                <SkillBadge
                  name={skill.name}
                  level={skill.level}
                  score={skill.score}
                />
                <div style={{ marginTop: "var(--spacing-2)" }}>
                  <Progress
                    value={skill.score}
                    size="sm"
                    color={
                      skill.score >= 80
                        ? "var(--color-status-success)"
                        : skill.score >= 60
                          ? "var(--color-accent-primary)"
                          : "var(--color-status-warning)"
                    }
                  />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Bottom grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "var(--spacing-6)",
        }}
      >
        {/* Recent activity */}
        <Card variant="default" padding="lg">
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "var(--spacing-5)",
            }}
          >
            <h2
              style={{
                fontFamily: "var(--font-display)",
                fontSize: "var(--font-size-2xl)",
                color: "var(--color-text-primary)",
              }}
            >
              Recent Activity
            </h2>
            <Button variant="ghost" size="sm">
              View All
            </Button>
          </div>
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "var(--spacing-3)",
            }}
          >
            {recentActivity.map((item, i) => (
              <div
                key={item.id}
                className={`stagger-${i + 1}`}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "var(--spacing-4)",
                  padding: "var(--spacing-3)",
                  borderRadius: "var(--radius-md)",
                  transition: "background-color var(--transition-normal)",
                  cursor: "pointer",
                  animation: "fadeInUp var(--transition-slow) both",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor =
                    "var(--color-surface-hover)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = "transparent";
                }}
              >
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "var(--spacing-2)",
                      marginBottom: "var(--spacing-1)",
                    }}
                  >
                    <span
                      style={{
                        fontSize: "var(--font-size-base)",
                        fontWeight: "var(--font-weight-medium)",
                        color: "var(--color-text-primary)",
                      }}
                    >
                      {item.title}
                    </span>
                    <Badge variant="default" size="sm">
                      {item.type}
                    </Badge>
                  </div>
                  <span
                    style={{
                      fontSize: "var(--font-size-xs)",
                      color: "var(--color-text-tertiary)",
                    }}
                  >
                    {item.time}
                  </span>
                </div>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "var(--spacing-3)",
                  }}
                >
                  {item.score !== null ? (
                    <span
                      style={{
                        fontFamily: "var(--font-display)",
                        fontSize: "var(--font-size-xl)",
                        color: "var(--color-accent-primary)",
                        fontVariantNumeric: "tabular-nums",
                      }}
                    >
                      {item.score}
                    </span>
                  ) : (
                    <StatusIndicator
                      status={item.status}
                      label="Assessing"
                      size="sm"
                    />
                  )}
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Recommended collections */}
        <Card variant="default" padding="lg">
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "var(--spacing-5)",
            }}
          >
            <h2
              style={{
                fontFamily: "var(--font-display)",
                fontSize: "var(--font-size-2xl)",
                color: "var(--color-text-primary)",
              }}
            >
              Recommended
            </h2>
            <Button variant="ghost" size="sm">
              Browse
            </Button>
          </div>
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "var(--spacing-3)",
            }}
          >
            {recommendedCollections.map((collection, i) => (
              <div
                key={collection.id}
                className={`stagger-${i + 1}`}
                style={{
                  padding: "var(--spacing-4)",
                  borderRadius: "var(--radius-md)",
                  border: "1px solid var(--color-border-subtle)",
                  transition: "all var(--transition-normal)",
                  cursor: "pointer",
                  animation: "fadeInUp var(--transition-slow) both",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor =
                    "var(--color-accent-primary)";
                  e.currentTarget.style.backgroundColor =
                    "var(--color-surface-hover)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor =
                    "var(--color-border-subtle)";
                  e.currentTarget.style.backgroundColor = "transparent";
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "flex-start",
                    marginBottom: "var(--spacing-2)",
                  }}
                >
                  <span
                    style={{
                      fontSize: "var(--font-size-base)",
                      fontWeight: "var(--font-weight-medium)",
                      color: "var(--color-text-primary)",
                    }}
                  >
                    {collection.title}
                  </span>
                  <Badge variant="accent" size="sm">
                    {collection.difficulty}
                  </Badge>
                </div>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "var(--spacing-3)",
                  }}
                >
                  <span
                    style={{
                      fontSize: "var(--font-size-xs)",
                      color: "var(--color-text-tertiary)",
                    }}
                  >
                    {collection.skill}
                  </span>
                  <span
                    style={{
                      fontSize: "var(--font-size-xs)",
                      color: "var(--color-text-tertiary)",
                    }}
                  >
                    {collection.items} items
                  </span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </Page>
  );
}
