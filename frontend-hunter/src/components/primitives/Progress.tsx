import type { HTMLAttributes } from "react";

interface ProgressProps extends HTMLAttributes<HTMLDivElement> {
  value: number;
  max?: number;
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
  color?: string;
  label?: string;
}

const heightMap = {
  sm: 4,
  md: 6,
  lg: 10,
};

export function Progress({
  value,
  max = 100,
  size = "md",
  showLabel = false,
  color = "var(--color-accent-primary)",
  label,
  style,
  ...props
}: ProgressProps) {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);
  const h = heightMap[size];

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "var(--spacing-1)",
        width: "100%",
        ...style,
      }}
      {...props}
    >
      {(label || showLabel) && (
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          {label && (
            <span
              style={{
                fontSize: "var(--font-size-sm)",
                color: "var(--color-text-secondary)",
              }}
            >
              {label}
            </span>
          )}
          {showLabel && (
            <span
              style={{
                fontSize: "var(--font-size-sm)",
                fontWeight: "var(--font-weight-medium)",
                color: "var(--color-text-primary)",
                fontVariantNumeric: "tabular-nums",
              }}
            >
              {Math.round(percentage)}%
            </span>
          )}
        </div>
      )}
      <div
        style={{
          width: "100%",
          height: h,
          backgroundColor: "var(--color-bg-tertiary)",
          borderRadius: "var(--radius-full)",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${percentage}%`,
            height: "100%",
            backgroundColor: color,
            borderRadius: "var(--radius-full)",
            transition: "width var(--transition-slow)",
          }}
        />
      </div>
    </div>
  );
}
