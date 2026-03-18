import { useState } from "react";
import { Page } from "@/components/layout";
import { Card, Badge, Button, Input } from "@/components/primitives";
import { SkillBadge } from "@/components/composed";

const collections = [
  {
    id: "1",
    title: "Difficult Conversations",
    description:
      "Practice handling confrontational situations with empathy and clarity. Covers conflict de-escalation, giving critical feedback, and navigating disagreements.",
    skill: "Conflict Handling",
    competency: "Communication",
    items: 12,
    difficulty: "Advanced",
    verified: true,
    author: "SoftSkills Team",
    attempts: 1847,
    avgScore: 68,
  },
  {
    id: "2",
    title: "Client Discovery Calls",
    description:
      "Master the art of asking the right questions during initial client meetings. Build rapport, uncover needs, and establish trust.",
    skill: "Active Listening",
    competency: "Communication",
    items: 8,
    difficulty: "Intermediate",
    verified: true,
    author: "SoftSkills Team",
    attempts: 2341,
    avgScore: 74,
  },
  {
    id: "3",
    title: "Executive Summaries",
    description:
      "Distill complex technical topics into concise, compelling narratives for senior leadership audiences.",
    skill: "Concise Communication",
    competency: "Communication",
    items: 6,
    difficulty: "Intermediate",
    verified: false,
    author: "Sarah Chen",
    attempts: 956,
    avgScore: 61,
  },
  {
    id: "4",
    title: "Sprint Planning Facilitation",
    description:
      "Lead effective sprint planning sessions. Balance team capacity, negotiate scope, and maintain momentum.",
    skill: "Facilitation",
    competency: "Leadership",
    items: 10,
    difficulty: "Advanced",
    verified: true,
    author: "SoftSkills Team",
    attempts: 1203,
    avgScore: 71,
  },
  {
    id: "5",
    title: "Empathy in Tech",
    description:
      "Develop genuine empathy in technical conversations. Understand perspectives, validate concerns, and build bridges.",
    skill: "Empathy",
    competency: "Teamwork",
    items: 9,
    difficulty: "Beginner",
    verified: false,
    author: "James Wright",
    attempts: 678,
    avgScore: 79,
  },
  {
    id: "6",
    title: "Stakeholder Alignment",
    description:
      "Navigate complex stakeholder landscapes with competing priorities. Build consensus and drive alignment across groups.",
    skill: "Stakeholder Management",
    competency: "Leadership",
    items: 11,
    difficulty: "Advanced",
    verified: true,
    author: "SoftSkills Team",
    attempts: 1456,
    avgScore: 63,
  },
];

const difficultyVariant: Record<string, "default" | "accent" | "warning"> = {
  Beginner: "default",
  Intermediate: "accent",
  Advanced: "warning",
};

const filters = ["All", "Verified", "Beginner", "Intermediate", "Advanced"];

export function CollectionsPage() {
  const [activeFilter, setActiveFilter] = useState("All");

  const filtered = collections.filter((c) => {
    if (activeFilter === "All") return true;
    if (activeFilter === "Verified") return c.verified;
    return c.difficulty === activeFilter;
  });

  return (
    <Page
      title="Collections"
      subtitle="Browse curated practice sets organized by skill, difficulty, and theme."
      actions={
        <div style={{ display: "flex", gap: "var(--spacing-3)" }}>
          <Input
            placeholder="Search collections..."
            icon={<SearchIcon />}
            style={{ width: 260 }}
          />
          <Button variant="outline" size="md">
            Create
          </Button>
        </div>
      }
    >
      {/* Filters */}
      <div
        style={{
          display: "flex",
          gap: "var(--spacing-2)",
          animation: "fadeInUp var(--transition-slow) both",
        }}
      >
        {filters.map((f) => (
          <button
            key={f}
            onClick={() => setActiveFilter(f)}
            style={{
              padding: "var(--spacing-1) var(--spacing-3)",
              borderRadius: "var(--radius-full)",
              fontSize: "var(--font-size-sm)",
              fontWeight: "var(--font-weight-medium)",
              color:
                activeFilter === f
                  ? "var(--color-text-inverse)"
                  : "var(--color-text-secondary)",
              backgroundColor:
                activeFilter === f
                  ? "var(--color-accent-primary)"
                  : "var(--color-bg-tertiary)",
              border:
                activeFilter === f
                  ? "1px solid transparent"
                  : "1px solid var(--color-border-default)",
              cursor: "pointer",
              transition: "all var(--transition-normal)",
              fontFamily: "var(--font-body)",
            }}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))",
          gap: "var(--spacing-5)",
        }}
      >
        {filtered.map((collection, i) => (
          <Card
            key={collection.id}
            variant="default"
            padding="lg"
            hoverable
            className={`stagger-${(i % 6) + 1}`}
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "var(--spacing-4)",
              animation: "fadeInUp var(--transition-slow) both",
            }}
          >
            {/* Header */}
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "flex-start",
              }}
            >
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "var(--spacing-1)",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "var(--spacing-2)",
                  }}
                >
                  <span
                    style={{
                      fontFamily: "var(--font-display)",
                      fontSize: "var(--font-size-xl)",
                      color: "var(--color-text-primary)",
                    }}
                  >
                    {collection.title}
                  </span>
                  {collection.verified && (
                    <span
                      style={{
                        color: "var(--color-status-success)",
                        display: "flex",
                      }}
                      title="Verified"
                    >
                      <VerifiedIcon />
                    </span>
                  )}
                </div>
                <span
                  style={{
                    fontSize: "var(--font-size-xs)",
                    color: "var(--color-text-tertiary)",
                  }}
                >
                  by {collection.author}
                </span>
              </div>
              <Badge
                variant={difficultyVariant[collection.difficulty] || "default"}
                size="sm"
              >
                {collection.difficulty}
              </Badge>
            </div>

            {/* Description */}
            <p
              style={{
                fontSize: "var(--font-size-sm)",
                color: "var(--color-text-secondary)",
                lineHeight: "var(--line-height-relaxed)",
              }}
            >
              {collection.description}
            </p>

            {/* Skills */}
            <div
              style={{
                display: "flex",
                gap: "var(--spacing-2)",
                flexWrap: "wrap",
              }}
            >
              <SkillBadge name={collection.skill} compact />
              <SkillBadge name={collection.competency} compact />
            </div>

            {/* Meta */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                paddingTop: "var(--spacing-3)",
                borderTop: "1px solid var(--color-border-subtle)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  gap: "var(--spacing-5)",
                }}
              >
                <MetaItem label="Items" value={String(collection.items)} />
                <MetaItem
                  label="Attempts"
                  value={collection.attempts.toLocaleString()}
                />
                <MetaItem label="Avg Score" value={String(collection.avgScore)} />
              </div>
              <Button variant="ghost" size="sm">
                Practice
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </Page>
  );
}

function MetaItem({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
      <span
        style={{
          fontSize: "var(--font-size-xs)",
          color: "var(--color-text-tertiary)",
          textTransform: "uppercase",
          letterSpacing: "var(--letter-spacing-wider)",
        }}
      >
        {label}
      </span>
      <span
        style={{
          fontSize: "var(--font-size-sm)",
          fontWeight: "var(--font-weight-semibold)",
          color: "var(--color-text-primary)",
          fontVariantNumeric: "tabular-nums",
        }}
      >
        {value}
      </span>
    </div>
  );
}

function SearchIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
  );
}

function VerifiedIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
      <path d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
    </svg>
  );
}
