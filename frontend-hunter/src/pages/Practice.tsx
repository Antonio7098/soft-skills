import { useState } from "react";
import { Page } from "@/components/layout";
import { Card, Badge, Button, Textarea, Progress } from "@/components/primitives";
import { StatusIndicator, SkillBadge } from "@/components/composed";

const scenario = {
  title: "Unhappy Stakeholder",
  context: "Sprint 14 Demo",
  difficulty: "Advanced",
  skills: ["Conflict Handling", "Empathy", "Stakeholder Management"],
  scenario: `You're presenting the sprint 14 demo to the product steering committee. Midway through, the VP of Sales interrupts and says: "This isn't what we asked for. The pipeline dashboard is completely missing — we needed it for the Q3 board review next week. I don't understand why engineering keeps deprioritizing what actually matters."

The room goes quiet. Your engineering lead shifts uncomfortably. The PM next to you whispers: "We flagged this risk two sprints ago, but Sales never confirmed the priority trade-off."`,
  task: "Respond to the VP of Sales in a way that de-escalates the tension, acknowledges their concern, and proposes a concrete path forward. Consider the competing priorities in the room.",
};

const practiceHistory = [
  { label: "Attempt 1", score: 62, date: "Mar 10" },
  { label: "Attempt 2", score: 71, date: "Mar 12" },
];

export function PracticePage() {
  const [response, setResponse] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [assessing, setAssessing] = useState(false);

  const handleSubmit = () => {
    if (!response.trim()) return;
    setSubmitted(true);
    setAssessing(true);
    setTimeout(() => setAssessing(false), 3000);
  };

  return (
    <Page
      title="Practice"
      subtitle="Work through realistic scenarios and get rubric-based feedback."
    >
      {/* Scenario card */}
      <Card
        variant="elevated"
        padding="lg"
        style={{ animation: "fadeInUp var(--transition-slow) both" }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            marginBottom: "var(--spacing-5)",
          }}
        >
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "var(--spacing-2)",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "var(--spacing-3)",
              }}
            >
              <Badge variant="accent" size="sm">
                Scenario
              </Badge>
              <Badge variant="warning" size="sm">
                {scenario.difficulty}
              </Badge>
            </div>
            <h2
              style={{
                fontFamily: "var(--font-display)",
                fontSize: "var(--font-size-3xl)",
                color: "var(--color-text-primary)",
              }}
            >
              {scenario.title}
            </h2>
            <span
              style={{
                fontSize: "var(--font-size-sm)",
                color: "var(--color-text-tertiary)",
              }}
            >
              Context: {scenario.context}
            </span>
          </div>
          <div
            style={{
              display: "flex",
              gap: "var(--spacing-2)",
              flexWrap: "wrap",
            }}
          >
            {scenario.skills.map((skill) => (
              <SkillBadge key={skill} name={skill} compact />
            ))}
          </div>
        </div>

        {/* Scenario text */}
        <div
          style={{
            padding: "var(--spacing-5)",
            backgroundColor: "var(--color-bg-tertiary)",
            borderRadius: "var(--radius-md)",
            borderLeft: "3px solid var(--color-accent-primary)",
            marginBottom: "var(--spacing-5)",
          }}
        >
          <p
            style={{
              fontSize: "var(--font-size-base)",
              color: "var(--color-text-primary)",
              lineHeight: "var(--line-height-relaxed)",
              whiteSpace: "pre-line",
            }}
          >
            {scenario.scenario}
          </p>
        </div>

        {/* Task */}
        <div
          style={{
            padding: "var(--spacing-4)",
            backgroundColor: "var(--color-accent-muted)",
            borderRadius: "var(--radius-md)",
          }}
        >
          <span
            style={{
              fontSize: "var(--font-size-xs)",
              fontWeight: "var(--font-weight-semibold)",
              color: "var(--color-accent-primary)",
              letterSpacing: "var(--letter-spacing-wider)",
              textTransform: "uppercase",
              display: "block",
              marginBottom: "var(--spacing-1)",
            }}
          >
            Your Task
          </span>
          <p
            style={{
              fontSize: "var(--font-size-base)",
              color: "var(--color-text-primary)",
              lineHeight: "var(--line-height-relaxed)",
            }}
          >
            {scenario.task}
          </p>
        </div>
      </Card>

      {/* Response area */}
      <Card
        variant="default"
        padding="lg"
        style={{ animation: "fadeInUp var(--transition-slow) both", animationDelay: "100ms" }}
      >
        <h3
          style={{
            fontFamily: "var(--font-display)",
            fontSize: "var(--font-size-xl)",
            color: "var(--color-text-primary)",
            marginBottom: "var(--spacing-4)",
          }}
        >
          Your Response
        </h3>

        {!submitted ? (
          <>
            <Textarea
              value={response}
              onChange={(e) => setResponse(e.target.value)}
              placeholder="Write your response here. Speak as you would in the actual situation..."
              minRows={6}
              hint="Write naturally — this is practice for real conversations."
            />
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginTop: "var(--spacing-4)",
              }}
            >
              <span
                style={{
                  fontSize: "var(--font-size-xs)",
                  color: "var(--color-text-tertiary)",
                }}
              >
                {response.length} characters
              </span>
              <div style={{ display: "flex", gap: "var(--spacing-3)" }}>
                <Button variant="ghost" size="md">
                  Save Draft
                </Button>
                <Button
                  variant="primary"
                  size="md"
                  onClick={handleSubmit}
                  disabled={!response.trim()}
                >
                  Submit for Assessment
                </Button>
              </div>
            </div>
          </>
        ) : (
          <div>
            <div
              style={{
                padding: "var(--spacing-4)",
                backgroundColor: "var(--color-bg-tertiary)",
                borderRadius: "var(--radius-md)",
                marginBottom: "var(--spacing-4)",
              }}
            >
              <p
                style={{
                  fontSize: "var(--font-size-base)",
                  color: "var(--color-text-primary)",
                  lineHeight: "var(--line-height-relaxed)",
                  whiteSpace: "pre-line",
                }}
              >
                {response}
              </p>
            </div>

            {assessing ? (
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  gap: "var(--spacing-4)",
                  padding: "var(--spacing-8)",
                }}
              >
                <StatusIndicator status="loading" label="Assessing Response" size="lg" pulse />
                <Progress value={65} size="md" color="var(--color-accent-primary)" style={{ width: 200 }} />
                <span
                  style={{
                    fontSize: "var(--font-size-sm)",
                    color: "var(--color-text-tertiary)",
                  }}
                >
                  Rubric-based evaluation in progress...
                </span>
              </div>
            ) : (
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  gap: "var(--spacing-4)",
                  padding: "var(--spacing-6)",
                }}
              >
                <StatusIndicator status="success" label="Assessment Complete" size="lg" />
                <Button variant="primary" size="lg" onClick={() => { setSubmitted(false); setResponse(""); }}>
                  View Detailed Feedback
                </Button>
              </div>
            )}
          </div>
        )}
      </Card>

      {/* Previous attempts */}
      {practiceHistory.length > 0 && (
        <Card
          variant="default"
          padding="lg"
          style={{ animation: "fadeInUp var(--transition-slow) both", animationDelay: "200ms" }}
        >
          <h3
            style={{
              fontFamily: "var(--font-display)",
              fontSize: "var(--font-size-xl)",
              color: "var(--color-text-primary)",
              marginBottom: "var(--spacing-4)",
            }}
          >
            Previous Attempts
          </h3>
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "var(--spacing-3)",
            }}
          >
            {practiceHistory.map((attempt, i) => (
              <div
                key={i}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "var(--spacing-3)",
                  borderRadius: "var(--radius-md)",
                  backgroundColor: "var(--color-bg-tertiary)",
                }}
              >
                <span
                  style={{
                    fontSize: "var(--font-size-sm)",
                    color: "var(--color-text-secondary)",
                  }}
                >
                  {attempt.label}
                </span>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "var(--spacing-4)",
                  }}
                >
                  <span
                    style={{
                      fontSize: "var(--font-size-xs)",
                      color: "var(--color-text-tertiary)",
                    }}
                  >
                    {attempt.date}
                  </span>
                  <span
                    style={{
                      fontFamily: "var(--font-display)",
                      fontSize: "var(--font-size-xl)",
                      color: "var(--color-accent-primary)",
                      fontVariantNumeric: "tabular-nums",
                    }}
                  >
                    {attempt.score}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </Page>
  );
}
