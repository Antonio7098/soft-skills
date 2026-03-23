import type { Theme } from './types';
import { obsidianColors } from './obsidian-colors';
import { typography } from '../tokens/typography.shared';
import { spacing, radius, shadows, motion, zIndex } from '../tokens/layout.shared';

/**
 * Obsidian theme - Dark, dramatic, editorial inspired.
 * Deep blacks meet warm amber highlights.
 * Cinematic atmosphere with refined typography.
 */
export const obsidianTheme: Theme = {
  id: 'obsidian',
  name: 'Obsidian',
  description: 'Dark cinematic depth with warm amber precision',
  colors: obsidianColors,
  typography,
  spacing,
  radius,
  shadows,
  motion,
  zIndex,
};
