import { type CSSProperties, type JSX } from 'react';
import { useTheme } from '../../theme';

interface AvatarProps {
  name: string;
  src?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  style?: CSSProperties;
}

function getInitials(name: string): string {
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}

function getColorFromName(name: string, theme: ReturnType<typeof useTheme>['activeTheme']): string {
  const colors = [
    theme.colors.primary,
    theme.colors.accent,
    theme.colors.success,
    theme.colors.warning,
  ];
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length];
}

export function Avatar({ name, src, size = 'md', style }: AvatarProps): JSX.Element {
  const { activeTheme: theme } = useTheme();

  const sizeMap = {
    sm: '2rem',
    md: '3rem',
    lg: '4rem',
    xl: '5rem',
  };

  const fontSizeMap = {
    sm: theme.typography.sizeXs,
    md: theme.typography.sizeSm,
    lg: theme.typography.sizeLg,
    xl: theme.typography.size2xl,
  };

  const avatarStyle: CSSProperties = {
    width: sizeMap[size],
    height: sizeMap[size],
    borderRadius: theme.borderRadius.full,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontFamily: theme.typography.fontBody,
    fontWeight: theme.typography.weightBold,
    fontSize: fontSizeMap[size],
    color: theme.colors.textInverse,
    backgroundColor: getColorFromName(name, theme),
    overflow: 'hidden',
    flexShrink: 0,
    ...style,
  };

  return (
    <div style={avatarStyle}>
      {src ? (
        <img
          src={src}
          alt={name}
          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
        />
      ) : (
        getInitials(name)
      )}
    </div>
  );
}
