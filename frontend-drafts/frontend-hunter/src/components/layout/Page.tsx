import type { HTMLAttributes, ReactNode } from "react";

interface PageProps extends HTMLAttributes<HTMLDivElement> {
  title?: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
}

export function Page({
  title,
  subtitle,
  actions,
  children,
  style,
  ...props
}: PageProps) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "var(--spacing-8)",
        animation: "fadeIn var(--transition-slow) both",
        ...style,
      }}
      {...props}
    >
      {(title || actions) && (
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            gap: "var(--spacing-4)",
            animation: "fadeInDown var(--transition-slow) both",
          }}
        >
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "var(--spacing-1)",
            }}
          >
            {title && (
              <h1
                style={{
                  fontFamily: "var(--font-display)",
                  fontSize: "var(--font-size-4xl)",
                  color: "var(--color-text-primary)",
                  lineHeight: "var(--line-height-tight)",
                  letterSpacing: "var(--letter-spacing-tight)",
                }}
              >
                {title}
              </h1>
            )}
            {subtitle && (
              <p
                style={{
                  fontSize: "var(--font-size-base)",
                  color: "var(--color-text-secondary)",
                  maxWidth: 560,
                }}
              >
                {subtitle}
              </p>
            )}
          </div>
          {actions && (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "var(--spacing-3)",
                flexShrink: 0,
              }}
            >
              {actions}
            </div>
          )}
        </div>
      )}
      {children}
    </div>
  );
}
