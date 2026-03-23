import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonVariant = "primary" | "secondary" | "ghost" | "outline" | "danger";
type ButtonSize = "sm" | "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  icon?: ReactNode;
  iconPosition?: "left" | "right";
  fullWidth?: boolean;
  children?: ReactNode;
}

const variantStyles: Record<ButtonVariant, React.CSSProperties> = {
  primary: {
    backgroundColor: "var(--color-accent-primary)",
    color: "var(--color-text-inverse)",
    border: "1px solid transparent",
  },
  secondary: {
    backgroundColor: "var(--color-bg-tertiary)",
    color: "var(--color-text-primary)",
    border: "1px solid var(--color-border-default)",
  },
  ghost: {
    backgroundColor: "transparent",
    color: "var(--color-text-secondary)",
    border: "1px solid transparent",
  },
  outline: {
    backgroundColor: "transparent",
    color: "var(--color-accent-primary)",
    border: "1px solid var(--color-accent-primary)",
  },
  danger: {
    backgroundColor: "var(--color-status-error)",
    color: "#fff",
    border: "1px solid transparent",
  },
};

const sizeStyles: Record<ButtonSize, React.CSSProperties> = {
  sm: {
    padding: "var(--spacing-1) var(--spacing-3)",
    fontSize: "var(--font-size-sm)",
    gap: "var(--spacing-1)",
  },
  md: {
    padding: "var(--spacing-2) var(--spacing-4)",
    fontSize: "var(--font-size-base)",
    gap: "var(--spacing-2)",
  },
  lg: {
    padding: "var(--spacing-3) var(--spacing-6)",
    fontSize: "var(--font-size-lg)",
    gap: "var(--spacing-3)",
  },
};

export function Button({
  variant = "primary",
  size = "md",
  loading = false,
  icon,
  iconPosition = "left",
  fullWidth = false,
  disabled,
  children,
  style,
  ...props
}: ButtonProps) {
  const isDisabled = disabled || loading;

  return (
    <button
      disabled={isDisabled}
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        fontWeight: "var(--font-weight-medium)",
        fontFamily: "var(--font-body)",
        borderRadius: "var(--radius-md)",
        cursor: isDisabled ? "not-allowed" : "pointer",
        opacity: isDisabled ? 0.6 : 1,
        transition: `all var(--transition-normal)`,
        width: fullWidth ? "100%" : "auto",
        whiteSpace: "nowrap",
        letterSpacing: "var(--letter-spacing-wide)",
        textTransform: "uppercase",
        ...variantStyles[variant],
        ...sizeStyles[size],
        ...style,
      }}
      onMouseEnter={(e) => {
        if (!isDisabled) {
          e.currentTarget.style.transform = "translateY(-1px)";
          e.currentTarget.style.boxShadow = "var(--shadow-md)";
        }
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = "translateY(0)";
        e.currentTarget.style.boxShadow = "none";
      }}
      {...props}
    >
      {loading && (
        <SpinnerIcon
          style={{
            width: size === "sm" ? 12 : size === "lg" ? 18 : 14,
            height: size === "sm" ? 12 : size === "lg" ? 18 : 14,
          }}
        />
      )}
      {!loading && icon && iconPosition === "left" && icon}
      {children}
      {!loading && icon && iconPosition === "right" && icon}
    </button>
  );
}

function SpinnerIcon({ style }: { style?: React.CSSProperties }) {
  return (
    <svg
      viewBox="0 0 24 24"
      style={{
        animation: "spin 1s linear infinite",
        ...style,
      }}
    >
      <circle
        cx="12"
        cy="12"
        r="10"
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
        strokeDasharray="31.4 31.4"
        opacity="0.3"
      />
      <circle
        cx="12"
        cy="12"
        r="10"
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
        strokeDasharray="31.4 31.4"
        strokeDashoffset="7.85"
      />
    </svg>
  );
}
