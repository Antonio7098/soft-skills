import { forwardRef, type HTMLAttributes, type ReactNode } from 'react';

type TagSize = 'sm' | 'md';

interface TagProps extends HTMLAttributes<HTMLSpanElement> {
  size?: TagSize;
  /** Icon before the label */
  icon?: ReactNode;
  /** Removable tag */
  removable?: boolean;
  /** Callback when remove is clicked */
  onRemove?: () => void;
}

/**
 * Tag - Compact label for skills, competencies, or categories.
 * Distinguished from Badge by typically representing user-generated labels.
 */
export const Tag = forwardRef<HTMLSpanElement, TagProps>(
  ({ size = 'md', icon, removable, onRemove, style, className, children, ...props }, ref) => {
    const tagStyle: React.CSSProperties = {
      display: 'inline-flex',
      alignItems: 'center',
      gap: '0.375rem',
      fontFamily: 'var(--font-body)',
      fontSize: size === 'sm' ? 'var(--font-size-small)' : 'var(--font-size-base)',
      fontWeight: 500,
      color: 'var(--color-fg-primary)',
      backgroundColor: 'var(--color-bg-secondary)',
      border: '1px solid var(--color-border-default)',
      borderRadius: 'var(--radius-md)',
      padding: size === 'sm' ? '0.125rem 0.5rem' : '0.25rem 0.75rem',
      lineHeight: 1.4,
      whiteSpace: 'nowrap',
      transition: 'all var(--duration-fast) var(--easing-default)',
      ...style,
    };

    return (
      <span
        ref={ref}
        className={className}
        style={tagStyle}
        {...props}
      >
        {icon && <span style={{ display: 'flex', alignItems: 'center' }}>{icon}</span>}
        {children}
        {removable && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onRemove?.();
            }}
            aria-label="Remove tag"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '1em',
              height: '1em',
              borderRadius: 'var(--radius-full)',
              border: 'none',
              backgroundColor: 'transparent',
              color: 'var(--color-fg-tertiary)',
              cursor: 'pointer',
              padding: 0,
              fontSize: 'inherit',
              lineHeight: 1,
            }}
          >
            x
          </button>
        )}
      </span>
    );
  }
);

Tag.displayName = 'Tag';
