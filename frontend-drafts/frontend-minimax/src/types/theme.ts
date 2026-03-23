export type ThemeId = 'obsidian' | 'parchment' | 'neon';

export interface ThemeColors {
  background: string;
  surface: string;
  surfaceAlt: string;
  primary: string;
  primaryHover: string;
  primaryMuted: string;
  accent: string;
  accentHover: string;
  text: string;
  textMuted: string;
  textInverse: string;
  border: string;
  borderFocus: string;
  success: string;
  warning: string;
  error: string;
  shadow: string;
}

export interface ThemeTypography {
  fontDisplay: string;
  fontBody: string;
  fontMono: string;
  sizeXs: string;
  sizeSm: string;
  sizeBase: string;
  sizeLg: string;
  sizeXl: string;
  size2xl: string;
  size3xl: string;
  size4xl: string;
  weightNormal: number;
  weightMedium: number;
  weightBold: number;
  lineHeightTight: string;
  lineHeightNormal: string;
  lineHeightRelaxed: string;
  letterSpacingTight: string;
  letterSpacingNormal: string;
  letterSpacingWide: string;
}

export interface ThemeSpacing {
  space1: string;
  space2: string;
  space3: string;
  space4: string;
  space5: string;
  space6: string;
  space8: string;
  space10: string;
  space12: string;
  space16: string;
  space20: string;
  space24: string;
}

export interface ThemeMotion {
  durationFast: string;
  durationNormal: string;
  durationSlow: string;
  easeOut: string;
  easeInOut: string;
  easeSpring: string;
}

export interface ThemeBorderRadius {
  sm: string;
  md: string;
  lg: string;
  xl: string;
  full: string;
}

export interface ThemeShadow {
  sm: string;
  md: string;
  lg: string;
  xl: string;
}

export interface Theme {
  id: ThemeId;
  name: string;
  description: string;
  colors: ThemeColors;
  typography: ThemeTypography;
  spacing: ThemeSpacing;
  motion: ThemeMotion;
  borderRadius: ThemeBorderRadius;
  shadow: ThemeShadow;
}

export interface ThemeConfig {
  themes: Record<ThemeId, Theme>;
  activeThemeId: ThemeId;
}
