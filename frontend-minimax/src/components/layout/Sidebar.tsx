import { type ReactNode, type CSSProperties, type JSX } from 'react';
import { useTheme } from '../../theme';

interface NavItemProps {
  label: string;
  href?: string;
  icon?: ReactNode;
  isActive?: boolean;
  onClick?: () => void;
}

export function NavItem({
  label,
  isActive = false,
  icon,
  onClick,
}: NavItemProps): JSX.Element {
  const { activeTheme: theme } = useTheme();

  const itemStyle: CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: theme.spacing.space3,
    padding: `${theme.spacing.space3} ${theme.spacing.space4}`,
    fontFamily: theme.typography.fontBody,
    fontSize: theme.typography.sizeBase,
    fontWeight: isActive ? theme.typography.weightMedium : theme.typography.weightNormal,
    color: isActive ? theme.colors.primary : theme.colors.text,
    backgroundColor: isActive ? theme.colors.primaryMuted : 'transparent',
    borderRadius: theme.borderRadius.md,
    cursor: 'pointer',
    transition: `all ${theme.motion.durationNormal} ${theme.motion.easeOut}`,
    textDecoration: 'none',
    border: 'none',
    width: '100%',
    alignSelf: 'stretch',
  };

  return (
    <div
      role="button"
      tabIndex={0}
      style={itemStyle}
      onClick={onClick}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick?.();
        }
      }}
    >
      {icon && <span style={{ display: 'flex', opacity: 0.8 }}>{icon}</span>}
      {label}
    </div>
  );
}

interface SidebarProps {
  logo?: ReactNode;
  navItems?: ReactNode;
  footer?: ReactNode;
  style?: CSSProperties;
}

export function Sidebar({
  logo,
  navItems,
  footer,
  style,
}: SidebarProps): JSX.Element {
  const { activeTheme: theme } = useTheme();

  const sidebarStyle: CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    padding: theme.spacing.space4,
    ...style,
  };

  const logoStyle: CSSProperties = {
    padding: theme.spacing.space4,
    marginBottom: theme.spacing.space4,
  };

  const navStyle: CSSProperties = {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    gap: theme.spacing.space1,
  };

  const footerStyle: CSSProperties = {
    paddingTop: theme.spacing.space4,
    borderTop: `1px solid ${theme.colors.border}`,
  };

  return (
    <nav style={sidebarStyle}>
      {logo && <div style={logoStyle}>{logo}</div>}
      <div style={navStyle}>{navItems}</div>
      {footer && <div style={footerStyle}>{footer}</div>}
    </nav>
  );
}
