import { forwardRef, type InputHTMLAttributes, type ReactNode } from 'react';
import { cn } from '@/lib/cn';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  readonly label?: string;
  readonly error?: string;
  readonly hint?: string;
  readonly icon?: ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, icon, className, id, ...props }, ref) => {
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
        <div className="relative">
          {icon && (
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-content-tertiary">
              {icon}
            </span>
          )}
          <input
            ref={ref}
            id={inputId}
            className={cn(
              'w-full h-10 px-3 rounded-input font-body text-body-md',
              'bg-surface-elevated text-content-primary',
              'border border-line placeholder:text-content-tertiary',
              'focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent',
              'transition-all duration-150',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              icon && 'pl-10',
              error && 'border-status-error focus:ring-status-error/30',
              className,
            )}
            {...props}
          />
        </div>
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

Input.displayName = 'Input';
