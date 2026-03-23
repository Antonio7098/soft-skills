import { Skeleton } from '@/design-system/primitives/Skeleton';
import { cn } from '@/lib/cn';

type LoadingVariant = 'spinner' | 'skeleton' | 'pulse';

interface LoadingStateProps {
  readonly message?: string;
  readonly variant?: LoadingVariant;
  readonly className?: string;
}

function Spinner() {
  return (
    <div className="flex flex-col items-center gap-3">
      <div className="w-8 h-8 border-2 border-accent/30 border-t-accent rounded-full animate-spin" />
    </div>
  );
}

function SkeletonBlock() {
  return (
    <div className="flex flex-col gap-4 w-full max-w-md">
      <Skeleton variant="rectangular" height="48px" className="w-full" />
      <div className="flex flex-col gap-2">
        <Skeleton width="80%" />
        <Skeleton width="60%" />
        <Skeleton width="70%" />
      </div>
      <div className="flex gap-3">
        <Skeleton variant="rectangular" height="36px" className="w-24" />
        <Skeleton variant="rectangular" height="36px" className="w-24" />
      </div>
    </div>
  );
}

function PulseBlock() {
  return (
    <div className="flex items-center gap-3">
      <div className="w-3 h-3 rounded-full bg-accent animate-skeleton-pulse" />
      <div className="w-3 h-3 rounded-full bg-accent animate-skeleton-pulse [animation-delay:200ms]" />
      <div className="w-3 h-3 rounded-full bg-accent animate-skeleton-pulse [animation-delay:400ms]" />
    </div>
  );
}

export function LoadingState({
  message = 'Loading...',
  variant = 'spinner',
  className,
}: LoadingStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center gap-4 py-16 px-6',
        className,
      )}
    >
      {variant === 'spinner' && <Spinner />}
      {variant === 'skeleton' && <SkeletonBlock />}
      {variant === 'pulse' && <PulseBlock />}
      {message && (
        <p className="text-body-sm text-content-secondary animate-skeleton-pulse">{message}</p>
      )}
    </div>
  );
}
