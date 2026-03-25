import { forwardRef, type TextareaHTMLAttributes } from 'react';
import { cn } from '@/lib/cn';

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  readonly label?: string;
  readonly error?: string;
  readonly hint?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, error, hint, className, id, ...props }, ref) => {
    const inputId = id ?? label?.toLowerCase().replace(/\s+/g, '-');

    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label
            htmlFor={inputId}
            className="text-body-sm font-medium text-content-primary"
          >
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          id={inputId}
          className={cn(
            'w-full min-h-[120px] px-4 py-3 rounded-input font-body text-body-md',
            'bg-surface-elevated text-content-primary',
            'border border-line placeholder:text-content-tertiary',
            'focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent',
            'transition-all duration-150 resize-y',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            error && 'border-status-error focus:ring-status-error/30',
            className,
          )}
          {...props}
        />
        {error && (
          <p className="text-body-xs text-status-error">{error}</p>
        )}
        {hint && !error && (
          <p className="text-body-xs text-content-tertiary">{hint}</p>
        )}
      </div>
    );
  },
);

Textarea.displayName = 'Textarea';
