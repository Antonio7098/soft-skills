import { cn } from '@/lib/cn';

type AvatarSize = 'sm' | 'md' | 'lg';

interface AvatarProps {
  readonly src?: string;
  readonly fallback: string;
  readonly size?: AvatarSize;
  readonly className?: string;
}

const sizeStyles: Record<AvatarSize, string> = {
  sm: 'w-8 h-8 text-body-xs',
  md: 'w-10 h-10 text-body-sm',
  lg: 'w-14 h-14 text-body-md',
};

function getInitials(name: string): string {
  return name
    .split(' ')
    .slice(0, 2)
    .map((s) => s[0]?.toUpperCase() ?? '')
    .join('');
}

export function Avatar({ src, fallback, size = 'md', className }: AvatarProps) {
  if (src) {
    return (
      <img
        src={src}
        alt={fallback}
        className={cn(
          'rounded-full object-cover ring-2 ring-line',
          sizeStyles[size],
          className,
        )}
      />
    );
  }

  return (
    <div
      className={cn(
        'rounded-full flex items-center justify-center font-body font-semibold',
        'bg-accent-muted text-accent-text ring-2 ring-line',
        sizeStyles[size],
        className,
      )}
      aria-label={fallback}
    >
      {getInitials(fallback)}
    </div>
  );
}
