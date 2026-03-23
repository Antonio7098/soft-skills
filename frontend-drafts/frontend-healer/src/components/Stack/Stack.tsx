import { forwardRef, type HTMLAttributes, type ReactNode } from 'react';

type StackDirection = 'row' | 'column';
type Align = 'start' | 'center' | 'end' | 'stretch';
type Justify = 'start' | 'center' | 'end' | 'between' | 'around';

interface StackProps extends HTMLAttributes<HTMLDivElement> {
  direction?: StackDirection;
  align?: Align;
  justify?: Justify;
  gap?: string;
  wrap?: boolean;
  children?: ReactNode;
}

const alignMap: Record<Align, string> = {
  start: 'flex-start',
  center: 'center',
  end: 'flex-end',
  stretch: 'stretch',
};

const justifyMap: Record<Justify, string> = {
  start: 'flex-start',
  center: 'center',
  end: 'flex-end',
  between: 'space-between',
  around: 'space-around',
};

/**
 * Stack - Flexible layout primitive for arranging children.
 * Supports horizontal and vertical layouts with gap and alignment.
 */
export const Stack = forwardRef<HTMLDivElement, StackProps>(
  (
    {
      direction = 'column',
      align = 'stretch',
      justify = 'start',
      gap = 'var(--space-4)',
      wrap = false,
      style,
      className,
      children,
      ...props
    },
    ref
  ) => {
    const stackStyle: React.CSSProperties = {
      display: 'flex',
      flexDirection: direction,
      alignItems: alignMap[align],
      justifyContent: justifyMap[justify],
      gap,
      flexWrap: wrap ? 'wrap' : 'nowrap',
      ...style,
    };

    return (
      <div
        ref={ref}
        className={className}
        style={stackStyle}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Stack.displayName = 'Stack';
