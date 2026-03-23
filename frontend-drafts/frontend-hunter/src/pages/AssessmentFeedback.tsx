import { Page } from "@/components/layout";
import { Card, Button, Progress } from "@/components/primitives";
import {
  ProgressRing,
  StatusIndicator,
} from "@/components/composed";

const assessment = {
  scenario: "Unhappy Stakeholder — Sprint 14 Demo",
  overallScore: 78,
  date: "March 14, 2026",
  rubric: "Stakeholder Communication v2.1",
  model: "gpt-4o-2024-11-20",
  status: "validated",
};

const skillScores = [
  { name: "Conflict Handling", score: 82, evidence: "Acknowledged the VP's frustration directly without being defensive. Proposed a structured follow-up meeting rather than debating in the demo." },
  { name: "Empathy", score: 76, evidence: "Recognized the Sales team's business pressure. Validated their need for the pipeline dashboard, though could have been more specific about impact." },
  { name: "Stakeholder Management", score: 74, evidence: "Brought in the PM's context about the flagged risk. Could improve by proactively owning the communication gap rather than referencing the PM." },
  { name: "Concise Communication", score: 80, evidence: "Kept response focused and actionable. Clear structure: acknowledge, clarify, propose." },
];

const strengths = [
  "Direct acknowledgment of the concern without being defensive",
  "Clear proposal for a follow-up meeting with specific timeline",
  "Good use of framing to bring the room back to a constructive place",
];

const weaknesses = [
  "Could have been more specific about the trade-off that was made",
  "Missed opportunity to reference the documented risk flag directly",
  "Response could have included a concrete short-term workaround",
];

const nextActions = [
  "Practice acknowledging concerns with specific business impact language",
  "Work on owning communication gaps rather than deflecting to others",
  "Try scenarios with multiple competing stakeholders in the room",
];

export function AssessmentFeedbackPage() {
  return (
    <Page
      title="Assessment Feedback"
      subtitle="Understand your score, what drove it, and how to improve."
    >
      {/* Score overview */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "auto 1fr",
          gap: "var(--spacing-6)",
          animation: "fadeInUp var(--transition-slow) both",
        }}
      >
        <Card
          variant="elevated"
          padding="lg"
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "var(--spacing-4)",
            minWidth: 220,
          }}
        >
          <ProgressRing
            value={assessment.overallScore}
            size={120}
            strokeWidth={8}
            label="Overall Score"
          />
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: "var(--spacing-2)",
            }}
          >
            <StatusIndicator status="success" label="Validated" />
            <span
              style={{
                fontSize: "var(--font-size-xs)",
                color: "var(--color-text-tertiary)",
              }}
            >
              {assessment.date}
            </span>
          </div>
        </Card>

        <Card variant="default" padding="lg">
          <h2
            style={{
              fontFamily: "var(--font-display)",
              fontSize: "var(--font-size-2xl)",
              color: "var(--color-text-primary)",
              marginBottom: "var(--spacing-4)",
            }}
          >
            {assessment.scenario}
          </h2>
          <div
            style={{
              display: "flex",
              gap: "var(--spacing-4)",
              flexWrap: "wrap",
              marginBottom: "var(--spacing-5)",
            }}
          >
            <Meta label="Rubric" value={assessment.rubric} />
            <Meta label="Model" value={assessment.model} />
          </div>

          {/* Skill breakdown */}
          <h3
            style={{
              fontSize: "var(--font-size-sm)",
              fontWeight: "var(--font-weight-semibold)",
              color: "var(--color-text-secondary)",
              letterSpacing: "var(--letter-spacing-wider)",
              textTransform: "uppercase",
              marginBottom: "var(--spacing-4)",
            }}
          >
            Skill Breakdown
          </h3>
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "var(--spacing-4)",
            }}
          >
            {skillScores.map((skill, i) => (
              <div
                key={skill.name}
                className={`stagger-${i + 1}`}
                style={{
                  animation: "fadeInUp var(--transition-slow) both",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: "var(--spacing-1)",
                  }}
                >
                  <span
                    style={{
                      fontSize: "var(--font-size-sm)",
                      fontWeight: "var(--font-weight-medium)",
                      color: "var(--color-text-primary)",
                    }}
                  >
                    {skill.name}
                  </span>
                  <span
                    style={{
                      fontFamily: "var(--font-display)",
                      fontSize: "var(--font-size-lg)",
                      color:
                        skill.score >= 80
                          ? "var(--color-status-success)"
                          : "var(--color-accent-primary)",
                      fontVariantNumeric: "tabular-nums",
                    }}
                  >
                    {skill.score}
                  </span>
                </div>
                <Progress
                  value={skill.score}
                  size="sm"
                  color={
                    skill.score >= 80
                      ? "var(--color-status-success)"
                      : "var(--color-accent-primary)"
                  }
                />
                <p
                  style={{
                    fontSize: "var(--font-size-xs)",
                    color: "var(--color-text-tertiary)",
                    marginTop: "var(--spacing-2)",
                    lineHeight: "var(--line-height-relaxed)",
                    paddingLeft: "var(--spacing-3)",
                    borderLeft: "2px solid var(--color-border-subtle)",
                  }}
                >
                  {skill.evidence}
                </p>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Feedback sections */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr 1fr",
          gap: "var(--spacing-5)",
        }}
      >
        <FeedbackSection
          title="Strengths"
          items={strengths}
          icon="strength"
          color="var(--color-status-success)"
          className="stagger-1"
        />
        <FeedbackSection
          title="Weaknesses"
          items={weaknesses}
          icon="weakness"
          color="var(--color-status-warning)"
          className="stagger-2"
        />
        <FeedbackSection
          title="Next Actions"
          items={nextActions}
          icon="action"
          color="var(--color-accent-primary)"
          className="stagger-3"
        />
      </div>

      {/* Actions */}
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          gap: "var(--spacing-4)",
          animation: "fadeIn var(--transition-slow) both",
        }}
      >
        <Button variant="outline" size="lg">
          Try Again
        </Button>
        <Button variant="secondary" size="lg">
          Practice Similar
        </Button>
        <Button variant="primary" size="lg">
          Next Practice
        </Button>
      </div>
    </Page>
  );
}

function FeedbackSection({
  title,
  items,
  color,
  className,
}: {
  title: string;
  items: string[];
  icon: string;
  color: string;
  className?: string;
}) {
  return (
    <Card
      variant="default"
      padding="lg"
      className={className}
      style={{ animation: "fadeInUp var(--transition-slow) both" }}
    >
      <h3
        style={{
          fontFamily: "var(--font-display)",
          fontSize: "var(--font-size-xl)",
          color: color,
          marginBottom: "var(--spacing-4)",
          display: "flex",
          alignItems: "center",
          gap: "var(--spacing-2)",
        }}
      >
        <span
          style={{
            width: 6,
            height: 6,
            borderRadius: "50%",
            backgroundColor: color,
            display: "inline-block",
          }}
        />
        {title}
      </h3>
      <ul
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "var(--spacing-3)",
        }}
      >
        {items.map((item, i) => (
          <li
            key={i}
            style={{
              fontSize: "var(--font-size-sm)",
              color: "var(--color-text-secondary)",
              lineHeight: "var(--line-height-relaxed)",
              paddingLeft: "var(--spacing-4)",
              position: "relative",
            }}
          >
            <span
              style={{
                position: "absolute",
                left: 0,
                top: "0.5em",
                width: 4,
                height: 4,
                borderRadius: "50%",
                backgroundColor: "var(--color-border-strong)",
              }}
            />
            {item}
          </li>
        ))}
      </ul>
    </Card>
  );
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: "flex", gap: "var(--spacing-2)", alignItems: "center" }}>
      <span
        style={{
          fontSize: "var(--font-size-xs)",
          color: "var(--color-text-tertiary)",
          textTransform: "uppercase",
          letterSpacing: "var(--letter-spacing-wider)",
        }}
      >
        {label}:
      </span>
      <span
        style={{
          fontSize: "var(--font-size-sm)",
          color: "var(--color-text-secondary)",
        }}
      >
        {value}
      </span>
    </div>
  );
}
