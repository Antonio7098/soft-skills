import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from '@/design-system/primitives/Button';
import { cn } from '@/lib/cn';

interface ErrorStateProps {
  readonly title?: string;
  readonly message: string;
  readonly onRetry?: () => void;
  readonly className?: string;
}

export function ErrorState({
  title = 'Something went wrong',
  message,
  onRetry,
  className,
}: ErrorStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center gap-4 py-16 px-6 text-center',
        className,
      )}
    >
      <div className="w-12 h-12 rounded-full bg-status-error/10 flex items-center justify-center">
        <AlertTriangle className="w-6 h-6 text-status-error" />
      </div>
      <div className="flex flex-col gap-1.5 max-w-sm">
        <h3 className="font-display text-display-sm text-content-primary">{title}</h3>
        <p className="text-body-sm text-content-secondary">{message}</p>
      </div>
      {onRetry && (
        <Button
          variant="secondary"
          size="sm"
          icon={<RefreshCw className="w-3.5 h-3.5" />}
          onClick={onRetry}
        >
          Try again
        </Button>
      )}
    </div>
  );
}
