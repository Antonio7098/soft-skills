export const THEME_NAMES = ['obsidian', 'chalk', 'verdant'] as const;

export type ThemeName = (typeof THEME_NAMES)[number];

export interface ThemeMeta {
  readonly name: ThemeName;
  readonly label: string;
  readonly description: string;
  readonly swatch: string;
}

export const THEMES: Record<ThemeName, ThemeMeta> = {
  obsidian: {
    name: 'obsidian',
    label: 'Obsidian',
    description: 'Dark luxury with warm gold accents',
    swatch: '#C9A96E',
  },
  chalk: {
    name: 'chalk',
    label: 'Chalk',
    description: 'Light editorial with deep teal accents',
    swatch: '#1A6B5C',
  },
  verdant: {
    name: 'verdant',
    label: 'Verdant',
    description: 'Earthy warmth with terracotta accents',
    swatch: '#8B5E3C',
  },
} as const;

export const DEFAULT_THEME: ThemeName = 'verdant';
