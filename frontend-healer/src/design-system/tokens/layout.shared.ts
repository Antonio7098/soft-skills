import type { SpacingTokens, RadiusTokens, ShadowTokens, MotionTokens, ZIndexTokens } from './layout';

/**
 * Shared spacing tokens - 4px base unit.
 */
export const spacing: SpacingTokens = {
  space0: '0',
  space1: '0.25rem',   // 4px
  space2: '0.5rem',    // 8px
  space3: '0.75rem',   // 12px
  space4: '1rem',      // 16px
  space5: '1.25rem',   // 20px
  space6: '1.5rem',    // 24px
  space8: '2rem',      // 32px
  space10: '2.5rem',   // 40px
  space12: '3rem',     // 48px
  space16: '4rem',     // 64px
  space20: '5rem',     // 80px
  space24: '6rem',     // 96px
  space32: '8rem',     // 128px
};

/**
 * Border radius tokens.
 */
export const radius: RadiusTokens = {
  radiusNone: '0',
  radiusSm: '0.25rem',
  radiusMd: '0.5rem',
  radiusLg: '0.75rem',
  radiusXL: '1rem',
  radius2XL: '1.5rem',
  radiusFull: '9999px',
};

/**
 * Shadow tokens - theme-aware via CSS variables.
 */
export const shadows: ShadowTokens = {
  shadowNone: 'none',
  shadowSm: '0 1px 2px var(--shadow-color)',
  shadowMd: '0 4px 6px -1px var(--shadow-color)',
  shadowLg: '0 10px 15px -3px var(--shadow-color)',
  shadowXL: '0 20px 25px -5px var(--shadow-color)',
  shadow2XL: '0 25px 50px -12px var(--shadow-color)',
  shadowInner: 'inset 0 2px 4px var(--shadow-color)',
  shadowGlow: '0 0 20px var(--glow-color)',
};

/**
 * Motion tokens.
 */
export const motion: MotionTokens = {
  durationInstant: '50ms',
  durationFast: '150ms',
  durationNormal: '250ms',
  durationSlow: '400ms',
  durationSlower: '600ms',
  easingDefault: 'cubic-bezier(0.4, 0, 0.2, 1)',
  easingIn: 'cubic-bezier(0.4, 0, 1, 1)',
  easingOut: 'cubic-bezier(0, 0, 0.2, 1)',
  easingInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
  easingBounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
};

/**
 * Z-index tokens.
 */
export const zIndex: ZIndexTokens = {
  zBase: 0,
  zDropdown: 100,
  zSticky: 200,
  zFixed: 300,
  zOverlay: 400,
  zModal: 500,
  zPopover: 600,
  zTooltip: 700,
  zToast: 800,
};
