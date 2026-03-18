import { Page } from "@/components/layout";
import { Card, Badge, Progress, Button } from "@/components/primitives";
import { ProgressRing, SkillBadge } from "@/components/composed";

const competencyData = [
  {
    name: "Communication",
    score: 72,
    trend: "+6",
    skills: [
      { name: "Active Listening", score: 78, level: "proficient" as const },
      { name: "Concise Communication", score: 65, level: "developing" as const },
      { name: "Empathy", score: 81, level: "proficient" as const },
      { name: "Conflict Handling", score: 68, level: "developing" as const },
    ],
  },
  {
    name: "Leadership",
    score: 58,
    trend: "+3",
    skills: [
      { name: "Stakeholder Management", score: 72, level: "developing" as const },
      { name: "Decision Making", score: 55, level: "novice" as const },
      { name: "Facilitation", score: 60, level: "developing" as const },
      { name: "Delegation", score: 48, level: "novice" as const },
    ],
  },
  {
    name: "Teamwork",
    score: 65,
    trend: "+8",
    skills: [
      { name: "Collaboration", score: 70, level: "developing" as const },
      { name: "Giving Feedback", score: 62, level: "developing" as const },
      { name: "Receiving Feedback", score: 74, level: "proficient" as const },
      { name: "Trust Building", score: 58, level: "novice" as const },
    ],
  },
];

const progressHistory = [
  { date: "Week 1", score: 52 },
  { date: "Week 2", score: 55 },
  { date: "Week 3", score: 58 },
  { date: "Week 4", score: 61 },
  { date: "Week 5", score: 64 },
  { date: "Week 6", score: 66 },
  { date: "Week 7", score: 68 },
  { date: "Week 8", score: 72 },
];

export function ProgressPage() {
  const maxScore = Math.max(...progressHistory.map((h) => h.score));

  return (
    <Page
      title="Progress"
      subtitle="Track your competency growth over time. Progress reflects demonstrated performance, not activity volume."
      actions={
        <div style={{ display: "flex", gap: "var(--spacing-3)" }}>
          <Button variant="ghost" size="md">
            Export
          </Button>
          <Button variant="outline" size="md">
            History
          </Button>
        </div>
      }
    >
      {/* Overview rings */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
          gap: "var(--spacing-5)",
          animation: "fadeInUp var(--transition-slow) both",
        }}
      >
        {competencyData.map((comp, i) => (
          <Card
            key={comp.name}
            variant="default"
            padding="lg"
            className={`stagger-${i + 1}`}
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: "var(--spacing-3)",
              animation: "fadeInUp var(--transition-slow) both",
            }}
          >
            <ProgressRing
              value={comp.score}
              size={100}
              strokeWidth={6}
              color={
                comp.score >= 70
                  ? "var(--color-status-success)"
                  : comp.score >= 55
                    ? "var(--color-accent-primary)"
                    : "var(--color-status-warning)"
              }
            />
            <span
              style={{
                fontSize: "var(--font-size-sm)",
                fontWeight: "var(--font-weight-medium)",
                color: "var(--color-text-primary)",
              }}
            >
              {comp.name}
            </span>
            <span
              style={{
                fontSize: "var(--font-size-xs)",
                fontWeight: "var(--font-weight-semibold)",
                color: "var(--color-status-success)",
                fontVariantNumeric: "tabular-nums",
              }}
            >
              {comp.trend} this month
            </span>
          </Card>
        ))}
      </div>

      {/* Progress chart */}
      <Card
        variant="default"
        padding="lg"
        style={{ animation: "fadeInUp var(--transition-slow) both", animationDelay: "150ms" }}
      >
        <h2
          style={{
            fontFamily: "var(--font-display)",
            fontSize: "var(--font-size-2xl)",
            color: "var(--color-text-primary)",
            marginBottom: "var(--spacing-6)",
          }}
        >
          Overall Trend
        </h2>
        <div
          style={{
            display: "flex",
            alignItems: "flex-end",
            gap: "var(--spacing-3)",
            height: 200,
            padding: "0 var(--spacing-2)",
          }}
        >
          {progressHistory.map((point, i) => {
            const heightPct = (point.score / maxScore) * 100;
            return (
              <div
                key={point.date}
                style={{
                  flex: 1,
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  gap: "var(--spacing-2)",
                  height: "100%",
                  justifyContent: "flex-end",
                }}
              >
                <span
                  style={{
                    fontSize: "var(--font-size-xs)",
                    fontWeight: "var(--font-weight-semibold)",
                    color: "var(--color-accent-primary)",
                    fontVariantNumeric: "tabular-nums",
                  }}
                >
                  {point.score}
                </span>
                <div
                  style={{
                    width: "100%",
                    maxWidth: 40,
                    height: `${heightPct}%`,
                    minHeight: 4,
                    borderRadius: "var(--radius-sm) var(--radius-sm) 0 0",
                    backgroundColor:
                      i === progressHistory.length - 1
                        ? "var(--color-accent-primary)"
                        : "var(--color-bg-tertiary)",
                    border: `1px solid ${
                      i === progressHistory.length - 1
                        ? "var(--color-accent-primary)"
                        : "var(--color-border-default)"
                    }`,
                    transition: "all var(--transition-slow)",
                    animation: `fadeInUp var(--transition-slow) both`,
                    animationDelay: `${i * 50}ms`,
                  }}
                />
                <span
                  style={{
                    fontSize: "var(--font-size-xs)",
                    color: "var(--color-text-tertiary)",
                    whiteSpace: "nowrap",
                  }}
                >
                  {point.date}
                </span>
              </div>
            );
          })}
        </div>
      </Card>

      {/* Skill detail by competency */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "var(--spacing-5)",
        }}
      >
        {competencyData.map((comp, ci) => (
          <Card
            key={comp.name}
            variant="default"
            padding="lg"
            className={`stagger-${ci + 1}`}
            style={{ animation: "fadeInUp var(--transition-slow) both" }}
          >
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
                {comp.name}
              </h2>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "var(--spacing-3)",
                }}
              >
                <Badge variant="accent" size="sm">
                  Score: {comp.score}
                </Badge>
                <Badge variant="success" size="sm">
                  {comp.trend}
                </Badge>
              </div>
            </div>
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "var(--spacing-4)",
              }}
            >
              {comp.skills.map((skill) => (
                <div
                  key={skill.name}
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "var(--spacing-2)",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                    }}
                  >
                    <SkillBadge
                      name={skill.name}
                      level={skill.level}
                      score={skill.score}
                    />
                  </div>
                  <Progress
                    value={skill.score}
                    size="sm"
                    color={
                      skill.score >= 75
                        ? "var(--color-status-success)"
                        : skill.score >= 60
                          ? "var(--color-accent-primary)"
                          : "var(--color-status-warning)"
                    }
                  />
                </div>
              ))}
            </div>
          </Card>
        ))}
      </div>
    </Page>
  );
}
