import { forwardRef, type HTMLAttributes, type ReactNode } from 'react';

type ContainerSize = 'sm' | 'md' | 'lg' | 'xl' | 'full';

interface ContainerProps extends HTMLAttributes<HTMLDivElement> {
  size?: ContainerSize;
  children?: ReactNode;
}

const sizeStyles: Record<ContainerSize, React.CSSProperties> = {
  sm: { maxWidth: '640px' },
  md: { maxWidth: '768px' },
  lg: { maxWidth: '1024px' },
  xl: { maxWidth: '1280px' },
  full: { maxWidth: '100%' },
};

/**
 * Container - Page layout wrapper.
 * Centers content with responsive max-width.
 */
export const Container = forwardRef<HTMLDivElement, ContainerProps>(
  ({ size = 'lg', style, className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={className}
        style={{
          width: '100%',
          margin: '0 auto',
          paddingLeft: 'var(--space-6)',
          paddingRight: 'var(--space-6)',
          ...sizeStyles[size],
          ...style,
        }}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Container.displayName = 'Container';
