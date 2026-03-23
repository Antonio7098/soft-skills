import { forwardRef, useId, type InputHTMLAttributes } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hint?: string;
  error?: string;
  icon?: React.ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, hint, error, icon, style, id, ...props }, ref) => {
    const generatedId = useId();
    const inputId = id || generatedId;

    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "var(--spacing-1)" }}>
        {label && (
          <label
            htmlFor={inputId}
            style={{
              fontSize: "var(--font-size-sm)",
              fontWeight: "var(--font-weight-medium)",
              color: "var(--color-text-secondary)",
              letterSpacing: "var(--letter-spacing-wide)",
              textTransform: "uppercase",
            }}
          >
            {label}
          </label>
        )}
        <div style={{ position: "relative" }}>
          {icon && (
            <span
              style={{
                position: "absolute",
                left: "var(--spacing-3)",
                top: "50%",
                transform: "translateY(-50%)",
                color: "var(--color-text-tertiary)",
                display: "flex",
                alignItems: "center",
              }}
            >
              {icon}
            </span>
          )}
          <input
            ref={ref}
            id={inputId}
            style={{
              width: "100%",
              padding: icon
                ? "var(--spacing-2) var(--spacing-3) var(--spacing-2) var(--spacing-10)"
                : "var(--spacing-2) var(--spacing-3)",
              fontSize: "var(--font-size-base)",
              fontFamily: "var(--font-body)",
              color: "var(--color-text-primary)",
              backgroundColor: "var(--color-bg-tertiary)",
              border: `1px solid ${error ? "var(--color-status-error)" : "var(--color-border-default)"}`,
              borderRadius: "var(--radius-md)",
              outline: "none",
              transition: "all var(--transition-normal)",
              lineHeight: "var(--line-height-normal)",
              ...style,
            }}
            onFocus={(e) => {
              e.currentTarget.style.borderColor = "var(--color-accent-primary)";
              e.currentTarget.style.boxShadow = "0 0 0 3px var(--color-accent-muted)";
            }}
            onBlur={(e) => {
              e.currentTarget.style.borderColor = error
                ? "var(--color-status-error)"
                : "var(--color-border-default)";
              e.currentTarget.style.boxShadow = "none";
            }}
            {...props}
          />
        </div>
        {hint && !error && (
          <span
            style={{
              fontSize: "var(--font-size-xs)",
              color: "var(--color-text-tertiary)",
            }}
          >
            {hint}
          </span>
        )}
        {error && (
          <span
            style={{
              fontSize: "var(--font-size-xs)",
              color: "var(--color-status-error)",
            }}
          >
            {error}
          </span>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";
