import { forwardRef, useId, type TextareaHTMLAttributes } from "react";

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  hint?: string;
  error?: string;
  minRows?: number;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, hint, error, minRows = 4, style, id, ...props }, ref) => {
    const generatedId = useId();
    const textareaId = id || generatedId;

    return (
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "var(--spacing-1)",
        }}
      >
        {label && (
          <label
            htmlFor={textareaId}
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
        <textarea
          ref={ref}
          id={textareaId}
          rows={minRows}
          style={{
            width: "100%",
            padding: "var(--spacing-3)",
            fontSize: "var(--font-size-base)",
            fontFamily: "var(--font-body)",
            color: "var(--color-text-primary)",
            backgroundColor: "var(--color-bg-tertiary)",
            border: `1px solid ${error ? "var(--color-status-error)" : "var(--color-border-default)"}`,
            borderRadius: "var(--radius-md)",
            outline: "none",
            transition: "all var(--transition-normal)",
            lineHeight: "var(--line-height-relaxed)",
            resize: "vertical",
            minHeight: `${minRows * 1.75}em`,
            ...style,
          }}
          onFocus={(e) => {
            e.currentTarget.style.borderColor = "var(--color-accent-primary)";
            e.currentTarget.style.boxShadow =
              "0 0 0 3px var(--color-accent-muted)";
          }}
          onBlur={(e) => {
            e.currentTarget.style.borderColor = error
              ? "var(--color-status-error)"
              : "var(--color-border-default)";
            e.currentTarget.style.boxShadow = "none";
          }}
          {...props}
        />
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

Textarea.displayName = "Textarea";
