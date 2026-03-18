import type { ColorTokens } from '../tokens/colors';

/**
 * Concrete theme - Light, industrial, brutalist inspired.
 * Raw concrete textures meet sharp editorial typography.
 * Burnt orange accents cut through warm neutral backgrounds.
 */
export const concreteColors: ColorTokens = {
  // Background surfaces - warm concrete tones
  bgPrimary: '#F5F2ED',
  bgSecondary: '#EBE7E0',
  bgTertiary: '#E0DBD3',
  bgInverse: '#1A1A1A',
  bgMuted: '#D9D4CB',

  // Foreground / text - deep charcoal
  fgPrimary: '#1A1A1A',
  fgSecondary: '#4A4A4A',
  fgTertiary: '#7A7A7A',
  fgInverse: '#F5F2ED',
  fgAccent: '#C44D2B',

  // Borders - subtle concrete lines
  borderDefault: '#C8C3BA',
  borderStrong: '#9E9890',
  borderSubtle: '#DDD8D0',
  borderAccent: '#C44D2B',

  // Interactive - burnt orange accent
  interactiveDefault: '#C44D2B',
  interactiveHover: '#A83D1F',
  interactiveActive: '#8C3119',
  interactiveMuted: '#D4A096',

  // Status colors - muted earth tones
  statusSuccess: '#2D6B4F',
  statusWarning: '#B8860B',
  statusError: '#C44D2B',
  statusInfo: '#2B5C8A',

  // Accent - burnt orange + deep blue
  accentPrimary: '#C44D2B',
  accentSecondary: '#2B5C8A',
  accentTertiary: '#5C7A4A',

  // Overlay
  overlayLight: 'rgba(245, 242, 237, 0.85)',
  overlayDark: 'rgba(26, 26, 26, 0.75)',

  // Effects
  shadowColor: 'rgba(26, 26, 26, 0.12)',
  glowColor: 'rgba(196, 77, 43, 0.3)',
};
