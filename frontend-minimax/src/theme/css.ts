import type { Theme } from '../types/theme';

export function generateThemeCSS(theme: Theme): string {
  const { colors, typography, spacing, motion, borderRadius, shadow } = theme;

  return `
:root {
  --color-background: ${colors.background};
  --color-surface: ${colors.surface};
  --color-surface-alt: ${colors.surfaceAlt};
  --color-primary: ${colors.primary};
  --color-primary-hover: ${colors.primaryHover};
  --color-primary-muted: ${colors.primaryMuted};
  --color-accent: ${colors.accent};
  --color-accent-hover: ${colors.accentHover};
  --color-text: ${colors.text};
  --color-text-muted: ${colors.textMuted};
  --color-text-inverse: ${colors.textInverse};
  --color-border: ${colors.border};
  --color-border-focus: ${colors.borderFocus};
  --color-success: ${colors.success};
  --color-warning: ${colors.warning};
  --color-error: ${colors.error};
  --color-shadow: ${colors.shadow};

  --font-display: ${typography.fontDisplay};
  --font-body: ${typography.fontBody};
  --font-mono: ${typography.fontMono};

  --font-size-xs: ${typography.sizeXs};
  --font-size-sm: ${typography.sizeSm};
  --font-size-base: ${typography.sizeBase};
  --font-size-lg: ${typography.sizeLg};
  --font-size-xl: ${typography.sizeXl};
  --font-size-2xl: ${typography.size2xl};
  --font-size-3xl: ${typography.size3xl};
  --font-size-4xl: ${typography.size4xl};

  --font-weight-normal: ${typography.weightNormal};
  --font-weight-medium: ${typography.weightMedium};
  --font-weight-bold: ${typography.weightBold};

  --line-height-tight: ${typography.lineHeightTight};
  --line-height-normal: ${typography.lineHeightNormal};
  --line-height-relaxed: ${typography.lineHeightRelaxed};

  --letter-spacing-tight: ${typography.letterSpacingTight};
  --letter-spacing-normal: ${typography.letterSpacingNormal};
  --letter-spacing-wide: ${typography.letterSpacingWide};

  --space-1: ${spacing.space1};
  --space-2: ${spacing.space2};
  --space-3: ${spacing.space3};
  --space-4: ${spacing.space4};
  --space-5: ${spacing.space5};
  --space-6: ${spacing.space6};
  --space-8: ${spacing.space8};
  --space-10: ${spacing.space10};
  --space-12: ${spacing.space12};
  --space-16: ${spacing.space16};
  --space-20: ${spacing.space20};
  --space-24: ${spacing.space24};

  --motion-duration-fast: ${motion.durationFast};
  --motion-duration-normal: ${motion.durationNormal};
  --motion-duration-slow: ${motion.durationSlow};
  --motion-ease-out: ${motion.easeOut};
  --motion-ease-in-out: ${motion.easeInOut};
  --motion-ease-spring: ${motion.easeSpring};

  --radius-sm: ${borderRadius.sm};
  --radius-md: ${borderRadius.md};
  --radius-lg: ${borderRadius.lg};
  --radius-xl: ${borderRadius.xl};
  --radius-full: ${borderRadius.full};

  --shadow-sm: ${shadow.sm};
  --shadow-md: ${shadow.md};
  --shadow-lg: ${shadow.lg};
  --shadow-xl: ${shadow.xl};
}
`.trim();
}
