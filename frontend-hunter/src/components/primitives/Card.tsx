import type { HTMLAttributes, ReactNode } from "react";

type CardVariant = "default" | "elevated" | "outlined" | "ghost";
type CardPadding = "none" | "sm" | "md" | "lg";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: CardVariant;
  padding?: CardPadding;
  hoverable?: boolean;
  children: ReactNode;
}

const variantStyles: Record<CardVariant, React.CSSProperties> = {
  default: {
    backgroundColor: "var(--color-bg-secondary)",
    border: "1px solid var(--color-border-subtle)",
  },
  elevated: {
    backgroundColor: "var(--color-bg-elevated)",
    border: "1px solid var(--color-border-subtle)",
    boxShadow: "var(--shadow-md)",
  },
  outlined: {
    backgroundColor: "transparent",
    border: "1px solid var(--color-border-default)",
  },
  ghost: {
    backgroundColor: "transparent",
    border: "none",
  },
};

const paddingStyles: Record<CardPadding, string> = {
  none: "0",
  sm: "var(--spacing-3)",
  md: "var(--spacing-5)",
  lg: "var(--spacing-8)",
};

export function Card({
  variant = "default",
  padding = "md",
  hoverable = false,
  children,
  style,
  ...props
}: CardProps) {
  return (
    <div
      style={{
        borderRadius: "var(--radius-lg)",
        padding: paddingStyles[padding],
        transition: "all var(--transition-normal)",
        animation: "fadeInUp var(--transition-slow) both",
        ...variantStyles[variant],
        ...(hoverable
          ? { cursor: "pointer" }
          : {}),
        ...style,
      }}
      onMouseEnter={(e) => {
        if (hoverable) {
          e.currentTarget.style.transform = "translateY(-2px)";
          e.currentTarget.style.boxShadow = "var(--shadow-lg)";
          e.currentTarget.style.borderColor = "var(--color-border-strong)";
        }
      }}
      onMouseLeave={(e) => {
        if (hoverable) {
          e.currentTarget.style.transform = "translateY(0)";
          e.currentTarget.style.boxShadow =
            variant === "elevated" ? "var(--shadow-md)" : "none";
          e.currentTarget.style.borderColor =
            variantStyles[variant].border === "none"
              ? "transparent"
              : "var(--color-border-subtle)";
        }
      }}
      {...props}
    >
      {children}
    </div>
  );
}
