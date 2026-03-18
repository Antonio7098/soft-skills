import type { TypographyTokens } from './typography';

/**
 * Shared typography tokens.
 * Uses Instrument Serif for display + DM Sans for body.
 * An editorial pairing that avoids generic AI aesthetics.
 */
export const typography: TypographyTokens = {
  fontFamilyDisplay: "'Instrument Serif', 'Georgia', serif",
  fontFamilyBody: "'DM Sans', 'Helvetica Neue', sans-serif",
  fontFamilyMono: "'JetBrains Mono', 'Fira Code', monospace",

  // Font sizes - modular scale 1.25
  fontSizeMicro: '0.64rem',    // ~10.24px
  fontSizeSmall: '0.8rem',     // ~12.8px
  fontSizeBase: '1rem',        // 16px
  fontSizeMedium: '1.125rem',  // ~18px
  fontSizeLarge: '1.25rem',    // ~20px
  fontSizeXL: '1.563rem',      // ~25px
  fontSize2XL: '1.953rem',     // ~31.25px
  fontSize3XL: '2.441rem',     // ~39px
  fontSize4XL: '3.052rem',     // ~48.8px
  fontSize5XL: '3.815rem',     // ~61px

  // Line heights
  lineHeightTight: 1.1,
  lineHeightNormal: 1.5,
  lineHeightRelaxed: 1.75,
  lineHeightLoose: 2,

  // Font weights
  fontWeightLight: 300,
  fontWeightRegular: 400,
  fontWeightMedium: 500,
  fontWeightSemibold: 600,
  fontWeightBold: 700,

  // Letter spacing
  letterSpacingTight: '-0.025em',
  letterSpacingNormal: '0',
  letterSpacingWide: '0.025em',
  letterSpacingWider: '0.05em',
};
