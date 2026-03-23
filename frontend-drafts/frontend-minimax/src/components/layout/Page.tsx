import { type ReactNode, type CSSProperties, type JSX } from 'react';
import { useTheme } from '../../theme';

interface PageProps {
  children: ReactNode;
  maxWidth?: string | number;
  padding?: boolean;
  style?: CSSProperties;
}

export function Page({
  children,
  maxWidth = '1200px',
  padding = true,
  style,
}: PageProps): JSX.Element {
  const { activeTheme: theme } = useTheme();

  const pageStyle: CSSProperties = {
    width: '100%',
    maxWidth,
    margin: '0 auto',
    padding: padding ? theme.spacing.space6 : undefined,
    ...style,
  };

  return <div style={pageStyle}>{children}</div>;
}

interface SectionProps {
  children: ReactNode;
  gap?: 'sm' | 'md' | 'lg';
  style?: CSSProperties;
}

export function Section({
  children,
  gap = 'md',
  style,
}: SectionProps): JSX.Element {
  const { activeTheme: theme } = useTheme();

  const gapMap = {
    sm: theme.spacing.space3,
    md: theme.spacing.space6,
    lg: theme.spacing.space8,
  };

  const sectionStyle: CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    gap: gapMap[gap],
    ...style,
  };

  return <section style={sectionStyle}>{children}</section>;
}

interface GridProps {
  children: ReactNode;
  columns?: number | string;
  gap?: 'sm' | 'md' | 'lg';
  style?: CSSProperties;
}

export function Grid({
  children,
  columns = 'repeat(auto-fit, minmax(300px, 1fr))',
  gap = 'md',
  style,
}: GridProps): JSX.Element {
  const { activeTheme: theme } = useTheme();

  const gapMap = {
    sm: theme.spacing.space3,
    md: theme.spacing.space6,
    lg: theme.spacing.space8,
  };

  const gridStyle: CSSProperties = {
    display: 'grid',
    gridTemplateColumns: columns,
    gap: gapMap[gap],
    ...style,
  };

  return <div style={gridStyle}>{children}</div>;
}
