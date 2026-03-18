/**
 * Color tokens for SoftSkills design system.
 *
 * All colors are defined as semantic tokens, not raw hex values.
 * Themes map these tokens to actual values.
 */
export interface ColorTokens {
  // Background surfaces
  bgPrimary: string;
  bgSecondary: string;
  bgTertiary: string;
  bgInverse: string;
  bgMuted: string;

  // Foreground / text
  fgPrimary: string;
  fgSecondary: string;
  fgTertiary: string;
  fgInverse: string;
  fgAccent: string;

  // Borders
  borderDefault: string;
  borderStrong: string;
  borderSubtle: string;
  borderAccent: string;

  // Interactive
  interactiveDefault: string;
  interactiveHover: string;
  interactiveActive: string;
  interactiveMuted: string;

  // Status
  statusSuccess: string;
  statusWarning: string;
  statusError: string;
  statusInfo: string;

  // Accent
  accentPrimary: string;
  accentSecondary: string;
  accentTertiary: string;

  // Overlay
  overlayLight: string;
  overlayDark: string;

  // Effects
  shadowColor: string;
  glowColor: string;
}
