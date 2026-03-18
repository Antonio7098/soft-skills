import type { HTMLAttributes } from "react";

interface ProgressRingProps extends HTMLAttributes<HTMLDivElement> {
  value: number;
  max?: number;
  size?: number;
  strokeWidth?: number;
  color?: string;
  bgColor?: string;
  showValue?: boolean;
  label?: string;
}

export function ProgressRing({
  value,
  max = 100,
  size = 80,
  strokeWidth = 6,
  color = "var(--color-accent-primary)",
  bgColor = "var(--color-bg-tertiary)",
  showValue = true,
  label,
  style,
  ...props
}: ProgressRingProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);
  const offset = circumference - (percentage / 100) * circumference;

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: "var(--spacing-2)",
        ...style,
      }}
      {...props}
    >
      <div
        style={{
          position: "relative",
          width: size,
          height: size,
        }}
      >
        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          style={{ transform: "rotate(-90deg)" }}
        >
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={bgColor}
            strokeWidth={strokeWidth}
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{
              transition: "stroke-dashoffset 1s cubic-bezier(0.16, 1, 0.3, 1)",
            }}
          />
        </svg>
        {showValue && (
          <div
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontFamily: "var(--font-display)",
              fontSize: size * 0.28,
              color: "var(--color-text-primary)",
              fontVariantNumeric: "tabular-nums",
            }}
          >
            {Math.round(percentage)}
          </div>
        )}
      </div>
      {label && (
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
      )}
    </div>
  );
}
