import { concreteTheme } from './concrete';
import { obsidianTheme } from './obsidian';
import type { Theme, ThemeId } from './types';

/**
 * Registry of all available themes.
 */
export const themes: Record<ThemeId, Theme> = {
  concrete: concreteTheme,
  obsidian: obsidianTheme,
};

/**
 * Get a theme by its ID.
 */
export function getTheme(id: ThemeId): Theme {
  return themes[id];
}

/**
 * Get all theme metadata (without full token data).
 */
export function getThemeList(): Array<{ id: ThemeId; name: string; description: string }> {
  return Object.values(themes).map(({ id, name, description }) => ({
    id: id as ThemeId,
    name,
    description,
  }));
}

export type { Theme, ThemeId };
export { concreteTheme } from './concrete';
export { obsidianTheme } from './obsidian';
