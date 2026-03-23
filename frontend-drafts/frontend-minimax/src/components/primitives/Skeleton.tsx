import { type CSSProperties, type JSX } from 'react';
import { useTheme } from '../../theme';

interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  variant?: 'text' | 'circular' | 'rectangular';
  animation?: 'pulse' | 'wave' | 'none';
  style?: CSSProperties;
}

export function Skeleton({
  width,
  height,
  variant = 'text',
  animation = 'pulse',
  style,
}: SkeletonProps): JSX.Element {
  const { activeTheme: theme } = useTheme();

  const variantStyles: Record<string, React.CSSProperties> = {
    text: {
      width: width ?? '100%',
      height: height ?? '1em',
      borderRadius: theme.borderRadius.sm,
    },
    circular: {
      width: width ?? '3rem',
      height: height ?? '3rem',
      borderRadius: theme.borderRadius.full,
    },
    rectangular: {
      width: width ?? '100%',
      height: height ?? '5rem',
      borderRadius: theme.borderRadius.md,
    },
  };

  const baseStyle: React.CSSProperties = {
    backgroundColor: theme.colors.surfaceAlt,
    ...variantStyles[variant],
    ...style,
  };

  if (animation === 'none') {
    return <div style={baseStyle} />;
  }

  if (animation === 'pulse') {
    return (
      <div
        style={{
          ...baseStyle,
          animation: `skeleton-pulse ${theme.motion.durationSlow} ease-in-out infinite`,
        }}
      />
    );
  }

  return (
    <div
      style={{
        ...baseStyle,
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: `linear-gradient(90deg, transparent, ${theme.colors.surfaceAlt}, transparent)`,
          animation: `skeleton-wave ${theme.motion.durationSlow} linear infinite`,
        }}
      />
    </div>
  );
}
