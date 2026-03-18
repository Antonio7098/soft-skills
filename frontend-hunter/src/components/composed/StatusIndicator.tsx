import type { HTMLAttributes } from "react";

type StatusType = "loading" | "success" | "error" | "warning" | "info" | "idle";

interface StatusIndicatorProps extends HTMLAttributes<HTMLDivElement> {
  status: StatusType;
  label?: string;
  size?: "sm" | "md" | "lg";
  pulse?: boolean;
}

const statusConfig: Record<
  StatusType,
  { color: string; bgColor: string; label: string }
> = {
  loading: {
    color: "var(--color-status-info)",
    bgColor: "rgba(91, 142, 196, 0.15)",
    label: "Loading",
  },
  success: {
    color: "var(--color-status-success)",
    bgColor: "rgba(91, 154, 111, 0.15)",
    label: "Complete",
  },
  error: {
    color: "var(--color-status-error)",
    bgColor: "rgba(196, 84, 84, 0.15)",
    label: "Error",
  },
  warning: {
    color: "var(--color-status-warning)",
    bgColor: "rgba(212, 148, 74, 0.15)",
    label: "Warning",
  },
  info: {
    color: "var(--color-status-info)",
    bgColor: "rgba(91, 142, 196, 0.15)",
    label: "Info",
  },
  idle: {
    color: "var(--color-text-tertiary)",
    bgColor: "var(--color-bg-tertiary)",
    label: "Idle",
  },
};

const dotSizeMap = { sm: 6, md: 8, lg: 10 };

export function StatusIndicator({
  status,
  label,
  size = "md",
  pulse = false,
  style,
  ...props
}: StatusIndicatorProps) {
  const config = statusConfig[status];
  const dotSize = dotSizeMap[size];

  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "var(--spacing-2)",
        ...style,
      }}
      {...props}
    >
      <span
        style={{
          position: "relative",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {(pulse || status === "loading") && (
          <span
            style={{
              position: "absolute",
              width: dotSize + 6,
              height: dotSize + 6,
              borderRadius: "50%",
              backgroundColor: config.color,
              opacity: 0.2,
              animation: "pulse 2s ease-in-out infinite",
            }}
          />
        )}
        <span
          style={{
            width: dotSize,
            height: dotSize,
            borderRadius: "50%",
            backgroundColor: config.color,
            boxShadow: `0 0 6px ${config.color}`,
            animation:
              status === "loading" ? "spin 2s linear infinite" : undefined,
            ...(status === "loading"
              ? {
                  borderRadius: "var(--radius-full)",
                  clipPath:
                    "polygon(50% 0%, 100% 38%, 82% 100%, 18% 100%, 0% 38%)",
                }
              : {}),
          }}
        />
      </span>
      {(label || size !== "sm") && (
        <span
          style={{
            fontSize:
              size === "sm"
                ? "var(--font-size-xs)"
                : size === "lg"
                  ? "var(--font-size-base)"
                  : "var(--font-size-sm)",
            fontWeight: "var(--font-weight-medium)",
            color: config.color,
            letterSpacing: "var(--letter-spacing-wide)",
            textTransform: "uppercase",
          }}
        >
          {label || config.label}
        </span>
      )}
    </div>
  );
}
