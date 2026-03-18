import { forwardRef, type HTMLAttributes, type ElementType } from 'react';

type PolymorphicProps<E extends ElementType> = {
  as?: E;
} & HTMLAttributes<HTMLElement>;

/**
 * Box - The base layout primitive.
 * Renders as a <div> by default, supports polymorphic `as` prop.
 * All spacing and color via CSS variables.
 */
export const Box = forwardRef<HTMLElement, PolymorphicProps<ElementType>>(
  ({ as: Component = 'div', style, className, ...props }, ref) => {
    return (
      <Component
        ref={ref}
        className={className}
        style={style}
        {...props}
      />
    );
  }
);

Box.displayName = 'Box';
