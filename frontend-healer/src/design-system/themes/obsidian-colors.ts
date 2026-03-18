import type { ColorTokens } from '../tokens/colors';

/**
 * Obsidian theme colors - Dark, dramatic, editorial inspired.
 * Deep blacks meet warm amber highlights.
 */
export const obsidianColors: ColorTokens = {
  // Background surfaces - deep warm blacks
  bgPrimary: '#0D0D0D',
  bgSecondary: '#161616',
  bgTertiary: '#1F1F1F',
  bgInverse: '#F5F2ED',
  bgMuted: '#2A2A2A',

  // Foreground / text - warm whites
  fgPrimary: '#F0EDE8',
  fgSecondary: '#B8B4AD',
  fgTertiary: '#7A7772',
  fgInverse: '#1A1A1A',
  fgAccent: '#E8A87C',

  // Borders - subtle warm grays
  borderDefault: '#3A3A3A',
  borderStrong: '#5A5A5A',
  borderSubtle: '#2A2A2A',
  borderAccent: '#E8A87C',

  // Interactive - warm amber
  interactiveDefault: '#E8A87C',
  interactiveHover: '#F0BC96',
  interactiveActive: '#D4956A',
  interactiveMuted: '#5A4A3A',

  // Status colors - vivid but warm
  statusSuccess: '#6BCB8F',
  statusWarning: '#F0C040',
  statusError: '#E87C6C',
  statusInfo: '#6CA0E8',

  // Accent - amber + cool slate
  accentPrimary: '#E8A87C',
  accentSecondary: '#7C9EB8',
  accentTertiary: '#8CB87C',

  // Overlay
  overlayLight: 'rgba(13, 13, 13, 0.85)',
  overlayDark: 'rgba(0, 0, 0, 0.9)',

  // Effects
  shadowColor: 'rgba(0, 0, 0, 0.5)',
  glowColor: 'rgba(232, 168, 124, 0.25)',
};
