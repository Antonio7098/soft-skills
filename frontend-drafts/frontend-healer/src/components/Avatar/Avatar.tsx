import { forwardRef, type HTMLAttributes } from 'react';

type AvatarSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

interface AvatarProps extends HTMLAttributes<HTMLDivElement> {
  /** Image source URL */
  src?: string;
  /** Alt text */
  alt?: string;
  /** Display name for fallback initials */
  name?: string;
  /** Size preset */
  size?: AvatarSize;
  /** Status indicator */
  status?: 'online' | 'offline' | 'busy' | 'away';
}

const sizeStyles: Record<AvatarSize, { size: string; fontSize: string }> = {
  xs: { size: '1.5rem', fontSize: 'var(--font-size-micro)' },
  sm: { size: '2rem', fontSize: 'var(--font-size-small)' },
  md: { size: '2.5rem', fontSize: 'var(--font-size-base)' },
  lg: { size: '3.5rem', fontSize: 'var(--font-size-xl)' },
  xl: { size: '5rem', fontSize: 'var(--font-size-2xl)' },
};

const statusColors: Record<string, string> = {
  online: 'var(--color-status-success)',
  offline: 'var(--color-fg-tertiary)',
  busy: 'var(--color-status-error)',
  away: 'var(--color-status-warning)',
};

function getInitials(name?: string): string {
  if (!name) return '?';
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0][0].toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

/**
 * Avatar - User or person representation.
 * Shows image or fallback initials with optional status.
 */
export const Avatar = forwardRef<HTMLDivElement, AvatarProps>(
  ({ src, alt, name, size = 'md', status, style, className, ...props }, ref) => {
    const { size: dimensions, fontSize } = sizeStyles[size];

    return (
      <div
        ref={ref}
        className={className}
        style={{
          position: 'relative',
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: dimensions,
          height: dimensions,
          borderRadius: 'var(--radius-full)',
          overflow: 'visible',
          flexShrink: 0,
          ...style,
        }}
        {...props}
      >
        {src ? (
          <img
            src={src}
            alt={alt || name || 'Avatar'}
            style={{
              width: '100%',
              height: '100%',
              borderRadius: 'var(--radius-full)',
              objectFit: 'cover',
            }}
          />
        ) : (
          <div style={{
            width: '100%',
            height: '100%',
            borderRadius: 'var(--radius-full)',
            backgroundColor: 'var(--color-bg-muted)',
            color: 'var(--color-fg-secondary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontFamily: 'var(--font-body)',
            fontSize,
            fontWeight: 600,
            letterSpacing: '0.025em',
          }}>
            {getInitials(name)}
          </div>
        )}
        {status && (
          <span style={{
            position: 'absolute',
            bottom: 0,
            right: 0,
            width: size === 'xs' || size === 'sm' ? '0.5rem' : '0.75rem',
            height: size === 'xs' || size === 'sm' ? '0.5rem' : '0.75rem',
            borderRadius: 'var(--radius-full)',
            backgroundColor: statusColors[status],
            border: '2px solid var(--color-bg-primary)',
          }} />
        )}
      </div>
    );
  }
);

Avatar.displayName = 'Avatar';
