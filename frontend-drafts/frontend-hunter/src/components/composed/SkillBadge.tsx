import { Badge } from "@/components/primitives";

type SkillLevel = "novice" | "developing" | "proficient" | "advanced" | "expert";

interface SkillBadgeProps {
  name: string;
  level?: SkillLevel;
  score?: number;
  compact?: boolean;
}

const levelConfig: Record<
  SkillLevel,
  { label: string; variant: "default" | "accent" | "success" | "warning" | "info" }
> = {
  novice: { label: "Novice", variant: "default" },
  developing: { label: "Developing", variant: "info" },
  proficient: { label: "Proficient", variant: "accent" },
  advanced: { label: "Advanced", variant: "success" },
  expert: { label: "Expert", variant: "success" },
};

export function SkillBadge({ name, level, score, compact = false }: SkillBadgeProps) {
  if (compact) {
    return (
      <div
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "var(--spacing-2)",
          padding: "var(--spacing-1) var(--spacing-3)",
          backgroundColor: "var(--color-bg-tertiary)",
          border: "1px solid var(--color-border-subtle)",
          borderRadius: "var(--radius-full)",
        }}
      >
        <span
          style={{
            fontSize: "var(--font-size-sm)",
            color: "var(--color-text-primary)",
          }}
        >
          {name}
        </span>
        {score !== undefined && (
          <span
            style={{
              fontSize: "var(--font-size-xs)",
              fontWeight: "var(--font-weight-semibold)",
              color: "var(--color-accent-primary)",
              fontVariantNumeric: "tabular-nums",
            }}
          >
            {score}
          </span>
        )}
      </div>
    );
  }

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "var(--spacing-3)",
      }}
    >
      <span
        style={{
          fontSize: "var(--font-size-base)",
          color: "var(--color-text-primary)",
          flex: 1,
        }}
      >
        {name}
      </span>
      {level && (
        <Badge variant={levelConfig[level].variant} size="sm" dot>
          {levelConfig[level].label}
        </Badge>
      )}
      {score !== undefined && (
        <span
          style={{
            fontSize: "var(--font-size-sm)",
            fontWeight: "var(--font-weight-semibold)",
            color: "var(--color-accent-primary)",
            fontVariantNumeric: "tabular-nums",
            minWidth: 28,
            textAlign: "right",
          }}
        >
          {score}
        </span>
      )}
    </div>
  );
}
