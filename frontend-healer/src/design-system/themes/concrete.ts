import type { Theme } from './types';
import { concreteColors } from './concrete-colors';
import { typography } from '../tokens/typography.shared';
import { spacing, radius, shadows, motion, zIndex } from '../tokens/layout.shared';

/**
 * Concrete theme - Light, industrial, brutalist inspired.
 * Raw concrete textures meet sharp editorial typography.
 * Burnt orange accents cut through warm neutral backgrounds.
 */
export const concreteTheme: Theme = {
  id: 'concrete',
  name: 'Concrete',
  description: 'Raw industrial warmth with editorial precision',
  colors: concreteColors,
  typography,
  spacing,
  radius,
  shadows,
  motion,
  zIndex,
};
