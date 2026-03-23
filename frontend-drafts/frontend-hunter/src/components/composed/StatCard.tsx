import type { HTMLAttributes, ReactNode } from "react";
import { Card } from "@/components/primitives";

interface StatCardProps extends HTMLAttributes<HTMLDivElement> {
  label: string;
  value: string | number;
  change?: {
    value: number;
    direction: "up" | "down" | "neutral";
  };
  icon?: ReactNode;
  accent?: boolean;
}

export function StatCard({
  label,
  value,
  change,
  icon,
  accent = false,
  style,
  ...props
}: StatCardProps) {
  const changeColor =
    change?.direction === "up"
      ? "var(--color-status-success)"
      : change?.direction === "down"
        ? "var(--color-status-error)"
        : "var(--color-text-tertiary)";

  const changePrefix =
    change?.direction === "up" ? "+" : change?.direction === "down" ? "" : "";

  return (
    <Card variant="default" padding="md" style={{ ...style }} {...props}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          marginBottom: "var(--spacing-3)",
        }}
      >
        <span
          style={{
            fontSize: "var(--font-size-xs)",
            fontWeight: "var(--font-weight-medium)",
            color: "var(--color-text-tertiary)",
            letterSpacing: "var(--letter-spacing-wider)",
            textTransform: "uppercase",
          }}
        >
          {label}
        </span>
        {icon && (
          <span
            style={{
              color: accent
                ? "var(--color-accent-primary)"
                : "var(--color-text-tertiary)",
              opacity: 0.6,
            }}
          >
            {icon}
          </span>
        )}
      </div>
      <div
        style={{
          display: "flex",
          alignItems: "baseline",
          gap: "var(--spacing-3)",
        }}
      >
        <span
          style={{
            fontFamily: "var(--font-display)",
            fontSize: "var(--font-size-4xl)",
            fontWeight: "var(--font-weight-regular)",
            color: accent
              ? "var(--color-accent-primary)"
              : "var(--color-text-primary)",
            lineHeight: "1",
            fontVariantNumeric: "tabular-nums",
          }}
        >
          {value}
        </span>
        {change && (
          <span
            style={{
              fontSize: "var(--font-size-sm)",
              fontWeight: "var(--font-weight-medium)",
              color: changeColor,
              fontVariantNumeric: "tabular-nums",
            }}
          >
            {changePrefix}
            {change.value}%
          </span>
        )}
      </div>
    </Card>
  );
}
