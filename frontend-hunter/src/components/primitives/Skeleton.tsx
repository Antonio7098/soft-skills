import type { HTMLAttributes } from "react";

type SkeletonVariant = "text" | "circular" | "rectangular";

interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  variant?: SkeletonVariant;
  width?: string | number;
  height?: string | number;
  lines?: number;
}

export function Skeleton({
  variant = "rectangular",
  width,
  height,
  lines = 1,
  style,
  ...props
}: SkeletonProps) {
  if (variant === "text" && lines > 1) {
    return (
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "var(--spacing-2)",
        }}
      >
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            style={{
              height: "var(--font-size-base)",
              width: i === lines - 1 ? "60%" : "100%",
              borderRadius: "var(--radius-sm)",
              background: `linear-gradient(90deg, var(--color-bg-tertiary) 25%, var(--color-border-subtle) 50%, var(--color-bg-tertiary) 75%)`,
              backgroundSize: "200% 100%",
              animation: "shimmer 1.5s ease-in-out infinite",
              ...style,
            }}
            {...props}
          />
        ))}
      </div>
    );
  }

  const borderRadius =
    variant === "circular" ? "var(--radius-full)" : "var(--radius-md)";

  return (
    <div
      style={{
        width: width || (variant === "text" ? "100%" : undefined),
        height: height || (variant === "text" ? "var(--font-size-base)" : undefined),
        borderRadius,
        background: `linear-gradient(90deg, var(--color-bg-tertiary) 25%, var(--color-border-subtle) 50%, var(--color-bg-tertiary) 75%)`,
        backgroundSize: "200% 100%",
        animation: "shimmer 1.5s ease-in-out infinite",
        ...style,
      }}
      {...props}
    />
  );
}
