import type { HTMLAttributes, ReactNode } from "react";

type BadgeVariant =
  | "default"
  | "accent"
  | "success"
  | "warning"
  | "error"
  | "info";
type BadgeSize = "sm" | "md";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  size?: BadgeSize;
  dot?: boolean;
  children: ReactNode;
}

const variantStyles: Record<BadgeVariant, React.CSSProperties> = {
  default: {
    backgroundColor: "var(--color-bg-tertiary)",
    color: "var(--color-text-secondary)",
    border: "1px solid var(--color-border-default)",
  },
  accent: {
    backgroundColor: "var(--color-accent-muted)",
    color: "var(--color-accent-primary)",
    border: "1px solid transparent",
  },
  success: {
    backgroundColor: "rgba(91, 154, 111, 0.12)",
    color: "var(--color-status-success)",
    border: "1px solid rgba(91, 154, 111, 0.2)",
  },
  warning: {
    backgroundColor: "rgba(212, 148, 74, 0.12)",
    color: "var(--color-status-warning)",
    border: "1px solid rgba(212, 148, 74, 0.2)",
  },
  error: {
    backgroundColor: "rgba(196, 84, 84, 0.12)",
    color: "var(--color-status-error)",
    border: "1px solid rgba(196, 84, 84, 0.2)",
  },
  info: {
    backgroundColor: "rgba(91, 142, 196, 0.12)",
    color: "var(--color-status-info)",
    border: "1px solid rgba(91, 142, 196, 0.2)",
  },
};

const dotColors: Record<BadgeVariant, string> = {
  default: "var(--color-text-tertiary)",
  accent: "var(--color-accent-primary)",
  success: "var(--color-status-success)",
  warning: "var(--color-status-warning)",
  error: "var(--color-status-error)",
  info: "var(--color-status-info)",
};

export function Badge({
  variant = "default",
  size = "md",
  dot = false,
  children,
  style,
  ...props
}: BadgeProps) {
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "var(--spacing-1)",
        padding:
          size === "sm"
            ? "1px var(--spacing-2)"
            : "var(--spacing-1) var(--spacing-3)",
        fontSize: size === "sm" ? "var(--font-size-xs)" : "var(--font-size-sm)",
        fontWeight: "var(--font-weight-medium)",
        fontFamily: "var(--font-body)",
        borderRadius: "var(--radius-full)",
        lineHeight: "1",
        whiteSpace: "nowrap",
        letterSpacing: "var(--letter-spacing-wide)",
        textTransform: "uppercase",
        ...variantStyles[variant],
        ...style,
      }}
      {...props}
    >
      {dot && (
        <span
          style={{
            width: size === "sm" ? 5 : 6,
            height: size === "sm" ? 5 : 6,
            borderRadius: "50%",
            backgroundColor: dotColors[variant],
            flexShrink: 0,
          }}
        />
      )}
      {children}
    </span>
  );
}
