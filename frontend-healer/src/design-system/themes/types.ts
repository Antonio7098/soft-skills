import type { ColorTokens } from '../tokens/colors';
import type { TypographyTokens } from '../tokens/typography';
import type { SpacingTokens, RadiusTokens, ShadowTokens, MotionTokens, ZIndexTokens } from '../tokens/layout';

/**
 * Complete theme definition.
 * Combines all token sets into a single cohesive theme.
 */
export interface Theme {
  id: string;
  name: string;
  description: string;
  colors: ColorTokens;
  typography: TypographyTokens;
  spacing: SpacingTokens;
  radius: RadiusTokens;
  shadows: ShadowTokens;
  motion: MotionTokens;
  zIndex: ZIndexTokens;
}

/**
 * Available theme IDs.
 */
export type ThemeId = 'concrete' | 'obsidian';
